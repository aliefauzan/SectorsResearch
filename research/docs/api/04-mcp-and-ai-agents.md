# Sectors MCP & AI Agent Integration

> Sources: <https://docs.sectors.app/recipes/sectors-for-ai-agents/00-sectors-mcp-guide>,
> `/01-agent-skills-guide`, `/02-sectors-in-claude`, `/03-sectors-in-chatgpt`.
> Captured 4 September 2026.

This is the surface most relevant to **Track 01** — and the one with the sharpest trap in it.
Read the warning at the bottom before you plan an agent project.

---

## The MCP server

| | |
| --- | --- |
| **URL** | `https://sectors-mcp.supertype.ai/mcp` |
| **Transport** | Streamable HTTP (remote; no local install) |
| **Hosting** | Cloudflare Workers |
| **Auth** | `Authorization: Bearer <YOUR_API_KEY>` — **the `Bearer` prefix is required here**, unlike the REST API |
| **Tools** | **66** in the server, **65** in the documented catalogue — see below |
| **Requires** | Insider plan API key (or the hackathon grant) |

Works with any MCP-capable client: Claude Desktop, Claude Code, Cursor, VS Code + Copilot,
Windsurf, JetBrains IDEs.

### Setup

**Claude Code**

```bash
claude mcp add -t http sectors https://sectors-mcp.supertype.ai/mcp \
  -H "Authorization: Bearer YOUR_API_KEY_HERE"
```

**Cursor** — `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "sectors": {
      "url": "https://sectors-mcp.supertype.ai/mcp",
      "headers": { "Authorization": "Bearer YOUR_API_KEY_HERE" }
    }
  }
}
```

**VS Code (Copilot)** — `.vscode/mcp.json`, prompts for the key per session

```json
{
  "servers": {
    "sectors": {
      "type": "http",
      "url": "https://sectors-mcp.supertype.ai/mcp",
      "headers": { "Authorization": "Bearer ${input:sectors-api-key}" }
    }
  },
  "inputs": [
    { "type": "promptString", "id": "sectors-api-key",
      "description": "Your Sectors Financial API key", "password": true }
  ]
}
```

**Any other Streamable-HTTP client**

| Setting | Value |
| --- | --- |
| Transport | `http` |
| URL | `https://sectors-mcp.supertype.ai/mcp` |
| Authorization header | `Bearer YOUR_API_KEY_HERE` |

**Claude web/desktop and ChatGPT** support a **one-click OAuth custom connector** — no API key
in a config file at all. See the
[Claude](https://docs.sectors.app/recipes/sectors-for-ai-agents/02-sectors-in-claude) and
[ChatGPT](https://docs.sectors.app/recipes/sectors-for-ai-agents/03-sectors-in-chatgpt) guides.

Restart the client fully after adding the config — most only load MCP servers at startup.
`claude mcp list` confirms registration.

---

## Tool catalogue (65 documented, 66 implemented)

> **Counted, not estimated.** `llms-full.txt` names exactly **65** tools, all `fetch-*`.
> The server's own source — [`supertypeai/sectors-mcp`](https://github.com/supertypeai/sectors-mcp),
> `src/tools/generated/*.ts` — contains **66** files. The extra one is **`get-subsectors`**,
> the only tool not named `fetch-*`, and it appears in no documentation page. File tree saved
> at [`evidence/sectors/sectors-mcp-repo-tree.txt`](../../evidence/sectors/sectors-mcp-repo-tree.txt).
> By market the documented 65 split IDX 31 / SGX 11 / KLSE 4 / mining 19.

Tool names map closely onto REST endpoints, so the
[endpoint reference](02-endpoint-reference.md) doubles as the parameter documentation.

### Company analysis
| Tool | Key params |
| --- | --- |
| `fetch-company-report` — full report, selectable sections (overview, valuation, future, peers, financials, dividend, management, ownership) | `symbol`, `sections` |
| `fetch-company-segments` — revenue/cost segment breakdown | `symbol`, `financial_year` |
| `fetch-listing-performance` — performance since listing across 7/30/90/365d | `symbol` |
| `fetch-corporate-actions` — splits, rights, warrants, bonus shares, AGM, dividends | `symbol` |
| `fetch-shareholders-composition` — monthly breakdown by investor category, local and foreign | `symbol`, `year` |

### Market screening & rankings
| Tool | Key params |
| --- | --- |
| `fetch-companies-by-subsector` — the screener; structured or natural language | `q`, `where`, `order_by`, `limit` |
| `fetch-companies-top-changes` — gainers/losers over 1d/7d/14d/30d/365d | `classifications`, `periods`, `sub_sector`, `n_stock` |
| `fetch-most-traded-stocks` | `start`, `end`, `n_stock`, `sub_sector` |
| `fetch-close` — every IDX ticker's close on one day | `date` |

### Financial data
`fetch-quarterly-financials` (`symbol`, `n_quarters`, `report_date`) ·
`fetch-quarterly-financial-dates` (`symbol`) ·
`fetch-companies-quarterly-financial-dates` (`since`, `year` — freshness polling)

### Market indices & daily data
`fetch-index-daily` · `fetch-idx-market-cap` · `fetch-daily-transaction` ·
`fetch-foreign-flow` · `fetch-free-float`

### Sector & industry classification
`get-subsectors` · `fetch-industries` · `fetch-subindustries` · `fetch-subsector-report` ·
`fetch-companies-with-segments`

### News, filings & events
`fetch-news` (`extension`, `sector`, `sub_sector`, `symbols`, `keyword`, `tags`, `start`, `end`) ·
`fetch-filings` (insider buy/sell) · `fetch-suspensions` · `fetch-tags`

### Broker data (bandarmology)
`fetch-brokers` (registry, `origin`, `cohort`) · `fetch-top-brokers` ·
`fetch-broker-summary` · `fetch-broker-summary-top` ·
`fetch-broker-activity` · `fetch-broker-activity-top`

### Singapore (SGX) — 11 tools
`fetch-sgx-sectors` · `fetch-sgx-subsectors` · `fetch-sgx-company-report` ·
`fetch-sgx-companies-by-sector` · `fetch-sgx-top-companies` · `fetch-sgx-daily-transaction` ·
`fetch-sgx-filings` · `fetch-sgx-news` · `fetch-sgx-buybacks` · `fetch-sgx-short-sell` ·
`fetch-sgx-tags`

### Malaysia (KLSE) — 4 tools
`fetch-klse-sectors` · `fetch-klse-company-report` · `fetch-klse-companies-by-sector` ·
`fetch-klse-top-companies`

### Mining (Indonesia) — 19 tools
`fetch-mining-commodities` · `fetch-mining-commodity-price` · `fetch-mining-global-commodity` ·
`fetch-mining-companies` · `fetch-mining-company-detail` · `fetch-mining-company-financials` ·
`fetch-mining-company-ownership` · `fetch-mining-company-performance` · `fetch-mining-sites` ·
`fetch-mining-site-detail` · `fetch-mining-total-production` · `fetch-mining-exports` ·
`fetch-mining-sales-destination` · `fetch-mining-contracts` · `fetch-mining-licenses` ·
`fetch-mining-license-auctions` · `fetch-mining-license-auction-detail` ·
`fetch-mining-resources-reserves` · `fetch-mining-resources-reserves-detail`

---

## Agent skills (non-MCP)

An official skill package for coding agents lives at
**<https://github.com/supertypeai/sectors-agent-skills>**. It covers 19 IDX and 6 SGX
endpoints via plain REST rather than MCP.

> ### ⚠️ This repo is stale — it targets the discontinued v1 API
>
> Verified 4 September 2026 by reading the repo directly. `SKILL.md` states:
>
> > "ONLY make HTTP requests to `https://api.sectors.app/v1`."
>
> and sets `BASE_URL = "https://api.sectors.app/v1"`. `assets/endpoint-map.md` says
> "All endpoints: `GET https://api.sectors.app/v1{path}`".
>
> **Seven `/v1` references, zero `/v2` references** across both files. Repo last pushed
> 2026-07-21, two months after **v1 was discontinued on 2026-05-11**. Every `/v1/*` path now
> returns **HTTP 410 Gone**.
>
> An agent that installs this skill and follows it will make requests that cannot succeed —
> and because 410s aren't billed, it will fail silently rather than obviously running out of
> credits. The docs' own "Agent Skills Guide" recipe links to this repo without flagging it.
>
> **If you use it:** clone it, then rewrite every `/v1` to `/v2` and re-check the endpoint
> map against [`02-endpoint-reference.md`](02-endpoint-reference.md) — several v1 endpoints
> did not survive the migration unchanged (the screener, rankings and news endpoints all
> changed shape, and `idx_ticker` became `symbol`).
>
> The genuinely useful parts that are still correct: the setup instructions, the
> `SECTORS_API_KEY` convention, and the rule that the REST `Authorization` header takes the
> **raw key with no `Bearer` prefix**.
>
> Repo state at capture: 2 stars, 0 forks, 1 open issue, created 2026-02-12, MIT declared in
> the skill frontmatter. A local copy of `SKILL.md` and the endpoint map is in
> [`evidence/sectors/agent-skills/`](../../evidence/sectors/agent-skills/).

```bash
git clone https://github.com/supertypeai/sectors-agent-skills/
cd sectors-agent-skills
export SECTORS_API_KEY="your-key"
```

> That `export` is the upstream skill's own setup, quoted as published. Inside **this**
> repository the same variable comes from the git-ignored `.env` at the root — see
> [`SETUP.md`](../../../SETUP.md). To hand it to an external tool that reads the environment
> directly, source the file for that command rather than retyping the key:
> `set -a && . .env && set +a`.

Supported hosts: **Claude Code** (`claude config set env SECTORS_API_KEY ...`),
**OpenCode** (auto-detects `SKILL.md`), **OpenClaw**
(`openclaw skills install sectors-api` via [ClawHub](https://www.clawhub.ai)).

The skill's own constraints are worth repeating because they are the API's constraints:

- Never hardcode or guess an API key; always read `SECTORS_API_KEY`
- The `Authorization` header uses the **raw key, no `Bearer` prefix** (REST, not MCP)
- All endpoints are GET against `https://api.sectors.app/v2`

---

## ⚠️ The Track 01 trap

Track 01's disqualifying example is stated explicitly on the track page:

> "Connecting an off-the-shelf AI client such as Claude, OpenClaw, or Hermes to the Sectors
> MCP with custom prompts or configuration alone" **does not qualify**.
>
> "If the product would disappear when the team's prompt is removed from someone else's
> client, it does not meet this track's bar."

The Sectors MCP is excellent and makes a convincing demo in about ten minutes. That is
precisely the problem: **that demo is not a Track 01 project**. Judges will have seen it many
times over.

To clear the bar, own the orchestration layer:

| ❌ Doesn't qualify | ✅ Qualifies |
| --- | --- |
| Claude Desktop + Sectors MCP + a good system prompt | Your own agent runtime that calls Sectors tools as one of several sources |
| A `.mcp.json` and a prompt file in the repo | A planner that decides *which* endpoints to hit, in what order, and when to re-query |
| Chat UI wrapping someone else's client | Memory/state across turns that you implemented |
| — | A verification step that checks the model's numbers against a second endpoint |
| — | Routing between Sectors, filings text, and your own computed features |

**Using the MCP server is still fine** — the rules say any track may use MCP, REST, or both.
What matters is that something you built sits above it. A common working shape: your own
tool layer over the REST API for the deterministic parts (screening, math, thresholds), with
MCP or an LLM for the parts that genuinely need language.

And make the orchestration *visible in the video*. Show the plan, the tool calls chosen, the
re-query when the first answer was thin. Invisible orchestration scores like no orchestration.

---

## Credits still apply

MCP tool calls hit the same API and spend the same credits at the same per-endpoint rates.
An agent that calls `fetch-company-report` without a `sections` argument spends **8 credits
per company** — and agents love to call things in loops.

Concrete guardrails for an agent project on a 1,000-credit grant:

- **Constrain tool schemas.** Make `sections` required in your own tool wrapper, defaulting to one section, not all eight.
- **Cache aggressively.** Company reports change quarterly, not per turn. Cache by `(symbol, section, date)`.
- **Cap the loop.** Hard-limit tool calls per user turn; return partial results rather than iterating freely.
- **Meter it.** Log `X-Credits-Charged` per call and count it, so you find the runaway loop in development and not on submission day.
- **Develop against the mock.** [`harness/`](../../harness/) serves all 70 endpoints offline with a credit meter, so agent loops can run all day for zero credits.
