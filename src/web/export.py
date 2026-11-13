"""
Export the engine's results to one JSON file for the Joota Pulse web app.

The web app is a static site (HTML, CSS, JavaScript) so it can be hosted free on
GitHub Pages. Everything heavy is computed here in Python; the browser only filters,
sorts and displays. Workspace-level numbers are pre-computed for every workspace
(all brands, core brands, each brand); money is computed in the browser because the
user can change the price and conversion assumptions.

Run after run_pipeline.py:  python src/web/export.py  [output path]
"""
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "engine"))
from replies import REPLIES  # noqa: E402

PROC = ROOT / "data" / "processed"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "web" / "data.json"
CORE = ["Borjan", "Servis", "Ndure"]
BRAND_POST, CREATOR_POST = "Brand's own post", "Creator / influencer post"
SNAPSHOT = dict(run_date="2026-11-12", videos_found=2561, videos_kept=853, comments_raw=8508, comments_clean=6767)


def run_info():
    """Date and collection numbers of the data being exported (live run or the 12 Nov snapshot)."""
    p = PROC / "pipeline_stats.json"
    info = {**SNAPSHOT, **(json.loads(p.read_text()) if p.exists() else {})}
    d = dt.date.fromisoformat(info["run_date"])
    info["label"] = f"{d.day} {d.strftime('%b %Y')}"
    return info

ASK = {"price": "Price", "availability": "Where to buy", "delivery_order": "Order & delivery",
       "contact": "Contact", "size_fit": "Size", "complaint": "Complaint"}
SHORT_NEED = {"Availability / location": "Where to buy", "Price inquiry": "Price", "Discount / sale": "Sales & discounts",
              "Delivery / how to order": "Ordering & delivery", "Contact / link request": "Contact details",
              "Size / fit": "Size & fit", "Quality / comfort": "Quality & comfort", "Complaint / problem": "Complaints",
              "Ad nostalgia / celebrity buzz": "Ad nostalgia", "Product praise / wants it": "Product love"}
HOT_NEEDS = {"Where to buy", "Price", "Ordering & delivery", "Contact details", "Size & fit"}
SEGMENTS = [  # name, emoji, badge, tone, what to do, needs that define the group
    ("Where-can-I-buy askers", "📍", "Ready to buy", "hot", "Pin a store locator and the order link.", {"availability"}),
    ("Price checkers", "💰", "Ready to buy", "hot", "Show prices on screen or in a pinned comment.", {"price"}),
    ("Deal hunters", "🏷️", "Ready to buy", "hot", "Post sale start and end dates.", {"discount_sale"}),
    ("Order & delivery askers", "🚚", "Ready to buy", "hot", "Explain cash on delivery and delivery days.", {"delivery_order"}),
    ("Contact seekers", "📞", "Ready to buy", "hot", "Put WhatsApp and website in every description.", {"contact"}),
    ("Size & fit askers", "📏", "Ready to buy", "hot", "Share a size guide and how each article fits.", {"size_fit"}),
    ("Unhappy customers", "⚠️", "Needs care", "bad", "Reply within a day and fix it privately.", {"complaint"}),
    ("Quality-conscious shoppers", "🔍", "Considering", "warm", "Show soles and stitching up close.", {"quality_comfort"}),
    ("Product fans", "💜", "Fans", "cool", "Retarget them with the same articles.", {"praise_product"}),
    ("Ad & meme crowd", "📺", "Buzz", "cool", "Reuse the buzz in throwback content.", {"nostalgia_ad"}),
    ("Supporters (general praise)", "👏", "Fans", "cool", "Thank them and point to the shop.", {"general_praise", "praise_content"}),
]
CITY = {"Lahore": r"lahore|lhr", "Karachi": r"karachi|khi", "Faisalabad": r"faisalabad|fsd", "Rawalpindi": r"pindi|rawalpindi",
        "Islamabad": r"islamabad|isb", "Hyderabad": r"hyderabad", "Multan": r"multan", "Sialkot": r"sialkot",
        "Peshawar": r"peshawar", "Gujranwala": r"gujranwala"}


def load():
    com = pd.read_csv(PROC / "comments_labeled.csv")
    vids = pd.read_csv(PROC / "videos_enriched.csv")
    seg = pd.read_csv(PROC / "comment_segments.csv")
    com = com.drop(columns=["channel", "title", "source", "channel_country"], errors="ignore")
    com = com.merge(vids[["video_id", "post_type", "channel", "channel_id", "title", "format", "content_type", "url"]],
                    on="video_id", how="left").merge(seg[["comment_id", "segment"]], on="comment_id", how="left")
    com["answered"] = com.thread.isin(set(com[com.owner_reply].thread))
    fs = PROC / "first_seen.csv"
    first = pd.read_csv(fs) if fs.exists() else pd.DataFrame(columns=["comment_id", "first_seen"])
    com = com.merge(first, on="comment_id", how="left")
    com["first_seen"] = com.first_seen.fillna(SNAPSHOT["run_date"])
    return com, vids


def last_run_date(com):
    """Comments first seen after the previous run are 'new'. With one run only, nothing is new."""
    dates = sorted(com.first_seen.unique())
    return dates[-1] if len(dates) > 1 else None


def cities(cust):
    t = cust.text.astype(str).str.lower()
    out = [(c, int(t.str.contains(rf"\b(?:{p})\b").sum())) for c, p in CITY.items()]
    return [{"city": c, "n": n} for c, n in sorted(out, key=lambda x: -x[1]) if n]


def leads(cust):
    q = cust[(cust.intent == "high") & (~cust.is_reply) & (cust.post_type == CREATOR_POST)]
    g = q.groupby(["channel", "channel_id"]).agg(buyers=("comment_id", "count"),
                                                 brands=("brand", lambda s: ", ".join(s.value_counts().index[:2])),
                                                 answered=("answered", "mean")).reset_index()
    g = g.sort_values("buyers", ascending=False).head(10)
    return [{"channel": r.channel, "url": f"https://www.youtube.com/channel/{r.channel_id}", "brands": r.brands,
             "buyers": int(r.buyers), "answered": round(float(r.answered), 3)} for r in g.itertuples()]


def campaigns(cust, vids, picked, label, waiting_n, buy_q):
    """Campaign ideas; '{MONEY}' is filled in by the browser from the user's assumptions."""
    out = []
    own = buy_q[buy_q.post_type == BRAND_POST]
    out.append(dict(id="reply", title="24-hour reply promise", impact="High impact", effort="Low effort", channel="YouTube comments",
                    why=f"{waiting_n:,} buying questions are waiting for a reply ({{MONEY}} in missed sales). On the brands' own "
                        f"videos, {int(own.answered.sum())} of {len(own)} were answered.",
                    do="Clear the Leads inbox every morning with the ready replies.",
                    en="Got a question about price, size or delivery? Comment below and we'll reply within 24 hours. 💬",
                    ru="Price, size ya delivery ka sawal hai? Comment karein, hum 24 ghante mein jawab denge. 💬"))
    ld = leads(cust)
    if ld:
        total = int(cust[(cust.intent == "high") & (~cust.is_reply) & (cust.post_type == CREATOR_POST)].shape[0])
        out.append(dict(id="creators", title="Creator sale-vlog partnership", impact="High impact", effort="Medium effort",
                        channel="Creators",
                        why=f"Creator videos hold {total:,} buying questions the brand never sees. Top: "
                            + ", ".join(x["channel"] for x in ld[:3]) + ".",
                        do="Send top creators a price list, size chart and order link to pin.",
                        en="Brief for creators: show 5 best-sellers with price on screen, try one pair on, pin the order link and sale end date.",
                        ru="Creator brief: 5 best-sellers price ke saath dikhayein, ek joota pehen kar dikhayein, order link aur sale ki last date pin karein."))
    cl = cities(cust)
    if cl:
        c1, c2 = cl[0]["city"], (cl[1]["city"] if len(cl) > 1 else "")
        out.append(dict(id="city", title=f"{c1}{' & ' + c2 if c2 else ''} city ads", impact="Medium impact", effort="Low effort",
                        channel="Instagram + Facebook ads",
                        why=f"{int((cust.segment == 'Where-can-I-buy askers').sum()):,} comments ask where to buy; "
                            + ", ".join(f"{x['city']} ({x['n']})" for x in cl[:3]) + " are named most.",
                        do="Run location-targeted ads that name the branch and the order link.",
                        en=f"Now in {c1}! Visit our nearest store or order online with cash on delivery. 📍",
                        ru=f"Ab {c1} mein! Qareebi store aayein ya online order karein, cash on delivery ke saath. 📍"))
    deal = int((cust.segment == "Deal hunters").sum())
    until = int(cust.text.str.lower().str.contains(r"kab tak|kb tk|kab tk|kb tak|until when|till when|last date").sum())
    if deal:
        out.append(dict(id="sale", title="Sale countdown posts", impact="Medium impact", effort="Low effort", channel="Stories + Shorts",
                        why=f"{deal:,} deal-hunter comments; {until} ask when a sale starts or ends ('sale kab tak hai?').",
                        do="Post the end date on day 1, then a 3-2-1 countdown with sizes left.",
                        en="⏳ Only 3 days left! Flat 30% off on best-sellers. Sale ends Sunday night. Shop now.",
                        ru="⏳ Sirf 3 din baqi! Best-sellers par flat 30% off. Sale Sunday raat khatam. Abhi order karein."))
    v = vids.copy()
    v["pt"] = v.title.str.lower().str.contains(r"price|\brs\.?\s?\d|\d{3,5}\s?(?:rs|pkr)")
    x = cust.merge(v[["video_id", "pt"]], on="video_id")
    if x.pt.any() and (~x.pt).any():
        a, b = (x[x.pt].need == "price").mean(), (x[~x.pt].need == "price").mean()
        if a < b:
            out.append(dict(id="prices", title="Prices on screen test", impact="Medium impact", effort="Low effort", channel="Shorts + Reels",
                            why=f"Videos with prices in the title get {a:.1%} price questions vs {b:.1%} without ({1 - a / b:.0%} fewer).",
                            do="A/B test the same video with and without prices on screen.",
                            en="New arrivals with prices 👟 Rs 3,999 | Rs 4,499 | Rs 5,999. Sizes 36–45. Order now.",
                            ru="Naye articles qeemat ke saath 👟 Rs 3,999 | Rs 4,499 | Rs 5,999. Size 36–45. Abhi order karein."))
    if "Servis" in picked:
        s = cust[cust.brand == "Servis"]
        out.append(dict(id="throwback", title="Servis throwback ad", impact="High impact", effort="Medium effort", channel="YouTube + Reels",
                        why=f"{(s.need == 'nostalgia_ad').mean():.0%} of Servis comments are about its classic ads; a 2012 ad still gets comments in 2026.",
                        do="A/B test a modern remake of the classic ad against a product ad.",
                        en="Remember this one? 😄 The classic is back, with a 2026 twist. Same comfort, new style.",
                        ru="Ye ad yaad hai? 😄 Classic wapas aa gaya, 2026 ke andaz mein. Wahi aaram, naya style."))
    size = int((cust.segment == "Size & fit askers").sum())
    if size:
        out.append(dict(id="size", title="Size guide reel", impact="Low impact", effort="Low effort", channel="Reels + pinned post",
                        why=f"{size} comments ask about size or fit; wrong sizes mean exchanges and bad reviews.",
                        do="Post a 15-second EU / UK / PK size chart reel.",
                        en="Not sure about your size? 📏 Here's our EU / UK / PK size guide. Easy exchange if it doesn't fit.",
                        ru="Size ka masla? 📏 Ye raha EU / UK / PK size guide. Fit na ho to aasaan exchange."))
    return out


def workspace(com, vids_all, picked, label, newest=None):
    c = com[com.brand.isin(picked)]
    cust = c[~c.owner_reply]
    vids = vids_all[vids_all.brand.isin(picked)]
    top = cust[~cust.is_reply]
    buy_q = top[top.intent == "high"]
    waiting = buy_q[~buy_q.answered]
    own = buy_q[buy_q.post_type == BRAND_POST]

    vc = cust.need_label.value_counts()
    asks = [{"label": SHORT_NEED[k], "n": int(vc.get(k, 0)), "hot": SHORT_NEED[k] in HOT_NEEDS}
            for k in ["Availability / location", "Price inquiry", "Discount / sale", "Delivery / how to order",
                      "Quality / comfort", "Contact / link request", "Complaint / problem", "Size / fit"] if vc.get(k, 0)]
    asks = sorted(asks, key=lambda a: -a["n"])

    d = pd.to_datetime(cust.published)
    cut = d.max() - pd.Timedelta(days=183)
    a = cust[d >= cut].need_label.value_counts(normalize=True)
    b = cust[d < cut].need_label.value_counts(normalize=True)
    diff = (a.sub(b, fill_value=0) * 100).drop(["Other / off-topic", "General praise / blessing", "Praise for the video"], errors="ignore")
    trend = [{"label": SHORT_NEED.get(k, k), "pts": round(float(v), 1)} for k, v in pd.concat([diff.nlargest(3), diff.nsmallest(2)]).items()]

    g = cust.groupby("segment").agg(people=("author", "nunique"), comments=("comment_id", "count"))
    segs = []
    for name, emo, badge, tone, todo, needs in SEGMENTS:
        if name not in g.index:
            continue
        sub = cust[(cust.segment == name) & cust.need.isin(needs)]
        best = sub[(sub.label_source == "word list") & sub.text.astype(str).str.len().between(15, 90)]
        quote = best.sort_values("likes", ascending=False).text.iloc[0] if len(best) else ""
        ex = sub.drop_duplicates("text")
        ex = ex.sample(min(6, len(ex)), random_state=4) if len(ex) else ex
        segs.append(dict(name=name, emoji=emo, badge=badge, tone=tone, todo=todo, people=int(g.loc[name, "people"]),
                         comments=int(g.loc[name, "comments"]), quote=quote,
                         examples=[{"text": t[:220], "brand": br, "date": dt} for t, br, dt in zip(ex.text, ex.brand, ex.published)]))

    pt = vids.groupby("post_type").agg(cm=("comments_per_1k", "median"), views=("views", "median"))
    hi = cust.groupby("post_type").intent.apply(lambda s: (s == "high").mean())
    stats = None
    if BRAND_POST in pt.index and CREATOR_POST in pt.index and pt.loc[BRAND_POST, "cm"] > 0:
        stats = dict(cm_ratio=round(float(pt.loc[CREATOR_POST, "cm"] / pt.loc[BRAND_POST, "cm"]), 1),
                     hi_creator=round(float(hi.get(CREATOR_POST, 0)), 3), hi_brand=round(float(hi.get(BRAND_POST, 0)), 3),
                     views_ratio=round(float(pt.loc[BRAND_POST, "views"] / max(pt.loc[CREATOR_POST, "views"], 1)), 1))
    cg = vids.groupby(["content_type", "format"]).agg(n=("video_id", "count"), cm=("comments_per_1k", "median"),
                                                      views=("views", "median"), hi=("high_intent_share", "mean")).reset_index()
    cg = cg[(cg.n >= 5) & (cg.content_type != "Other / untitled")].sort_values("cm", ascending=False)
    card = lambda r: dict(type=r.content_type, format=r.format, cm=round(float(r.cm), 2), hi=round(float(r.hi), 3),
                          views=int(r.views), n=int(r.n))
    unusual = pd.read_csv(PROC / "unusual_posts.csv")
    u = unusual[unusual.brand.isin(picked) & unusual.what_to_do.str.startswith("Learn")].head(6)

    return dict(
        label=label, brands=picked,
        comments=int(len(cust)), people=int(cust.author.nunique()), videos=int(vids.video_id.nunique()),
        top_level=int(len(top)), buying=int(len(buy_q)), waiting=int(len(waiting)),
        own_q=int(len(own)), own_answered=int(own.answered.sum()),
        creator_q=int((buy_q.post_type == CREATOR_POST).sum()),
        new_buyers=int((buy_q.first_seen == newest).sum()) if newest else 0,
        new_comments=int((cust.first_seen == newest).sum()) if newest else 0,
        cities=cities(cust)[:6], asks=asks, trend=trend,
        recent=int((d >= cut).sum()), older=int((d < cut).sum()),
        segments=segs, stats=stats, post_more=[card(r) for r in cg.head(3).itertuples()],
        post_less=[card(r) for r in cg.tail(3).iloc[::-1].itertuples()], leads=leads(cust),
        standouts=[dict(title=r.title, url=r.url, brand=r.brand, channel=r.channel, views=int(r.views),
                        why=r.unusual_because.split(";")[0]) for r in u.itertuples()],
        campaigns=campaigns(cust, vids, picked, label, int(len(waiting)), buy_q),
    )


def main():
    com, vids = load()
    brands = CORE + sorted(b for b in vids.brand.unique() if b not in CORE)
    newest = last_run_date(com)
    spaces = {"all": workspace(com, vids, brands, f"All {len(brands)} brands", newest),
              "core": workspace(com, vids, CORE, "Borjan · Servis · Ndure", newest)}
    for b in brands:
        spaces[b] = workspace(com, vids, [b], b, newest)

    cust = com[~com.owner_reply]
    top = cust[~cust.is_reply]
    inbox = top[((top.intent == "high") | (top.need == "complaint")) & (~top.answered)].sort_values(["published", "likes"], ascending=False)
    inbox_items = [dict(id=i, brand=r.brand, ask=ASK.get(r.need, "Other"), need=r.need, text=str(r.text)[:500], date=r.published,
                        where="Your video" if r.post_type == BRAND_POST else f"Creator · {r.channel}",
                        own=r.post_type == BRAND_POST, url=r.url, likes=int(r.likes), lang=r.lang,
                        new=bool(newest and r.first_seen == newest))
                   for i, r in enumerate(inbox.itertuples())]

    comp = []
    for b in brands:
        s = cust[cust.brand == b]
        t = s[~s.is_reply]
        own = t[(t.intent == "high") & (t.post_type == BRAND_POST)]
        buy = s[s.need.isin(ASK) & (s.need != "complaint")].need.map(ASK).value_counts()
        comp.append(dict(brand=b, comments=int(len(s)), buying=round(float((t.intent == "high").mean()), 3),
                         top=buy.index[0] if len(buy) else "–", own_q=int(len(own)), own_answered=int(own.answered.sum()),
                         fans=round(float(s.need.isin(["praise_product", "general_praise"]).mean()), 3),
                         complaints=round(float((s.need == "complaint").mean()), 4), buzz=round(float((s.need == "nostalgia_ad").mean()), 3),
                         mix={k: round(float((s.need == n).mean() * 100), 1) for k, n in
                              {"Where to buy": "availability", "Price": "price", "Sale": "discount_sale",
                               "Order & delivery": "delivery_order", "Quality": "quality_comfort", "Complaints": "complaint"}.items()}))

    metrics = json.loads((PROC / "method_metrics.json").read_text())
    cmap = pd.read_csv(PROC / "cluster_map.csv").merge(com[["comment_id", "text"]], on="comment_id")
    names = pd.read_csv(PROC / "clusters.csv").set_index("cluster").main_need_label
    pts = cmap.sample(1500, random_state=0)
    bench = None
    if (PROC / "benchmark.csv").exists():
        b = pd.read_csv(PROC / "benchmark.csv")
        bench = b.astype(object).where(b.notna(), None).to_dict("records")   # NaN is not valid JSON

    info = run_info()
    limits = dict(size_q=int((cust.need == "size_fit").sum()), complaints=int((cust.need == "complaint").sum()),
                  unlabelled=round(float((cust.need == "other").mean()), 3))
    data = dict(
        date=info["label"], updated=info["run_date"], pipeline=info, limits=limits, history=[], brands=brands, spaces=spaces, inbox=inbox_items,
        replies={k: v for k, v in REPLIES.items()}, competitors=comp,
        how=dict(metrics=metrics, comments=int(len(com)), customer_comments=int(len(cust)), videos=int(len(vids)),
                 points=[dict(x=round(float(r.x), 3), y=round(float(r.y), 3), g=names.get(r.cluster, "Other"), t=str(r.text)[:70])
                         for r in pts.itertuples()], benchmark=bench),
        links=dict(repo="https://github.com/usamahanif349/pk-footwear-audience-engine",
                   p1="https://github.com/usamahanif349/pk-footwear-sentiment-analysis",
                   p2="https://github.com/usamahanif349/pk-footwear-budget-optimizer",
                   p2app="https://pk-footwear-budget-optimizer.streamlit.app/",
                   streamlit="https://pk-footwear-audience-engine.streamlit.app/"),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False))
    print("wrote", OUT, f"{OUT.stat().st_size / 1e6:.2f} MB", "| inbox items:", len(inbox_items))


if __name__ == "__main__":
    main()
