"""
Joota Pulse: audience intelligence for Pakistani footwear brands (Big Data Project 3).

A marketing web app built on REAL public YouTube comments and video stats, collected
with the official YouTube Data API. It finds buyers waiting for a reply, the customer
groups behind the comments, the content that works and ready-to-run campaigns.

Run locally (Command Prompt):  streamlit run src\\dashboard\\app.py
"""
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "engine"))
from replies import REPLIES  # noqa: E402

PROC, ASSETS = ROOT / "data" / "processed", ROOT / "assets"
REPO_URL = "https://github.com/usamahanif349/pk-footwear-audience-engine"
P1_URL = "https://github.com/usamahanif349/pk-footwear-sentiment-analysis"
P2_URL = "https://github.com/usamahanif349/pk-footwear-budget-optimizer"
P2_APP = "https://pk-footwear-budget-optimizer.streamlit.app/"
DATA_DATE = "12 Nov 2026"
CORE = ["Borjan", "Servis", "Ndure"]
BRAND_POST, CREATOR_POST = "Brand's own post", "Creator / influencer post"

VIOLET, VIOLET_SOFT, ORANGE, GREEN, RED = "#5B4BDB", "#EEEBFF", "#F26B3A", "#12A150", "#D92D20"
INK, MUTED, LINE = "#14142B", "#6E6E85", "#ECECF3"
FONT = "Plus Jakarta Sans, Segoe UI, Helvetica Neue, Arial, sans-serif"

ASK = {  # need -> short inbox label
    "price": "Price", "availability": "Where to buy", "delivery_order": "Order & delivery",
    "contact": "Contact", "size_fit": "Size", "complaint": "Complaint"}
SEGMENT_CARD = {  # segment -> (emoji, badge, badge tone, what to do)
    "Where-can-I-buy askers": ("📍", "Ready to buy", "hot", "Pin a store locator and the order link."),
    "Price checkers": ("💰", "Ready to buy", "hot", "Show prices on screen or in a pinned comment."),
    "Deal hunters": ("🏷️", "Ready to buy", "hot", "Post sale start and end dates."),
    "Order & delivery askers": ("🚚", "Ready to buy", "hot", "Explain cash on delivery and delivery days."),
    "Contact seekers": ("📞", "Ready to buy", "hot", "Put WhatsApp and website in every description."),
    "Size & fit askers": ("📏", "Ready to buy", "hot", "Share a size guide and how each article fits."),
    "Unhappy customers": ("⚠️", "Needs care", "bad", "Reply within a day and fix it privately."),
    "Quality-conscious shoppers": ("🔍", "Considering", "warm", "Show soles and stitching up close."),
    "Product fans": ("💜", "Fans", "cool", "Retarget them with the same articles."),
    "Ad & meme crowd": ("📺", "Buzz", "cool", "Reuse the buzz in throwback content."),
    "Supporters (general praise)": ("👏", "Fans", "cool", "Thank them and point to the shop."),
}

SEG_NEED = {"Where-can-I-buy askers": {"availability"}, "Price checkers": {"price"}, "Deal hunters": {"discount_sale"},
            "Order & delivery askers": {"delivery_order"}, "Contact seekers": {"contact"}, "Size & fit askers": {"size_fit"},
            "Unhappy customers": {"complaint"}, "Quality-conscious shoppers": {"quality_comfort"},
            "Product fans": {"praise_product"}, "Ad & meme crowd": {"nostalgia_ad"},
            "Supporters (general praise)": {"general_praise", "praise_content"}}
SHORT_NEED = {"Availability / location": "Where to buy", "Price inquiry": "Price", "Discount / sale": "Sales & discounts",
              "Delivery / how to order": "Ordering & delivery", "Contact / link request": "Contact details",
              "Size / fit": "Size & fit", "Quality / comfort": "Quality & comfort", "Complaint / problem": "Complaints",
              "Ad nostalgia / celebrity buzz": "Ad nostalgia", "Product praise / wants it": "Product love"}

st.set_page_config(page_title="Joota Pulse", page_icon=str(ASSETS / "logo_icon.png"), layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp, .stMarkdown, button, input, select, textarea {
  font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif !important;}
.stApp {background: #F7F7FB;}
.block-container {padding-top: 2.6rem; padding-bottom: 3rem; max-width: 1240px;}
header[data-testid="stHeader"] {background: transparent;}
[data-testid="stSidebar"] {background: #FFFFFF; border-right: 1px solid #ECECF3;}
[data-testid="stSidebarNav"] a span {font-weight: 500;}
h1, h2, h3, h4 {font-family: 'Plus Jakarta Sans', sans-serif !important; letter-spacing: -0.02em;}

.top {display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap; margin-bottom: 18px;}
.top h1 {font-size: 1.75rem; font-weight: 800; color: #14142B; margin: 0; padding: 0; line-height: 1.2;}
.top p {color: #6E6E85; margin: 6px 0 0; font-size: .98rem;}
.ws {display: inline-flex; align-items: center; gap: 8px; background: #FFFFFF; border: 1px solid #ECECF3;
  border-radius: 999px; padding: 6px 14px 6px 8px; font-size: .86rem; color: #14142B; font-weight: 600;}
.ws i {width: 22px; height: 22px; border-radius: 50%; background: #5B4BDB; color: #fff; font-style: normal;
  display: inline-grid; place-items: center; font-size: .7rem;}

[class*="st-key-box_"] {background: #FFFFFF; border: 1px solid #ECECF3; border-radius: 18px; padding: 20px 22px 16px;}
.bh {display: flex; justify-content: space-between; align-items: baseline; gap: 10px; margin-bottom: 10px;}
.bh h3 {font-size: 1.05rem; font-weight: 700; color: #14142B; margin: 0; padding: 0;}
.bh span {color: #6E6E85; font-size: .84rem;}

.kpis {display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 16px;}
.kpi {background: #FFFFFF; border: 1px solid #ECECF3; border-radius: 18px; padding: 18px 20px;}
.kpi.money {background: linear-gradient(135deg, #5B4BDB 0%, #7B5CF0 100%); border: 0;}
.kpi .l {color: #6E6E85; font-size: .84rem; font-weight: 600;}
.kpi .v {color: #14142B; font-size: 1.9rem; font-weight: 800; line-height: 1.15; margin-top: 8px; letter-spacing: -0.03em;}
.kpi .n {color: #6E6E85; font-size: .82rem; margin-top: 6px;}
.kpi.money .l, .kpi.money .n {color: #DCD6FF;}
.kpi.money .v {color: #FFFFFF;}
.up {color: #12A150; font-weight: 700;} .down {color: #D92D20; font-weight: 700;}

.todo {display: flex; gap: 14px; align-items: flex-start; padding: 14px 0; border-bottom: 1px solid #F1F1F6;}
.todo:last-child {border-bottom: 0;}
.todo .num {flex: none; width: 30px; height: 30px; border-radius: 10px; background: #EEEBFF; color: #5B4BDB;
  font-weight: 800; display: grid; place-items: center;}
.todo .t {font-weight: 700; color: #14142B;}
.todo .w {color: #6E6E85; font-size: .88rem; margin-top: 2px;}

.bar {margin: 9px 0;}
.bar .row {display: flex; justify-content: space-between; font-size: .88rem; color: #14142B; font-weight: 600;}
.bar .row span {color: #6E6E85; font-weight: 500;}
.bar .track {height: 8px; border-radius: 99px; background: #F1F1F6; margin-top: 5px; overflow: hidden;}
.bar .fill {height: 100%; border-radius: 99px; background: #5B4BDB;}
.bar .fill.hot {background: #F26B3A;}

.badge {display: inline-block; font-size: .74rem; font-weight: 700; padding: 3px 9px; border-radius: 999px; white-space: nowrap;}
.badge.hot {background: #FFF1EA; color: #C4410C;}
.badge.bad {background: #FEECEB; color: #B42318;}
.badge.warm {background: #FFF8E1; color: #9A6700;}
.badge.cool {background: #EEEBFF; color: #4A3BC4;}
.badge.ok {background: #E7F7EE; color: #0B7A3C;}
.badge.grey {background: #F1F1F6; color: #4A4A63;}

.tiles {display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px;}
.tile {background: #FFFFFF; border: 1px solid #ECECF3; border-radius: 18px; padding: 18px 20px;}
.tile .h {display: flex; justify-content: space-between; align-items: center;}
.tile .e {font-size: 1.5rem;}
.tile .name {font-weight: 700; color: #14142B; margin-top: 10px;}
.tile .big {font-size: 1.7rem; font-weight: 800; color: #14142B; letter-spacing: -0.03em; margin-top: 2px;}
.tile .big small {font-size: .85rem; color: #6E6E85; font-weight: 500; letter-spacing: 0;}
.tile .q {color: #4A4A63; font-size: .88rem; font-style: italic; margin-top: 10px; min-height: 2.6em;}
.tile .do {color: #14142B; font-size: .88rem; margin-top: 10px; padding-top: 10px; border-top: 1px solid #F1F1F6;}
.tile .do b {color: #5B4BDB;}

.msg {display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid #F1F1F6;}
.msg:last-child {border-bottom: 0;}
.av {flex: none; width: 36px; height: 36px; border-radius: 50%; display: grid; place-items: center;
  font-weight: 700; color: #fff; font-size: .85rem;}
.msg .meta {font-size: .8rem; color: #6E6E85;}
.msg .txt {color: #14142B; font-size: .95rem; margin-top: 3px;}

.lead {display: flex; align-items: center; gap: 12px; padding: 11px 0; border-bottom: 1px solid #F1F1F6;}
.lead:last-child {border-bottom: 0;}
.lead .rank {width: 22px; color: #6E6E85; font-weight: 700;}
.lead .who {flex: 1;}
.lead .who a {font-weight: 700; color: #14142B; text-decoration: none;}
.lead .who a:hover {text-decoration: underline;}
.lead .who div {font-size: .8rem; color: #6E6E85;}
.lead .n {font-weight: 800; color: #14142B; text-align: right;}
.lead .n span {display: block; font-size: .75rem; color: #6E6E85; font-weight: 500;}

.pc {border: 1px solid #ECECF3; border-radius: 14px; padding: 14px 16px; margin-bottom: 10px; background: #FFFFFF;}
.pc .t {font-weight: 700; color: #14142B;}
.pc .s {color: #6E6E85; font-size: .84rem; margin-top: 2px;}
.pc .m {display: flex; gap: 18px; margin-top: 10px; flex-wrap: wrap;}
.pc .m div {font-size: .8rem; color: #6E6E85;}
.pc .m b {display: block; font-size: 1.15rem; color: #14142B;}
.pc a {color: #14142B; text-decoration: none; font-weight: 700;}
.pc a:hover {text-decoration: underline;}

.stat {background: #FFFFFF; border: 1px solid #ECECF3; border-radius: 18px; padding: 16px 18px;}
.stat b {font-size: 1.6rem; font-weight: 800; color: #5B4BDB; letter-spacing: -0.03em;}
.stat div {color: #4A4A63; font-size: .88rem; margin-top: 4px;}

.camp {background: #FFFFFF; border: 1px solid #ECECF3; border-radius: 18px; padding: 18px 20px; margin-bottom: 6px;}
.camp .tags {display: flex; gap: 6px; flex-wrap: wrap;}
.camp .t {font-weight: 800; color: #14142B; font-size: 1.05rem; margin-top: 10px;}
.camp .w {color: #4A4A63; font-size: .9rem; margin-top: 6px;}
.camp .d {color: #6E6E85; font-size: .84rem; margin-top: 8px;}

table.cmp {width: 100%; border-collapse: collapse; font-size: .9rem;}
table.cmp th {text-align: left; color: #6E6E85; font-weight: 600; font-size: .8rem; padding: 8px 10px; border-bottom: 1px solid #ECECF3;}
table.cmp td {padding: 10px; border-bottom: 1px solid #F1F1F6; color: #14142B;}
table.cmp tr.me td {background: #F6F4FF; font-weight: 700;}
table.cmp td.num {font-variant-numeric: tabular-nums;}

.reply {background: #F6F4FF; border: 1px solid #E2DDFF; border-radius: 14px; padding: 14px 16px; color: #14142B;}
.quote {background: #FAFAFC; border: 1px solid #ECECF3; border-radius: 12px; padding: 10px 12px; margin: 6px 0;
  color: #14142B; font-size: .92rem;}
.quote span {display: block; color: #6E6E85; font-size: .78rem; margin-top: 3px;}
.note {color: #6E6E85; font-size: .82rem;}
[data-testid="stCode"] pre, [data-testid="stCode"] code {font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: .98rem !important; color: #14142B !important; white-space: pre-wrap !important; line-height: 1.55 !important;}
[data-testid="stCode"] pre {background: #F6F4FF !important; border: 1px solid #E2DDFF; border-radius: 14px;}
div[data-testid="stDownloadButton"] button, div[data-testid="stLinkButton"] a {border-radius: 12px; font-weight: 600;}
@media (max-width: 900px) {
  .kpis {grid-template-columns: repeat(2, minmax(0, 1fr));}
  .tiles {grid-template-columns: 1fr;}
  .kpi .v {font-size: 1.4rem;}
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------- helpers ----------------
def html(s):
    st.markdown(s, unsafe_allow_html=True)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(name):
    return st.container(key=f"box_{name}")


def box_head(title, right=""):
    html(f'<div class="bh"><h3>{title}</h3><span>{right}</span></div>')


def top(title, sub):
    html(f'<div class="top"><div><h1>{title}</h1><p>{sub}</p></div>'
         f'<div class="ws"><i>{WS_INITIAL}</i>{esc(WS_LABEL)}</div></div>')


def kpis(items):
    cells = "".join(f'<div class="kpi {cls}"><div class="l">{l}</div><div class="v">{v}</div><div class="n">{n}</div></div>'
                    for l, v, n, cls in items)
    html(f'<div class="kpis">{cells}</div>')


def bars(rows, hot=()):
    mx = max([v for _, v, _ in rows] + [1e-9])
    html("".join(f'<div class="bar"><div class="row">{esc(k)}<span>{lbl}</span></div><div class="track">'
                 f'<div class="fill {"hot" if k in hot else ""}" style="width:{v / mx * 100:.0f}%"></div></div></div>'
                 for k, v, lbl in rows))


def rupees(x):
    if x >= 100_000:
        return f"Rs {x / 100_000:.1f} lakh"
    return f"Rs {x:,.0f}"


def pick(label, options, key, default):
    if key not in st.session_state:
        st.session_state[key] = default
    if hasattr(st, "segmented_control"):
        v = st.segmented_control(label, options, key=key, label_visibility="collapsed")
    else:
        v = st.radio(label, options, key=key, horizontal=True, label_visibility="collapsed")
    return default if v is None else v


def avatar(name):
    palette = ["#5B4BDB", "#F26B3A", "#12A150", "#2A78D6", "#C2410C", "#9E77ED", "#0E9384"]
    return f'<div class="av" style="background:{palette[sum(map(ord, str(name))) % len(palette)]}">{esc(str(name)[:1].upper())}</div>'


# ---------------- data ----------------
@st.cache_data
def load():
    com = pd.read_csv(PROC / "comments_labeled.csv")
    vids = pd.read_csv(PROC / "videos_enriched.csv")
    seg = pd.read_csv(PROC / "comment_segments.csv")
    com = com.drop(columns=["channel", "title", "source", "channel_country"], errors="ignore")
    com = com.merge(vids[["video_id", "post_type", "channel", "channel_id", "title", "format", "content_type", "url"]],
                    on="video_id", how="left").merge(seg[["comment_id", "segment"]], on="comment_id", how="left")
    com["answered"] = com.thread.isin(set(com[com.owner_reply].thread))
    unusual = pd.read_csv(PROC / "unusual_posts.csv")
    metrics = json.loads((PROC / "method_metrics.json").read_text())
    clusters = pd.read_csv(PROC / "clusters.csv")
    cmap = pd.read_csv(PROC / "cluster_map.csv")
    bench = pd.read_csv(PROC / "benchmark.csv") if (PROC / "benchmark.csv").exists() else None
    return com, vids, unusual, metrics, clusters, cmap, bench


COM, VIDS, UNUSUAL, METRICS, CLUSTERS, CMAP, BENCH = load()
BRANDS = CORE + sorted(b for b in VIDS.brand.unique() if b not in CORE)

if hasattr(st, "logo"):
    st.logo(str(ASSETS / "logo.png"), icon_image=str(ASSETS / "logo_icon.png"))

with st.sidebar:
    ws = st.selectbox("Workspace", ["All brands (agency view)", "Core brands (Borjan, Servis, Ndure)"] + BRANDS,
                      key="workspace")
    with st.expander("Money assumptions"):
        PRICE = st.number_input("Average pair price (Rs)", 1000, 20000, 4500, 500, key="price")
        CONV = st.slider("Askers who would buy if answered (%)", 1, 40, 10, key="conv") / 100
        st.caption("Used only for the missed-sales estimate. Change them to match the brand.")
    st.caption(f"Real public YouTube data · collected {DATA_DATE}")

PICKED = BRANDS if ws.startswith("All") else (CORE if ws.startswith("Core") else [ws])
WS_LABEL = "All 8 brands" if ws.startswith("All") else ("Borjan · Servis · Ndure" if ws.startswith("Core") else ws)
WS_INITIAL = "A" if ws.startswith("All") else ("C" if ws.startswith("Core") else ws[:1])
com = COM[COM.brand.isin(PICKED)]
cust = com[~com.owner_reply]
vids = VIDS[VIDS.brand.isin(PICKED)]
top_level = cust[~cust.is_reply]
buy_q = top_level[top_level.intent == "high"]
waiting = buy_q[~buy_q.answered]
MISSED = len(waiting) * CONV * PRICE


def cities(df):
    pats = {"Lahore": r"lahore|lhr", "Karachi": r"karachi|khi", "Faisalabad": r"faisalabad|fsd",
            "Rawalpindi": r"pindi|rawalpindi", "Islamabad": r"islamabad|isb", "Hyderabad": r"hyderabad",
            "Multan": r"multan", "Sialkot": r"sialkot", "Peshawar": r"peshawar", "Gujranwala": r"gujranwala"}
    t = df.text.astype(str).str.lower()
    out = [(c, int(t.str.contains(rf"\b(?:{p})\b").sum())) for c, p in pats.items()]
    return sorted([o for o in out if o[1]], key=lambda x: -x[1])


def creator_leads(df):
    q = df[(df.intent == "high") & (~df.is_reply) & (df.post_type == CREATOR_POST)]
    g = q.groupby(["channel", "channel_id"]).agg(buyers=("comment_id", "count"), brands=("brand", lambda s: ", ".join(s.value_counts().index[:2])),
                                                 answered=("answered", "mean")).reset_index()
    return g.sort_values("buyers", ascending=False)


def campaigns():
    """Ready-to-run campaign ideas, each backed by a number from the data."""
    out = []
    own_q = buy_q[buy_q.post_type == BRAND_POST]
    out.append(dict(
        title="24-hour reply promise", brand=WS_LABEL, impact="High impact", effort="Low effort", channel="YouTube comments",
        why=f"{len(waiting):,} buying questions are waiting for a reply (≈ {rupees(MISSED)} in missed sales). "
            f"On the brands' own videos, {int(own_q.answered.sum())} of {len(own_q)} were answered.",
        do="Assign one person to clear the Leads inbox every morning with the ready replies.",
        en="Got a question about price, size or delivery? Comment below and we'll reply within 24 hours. 💬",
        ru="Price, size ya delivery ka sawal hai? Comment karein, hum 24 ghante mein jawab denge. 💬"))
    leads = creator_leads(cust)
    if len(leads):
        tops = ", ".join(leads.channel.head(3))
        out.append(dict(
            title="Creator sale-vlog partnership", brand=WS_LABEL, impact="High impact", effort="Medium effort", channel="Creators",
            why=f"Creator videos hold {int(leads.buyers.sum()):,} buying questions the brand never sees. Top: {tops}.",
            do="Send top creators a price list, size chart and order link to pin under their next video.",
            en="Brief for creators: show 5 best-sellers with price on screen, try one pair on, pin the order link and sale end date.",
            ru="Creator brief: 5 best-sellers price ke saath dikhayein, ek joota pehen kar dikhayein, order link aur sale ki last date pin karein."))
    cl = cities(cust)
    if cl:
        c1 = cl[0][0]
        c2 = cl[1][0] if len(cl) > 1 else ""
        out.append(dict(
            title=f"{c1}{' & ' + c2 if c2 else ''} city ads", brand=WS_LABEL, impact="Medium impact", effort="Low effort",
            channel="Instagram + Facebook ads",
            why=f"{int((cust.segment == 'Where-can-I-buy askers').sum()):,} comments ask where to buy; "
                + ", ".join(f"{c} ({n})" for c, n in cl[:3]) + " are named most.",
            do="Run location-targeted ads that name the branch and show the online order link.",
            en=f"Now in {c1}! Visit our nearest store or order online with cash on delivery. 📍",
            ru=f"Ab {c1} mein! Qareebi store aayein ya online order karein, cash on delivery ke saath. 📍"))
    until = int(cust.text.str.lower().str.contains(r"kab tak|kb tk|kab tk|kb tak|until when|till when|last date").sum())
    deal = int((cust.segment == "Deal hunters").sum())
    if deal:
        out.append(dict(
            title="Sale countdown posts", brand=WS_LABEL, impact="Medium impact", effort="Low effort", channel="Stories + Shorts",
            why=f"{deal:,} deal-hunter comments; {until} ask when a sale starts or ends ('sale kab tak hai?').",
            do="Post the sale end date on day 1, then a 3-2-1 countdown with best-sellers and sizes left.",
            en="⏳ Only 3 days left! Flat 30% off on best-sellers. Sale ends Sunday night. Shop now.",
            ru="⏳ Sirf 3 din baqi! Best-sellers par flat 30% off. Sale Sunday raat khatam. Abhi order karein."))
    v = vids.copy()
    v["price_in_title"] = v.title.str.lower().str.contains(r"price|\brs\.?\s?\d|\d{3,5}\s?(?:rs|pkr)")
    x = cust.merge(v[["video_id", "price_in_title"]], on="video_id")
    if x.price_in_title.any() and (~x.price_in_title).any():
        a, b = (x[x.price_in_title].need == "price").mean(), (x[~x.price_in_title].need == "price").mean()
        if a < b:
            out.append(dict(
                title="Prices on screen test", brand=WS_LABEL, impact="Medium impact", effort="Low effort", channel="Shorts + Reels",
                why=f"Videos with prices in the title get {a:.1%} price questions vs {b:.1%} without ({1 - a / b:.0%} fewer).",
                do="A/B test: same video, one version with prices on screen, one without. Compare questions and clicks.",
                en="New arrivals with prices 👟 Rs 3,999 | Rs 4,499 | Rs 5,999. Sizes 36–45. Order now.",
                ru="Naye articles qeemat ke saath 👟 Rs 3,999 | Rs 4,499 | Rs 5,999. Size 36–45. Abhi order karein."))
    if "Servis" in PICKED:
        s = cust[cust.brand == "Servis"]
        out.append(dict(
            title="Servis throwback ad", brand="Servis", impact="High impact", effort="Medium effort", channel="YouTube + Reels",
            why=f"{(s.need == 'nostalgia_ad').mean():.0%} of Servis comments are about its classic ads; a 2012 ad still gets comments in 2026.",
            do="A/B test a modern remake of the classic ad against a normal product ad, same budget and audience.",
            en="Remember this one? 😄 The classic is back, with a 2026 twist. Same comfort, new style.",
            ru="Ye ad yaad hai? 😄 Classic wapas aa gaya, 2026 ke andaz mein. Wahi aaram, naya style."))
    size = int((cust.segment == "Size & fit askers").sum())
    if size:
        out.append(dict(
            title="Size guide reel", brand=WS_LABEL, impact="Low impact", effort="Low effort", channel="Reels + pinned post",
            why=f"{size} comments ask about size or fit; wrong sizes mean exchanges and bad reviews.",
            do="Post a 15-second reel: EU / UK / PK size chart and which articles run small or large.",
            en="Not sure about your size? 📏 Here's our EU / UK / PK size guide. Easy exchange if it doesn't fit.",
            ru="Size ka masla? 📏 Ye raha EU / UK / PK size guide. Fit na ho to aasaan exchange."))
    return out


# =====================================================================
def page_today():
    top("Today's opportunities", "Buyers waiting, what they want and what to do first.")
    own = buy_q[buy_q.post_type == BRAND_POST]
    cl = cities(cust)
    kpis([
        ("Missed sales (estimate)", rupees(MISSED), f"{len(waiting):,} buyers asked and got no reply", "money"),
        ("Buying questions", f"{len(buy_q):,}", f"{len(buy_q) / max(len(top_level), 1):.0%} of all comments", ""),
        ("Your reply rate", f"{own.answered.mean():.0%}" if len(own) else "–",
         f"{int(own.answered.sum())} of {len(own)} answered on your own videos" if len(own) else "no buying questions on own videos", ""),
        ("Hottest city", cl[0][0] if cl else "–", f"{cl[0][1]} shoppers asked about it" if cl else "", ""),
    ])
    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        with box("todo"):
            box_head("Do these 3 things today", "From your data")
            camps = campaigns()[:3]
            html("".join(f'<div class="todo"><div class="num">{i}</div><div><div class="t">{esc(c["title"])}</div>'
                         f'<div class="w">{esc(c["do"])}</div></div></div>' for i, c in enumerate(camps, 1)))
            b1, b2 = st.columns(2)
            with b1:
                st.page_link(PAGES["inbox"], label=f"Open leads inbox ({len(waiting):,})", icon=":material/inbox:")
            with b2:
                st.page_link(PAGES["campaigns"], label="See all campaign ideas", icon=":material/rocket_launch:")
    with c2:
        with box("asks"):
            box_head("What customers ask", f"{len(cust):,} comments")
            order = ["Availability / location", "Price inquiry", "Discount / sale", "Delivery / how to order",
                     "Quality / comfort", "Contact / link request", "Complaint / problem", "Size / fit"]
            vc = cust.need_label.value_counts()
            rows = [(SHORT_NEED[k], vc.get(k, 0), f"{vc.get(k, 0):,}") for k in order if vc.get(k, 0)]
            bars(sorted(rows, key=lambda r: -r[1])[:6], hot={"Where to buy", "Price", "Ordering & delivery", "Contact details", "Size & fit"})
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        with box("trend"):
            box_head("Trending in the last 6 months", "vs earlier comments")
            d = pd.to_datetime(cust.published)
            cut = d.max() - pd.Timedelta(days=183)
            a = cust[d >= cut].need_label.value_counts(normalize=True)
            b = cust[d < cut].need_label.value_counts(normalize=True)
            diff = (a.sub(b, fill_value=0) * 100).drop(["Other / off-topic", "General praise / blessing", "Praise for the video"], errors="ignore")
            rows = ""
            for k, v in pd.concat([diff.nlargest(3), diff.nsmallest(2)]).items():
                cls, arrow = ("up", "▲") if v > 0 else ("down", "▼")
                rows += f'<div class="bar"><div class="row">{esc(SHORT_NEED.get(k, k))}<span class="{cls}">{arrow} {abs(v):.1f} pts</span></div></div>'
            html(rows)
            st.caption(f"{int((d >= cut).sum()):,} recent comments vs {int((d < cut).sum()):,} older ones.")
    with c4:
        with box("whereq"):
            box_head("Where buyers ask", "Buying questions by video type")
            mix = buy_q.post_type.value_counts()
            bars([("On creator videos", mix.get(CREATOR_POST, 0), f"{mix.get(CREATOR_POST, 0):,}"),
                  ("On your own videos", mix.get(BRAND_POST, 0), f"{mix.get(BRAND_POST, 0):,}")], hot={"On creator videos"})
            st.caption("Most buyers ask under creators' sale vlogs and reviews, where the brand never replies.")


# =====================================================================
def page_inbox():
    top("Leads inbox", f"{len(waiting):,} buyers are waiting for a reply. Pick one, copy the reply, paste it on YouTube.")
    items = top_level[(top_level.intent == "high") | (top_level.need == "complaint")]
    items = items[~items.answered].copy()
    items["ask"] = items.need.map(ASK)
    items["where"] = np.where(items.post_type == BRAND_POST, "Your video", "Creator: " + items.channel.astype(str))
    items = items.sort_values(["published", "likes"], ascending=False)
    f1, f2 = st.columns([3, 2])
    with f1:
        kind = pick("Type", ["All", "Where to buy", "Price", "Order & delivery", "Size", "Contact", "Complaint"], "inbox_kind", "All")
    with f2:
        src = pick("Source", ["Everywhere", "Your videos", "Creator videos"], "inbox_src", "Everywhere")
    if kind != "All":
        items = items[items.ask == kind]
    if src == "Your videos":
        items = items[items.post_type == BRAND_POST]
    elif src == "Creator videos":
        items = items[items.post_type == CREATOR_POST]

    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        with box("list"):
            box_head("Messages", f"{len(items):,} waiting")
            table = items[["published", "brand", "ask", "text", "where"]].rename(
                columns={"published": "Date", "brand": "Brand", "ask": "Asking about", "text": "Comment", "where": "Posted on"})
            sel = None
            try:
                ev = st.dataframe(table, hide_index=True, use_container_width=True, height=470, on_select="rerun",
                                  selection_mode="single-row", key="inbox_table")
                rows = getattr(getattr(ev, "selection", None), "rows", []) or []
                sel = rows[0] if rows else None
            except TypeError:
                st.dataframe(table, hide_index=True, use_container_width=True, height=470)
            st.download_button("Export leads (CSV)", items[["published", "brand", "ask", "text", "where", "url"]].to_csv(index=False),
                               "leads_inbox.csv", "text/csv")
    with c2:
        with box("reply"):
            if not len(items):
                box_head("All clear", "")
                html('<div class="note">No waiting messages for this filter. 🎉</div>')
                return
            r = items.iloc[sel if sel is not None and sel < len(items) else 0]
            box_head("Reply", "Click a row to switch")
            html(f'<div class="msg">{avatar(r.brand)}<div><div class="meta">{esc(r.brand)} · {esc(r.where)} · {r.published}</div>'
                 f'<div class="txt">{esc(r.text)[:400]}</div></div></div>')
            lang = pick("Language", ["Roman Urdu", "English"], "inbox_lang", "Roman Urdu")
            link = st.text_input("Shop link", "the link in our bio", key="inbox_link")
            key = r.need if r.need in REPLIES else "contact"
            text = REPLIES[key]["ru" if lang == "Roman Urdu" else "en"].format(
                brand=r.brand, link=link, price="____", end_date="____")
            st.code(text, language=None)
            st.caption("Use the copy icon on the reply, then paste it under the comment. Fill in any ____ first.")
            if isinstance(r.url, str):
                st.link_button("Open the video on YouTube", r.url, use_container_width=True)


# =====================================================================
def page_customers():
    top("Your customers", "Everyone who commented, grouped by what they want.")
    g = cust.groupby("segment").agg(people=("author", "nunique"), comments=("comment_id", "count"))
    ready = g[g.index.isin([s for s, v in SEGMENT_CARD.items() if v[2] == "hot"])].people.sum()
    kpis([
        ("People who commented", f"{cust.author.nunique():,}", f"{len(cust):,} comments", ""),
        ("Ready to buy", f"{ready:,}", "asked about price, stock, size, delivery or deals", "money"),
        ("Need care", f"{int(g.people.get('Unhappy customers', 0)):,}", "complaints to fix", ""),
        ("Fans", f"{int(g.people.get('Product fans', 0) + g.people.get('Supporters (general praise)', 0)):,}", "praise and love", ""),
    ])
    tiles = []
    for segname, (emo, badge, tone, todo) in SEGMENT_CARD.items():
        if segname not in g.index:
            continue
        sub = cust[(cust.segment == segname) & cust.need.isin(SEG_NEED[segname]) & (cust.label_source == "word list")]
        sub = sub[sub.text.astype(str).str.len().between(15, 90)]
        quote = sub.sort_values("likes", ascending=False).text.iloc[0] if len(sub) else ""
        tiles.append(f'<div class="tile"><div class="h"><span class="e">{emo}</span><span class="badge {tone}">{badge}</span></div>'
                     f'<div class="name">{esc(segname)}</div><div class="big">{int(g.loc[segname, "people"]):,} <small>people</small></div>'
                     f'<div class="q">{"“" + esc(quote) + "”" if quote else ""}</div>'
                     f'<div class="do"><b>Do:</b> {esc(todo)}</div></div>')
    html(f'<div class="tiles">{"".join(tiles)}</div>')
    st.write("")
    with box("hear"):
        box_head("Hear them out", "Real comments from one group")
        names = [s for s in SEGMENT_CARD if s in g.index]
        segname = st.selectbox("Group", names, key="cust_seg", label_visibility="collapsed")
        ex = cust[(cust.segment == segname) & cust.need.isin(SEG_NEED[segname])].drop_duplicates("text")
        ex = ex.sample(min(6, len(ex)), random_state=4) if len(ex) else ex
        c1, c2 = st.columns(2)
        for i, r in enumerate(ex.itertuples()):
            with (c1 if i % 2 == 0 else c2):
                html(f'<div class="quote">{esc(r.text)[:220]}<span>{esc(r.brand)} · {r.published}</span></div>')


# =====================================================================
def page_content():
    top("Post this, not that", "What gets people talking and asking to buy, and who to partner with.")
    pt = vids.groupby("post_type").agg(cm=("comments_per_1k", "median"), views=("views", "median"), lk=("likes_per_1k", "median"))
    hi = cust.groupby("post_type").intent.apply(lambda s: (s == "high").mean())
    if BRAND_POST in pt.index and CREATOR_POST in pt.index and pt.loc[BRAND_POST, "cm"] > 0:
        s1, s2, s3 = st.columns(3)
        with s1:
            html(f'<div class="stat"><b>{pt.loc[CREATOR_POST, "cm"] / pt.loc[BRAND_POST, "cm"]:.0f}×</b>'
                 f'<div>more comments per view on creator videos than on brand videos</div></div>')
        with s2:
            html(f'<div class="stat"><b>{hi.get(CREATOR_POST, 0):.0%} vs {hi.get(BRAND_POST, 0):.0%}</b>'
                 f'<div>buying questions on creator vs brand videos</div></div>')
        with s3:
            html(f'<div class="stat"><b>{pt.loc[BRAND_POST, "views"] / max(pt.loc[CREATOR_POST, "views"], 1):.0f}×</b>'
                 f'<div>more views on brand videos, mostly paid reach with little talk</div></div>')
        st.write("")
    g = vids.groupby(["content_type", "format"]).agg(n=("video_id", "count"), cm=("comments_per_1k", "median"),
                                                     views=("views", "median"), hi=("high_intent_share", "mean")).reset_index()
    g = g[(g.n >= 5) & (g.content_type != "Other / untitled")].sort_values("cm", ascending=False)
    c1, c2 = st.columns(2, gap="medium")

    def card(r, tone):
        return (f'<div class="pc"><div class="t">{esc(r.content_type)} <span class="badge {tone}">{r.format}</span></div>'
                f'<div class="m"><div><b>{r.cm:.2f}</b>comments / 1k views</div><div><b>{r.hi:.0%}</b>buying questions</div>'
                f'<div><b>{r.views:,.0f}</b>median views</div><div><b>{r.n}</b>videos</div></div></div>')
    with c1:
        with box("more"):
            box_head("✅ Post more of this", "Most conversation per view")
            html("".join(card(r, "ok") for r in g.head(3).itertuples()))
    with c2:
        with box("less"):
            box_head("✋ Less of this", "Views without conversation")
            html("".join(card(r, "grey") for r in g.tail(3).iloc[::-1].itertuples()))
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        with box("leaders"):
            box_head("Creators to partner with", "Ranked by buyers asking on their videos")
            ld = creator_leads(cust).head(8)
            html("".join(f'<div class="lead"><div class="rank">{i}</div>{avatar(r.channel)}<div class="who">'
                         f'<a href="https://www.youtube.com/channel/{r.channel_id}" target="_blank">{esc(r.channel)}</a>'
                         f'<div>{esc(r.brands)} · creator answers {r.answered:.0%}</div></div>'
                         f'<div class="n">{r.buyers}<span>buyers asked</span></div></div>'
                         for i, r in enumerate(ld.itertuples(), 1)) or '<div class="note">No creator videos here.</div>')
    with c4:
        with box("standouts"):
            box_head("Standout posts", "Far ahead of similar posts")
            u = UNUSUAL[UNUSUAL.brand.isin(PICKED) & UNUSUAL.what_to_do.str.startswith("Learn")].head(5)
            html("".join(f'<div class="pc"><a href="{r.url}" target="_blank">{esc(r.title)[:80]}</a>'
                         f'<div class="s">{esc(r.brand)} · {esc(r.channel)} · {int(r.views):,} views</div>'
                         f'<div class="s" style="color:#0B7A3C;margin-top:6px">▲ {esc(r.unusual_because.split(";")[0])}</div></div>'
                         for r in u.itertuples()) or '<div class="note">No standout posts here.</div>')


# =====================================================================
def page_competitors():
    top("Competitors", "How each brand's audience compares, side by side.")
    allc = COM[~COM.owner_reply]
    rows = []
    for b in BRANDS:
        s = allc[allc.brand == b]
        t = s[~s.is_reply]
        own = t[(t.intent == "high") & (t.post_type == BRAND_POST)]
        buy = s[s.need.isin(ASK) & (s.need != "complaint")].need.map(ASK).value_counts()
        rows.append(dict(brand=b, comments=len(s), buying=(t.intent == "high").mean(), top=buy.index[0] if len(buy) else "–",
                         reply=f"{int(own.answered.sum())} of {len(own)}" if len(own) else "–",
                         complaints=(s.need == "complaint").mean(), buzz=(s.need == "nostalgia_ad").mean(),
                         fans=s.need.isin(["praise_product", "general_praise"]).mean()))
    t = pd.DataFrame(rows)
    body = "".join(
        f'<tr class="{"me" if r.brand in PICKED and len(PICKED) < len(BRANDS) else ""}"><td>{esc(r.brand)}</td>'
        f'<td class="num">{r.comments:,}</td><td class="num">{r.buying:.0%}</td><td>{esc(r.top)}</td>'
        f'<td class="num">{r.reply}</td><td class="num">{r.fans:.0%}</td><td class="num">{r.complaints:.1%}</td>'
        f'<td class="num">{r.buzz:.0%}</td></tr>' for r in t.itertuples())
    with box("cmp"):
        box_head("Brand scorecard", "Highlighted rows = your workspace")
        html('<table class="cmp"><tr><th>Brand</th><th>Comments</th><th>Buying questions</th><th>Top ask</th>'
             f'<th>Replies on own videos</th><th>Fans</th><th>Complaints</th><th>Ad buzz</th></tr>{body}</table>')
    st.write("")
    with box("cmpchart"):
        box_head("What each brand's customers ask about", "Share of the brand's comments")
        needs = {"Where to buy": "availability", "Price": "price", "Sale": "discount_sale", "Order & delivery": "delivery_order",
                 "Quality": "quality_comfort", "Complaints": "complaint"}
        colors = ["#5B4BDB", "#F26B3A", "#E87BA4", "#2A78D6", "#12A150", "#D92D20"]
        fig = go.Figure()
        for (lbl, key), col in zip(needs.items(), colors):
            vals = [(allc[allc.brand == b].need == key).mean() * 100 for b in BRANDS]
            fig.add_trace(go.Bar(name=lbl, x=BRANDS, y=vals, marker_color=col,
                                 hovertemplate=lbl + ": %{y:.1f}%<extra>%{x}</extra>"))
        fig.update_layout(barmode="group", height=360, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                          font=dict(family=FONT, color="#4A4A63", size=12), margin=dict(t=30, l=6, r=6, b=6),
                          legend=dict(orientation="h", y=1.08, x=0, title_text=""), yaxis=dict(title="% of comments", gridcolor="#F1F1F6"),
                          xaxis=dict(linecolor="#ECECF3"), bargap=0.25)
        st.plotly_chart(fig, theme=None, config={"displaylogo": False, "displayModeBar": False})


# =====================================================================
def page_campaigns():
    top("Campaign ideas", "Smart suggestions built from your comments. Each one comes with ready ad copy.")
    camps = campaigns()
    for i in range(0, len(camps), 2):
        cols = st.columns(2, gap="medium")
        for col, c in zip(cols, camps[i:i + 2]):
            with col:
                tone = "hot" if c["impact"].startswith("High") else ("warm" if c["impact"].startswith("Medium") else "grey")
                html(f'<div class="camp"><div class="tags"><span class="badge {tone}">{c["impact"]}</span>'
                     f'<span class="badge ok">{c["effort"]}</span><span class="badge cool">{esc(c["channel"])}</span></div>'
                     f'<div class="t">{esc(c["title"])}</div><div class="w">{esc(c["do"])}</div>'
                     f'<div class="d">Why: {esc(c["why"])}</div></div>')
                with st.expander("Ready ad copy"):
                    st.code(c["en"], language=None)
                    st.code(c["ru"], language=None)
    st.write("")
    with box("p2"):
        box_head("Plan the budget in Project 2", "")
        html('<div class="note">Turn these ideas into a spend plan: Project 2 splits the ad budget across Facebook, TikTok, '
             'Instagram, Google and YouTube for the same brands, and writes ads around the same angles (price, size, delivery, quality).</div>')
        st.link_button("Open the ad budget optimizer (Project 2)", P2_APP)


# =====================================================================
def page_report():
    top("Client report", "A one-page snapshot to send to the brand. Download as PDF.")
    from report_pdf import build_report
    segs = cust.groupby("segment").author.nunique()
    segs = segs[segs.index.isin([s for s, v in SEGMENT_CARD.items() if v[2] in ("hot", "bad")])].sort_values(ascending=False).head(5)
    own = buy_q[buy_q.post_type == BRAND_POST]
    camps = campaigns()[:3]
    leads = creator_leads(cust).head(3)
    cl = cities(cust)[:4]
    ctx = dict(
        workspace=WS_LABEL, date=f"data collected {DATA_DATE}",
        kpis=[("Missed sales (estimate)", rupees(MISSED), f"{len(waiting):,} buyers waiting for a reply"),
              ("Buying questions", f"{len(buy_q):,}", "price, stock, order, size, contact"),
              ("Reply rate, own videos", f"{own.answered.mean():.0%}" if len(own) else "–", f"{int(own.answered.sum())} of {len(own)} answered"),
              ("Hottest city", cl[0][0] if cl else "–", f"{cl[0][1]} mentions" if cl else "")],
        actions=[(c["title"] + ": " + c["do"], c["why"]) for c in camps],
        segments=[(s, int(n), SEGMENT_CARD[s][3]) for s, n in segs.items()],
        cities=cl, creators=[(r.channel, r.brands, int(r.buyers)) for r in leads.itertuples()],
        assumptions=f"Missed sales = unanswered buying questions x {CONV:.0%} who would buy x Rs {PRICE:,.0f} per pair. An estimate, not a measured figure.",
        source=f"Source: {len(cust):,} public YouTube comments on {vids.video_id.nunique():,} videos, official YouTube Data API. Names removed.",
        url=REPO_URL)
    pdf = build_report(ctx)
    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        with box("preview"):
            box_head(f"Client snapshot: {esc(WS_LABEL)}", f"data collected {DATA_DATE}")
            html("".join(f'<div class="bar"><div class="row">{esc(l)}<span>{esc(v)}</span></div></div>' for l, v, _ in ctx["kpis"]))
            html("<br><b>Do these first</b>" + "".join(f'<div class="todo"><div class="num">{i}</div><div><div class="t">{esc(c["title"])}</div>'
                                                       f'<div class="w">{esc(c["do"])}</div></div></div>' for i, c in enumerate(camps, 1)))
    with c2:
        with box("dl"):
            box_head("Download", "")
            st.download_button("Download PDF report", pdf, f"joota_pulse_{WS_LABEL.replace(' ', '_').lower()}.pdf",
                               "application/pdf", use_container_width=True, type="primary")
            html('<div class="note" style="margin-top:10px">Switch the workspace in the sidebar to make a report for one brand. '
                 'Adjust the money assumptions in the sidebar to match the brand.</div>')


# =====================================================================
def page_how():
    top("How it works", "The method, the checks and the limits. For the curious (and for marking).")
    t1, t2, t3, t4, t5 = st.tabs(["Pipeline", "Accuracy checks", "Big Data benchmark", "Data & privacy", "Limitations"])
    with t1:
        st.markdown(
            "1. **Collect:** the official YouTube Data API finds videos about 8 Pakistani footwear brands (their own channels "
            "plus creators' sale vlogs and reviews) and downloads every comment.\n"
            "2. **Clean:** keep videos that name the brand, drop Indian and foreign videos (Bata's channel is Bata India, so "
            "Bata is out), drop foreign-language and empty comments, remove phone numbers, e-mails and names.\n"
            "3. **Understand:** word lists in English, Roman Urdu and Urdu tag clear needs (price, where to buy, delivery, size…). "
            "A multilingual AI embedding model (`paraphrase-multilingual-mpnet-base-v2`) tags similar comments the word lists miss.\n"
            "4. **Group:** K-Means clustering finds natural topic groups; each person is placed in one customer group.\n"
            "5. **Compare content:** attention per video (views per day, likes and comments per 1,000 views, share of buying questions).\n"
            "6. **Spot the unusual:** each video vs similar videos (robust z-scores), plus an Isolation Forest.\n"
            "7. **Act:** rules turn the numbers into campaign ideas, inbox replies and a client report.")
        st.markdown(f"Code: [{REPO_URL}]({REPO_URL})")
    with t2:
        c1, c2 = st.columns([2, 3])
        with c1:
            html(f'<div class="bar"><div class="row">Comments tagged by word lists<span>{METRICS["labelled_by_word_list"]:,}</span></div></div>'
                 f'<div class="bar"><div class="row">Tagged by nearest neighbours (AI embeddings)<span>{METRICS["labelled_by_neighbours"]:,}</span></div></div>'
                 f'<div class="bar"><div class="row">Neighbour tagging check, 5-fold<span>{METRICS["knn_cv_accuracy"]:.0%}</span></div></div>'
                 f'<div class="bar"><div class="row">Topic clusters (best silhouette)<span>{METRICS["k"]}</span></div></div>'
                 f'<div class="bar"><div class="row">Cluster–need match, embeddings (NMI)<span>{METRICS["nmi_embeddings_vs_needs"]:.2f}</span></div></div>'
                 f'<div class="bar"><div class="row">Cluster–need match, TF-IDF baseline<span>{METRICS["nmi_tfidf_vs_needs"]:.2f}</span></div></div>')
            st.caption("Embeddings group comments by need better than word counts (0.43 vs 0.34). Silhouette is low "
                       "(about 0.14) because short comments overlap, so clusters are a guide, not hard lines.")
        with c2:
            cm = CMAP.merge(COM[["comment_id", "text"]], on="comment_id").sample(2500, random_state=0)
            cm["group"] = cm.cluster.map(CLUSTERS.set_index("cluster").main_need_label)
            fig = go.Figure()
            for gname, d in cm.groupby("group"):
                fig.add_trace(go.Scattergl(x=d.x, y=d.y, mode="markers", name=gname, marker=dict(size=5, opacity=.6),
                                           text=d.text.str[:70], hovertemplate="%{text}<extra>" + gname + "</extra>"))
            fig.update_layout(height=380, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(family=FONT, size=11),
                              xaxis=dict(visible=False), yaxis=dict(visible=False), margin=dict(t=10, l=0, r=0, b=0),
                              legend=dict(font=dict(size=10)))
            st.plotly_chart(fig, theme=None, config={"displaylogo": False})
            st.caption("Each dot is a comment placed by meaning; similar comments sit together even across languages.")
    with t3:
        if BENCH is None:
            st.info("Benchmark results will appear here after the Spark run.")
        else:
            fig = go.Figure()
            for eng, d in BENCH.groupby("engine"):
                fig.add_trace(go.Scatter(x=d.rows, y=d.seconds, mode="lines+markers", name=eng, line=dict(width=3)))
            fig.update_layout(height=340, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(family=FONT),
                              xaxis=dict(type="log", title="Comments"), yaxis=dict(type="log", title="Seconds"),
                              margin=dict(t=10))
            st.plotly_chart(fig, theme=None, config={"displaylogo": False})
            st.dataframe(BENCH, hide_index=True)
            st.caption("On a free 2-core Colab machine Spark was about 2× slower than pandas at every size, and both grew in a "
                       "straight line with the data; labels matched 100%. Spark's start-up and coordination cost only pays off "
                       "on a cluster or when the data no longer fits in one computer's memory.")
    with t4:
        st.markdown(
            f"- **Real data only:** {len(COM):,} public comments on {len(VIDS):,} videos, collected {DATA_DATE} with the official YouTube Data API.\n"
            "- **Collected:** 853 videos and 8,508 comments; after cleaning, 690 videos and 6,724 comments.\n"
            "- **Privacy:** commenter names are never stored (each person is an anonymous code); phone numbers, e-mails, "
            "@handles and order numbers are removed from the text.\n"
            "- **Every video keeps its link and collection date** (Table A); every comment keeps its video, language, topic and "
            "purchase intent (Table B).")
        ta = VIDS[["video_id", "brand", "platform", "content_type", "format", "post_type", "title", "views", "likes", "comments",
                   "published", "url", "collected_on"]]
        tb = COM[["video_id", "comment_id", "brand", "text", "lang", "need_label", "intent", "published", "collected_on"]]
        c1, c2 = st.columns(2)
        c1.download_button("Table A: posts (CSV)", ta.to_csv(index=False), "table_a_posts.csv", "text/csv", use_container_width=True)
        c2.download_button("Table B: comments (CSV)", tb.to_csv(index=False), "table_b_comments.csv", "text/csv", use_container_width=True)
    with t5:
        st.markdown(
            "- **YouTube only.** Instagram, TikTok and Facebook comments can't be collected within their terms; the data has a "
            "platform column so Instagram post stats can be added later.\n"
            "- **No shares.** YouTube's API doesn't report them.\n"
            "- **Most comments are on creator videos,** so they show what shoppers ask, not how a brand's own page performs.\n"
            "- **Brand videos with huge views and few comments are probably paid promotion.**\n"
            "- **Roman Urdu spelling varies,** so some comments are missed or mis-tagged; about a third stay unlabelled.\n"
            "- **The missed-sales figure is an estimate** from the assumptions in the sidebar, not a measured number.\n"
            "- **Small groups:** size questions (38) and complaints (73) are small samples.\n"
            "- **Patterns, not proof:** 'prices shown → fewer price questions' is a correlation worth A/B testing.\n"
            "- **The API returns up to 5 replies per thread,** so a few brand replies may be missed.")
        st.markdown(f"Series: [Project 1 sentiment]({P1_URL}) · [Project 2 ad budget]({P2_URL})")


# ---------------- navigation ----------------
PAGES = {
    "today": st.Page(page_today, title="Today", icon=":material/space_dashboard:", url_path="today", default=True),
    "inbox": st.Page(page_inbox, title="Leads inbox", icon=":material/inbox:", url_path="inbox"),
    "customers": st.Page(page_customers, title="Your customers", icon=":material/groups:", url_path="customers"),
    "content": st.Page(page_content, title="Post this, not that", icon=":material/smart_display:", url_path="content"),
    "competitors": st.Page(page_competitors, title="Competitors", icon=":material/leaderboard:", url_path="competitors"),
    "campaigns": st.Page(page_campaigns, title="Campaign ideas", icon=":material/rocket_launch:", url_path="campaigns"),
    "report": st.Page(page_report, title="Client report", icon=":material/description:", url_path="report"),
    "how": st.Page(page_how, title="How it works", icon=":material/info:", url_path="how-it-works"),
}
st.navigation({"Workspace": [PAGES[k] for k in ["today", "inbox", "customers", "content", "competitors", "campaigns"]],
               "Share": [PAGES["report"]], "About": [PAGES["how"]]}).run()
