# What We Can Build — Ideas Mapped to Tracks and Data

Generated from the actual endpoint inventory, not from imagination. Every idea below names
the endpoints it runs on and roughly what it costs against a 1,000-credit grant.

> **Read [`already-published.md`](already-published.md) before choosing.** Supertype has
> published working tutorials for the most obvious project in each track — a 7am scheduled
> top-movers digest, a natural-language stock chatbot, and a three-specialist-agent analyst.
> The ideas below are written to sit outside that overlap, but check your final pitch against
> it.

**Read the scoring weights first.** Real-world usability is 40%, video and storytelling 30%,
technical depth 30%. Seventy percent of your score is *whose problem this is* and *how well
you explain it*. Pick the idea whose user you can name.

---

## The data nobody else has

Before ideas, the assets. These are the parts of Sectors that a generic financial API cannot
give you, and therefore the parts most likely to produce something genuinely new:

| Asset | Endpoints | Why it's rare |
| --- | --- | --- |
| **Broker flow / bandarmology** | `/v2/broker-summary/{symbol}/`, `/v2/broker-activity/{broker_code}/`, `/v2/brokers/top/`, `/v2/foreign-flow/{symbol}/` | Per-broker daily buy/sell/net per stock, with foreign/domestic origin and retail/institutional cohort. Retail investors in Indonesia care intensely about this and it is very hard to get programmatically |
| **Broker registry with cohorts** | `/v2/brokers/` | Curated foreign/domestic + retail/mixed/institutional classification. Turns raw broker codes into a signal |
| **Mining extension** | 19 endpoints | Sites, production, reserves, licenses, IUP/IUPK, ESDM auctions, ownership trees, export destinations, commodity prices — **including private and unlisted companies** |
| **Revenue/cost segments** | `/v2/company/get-segments/{symbol}/` | Sankey-ready segment breakdowns. Sectors describes this as first-party data covering product lines, business units **and key customers** — customer-concentration data that is peer-comparable and, by their claim, available nowhere else. 1 credit, no recipe uses it |
| **Shareholders composition** | `/v2/company/shareholders-composition/{symbol}/` | Monthly, by investor category, local and foreign |
| **Suspensions** | `/v2/suspensions/` | Dates, official reasons, IDX PDF notices |
| **Corporate actions** | `/v2/company/corporate-actions/{symbol}/` | Splits, rights, warrants, bonus shares, AGM |
| **Insider filings** | `/v2/filings/` | Insider and major-shareholder buy/sell, filterable |
| **Free float** | `/v2/free-float/` | Public float percentage across the market |
| **219-field screener** | `/v2/companies/` | Arithmetic, year and quarter brackets, peer averages — 1 credit per query |

The mining extension and the broker cohort data are the two most under-exploited. Almost
every hackathon project in a stock-data event is a screener or a chatbot; almost none is
about coal licenses or foreign-institutional accumulation patterns.

### And five more found by reading the payloads, not the descriptions

A field-by-field pass over the official example responses turned up data that appears in
**no endpoint description**. Full detail in
[`../docs/api/08-hidden-data.md`](../docs/api/08-hidden-data.md):

| Hidden asset | Where | Why it's rare |
| --- | --- | --- |
| **Named institutional flow** | `company/report?sections=ownership` → `top_transactions` | Buyers and sellers named institution by institution (the BBCA example names two Fidelity entities), plus `institutional_transaction_flow` as a dated net series |
| **Whale investors & conglomerate groups** | same section | Named individuals (`Anthoni Salim`) and business groups (`Djarum Group`) per company — a ready-made ownership network |
| **Monthly ownership panel, local vs foreign** | `shareholders-composition` | 9 investor categories × local/foreign × monthly, plus shareholder counts and their change |
| **News pre-classified on 8 dimensions** | `/v2/news/` → `dimension` | Every article already scored across future / dividend / ownership / technical / valuation / financials / management / sustainability |
| **Mining ownership graph with tickers** | `mining/companies/ownership/{slug}` | Parents and subsidiaries carry both a slug and a listed `symbol` — links private mining entities to listed parents |

All of these are 1–2 credits and none require an LLM to become interesting.

---

## Track 03 · Market Intelligence — cheapest to build, hardest to differentiate

**Bar:** must produce *derived insight*. A prettier view of raw data does not qualify.

### 3.1 Bandarmology accumulation detector
Rank stocks by sustained net accumulation from **institutional foreign** brokers, separated
from retail noise, and confirm against price action.

- **Endpoints:** `/v2/brokers/` (cohorts, 1) · `/v2/broker-summary/{symbol}/top/` · `/v2/foreign-flow/{symbol}/` · `/v2/daily/{symbol}/`
- **Derivation:** a dominance score — institutional net buy as a share of total traded value, smoothed over 14 days, cross-checked against price drift. Quiet accumulation (high dominance, flat price) is the interesting quadrant.
- **Cost:** 4 credits per ticker — `broker-summary/top` 2 + `foreign-flow` 1 + `daily` 1, over a 14-day window. 50 tickers ≈ 200 credits, plus 1 once for the broker registry.
- **Why it scores:** uses data global providers don't have; the derivation is defensible; the audience (Indonesian retail investors) is real, large, and already obsessed with this concept.
- **Caution:** stay descriptive. "Institutional brokers were net buyers" is analysis. "Buy this" is financial advice, which the code of conduct prohibits.
- **Read first:** the **zero-sum trap** in [`../docs/api/10-domain-pitfalls.md`](../docs/api/10-domain-pitfalls.md). Summing buyer and seller nets always yields ~zero and will make this project look like it found nothing. Use a dominance score.

> **Mining is real and deep** — `mining.sectors.app` is a whole product with 594 coal
> companies, genuinely unlisted firms, and 17 orientation guides. But two things are
> **product-only, not in the API**: the **HBA coal benchmark** and everything on
> `reits.sectors.app`. See [`../docs/api/13-subdomains-and-terms.md`](../docs/api/13-subdomains-and-terms.md).
> **Do not plan a REITs project** — there is no REIT data in the API or MCP, so it would fail
> the eligibility check.

### 3.2 Mining licence and reserve risk map
Which listed miners hold licences expiring soon, over which commodities, in which provinces —
joined to reserves, production and their financials.

- **Endpoints:** `/v2/mining/licenses/` (`expiring_soon`) · `/v2/mining/companies/` · `/v2/mining/companies/performance/{slug}/` · `/v2/mining/resources-reserves/{province}/` · `/v2/mining/sites/` (has lat/long) · `/v2/mining/companies/ownership/{slug}/`
- **Derivation:** a concession-risk score — share of production under licences expiring within N months, weighted by reserve life and commodity price trend.
- **Cost:** modest; mostly 1-credit list endpoints.
- **Why it scores:** almost certainly unique in the field. Sites carry coordinates, so it maps beautifully — which helps the 30% video score. Real audience: commodity analysts, ESG researchers, journalists.

### 3.3 Segment concentration and revenue-fragility index

> Strengthened by a pass-7 finding: Sectors states this endpoint carries **key-customer**
> breakdowns, not just product lines — see [`../docs/api/11-data-provenance.md`](../docs/api/11-data-provenance.md).
> Customer-concentration risk that is peer-comparable and first-party is a genuinely rare
> dataset, it costs 1 credit, and no published recipe touches it.
Which companies depend on a single revenue segment or a single export destination, and how
that has moved over time.

- **Endpoints:** `/v2/companies/list_companies_with_segments/` · `/v2/company/get-segments/{symbol}/` · `/v2/mining/sales-destination/{slug}/`
- **Derivation:** a Herfindahl-style concentration index per company per year, trended.
- **Cost:** 1 credit per company-year.
- **Why it scores:** a genuine analytical primitive that Sectors' own UI doesn't surface as a ranking.

### 3.4 Loan-at-Risk (LAR) bank screen

Indonesian banks are usually screened on NPL alone. **Loan at Risk is broader** — it includes
restructured-but-currently-performing loans that NPL misses, and Sectors exposes both
components.

- **Endpoints:** `/v2/companies/` structured query on `non_performing_loan[YYYY]`, `restructured_loan_current[YYYY]`, `special_mention_loan[YYYY]`, `gross_loan[YYYY]` — **1 credit for the whole banking sector**
- **Derivation:** LAR ratio = (NPL + special mention + restructured current) ÷ gross loan, trended year over year, ranked against peers
- **Why it scores:** a defensible derived metric with a real regulatory definition behind it (OJK 40/POJK.03/2019, Basel III), computed from fields nobody combines. Sectors' own FLARE series defines it — see [`../docs/api/14-flare-community-and-engineering.md`](../docs/api/14-flare-community-and-engineering.md) — so the judges know exactly what it is and will recognise that you did the reading.
- **Cost:** essentially 1 credit. The cheapest differentiated idea in this document.

### 3.5 Post-suspension recovery study
What actually happens to a stock after an IDX suspension, grouped by the official reason.

- **Endpoints:** `/v2/suspensions/` · `/v2/daily/{symbol}/` · `/v2/company/report/{symbol}/?sections=overview`
- **Derivation:** event study — normalized price paths for N days after resumption, bucketed by suspension reason.
- **Cost:** ~1–2 credits per event.
- **Why it scores:** clear question, clear answer, unusual dataset, and the output is a chart that explains itself in a video.

### 3.5 Institutional ownership network mapper
Build the graph: companies → conglomerate groups → whale investors → named institutional
buyers and sellers, and show where the money is concentrating.

- **Endpoints:** `/v2/company/report/{symbol}/?sections=ownership` (1 credit per company) · `?sections=overview` for `affiliates` · `/v2/company/shareholders-composition/{symbol}/`
- **Derivation:** a network graph plus a concentration measure — which groups control what share of a sector's market cap, and which institutions are on both sides of the same names.
- **Cost:** ~1–3 credits per company. A 100-name universe is affordable.
- **Why it scores:** `whale_investors`, `conglomerates_group` and named `top_transactions` are undocumented and almost certainly unused by the rest of the field. Indonesian markets are conglomerate-dominated, so the output is genuinely meaningful, and network graphs demo beautifully in a three-minute video.

### 3.6 Local-vs-foreign ownership divergence tracker
Monthly, per company: are foreign institutions accumulating while domestic retail
distributes — or the reverse?

- **Endpoints:** `/v2/company/shareholders-composition/{symbol}/` (1 credit) — 9 investor categories, each split local (`_l`) and foreign (`_f`), monthly
- **Derivation:** divergence score between foreign-institutional and domestic-individual share change, ranked across a universe, cross-checked against `/v2/foreign-flow/{symbol}/`.
- **Why it scores:** the endpoint description says "monthly shareholder breakdown"; almost nobody will read far enough to notice it's a full local/foreign panel with shareholder counts. Two independent confirmations of the same signal (composition + broker flow) is exactly the "technical depth" judges reward.

### 3.7 IPO pricing post-mortem
Did the offer price land at the top or bottom of the book-building range — and did that
predict aftermarket performance?

- **Endpoints:** `/v2/listing-performance/{symbol}/` — returns `book_building_lower_bound`, `book_building_upper_bound`, `offering_price`, `shares_offered`, `percent_total_shares`, every relevant date, `prospectus_url`, and `chg_7d/30d/90d/365d`
- **Derivation:** position-in-range vs subsequent return, across every recent IPO.
- **Cost:** 1 credit per IPO.
- **Why it scores:** a single endpoint answers a real, sharply-framed question, and the answer is one chart. Perfect for a short video.

### 3.8 Free-float-adjusted crowding screen
Low free float + heavy recent retail broker participation + price extension = crowded, thin,
fragile. A risk screen rather than an opportunity screen.

- **Endpoints:** `/v2/free-float/` (10 credits for the market) · `/v2/broker-summary/{symbol}/top/` · `/v2/companies/`
- **Why it scores:** most tools point at what to buy. A tool that flags fragility is differentiated and much easier to position without straying into advice.

---

## Track 02 · Automation & Workflows — best effort-to-score ratio

**Bar:** runs autonomously on a schedule or trigger. **And you must show the schedule config
plus logs/timestamps of unattended runs in the video.**

### 2.1 Pre-market brief, delivered before open
A daily digest at 07:00 WIB to Telegram/Slack/email: overnight moves, foreign flow reversals,
new filings, fresh quarterly reports, suspensions.

- **Endpoints per run:** `/v2/companies/top-changes/` (constrained to 1 classification × 1 period = 1 credit) · `/v2/news/` · `/v2/filings/` · `/v2/idx-total/` · `/v2/suspensions/`
- **Cost:** ~4–5 credits per run if you constrain every parameter. 40 runs ≈ 200 credits.
- **Scheduler:** GitHub Actions `schedule:`, n8n, or a cron — all named as qualifying.
- **Why it scores:** the qualifying test is trivially met, the evidence requirement is easy to satisfy if you start early, and the output is legible to a non-technical judge in five seconds.
- **Do this now:** stand the scheduler up today against a stub, so by demo day you have three weeks of genuine unattended runs to show. That history *is* the evidence.
- **Handle market holidays.** IDX had a holiday on 25 August 2026, inside the build window, and **no endpoint exposes the trading calendar**. A job that doesn't skip holidays emits a blank brief; one that logs `skipped: IDX market holiday` looks deliberate. Hardcoded calendar in [`../docs/api/12-trading-calendar-and-releases.md`](../docs/api/12-trading-calendar-and-releases.md).

### 2.2 Quarterly-filing freshness watcher
Poll `/v2/companies/quarterly-financial-dates/?since=<last-seen>`; when a company reports,
pull its numbers, compute the quarter-over-quarter and year-over-year deltas, and push a card.

- **Endpoints:** `/v2/companies/quarterly-financial-dates/` (incremental — the whole point) · `/v2/financials/quarterly/{symbol}/`
- **Cost:** very low. This endpoint exists specifically for cheap freshness polling.
- **Why it scores:** shows you read the docs closely enough to find the endpoint designed for exactly this. That is the kind of thing the technical-depth criterion means when it asks "how innovative is the use of Sectors API or MCP".

> **Before you commit to any alert-shaped Track 02 idea:** Sectors already ships
> **Sectors Workflow**, an if-this-then-that builder with WhatsApp / Email / Slack / Telegram /
> Google Sheets delivery and ~60 templates, several of which are exactly "alert me when
> sector X hits a new high". A bare alert bot is a reimplementation of the host's own product.
> See [`competitive-landscape.md`](competitive-landscape.md) for what it does and how to be
> different. The brief idea above survives that test; "2.4 Watchlist condition engine" below
> only survives if the conditions are genuinely yours.

### 2.3 Insider-filing trigger with context
When an insider or major shareholder files a buy/sell, immediately push the filing alongside
the company's valuation, recent price action, and that insider's prior filing history.

- **Endpoints:** `/v2/filings/` · `/v2/company/report/{symbol}/?sections=overview` · `/v2/daily/{symbol}/`
- **Why it scores:** genuine information asymmetry, delivered fast. Very clear "who is this for" answer.

### 2.4 Dimension-routed news desk
Route every article to the right channel using the `dimension` object Sectors already
computes — dividend news to income investors, ownership news to the bandarmology channel,
sustainability news to the ESG channel.

- **Endpoints:** `/v2/news/` (the `dimension` object is on every row) · `/v2/filings/` · `/v2/company/corporate-actions/{symbol}/`
- **Why it qualifies:** scheduled polling with autonomous routing, no human per cycle.
- **Why it scores:** the classification is free and pre-computed, so the whole project is routing and delivery — cheap to build, cheap to run, and the multi-channel output is visually obvious in a demo. `thumbnail` gives you images for nothing.

### 2.5 Watchlist condition engine
User defines conditions in the screener's own `where` syntax; the job evaluates them every
close and notifies on transitions — *entering* a screen, not merely being on it.

- **Endpoints:** `/v2/companies/` structured, 1 credit per condition set per run
- **Why it scores:** transition detection (state diffing between runs) is more than a re-query, and it's cheap.
- **Caution:** this is the idea most at risk of duplicating Sectors Workflow, which already does entity selection → trigger conditions → multi-channel delivery. It is only differentiated if the *conditions* are computed by you (a composite score crossing a threshold, a cross-endpoint join) rather than selected from pre-assigned tags. If your triggers are tags, build something else.

---

## Track 01 · AI Agents & Assistants — highest ceiling, highest risk

**Bar:** custom-built agent logic or orchestration. Connecting an off-the-shelf client to the
Sectors MCP with a good prompt **does not qualify**. See the trap section in
[`../docs/api/04-mcp-and-ai-agents.md`](../docs/api/04-mcp-and-ai-agents.md).

### 1.1 Multi-step comparative research agent
"Compare BBCA, BMRI and BBRI on asset quality" → the agent plans which sections and quarters
it needs, fetches them, notices a gap, re-queries, and produces a cited comparison.

- **Your orchestration:** a planner that turns a question into an endpoint plan; a budget-aware executor; a verification pass that checks every stated number against the payload it came from; citations back to endpoint + field.
- **Endpoints:** `/v2/company/report/{symbol}/?sections=financials` · `/v2/financials/quarterly/{symbol}/` · `/v2/subsector/report/{sub_sector}/` · `/v2/companies/`
- **Why it clears the bar:** the planner, the budget governor and the verifier are all yours, and all visible in a demo.
- **Show in the video:** the plan it produced, the calls it chose, and the moment it re-queried. Invisible orchestration scores like none.

### 1.2 Filing-to-insight agent with memory
Watches filings and news, maintains per-company state across time, and answers "what changed
about this company since I last asked?"

- **Your orchestration:** persistent memory keyed by company; a diffing layer over successive snapshots; retrieval that decides what is worth surfacing.
- **Endpoints:** `/v2/filings/` · `/v2/news/` · `/v2/company/corporate-actions/{symbol}/` · `/v2/company/shareholders-composition/{symbol}/`
- **Why it clears the bar:** memory and state management are named explicitly as qualifying.

### 1.3 Numbers-verified analyst assistant
An assistant whose distinguishing feature is that **it cannot state a number it did not
fetch**. Every figure carries a citation to the endpoint and field; a post-generation checker
rejects any unsourced number and forces a re-fetch.

- **Your orchestration:** a constrained tool layer, a citation schema, and a verification pass that fails closed.
- **Why it clears the bar and scores:** hallucinated financial figures are *the* objection to LLMs in finance. A demo where the assistant refuses to answer until it has fetched the number is memorable, honest, and directly addresses a real-world problem — which is the 40% criterion.

### 1.4 Bilingual retail explainer
Takes a ticker and produces a plain-Bahasa-Indonesia explanation of what the company does,
how it earns, and what its numbers mean — grounded in segments, financials and peers, aimed
at first-time investors.

- **Endpoints:** `/v2/company/report/{symbol}/` (specific sections) · `/v2/company/get-segments/{symbol}/` · `/v2/subsector/report/{sub_sector}/`
- **Why it scores:** the clearest "real-world usability" story in this list — Indonesia has a very large population of new retail investors and very little plain-language grounded explanation. Rules explicitly accept Bahasa Indonesia with no scoring penalty.
- **Caution:** explanation, not recommendation. Disclaimer on screen.

---

## Cross-cutting advice

**Name the user in the first sentence.** "For retail investors in Indonesia who follow broker
flow but read it manually off screenshots" beats "a platform for market intelligence." Forty
percent of your score is this.

**Pick a problem you can demo in ninety seconds.** You have three minutes total and no live
session. If the value takes five minutes to explain, pick a different problem.

**Make the Sectors dependency visible.** Technical depth is verified against your repo. Name
the endpoints in the video. Show the join that no single Sectors screen gives you.

**Use the unusual data.** Ten teams will build a screener or a chatbot. Very few will touch
mining licences, suspensions, shareholder composition, or broker cohorts.

**Ship the disclaimer.** Information and analysis tool, not investment advice. It's a code-of-
conduct requirement, and it takes one line.

**Do not build a trading bot.** Automated trade execution is prohibited in every track.

---

## If you have to choose one

Given the 40/30/30 weighting and the calendar (18 days to register, 26 to submit as of
4 September 2026):

**Track 02 with a genuinely useful daily brief** is the highest-probability medal. The
qualifying bar is objective and easy to clear, the evidence requirement is free if you start
the scheduler today, the cost is predictable, and the output is instantly legible to a judge.

The public matching board backs this up: of 44 public teams,
**16 chose Track 01, 11 chose Track 03, and only 4 chose Track 02**. See
[`competitive-landscape.md`](competitive-landscape.md).

**Track 03 with a broker-flow or mining derivation** is the best differentiation play — it
uses data nobody else has and the derivation is easy to defend.

**Track 01** has the highest ceiling and the highest chance of being told your project was
"a prompt on someone else's client." Only take it if you are genuinely building the
orchestration layer, and if you can *show* it working in the video.
