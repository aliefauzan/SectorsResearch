# What Sectors Is

> Sources: <https://sectors.app>, <https://sectors.app/pricing>, <https://sectors.app/api>,
> <https://docs.sectors.app>. Captured 4 September 2026.

## The product

Sectors is an **API-first financial data platform for Southeast Asian markets**, built by
[Supertype](https://supertype.ai). Its own positioning: *"API-first Financial Data for
Indonesia and Singapore."*

Coverage spans three exchanges plus a mining data extension:

| Market | Coverage | Depth |
| --- | --- | --- |
| **IDX** (Indonesia) | 99.99% of ~950+ listed companies | Primary market. Equities, brokers, filings, corporate actions, shareholders, news, suspensions |
| **SGX** (Singapore) | ~80%, 617 companies | Reports, screener, dividends, buybacks, short-sell, filings, news |
| **KLSE** (Malaysia) | Sector-level | Basic company report and sector lists only |
| **Mining (Indonesia)** | Listed *and unlisted/private* companies | Sites, production, reserves, licenses, auctions, commodity prices, exports, ownership trees |

The stated differentiator against global providers: coverage of the **long tail**. Global
APIs index popular tickers and miss smaller names; Sectors claims ">35% more coverage than
any global financial data provider" on IDX, and goes deeper — broker filings, corporate
actions, buybacks, segment revenue breakdowns.

Listed institutional users on the site: Bank Indonesia, IDX itself, Kementerian Keuangan,
BPK RI, Bank BRI, Trimegah Securities, DSNG.

## Surfaces

Sectors is not only an API. Understanding the surrounding product helps you build something
that complements rather than duplicates it — worth knowing, because Track 03 explicitly
excludes "raw Sectors data in a different visual form."

| Surface | What it is |
| --- | --- |
| **Sectors App** (sectors.app) | The web product: dashboards, company pages, sector pages, screener |
| **Search Console** | Multi-modal financial search engine |
| **Sectors AI Chat** | GPT-like stock research assistant grounded in Sectors data |
| **Smart Watchlist** | Track companies, sectors and news tags |
| **Sectors Workflow** | If-this-then-that automation builder; alerts and recurring research delivered to email, Slack, Telegram, WhatsApp |
| **Screener & Query Builder** | Chain financial queries, filter on 500+ metrics, self-updating in Workflow |
| **Sectors Financial API** | `https://api.sectors.app` — the REST API, 70 v2 endpoints |
| **Sectors MCP** | Cloud-hosted MCP server, 66 tools (65 documented), for AI clients |
| **Integrations** | Google Sheets add-on, Chrome extension (IDX ticker lens), Excel Power Query, Looker Studio, n8n, Claude and ChatGPT via OAuth |
| **Peer Comparison** | `sectors.app/peers` |
| **Curated market pages** | Foreign flow (`/idx/foreign-flow`), broker rankings (`/idx/broker`), conglomerates & groups (`/indonesia/group`), BUMN companies (`/indonesia/bumn`), index pages (`/indonesia/index/<code>`) |
| **Financial API Workshops** | Monthly workshops on financial data science, financial AI agents, API integration and automation. **Free for Insider subscribers**; 1,200 students to date. `sectors.app/financial-api-workshops` |

Scale claim from the API page: "Serving 40,000 financial workflows each month."

Community channels beyond the docs: [Instagram](https://www.instagram.com/sectorsapp),
[LinkedIn](https://www.linkedin.com/company/sectorsapp/),
[Discord](https://discord.gg/TAnZMmNS4X). Enterprise enquiries: help@sectors.app.

> Note for Track 03 teams: Sectors already ships a screener, a watchlist, an AI chat, and an
> if-this-then-that workflow builder. Something that mostly reproduces one of those is
> competing with the host's own product on the host's own data. Derive something they don't.

## Plans and how the API is gated

Pricing captured 4 September 2026, annual-billing figures as displayed:

| Plan | Price | API access |
| --- | --- | --- |
| **Forever Free** | Free | ❌ No API. App access, limited export, Search Console without AI |
| **Standard** | $49 (2 months free, save 17%) | ❌ No API. Unlimited export, watchlist, premium data (broker/bandarmology, order books, deeper financials, insider transactions, filings), AI Search, AI Chat |
| **Insider** | $53 (3 months free, save 25%) | ✅ **5,000 Sectors API credits/month**, Sectors Workflow, Screener & Query Builder, free workshop entry, past workshop recordings, priority email + Discord support |

**The API requires the Insider plan.** Insider is only $3/month more than Standard — Sectors
is clearly steering developers there.

For the hackathon this matters less: registered teams get **1,000 API credits** granted
through the hackathon portal. But note the difference in scale — the grant is one fifth of a
single month of an Insider subscription. Budget accordingly; see
[`05-credit-budget.md`](05-credit-budget.md).

## Documentation map

| Resource | URL | Use it for |
| --- | --- | --- |
| Docs home | <https://docs.sectors.app> | Everything |
| Get started (v2) | <https://docs.sectors.app/get-started/v2/overview> | API key, first request |
| v1→v2 migration | <https://docs.sectors.app/get-started/v2/migration-guide> | Old tutorials still show `/v1/` |
| API reference | `/api-references/v2/...` | Per-endpoint detail |
| v2 changelog | <https://docs.sectors.app/api-references/v2/changelog> | Billing rules, breaking changes |
| Recipes | <https://docs.sectors.app/recipes/> | Worked examples, Python/R/n8n/Looker/Sheets |
| **OpenAPI spec** | <https://docs.sectors.app/schema.json> | Full machine-readable spec, examples for all 70 endpoints |
| **llms-full.txt** | <https://docs.sectors.app/llms-full.txt> | Entire docs site as one 840 KB text file |
| Postman collection | <https://docs.sectors.app/recipes/postman-collection/01-postman-collection> | Click-testing endpoints |
| Agent skills repo | <https://github.com/supertypeai/sectors-agent-skills> | Drop-in skill for Claude Code / OpenCode / OpenClaw |
| Discord | <https://discord.com/invite/TAnZMmNS4X> | Community |

> Both `llms-full.txt` and `schema.json` are fetchable without auth and are by far the fastest
> way to give a coding agent complete knowledge of this API. Copies are in
> [`99-raw/`](../99-raw/).

## Recipes worth reading before you design

The docs contain full worked projects. Several map directly onto hackathon tracks:

| Recipe | Track it maps to |
| --- | --- |
| [Sectors MCP guide](https://docs.sectors.app/recipes/sectors-for-ai-agents/00-sectors-mcp-guide) | 01 |
| [Human-Agent Collaboration Framework for IDX Stock Analysis](https://docs.sectors.app/recipes/sectors-for-ai-agents/04-human-agent) | 01 |
| [Multi-Agent Workflows for Financial Research](https://docs.sectors.app/recipes/generative-ai-python/03-multiagent-workflows) | 01 |
| [Tool Use and Function Calling for Finance LLMs](https://docs.sectors.app/recipes/generative-ai-python/02-tool-use) | 01 |
| [Conversational Memory and Tool Use AI Agents](https://docs.sectors.app/recipes/generative-ai-python/06-memory-ai) | 01 |
| [Using the Sectors API with n8n](https://docs.sectors.app/recipes/non-programmatical-tools/04-n8n/01-n8n-sectors-api-guide) | 02 |
| [AI-Powered Stock Analyst with Sectors API and n8n](https://docs.sectors.app/recipes/non-programmatical-tools/04-n8n/02-n8n-natural-language-screener) | 02 |
| [GNN Anomaly Detection, parts 1–3](https://docs.sectors.app/recipes/gnn-anomaly-detection/01-gnn-part-1) | 03 |
| [Benchmarking IDX Banking Stocks](https://docs.sectors.app/recipes/stock-investing-and-finance/02-benchmarking-idx-banking-stocks-sectors-api) | 03 |
| [Portfolio Optimization with Python](https://docs.sectors.app/recipes/stock-investing-and-finance/01-portfolio-optimization) | 03 |
| [SectorScan: Streamlit financial intelligence app](https://docs.sectors.app/recipes/build-python-app/sectorscan/02-sectorscan-part2) | 03 |
| [Best Practices for Safely Using the Sectors API](https://docs.sectors.app/recipes/api-security/01-securing-api-usage) | All |

Reading these is also competitive intelligence: they show the depth the organizers consider
normal, and they hint at what judges have already seen many times.
