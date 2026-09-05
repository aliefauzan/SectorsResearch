# Where the Data Comes From — Provenance, Standards, and Proprietary Depth

> Seventh-pass finding, from three pages not previously captured:
> <https://sectors.app/api-for-idx>, <https://sectors.app/data-operations>, and the
> tabbed <https://sectors.app/api>. Captured 4 September 2026 via browser
> (curl is blocked on sectors.app by a Vercel security checkpoint).

This matters for the hackathon in two ways. First, **"technical depth" is 30% of the score**,
and knowing *why* a number is trustworthy is the difference between using an API and
understanding it. Second, several of these datasets exist nowhere else — which is exactly
where a differentiated project lives.

---

## How the data is produced

From the data-operations page, the pipeline is **AI-assisted with a human in the loop** —
their framing, explicitly: AI is "designed to enhance the efficiency and accuracy of our
financial data products, and not to replace human judgment."

The AI-assisted stages:

- Information retrieval from **raw financial reports in PDF**
- Data extraction from filings in **Excel or XBRL**
- Intelligent parsing, tagging and structuring of financial data
- Parsing, tagging, **entity-relationship mapping** and automatic summary of news articles
- Quality assurance and **automatic anomaly detection, flagged for human review**
- Summarization, trend discovery and insight generation across sector and company reports
- **Self-learning weights** for "investability" dimensions and scores

Sources feeding it: IDX filings (insider transactions, EGMs), annual and sustainability
reports, balance sheets, income statements, cash-flow statements, Indonesian financial news
portals, press releases, company announcements, dividend and stock-split announcements,
market data (prices, indices, exchange rates, market cap, volume), upcoming IPOs, analyst
recommendations, and in-house research (competitor, supply chain, market share, customer
concentration, bank asset quality and profitability).

Stated scale: **99% of IDX companies analyzed daily**, "at least 30% more than the nearest
competitor."

---

## Three claims that should change how you use the data

### 1. Standardization involves human accounting judgment

Their own worked example is worth quoting because it's the kind of thing that silently breaks
a peer comparison:

> "An example is the treatment of 'Non-performing Loans' in balance sheets of banking
> companies. Most companies report this figure having accounted for provision of restructured
> loans, but there are instances where this figure is reported following the collectibility
> classification without further consideration."

They consult financial experts, pick a treatment, and document it in a data dictionary.

**Why this matters to you:** it means Sectors' banking metrics are *comparable across peers*
in a way that raw filings are not. If your project compares banks — asset quality, NPL, CASA,
LDR — that comparability is doing real work, and saying so in your video is a credible
technical-depth point. It also means the numbers may not match a company's own reported
figure exactly, and you should not present them as if they were verbatim filings.

### 2. Standards followed

- **IDX-IC** (Indonesian Industry Classification) for sector / sub-sector / industry / sub-industry — not GICS
- For banks: loan collectibility and financial-asset-quality classification per **OJK, Basel III, and Bank Indonesia**

They claim to be "the only financial data provider engineered on top of these standards."

This explains why the taxonomy slugs don't match global providers, and why the banking field
set is unusually deep.

### 3. Self-healing upstream corrections

From the API-for-IDX page: pipelines "detect and correct" misfiled or erroneous upstream data,
with "daily updates, self-healing upstream corrections, and event-driven enhancements."

**Practical consequence:** a value you fetched last week can legitimately change. If you cache
aggressively — and [`05-credit-budget.md`](05-credit-budget.md) tells you to — a long TTL on
fundamentals means you may be holding a figure that has since been corrected. For a six-week
hackathon this is a minor risk, but if your project's premise is a historical time series,
re-pull rather than assuming immutability.

---

## Data that exists nowhere else

The data-operations page lists what it calls data "you will not find anywhere else on the
internet". Cross-referenced against the endpoint inventory:

| Exclusive dataset | Reachable via | Endpoint |
| --- | --- | --- |
| **Revenue segments by product line, business unit, and even key customers** — verifiable, first-party, peer-comparable | ✅ API | `/v2/company/get-segments/{symbol}/` |
| **Cost structures by cost category**, peer-comparable | ✅ API | same endpoint (Sankey-ready) |
| **Financing Asset Quality for banks** — loan portfolio quality, default risk, profitability, standardized to OJK | ✅ API | screener banking fields, quarterly financials |
| **The IDX Total Index** | ✅ API | `/v2/idx-total/` |
| Detailed industry peer analysis tables | ✅ partly | company report `peers` section |
| Dynamic fact sheets for 15 IDX stock indices | ⚠️ partly | `/v2/index-daily/{index_code}/` gives prices only |
| 10+ IDX-specific screening and visual tools | ❌ product-only | — |

Note the **"even key customers"** claim on revenue segments. Customer-concentration data,
peer-comparable and first-party, is genuinely rare and is exposed through a **1-credit
endpoint**. Almost no hackathon project will touch it — and there is
[no worked recipe for it either](../04-build-plan/already-published.md).

---

## Pricing, restated precisely

The three pages quote the Insider plan differently, so here is every figure seen:

| Source | Figure |
| --- | --- |
| `/pricing` | **$53** — annual billing, "3 months free, save 25%" |
| `/api-for-idx` | **$1.45 per day** billed annually · **$59 per month** billed monthly |

`$1.45 × 365 ≈ $529/year ≈ $44/month`, so the "$53" on the pricing page and the "$1.45/day"
here are not describing the same unit. Treat the pricing page as authoritative and confirm
in checkout — none of this affects hackathon teams, who receive granted credits.

**Enterprise plans exist** with unlimited API calls, custom datasets, and dedicated support
(help@sectors.app). Relevant only if you are asked about scaling in judging.

---

## The free-tier / referral wrinkle

The API-for-IDX FAQ says something the pricing page does not:

> "with a free account (no credit card required), you can access 90% of our core product
> features, and **win more API credits through our referral program**, making it possible to
> build and test with real IDX data on our API infrastructure at no cost."

This sits awkwardly against the `/api` page's flat statement that the API "is available on our
Insider plans". The most likely reading is that a free account can obtain *some* API credits
via referrals, while the Insider plan is what grants the recurring 5,000/month allocation.

> ⚠️ **Be careful here.** The hackathon rules state that "registering additional accounts to
> obtain extra credits for the same project is a rules violation and grounds for
> disqualification." A referral program is not the same as multi-accounting, but referring
> your own teammates to farm credits for the team project is close enough to that line that
> it is not worth the risk. If you want more credits, **ask in Slack `#support`** rather than
> improvising. The intended budget is 1,000 per team — design for it.

---

## Other surfaces worth knowing

| Page | What's there |
| --- | --- |
| `/api` | Three tabs: Get Started, **API Playground**, **API Key Management**. Both of the latter are login-gated — the Playground is where you test endpoints interactively once you have an account |
| `/data-operations` | The pipeline description above |
| `/api-for-idx` | Bilingual (EN/ID) SEO landing page; comparison against global APIs and DIY pipelines |
| `/enterprise` | Enterprise API options |
| `/financial-api-workshops` | Monthly workshops, free for Insider subscribers, 1,200 students |
| `/auth` | Sign-up / sign-in |

**The API Playground is the fastest way to explore endpoints once you have an account** — it
is the one thing this dossier cannot substitute for, since it needs a login. Use it to
sanity-check response shapes before writing a parser, and cross-reference against
[`07-response-shapes.md`](07-response-shapes.md).
