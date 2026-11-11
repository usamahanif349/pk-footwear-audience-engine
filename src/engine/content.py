"""
Step 2 of the engine: which content attracts attention, and which posts are unusual?

Video level. Every video gets attention metrics (views per day, likes and comments per
1,000 views) and audience metrics from its comments (share of buying questions,
complaints, ad buzz). Unusual posts are found two ways:
  * peer check: robust z-score against videos of the same format and content type
  * Isolation Forest across all videos, as a second opinion
A video is flagged when the peer check finds a large gap; the Isolation Forest score
ranks how unusual it is overall.

Run after needs.py:  python src/engine/content.py
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed"
MIN_VIEWS, MIN_COMMENTS, Z_FLAG = 500, 5, 2.5

TYPE_RULES = [  # first match wins; checked against the video title
    ("Eid / wedding campaign", r"\beid|wedding|bridal|shadi|barat|mehndi|ramzan|ramadan"),
    ("Sale announcement", r"\bsale\b|% ?off|discount|clearance|11\.11|black friday|white friday|flat \d+|upto|up to \d+"),
    ("Brand ad / campaign", r"\bad\b|\btvc\b|commercial|campaign|presents|introducing|launch"),
    ("Styling / try-on", r"styl|try ?on|outfit|matching|ootd|grwm|look\b|how to wear|pair(ed|ing)? with"),
    ("Review / unboxing", r"review|unbox|haul|honest|worth it|comparison|vs\b"),
    ("New collection", r"collection|new arrival|winter|summer|spring|autumn|new design|latest|article"),
    ("Store visit / vlog", r"outlet|mall|store|vlog|shopping|market|factory"),
]


def content_type(title):
    t = str(title).lower()
    for name, pat in TYPE_RULES:
        if re.search(pat, t):
            return name
    return "Other / untitled"


def robust_z(x, groups):
    med = x.groupby(groups).transform("median")
    mad = (x - med).abs().groupby(groups).transform("median") * 1.4826
    mad = mad.where(mad > 0, x.std())
    return (x - med) / mad


def video_table(vids, com):
    v = vids.copy()
    v["content_type"] = v.title.apply(content_type)
    v["post_type"] = np.where(v.source == "official", "Brand's own post", "Creator / influencer post")
    collected = pd.to_datetime(v.collected_on)
    v["age_days"] = (collected - pd.to_datetime(v.published)).dt.days.clip(lower=1)
    v["views_per_day"] = v.views / v.age_days
    # likes = 0 on a viewed video almost always means the owner hid the like count
    v["likes_per_1k"] = (v.likes / v.views.clip(lower=1) * 1000).where(v.likes > 0)
    v["comments_per_1k"] = v.comments / v.views.clip(lower=1) * 1000

    cust = com[~com.owner_reply]
    g = cust.groupby("video_id")
    audience = pd.DataFrame({
        "customer_comments": g.size(),
        "high_intent_share": g.intent.apply(lambda s: (s == "high").mean()),
        "complaint_share": g.need.apply(lambda s: (s == "complaint").mean()),
        "buzz_share": g.need.apply(lambda s: (s == "nostalgia_ad").mean()),
        "praise_share": g.need.apply(lambda s: s.isin(["praise_product", "general_praise", "praise_content"]).mean()),
    })
    v = v.merge(audience, left_on="video_id", right_index=True, how="left")
    v["customer_comments"] = v.customer_comments.fillna(0).astype(int)
    for c in ["high_intent_share", "complaint_share", "buzz_share", "praise_share"]:
        v[c] = v[c].fillna(0)
    return v


def content_summary(v):
    rows = []
    for keys, g in v.groupby(["platform", "format", "content_type", "post_type"]):
        rows.append(dict(zip(["platform", "format", "content_type", "post_type"], keys),
                         videos=len(g), median_views=g.views.median(), median_views_per_day=g.views_per_day.median(),
                         median_likes_per_1k=g.likes_per_1k.median(), median_comments_per_1k=g.comments_per_1k.median(),
                         customer_comments=int(g.customer_comments.sum()),
                         high_intent_share=(g.high_intent_share * g.customer_comments).sum() / max(g.customer_comments.sum(), 1)))
    return pd.DataFrame(rows).sort_values("median_views", ascending=False)


def anomalies(v):
    ok = (v.views >= MIN_VIEWS) & (v.comments >= MIN_COMMENTS)
    a = v[ok].copy()
    peer = a.format + " · " + a.content_type
    metrics = {"views_per_day": np.log1p(a.views_per_day), "likes_per_1k": np.log1p(a.likes_per_1k),
               "comments_per_1k": np.log1p(a.comments_per_1k), "high_intent_share": a.high_intent_share,
               "complaint_share": a.complaint_share}
    names = {"views_per_day": "views per day", "likes_per_1k": "likes per 1,000 views",
             "comments_per_1k": "comments per 1,000 views", "high_intent_share": "share of buying questions",
             "complaint_share": "share of complaints"}
    z = pd.DataFrame({k: robust_z(s, peer) for k, s in metrics.items()})
    # a complaint share only counts when at least 2 real complaints sit behind it
    complaints = (a.complaint_share * a.customer_comments).round()
    z.loc[complaints < 2, "complaint_share"] = 0
    m = pd.DataFrame(metrics)
    feats = StandardScaler().fit_transform(m.fillna(m.median()))
    iso = IsolationForest(n_estimators=300, contamination=0.08, random_state=0).fit(feats)
    a["isolation_score"] = -iso.score_samples(feats)
    a["isolation_flag"] = iso.predict(feats) == -1
    a["peer_group"] = peer

    reasons, direction = [], []
    for i, row in z.iterrows():
        big = row.dropna()
        big = big[big.abs() >= Z_FLAG].sort_values(key=abs, ascending=False)
        if big.empty:
            reasons.append(""); direction.append("")
            continue
        parts = []
        for k, val in big.items():
            raw = a.loc[i, k]
            med = a.loc[peer == peer[i], k].median()
            if k.endswith("share"):
                parts.append(f"{names[k]} {raw:.0%} vs {med:.0%} for similar posts")
            else:
                ratio = raw / med if med > 0 else np.inf
                parts.append(f"{names[k]} {ratio:.1f}× similar posts" if ratio >= 0.1
                             else f"{names[k]} far below similar posts ({raw:.2f} vs {med:.2f})")
        reasons.append("; ".join(parts))
        bad = ("complaint_share" in big.index and big["complaint_share"] > 0) or (big.drop("complaint_share", errors="ignore") < 0).all()
        direction.append("Investigate (underperforming or complaints)" if bad else "Learn from it (outperforming)")
    a["unusual_because"] = reasons
    a["what_to_do"] = direction
    a["peer_flag"] = a.unusual_because != ""
    flagged = a[a.peer_flag].sort_values("isolation_score", ascending=False)
    return a, flagged


def post_audience_types(v, k=4):
    """Group posts by the mix of what their commenters talk about."""
    p = v[v.customer_comments >= 10].copy()
    X = p[["high_intent_share", "complaint_share", "buzz_share", "praise_share"]].values
    km = KMeans(k, n_init=20, random_state=0).fit(X)
    p["audience_type_id"] = km.labels_
    names = {}
    for c in range(k):
        hi, co, bu, pr = km.cluster_centers_[c]
        if hi >= 0.3:
            names[c] = "Shopper posts (people asking to buy)"
        elif bu >= 0.2:
            names[c] = "Buzz posts (ads and memes people talk about)"
        elif pr >= 0.6:
            names[c] = "Fan posts (mostly praise)"
        elif pr >= 0.35:
            names[c] = "Praise-led posts (some questions)"
        else:
            names[c] = "Chatter posts (off-topic talk)"
    p["audience_type"] = p.audience_type_id.map(names)
    centres = pd.DataFrame(km.cluster_centers_, columns=["high_intent_share", "complaint_share", "buzz_share", "praise_share"])
    centres["audience_type"] = [names[c] for c in range(k)]
    centres["posts"] = p.audience_type_id.value_counts().sort_index().values
    return p[["video_id", "audience_type"]], centres


def main():
    com = pd.read_csv(OUT / "comments_labeled.csv")
    vids = pd.read_csv(OUT / "videos.csv")
    if "platform" not in vids:
        vids["platform"] = "YouTube"
    v = video_table(vids, com)
    types, centres = post_audience_types(v)
    v = v.merge(types, on="video_id", how="left")
    v["audience_type"] = v.audience_type.fillna("Too few comments to tell")
    a, flagged = anomalies(v)
    v = v.merge(a[["video_id", "isolation_score", "isolation_flag", "peer_flag", "unusual_because", "what_to_do"]],
                on="video_id", how="left")
    v.to_csv(OUT / "videos_enriched.csv", index=False)
    content_summary(v).to_csv(OUT / "content_summary.csv", index=False)
    centres.to_csv(OUT / "post_audience_types.csv", index=False)
    flagged.to_csv(OUT / "unusual_posts.csv", index=False)
    print("videos:", len(v), "| checked for anomalies:", len(a), "| flagged:", len(flagged),
          "| isolation forest also flags:", int(flagged.isolation_flag.sum()))
    print(centres.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
