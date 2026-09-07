# Landscape · "Meridian, but for stocks" — agent-native market tooling

Research only, 7 September 2026. **No live Sectors API calls; zero credits spent.**
Tooling: agent-reach (Exa search, Jina Reader, `gh-burner.sh`, twitter-cli), WebSearch, WebFetch,
plus direct reads of the Agentic Market and x402 Bazaar catalogues.

The question that started this: *crypto has Meridian for AI-agent automation — is there an
equivalent for stocks, and specifically for Sectors?*

Short answer: **yes for US equities, in two separate shapes, and the category is about a year
old. For IDX one of the two shapes exists (Sectors, and unofficial Stockbit wrappers); the
other is empty, and the emptiness is measurable.**

---

## First: "Meridian" is at least six different products

The name collides badly. Disambiguate before comparing anything.

| Product | What it actually is | Which reading it supports |
| --- | --- | --- |
| **[meridian.app](https://www.meridian.app/)** — MRDN Labs, Inc. | Self-custody crypto investing **iPhone app** on Solana. Tagline *"Your money. Your language."* Unveiled by Benedict Brady at **Solana Breakpoint 2025** (Dec 2025), now in App Store beta. Text-to-trade: *"buy $5 of Bitcoin"*, *"I want to DCA into Bitcoin"* → the agent asks clarifying questions, then **builds and executes the strategy**. Runs *"an agent 24/7 that is essentially scraping Twitter, scraping all the data on the blockchains"* as its knowledge base. Debit/credit/ACH on-ramp. | **Consumer agent automation.** Most likely the one meant by "Meridian for AI agent automation". |
| [meridianfin.io](https://meridianfin.io/) | Market-intelligence platform *built to be consumed by agents* — MCP tools, REST, x402 pay-per-call, discovery via `agents.json` / `llms.txt` / OpenAPI. US smart money (Congress trades, dark pool, 13F, insider), crypto, cross-asset macro. Features named "Multi-signal Fusion", "Confluence Engine", "Confluence Scoring". | **Agent-native data infrastructure.** |
| [meridian402.xyz](https://meridian402.xyz/) | Autonomous market-making agent running its own book on Uniswap v4 / Robinhood Chain. Live console shows it watching tokenized-TSLA basis vs *"its real-market print"* across *"76 venues … treasuries, equities, credit"*. | Autonomous execution on crypto rails. |
| [meridianmarkets.co](https://meridianmarkets.co/) | AI trading-signal service — one daily briefing, 100+ assets, 6 markets, includes AAPL/NVDA. | Signal product. |
| Meridian (MRDN) per MEXC | x402 payment infrastructure / proxy facilitator for cross-chain agent payments. **Note:** MRDN Labs (the app above) and this "MRDN" may or may not be the same entity — the MEXC listing describes payment rails, the app describes consumer investing. Treat as unresolved. | Payment rail. |
| [agentmeridian.xyz](https://agentmeridian.xyz/), `jintukumardas/meridian`, LabLab entries | DLMM agent, agent-to-agent lending economy, hackathon trading bot. | Noise. |

Because the intended referent is ambiguous, this doc answers **both** serious readings.

---

## The category splits in two, and equities split it harder

Crypto blurs the two because one keypair both reads data and signs trades. Equities cannot.

**Layer A — agent-native data and intelligence.** Discoverable without a human, priced per
call, tool-shaped for an LLM.

**Layer B — agent automation and execution.** Something that acts: places orders, runs a
schedule, keeps a book.

---

## Layer A · Agent-native stock data — the direct equivalents

| Product | Agent surface | Payment | Coverage |
| --- | --- | --- | --- |
| **Massive** (Polygon.io **rebranded to Massive on 30 Oct 2025**) | MCP server + `agent.massive.com` x402 routes; listed on Agentic.Market and in the x402 Bazaar | x402 / USDC on Base, per route, no API key. Coinbase CDP is the facilitator. **GA 1 Sep 2026** | US equities: bars, snapshots, movers, SMA/EMA/RSI/MACD, news + sentiment, EDGAR (10-K sections, 8-K, risk factors, 13-F, Form 3/4) |
| **x402stock.xyz** | 140 paid endpoints + free market-status; MCP at `/api/mcp`; OpenAPI 3.1, `llms.txt`, `/.well-known/x402.json` | x402 + MPP, USDC on Base (Solana/Tempo where enabled). $0.01 base → $0.05 bundles, $0.15–$0.75 specialised. Flat-rate `sk_live_…` key also sold | US stocks/ETFs/options, forex, crypto + Hyperliquid perps, energy, US and World-Bank macro, EDGAR, congressional trades, sentiment. **Explicitly no Asia/Indonesia.** |
| **meridianfin.io** | MCP tools, REST with `?sample=true` preview, `agents.json` + `llms.txt` + OpenAPI | x402, route-specific price returned in the 402 | US smart money, crypto, cross-asset macro |
| **Stock Price X402** (klymax402) | One MCP tool, `finance_get_stock_price` | $0.002/call, USDC on Base | Quotes only, "all major US and international exchanges" |
| **Alpha Vantage · EODHD · Tiingo · Intrinio · Nasdaq Data Link** | MCP servers, agent-optimised tool surfaces (EODHD also ships "AI skills" + OpenAPI) | Conventional API key + subscription | EODHD is the broad international one: 60+ exchanges, 150k+ tickers |

**Pattern.** The 2026 shape of an agent-native data provider: MCP server for the IDE/desktop
path, x402 routes for the headless path, and machine-readable discovery (`llms.txt`, OpenAPI,
`agents.json`, a Bazaar listing) so an agent can find you mid-task. Massive's own framing:
*"Discovery has to work the same way; agent-first."*

Price context, from a single third-party survey of 78,267 x402 endpoints: the going rate for an
agent API call is roughly **two cents**. One source, not independently confirmed.

---

## Layer B · Agent automation and execution on equities

| Product | What the agent may do | Note |
| --- | --- | --- |
| **Alpaca Agentic** | Official MCP server + Trading CLI + hosted plugins + remote MCP. Research, portfolio P/L and **order placement** in natural language: fractional equities, ETFs, crypto, multi-leg options. Paper mode with $100k simulated funds; go live by swapping keys. | The reference agent-first brokerage. US only. |
| **Composer** (SoFi) | MCP server: the LLM backtests an idea, execution then follows fixed rules a human reviewed. | Deliberately conservative — agent designs, rules execute. |
| **Robinhood** | Agentic trading accounts announced May 2026; a **separate dedicated account** is required; equities only at launch. | Regulatory containment visible in the product. |
| **Horizon.Trade, AgenticTrading, Tickeron, Trade Ideas** | Plain-English strategy → backtest → deploy; MCP/A2A between agents replacing static pipeline stages. | Varying autonomy. |
| **Virtuals EconomyOS** (`acp trade`) | An agent wallet takes leveraged **equity perps** and buys **tokenized stocks (xStocks) spot** on Hyperliquid — same CLI as its crypto trades. | The crypto-rails route *around* equity regulation. |
| **meridian402.xyz** | Autonomous market-maker quoting tokenized equities on Robinhood Chain. | Same route, live. |

**Why the split exists.** A crypto agent needs a keypair. An equity agent needs a licensed
broker, an account in a named human, and an audit trail — so the only fully autonomous "equity"
agents run on tokenized-equity rails (Hyperliquid perps, xStocks, Robinhood Chain), where the
instrument is a derivative and the venue is a DEX. That is the structural reason the crypto side
got a Meridian first.

---

## Indonesia / IDX — what exists, and the measured hole

### Agent-native IDX data

| Thing | Status |
| --- | --- |
| **Sectors MCP** (`sectors-mcp.supertype.ai/mcp`) | Official. Cloud-hosted on Cloudflare Workers, 66 tools, Streamable HTTP, `Bearer` auth, one-click OAuth connector for Claude and ChatGPT. IDX + SGX + KLSE + Indonesian mining. Insider-plan key required. |
| **`INo-xious/stockbit-mcp`** ⭐25, 6 forks, MIT, created 1 Aug 2026 | Unofficial, unaffiliated. Wraps Stockbit's **private** JSON API through your own logged-in session — bandarmology, quotes, 10-level orderbook, fundamentals, watchlist, portfolio, and **confirm-gated order entry** behind an explicit `stockbit-auth trading-enable` ladder. 153 permitted request shapes in a closed route table; refresh token in the macOS Keychain. Its own README carries a CAUTION about Stockbit's Terms of Use. |
| **`rifkydelta/mcp-stockbit`** ⭐13, 8 forks, created 7 Sep 2026 | Bridges the Stockbit **Desktop** app over Chrome DevTools Protocol; MCP server + local dashboard. Deliberately **read-only, no order execution**. Real portfolio, RDN cash, order queue, orderbook, broker summary. |
| `YogaSakti/mcp-idx`, `giantrksa/stock_mcp`, `baguskto/saham-mcp`, `luminovaa/idx-stock-mcp`, `aldisubarja/us-indonesia-stocks-mcp`, `arbyazra123/auto-news`, `CenblueOne/tradingview-mcp-py` | Hobby-scale MCP servers, mostly yfinance- or scrape-backed; technical + fundamental indicators. |
| `silenccy/orderflow-station` | IDX footprint charts / DOM off the **Stockbit Pro websocket** — the realtime channel Sectors does not have. |

### The measured hole — agent-payable access to IDX data

Queried the **Agentic Market** catalogue API (`api.agentic.market/v1/services/search`) directly
on 7 Sep 2026:

| Query | Services returned |
| --- | --- |
| `indonesia` | **0** |
| `idx` | **0** |
| `sgx` | **0** |
| `jakarta` | **0** |
| `saham` | **0** |
| `southeast asia` | 4 — all macro/sentiment, none equity |
| `stock` | 7 · `equities` 6 · `market data` 10 · `finance` 4 — all US or crypto |

The only Asia-tagged listing, **AsiaPulse** (`asia.lonestaroracle.xyz/pulse`, $0.05/call), is
*"Asia regional macro + geopolitical stress pulse"* — and its own quality block reports
**4 calls from 3 unique payers in 30 days**. There is no agent-payable Indonesian equity data
anywhere in that marketplace.

**Sectors is also absent from the MCP directories.** Searching Glama (`glama.ai/mcp/servers`)
and `mcp.so` for "sectors" returns unrelated servers — climate-sector tools, recruiter
connectors. The official Sectors MCP server does not appear.

### Agent automation on IDX

- **Sectors Workflow** — the only if-this-then-that automation with official IDX data behind it.
  Templates such as *"Notify Slack if Indonesian banks hit a new high"*; delivery to WhatsApp /
  Email / Slack / Telegram / Google Sheets; **1 credit per execution**.
- **Stockbit AI Reports** (Beta, announced June 2026, promoted again Aug 2026) — auto-summarises
  *keterbukaan informasi* documents (rights issue, RUPS, corporate actions) into bullet points
  on the stock page, with key takeaways. The published ENRG rights-issue example extracts share
  count, HMETD ratio, exercise price, funds raised, **maximum dilution 33.33%**, and the trading
  window. **Treat this as prior art for any "AI summarises IDX filings" idea.**
- **insting.io** (SignX, PT Miracle Insting Technology, ~1,700 members since 2020) — realtime
  IDX/IHSG ML signals. `rebekz/stockai` — multi-agent IDX analysis CLI. Neither is infrastructure.

### The regulatory picture — corrected

An earlier draft of this doc asserted that *"OJK in 2026 requires any automated-trading platform
to hold a Manajer Investasi or APERD licence, with independent algorithm audits."* **That claim
came from low-quality SEO sites and does not survive checking. It is withdrawn.** What the
primary sources actually support:

- **Robot trading is a Bappebti matter, not an OJK-equities matter.** *Peraturan Bappebti
  No. 12 Tahun 2022* licenses Expert Advisor services under the **Penasihat Berjangka** regime —
  minimum additional capital **Rp1 billion**, a five-year transaction record, exchange-approved
  system, and mandatory backtesting reports. Its scope is **retail commodity futures**, not
  listed equities. As of **28 August 2026 no provider is verified** on Bappebti's own Expert
  Advisor page (`ceklegalitas.bappebti.go.id`).
- **Bank Indonesia PADG No. 26 Tahun 2025**, in force since 1 December 2025, additionally covers
  robot trading for FX-derivative (PUVA) transactions, with a **Rp50 million** minimum client
  margin.
- **OJK POJK 13/2025** (internal control and conduct for PEE/PPE/PED securities companies)
  **does not mention algorithmic trading, automated order systems, or AI**. Its only
  technology clause is generic IT-risk management: *"Penerapan manajemen risiko penggunaan
  teknologi informasi, termasuk pemanfaatan penyedia jasa teknologi."*
- **IDX has no published equity robot-trading rule.** Coverage of a BEI rule for
  *"penggunaan robot trading dalam perdagangan saham"* dates entirely to **October 2021**
  (Kompas, CNBC Indonesia, IDX Channel, Bisnis), where it is described as still being drafted.
  No later regulation surfaced in search.

**Net:** automated equity execution in Indonesia sits in an unlegislated gap rather than under
an explicit licence regime — which is a reason for caution, not permission. It also matches the
hackathon's own rule banning automated trade execution in every track.

---

## Where Sectors sits

Sectors is most of the way to being the meridianfin.io of Southeast Asian equities:

- ✅ **MCP server** — 66 tools, hosted, OAuth connectors. Ahead of most US data vendors.
- ✅ **Machine-readable discovery** — `llms.txt` (31.9 KB), `llms-full.txt` (819.9 KB),
  OpenAPI 3.0.3 (`schema.json`, 928.9 KB), Postman collection.
- ✅ **Automation surface** — Sectors Workflow, *"40,000 financial workflows each month"*.
- ✅ **Data nobody else has agent-shaped** — IDX/SGX/KLSE fundamentals, broker summary, foreign
  flow, mining licences, shareholder panels.
- ❌ **No agent-payable rail.** Grepping the full spec dump: `x402` 0 hits, `agents.json` 0 hits,
  `micropay` 0 hits, `usdc` 0 hits. Access is a human-provisioned Insider-plan key.
- ❌ **No marketplace presence.** Absent from Glama and mcp.so; absent from Agentic Market and
  the x402 Bazaar.
- ❌ **No realtime channel.** Confirmed empirically on 6–7 Sep 2026 — sector market cap frozen
  33 minutes after the open. Everything numeric is T-1. Stockbit's private websocket is the only
  realtime IDX feed an agent can reach, and it is unofficial.

**So: the "Meridian for stocks" exists for the US in both shapes. For IDX, Sectors is the only
Layer-A candidate, and what it is missing is distribution and agent-payable access — not data.**

---

## What this means for the hackathon

1. **Do not pitch "Sectors MCP + a chat client" as the innovation.** That surface exists
   officially, plus at least seven unofficial IDX MCP servers, two with real traction. Track 01
   is already the most crowded track on the matching board (15 of 48 public teams, 31%).
2. **Do not pitch "AI summarises IDX corporate actions."** Stockbit shipped AI Reports in
   June 2026 and it is in the app, on the stock page, free.
3. **The unclaimed shape is Layer A applied to IDX-only data** — a confluence/fusion layer over
   what a US provider structurally cannot see (broker summary, foreign flow, PPK criteria, IUP
   licence runway, the I-N suspension ladder), delivered agent-shaped. meridianfin.io's
   differentiator is not its data, it is the *Confluence Engine* scoring agreement across
   sources. Nothing does that for IDX.
4. **If the intended analogy is meridian.app** — natural-language *"set up a DCA into X"* —
   then the equity equivalent is Layer B, which is closed to you: automated execution is banned
   in every track, no IDX broker exposes an official order API, and the only IDX order path an
   agent has is an unofficial wrapper around Stockbit's private API. Build the *reasoning* half,
   stop before the order.
5. **Realtime is unavailable and not worth faking.** Design around a T-1 baseline plus the two
   same-day channels (`/v2/news/` on a 4-hour cron, `/v2/filings/` on a 2-hour cron).
6. **An x402-style façade is technically open** — nothing stops a submission from putting
   pay-per-call in front of its *own derived signal*, with Sectors as the core upstream. With
   0 Indonesian services in the whole Agentic Market catalogue it would be a genuine first.
   Weigh that against the 30% "innovative use of the Sectors API" criterion and the risk of
   judges reading a crypto rail as off-theme.

---

## Research limits

- **Twitter/X and Reddit were not reachable.** `agent-reach doctor` reports
  `active_backend: null` for both (OpenCLI browser extension not connected); `twitter-cli`
  authenticates but its search endpoint returns HTTP 404, and `@MeridianApp` resolves to
  `not_found`. **Nothing in this doc rests on social sentiment.**
- `mcpmarket.com` and `sectors.app` are behind a Vercel security checkpoint (HTTP 429 to both
  WebFetch and Jina Reader); the Sectors Workflow facts come from the committed 4 Sep 2026
  browser capture in `evidence/`.
- The two-cent x402 price point rests on a single third-party survey.
- MRDN Labs vs the MRDN payment-infrastructure token is unresolved; do not assert they are
  the same project.

---

## Sources

**Meridian (crypto):** [meridian.app](https://www.meridian.app/) ·
[Breakpoint 2025 product keynote writeup](https://solanacompass.com/learn/breakpoint-25/product-keynote-meridian) ·
[Solana Compass project page](https://solanacompass.com/projects/meridian) ·
[meridianfin.io](https://meridianfin.io/) · [meridian402.xyz](https://meridian402.xyz/) ·
[meridianmarkets.co](https://meridianmarkets.co/) ·
[MRDN via MEXC](https://www.mexc.com/learn/article/what-is-meridian-mrdn-complete-guide-to-the-ai-agent-payment-infrastructure/1)

**Agent-native data:** [Massive x402 announcement](https://massive.com/blog/x402-payments-for-ai-agents) ·
[Polygon.io is Now Massive](https://massive.com/blog/polygon-is-now-massive) ·
[x402stock.xyz](https://x402stock.xyz/) ·
[Stock Price X402](https://mcp.so/servers/stock-price-x402) ·
[Agentic Market](https://agentic.market/) · [x402 Bazaar](https://www.x402bazaar.org/services) ·
[x402 pricing report](https://theaicareerlab.com/blog/x402-pricing-report-2026) ·
[MCP servers for stock market data](https://www.lambdafin.com/articles/mcp-server-stock-market-data)

**Execution:** [Alpaca Agentic](https://alpaca.markets/agentic) ·
[alpaca-mcp-server](https://github.com/alpacahq/alpaca-mcp-server) ·
[Composer via Alpaca](https://alpaca.markets/blog/how-composer-is-redefining-algorithmic-trading-with-their-no-code-platform/) ·
[Robinhood agentic trading (Forbes)](https://www.forbes.com/sites/zacharyfolk/2026/05/27/robinhood-will-allow-users-ai-agents-to-trade-stocks/) ·
[Virtuals EconomyOS trading](https://os.virtuals.io/trading)

**Indonesia:** [Sectors MCP guide](https://docs.sectors.app/recipes/sectors-for-ai-agents/00-sectors-mcp-guide) ·
[`INo-xious/stockbit-mcp`](https://github.com/INo-xious/stockbit-mcp) ·
[`rifkydelta/mcp-stockbit`](https://github.com/rifkydelta/mcp-stockbit) ·
[Stockbit AI Reports](https://snips.stockbit.com/fitur-stockbit/ai-reports-stockbit-inovasi-ai-dari-sekuritas-terbaik-dan-aman-di-indonesia) ·
[insting.io](https://www.insting.io/) · [`rebekz/stockai`](https://github.com/rebekz/stockai)

**Regulation:** [Pluang — aturan robot trading (Bappebti 12/2022, BI PADG 26/2025)](https://pluang.com/akademi/berita-analisis/aturan-untuk-robot-trading-di-indonesia) ·
[OJK POJK 13/2025 press release](https://www.ojk.go.id/id/berita-dan-kegiatan/siaran-pers/Pages/POJK-13-Tahun-2025.aspx) ·
[POJK 5/2026 — Kegiatan Usaha Manajer Investasi](https://ojk.go.id/id/regulasi/Pages/POJK-5-Tahun-2026-Penyelenggaraan-Kegiatan-Usaha-Manajer-Investasi.aspx) ·
[BEI robot-trading rule, Oct 2021 (Kompas)](https://money.kompas.com/read/2021/10/11/190559226/bei-sempurnakan-aturan-tentang-pengguanan-robot-trading) ·
[CNBC Indonesia, Oct 2021](https://www.cnbcindonesia.com/market/20211011141241-17-282978/sebentar-lagi-trading-saham-pakai-robot-aturan-lagi-digodok)

**Local evidence:** [`evidence/sectors/sectors-workflow-page.md`](../evidence/sectors/sectors-workflow-page.md) ·
[`docs/api/04-mcp-and-ai-agents.md`](../docs/api/04-mcp-and-ai-agents.md) ·
[`plan/competitive-landscape.md`](competitive-landscape.md)
