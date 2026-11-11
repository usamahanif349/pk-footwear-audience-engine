"""
Big Data benchmark: the comment pipeline in pandas vs Apache Spark (PySpark).

Pipeline (same in both engines):
  1. read comments from CSV
  2. label each comment's main need with the word lists (11 regex groups, priority order)
  3. roll up: comments per brand x need, and the share of buying questions per video
The real data (6,767 comments) is copied over and over to reach larger sizes, as a
stand-in for a brand collecting comments across all platforms for a few years.

Run in Google Colab (needs Java, which Colab has):
    !git clone https://github.com/usamahanif349/pk-footwear-audience-engine
    %cd pk-footwear-audience-engine
    !pip -q install pyspark
    !python src/bigdata/benchmark.py
Writes data/processed/benchmark.csv
"""
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "engine"))
from lexicon import HIGH_INTENT, NEED_ORDER, NEED_PATTERNS  # noqa: E402

SIZES = [int(x) for x in os.environ.get("SIZES", "6767,100000,1000000,3000000").split(",")]
TMP = Path("/tmp/bench")
NEED_REGEX = {k: "(?i)(?:" + "|".join(f"(?:{p})" for p in NEED_PATTERNS[k]) + ")" for k in NEED_ORDER}


def make_file(n):
    src = pd.read_csv(ROOT / "data" / "processed" / "comments_labeled.csv", usecols=["comment_id", "video_id", "brand", "text"])
    reps = int(np.ceil(n / len(src)))
    df = pd.concat([src] * reps, ignore_index=True).iloc[:n]
    df["comment_id"] = df.comment_id + "_" + (df.index // len(src)).astype(str)
    TMP.mkdir(exist_ok=True)
    path = TMP / f"comments_{n}.csv"
    df.to_csv(path, index=False)
    return path


def run_pandas(path):
    t0 = time.time()
    df = pd.read_csv(path)
    text = df.text.fillna("").astype(str)
    conds = [text.str.contains(NEED_REGEX[k][4:], case=False, regex=True) for k in NEED_ORDER]
    df["need"] = np.select(conds, NEED_ORDER, default="other")
    by_brand = df.groupby(["brand", "need"]).size()
    per_video = df.assign(hi=df.need.isin(HIGH_INTENT)).groupby("video_id").hi.mean()
    secs = time.time() - t0
    return secs, by_brand, per_video


def run_spark(spark, path):
    from pyspark.sql import functions as F
    t0 = time.time()
    df = spark.read.csv(str(path), header=True, multiLine=True, escape='"')
    text = F.coalesce(F.col("text"), F.lit(""))
    need = F.lit("other")
    for k in reversed(NEED_ORDER):  # build the chain so the first need in NEED_ORDER wins
        need = F.when(text.rlike(NEED_REGEX[k]), F.lit(k)).otherwise(need)
    df = df.withColumn("need", need)
    by_brand = df.groupBy("brand", "need").count().toPandas().set_index(["brand", "need"])["count"]
    per_video = (df.withColumn("hi", F.col("need").isin(list(HIGH_INTENT)).cast("double"))
                   .groupBy("video_id").agg(F.avg("hi").alias("hi")).toPandas())
    secs = time.time() - t0
    return secs, by_brand, per_video


def main():
    from pyspark.sql import SparkSession
    spark = (SparkSession.builder.master("local[*]").appName("audience-benchmark")
             .config("spark.driver.memory", "8g").config("spark.sql.shuffle.partitions", "8").getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    rows = []
    for n in SIZES:
        path = make_file(n)
        p_secs, p_brand, _ = run_pandas(path)
        s_secs, s_brand, _ = run_spark(spark, path)
        both = pd.concat([p_brand.rename("pandas"), s_brand.rename("spark")], axis=1).fillna(0)
        agree = 1 - (both.pandas - both.spark).abs().sum() / (2 * both.pandas.sum())
        rows += [dict(engine="Pandas", rows=n, seconds=round(p_secs, 2)),
                 dict(engine="Spark", rows=n, seconds=round(s_secs, 2), labels_agree_with_pandas=round(agree, 4))]
        print(f"{n:>10,} rows | pandas {p_secs:7.1f}s | spark {s_secs:7.1f}s | label agreement {agree:.2%}")
        path.unlink()
    out = pd.DataFrame(rows)
    out["machine"] = f"Google Colab, {os.cpu_count()} CPU cores, Spark local mode"
    out.to_csv(ROOT / "data" / "processed" / "benchmark.csv", index=False)
    print(out)
    spark.stop()


if __name__ == "__main__":
    main()
