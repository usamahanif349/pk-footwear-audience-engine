"""
Streamlit dashboard: Pakistan Social Audience & Campaign Intelligence Engine for
Pakistani footwear brands (Project 3). All comments and video numbers are REAL public
YouTube data, collected with the official YouTube Data API.

Run locally (Command Prompt):  streamlit run src\\dashboard\\app.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "engine"))
from lexicon import NEED_LABEL  # noqa: E402
from replies import REPLIES  # noqa: E402

PROC = ROOT / "data" / "processed"
REPO_URL = "https://github.com/usamahanif349/pk-footwear-audience-engine"
P1_URL = "https://github.com/usamahanif349/pk-footwear-sentiment-analysis"
P2_URL = "https://github.com/usamahanif349/pk-footwear-budget-optimizer"
P2_APP = "https://pk-footwear-budget-optimizer.streamlit.app/"
CORE = ["Borjan", "Servis", "Ndure"]

# ---------------- COLOURS ----------------
INK, INK_2, MUTED, LINE = "#101828", "#475467", "#667085", "#E4E7EC"
NAVY, GREY, GREY_LIGHT = "#1E3A5F", "#98A2B3", "#D0D5DD"
GOOD, BAD, WARN = "#067647", "#B42318", "#B54708"
# buying needs in warm colours, praise and buzz in cool ones, the rest grey
NEED_COLORS = {
    "Price inquiry": "#EB6834", "Availability / location": "#EDA100", "Delivery / how to order": "#C2410C",
    "Contact / link request": "#D97706", "Size / fit": "#B45309", "Complaint / problem": "#B42318",
    "Discount / sale": "#E87BA4", "Quality / comfort": "#9E77ED", "Product praise / wants it": "#1BAF7A",
    "Praise for the video": "#2A78D6", "General praise / blessing": "#7CB4F0",
    "Ad nostalgia / celebrity buzz": "#1E3A5F", "Other / off-topic": "#D0D5DD",
}
FORMAT_COLORS = {"Short": "#EB6834", "Video": "#2A78D6"}
POST_COLORS = {"Brand's own post": NAVY, "Creator / influencer post": "#1BAF7A"}
CHART_FONT = "Segoe UI, -apple-system, Helvetica Neue, Arial, sans-serif"
BRAND_POST, CREATOR_POST = "Brand's own post", "Creator / influencer post"
BUY_NEEDS = ["Price inquiry", "Availability / location", "Delivery / how to order", "Contact / link request", "Size / fit"]

st.set_page_config(page_title="Footwear audience engine", page_icon="📣", layout="wide")

CSS = """
<style>
.stApp {background: #F6F7F9;}
.block-container {padding-top: 3.2rem; padding-bottom: 3rem; max-width: 1280px;}
[data-testid="stSidebar"] {background: #FFFFFF; border-right: 1px solid #E4E7EC;}
.page-h {display: flex; justify-content: space-between; align-items: flex-end; gap: 16px;
  flex-wrap: wrap; margin-bottom: 1.1rem;}
.page-h .crumb {color: #667085; font-size: .86rem; margin: 0 0 4px;}
.page-h h1 {font-size: 1.85rem; font-weight: 700; color: #101828; margin: 0; padding: 0;
  letter-spacing: -0.01em; line-height: 1.2;}
.page-h .sub {color: #475467; margin: 6px 0 0; font-size: 1rem; max-width: 72ch;}
.tag {display: inline-block; font-size: .8rem; font-weight: 600; padding: 4px 10px; border-radius: 999px;
  background: #EEF2F7; color: #1E3A5F; border: 1px solid #D5DEEA; white-space: nowrap;}
.tag.real {background: #ECFDF3; color: #067647; border-color: #ABEFC6;}
[class*="st-key-card_"] {background: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 14px;
  padding: 18px 20px 14px; box-shadow: 0 1px 2px rgba(16, 24, 40, .05);}
.card-h h4 {font-size: 1.05rem; font-weight: 600; color: #101828; margin: 0; padding: 0;}
.card-h p {color: #667085; font-size: .88rem; margin: 3px 0 10px;}
.kpis {display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 14px;}
.kpi {background: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 14px; padding: 16px 18px;
  box-shadow: 0 1px 2px rgba(16, 24, 40, .05);}
.kpi .lbl {color: #475467; font-size: .88rem; font-weight: 500;}
.kpi .row {display: flex; align-items: center; gap: 10px; margin-top: 6px; flex-wrap: wrap;}
.kpi .val {color: #101828; font-size: 1.6rem; font-weight: 700; line-height: 1.15; white-space: nowrap;}
.kpi .note {color: #667085; font-size: .82rem; margin-top: 6px;}
.chip {font-size: .78rem; font-weight: 600; padding: 2px 8px; border-radius: 999px; white-space: nowrap;}
.chip.good {background: #ECFDF3; color: #067647;}
.chip.bad {background: #FEF3F2; color: #B42318;}
.chip.neutral {background: #F2F4F7; color: #344054;}
@media (max-width: 900px) {
  .kpis {grid-template-columns: repeat(2, minmax(0, 1fr));}
  .kpi .val {font-size: 1.25rem; white-space: normal;}
  .page-h h1 {font-size: 1.5rem;}
}
.why {color: #344054; line-height: 1.6; font-size: .97rem;}
.why b {color: #101828;}
.fact {display: flex; justify-content: space-between; gap: 12px; padding: 8px 0;
  border-bottom: 1px solid #F2F4F7; font-size: .93rem; color: #344054;}
.fact:last-child {border-bottom: 0;}
.fact b {color: #101828; font-variant-numeric: tabular-nums; text-align: right;}
.answer {padding: 12px 0; border-bottom: 1px solid #F2F4F7;}
.answer:last-child {border-bottom: 0;}
.answer .q {font-weight: 600; color: #101828; font-size: .98rem;}
.answer .a {color: #344054; font-size: .94rem; margin-top: 3px; line-height: 1.55;}
.act {padding: 12px 0 12px; border-bottom: 1px solid #F2F4F7;}
.act:last-child {border-bottom: 0;}
.act .top {display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 4px;}
.act .what {font-weight: 600; color: #101828;}
.act .ev {color: #475467; font-size: .9rem; margin-top: 3px;}
.pill {font-size: .75rem; font-weight: 600; padding: 2px 8px; border-radius: 999px;
  background: #F2F4F7; color: #344054; white-space: nowrap;}
.pill.p1 {background: #FEF3F2; color: #B42318;}
.pill.p2 {background: #FFFAEB; color: #B54708;}
.pill.p3 {background: #F2F4F7; color: #344054;}
.flag {padding: 12px 0; border-bottom: 1px solid #F2F4F7;}
.flag:last-child {border-bottom: 0;}
.flag a {font-weight: 600; color: #101828; text-decoration: none;}
.flag a:hover {text-decoration: underline;}
.flag .meta {color: #667085; font-size: .84rem; margin-top: 2px;}
.flag .why2 {color: #344054; font-size: .92rem; margin-top: 4px;}
.quote {background: #F8FAFC; border: 1px solid #E4E7EC; border-radius: 10px; padding: 8px 12px;
  margin: 6px 0; color: #344054; font-size: .93rem;}
.quote span {color: #667085; font-size: .8rem;}
[data-testid="stCode"] pre, [data-testid="stCode"] code {
  font-family: "Source Sans Pro", "Source Sans", "Segoe UI", sans-serif !important;
  font-size: 1rem !important; color: #101828 !important; line-height: 1.5 !important; white-space: pre-wrap !important;}
[data-testid="stCode"] pre {background: #F8FAFC !important; border: 1px solid #E4E7EC;}
.side-brand {font-size: 1.1rem; font-weight: 700; color: #101828; line-height: 1.25; margin-bottom: 2px;}
.side-brand span {display: block; font-size: .85rem; font-weight: 400; color: #667085;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

pio.templates["clean"] = go.layout.Template(layout=go.Layout(
    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color="#475467", family=CHART_FONT, size=13),
    xaxis=dict(gridcolor="#F0F2F5", zerolinecolor="#D0D5DD", linecolor="#D0D5DD", ticks="", showline=True),
    yaxis=dict(gridcolor="#F0F2F5", zerolinecolor="#D0D5DD", linecolor="#D0D5DD", ticks=""),
    margin=dict(t=30, l=8, r=16, b=8),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title_text=""),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#D0D5DD", font=dict(color=INK, family=CHART_FONT))))


# ---------------- HELPERS ----------------
def show(fig, height=None):
    fig.update_layout(template="plotly_white+clean", paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                      font=dict(color="#475467", family=CHART_FONT, size=13))
    axis = dict(gridcolor="#F0F2F5", zerolinecolor="#D0D5DD", linecolor="#D0D5DD")
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, theme=None, config={"displaylogo": False})


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def card(name):
    return st.container(key=f"card_{name}")


def card_head(title, sub=""):
    html(f'<div class="card-h"><h4>{title}</h4><p>{sub}</p></div>')


def page_head(crumb, title, sub, tags=()):
    tag_html = "".join(f'<span class="tag {cls}">{t}</span> ' for t, cls in tags)
    html(f'<div class="page-h"><div><p class="crumb">{crumb}</p><h1>{title}</h1>'
         f'<p class="sub">{sub}</p></div><div>{tag_html}</div></div>')


def kpi_cards(items):
    cells = []
    for lbl, val, chip, tone, note in items:
        chip_html = f'<span class="chip {tone}">{chip}</span>' if chip else ""
        cells.append(f'<div class="kpi"><div class="lbl">{lbl}</div><div class="row"><span class="val">{val}</span>'
                     f'{chip_html}</div><div class="note">{note}</div></div>')
    html(f'<div class="kpis">{"".join(cells)}</div>')


def segmented(label, options, key, default):
    if key not in st.session_state:
        st.session_state[key] = default
    if hasattr(st, "segmented_control"):
        val = st.segmented_control(label, options, key=key)
    else:
        val = st.radio(label, options, key=key, horizontal=True)
    return default if val is None else val


def pct(x, digits=0):
    return f"{x * 100:.{digits}f}%"


# ---------------- DATA ----------------
@st.cache_data
def load():
    com = pd.read_csv(PROC / "comments_labeled.csv")
    vids = pd.read_csv(PROC / "videos_enriched.csv")
    seg = pd.read_csv(PROC / "comment_segments.csv")
    com = com.drop(columns=["channel", "title", "source", "channel_country"], errors="ignore")
    com = com.merge(vids[["video_id", "post_type", "channel", "title", "format", "content_type", "url"]],
                    on="video_id", how="left").merge(seg[["comment_id", "segment"]], on="comment_id", how="left")
    answered = set(com[com.owner_reply].thread)
    com["answered"] = com.thread.isin(answered)
    tables = {n: pd.read_csv(PROC / f"{n}.csv") for n in
              ["segments", "unusual_posts", "creator_leads", "city_mentions", "action_plan", "clusters",
               "cluster_map", "post_audience_types", "content_summary"]}
    findings = json.loads((PROC / "findings.json").read_text())
    metrics = json.loads((PROC / "method_metrics.json").read_text())
    bench = pd.read_csv(PROC / "benchmark.csv") if (PROC / "benchmark.csv").exists() else None
    return com, vids, tables, findings, metrics, bench


com_all, vids_all, T, F, M, BENCH = load()
BRANDS = CORE + sorted(b for b in vids_all.brand.unique() if b not in CORE)

with st.sidebar:
    html('<div class="side-brand">Footwear audience engine<span>Project 3 · Big Data Analytics</span></div>')
    view = st.selectbox("Brands", ["All 8 brands", "Core brands (Borjan, Servis, Ndure)"] + BRANDS, key="brand_view")
    st.caption("Real public YouTube comments and video stats, collected with the official YouTube Data API.")

if view == "All 8 brands":
    picked = BRANDS
elif view.startswith("Core"):
    picked = CORE
else:
    picked = [view]
com = com_all[com_all.brand.isin(picked)]
cust = com[~com.owner_reply]
vids = vids_all[vids_all.brand.isin(picked)]
REAL_TAG = ("Real YouTube data", "real")
VIEW_TAG = (view if len(picked) > 1 else picked[0], "")


# =====================================================================
# OVERVIEW
# =====================================================================
def page_overview():
    page_head("Dashboard / Overview", "What Pakistani footwear shoppers are really asking for",
              "An engine that groups real YouTube comments into audience needs, compares content, flags unusual "
              "posts and turns it all into actions for the marketing team.", [VIEW_TAG, REAL_TAG])
    hi = cust[cust.intent == "high"]
    top_q = hi[~hi.is_reply]
    own = top_q[top_q.post_type == "Brand's own post"]
    need_mix = cust.need_label.value_counts(normalize=True)
    top_buy = cust[cust.need_label.isin(BUY_NEEDS)].need_label.value_counts()
    kpi_cards([
        ("Customer comments", f"{len(cust):,}", f"{cust.author.nunique():,} people", "neutral",
         f"on {vids.video_id.nunique():,} videos, {cust.brand.nunique()} brand(s)"),
        ("Buying questions", f"{len(hi):,}", pct(len(hi) / max(len(cust), 1)), "neutral",
         "price, where to buy, how to order, size, contact"),
        ("Answered on brand posts", f"{int(own.answered.sum())} of {len(own)}",
         "missed sales" if len(own) and own.answered.mean() < 0.5 else "", "bad",
         "buying questions the brand replied to on its own videos"),
        ("Top buying need", top_buy.index[0] if len(top_buy) else "-", pct(top_buy.iloc[0] / len(cust)) if len(top_buy) else "",
         "neutral", "share of all customer comments"),
    ])

    left, right = st.columns([7, 5], gap="medium")
    with left:
        with card("answers"):
            card_head("The five questions, answered", "Short answers; each page has the detail")
            sv = vids.groupby("post_type").agg(cpk=("comments_per_1k", "median"), views=("views", "median"))
            hi_share = cust.groupby("post_type").intent.apply(lambda s: (s == "high").mean())
            ct = vids.groupby("content_type").agg(views=("views", "median"), cpk=("comments_per_1k", "median"), n=("video_id", "count"))
            ct = ct[ct.n >= 5]
            unusual = T["unusual_posts"][T["unusual_posts"].brand.isin(picked)]
            segs = cust.groupby("segment").author.nunique().sort_values(ascending=False)
            buy_segs = segs[segs.index.isin(["Where-can-I-buy askers", "Price checkers", "Deal hunters",
                                             "Order & delivery askers", "Contact seekers", "Size & fit askers"])]
            items = [
                ("1. Which content attracts attention?",
                 (f"<b>{ct.views.idxmax()}</b> gets the most views (median {ct.views.max():,.0f}), but "
                  f"<b>{ct.cpk.idxmax()}</b> gets people talking ({ct.cpk.max():.1f} comments per 1,000 views). "
                  if len(ct) else "") +
                 (f"Creator posts earn far more conversation per view than brand posts "
                  f"({sv.cpk[CREATOR_POST]:.2f} vs {sv.cpk[BRAND_POST]:.2f} comments per 1,000 views)."
                  if CREATOR_POST in sv.index and BRAND_POST in sv.index else "")),
                ("2. What does the audience want?",
                 "Beyond praise, the biggest needs are " + ", ".join(
                     f"<b>{n.lower()}</b> ({pct(need_mix.get(n, 0))})" for n in top_buy.index[:3]) + "."),
                ("3. Which patterns are unusual?",
                 f"<b>{len(unusual)}</b> posts stand out from similar posts: "
                 f"{(unusual.what_to_do.str.startswith('Learn')).sum()} to learn from, "
                 f"{(unusual.what_to_do.str.startswith('Inv')).sum()} to investigate."),
                ("4. Which audience needs should the brand address?",
                 "Largest buying groups: " + ", ".join(f"<b>{s}</b> ({n:,})" for s, n in buy_segs.head(3).items()) + "."),
                ("5. What should the team do next?",
                 f"Answer the buying questions ({int(own.answered.sum())} of {len(own)} answered on brand posts), "
                 f"work with the creators who already get them, show prices up front and name the city in ads. "
                 f"See the Action plan."),
            ]
            html("".join(f'<div class="answer"><div class="q">{q}</div><div class="a">{a}</div></div>' for q, a in items))
    with right:
        with card("needmix"):
            card_head("What the comments are about", f"{len(cust):,} customer comments, by main need")
            mix = need_mix.rename_axis("need").reset_index(name="share").iloc[::-1]
            fig = go.Figure(go.Bar(y=mix.need, x=mix.share * 100, orientation="h",
                                   marker_color=[NEED_COLORS.get(n, GREY) for n in mix.need],
                                   text=[f"{s * 100:.1f}%" for s in mix.share], textposition="outside", cliponaxis=False,
                                   hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
            fig.update_layout(xaxis_title="Share of comments (%)", showlegend=False, margin=dict(t=6),
                              xaxis_range=[0, mix.share.max() * 118], yaxis=dict(ticksuffix="  ", showline=False))
            show(fig, 430)
            st.caption("Warm colours are buying needs. Grey is off-topic or unclear.")

    with card("series"):
        card_head("One footwear marketing system, three projects", "How this project connects to the first two")
        html('<div class="why"><b>Project 1</b> measured how customers feel about Borjan, Servis and Ndure. '
             '<b>Project 2</b> decided where each brand should spend its ad budget and what the ads should say. '
             '<b>Project 3</b> finds the audience groups behind the comments, so the ad copy angles from Project 2 '
             '(price, size, delivery, quality) can be aimed at real groups of shoppers, and the reply gaps show where '
             'sales are slipping away.</div>')
        st.markdown(f"[Project 1 repo]({P1_URL}) · [Project 2 repo]({P2_URL}) · [Project 2 dashboard]({P2_APP})")


# =====================================================================
# CONTENT
# =====================================================================
def page_content():
    page_head("Dashboard / Content", "Which content attracts attention?",
              "Views show reach; likes and comments per 1,000 views show how strongly people react. "
              "Buying-question share shows whether the content moves people toward a purchase.", [VIEW_TAG, REAL_TAG])
    metric_names = {"Median views": "views", "Likes per 1,000 views": "likes_per_1k",
                    "Comments per 1,000 views": "comments_per_1k", "Buying-question share": "high_intent_share"}
    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        with card("attention"):
            card_head("Reach vs conversation", "Each bubble is a content type and format; size = number of videos")
            g = vids.groupby(["content_type", "format"]).agg(videos=("video_id", "count"), views=("views", "median"),
                                                              cpk=("comments_per_1k", "median")).reset_index()
            g = g[g.videos >= 3]
            fig = go.Figure()
            for fmt, d in g.groupby("format"):
                fig.add_trace(go.Scatter(
                    x=d.views, y=d.cpk, mode="markers+text", name=fmt, text=d.content_type,
                    textposition="top center", textfont=dict(size=11, color=INK_2),
                    marker=dict(size=np.sqrt(d.videos) * 5 + 6, color=FORMAT_COLORS.get(fmt, GREY), opacity=.75,
                                line=dict(color="#FFFFFF", width=1)),
                    customdata=d.videos,
                    hovertemplate="%{text} (" + fmt + ")<br>median views %{x:,.0f}<br>%{y:.2f} comments per 1,000 views"
                                  "<br>%{customdata} videos<extra></extra>"))
            fig.update_layout(xaxis=dict(type="log", title="Median views (log scale)"),
                              yaxis=dict(type="log", title="Comments per 1,000 views (log)"))
            show(fig, 440)
            st.caption("Top right is the sweet spot: seen by many and talked about. Only groups with 3+ videos are shown.")
    with c2:
        with card("brand_vs_creator"):
            card_head("Brand posts vs creator posts", "Medians per video")
            pt = vids.groupby("post_type").agg(videos=("video_id", "count"), views=("views", "median"),
                                               lk=("likes_per_1k", "median"), cm=("comments_per_1k", "median"))
            hi_share = cust.groupby("post_type").intent.apply(lambda s: (s == "high").mean())
            rows = ""
            for label, col, fmt in [("Videos", "videos", "{:,.0f}"), ("Median views", "views", "{:,.0f}"),
                                    ("Likes per 1,000 views", "lk", "{:.1f}"), ("Comments per 1,000 views", "cm", "{:.2f}")]:
                vals = " · ".join(f"{p.split(' ')[0]}: {fmt.format(pt.loc[p, col])}" for p in pt.index)
                rows += f'<div class="fact"><span>{label}</span><b>{vals}</b></div>'
            vals = " · ".join(f"{p.split(' ')[0]}: {hi_share.get(p, 0):.0%}" for p in pt.index)
            rows += f'<div class="fact"><span>Buying questions</span><b>{vals}</b></div>'
            html(rows)
            st.caption("Brand posts reach more people (likely paid promotion), but creator posts get far more "
                       "reaction and buying questions per view.")
        with card("metric_pick"):
            card_head("Compare content types", "Pick a measure")
            m = segmented("Measure", list(metric_names), "content_metric", "Comments per 1,000 views")
            col = metric_names[m]
            agg = "mean" if col == "high_intent_share" else "median"
            d = vids.groupby("content_type")[col].agg(agg).sort_values()
            fig = go.Figure(go.Bar(y=d.index, x=d.values * (100 if col == "high_intent_share" else 1), orientation="h",
                                   marker_color=NAVY, hovertemplate="%{y}: %{x:,.2f}<extra></extra>"))
            fig.update_layout(xaxis_title=m + (" (%)" if col == "high_intent_share" else ""), margin=dict(t=6),
                              yaxis=dict(ticksuffix="  ", showline=False), showlegend=False)
            show(fig, 300)
    with st.expander("Full content table"):
        t = T["content_summary"]
        st.dataframe(t.style.format({"median_views": "{:,.0f}", "median_views_per_day": "{:,.1f}",
                                     "median_likes_per_1k": "{:.1f}", "median_comments_per_1k": "{:.2f}",
                                     "high_intent_share": "{:.0%}"}), hide_index=True)
        st.caption("YouTube's API doesn't share 'shares', so shares are not included. Instagram data can be added "
                   "later with the same columns (platform = Instagram).")


# =====================================================================
# AUDIENCE WANTS
# =====================================================================
def page_wants():
    page_head("Dashboard / Audience", "What does the audience want?",
              "Every comment is labelled with its main need. Word lists in English, Roman Urdu and Urdu label the "
              "clear cases; a multilingual embedding model labels similar comments the word lists miss.",
              [VIEW_TAG, REAL_TAG])
    left, right = st.columns([3, 2], gap="medium")
    with left:
        with card("brand_needs"):
            card_head("Needs by brand", "Share of each brand's customer comments (praise and off-topic hidden)")
            hide = {"Other / off-topic", "General praise / blessing", "Praise for the video"}
            d = cust[~cust.need_label.isin(hide)]
            tab = (pd.crosstab(cust.brand, cust.need_label, normalize="index") * 100)
            cols = [c for c in NEED_COLORS if c in tab.columns and c not in hide]
            order = [b for b in BRANDS if b in tab.index]
            fig = go.Figure()
            for c in cols:
                fig.add_trace(go.Bar(y=order, x=tab.loc[order, c], name=c, orientation="h",
                                     marker_color=NEED_COLORS[c], hovertemplate=c + ": %{x:.1f}%<extra>%{y}</extra>"))
            fig.update_layout(barmode="stack", xaxis_title="Share of the brand's comments (%)",
                              yaxis=dict(autorange="reversed", ticksuffix="  ", showline=False),
                              legend=dict(font=dict(size=11)), margin=dict(t=90))
            show(fig, 470)
            st.caption(f"Based on {len(d):,} comments with a clear need.")
    with right:
        with card("examples"):
            card_head("Hear it in their words", "Real comments for one need")
            needs = [n for n in NEED_COLORS if n in set(cust.need_label)]
            pick = st.selectbox("Need", needs, index=needs.index("Availability / location") if "Availability / location" in needs else 0,
                                key="need_pick")
            ex = cust[cust.need_label == pick].drop_duplicates("text")
            ex = ex.sample(min(7, len(ex)), random_state=1) if len(ex) else ex
            html("".join(f'<div class="quote">{esc(r.text)[:220]}<br><span>{r.brand} · {r.lang.replace("_", " ")}</span></div>'
                         for r in ex.itertuples()))
        with card("languages"):
            card_head("Languages", "How shoppers write")
            lang = cust.lang.replace({"roman_urdu": "Roman Urdu", "english": "English", "urdu": "Urdu",
                                      "short_unclear": "Short / unclear", "emoji/symbols": "Emoji only"}).value_counts(normalize=True)
            html("".join(f'<div class="fact"><span>{k}</span><b>{v:.0%}</b></div>' for k, v in lang.items()))

    with card("method"):
        card_head("How the grouping works, and how well", "Discovery clustering and checks")
        c1, c2 = st.columns([3, 2], gap="medium")
        with c1:
            cm = T["cluster_map"].merge(com_all[["comment_id", "brand", "text"]], on="comment_id")
            cm = cm[cm.brand.isin(picked)]
            names = T["clusters"].set_index("cluster").main_need_label
            cm["group"] = cm.cluster.map(names)
            cm = cm.sample(min(2500, len(cm)), random_state=0)
            fig = go.Figure()
            for gname, d in cm.groupby("group"):
                fig.add_trace(go.Scattergl(x=d.x, y=d.y, mode="markers", name=gname,
                                           marker=dict(size=5, color=NEED_COLORS.get(gname, GREY), opacity=.65),
                                           text=d.text.str[:80], hovertemplate="%{text}<extra>" + gname + "</extra>"))
            fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), legend=dict(font=dict(size=11)),
                              margin=dict(t=70))
            show(fig, 420)
            st.caption("Each dot is a comment, placed by meaning (2-D view of the embeddings) and coloured by the "
                       "K-Means cluster it fell into. Similar comments land together even in different languages.")
        with c2:
            html(f'<div class="fact"><span>Labelled by word lists</span><b>{M["labelled_by_word_list"]:,}</b></div>'
                 f'<div class="fact"><span>Labelled by nearest neighbours</span><b>{M["labelled_by_neighbours"]:,}</b></div>'
                 f'<div class="fact"><span>Neighbour check (5-fold accuracy)</span><b>{M["knn_cv_accuracy"]:.0%}</b></div>'
                 f'<div class="fact"><span>Discovery clusters (best by silhouette)</span><b>{M["k"]}</b></div>'
                 f'<div class="fact"><span>Cluster–need agreement, embeddings (NMI)</span><b>{M["nmi_embeddings_vs_needs"]:.2f}</b></div>'
                 f'<div class="fact"><span>Cluster–need agreement, TF-IDF baseline</span><b>{M["nmi_tfidf_vs_needs"]:.2f}</b></div>')
            st.caption("Embeddings group comments by need better than plain word counts (TF-IDF), which supports "
                       "using them. Silhouette scores are low (about 0.14): short comments overlap a lot, so "
                       "clusters are a guide, not hard boundaries.")
        with st.expander("All discovery clusters"):
            st.dataframe(T["clusters"][["cluster", "size", "main_need_label", "purity", "examples"]]
                         .style.format({"purity": "{:.0%}"}), hide_index=True)


# =====================================================================
# SEGMENTS
# =====================================================================
def page_segments():
    page_head("Dashboard / Segments", "Which audience groups should the brand address?",
              "Each commenter is placed in one group by what they asked or said. Problems come first, then buying "
              "questions, then everything else.", [VIEW_TAG, REAL_TAG])
    seg = T["segments"].set_index("segment")
    g = cust.groupby("segment").agg(people=("author", "nunique"), comments=("comment_id", "count"),
                                    hi=("intent", lambda s: (s == "high").mean()))
    g = g.reindex([s for s in seg.index if s in g.index])
    left, right = st.columns([3, 2], gap="medium")
    with left:
        with card("seg_chart"):
            card_head("Audience groups", "Number of people in each group")
            d = g.drop(index=[i for i in ["Off-topic / unclear"] if i in g.index]).iloc[::-1]
            colors = [BAD if s == "Unhappy customers" else ("#EB6834" if h > 0.5 else (NAVY if s == "Ad & meme crowd" else "#1BAF7A"))
                      for s, h in zip(d.index, d.hi)]
            fig = go.Figure(go.Bar(y=d.index, x=d.people, orientation="h", marker_color=colors,
                                   text=d.people, textposition="outside", cliponaxis=False,
                                   hovertemplate="%{y}: %{x:,} people<extra></extra>"))
            fig.update_layout(xaxis_title="People", showlegend=False, margin=dict(t=6),
                              xaxis_range=[0, d.people.max() * 1.15], yaxis=dict(ticksuffix="  ", showline=False))
            show(fig, 460)
            st.caption("Orange: ready-to-buy groups. Red: unhappy customers. Green: fans and supporters. "
                       "Navy: ad buzz. Off-topic commenters are hidden.")
    with right:
        with card("seg_detail"):
            card_head("Group profile", "What they say and what to do")
            names = [s for s in g.index if s != "Off-topic / unclear"]
            pick = st.selectbox("Group", names, key="seg_pick")
            r = seg.loc[pick]
            rows = (f'<div class="fact"><span>People</span><b>{int(g.loc[pick, "people"]):,}</b></div>'
                    f'<div class="fact"><span>Comments</span><b>{int(g.loc[pick, "comments"]):,}</b></div>'
                    f'<div class="fact"><span>Most common brands</span><b>{esc(r.top_brands)}</b></div>'
                    f'<div class="fact"><span>Project 2 ad angle</span><b>{esc(r.project2_angle)}</b></div>')
            html(rows)
            html(f'<div class="why" style="margin-top:10px"><b>What to do:</b> {esc(r.action)}</div>')
            ex = cust[(cust.segment == pick) & (cust.need != "other")].drop_duplicates("text")
            ex = ex.sample(min(4, len(ex)), random_state=2) if len(ex) else ex
            html("".join(f'<div class="quote">{esc(t)[:180]}</div>' for t in ex.text))
    with st.expander("All groups in a table"):
        t = T["segments"][["segment", "commenters", "comments", "high_intent_share", "top_brands", "action", "project2_angle"]]
        st.dataframe(t.style.format({"high_intent_share": "{:.0%}"}), hide_index=True)
        st.caption("Table covers all 8 brands. Most people comment once, so a group mostly reflects that one comment.")


# =====================================================================
# UNUSUAL POSTS
# =====================================================================
MEASURES = ["views per day", "likes per 1,000 views", "comments per 1,000 views", "share of buying questions",
            "share of complaints"]


def most_common_reason(u):
    counts = {m: int(u.unusual_because.str.contains(m, regex=False).sum()) for m in MEASURES}
    best = max(counts, key=counts.get)
    return best.capitalize() if counts[best] else "-"


def page_unusual():
    page_head("Dashboard / Unusual posts", "Which marketing patterns are unusual?",
              "Each video is compared with similar videos (same format and content type). Posts far above or below "
              "their peers are flagged for a closer look; an Isolation Forest ranks how unusual they are overall.",
              [VIEW_TAG, REAL_TAG])
    u = T["unusual_posts"]
    u = u[u.brand.isin(picked)]
    kind = segmented("Show", ["Learn from it", "Investigate", "All"], "unusual_kind", "Learn from it")
    if kind != "All":
        u = u[u.what_to_do.str.startswith(kind[:5])]
    kpi_cards([
        ("Videos checked", f"{int(((vids.views >= 500) & (vids.comments >= 5)).sum()):,}", "", "",
         "with 500+ views and 5+ comments"),
        ("Flagged", f"{len(u)}", "", "", "far from similar posts on at least one measure"),
        ("Also flagged by Isolation Forest", f"{int(u.isolation_flag.sum())}", "", "", "the strongest cases"),
        ("Most common reason", most_common_reason(u), "", "", "measure most often far from similar posts"),
    ])
    left, right = st.columns([3, 2], gap="medium")
    with left:
        with card("flags"):
            card_head("Flagged posts", "Most unusual first; click a title to open the video")
            rows = []
            for r in u.head(25).itertuples():
                tone = "p1" if r.what_to_do.startswith("Inv") else "p3"
                rows.append(f'<div class="flag"><a href="{r.url}" target="_blank">{esc(r.title)[:110]}</a>'
                            f'<div class="meta">{r.brand} · {r.post_type} · {r.format} · {r.content_type} · '
                            f'{int(r.views):,} views · {int(r.comments):,} comments</div>'
                            f'<div class="why2"><span class="pill {tone}">{esc(r.what_to_do)}</span> {esc(r.unusual_because)}</div></div>')
            html("".join(rows) if rows else '<div class="why">No flagged posts for this selection.</div>')
    with right:
        with card("post_types"):
            card_head("Post audience types", "Videos grouped by what their commenters talk about (K-Means)")
            pt = T["post_audience_types"]
            html("".join(f'<div class="fact"><span>{esc(r.audience_type)}</span><b>{int(r.posts)} posts · '
                         f'{r.high_intent_share:.0%} buying, {r.praise_share:.0%} praise</b></div>'
                         for r in pt.sort_values("high_intent_share", ascending=False).itertuples()))
            x = vids[vids.audience_type != "Too few comments to tell"]
            if len(x):
                tab = pd.crosstab(x.content_type, x.audience_type)
                st.dataframe(tab, use_container_width=True)
            st.caption("Only videos with 10+ customer comments are typed. Shopper posts are where buying questions "
                       "pile up, so they need replies fastest.")


# =====================================================================
# LOST SALES (reply gaps)
# =====================================================================
def page_gaps():
    page_head("Dashboard / Reply gaps", "Buying questions nobody answers",
              "A buying question counts as answered when the video's owner replied in the same thread. On creator "
              "videos the brand never replies, so those questions only reach the creator.", [VIEW_TAG, REAL_TAG])
    q = cust[(cust.intent == "high") & (~cust.is_reply)]
    own, cre = q[q.post_type == "Brand's own post"], q[q.post_type != "Brand's own post"]
    cities = T["city_mentions"]
    kpi_cards([
        ("Buying questions", f"{len(q):,}", "", "", "top-level comments asking to buy"),
        ("On brand posts", f"{len(own):,}", f"{int(own.answered.sum())} answered", "bad", "brands' own YouTube videos"),
        ("On creator posts", f"{len(cre):,}", f"{cre.answered.mean():.0%} answered by creator" if len(cre) else "", "neutral",
         "the brand never sees these"),
        ("Most-named city", cities.iloc[0].city, f"{int(cities.iloc[0].mentions)} mentions", "neutral", "in all comments"),
    ])
    left, right = st.columns([3, 2], gap="medium")
    with left:
        with card("gap_chart"):
            card_head("Where the buying questions are", "By brand and post type")
            d = q.groupby(["brand", "post_type"]).size().unstack(fill_value=0)
            d = d.reindex([b for b in BRANDS if b in d.index])
            fig = go.Figure()
            for p in d.columns:
                fig.add_trace(go.Bar(x=d.index, y=d[p], name=p, marker_color=POST_COLORS.get(p, GREY),
                                     hovertemplate="%{x}: %{y} questions<extra>" + p + "</extra>"))
            fig.update_layout(barmode="stack", yaxis_title="Buying questions", margin=dict(t=40))
            show(fig, 360)
        with card("leads"):
            card_head("Creators whose viewers ask to buy", "Partnership leads: give them prices, sizes and the order link")
            ld = T["creator_leads"]
            ld = ld[ld.brand.isin(picked)].head(12)
            st.dataframe(ld.rename(columns={"answered_by_creator": "answered by creator"})
                         .style.format({"answered by creator": "{:.0%}"}), hide_index=True, use_container_width=True)
    with right:
        with card("unanswered"):
            card_head("Unanswered questions", "Newest first; download the full list for the support team")
            un = q[~q.answered].sort_values("published", ascending=False)
            html("".join(f'<div class="quote">{esc(r.text)[:200]}<br><span>{r.brand} · {r.need_label} · '
                         f'{r.post_type.split(" ")[0]} post · {r.published}</span></div>' for r in un.head(8).itertuples()))
            st.download_button("Download unanswered questions (CSV)",
                               un[["brand", "post_type", "channel", "need_label", "text", "published", "url"]].to_csv(index=False),
                               "unanswered_buying_questions.csv", "text/csv")
        with card("cities"):
            card_head("Cities shoppers name", "Mentions in comments")
            html("".join(f'<div class="fact"><span>{r.city}</span><b>{int(r.mentions)}</b></div>'
                         for r in cities.head(8).itertuples()))
    st.caption("The API returns up to 5 replies per thread, so a few owner replies in very long threads may be missed.")


# =====================================================================
# ACTION PLAN
# =====================================================================
def brief_text(acts):
    lines = [f"AUDIENCE ACTION PLAN | {view}", "Pakistan Social Audience & Campaign Intelligence Engine (Project 3)",
             f"Based on {len(cust):,} real YouTube comments on {vids.video_id.nunique():,} videos.", ""]
    for area, g in acts.groupby("area", sort=False):
        lines.append(f"=== {area.upper()} ===")
        for r in g.itertuples():
            lines += [f"[Priority {r.priority}] {r.brand}: {r.action}", f"   Evidence: {r.evidence}"]
        lines.append("")
    lines.append(f"Dashboard and code: {REPO_URL}")
    return "\n".join(lines)


def page_actions():
    page_head("Dashboard / Action plan", "What should the marketing team do next?",
              "Every action comes from a rule applied to the data, and shows the number that triggered it.",
              [VIEW_TAG, REAL_TAG])
    a = T["action_plan"]
    a = a[(a.brand == "All brands") | a.brand.apply(lambda b: any(p in str(b) for p in picked))]
    areas = ["All areas"] + sorted(a.area.unique())
    area = segmented("Area", areas, "act_area", "All areas")
    if area != "All areas":
        a = a[a.area == area]
    with card("actions"):
        card_head("Actions", "Priority 1 first")
        html("".join(f'<div class="act"><div class="top"><span class="pill p{r.priority}">Priority {r.priority}</span>'
                     f'<span class="pill">{esc(r.area)}</span><span class="pill">{esc(r.brand)}</span></div>'
                     f'<div class="what">{esc(r.action)}</div><div class="ev">Evidence: {esc(r.evidence)}</div></div>'
                     for r in a.itertuples()))
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Download the action plan (TXT)", brief_text(a), "audience_action_plan.txt", "text/plain",
                           use_container_width=True)
    with c2:
        st.download_button("Download the action plan (CSV)", a.to_csv(index=False), "audience_action_plan.csv",
                           "text/csv", use_container_width=True)
    with card("p2link"):
        card_head("Take it into Project 2", "Turn audience groups into ads")
        html('<div class="why">Project 2\'s Ad copy studio writes ads around angles like <b>price</b>, <b>size</b>, '
             '<b>delivery</b> and <b>quality</b>. Use the largest buying group for each brand (Segments page) to pick '
             'the lead angle, and use the city list (Reply gaps page) to target the ads.</div>')
        st.markdown(f"[Open the Project 2 dashboard]({P2_APP})")


# =====================================================================
# REPLY ASSISTANT
# =====================================================================
def page_replies():
    page_head("Dashboard / Reply assistant", "Ready-to-paste replies",
              "Sample replies for each kind of comment, in English and Roman Urdu. Fill in the link, price or "
              "sale date, then copy.", [VIEW_TAG])
    keys = [k for k in REPLIES]
    labels = {k: NEED_LABEL[k] for k in keys}
    c1, c2 = st.columns([2, 3], gap="medium")
    with c1:
        with card("reply_in"):
            card_head("Settings")
            need = st.selectbox("Comment type", keys, format_func=lambda k: labels[k], key="reply_need")
            brand = st.selectbox("Brand", BRANDS, key="reply_brand")
            lang = segmented("Language", ["English", "Roman Urdu"], "reply_lang", "Roman Urdu")
            link = st.text_input("Shop link", f"{brand.lower().replace(' ', '')}.com.pk", key="reply_link")
            price = st.text_input("Price (Rs.)", "4,999", key="reply_price")
            end = st.text_input("Sale ends", "30 November", key="reply_end")
    with c2:
        with card("reply_out"):
            card_head(f"Reply: {labels[need]}", f"{brand}, {lang}")
            text = REPLIES[need]["en" if lang == "English" else "ru"].format(
                brand=brand, link=link, price=price, end_date=end)
            st.code(text, language=None)
            card_head("Real comments this reply fits", "Unanswered, for the chosen brand")
            ex = cust[(cust.need == need) & (cust.brand == brand) & (~cust.answered)].drop_duplicates("text")
            ex = ex.sample(min(5, len(ex)), random_state=3) if len(ex) else ex
            html("".join(f'<div class="quote">{esc(t)[:200]}</div>' for t in ex.text) or
                 '<div class="why">No unanswered comments of this type for this brand.</div>')
    st.caption("Sample wording written for a class project, not the brands' real customer-service scripts.")


# =====================================================================
# BIG DATA BENCHMARK
# =====================================================================
def page_bigdata():
    page_head("Dashboard / Big Data", "Does the engine scale?",
              "The comment pipeline (labelling needs and rolling them up by brand, video and audience group) run "
              "on growing copies of the data, in pandas and in Apache Spark.", [REAL_TAG])
    if BENCH is None:
        st.info("Benchmark results are not added yet.")
        return
    with card("bench"):
        card_head("Run time by data size", "Lower is better; log scales")
        fig = go.Figure()
        for eng, d in BENCH.groupby("engine"):
            fig.add_trace(go.Scatter(x=d.rows, y=d.seconds, mode="lines+markers", name=eng,
                                     line=dict(color={"Pandas": "#2A78D6", "Spark": "#EB6834"}.get(eng, GREY), width=3),
                                     hovertemplate=eng + ": %{x:,} rows in %{y:.1f} s<extra></extra>"))
        fig.update_layout(xaxis=dict(type="log", title="Comments"), yaxis=dict(type="log", title="Seconds"))
        show(fig, 380)
        st.dataframe(BENCH, hide_index=True)
        if "note" in BENCH:
            st.caption(str(BENCH.note.dropna().iloc[0]) if BENCH.note.notna().any() else "")


# =====================================================================
# DATA & LIMITATIONS
# =====================================================================
def page_about():
    page_head("Dashboard / About", "Data, method and limitations",
              "Where the data came from, how it was cleaned and what it can't tell you.", [REAL_TAG])
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with card("funnel"):
            card_head("From collection to analysis", "Every step is in the repo")
            steps = [("Videos found by search and brand channels", "2,561"),
                     ("Kept: title names the brand, not from India or abroad, has comments", "853 videos"),
                     ("Comments downloaded (official YouTube Data API)", "8,508"),
                     ("Removed: Bata (channel is Bata India), foreign videos, empty or foreign-language comments", "−1,741"),
                     ("Removed: 3 international sneaker videos (e.g. 'Air Max Metro')", f"−{6767 - len(com_all):,}"),
                     ("Comments analysed", f"{len(com_all):,}"),
                     ("…of which customer comments (not owner replies)", f"{(~com_all.owner_reply).sum():,}")]
            html("".join(f'<div class="fact"><span>{a}</span><b>{b}</b></div>' for a, b in steps))
            st.caption("Commenter names are never stored; each person is an anonymous code. Each video keeps its URL "
                       "and collection date.")
        with card("tables"):
            card_head("The brief's tables", "Table A (posts) and Table B (comments)")
            ta = vids_all[["video_id", "brand", "platform", "content_type", "format", "post_type", "title", "views", "likes",
                           "comments", "age_days", "published", "url", "collected_on"]].rename(
                columns={"video_id": "post_id", "comments": "comments_count", "age_days": "days_since_post"})
            ta["shares"] = "not available (YouTube API)"
            tb = com_all[["video_id", "comment_id", "brand", "text", "lang", "need_label", "intent", "published", "collected_on"]].copy()
            tb["sentiment"] = np.select([tb.need_label.isin(["Complaint / problem"]),
                                         tb.need_label.isin(["Product praise / wants it", "General praise / blessing",
                                                             "Praise for the video", "Quality / comfort"])],
                                        ["Negative", "Positive"], "Neutral")
            tb = tb.rename(columns={"video_id": "post_id", "text": "comment_text", "lang": "language_type",
                                    "need_label": "topic", "intent": "purchase_intent"})
            st.download_button("Download Table A: posts (CSV)", ta.to_csv(index=False), "table_a_posts.csv", "text/csv",
                               use_container_width=True)
            st.download_button("Download Table B: comments (CSV)", tb.to_csv(index=False), "table_b_comments.csv",
                               "text/csv", use_container_width=True)
            st.caption("Sentiment in Table B is a simple rule from the topic (complaint = negative, praise = positive). "
                       "Project 1 covers proper sentiment analysis.")
    with c2:
        with card("limits"):
            card_head("Limitations", "Read these before acting on the numbers")
            st.markdown(
                "- **YouTube only.** Instagram, TikTok and Facebook comments can't be collected within their terms. "
                "The tables already have a platform column, so Instagram post data can be added later.\n"
                "- **No shares.** The YouTube API doesn't report shares.\n"
                "- **Creator videos aren't brand posts.** Most comments come from creators' sale vlogs and reviews, "
                "so they show what shoppers ask, not how the brand's own page performs.\n"
                "- **Paid views.** Brand videos with huge views and almost no comments are probably promoted; views "
                "there measure ad spend more than interest.\n"
                "- **Roman Urdu is messy.** Spellings vary, so the word lists miss some comments and mislabel a few. "
                "About a third of comments are short or off-topic and stay unlabelled.\n"
                "- **Small groups.** Size questions (38 comments) and complaints (about 70) are small samples.\n"
                "- **Correlation, not cause.** 'Prices in the title → fewer price questions' is a pattern worth testing, "
                "not proof.\n"
                "- **Replies.** Only up to 5 replies per thread come back from the API, so a few answers may be missed.\n"
                "- **Brands chosen by us.** Bata was dropped because its YouTube channel is Bata India.")
        with card("links"):
            card_head("Links")
            st.markdown(f"- [GitHub repo]({REPO_URL})\n- [Project 1: sentiment analysis]({P1_URL})\n"
                        f"- [Project 2: ad budget optimizer]({P2_URL})")


# ---------------- NAVIGATION ----------------
pages = [
    st.Page(page_overview, title="Overview", icon=":material/space_dashboard:", url_path="overview", default=True),
    st.Page(page_content, title="Content that works", icon=":material/smart_display:", url_path="content"),
    st.Page(page_wants, title="What the audience wants", icon=":material/forum:", url_path="audience"),
    st.Page(page_segments, title="Audience groups", icon=":material/groups:", url_path="segments"),
    st.Page(page_unusual, title="Unusual posts", icon=":material/troubleshoot:", url_path="unusual"),
    st.Page(page_gaps, title="Reply gaps", icon=":material/mark_chat_unread:", url_path="reply-gaps"),
    st.Page(page_actions, title="Action plan", icon=":material/checklist:", url_path="action-plan"),
    st.Page(page_replies, title="Reply assistant", icon=":material/quickreply:", url_path="replies"),
    st.Page(page_bigdata, title="Big Data benchmark", icon=":material/storage:", url_path="big-data"),
    st.Page(page_about, title="Data & limitations", icon=":material/info:", url_path="about"),
]
st.navigation(pages).run()
