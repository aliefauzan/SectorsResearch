# Every footer link, opened individually — captures
Captured 4 September 2026 via browser.

## /bulletin/search-architecture — "Architectural Notes for our Financial Search Engine"
By Samuel Chan, 17 min read, published June 22 2026.
Sections: The Technical Pieces of a Financial Search Engine · An In-Browser Search
Architecture · Indexing · Searching · Relevance Ranking · Lite-IDF Weighting for Intent and
Discrimination · Debouncing and Highlighting the Query · Search Highlighting · Driving the
Results from the Keyboard · Web Worker Support · Closing Notes · Footnotes

Key points:
- Primary search runs entirely in the browser. Corpus built offline, refreshed ~twice weekly,
  shipped to client, indexed in-memory. "The slowest part of a query is no longer the network."
- Requirements framed as breadth, precision under ambiguity, trust (determinism + speed).
- Entities searchable: companies, sectors, indices, brokers, major shareholders, conglomerate
  groups — "all first-class citizens".
- Progressive indexing: IDX index built synchronously on mount; conglomerates lazy; SGX waits
  on a fetch of valid tickers. "Readiness is per-index" — no global ready gate.
- Ticker/name/description collapsed under one identifier (the ticker). Simple retrieval,
  complexity pushed to ranking.
- Command-palette scoping: `/sg banks`, `/id ...` parsed before touching the index.
- Ranking key: {inFull, inName, inDesc, lq45}. Explicitly rejects weighted-sum scoring
  ("magic numbers ... exist to make the math work, not because they have inherent meaning").
  Uses a tiered comparator: each `||` is a tier.
- Relevance cutoff: if any name-tier match exists, drop description-only tail; else keep all.
- Lite-IDF weighting so rare tokens (pan) outweigh common ones (bank).
- Web workers keep work off the typing thread.
- Unranked-results bug "surfaced by @jigsawinthecity immediately".

## /finance/asset-quality — FLARE part 1
"Asset Quality in Banks: LARs, NPLs, & Credit Quality"
Sections: Understanding Earning Assets in the Banking Sector · Collectibility Classification
of Earning Assets · Asset Quality of Securities · of Government Securities & BI Certificates ·
of Placements · of Equity Participation · Credit Quality · Provision of Funds in Small Amounts
· Article 10 · LARs and NPLs · Non-Performing Loans · Restructured Loans · Loan at Risk ·
Incorporating Asset Quality in your Research and Analysis · Risk and Efficiency: Indonesian
Banking Sector
Citations: BI Regulation 7/2/PBI/2005; OJK 40/POJK.03/2019

## /finance/bank-liquidity — FLARE part 3
"Bank Liquidity & Credit Risk Explained"
Sections: Liquidity Coverage Ratio (LCR) · High-Quality Liquid Assets (HQLA) · Loan to
Deposit Ratio (LDR) · CASA Ratio · Capital Adequacy Ratio (CAR) + formula · Liquidity and
Risk Management of Indonesian Banks
Citations: Basel III LCR; OJK Minimum Capital Adequacy Requirement; Basel III capital definition

## /bulletin — Community Bulletin
- Refer-a-Friend: "you will be credited with points. Redeem your points for rewards, API
  credits and Sectors merchandise." Get your Referral Code.
- Student-Ambassadorship: "Open to all Indonesian and Malaysian students who are currently
  enrolled in a university."
- Merchandise tasks: complete the Practicum on Financial API Workshops · create remarkable
  tutorials or guides ft. Sectors datasets · refer 6+ friends · annual subscription
- Community manager: Samuel Chan
- FLARE 3-part series listed: 1 Earning Assets · 2 NII, NIM and IRR · 3 Bank Liquidity and
  Credit Risk
- Article: "Finding the True Free-Float on the IDX" — "IDR 11,081T across 960 listed companies"

## /enterprise — "Indonesia's Financial Database"
- 99.9% Indonesian companies indexed · 40,000 live financial and AI workflows
- 100% Indonesian economic sectors indexed, IDX specifications
- **67,900+ data points collected and processed daily**
- "Most other financial data providers have ~60% coverage of Indonesian stocks"
- Example peer comparison shown: BBCA ROA 3.46%, BBRI 3.06%, BMRI 2.53%, BBNI 1.92%,
  BSI 1.61%, Mega 2.66%, Panin 1.14%

## /financial-api-workshops
- 1,577+ satisfied students since 2020 · 12 workshops delivered · 500+ companies in region
- Jakarta venues + live Zoom · 4.9/5 average rating from 100+ participants
- "We currently do not have any planned events"
- Recordings stream with a Sectors Insider membership

## /story — Stories
"Deep dives into ownership trails, exits, and the deals reshaping Indonesia's listed companies."
- Aug 19 2026: "IMPC's 1.45 billion-share block never left the family" — record profits two
  years running, stock down 66% from January highs
- Aug 13 2026: "Indonesian Tycoons" — three major family empires taking different paths
- Aug 13 2026: "DSSA releases its buyback shares as profit keeps falling" — 9.63 billion
  treasury shares back into the market

## Remaining footer links — classified, no unique data beyond the API
/search /chat /screener /peers (product surfaces) · /indonesia /singapore /malaysia (market
landing) · /indonesia/most-traded /idx/broker /idx/foreign-flow (product views of documented
endpoints) · /indonesia/group /singapore/group (conglomerate groups) · /indonesia/bumn (SOEs)
· /indonesia/economic-sectors /indonesia/indeks · /indonesia/news /singapore/news ·
/indonesia/2026/latest (weekly digest) · /indonesia/calendars/dividend-calendar · six curated
stock-list pages · /privacy · /sitemap.xml · supertype.ai
