# sectors.app/release — full Dev Log timeline

Captured 7 September 2026. Tooling: agent-reach (`web` channel). Jina Reader and `curl` both
returned the Vercel Security Checkpoint / HTTP 429, so the page was read through the browser
pane. 28 entries, complete from first release to latest.

Page title: "Dev Logs by Sectors Financial Data Platform". Cadence is monthly, landing
between the 1st and the 16th, most often the 12th–14th.

| Date | Release name | Headline items |
| --- | --- | --- |
| 2026-08-10 | Foreign Flows | IDX Foreign Flow reports · Slash-Commands in Search Console · Better API and MCP experience (homepage demo, improved MCP service, API-key observability) |
| 2026-07-02 | The Straits | Singapore & Indonesia Groups (conglomerate pages) · 3x Singapore coverage · Onboarding Quests |
| 2026-06-16 | Search Console | Sectors Search Console · ~90 IDX Broker report pages · v2 API coverage expansion |
| 2026-05-12 | Bandarmology | The Orderbook · Foreign Flow · Ownership Movements · official deprecation of API v1 |
| 2026-04-14 | Treasury of the Republic | Improved AI Chat · Discover by Industry · Government Ownership in Companies · early access to Sectors Workflow |
| 2026-03-18 | The Crescent Moon | Redesigned landing · Events Calendar (corporate actions, every company) · Social accounts Google/GitHub + OTP |
| 2026-03-04 | A Journalist's Dream | News in Sectors Search · Watchlist Groups · SGX stock report upgrades |
| 2026-02-02 | Natural Language Screeners | v2 API with NL stock screening · SQL-like deterministic queries · Singapore News · more CSV downloads |
| 2026-01-01 | New Foundations | Deep Linking (embeddable Search) · Feature Box · remodeled API page · 2026 trading holidays |
| 2025-12-08 | Santa Season | Free API credits · SGX buybacks & insider trades · AI Search as an "open box" (query path shown) · AI Chat on v2 |
| 2025-11-12 | Watchful Eyes behind Sectors | Reworked Sustainability section · AI Search on v2 · Automated Treatment Flags (backend outlier detection) |
| 2025-10-13 | Banks and REITs of the Lion City | In-depth SGX REITs · upgraded SGX bank reports · Docks in SGX reports |
| 2025-09-12 | Curate and Navigate | Thematic and sector listings · loan portfolio for banks · new nav menu · Search finds stock indices |
| 2025-08-13 | The Intelligent Investor | Sectors Insider x Search · "Top Questions before your Stock Purchase" |
| 2025-07-14 | Mid-Year Content Pack | Weekly Digests on-platform · trading calendars IDX/SGX/KLSE · Snapshot: Coal Edition |
| 2025-06-13 | 1st Anniversary Release | Sectors AI Chat soft launch · revamped pricing · Snapshot: Bank Edition |
| 2025-05-13 | Multi-region Search | SGX coverage in Search · inside transactions & share transfers · Sectors Digest by email |
| 2025-04-14 | The Merlion | SGX stock reports · liquidity and credit risk analysis for banks · watchlist tags |
| 2025-03-13 | Closer to the Source | Improved Search with AI summaries · data source upgrades · smarter news feed |
| 2025-02-16 | FY2024 Availability | FY2024 financials · pipeline infrastructure upgrade · Industry Leaders · Community Bulletin |
| 2025-01-13 | Functional Minimalism | Dock on stock reports · IDX Total Index · dividends calendar · workshop MP4s |
| 2024-12-31 | Kickin' off 2025 | Richer Peers · loan quality, NII/NIM · rebuilt light theme · banking sector explainers |
| 2024-12-10 | Mid-December Release | Sectors Search 2.0 (keyword and phrase queries) · post-IPO pages · BUMN/Persero companies |
| 2024-11-13 | Watchlist Email Summary | Weekly watchlist email · Overview section and radar charts · sector report improvements · largest employers |
| 2024-10-12 | Financial Reports Upgrade | Revenue and income evolution (~300 reports) · cost structure breakdown · API workshops · watchlist integration |
| 2024-09-12 | Watchlist and Calculators | Stock & sectors watchlist · intrinsic value calculator |
| 2024-08-13 | Sectors AI for Search and Filings | Sectors AI Search · AI key-filings extraction and news · companies by ranking |
| 2024-07-13 | Indices, SGX and 2 New Sections | 13 indices · Singapore page · Sustainability section · Technical Indicators section · API credits |
| 2024-06-12 | 👋 Sectors launch | Sectors Financial API · Exploration tab with 17 research tools · API documentation |

## Terms that appear in zero of the 28 entries

Searched the full page text: `pemantauan`, `special monitoring`, `full call auction`,
`suspension`, `delisting`, `notasi khusus`, `licence`/`license`, `IUP`, `expiry`, `forecast`,
`predict`, `early warning`, `risk score`.

None occur. The only flag-shaped feature ever shipped — "Automated Treatment Flags"
(2025-11-12) — is explicitly an internal data-quality outlier system, not a user-facing signal.

## Footer surfaces present but never announced in a release

"Mining, Metals & Minerals" and "REITs" appear in the site footer. REITs got a release
(2025-10-13, SGX only). Mining never did, despite `/v2/mining/*` being 20+ live endpoints.
