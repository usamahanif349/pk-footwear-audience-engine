"""
Step 1 of the engine: what does the audience want?

1. Word lists (lexicon.py) label the comments they clearly match (high precision).
2. Comments the word lists miss get a label from their nearest labelled neighbours in
   embedding space (multilingual sentence embeddings), only when the neighbours agree.
3. Discovery clustering (K-Means on embeddings) shows the natural groups in the data;
   a TF-IDF version is the baseline, so we can show embeddings group needs better.

Run: python src/engine/needs.py   (from the repo root)
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import normalized_mutual_info_score, silhouette_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score

sys.path.insert(0, str(Path(__file__).parent))
from lexicon import (HIGH_INTENT, MEDIUM_INTENT, NEED_LABEL, is_general_praise,  # noqa: E402
                     is_question, needs_of)

ROOT = Path(__file__).resolve().parents[2]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
# videos that are not about Pakistani footwear brands: other countries, or international
# sneakers whose names happen to contain our brand words ("Air Max Metro", "Insignia Blue")
FOREIGN = ["singapore", "ofw", "philippine", "malaysia", "indonesia", "ghana", "nigeria", "smriti", "karthik",
           "adidas originals", "nike air max", "air jordan"]
K_NEIGHBOURS, MIN_VOTE, MIN_SIM = 15, 0.7, 0.6


def load():
    com = pd.read_csv(RAW / "comments_clean.csv")
    vids = pd.read_csv(RAW / "videos_clean.csv")
    emb = np.load(RAW / "embeddings.npz", allow_pickle=True)
    assert (emb["comment_id"] == com.comment_id.values).all(), "embeddings out of order"
    keep_vid = ~vids.title.str.lower().apply(lambda t: any(w in t for w in FOREIGN))
    vids = vids[keep_vid & vids.video_id.isin(com.video_id)].reset_index(drop=True)
    mask = com.video_id.isin(vids.video_id).values
    return com[mask].reset_index(drop=True), vids, emb["emb"][mask].astype(np.float32)


def thread_of(comment_id):
    """Replies have ids like '<parent>.<reply>'; top-level comments are their own thread."""
    return str(comment_id).split(".")[0]


def label(com, X):
    com = com.copy()
    com["platform"] = "YouTube"
    com["owner_reply"] = com.pop("brand_reply")          # reply by whoever owns the video
    com["thread"] = com.comment_id.apply(thread_of)
    com["has_text"] = ~com.lang.isin(["emoji/symbols"])
    cust = ~com.owner_reply

    needs = com.text.apply(needs_of)
    com["all_needs"] = needs.apply(lambda n: "|".join(n))
    com["need"] = needs.str[0]
    gp = com.need.isna() & com.text.apply(is_general_praise)
    com.loc[gp, "need"] = "general_praise"
    com["label_source"] = np.where(com.need.notna(), "word list", "")

    # neighbour vote for comments the word lists missed
    train = cust & com.need.notna() & com.has_text
    todo = cust & com.need.isna() & com.has_text
    knn = KNeighborsClassifier(n_neighbors=K_NEIGHBOURS, metric="cosine", weights="distance")
    knn.fit(X[train.values], com.need[train])
    proba = knn.predict_proba(X[todo.values])
    dist, _ = knn.kneighbors(X[todo.values], n_neighbors=1)
    best = proba.argmax(1)
    ok = (proba.max(1) >= MIN_VOTE) & (1 - dist[:, 0] >= MIN_SIM)
    idx = np.where(todo.values)[0]
    com.loc[idx[ok], "need"] = knn.classes_[best[ok]]
    com.loc[idx[ok], "label_source"] = "nearest neighbours"
    com["need"] = com.need.fillna("other")
    com.loc[com.label_source == "", "label_source"] = "none"
    com.loc[com.owner_reply, "need"] = "owner_reply"

    # how consistent are the labels with the embeddings? (5-fold check on word-list labels)
    cv = cross_val_score(KNeighborsClassifier(n_neighbors=K_NEIGHBOURS, metric="cosine", weights="distance"),
                         X[train.values], com.loc[train, "need"], cv=5).mean()

    com["need_label"] = com.need.map(NEED_LABEL).fillna("Brand / creator reply")
    com["question"] = com.text.apply(is_question)
    com["intent"] = np.select(
        [com.need.isin(HIGH_INTENT), com.need.isin(MEDIUM_INTENT) | (com.question & com.need.isin(["other"]))],
        ["high", "medium"], "low")
    com.loc[com.owner_reply, "intent"] = "-"
    return com, {"knn_cv_accuracy": round(float(cv), 3), "labelled_by_word_list": int((com.label_source == "word list").sum()),
                 "labelled_by_neighbours": int((com.label_source == "nearest neighbours").sum())}


def discover(com, X):
    """Unsupervised view: which groups appear on their own? Embeddings vs TF-IDF baseline."""
    m = (~com.owner_reply & com.has_text).values
    Xm, texts, needs = X[m], com.text[m].astype(str), com.need[m]
    Xp = PCA(50, random_state=0).fit_transform(Xm)
    scores = {}
    for k in range(8, 21, 2):
        km = KMeans(k, n_init=5, random_state=0).fit(Xp)
        scores[k] = silhouette_score(Xp, km.labels_, sample_size=3000, random_state=0)
    k_best = max(scores, key=scores.get)
    km = KMeans(k_best, n_init=10, random_state=0).fit(Xp)

    tf = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=3, sublinear_tf=True).fit_transform(texts)
    km_tf = KMeans(k_best, n_init=10, random_state=0).fit(tf)
    labelled = (needs != "other").values
    nmi_emb = normalized_mutual_info_score(needs[labelled], km.labels_[labelled])
    nmi_tf = normalized_mutual_info_score(needs[labelled], km_tf.labels_[labelled])

    xy = PCA(2, random_state=0).fit_transform(Xm)
    disc = pd.DataFrame({"comment_id": com.comment_id[m].values, "cluster": km.labels_,
                         "x": xy[:, 0].round(4), "y": xy[:, 1].round(4)})
    # name each cluster by its most common need and a few typical comments
    tmp = disc.assign(need=needs.values, text=texts.values)
    names = []
    for k, g in tmp.groupby("cluster"):
        top = g.need.value_counts(normalize=True)
        centre = km.cluster_centers_[k]
        d = np.linalg.norm(Xp[(km.labels_ == k)] - centre, axis=1)
        examples = g.text.iloc[np.argsort(d)[:4]].str.replace("\n", " ").str[:60].tolist()
        names.append(dict(cluster=int(k), size=len(g), main_need=top.index[0],
                          main_need_label=NEED_LABEL.get(top.index[0], top.index[0]),
                          purity=round(float(top.iloc[0]), 3), examples=" | ".join(examples)))
    metrics = {"k": int(k_best), "silhouette_by_k": {int(a): round(float(b), 4) for a, b in scores.items()},
               "nmi_embeddings_vs_needs": round(float(nmi_emb), 3), "nmi_tfidf_vs_needs": round(float(nmi_tf), 3)}
    return disc, pd.DataFrame(names).sort_values("size", ascending=False), metrics


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    com, vids, X = load()
    com, m1 = label(com, X)
    disc, clusters, m2 = discover(com, X)
    com = com.merge(disc[["comment_id", "cluster"]], on="comment_id", how="left")
    # Table B of the brief asks for a sentiment column: derived from the topic (praise = positive,
    # complaint = negative, everything else = neutral). The project's focus is needs, not sentiment.
    com["sentiment"] = np.where(com.need.isin(["praise_product", "praise_content", "general_praise"]), "Positive",
                                np.where(com.need == "complaint", "Negative", "Neutral"))
    com.to_csv(OUT / "comments_labeled.csv", index=False)
    disc.to_csv(OUT / "cluster_map.csv", index=False)
    clusters.to_csv(OUT / "clusters.csv", index=False)
    vids.to_csv(OUT / "videos.csv", index=False)
    metrics = {**m1, **m2, "comments": len(com), "customer_comments": int((~com.owner_reply).sum()),
               "videos": len(vids)}
    (OUT / "method_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    print(com[~com.owner_reply].need_label.value_counts())


if __name__ == "__main__":
    main()
