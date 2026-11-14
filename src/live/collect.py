"""
Collect and clean YouTube data for the live Joota Pulse app (same cleaning rules as the
12 Nov 2026 Colab collection in notebooks/01_collect_youtube_colab.py).

Version 2 (grows the data run by run, safely within YouTube's free 10,000 units a day):
  * an archive of every comment ever collected (state/comments_archive.csv.gz), so a run that
    stops early at the daily limit never loses data; new comments are added, old ones kept
  * a unit budget: searches stop well before the limit, comment collection stops cleanly at it
  * a bank of search terms per brand, rotated run by run (state/search_cursor.json)
  * cheap depth: the recent uploads of creators who already review our brands are scanned
    for more videos about the brands (1 unit per 50 videos)
  * comments are re-fetched only for videos whose comment count changed
The first archive starts from the 12 Nov 2026 collection in data/raw/.
"""
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from privacy import redact  # noqa: E402

SEARCH_NAME = {"Borjan": "Borjan", "Servis": "Servis", "Ndure": "Ndure", "Stylo": "Stylo",
               "Bata Pakistan": "Bata", "Metro Shoes": "Metro", "Hush Puppies Pakistan": "Hush Puppies",
               "Insignia": "Insignia", "ECS Shoes": "ECS", "Unze London": "Unze London", "Walkeaze": "Walkeaze",
               "Starlet": "Starlet"}
TITLE_KEY = {"Borjan": ["borjan"], "Servis": ["servis"], "Ndure": ["ndure"], "Stylo": ["stylo"],
             "Bata Pakistan": ["bata"], "Metro Shoes": ["metro"], "Hush Puppies Pakistan": ["hush pup", "hushpup", "hush pap"],
             "Insignia": ["insignia"], "ECS Shoes": ["ecs"], "Unze London": ["unze"], "Walkeaze": ["walkeaze", "walk eaze"],
             "Starlet": ["starlet"]}
# brand words that also mean other things (Metro cash & carry, Opel Insignia, Stylo pens...): a creator video
# found by scanning uploads must also mention footwear before it counts for these brands
AMBIGUOUS = {"Stylo", "Metro Shoes", "Insignia", "ECS Shoes", "Starlet", "Bata Pakistan"}
SHOE_WORDS = ["shoe", "joota", "jutay", "jootay", "sandal", "chappal", "sneaker", "heel", "slipper", "khussa", "footwear",
              "jogger", "loafer", "moccasin", "peshawari", "kolhapuri", "pumps", "flats", "boots"]
OFFICIAL_OK = ["Borjan", "Servis", "Ndure", "Stylo", "Metro Shoes", "Hush Puppies Pakistan", "Insignia",
               "Unze London", "Walkeaze", "Starlet"]
DROP_BRANDS = ["Bata Pakistan"]          # Bata's channel is Bata India, so Bata is left out
QUERY_BANK = ["shoes sale", "shoes review unboxing", "shoes new collection", "shoes haul", "eid collection shoes",
              "wedding shoes", "sandals", "joggers", "sneakers", "chappal", "ladies shoes", "men shoes", "kids shoes",
              "winter collection shoes", "shoes price", "sale 50% off", "shoes try on", "outlet visit"]
SEARCH_COST, UNIT_LIMIT, COMMENT_RESERVE = 100, 9000, 3000
INDIA = ["india", "mumbai", "delhi", "amazon", "flipkart", "myntra", "meesho", "₹", "kolkata", "bangalore"]
FOREIGN = ["singapore", "ofw", "philippine", "malaysia", "indonesia", "ghana", "nigeria", "smriti", "karthik"]
ROMAN_URDU = set("""hai hain he ha ki ka ke k ko se me mein main mai mera meri ye yeh wo woh kya kia kyun
nahi nai nhi bohat bahut bht boht acha achi achay achhe ap aap apka apki kitne kitni kitna kab kahan
kaha krna karna krdo kardo kar kr raha rahi rahe hota hoti hoga gaya gayi diya dena lena chahiye
bhai bhi sath saath plz pls price qeemat wala wali wale yar yaar kese kaise kon konsa konsi konsy
abhi sirf zyada ziada sasta mehenga mehnga bilkul mashallah mashaallah masha allah wah zabardast zbrdst
bohot bahot kitny kitnay hy hay hn ni nae haan han ji jee g tou to tm tum hum ham app kidr kidhar idhar
udhar milega milegi milay mile milta milti dikhao dikhaye bataye batain btain btao bta lagta lagti lag
achy achey achaa pyara pyari piyari khubsurat khoobsurat zabardust sahi galat ghalat tak din dinon rupay
rupees walay chahye chahiay khareed khareedna lyna lyni kis kisi koi kuch bhot sb sab sare saray""".split())


def iso_seconds(d):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    return sum(int(x or 0) * k for x, k in zip(m.groups(), (3600, 60, 1))) if m else 0


def anon(channel_id):
    return hashlib.sha256((channel_id or "").encode()).hexdigest()[:12]


def lang_of(t):
    from langdetect import detect_langs, DetectorFactory
    DetectorFactory.seed = 0
    t = str(t).strip()
    if not t or t == "nan":
        return "empty"
    if re.search(r"[؀-ۿ]", t):
        return "urdu"
    words = re.findall(r"[a-zA-Z']+", t.lower())
    if not words:
        return "emoji/symbols"
    if any(w in ROMAN_URDU for w in words):
        return "roman_urdu"
    if len(words) < 4:
        return "short_unclear"
    try:
        best = detect_langs(t)[0]
        if best.lang == "en":
            return "english"
        return "foreign" if best.prob > 0.9 else "short_unclear"
    except Exception:
        return "short_unclear"


class OutOfBudget(Exception):
    pass


class Budget:
    """Counts YouTube API units and stops before the daily free limit."""
    def __init__(self, limit=UNIT_LIMIT):
        self.limit, self.used = limit, 0

    def call(self, request, cost=1):
        if self.used + cost > self.limit:
            raise OutOfBudget
        try:
            r = request.execute()
        except Exception as e:  # quota errors mean the day's units are gone
            if "quota" in str(e).lower():
                self.used = self.limit
                raise OutOfBudget
            raise
        self.used += cost
        return r


def mentions(title, brand, strict):
    t = title.lower()
    hit = any(k in t for k in TITLE_KEY[brand])
    if hit and strict and brand in AMBIGUOUS:
        hit = any(w in t for w in SHOE_WORDS)
    return hit


def brand_in_title(title):
    for b in TITLE_KEY:
        if b not in DROP_BRANDS and mentions(title, b, strict=True):
            return b
    return None


def find_videos(yt, budget, known, state):
    """video_id -> (brand, source). Known videos first (free), then brand channels, creator uploads, new searches."""
    found = {r.video_id: (r.brand, r.source) for r in known.itertuples()}
    chan_path = state / "channels.json"
    chans = json.loads(chan_path.read_text()) if chan_path.exists() else {}
    log = dict(official=0, creator_scan=0, search=0, searches_done=0)
    try:
        # 1. each brand's own channel: id cached after the first lookup, uploads cost 1 unit per 50 videos
        for brand in OFFICIAL_OK:
            if brand not in chans:
                ch = budget.call(yt.search().list(part="snippet", q=SEARCH_NAME[brand] + " shoes official", type="channel",
                                                  maxResults=1), SEARCH_COST)["items"]
                ok = ch and any(k in ch[0]["snippet"]["title"].lower().replace(" ", "") for k in
                                [x.replace(" ", "") for x in TITLE_KEY[brand]])
                chans[brand] = ch[0]["snippet"]["channelId"] if ok else ""
            if not chans[brand]:
                continue
            uploads, token, n = "UU" + chans[brand][2:], None, 0
            while n < 300:
                try:
                    r = budget.call(yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=token))
                except OutOfBudget:
                    raise
                except Exception:
                    break
                for x in r["items"]:
                    if x["contentDetails"]["videoId"] not in found:
                        log["official"] += 1
                    found[x["contentDetails"]["videoId"]] = (brand, "official")
                n += len(r["items"])
                token = r.get("nextPageToken")
                if not token:
                    break
        # 2. creators who already review our brands: scan their latest 100 uploads for more brand videos
        creators = known[known.source == "creator"]
        cids = creators.channel_id.dropna().unique().tolist() if "channel_id" in creators else []
        for cid in cids:
            if budget.used > budget.limit - COMMENT_RESERVE - 1500:
                break
            token = None
            for _ in range(2):
                try:
                    r = budget.call(yt.playlistItems().list(part="snippet", playlistId="UU" + cid[2:], maxResults=50, pageToken=token))
                except OutOfBudget:
                    raise
                except Exception:
                    break
                for x in r["items"]:
                    vid = x["snippet"]["resourceId"]["videoId"]
                    b = brand_in_title(x["snippet"]["title"])
                    if b and vid not in found:
                        found[vid] = (b, "creator")
                        log["creator_scan"] += 1
                token = r.get("nextPageToken")
                if not token:
                    break
        # 3. new searches, taking the next terms from each brand's bank, round-robin across brands
        cur_path = state / "search_cursor.json"
        cursor = json.loads(cur_path.read_text()) if cur_path.exists() else {}
        brands = [b for b in SEARCH_NAME if b not in DROP_BRANDS]
        while budget.used + SEARCH_COST <= budget.limit - COMMENT_RESERVE:
            progressed = False
            for brand in brands:
                if budget.used + SEARCH_COST > budget.limit - COMMENT_RESERVE:
                    break
                k = cursor.get(brand, 0)
                q = QUERY_BANK[k % len(QUERY_BANK)]
                r = budget.call(yt.search().list(part="snippet", q=f"{SEARCH_NAME[brand]} {q}", type="video", maxResults=50,
                                                 regionCode="PK"), SEARCH_COST)
                for x in r["items"]:
                    if x["id"]["videoId"] not in found:
                        found[x["id"]["videoId"]] = (brand, "creator")
                        log["search"] += 1
                cursor[brand] = k + 1
                log["searches_done"] += 1
                progressed = True
            if not progressed or all(cursor.get(b, 0) >= len(QUERY_BANK) * 4 for b in brands):
                break
        cur_path.write_text(json.dumps(cursor, indent=1))
    except OutOfBudget:
        pass
    chan_path.write_text(json.dumps(chans, indent=1))
    print("find_videos:", log, "units used:", budget.used, flush=True)
    return found


def video_details(yt, budget, found, today):
    ids, rows = list(found), []
    for i in range(0, len(ids), 50):
        try:
            r = budget.call(yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50])))
        except OutOfBudget:
            break
        for v in r["items"]:
            brand, source = found[v["id"]]
            sn, st = v["snippet"], v["statistics"]
            secs = iso_seconds(v["contentDetails"].get("duration"))
            rows.append(dict(video_id=v["id"], brand=brand, source=source, title=sn["title"], channel=sn["channelTitle"],
                             channel_id=sn["channelId"], published=sn["publishedAt"][:10],
                             format="Short" if secs <= 60 or "#short" in sn["title"].lower() else "Video",
                             content_type="", duration_s=secs, views=int(st.get("viewCount", 0)),
                             likes=int(st.get("likeCount", 0)), comments=int(st.get("commentCount", 0)),
                             url="https://www.youtube.com/watch?v=" + v["id"], collected_on=today))
    cols = ["video_id", "brand", "source", "title", "channel", "channel_id", "published", "format", "content_type",
            "duration_s", "views", "likes", "comments", "url", "collected_on"]
    vids = pd.DataFrame(rows, columns=cols)
    ch_ids, country = vids.channel_id.unique().tolist(), {}
    for i in range(0, len(ch_ids), 50):
        try:
            r = budget.call(yt.channels().list(part="snippet", id=",".join(ch_ids[i:i + 50])))
        except OutOfBudget:
            break
        for c in r["items"]:
            country[c["id"]] = c["snippet"].get("country", "")
    vids["channel_country"] = vids.channel_id.map(country).fillna("")
    return vids


def keep_videos(vids):
    title = vids.title.str.lower()
    names_brand = pd.Series([any(k in t for k in TITLE_KEY[b]) for t, b in zip(title, vids.brand)], index=vids.index)
    indian = (vids.channel_country == "IN") | title.apply(lambda t: any(w in t for w in INDIA))
    return vids[((vids.source == "official") | names_brand) & ~indian & (vids.comments > 0)].reset_index(drop=True)


def comments(yt, budget, vids, today, skip):
    """Fetch comments for kept videos, except those in `skip` (comment count unchanged since the archive).
    Returns (comments, set of videos fully fetched). Stops cleanly when the unit budget runs out."""
    owner = dict(zip(vids.video_id, vids.channel_id))
    rows, done = [], set()
    todo = vids[~vids.video_id.isin(skip)].sort_values("comments")   # small videos first: most videos per unit
    for vid, brand in zip(todo.video_id, todo.brand):
        token, got = None, []
        try:
            while True:
                r = budget.call(yt.commentThreads().list(part="snippet,replies", videoId=vid, maxResults=100,
                                                         textFormat="plainText", pageToken=token))
                for t in r["items"]:
                    items = [(t["snippet"]["topLevelComment"], False)] + [(c, True) for c in t.get("replies", {}).get("comments", [])]
                    for c, is_reply in items:
                        sn = c["snippet"]
                        author_ch = sn.get("authorChannelId", {}).get("value", "")
                        got.append(dict(comment_id=c["id"], video_id=vid, brand=brand, text=redact(sn["textDisplay"]),
                                        likes=sn.get("likeCount", 0), published=sn["publishedAt"][:10], is_reply=is_reply,
                                        brand_reply=(author_ch == owner[vid]), author=anon(author_ch)))
                token = r.get("nextPageToken")
                if not token:
                    break
        except OutOfBudget:
            break
        except Exception:
            pass   # comments turned off or video removed
        rows += got
        done.add(vid)
    com = pd.DataFrame(rows, columns=["comment_id", "video_id", "brand", "text", "likes", "published", "is_reply",
                                      "brand_reply", "author"]).drop_duplicates("comment_id")
    com["collected_on"] = today
    return com, done


def load_archive(state):
    """Comment and video archives; the first time, start from the 12 Nov 2026 collection."""
    cpath, vpath = state / "comments_archive.csv.gz", state / "videos_archive.csv.gz"
    if cpath.exists() and vpath.exists():
        return pd.read_csv(cpath), pd.read_csv(vpath)
    raw = Path(__file__).resolve().parents[2] / "data" / "raw"
    com, vids = pd.read_csv(raw / "comments.csv"), pd.read_csv(raw / "videos.csv")
    lang = pd.read_csv(raw / "comments_clean.csv", usecols=["comment_id", "lang"])
    com = com.merge(lang, on="comment_id", how="left")
    com["lang"] = com["lang"].fillna(com.text.apply(lang_of) if com["lang"].isna().any() else "")
    return com, vids


def collect(api_key, known, state, limit=UNIT_LIMIT):
    """Returns (videos_raw, comments_raw, videos_clean, comments_clean, stats) and updates the archives in `state`."""
    from googleapiclient.discovery import build
    yt = build("youtube", "v3", developerKey=api_key, cache_discovery=False)
    budget, today = Budget(limit), str(dt.date.today())
    arch_com, arch_vid = load_archive(state)
    known = pd.concat([known, arch_vid[["video_id", "brand", "source", "channel_id"]]]).drop_duplicates("video_id")
    found = find_videos(yt, budget, known, state)
    vids_all = video_details(yt, budget, found, today)
    vids = keep_videos(vids_all)
    # comments: skip videos whose comment count has not changed since they were archived
    prev = dict(zip(arch_vid.video_id, arch_vid.comments))
    in_arch = set(arch_com.video_id)
    skip = {v for v, n in zip(vids.video_id, vids.comments) if v in in_arch and prev.get(v) == n}
    new, done = comments(yt, budget, vids, today, skip)
    new["lang"] = new.text.apply(lang_of) if len(new) else []
    # merge: fully re-fetched videos replace their archived comments; everything else is kept
    com = pd.concat([arch_com[~arch_com.video_id.isin(done)], new], ignore_index=True).drop_duplicates("comment_id", keep="last")
    vid_arch = pd.concat([arch_vid[~arch_vid.video_id.isin(vids_all.video_id)], vids_all], ignore_index=True)
    vid_arch.loc[vid_arch.video_id.isin(set(vids.video_id) - done - skip), "comments"] = -1   # fetch again next run
    com.to_csv(state / "comments_archive.csv.gz", index=False)
    vid_arch.to_csv(state / "videos_archive.csv.gz", index=False)
    vids, com, vids_clean, clean = build_tables(com, vid_arch)
    vids = vid_arch.assign(comments=vid_arch.comments.abs())       # all posts found, for Table A
    stats = dict(videos_found=len(found), videos_kept=len(vids_clean), comments_raw=len(com), comments_clean=len(clean),
                 new_comments=len(new), videos_fetched=len(done), units_used=budget.used)
    print("collect:", stats, flush=True)
    return vids, com, vids_clean, clean, stats


def build_tables(com, vid_arch):
    """From the archives to the cleaned tables the engine uses: every kept video we have comments for."""
    vids = keep_videos(vid_arch[vid_arch.video_id.isin(set(com.video_id))].assign(comments=lambda d: d.comments.abs().clip(lower=1)))
    com = com[com.video_id.isin(vids.video_id)]
    com = com.drop(columns=["source", "channel", "channel_country", "title"], errors="ignore") \
             .merge(vids[["video_id", "source", "channel", "channel_country", "title"]], on="video_id", how="left")
    drop_video = com.brand.isin(DROP_BRANDS) | com.title.str.lower().apply(lambda t: any(w in t for w in FOREIGN))
    clean = com[~drop_video & ~com.lang.isin(["empty", "foreign"])].reset_index(drop=True)
    vids_clean = vids[~vids.brand.isin(DROP_BRANDS)].reset_index(drop=True)
    return vids, com, vids_clean, clean


def from_archive(state):
    """Rebuild everything from the saved archives without calling YouTube (0 units)."""
    arch_com, arch_vid = load_archive(state)
    vids, com, vids_clean, clean = build_tables(arch_com, arch_vid)
    vids = arch_vid.assign(comments=arch_vid.comments.abs())
    stats = dict(videos_found=len(arch_vid), videos_kept=len(vids_clean), comments_raw=len(com), comments_clean=len(clean),
                 new_comments=0, videos_fetched=0, units_used=0)
    print("rebuilt from archive:", stats, flush=True)
    return vids, com, vids_clean, clean, stats
