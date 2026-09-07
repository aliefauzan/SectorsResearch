# Recheck · Does Sectors offer live/push data, or must we poll?

7 September 2026. Question: is the "no realtime, poll only" claim in `docs/api/` actually
true, or an artifact of the 4 September capture?

Method: refetched the live spec and diffed it; grepped spec and docs for every push primitive;
opened `sectors.app` in a browser (it sits behind a Vercel Security Checkpoint that blocks
Jina Reader with 429).

## 1. The captured spec is still current

```
https://docs.sectors.app/schema.json     HTTP 200, 951,210 bytes  → cmp: IDENTICAL
https://docs.sectors.app/llms-full.txt   HTTP 200, 839,575 bytes  → cmp: IDENTICAL
```

Byte-identical to the 4 September capture in `evidence/spec/`. Nothing has changed. The
66-endpoint surface is current.

## 2. No push primitive exists anywhere

Term counts across `schema.json` + `llms-full.txt` + `llms.txt`:

| Term | Hits | What they actually are |
| --- | --- | --- |
| `websocket`, `web socket` | **0** | — |
| `server-sent`, `sse` (as a word) | **0** | — |
| `realtime` | **0** | — |
| `webhook` | 22 | **All outbound.** Every hit is the n8n recipe pushing *to* Discord. Verbatim: *"with a webhook, you are the one pushing data, and the receiving service decides what to do with it"* |
| `notifications/`, `resources/subscribe` | **0** | No MCP subscription capability |
| `intraday` | 4 | Only field descriptions — *"Intraday high in IDR"*, *"Intraday low in IDR"* on the daily bar, and the SGD equivalents |

**MCP transport is "Streamable HTTP."** That is the MCP protocol's transport name, not market
data streaming. It replaced the old SSE transport for request/response. Reading it as a live
feed is a mistake worth naming explicitly.

**`intraday` means the day's extremes inside an end-of-day bar.** Not an intraday series.

## 3. Sectors says "refreshed daily" in their own footer

On every page of `sectors.app`, including `/workflow` and `/indonesia/economic-sectors`:

> **"Near-complete IDX & SGX coverage, refreshed daily. Serving 40,000 financial workflows
> each month."**

`/indonesia/economic-sectors` renders 1-week, YTD and 1-year performance windows. No
timestamp, no "as of HH:MM", no intraday anything.

## 4. Two marketing lines contradict that footer

Both say "real-time", neither is an endpoint-level claim:

1. Postman tutorial intro — *"You can access real-time stock prices, historical data, market
   trends, and more."*
2. Workflow builder, step 3 — *"…or execute a Sectors Financial API call to fetch real-time
   data."*

The Workflow line sits on a page whose own footer says *refreshed daily*. **No endpoint
description in the OpenAPI spec claims real-time.** Treat "real-time" in Sectors' copy as
marketing for "current end-of-day", and design against the endpoint docs.

## 5. The finding that changes the architecture — Workflow is a push channel

Read live from `sectors.app/workflow`, 7 September 2026:

> **"Instantly trigger custom notifications when critical tags appear in any stock."**

Three-step builder: select entities (stocks, watchlist, sector, sub-sector, industry,
sub-industry) → define trigger conditions (event tags, significant price movements, or news
mentions) → choose an action.

> **"Deliver notifications via WhatsApp, Email, Slack, Telegram, or Google Sheets — or execute
> a Sectors Financial API call to fetch real-time data. Each successful execution consumes
> 1 Sectors credit."**

So **Sectors does operate a push mechanism.** It is just not exposed as a webhook to an
arbitrary URL of yours.

**The workaround is legitimate and cheap:** point a Workflow at a Slack channel or Telegram
bot **you control**, and have your own service consume from there.

```
Sectors Workflow → Slack / Telegram (yours) → your consumer → your pipeline
```

No polling. 1 credit per fire, billed only on successful execution.

Limits: triggers are confined to Sectors' pre-assigned tags — `new-high`, `new-low`,
`top-20-institution-buying`, `top-ten-1m-leaders`, `insider-1-month-buy` — plus price movements
and news mentions. You cannot trigger on a metric you computed. No arbitrary HTTP target.

## 6. Open question that must be asked in Slack

`docs/hackathon/01-rules.md` grants **"1,000 Sectors API credits per registered team"** and
says nothing about plan access. Workflow is an **Insider-plan** feature per `sectors.app/pricing`.

**Do hackathon teams get Workflow access, or only API credits?**

If yes, the whole Track 02 architecture changes — push instead of poll, and the unattended-run
evidence becomes a real Slack channel with a multi-day message history. Ask in `#discussion`
before committing to a polling design.

## 7. No streaming feature has ever shipped

`sectors.app/release`, read live: the latest entry is still **2026-08-10 "Foreign Flows"**.
Going back to 2026-01-01, no release mentions streaming, websockets, webhooks or realtime. The
August entry's API item is *"full observability over your Sectors API keys"* — usage
visibility in the product, not a data feed.

## Verdict

**Confirmed. There is no live or streaming market-data feed at any price.** The API is
end-of-day and poll-only, every billed poll costs at least 1 credit, and freshness is capped by
upstream ingestion (filings 2h, news 4h, suspensions daily 10:00 WIB, index-daily 18:00 WIB).

**One correction to the earlier analysis:** "polling is the only option" was too strong.
Sectors Workflow pushes, at 1 credit per execution, on their tags only — and a Slack or
Telegram channel you own turns that into an event stream you can consume. Whether hackathon
teams can use it is unresolved.

## Not checked

- Enterprise tiers. `help@sectors.app` handles organisation enquiries; a licensed real-time
  feed may exist commercially and would be irrelevant to a 1,000-credit grant either way.
- Whether IDX itself licenses real-time data to aggregators on terms that would explain the
  absence. Plausible, unverified here.

---

# Addendum · every other official Sectors surface

Question: is there an official channel besides Workflow that pushes, or that avoids per-call
billing? Checked each surface against the live docs.

| Surface | Bills credits? | Freshness | Pushes? |
| --- | --- | --- | --- |
| REST API, 66 endpoints | yes, per endpoint | end-of-day | no |
| **Sectors MCP** | **yes — same API, same per-endpoint rates** | end-of-day | no. Zero `notifications/`, zero `resources/subscribe` |
| OAuth connectors (Claude, ChatGPT) | yes — same MCP | end-of-day | no |
| **Google Sheets** (via API Connector) | **yes, every refresh** | on refresh | no. Scheduling hourly/daily is API Connector's own **paid** feature, not Sectors' |
| **Excel Power Query** | **yes, every refresh** | on manual `Refresh` | no |
| **Looker Studio** | **yes, every scheduled refresh** | `Data Freshness` schedule | no |
| n8n | yes | on schedule | no — the n8n webhook pushes *from* you *to* Discord |
| Public web pages | no credits | daily | no |
| Weekly market brief newsletter | no credits | weekly | **yes, but weekly** |
| CSV/JSON Data Exporter on report pages | plan-gated, not credit-gated | daily | no |

**Every developer integration is a thin wrapper over the same billed REST API.** Sheets, Excel,
Looker and n8n all call `https://api.sectors.app/v2/...` with your key, so a scheduled refresh
is a scheduled charge. There is no cheaper official path and no second push channel.

The docs use "live" for these too — *"Work with live financial data that refreshes
automatically directly in Business Intelligence tools"* — meaning auto-refresh, not streaming.
Same pattern as the Postman and Workflow copy.

## Free official surfaces, and their limits

The public web pages cost nothing to read: **IDX Weekly Digest**
(`/indonesia/2026/latest`), Top Gainers Today, Dividend Calendar, Stock Lists, foreign flow,
broker rankings, conglomerate groups, BUMN, index pages, economic sectors.

The Weekly Digest is genuinely rich — weekly market cap change, top gainers and losers with
market caps, sector performance, index performance, breadth counts. **But it lags:** read on
7 September 2026, the "latest" digest was still **Week 34, 24–28 August**.

Scraping these pages to avoid API billing is a disqualification risk, not a workaround — the
judges are Supertype and the repository is reviewed.

## Billing rules, from the v2 changelog dated 2026-07-31

Two items here are not in `docs/api/05-credit-budget.md` and should be:

- **Empty results are no longer errors.** List, filter, ranking and date-range queries that
  match nothing now return `200` with an empty result. A 2xx bills — **so an empty match still
  costs the endpoint's full price.**
- **Structured error codes** now appear on middleware errors: `subscription_does_not_allow`,
  `subscription_not_active`, **`monthly_limit_exceeded`**, `insufficient_credits`,
  `service_unavailable`. `monthly_limit_exceeded` implies a monthly cap distinct from the
  credit balance. Its value is undocumented — worth asking in `#discussion`.
- `503` with `code: service_unavailable` on database failures, instead of `500`.

Confirms and refines what the budget doc already has: 2xx and 404 bill; 400, 401/403, 429 and
5xx are free; a screener 400 costs 1 credit only when it fails *after* the `?q=` text reached
the LLM.

## Doc bug found while checking

`docs/api/04-mcp-and-ai-agents.md` line 261 advises logging **`X-Credits-Charged`** per call.
No such header exists — 116 live calls on 6 September returned zero headers matching
`credit|quota|rate.?limit|usage|balance`. That line predates the live verification and should
be corrected to say the client must meter its own spend.
