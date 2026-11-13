"""
Weekly refresh for the live Joota Pulse app (run by GitHub Actions in the joota-pulse repo).

  1. collect fresh YouTube videos and comments (needs YOUTUBE_API_KEY)
  2. compute multilingual embeddings for every cleaned comment
  3. run the engine: needs.py -> content.py -> segments.py
  4. remember when each comment was first seen, and log this run's key numbers
  5. export data.json for the web app

State kept between runs (in the joota-pulse repo, folder state/):
  known_videos.csv  videos kept in any run, so they are re-checked every week
  first_seen.csv    the first run each comment appeared in ("new" leads)
  history.json      one line of key numbers per run (trend chart)

Usage:  python src/live/refresh.py --state ../state --out ../data.json [--offline]
--offline skips collection and embeddings and reuses data/raw (for testing).
"""
import argparse
import datetime as dt
import json
import os
import runpy
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW, PROC = ROOT / "data" / "raw", ROOT / "data" / "processed"
SNAPSHOT_DATE = "2026-11-12"   # the original collection used for the report
MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


def embed(com):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL)
    emb = model.encode(com.text.fillna("").astype(str).tolist(), batch_size=64, show_progress_bar=False,
                       normalize_embeddings=True)
    np.savez_compressed(RAW / "embeddings.npz", comment_id=com.comment_id.values, emb=emb.astype(np.float16))


def run_engine():
    for step in ["needs", "content", "segments"]:
        print(f"--- {step}", flush=True)
        runpy.run_path(str(ROOT / "src" / "engine" / f"{step}.py"), run_name="__main__")


def update_state(state, today, stats):
    com = pd.read_csv(PROC / "comments_labeled.csv", usecols=["comment_id"])
    path = state / "first_seen.csv"
    first = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["comment_id", "first_seen"])
    if first.empty:   # first live run: everything collected so far counts as the original snapshot
        first = pd.DataFrame({"comment_id": com.comment_id, "first_seen": SNAPSHOT_DATE})
    new = com[~com.comment_id.isin(first.comment_id)]
    first = pd.concat([first, pd.DataFrame({"comment_id": new.comment_id, "first_seen": today})], ignore_index=True)
    first.to_csv(path, index=False)
    first.to_csv(PROC / "first_seen.csv", index=False)

    vids = pd.read_csv(RAW / "videos_clean.csv", usecols=["video_id", "brand", "source"])
    kpath = state / "known_videos.csv"
    known = pd.read_csv(kpath) if kpath.exists() else vids.iloc[0:0]
    pd.concat([known, vids]).drop_duplicates("video_id").to_csv(kpath, index=False)

    (PROC / "pipeline_stats.json").write_text(json.dumps({**stats, "run_date": today}, indent=2))


def log_history(state, today, data_path):
    data = json.loads(Path(data_path).read_text())
    hpath = state / "history.json"
    hist = json.loads(hpath.read_text()) if hpath.exists() else []
    point = {"date": today, **{k: {m: data["spaces"][k][m] for m in ["comments", "buying", "waiting", "own_q", "own_answered"]}
                               for k in data["spaces"]}}
    hist = [h for h in hist if h["date"] != today] + [point]
    hpath.write_text(json.dumps(hist, indent=1))
    data["history"] = hist
    Path(data_path).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--date", default=str(dt.date.today()))
    a = ap.parse_args()
    state, today = Path(a.state), a.date
    state.mkdir(parents=True, exist_ok=True)

    if a.offline:
        stats = json.loads((state / "snapshot_stats.json").read_text()) if (state / "snapshot_stats.json").exists() else {}
    else:
        sys.path.insert(0, str(Path(__file__).parent))
        from collect import collect
        kpath = state / "known_videos.csv"
        known = pd.read_csv(kpath) if kpath.exists() else pd.DataFrame(columns=["video_id", "brand", "source"])
        vids_raw, com_raw, vids, com, stats = collect(os.environ["YOUTUBE_API_KEY"], known)
        print("collected:", stats, flush=True)
        vids_raw.to_csv(RAW / "videos.csv", index=False)
        com_raw.drop(columns=["lang", "source", "channel", "channel_country", "title"]).to_csv(RAW / "comments.csv", index=False)
        vids.to_csv(RAW / "videos_clean.csv", index=False)
        com.to_csv(RAW / "comments_clean.csv", index=False)
        embed(com)

    run_engine()
    update_state(state, today, stats)
    sys.argv = ["export.py", a.out]
    runpy.run_path(str(ROOT / "src" / "web" / "export.py"), run_name="__main__")
    log_history(state, today, a.out)
    print("refresh done:", today, flush=True)


if __name__ == "__main__":
    main()
