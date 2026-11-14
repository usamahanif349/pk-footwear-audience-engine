"""
Table A of the brief: every relevant public post, with or without comments.

The analysis of comments needs posts that have comments, but question 1 of the brief ("which
content attracts attention?") is about all posts: a brand video with 50,000 views and zero
comments is itself a finding (attention without conversation). This step keeps every post that
is a brand's own upload or names the brand in its title, minus Indian and other foreign videos.

Columns follow Table A in the project brief: post_id, brand, platform, campaign, content_type,
product_category, likes, comments_count, shares (not available from the YouTube API), views,
days_since_post, plus post_type, format, url and collection date for provenance.

Run after content.py:  python src/engine/posts.py
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "src" / "live"))
from content import content_type  # noqa: E402
from collect import DROP_BRANDS, FOREIGN, INDIA, TITLE_KEY  # noqa: E402

CAMPAIGNS = [  # first match wins, checked against the title
    ("Eid / Ramadan", r"\beid|ramzan|ramadan|chaand raat|chand raat"),
    ("Wedding season", r"wedding|bridal|shadi|barat|mehndi|walima"),
    ("11.11 / Black Friday", r"11\.11|12\.12|black friday|white friday|blessed friday"),
    ("Sale / discount", r"\bsale\b|% ?off|discount|clearance|flat \d+|up ?to \d+"),
    ("Winter collection", r"winter"),
    ("Summer collection", r"summer"),
    ("Independence Day", r"14 august|azadi|independence"),
    ("Back to school", r"school|back to"),
]
CATEGORIES = [
    ("Sandals & chappals", r"sandal|chappal|chappel|slide|flip ?flop|kolhapuri|peshawari"),
    ("Sneakers & joggers", r"sneaker|jogger|running|sports? shoe|trainer|walking shoe"),
    ("Heels & pumps", r"heel|pump|stiletto|wedge|platform"),
    ("Khussa & traditional", r"khussa|kussa|nagra|traditional"),
    ("Formal & loafers", r"formal|loafer|moccasin|oxford|derby|brogue|office shoe|dress shoe"),
    ("Boots", r"\bboot"),
    ("Kids' shoes", r"\bkid|child|baby|school shoe"),
    ("Slippers", r"slipper|home shoe"),
]


def first_match(title, rules, default):
    t = str(title).lower()
    for name, pat in rules:
        if re.search(pat, t):
            return name
    return default


def main():
    vids = pd.read_csv(RAW / "videos.csv")
    vids = vids.drop_duplicates("video_id")
    t = vids.title.astype(str).str.lower()
    names_brand = pd.Series([any(k in x for k in TITLE_KEY.get(b, [str(b).lower()])) for x, b in zip(t, vids.brand)], index=vids.index)
    indian = (vids.channel_country.fillna("") == "IN") | t.apply(lambda x: any(w in x for w in INDIA))
    foreign = t.apply(lambda x: any(w in x for w in FOREIGN + ["adidas originals", "nike air max", "air jordan"]))
    keep = ((vids.source == "official") | names_brand) & ~indian & ~foreign & ~vids.brand.isin(DROP_BRANDS)
    p = vids[keep].copy()
    p["comments"] = p.comments.abs()          # -1 marks "fetch again", not a real count
    collected = pd.to_datetime(p.collected_on)
    a = pd.DataFrame({
        "post_id": p.video_id, "brand": p.brand, "platform": "YouTube",
        "post_type": np.where(p.source == "official", "Brand's own post", "Creator / influencer post"),
        "campaign": p.title.apply(lambda x: first_match(x, CAMPAIGNS, "No campaign named")),
        "content_type": p.title.apply(content_type),
        "product_category": p.title.apply(lambda x: first_match(x, CATEGORIES, "Footwear (general)")),
        "format": p.format, "likes": p.likes, "comments_count": p.comments, "shares": "not available (YouTube API)",
        "views": p.views, "days_since_post": (collected - pd.to_datetime(p.published)).dt.days.clip(lower=0),
        "title": p.title, "channel": p.channel, "url": p.url, "published": p.published, "collected_on": p.collected_on,
    })
    a.to_csv(OUT / "table_a_posts.csv", index=False)

    # question 1 on every post: attention (views, likes) and conversation (comments) by content type
    a["likes_per_1k"] = (a.likes / a.views.clip(lower=1) * 1000).where(a.likes > 0)
    a["silent"] = a.comments_count == 0
    q1 = a[a.views >= 100].groupby(["post_type", "content_type"]).agg(
        posts=("post_id", "size"), median_views=("views", "median"), median_likes_per_1k=("likes_per_1k", "median"),
        share_with_no_comments=("silent", "mean")).reset_index().sort_values(["post_type", "posts"], ascending=[True, False])
    q1.to_csv(OUT / "content_all_posts.csv", index=False)
    print(f"Table A: {len(a):,} posts ({int((a.comments_count > 0).sum()):,} with comments) | "
          f"campaigns named: {int((a.campaign != 'No campaign named').sum()):,} | "
          f"brand posts with no comments: {a[a.post_type == "Brand's own post"].silent.mean():.0%}")


if __name__ == "__main__":
    main()
