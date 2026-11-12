# Joota Pulse: audience intelligence for Pakistani footwear brands

**Project 3, Big Data Analytics (UMT Lahore)** · Usama Hanif · *Pakistan Social Audience & Campaign Intelligence Engine*

A marketing web app that reads **6,724 real YouTube comments** on **690 videos** about **8 Pakistani footwear brands**, groups them into audience needs and audience groups, flags unusual posts and turns the findings into a marketing action plan, with replies the team can paste.

Borjan, Servis and Ndure are the core brands, the same three as in [Project 1](https://github.com/usamahanif349/pk-footwear-sentiment-analysis) and [Project 2](https://github.com/usamahanif349/pk-footwear-budget-optimizer). Stylo, Metro, Hush Puppies, Insignia and ECS widen the audience.

🔗 **Joota Pulse web app:** https://usamahanif349.github.io/joota-pulse/ · **Analyst version (Streamlit):** https://pk-footwear-audience-engine.streamlit.app/

## What a marketing team gets

| Page | What it does |
|---|---|
| **Today** | Missed sales estimate, buying questions, reply rate, hottest city, and the 3 things to do today |
| **Leads inbox** | Every unanswered buying question in one list; click one and get a ready reply in Roman Urdu or English |
| **Your customers** | 11 customer groups (Where-can-I-buy askers, Price checkers, Deal hunters…) with what to do for each |
| **Post this, not that** | Content that starts conversations vs content that doesn't, plus a creator leaderboard |
| **Competitors** | Brand scorecard: buying questions, top ask, replies, complaints, ad buzz for all 8 brands |
| **Campaign ideas** | Ready-to-run campaigns, each with the number behind it and ad copy in English and Roman Urdu |
| **Client report** | One-click 1-page PDF for a brand |
| **How it works** | Method, accuracy checks, Big Data benchmark, data, privacy and limitations |

## The headline

> **Brands answered 1 of 65 buying questions on their own YouTube videos.** Another **832 buying questions** ("Price?", "Location send karen", "Order kaise karein?") sit under creators' sale vlogs and reviews, where the brand never replies.

## The five questions the brief asks

| Question | What the data says |
|---|---|
| **1. Which content attracts attention?** | Brand posts get the reach (median 66,402 views, likely paid promotion) but almost no conversation: 0.02 comments per 1,000 views. Creator posts get **35× more comments per view**, **3× more likes per view** and **18% buying questions vs 10%**. Reviews and unboxings start the most conversation. |
| **2. What does the audience want?** | Beyond praise: **where to buy** (9% of comments), **price** (5%), sales and discounts, how to order, contact details, quality and size. 32% of Servis comments are nostalgia and meme buzz about its classic ad. |
| **3. Which patterns are unusual?** | **56 posts** are far from similar posts (same format and content type): 47 to learn from (for example creator sale vlogs with 20–60× the usual comments per view) and 9 to investigate (complaint spikes, hidden or near-zero likes). |
| **4. Which audience groups should the brand address?** | 4,248 commenters in 12 groups. Largest buying groups: **Where-can-I-buy askers (458 people)**, **Price checkers (270)**, **Deal hunters (126)**, plus Order & delivery askers, Contact seekers, Size & fit askers and 46 Unhappy customers. |
| **5. What should the team do next?** | Answer buying questions within 24 hours; give top creators a pinned comment with prices and the order link; move part of the video budget to creator collaborations; show prices up front (videos with prices in the title get **38% fewer price questions**); run city-targeted ads (Lahore, Karachi, Faisalabad named most); A/B test a Servis throwback ad. |

## How it works

```
YouTube Data API (official)          Colab                         this repo
───────────────────────────          ─────                         ─────────
search + brand channels  ──►  853 videos, 8,508 comments  ──►  cleaning ──► 690 videos, 6,724 comments
                                                                    │
           multilingual sentence embeddings (Colab GPU)  ◄──────────┤
                                                                    ▼
 1. needs.py     word lists (English, Roman Urdu, Urdu) label clear comments,
                 nearest neighbours in embedding space label similar ones,
                 K-Means discovery clusters, checked against a TF-IDF baseline
 2. content.py   attention metrics per video; unusual posts by peer z-scores + Isolation Forest;
                 K-Means "post audience types"
 3. segments.py  audience groups per commenter, reply gaps, creator leads, city mentions,
                 rule-based action plan with the evidence behind each action
 4. app.py       analyst version (Streamlit) + one-page PDF client report
 5. web/         Joota Pulse web app (HTML/CSS/JS); src/web/export.py writes web/data.json
```

**Method checks**
- Neighbour labelling agrees with the word lists 81% of the time (5-fold check).
- Embedding clusters match the needs better than TF-IDF clusters: NMI **0.43 vs 0.34**.
- Silhouette is low (about 0.14) because short comments overlap; clusters are a guide, not hard boundaries.

**Big Data benchmark** (`src/bigdata/benchmark.py`, free 2-core Google Colab): the labelling and roll-up pipeline in pandas vs Apache Spark.

| Comments | pandas | Spark | Labels match |
|---|---|---|---|
| 6,767 | 1.3 s | 13.6 s | 100% |
| 100,000 | 11.7 s | 25.6 s | 100% |
| 1,000,000 | 115 s | 226 s | 100% |
| 3,000,000 | 347 s | 675 s | 100% |

Both scale in a straight line. On one small machine Spark is about 2× slower because of its start-up and coordination cost; it pays off on a cluster or when the data outgrows one machine's memory.

## Data

- **Real, public data only.** Video stats and comments from the official YouTube Data API v3, collected on 12 November 2026. Every video keeps its URL and collection date.
- **Privacy:** commenter names are never stored (each person is an anonymous code); phone numbers, e-mails, @handles and order numbers are removed from comment text.
- **Cleaning:**
  - **Bata** was dropped because its YouTube channel is Bata India.
  - Indian and other foreign videos, international sneaker videos and foreign-language comments were removed.
  - Search results had to name the brand in the title.
- **The brief's tables:** Table A (posts) and Table B (comments) can be downloaded from the dashboard's *Data & limitations* page.

## Limitations

- **YouTube only.** Instagram, TikTok and Facebook comments can't be collected within their terms. Every table has a `platform` column, so Instagram post data can be added later.
- **No shares.** The YouTube API has no share counts.
- **Most comments are on creator videos.** They show what shoppers ask, not how a brand's own page performs.
- **Inflated views.** Brand videos with huge views and almost no comments are probably promoted.
- **Messy Roman Urdu.** Spelling varies, so some comments are missed or mislabelled. About a third are short or off-topic and stay unlabelled.
- **Small groups.** Size questions (38 comments) and complaints (73) are small samples.
- **Patterns, not proof.** Patterns like "prices shown → fewer price questions" are correlations to test, not proof.
- **Missed replies.** The API returns up to 5 replies per thread, so a few owner replies may be missed.

## Run it

Command Prompt, from the repo folder:

```
pip install -r requirements.txt
python run_pipeline.py
streamlit run src\dashboard\app.py
```

`data/raw/` holds the cleaned YouTube data and the embeddings; `notebooks/` holds the Colab collection and embedding steps.

## The series

| | Project | Question |
|---|---|---|
| 1 | [Sentiment analysis](https://github.com/usamahanif349/pk-footwear-sentiment-analysis) | How do customers feel about each brand? |
| 2 | [Ad budget optimizer](https://github.com/usamahanif349/pk-footwear-budget-optimizer) | Where should each brand spend, and what should the ads say? |
| 3 | **Audience engine** (this repo) | Which audience groups exist, what do they need, and what should the team do? |

Project 2's ad copy angles (price, size, delivery, quality) map directly onto this project's audience groups.

*Built with help from Claude (AI). Sample replies in the reply assistant were written for this class project and are not the brands' real customer-service scripts.*
