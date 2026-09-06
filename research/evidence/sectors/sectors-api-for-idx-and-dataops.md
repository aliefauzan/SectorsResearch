# sectors.app/api-for-idx + /data-operations + /api — page captures

Captured 4 September 2026 via browser. curl is blocked on sectors.app by a Vercel security
checkpoint, so these were read through a real browser session.

---

## https://sectors.app/api-for-idx

Title: "API Saham Indonesia — IDX & Bursa Efek Indonesia (BEI) API"
Bilingual page (EN/ID toggle on the FAQ).

Headline stats:
- 99.9%+ of IDX-listed companies covered
- Daily updates with self-healing corrections
- REST + MCP — JSON endpoints & natural-language query
- From $1.45 per day, billed annually ($59/month when billed monthly)

CTAs: "Start free — no credit card" (/auth) · "Open API Playground" (/api) · "Read the API docs" (docs.sectors.app)

Five differentiators claimed:
1. 99.9%+ IDX coverage "including small caps and less liquid stocks that are often missed by
   global APIs that only cover the most popular Indonesian stocks"
2. Proprietary data and direct source extraction — "derived from direct PDF extraction of IDX
   filings, earnings reports, transcripts, guidance (e.g. Public Expose) and proprietary data
   collection methods, unavailable through any other API provider. Line-level data for
   financial statements, insider transactions, risk breakdowns, liability classifications"
3. Natural language query built into the API
4. Upstream corrections — "even when the upstream data source has misfiled or erroneous data,
   our pipelines detect and correct these issues"
5. Enterprise-ready integrations — REST JSON, MCP connectors, Sectors Workflow

FAQ (EN/ID), free-tier answer verbatim:
> "Sectors offers free access to core app features, while API quota and endpoint availability
> depend on plan tier. However, with a free account (no credit card required), you can access
> 90% of our core product features, and win more API credits through our referral program,
> making it possible to build and test with real IDX data on our API infrastructure at no cost.
> As your product grows, you can move to higher tiers for greater API throughput, broader
> endpoint access, and production-ready support for business-critical workflows."

Enterprise: "unlimited API calls, custom data needs, and dedicated support" — help@sectors.app

---

## https://sectors.app/api

Three tabs: **Get Started** · **API Playground** · **API Key Management**.
The Playground and Key Management tabs render no content when logged out — both are gated.

Get Started content matches the docs quick-start: upgrade to Insider, obtain key from API Key
Management, `headers = {"Authorization": api_key}` (raw key, no Bearer). Python/JavaScript/R
snippets.

---

## https://sectors.app/data-operations

Title: "Data Ops for the Indonesia Financial Market | The Sectors Perspective"

AI-assisted pipeline stages:
- Information retrieval from raw financial reports (PDF)
- Data extraction from filings (Excel, XBRL)
- Intelligent parsing, tagging and structuring
- Parsing, tagging, entity relationship mapping and automatic summary of news articles
- Quality assurance and automatic anomaly detection, flagged for human review
- Summarization, trend discovery, insight generation in sector and company reports
- Self-learning weights for "investability" dimensions and scores

Three annotations:
1. **Reviewed by humans** — human-in-the-loop on every AI step; "led by banking veterans and
   former data journalists"
2. **Standardization with good sense** — worked NPL example (provision of restructured loans
   vs collectibility classification); decisions documented in a data dictionary
3. **No magic formulas. Explainable models by default** — investability score methodology and
   per-dimension weights published in every stock report

Standards:
- IDX standards by default
- Banks: loan collectibility and financial asset quality per OJK, Basel III, Bank Indonesia
- Industry/sub-industry/sector: **IDX-IC** (Indonesian Industry Classification)
- "To date, we are the only financial data provider that are engineered on top of these standards."

Sources: financial reports and company filings (IDX filings incl. insider transactions and
EGMs, annual and sustainability reports, balance sheets, income statements, cash flow
statements); financial news (Indonesian portals, sector news, press releases, company
announcements, dividend announcements, stock splits); market data (stock prices, indices,
exchange rates, market cap, trading volume, upcoming IPOs, analyst recommendations); in-house
market research (competitor, supply chain, market share, customer composition & concentration,
financing asset quality & credit risk for banks, bank profitability).

Coverage: "99% coverage, at least 30% more than the nearest competitor", companies analyzed daily.

"Exclusively on Sectors" list:
- Verifiable first-party revenue segments by product line, business unit, **and even key customers**. Comparable across peers.
- Verifiable first-party cost structures by cost category. Comparable across peers.
- Financing Asset Quality for banks, standardized and OJK-compliant
- The IDX Total Index
- Detailed industry peer analysis and comparison tables
- Dynamic fact sheets of 15 IDX stock indices (KOMPAS100, IDX30, etc.)
- More than 10 IDX-specific stock screening, analytics and visual tools

Also claims numbers are "externally verifiable — you can trace back the source of each data
point to its original source document, and mathematically verify the calculations".
