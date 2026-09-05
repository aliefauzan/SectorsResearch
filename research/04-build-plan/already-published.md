# What the Organizers Have Already Built and Published

> Sixth-pass finding, and the most strategically important one in this dossier.
>
> Sectors' documentation contains **39 recipes**. Several of them are complete, working
> implementations of the projects a team would most naturally propose for each track — written
> by Supertype engineers, the same organization judging this hackathon, and published *before*
> the event.
>
> Judging is 30% "how innovative is the use of Sectors API or MCP". Rebuilding a published
> tutorial scores badly against that criterion, and the judges will recognise it instantly
> because they wrote it.

---

## The three that overlap most with obvious hackathon projects

### Track 02 · "Scheduled Daily Top Movers to Discord"

[Using the Sectors API with n8n](https://docs.sectors.app/recipes/non-programmatical-tools/04-n8n/01-n8n-sectors-api-guide) — March 2026

A four-node n8n workflow:

1. **Schedule Trigger** — "Runs the workflow automatically at 7:00 AM every day"
2. **HTTP Request** — fetches `/v2/companies/top-changes/`
3. **Code (JavaScript)** — formats the response into a message with emojis and markdown
4. **HTTP Request** — posts to a Discord webhook

The recipe names the pattern explicitly: *"Schedule → Fetch Data → Transform Data → Deliver
Results."*

**That is the daily-brief project.** A 7am scheduled pull of top movers pushed to a chat
channel is a published tutorial, not an idea. It also notes the webhook pattern works
identically for Slack and Teams, so switching the destination changes nothing.

### Track 01 · "AI-Powered Stock Analyst Chatbot"

[Building an AI-Powered Stock Analyst with Sectors API and n8n](https://docs.sectors.app/recipes/non-programmatical-tools/04-n8n/02-n8n-natural-language-screener) — March 2026

A four-stage pipeline with a public chat URL:

1. **Receive and Screen** — chat trigger → `/v2/companies/` screener
2. **Parallel Enrichment** — two HTTP nodes run simultaneously per company (valuation, financials)
3. **Recombine**
4. **Analyze**

Its own suggested prompts are "top 5 banks by market cap", "top 3 coal companies by revenue in
2023", "top 5 companies in LQ45 by market cap" — the exact demo queries a chatbot project
would show.

### Track 01 · "FinArena" — human-agent collaboration

[Building a Human-Agent Collaboration Framework for IDX Stock Analysis](https://docs.sectors.app/recipes/sectors-for-ai-agents/04-human-agent) — **June 2026**, two months before the hackathon

Adapts the FinArena paper (Xu et al., 2025) to IDX:

- A **Fundamental Agent** — financial statements and valuation
- A **Technical Agent** — price action and trading performance
- A **News Agent** — company news and filings
- A **Universal Expert Agent** — synthesizes all three, weighted by the user's stated risk profile
- Three specialist agents run **concurrently**

It even pre-empts the three pitches a team would make for such a project, under headings
"Problem 1: Existing tools use a single data type", "Problem 2: LLMs hallucinate on news
data", "Problem 3: AI frameworks ignore the investor".

**If your Track 01 pitch is "multiple specialist agents synthesize fundamental, technical and
news signals" — that is this recipe.** Including the risk-profile personalization angle.

### Also published

| Recipe | Overlaps with |
| --- | --- |
| [Multi-Agent Workflows for Financial Research](https://docs.sectors.app/recipes/generative-ai-python/03-multiagent-workflows) | Sequential chains and judge-critic patterns for reliability |
| [Tool-Use ReAct Conversational Agents](https://docs.sectors.app/recipes/generative-ai-python/05-conversational) | ReAct agent with streaming |
| [Conversational Memory and Tool Use AI Agents](https://docs.sectors.app/recipes/generative-ai-python/06-memory-ai) | Agent memory across turns |
| [GNN Anomaly Detection, parts 1–3](https://docs.sectors.app/recipes/gnn-anomaly-detection/01-gnn-part-1) | Graph-based anomaly detection confirmed by broker and foreign flow |
| [SectorScan, parts 1–2](https://docs.sectors.app/recipes/build-python-app/sectorscan/02-sectorscan-part2) | Streamlit financial-intelligence dashboard |
| [Portfolio Optimization](https://docs.sectors.app/recipes/stock-investing-and-finance/01-portfolio-optimization) | Monte Carlo / efficient frontier portfolio tool |
| [Benchmarking IDX Banking Stocks](https://docs.sectors.app/recipes/stock-investing-and-finance/02-benchmarking-idx-banking-stocks-sectors-api) | Sector benchmarking dashboard |
| [Excel](https://docs.sectors.app/recipes/non-programmatical-tools/01-excel/01-excel) / [Sheets](https://docs.sectors.app/recipes/non-programmatical-tools/02-sheets/02-sheets) / [Looker](https://docs.sectors.app/recipes/non-programmatical-tools/03-looker/03-looker) | No-code dashboards and BI integrations |

Between these and **Sectors Workflow** (see [`competitive-landscape.md`](competitive-landscape.md)),
the following are all effectively taken: the scheduled alert bot, the natural-language stock
chatbot, the multi-agent analyst, the anomaly detector, the Streamlit dashboard, the portfolio
optimizer, and the BI dashboard.

---

## This is not a reason to despair

Two things make it much less bad than it looks.

**First, most of the field will not have read these.** Thirty-nine recipes is a lot, and the
overlap is only visible if you go through them. A project that visibly *starts where the
recipes end* is immediately differentiated from the majority.

**Second, the recipes are a gift if you use them correctly.** They tell you:

- the depth Supertype considers normal
- the failure modes they already know about (see [`../02-sectors-platform/10-domain-pitfalls.md`](../02-sectors-platform/10-domain-pitfalls.md))
- exactly which demos will feel familiar to a judge

---

## How to use this

### The test to apply to your idea

> Could a judge finish my one-sentence pitch by naming one of their own recipes?

If yes, change the pitch — not necessarily the project.

### Concretely

| If your idea is… | Move it to… |
| --- | --- |
| Scheduled top-movers digest | A brief built on data the recipe doesn't touch — broker cohorts, shareholder composition, suspensions, mining licences — and that **ranks and explains** rather than lists |
| Natural-language stock chatbot | An agent whose distinguishing feature is verification, budget-awareness, or refusing to state unfetched numbers |
| Multi-agent fundamental/technical/news analyst | Something with a genuinely different decomposition — by *time horizon*, by *data reliability*, or an adversarial checker rather than three parallel specialists |
| Anomaly detector on price correlation | Anomalies in ownership, licensing or filings rather than price |
| Streamlit dashboard | Anything else; dashboards are explicitly weak for Track 03 anyway |

### The under-published space

All 39 recipe pages were extracted and searched (726,000 characters). Distinguishing a
**worked example** from a bare mention in the MCP tool table or the Postman endpoint listing:

| Endpoint / feature | Worked example in any recipe? | Where it's mentioned at all |
| --- | --- | --- |
| **Mining** (19 endpoints) | **No** | One line in the Postman collection listing |
| **`/v2/suspensions/`** | **No** | Nowhere in any recipe |
| **SGX buybacks** | **No** | Nowhere in any recipe |
| **SGX short-sell** | **No** | Nowhere in any recipe |
| **Corporate actions** | **No** | One row in the MCP guide's tool table |
| **Shareholders composition** | **No** | One row in the MCP guide's tool table |
| **Listing performance** | **No** | MCP tool table, a tool definition in the tool-use recipe, Postman listing |
| **News `dimension` field** | **No** | The word appears in recipes only as ML jargon (hidden-layer dimension) and as an unrelated parameter name |

For contrast, the endpoints that *are* worked through in depth: `broker-summary` (GNN part 3),
`foreign-flow` (GNN part 3), `companies/top-changes` (n8n), `free-float`, the screener, company
reports, and daily transactions.

So the six areas above are genuinely unexploited: 1–2 credits per call, real differentiated
data, and **no tutorial a judge could pattern-match your project against**. Mining is the
starkest — 19 endpoints and a single passing reference across 726K characters of recipes.

---

## Recipe coverage ledger

For anyone continuing this research, here is what has and hasn't been mined from the 39:

| Read and mined | Skimmed | Not read |
| --- | --- | --- |
| MCP guide · Agent skills guide · GNN parts 1–3 · Banking benchmark · API security · n8n ×2 · Human-agent (FinArena) · Multi-agent workflows | Portfolio optimization · SectorScan 1–2 · Quick-start Python 00–05 | Animated plots in R ×5 · Excel · Sheets · Looker ×2 · Postman collection · Generative-AI 01/04/05/06 · OAuth guides ×2 |

The unread set is dominated by visualization tutorials and no-code integrations. They are
worth a look only if your project targets the no-code or BI angle — the API knowledge in them
is a subset of what is already captured in
[`../02-sectors-platform/`](../02-sectors-platform/).
