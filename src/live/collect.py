"""
Collect and clean YouTube data for the live Joota Pulse app (same rules as the
12 Nov 2026 Colab collection in notebooks/01_collect_youtube_colab.py).

Every run re-crawls everything: new search results, the brands' own channels and every
video seen in earlier runs, so new comments and new brand replies are picked up.
Uses about 6,000 of the free 10,000 YouTube API units per day.
"""
import datetime as dt
import hashlib
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from privacy import redact  # noqa: E402

SEARCH_NAME = {"Borjan": "Borjan", "Servis": "Servis", "Ndure": "Ndure", "Stylo": "Stylo",
               "Bata Pakistan": "Bata", "Metro Shoes": "Metro", "Hush Puppies Pakistan": "Hush Puppies",
               "Insignia": "Insignia", "ECS Shoes": "ECS"}
TITLE_KEY = {"Borjan": ["borjan"], "Servis": ["servis"], "Ndure": ["ndure"], "Stylo": ["stylo"],
             "Bata Pakistan": ["bata"], "Metro Shoes": ["metro"], "Hush Puppies Pakistan": ["hush pup", "hushpup", "hush pap"],
             "Insignia": ["insignia"], "ECS Shoes": ["ecs"]}
OFFICIAL_OK = ["Borjan", "Servis", "Ndure", "Stylo", "Metro Shoes", "Hush Puppies Pakistan", "Insignia"]
DROP_BRANDS = ["Bata Pakistan"]          # Bata's channel is Bata India, so Bata is left out
QUERIES = ["shoes sale", "shoes review unboxing", "shoes new collection", "shoes haul"]
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


def find_videos(yt, known):
    """video_id -> (brand, source). `known` is a DataFrame of videos kept in earlier runs."""
    found = {}
    for brand, name in SEARCH_NAME.items():
        if brand in DROP_BRANDS:
            continue
        for q in QUERIES:
            r = yt.search().list(part="snippet", q=f"{name} {q}", type="video", maxResults=50, regionCode="PK").execute()
            for x in r["items"]:
                found.setdefault(x["id"]["videoId"], (brand, "creator"))
        if brand in OFFICIAL_OK:
            ch = yt.search().list(part="snippet", q=name + " shoes official", type="channel", maxResults=1).execute()["items"]
            if ch:
                info = yt.channels().list(part="contentDetails", id=ch[0]["snippet"]["channelId"]).execute()["items"][0]
                uploads, token, n = info["contentDetails"]["relatedPlaylists"]["uploads"], None, 0
                while n < 300:
                    r = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=token).execute()
                    for x in r["items"]:
                        found[x["contentDetails"]["videoId"]] = (brand, "official")
                    n += len(r["items"])
                    token = r.get("nextPageToken")
                    if not token:
                        break
    for r in known.itertuples():                     # keep re-checking videos found before
        found.setdefault(r.video_id, (r.brand, r.source))
    return found


def video_details(yt, found, today):
    ids, rows = list(found), []
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50])).execute()
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
    vids = pd.DataFrame(rows)
    ch_ids, country = vids.channel_id.unique().tolist(), {}
    for i in range(0, len(ch_ids), 50):
        r = yt.channels().list(part="snippet", id=",".join(ch_ids[i:i + 50])).execute()
        for c in r["items"]:
            country[c["id"]] = c["snippet"].get("country", "")
    vids["channel_country"] = vids.channel_id.map(country).fillna("")
    return vids


def keep_videos(vids):
    title = vids.title.str.lower()
    names_brand = pd.Series([any(k in t for k in TITLE_KEY[b]) for t, b in zip(title, vids.brand)], index=vids.index)
    indian = (vids.channel_country == "IN") | title.apply(lambda t: any(w in t for w in INDIA))
    return vids[((vids.source == "official") | names_brand) & ~indian & (vids.comments > 0)].reset_index(drop=True)


def comments(yt, vids, today):
    owner = dict(zip(vids.video_id, vids.channel_id))
    rows = []
    for vid, brand in zip(vids.video_id, vids.brand):
        token = None
        try:
            while True:
                r = yt.commentThreads().list(part="snippet,replies", videoId=vid, maxResults=100,
                                             textFormat="plainText", pageToken=token).execute()
                for t in r["items"]:
                    items = [(t["snippet"]["topLevelComment"], False)] + [(c, True) for c in t.get("replies", {}).get("comments", [])]
                    for c, is_reply in items:
                        s = c["snippet"]
                        author_ch = s.get("authorChannelId", {}).get("value", "")
                        rows.append(dict(comment_id=c["id"], video_id=vid, brand=brand, text=redact(s["textDisplay"]),
                                         likes=s.get("likeCount", 0), published=s["publishedAt"][:10], is_reply=is_reply,
                                         brand_reply=(author_ch == owner[vid]), author=anon(author_ch)))
                token = r.get("nextPageToken")
                if not token:
                    break
        except Exception:
            pass   # comments turned off or video removed
    com = pd.DataFrame(rows).drop_duplicates("comment_id")
    com["collected_on"] = today
    return com


def collect(api_key, known):
    """Returns (videos_raw, comments_raw, videos_clean, comments_clean, stats)."""
    from googleapiclient.discovery import build
    yt = build("youtube", "v3", developerKey=api_key, cache_discovery=False)
    today = str(dt.date.today())
    found = find_videos(yt, known)
    vids_all = video_details(yt, found, today)
    vids = keep_videos(vids_all)
    com = comments(yt, vids, today)
    com["lang"] = com.text.apply(lang_of)
    com = com.merge(vids[["video_id", "source", "channel", "channel_country", "title"]], on="video_id", how="left")
    drop_video = com.brand.isin(DROP_BRANDS) | com.title.str.lower().apply(lambda t: any(w in t for w in FOREIGN))
    clean = com[~drop_video & ~com.lang.isin(["empty", "foreign"])].reset_index(drop=True)
    vids_clean = vids[~vids.brand.isin(DROP_BRANDS)].reset_index(drop=True)
    stats = dict(videos_found=len(found), videos_kept=len(vids), comments_raw=len(com), comments_clean=len(clean))
    return vids, com, vids_clean, clean, stats
