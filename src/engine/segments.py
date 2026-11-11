"""
Steps 3 and 4 of the engine: which audience groups exist, and what should the brand do?

* Every commenter (anonymous id) is placed in one audience segment by what they asked
  or said, with a fixed priority: problems first, then buying questions, then the rest.
* Reply gaps: a buying question counts as answered when the video's owner replied in
  the same thread.
* The action plan is built from rules; every action carries the number that triggered it.

Run after content.py:  python src/engine/segments.py
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed"
CORE = ["Borjan", "Servis", "Ndure"]

SEGMENTS = [  # (segment, needs that put a commenter in it); first match wins
    ("Unhappy customers", {"complaint"}),
    ("Order & delivery askers", {"delivery_order"}),
    ("Price checkers", {"price"}),
    ("Where-can-I-buy askers", {"availability"}),
    ("Contact seekers", {"contact"}),
    ("Size & fit askers", {"size_fit"}),
    ("Deal hunters", {"discount_sale"}),
    ("Quality-conscious shoppers", {"quality_comfort"}),
    ("Product fans", {"praise_product"}),
    ("Ad & meme crowd", {"nostalgia_ad"}),
    ("Supporters (general praise)", {"general_praise", "praise_content"}),
    ("Off-topic / unclear", {"other"}),
]
SEGMENT_ACTION = {
    "Unhappy customers": "Reply publicly within a day, move to private message, fix and follow up.",
    "Order & delivery askers": "Pin a comment with the order link, cash on delivery and delivery times.",
    "Price checkers": "Put prices in the video, the title or a pinned comment.",
    "Where-can-I-buy askers": "Share a store locator and online link; run city-targeted ads.",
    "Contact seekers": "Add WhatsApp and website links to every description and pinned comment.",
    "Size & fit askers": "Publish a size guide (EU / UK / PK) and say how each article fits.",
    "Deal hunters": "Announce sale start and end dates clearly; send early-access offers.",
    "Quality-conscious shoppers": "Show close-ups of soles and stitching; share wear-test videos.",
    "Product fans": "Retarget with the same articles; ask them to tag a friend.",
    "Ad & meme crowd": "Reuse the buzz: throwback content, remakes, meme-friendly edits.",
    "Supporters (general praise)": "Thank them and nudge to the shop link; low priority.",
    "Off-topic / unclear": "No action needed.",
}
# Project 2 ad-copy angles that fit each segment (src/marketing/ad_copy.py in pk-footwear-budget-optimizer)
PROJECT2_ANGLE = {
    "Price checkers": "price", "Deal hunters": "price", "Where-can-I-buy askers": "staff (shop online)",
    "Order & delivery askers": "delivery", "Contact seekers": "delivery", "Size & fit askers": "size",
    "Quality-conscious shoppers": "quality", "Product fans": "design", "Unhappy customers": "quality",
}
CITIES = {"Karachi": r"karachi|khi", "Lahore": r"lahore|lhr", "Islamabad": r"islamabad|isb", "Rawalpindi": r"pindi|rawalpindi",
          "Faisalabad": r"faisalabad|fsd", "Multan": r"multan", "Hyderabad": r"hyderabad", "Peshawar": r"peshawar",
          "Sialkot": r"sialkot", "Gujranwala": r"gujranwala", "Quetta": r"quetta"}


def segment_of(needs):
    for name, keys in SEGMENTS:
        if needs & keys:
            return name
    return "Off-topic / unclear"


def build():
    com = pd.read_csv(OUT / "comments_labeled.csv")
    v = pd.read_csv(OUT / "videos_enriched.csv")
    com = com.drop(columns=["channel", "channel_country", "title", "source"], errors="ignore")
    com = com.merge(v[["video_id", "post_type", "channel", "content_type", "format", "title"]], on="video_id", how="left")
    cust = com[~com.owner_reply].copy()

    # ---------- segments ----------
    per = cust.groupby("author").agg(needs=("need", lambda s: set(s)), comments=("comment_id", "count"),
                                      brands=("brand", lambda s: ", ".join(sorted(set(s)))),
                                      top_brand=("brand", lambda s: s.value_counts().index[0]))
    per["segment"] = per.needs.apply(segment_of)
    cust["segment"] = cust.author.map(per.segment)

    answered_threads = set(com[com.owner_reply].thread)
    top = cust[~cust.is_reply].copy()
    top["answered"] = top.thread.isin(answered_threads)

    seg_rows = []
    for name, _ in SEGMENTS:
        g, c = per[per.segment == name], cust[cust.segment == name]
        t = top[top.segment == name]
        own = t[t.post_type == "Brand's own post"]
        examples = c[c.need != "other"].text if (c.need != "other").any() else c.text
        seg_rows.append(dict(
            segment=name, commenters=len(g), comments=len(c),
            share_of_commenters=len(g) / len(per),
            high_intent_share=(c.intent == "high").mean() if len(c) else 0,
            core_brand_share=c.brand.isin(CORE).mean() if len(c) else 0,
            top_brands=", ".join(c.brand.value_counts().head(3).index),
            questions_on_brand_posts=len(own), answered_on_brand_posts=int(own.answered.sum()),
            questions_on_creator_posts=int((t.post_type != "Brand's own post").sum()),
            examples=" | ".join(examples.drop_duplicates().sample(min(4, examples.nunique()), random_state=0)
                                .str.replace("\n", " ").str[:70]),
            action=SEGMENT_ACTION[name], project2_angle=PROJECT2_ANGLE.get(name, "-")))
    segments = pd.DataFrame(seg_rows)

    # ---------- needs by brand ----------
    brand_needs = (pd.crosstab(cust.brand, cust.need_label, normalize="index") * 100).round(1)
    brand_needs["customer_comments"] = cust.brand.value_counts()

    # ---------- reply gaps ----------
    hi = top[top.intent == "high"]
    gaps = hi.groupby(["brand", "post_type"]).agg(buying_questions=("comment_id", "count"),
                                                   answered=("answered", "sum")).reset_index()
    gaps["answer_rate"] = gaps.answered / gaps.buying_questions
    unanswered = hi[~hi.answered][["brand", "post_type", "channel", "need_label", "text", "published", "video_id"]]
    creator_leads = (hi[hi.post_type != "Brand's own post"].groupby(["channel", "brand"])
                     .agg(buying_questions=("comment_id", "count"), answered_by_creator=("answered", "mean"))
                     .reset_index().sort_values("buying_questions", ascending=False))

    # ---------- cities ----------
    t = cust.text.str.lower()
    cities = pd.DataFrame([(c, int(t.str.contains(rf"\b(?:{p})\b").sum())) for c, p in CITIES.items()],
                          columns=["city", "mentions"]).sort_values("mentions", ascending=False)

    # ---------- price shown or not ----------
    v["price_in_title"] = v.title.str.lower().str.contains(r"price|\brs\.?\s?\d|\d{3,5}\s?(?:rs|pkr)")
    x = cust.merge(v[["video_id", "price_in_title"]], on="video_id")
    price_q = x.groupby("price_in_title").need.apply(lambda s: (s == "price").mean())

    findings = dict(
        customer_comments=int(len(cust)), commenters=int(len(per)), videos=int(len(v)),
        buying_questions=int(len(hi)),
        buying_q_brand_posts=int((hi.post_type == "Brand's own post").sum()),
        buying_q_brand_posts_answered=int(hi[hi.post_type == "Brand's own post"].answered.sum()),
        buying_q_creator_posts=int((hi.post_type != "Brand's own post").sum()),
        buying_q_creator_posts_answered=int(hi[hi.post_type != "Brand's own post"].answered.sum()),
        price_q_share_price_shown=round(float(price_q.get(True, np.nan)), 4),
        price_q_share_price_hidden=round(float(price_q.get(False, np.nan)), 4),
        servis_buzz_share=round(float((cust[cust.brand == "Servis"].need == "nostalgia_ad").mean()), 4),
        brand_post_median_views=float(v[v.post_type == "Brand's own post"].views.median()),
        creator_post_median_views=float(v[v.post_type != "Brand's own post"].views.median()),
        brand_post_likes_per_1k=float(v[v.post_type == "Brand's own post"].likes_per_1k.median()),
        creator_post_likes_per_1k=float(v[v.post_type != "Brand's own post"].likes_per_1k.median()),
        brand_post_comments_per_1k=float(v[v.post_type == "Brand's own post"].comments_per_1k.median()),
        creator_post_comments_per_1k=float(v[v.post_type != "Brand's own post"].comments_per_1k.median()),
        brand_post_high_intent=float(cust[cust.post_type == "Brand's own post"].intent.eq("high").mean()),
        creator_post_high_intent=float(cust[cust.post_type != "Brand's own post"].intent.eq("high").mean()),
    )
    actions = action_plan(findings, segments, brand_needs, creator_leads, cities, v, cust)
    return cust, segments, brand_needs, gaps, unanswered, creator_leads, cities, findings, actions


def action_plan(f, seg, brand_needs, leads, cities, v, cust):
    s = seg.set_index("segment")
    acts = []

    def add(area, brand, action, evidence, priority):
        acts.append(dict(area=area, brand=brand, action=action, evidence=evidence, priority=priority))

    bq, ba = f["buying_q_brand_posts"], f["buying_q_brand_posts_answered"]
    add("Customer service", "All brands",
        "Answer buying questions on your own YouTube posts within 24 hours. Use the reply assistant templates.",
        f"Brands answered {ba} of {bq} buying questions (price, location, order, size, contact) on their own posts.", 1)
    cq = f["buying_q_creator_posts"]
    top_creators = ", ".join(leads.channel.head(3))
    add("Customer service", "All brands",
        "Monitor creator videos about your brand and give top creators a pinned comment with prices, sizes and the order link.",
        f"{cq} buying questions sit under creator videos, where the brand never replies. Top creators: {top_creators}.", 1)
    ratio_c = f["creator_post_comments_per_1k"] / max(f["brand_post_comments_per_1k"], 1e-9)
    add("Content", "All brands",
        "Shift part of the video budget from brand-made Shorts to creator collaborations (sale vlogs, try-ons, honest reviews).",
        f"Creator posts get {ratio_c:.0f}× more comments per 1,000 views and {f['creator_post_high_intent']:.0%} buying questions "
        f"vs {f['brand_post_high_intent']:.0%} on brand posts. Brand posts get more views ({f['brand_post_median_views']:,.0f} vs "
        f"{f['creator_post_median_views']:,.0f} median), likely from paid promotion.", 1)
    shown, hidden = f["price_q_share_price_shown"], f["price_q_share_price_hidden"]
    if shown < hidden:
        add("Content", "All brands", "Show prices in the title, on screen or in a pinned comment.",
            f"Videos with prices in the title get {shown:.1%} price questions vs {hidden:.1%} without, "
            f"{(1 - shown / hidden):.0%} fewer (a correlation, worth testing).", 2)
    city_txt = ", ".join(f"{r.city} ({r.mentions})" for r in cities.head(3).itertuples())
    add("Promotions", "All brands", "Run city-targeted ads and posts that name the branch, starting with the most-asked cities.",
        f"{int(s.loc['Where-can-I-buy askers', 'commenters'])} commenters asked where to buy. Most-named cities: {city_txt}.", 2)
    until = int(cust.text.str.lower().str.contains(r"kab tak|kb tk|kab tk|kb tak|until when|till when|last date|kab (?:se|sy|lagegi|lgy|lagay)").sum())
    add("Promotions", "All brands", "State sale start and end dates in every sale post and pinned comment.",
        f"{int(s.loc['Deal hunters', 'commenters'])} deal hunters; {until} comments ask when a sale starts or ends ('sale kab tak hai?').", 2)
    add("Customer service", "All brands", "Publish an EU / UK / PK size guide and note if an article runs small or large.",
        f"{int(s.loc['Size & fit askers', 'commenters'])} commenters asked about size or fit.", 3)
    sb = f["servis_buzz_share"]
    add("Campaign testing", "Servis",
        "A/B test a throwback remake of the classic Servis ad against a standard product ad, same budget, same audience.",
        f"{sb:.0%} of Servis comments are ad nostalgia and meme buzz; a 2012 ad still collects comments in 2026.", 1)
    for b in CORE:
        if b not in brand_needs.index:
            continue
        row = brand_needs.loc[b].drop("customer_comments")
        buy = row[[c for c in ["Price inquiry", "Availability / location", "Delivery / how to order",
                               "Contact / link request", "Size / fit"] if c in row]]
        main = buy.idxmax()
        add("Campaign testing", b,
            f"Test ad copy that answers the top buying question up front ({main.lower()}), against the current copy.",
            f"{main} is {buy.max():.1f}% of {b} comments, its largest buying need.", 2)
    unhappy = s.loc["Unhappy customers"]
    add("Customer service", unhappy.top_brands, "Set up a complaint routine: public reply, private follow-up, fix within 48 hours.",
        f"{int(unhappy.commenters)} unhappy customers (damaged pairs, refunds, late orders); most under {unhappy.top_brands}.", 2)
    return pd.DataFrame(acts).sort_values(["priority", "area"]).reset_index(drop=True)


def main():
    cust, segments, brand_needs, gaps, unanswered, leads, cities, findings, actions = build()
    cust[["comment_id", "author", "segment"]].to_csv(OUT / "comment_segments.csv", index=False)
    segments.to_csv(OUT / "segments.csv", index=False)
    brand_needs.to_csv(OUT / "brand_needs.csv")
    gaps.to_csv(OUT / "reply_gaps.csv", index=False)
    unanswered.to_csv(OUT / "unanswered_questions.csv", index=False)
    leads.to_csv(OUT / "creator_leads.csv", index=False)
    cities.to_csv(OUT / "city_mentions.csv", index=False)
    actions.to_csv(OUT / "action_plan.csv", index=False)
    (OUT / "findings.json").write_text(json.dumps(findings, indent=2))
    print(json.dumps(findings, indent=2))
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
    print(segments[["segment", "commenters", "comments", "high_intent_share", "top_brands"]].to_string(index=False))
    print(actions[["priority", "area", "brand", "evidence"]].to_string(index=False))


if __name__ == "__main__":
    main()
