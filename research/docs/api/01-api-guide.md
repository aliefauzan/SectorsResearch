# Sectors Financial API — Practical Guide

> Everything you need before writing the first request. Endpoint-by-endpoint detail lives in
> [`02-endpoint-reference.md`](02-endpoint-reference.md).

## The basics

| | |
| --- | --- |
| **Base URL** | `https://api.sectors.app` |
| **Version** | v2 only (`info.version` = 2.0.0) |
| **Method** | `GET` for all 70 endpoints |
| **Auth header** | `Authorization: <YOUR_API_KEY>` — **raw key, no `Bearer` prefix** |
| **Format** | JSON |
| **Get a key** | <https://sectors.app/api> (requires Insider plan, or the hackathon credit grant) |
| **Spec** | <https://docs.sectors.app/schema.json> |

> ⚠️ **The two auth styles differ and this catches people.**
> The **REST API** takes the raw key: `Authorization: sk_xxx`.
> The **MCP server** takes a bearer token: `Authorization: Bearer sk_xxx`.
> Same key, different header format. A 401 against MCP is usually a missing `Bearer `.

The OpenAPI spec also declares an `OAuthBearerAuth` scheme — a bearer token from the `/oauth/`
authorization flow — which is what the one-click Claude and ChatGPT connectors use.

### What the REST API actually does when something is wrong

Probed live on 6 September 2026 — all of these are free except the last, and none of them is
described in the spec. Details in [`audit/VERIFICATION-LIVE.md`](../../audit/VERIFICATION-LIVE.md).

| Situation | Status | Body |
| --- | --- | --- |
| No `Authorization` header | **403**, not 401 | `{"error": "Authentication credentials were not provided."}` |
| `POST` (or any non-GET) on a documented endpoint | **405** | `{"error": "Method \"POST\" not allowed."}` |
| A path that routes nowhere | **404** | `{"details": "The requested endpoint does not exist", "urls": {…}}` — note: **no `error` key**, unlike every other failure |
| A required query parameter omitted | **400** | `{"error": "Query parameter 'commodity_type' is required."}` |
| An identifier that does not exist | **404**, **billed 1** | `{"error": "Given stock symbol does not exist for this data."}` |
| Default `Python-urllib` user agent | **403** | `{"error": "error code: 1010"}` — Cloudflare, not the API. Send a browser `User-Agent` |
| `OPTIONS` | **200**, **billed 1** | a CORS preflight from a browser client costs a credit |

Two conveniences worth knowing: the **trailing slash is optional** (`/v2/subsectors` works),
and symbols are accepted **lowercase and with the `.JK` suffix** (`bbca`, `BBCA.JK`, `BBCA` all
resolve).

### First request

```python
import os
import requests

BASE = "https://api.sectors.app/v2"
headers = {"Authorization": os.environ["SECTORS_API_KEY"]}   # no "Bearer"

response = requests.get(f"{BASE}/subsectors/", headers=headers, timeout=30)
response.raise_for_status()
print(response.json())
```

```bash
curl -H "Authorization: $SECTORS_API_KEY" https://api.sectors.app/v2/subsectors/
```

Never hardcode the key. The docs' own security recipe uses `SECTORS_API_KEY` as the
environment variable name — the agent skills and MCP guide assume the same.

In this repository that variable comes from a git-ignored `.env` at the root, loaded by
[`harness/src/sectors_env.py`](../../harness/src/sectors_env.py), so no one has to export
anything by hand:

```python
from sectors_env import api_key, base_url

headers = {"Authorization": api_key()}
```

For a shell command that needs the variable exported — `curl`, or a tool that reads the
environment directly — source the file for that command only:

```bash
set -a && . .env && set +a          # exports .env into this shell
curl -H "Authorization: $SECTORS_API_KEY" https://api.sectors.app/v2/subsectors/
```

---

## v1 is gone

Sectors Financial API v1 was **discontinued on 2026-05-11**. Every `/v1/*` path now returns
**HTTP 410 Gone** with `Deprecation`, `Sunset` and `Link: rel="successor-version"` headers.

This matters because **many tutorials, blog posts and older recipes still show `/v1/`** —
including Sectors' own [agent-skills repo](https://github.com/supertypeai/sectors-agent-skills),
which as of 4 September 2026 still hardcodes `https://api.sectors.app/v1` throughout
(see [`04-mcp-and-ai-agents.md`](04-mcp-and-ai-agents.md)).
Most migrate by changing `/v1/` to `/v2/`, but not all — the screener, rankings and news
endpoints changed shape. See the
[migration guide](https://docs.sectors.app/get-started/v2/migration-guide).

Notable v2 renames to watch for in old code:

- `idx_ticker` → **`symbol`**, everywhere, in both params and response bodies
- `desc=true` → **`-` prefix** on `order_by` (e.g. `order_by=-market_cap`)
- SGX `/v2/sgx/companies/?sector=` flat array → paginated `{results, pagination}` envelope

### Three v1 endpoints have no v2 equivalent — they were folded into the screener

This is the part of the migration that surprises people, because there is nothing to rename:

| v1 endpoint | v2 replacement |
| --- | --- |
| `/v1/index/{index}/` — companies by index | `/v2/companies/?where=indices in ['lq45', 'idxbumn20']` |
| `/v1/companies/top/?classification=revenue&year=2023` | `/v2/companies/?order_by=-revenue[2023]` |
| Top companies by growth | `/v2/companies/` with the relevant growth field |

**There is no "companies by index" endpoint in v2.** Index membership is a screener array
field, not a route. If you're looking for one, stop looking — this is why you can't find it.

The upside is real: v1 could only query one index at a time and only eight predefined
ranking classifications. v2 can combine indices, sort by *any* of the 219 fields, and filter
at the same time — all for the same 1 credit.

> Note the case difference: migration examples write index codes lowercase in `where`
> (`'lq45'`, `'idxbumn20'`) while company-report `indices` arrays come back uppercase
> (`LQ45`). The docs state string comparisons are case-insensitive, so both should work —
> but if an index filter returns empty, try the other case before assuming no matches.

---

## Credits: how billing actually works

Credits are the currency. The hackathon grants **1,000 per team**; an Insider subscription is
5,000/month. Every endpoint declares its cost in its own description, and the
[endpoint reference](02-endpoint-reference.md) has the full table.

### Cost tiers

| Pattern | Cost | Endpoints |
| --- | --- | --- |
| Flat | **1 credit** | 49 of 70 endpoints — most helper lists, daily data, single lookups |
| Flat | **2 credits** | Exactly 4 endpoints, all "top N" rollups: `/v2/most-traded/`, `/v2/brokers/top/`, `/v2/broker-summary/{symbol}/top/`, `/v2/broker-activity/{broker_code}/top/` |
| Screener, natural language `?q=` | **3 credits** | `/v2/companies/`, `/v2/sgx/companies/` |
| Screener, structured `where`/`order_by` | **1 credit** | same endpoints |
| **Per requested section** | 1 × sections | Company Report (**default = all 8 sections = 8 credits**), Subsector Report (default 6), SGX report (default 4) |
| **Per classification × period** | 1 × n × m | Top Company Movers — **default 2 classifications × 5 periods = 10 credits** |
| **Per classification** | 1 × n | Top companies rankings — default all 5 = 5 credits |
| **Per quarter returned** | 1 × n_quarters | Quarterly Financials |
| **Per page** | 1 × pages | Full-universe endpoints — ~32 credits for a full sweep of `/v2/close/` or `/v2/companies/quarterly-financial-dates/` at max `limit=30` |
| **Per 100 companies, rounded up** | | Free Float |

> **The three defaults that will quietly drain your grant:**
> `/v2/company/report/{symbol}/` with no `sections` = **8 credits per company**.
> `/v2/companies/top-changes/` with no params = **10 credits per call**.
> A full `/v2/close/` sweep = **~32 credits**.
> Always pass `sections`, `classifications` and `periods` explicitly.

### What is and isn't billed

Standardized on 2026-07-31:

| Response | Billed? |
| --- | --- |
| **2xx** | Yes — the endpoint's stated cost |
| **404** | **Yes, 1 credit** — a valid request for a symbol that doesn't exist still ran the DB query |
| **400** | **No** — malformed params, invalid dates, unknown sections are free |
| 401 / 403 | No |
| 429 | No |
| 5xx | No |

One exception: a **400 from the screener costs 1 credit** if the failure happened *after* a
natural-language `?q=` was already sent to the LLM (sunk cost). Structured `where`/`order_by`
validation errors are free.

Also from that release: **empty results are no longer errors.** List, filter, ranking and
date-range queries that match nothing return `200` with an empty result. `404` is reserved for
genuinely missing resources.

### Two different error body shapes

The spec declares `400` on 34 endpoints, `404` on 32, and **`429` on all 70** — rate limiting
is universal. But the bodies are not the same shape, and code that assumes one will crash on
the other.

**Endpoint-level errors (400 / 404)** — a single human-readable `error` string:

```json
{"error": "Use a valid date format of YYYY-MM-DD."}
{"error": "Broker 'ZZ' not found in broker data."}
```

**Rate limiting (429)** — an error *code* plus a separate message:

```json
{"error": "RATE_LIMIT_EXCEEDED", "message": "Rate limit exceeded. Consider upgrading."}
```

**Middleware errors (subscription / credits / availability)** — carry the machine-readable
`code` field described below.

So `error` is sometimes prose and sometimes a symbol. Parse defensively:

```python
def explain(response):
    try:
        body = response.json()
    except ValueError:
        return response.status_code, "non-JSON response", response.text[:200]
    # `code` (middleware) is the reliable machine-readable field; `error` may be
    # either a symbol (429) or a human sentence (400/404).
    symbol = body.get("code") or (
        body.get("error") if body.get("message") else None
    )
    message = body.get("message") or body.get("error") or ""
    return response.status_code, symbol, message
```

### Structured error codes

Every middleware error response carries a machine-readable `code`:

| `code` | Meaning |
| --- | --- |
| `subscription_does_not_allow` | Plan lacks access to this endpoint |
| `subscription_not_active` | Plan inactive / bad key |
| `monthly_limit_exceeded` | Monthly quota gone |
| `insufficient_credits` | Credit balance exhausted |
| `service_unavailable` | Database unreachable — returned as **503**, and clients **should retry** |

Branch on `code`, not on the human-readable message.

---

## Hard limits to design around

| Limit | Endpoints |
| --- | --- |
| **90-day** max date range | Daily transaction, index daily, IDX market summary, most-traded, foreign flow, SGX daily |
| **14-day** max date range | Broker summary by symbol, broker activity by code (tightened from 30 on 2026-07-31) |
| **3-year** max range | Commodity price history |
| `limit` max **200** | Companies screener |
| `limit` max **30** | Paginated universe feeds (`/v2/close/`, quarterly-financial-dates) → ~32 pages for full IDX |
| Annual data only | SGX — quarterly bracket notation returns `400 QUARTERLY_NOT_SUPPORTED` |

Anything needing more than 90 days of history has to be **paged and cached**. Budget for it:
one year of daily data for one ticker is 5 calls (5 credits) because of the 90-day cap.

---

## Ticker and slug conventions

| Thing | Format | Examples |
| --- | --- | --- |
| IDX symbol | 4 letters, optional `.jk`, case-insensitive on input | `BBCA`, `bbca`, `BBCA.JK` |
| IDX in responses | always carries `.JK` | `BBCA.JK` |
| SGX symbol | 3–4 alphanumeric, optional `.SI` on input; output always `.SI` | `D05`, `U11`, `Z74` |
| KLSE symbol | 4-digit numeric code | `1155`, `4197` |
| Sector / subsector / industry | **kebab-case slugs** | `financials`, `banks`, `oil-gas-coal`, `software-it-services` |
| Mining company / site | **slug**, not numeric id | |

> The MCP docs say to pass IDX tickers **without** `.JK`. The REST API accepts either. Empty
> results are far more often a wrong kebab-case slug than a missing ticker — always fetch
> `/v2/subsectors/`, `/v2/industries/`, `/v2/subindustries/` and `/v2/tags/` once, cache them,
> and validate against them. Those are 1 credit each and you should never pay twice.

---

## Pagination

Newer list endpoints return a `{results, pagination}` envelope with `limit`/`offset`. Older
ones return a bare array. The mining endpoints were standardized onto the envelope in the
2026-03-06 release. Every endpoint's actual envelope and row keys are catalogued in
[`07-response-shapes.md`](07-response-shapes.md) — check there rather than assuming.

**Freshness polling pattern:** `/v2/companies/quarterly-financial-dates/` supports `?since=`.
Store the dates you've seen, then re-poll with `since` to fetch only companies that reported
a new quarter. A full sweep is ~32 credits; an incremental poll is a fraction of that. This is
the single most credit-efficient way to run a daily "what changed" job.

---

## Data freshness

From the MCP FAQ:

- **Market prices and daily transaction data**: updated **end of day**
- **Quarterly financials**: updated as companies file
- **Dividend data**: updated when announcements are made

There is no real-time or intraday tick feed. Design accordingly — an "alert the instant price
moves" product is not buildable on this API. An end-of-day brief, a post-close screener, or a
filings/news trigger is.

**Per-dataset cadences, from the public ingestion repos.** The docs give one blanket answer;
the pipelines are more specific, and the differences matter if you are scheduling a job:

| Dataset | Refresh | Source |
| --- | --- | --- |
| Insider filings → `/v2/filings/`, `/v2/news/` | **every 2 hours** | `sectors_idx_filing_pipeline` README |
| News articles | every 4 hours (`15 */4 * * *`) | `sectors_news` workflow |
| Index daily → `/v2/index-daily/` | weekdays **18:00 WIB** (`0 11 * * 1-5`) | `sectors_indices_company_list` workflow |
| Suspensions → `/v2/suspensions/` | daily **10:00 WIB** (`0 3 * * *`) | `sectors_idx_suspension` workflow |
| Mining commodity prices | weekly | `coalresearch` README |
| Corporate actions (rights issues, reverse splits, buybacks) | **entered by hand** via a Streamlit app | `sectors_corporate_actions` README |

These are read off committed cron expressions, not observed against the API — see
[`11-data-provenance.md`](11-data-provenance.md). Align a scheduled job to the slowest input
it depends on.

---

## Rate limits

The numeric limit is not published. **It was measured on 6 September 2026:**

> **25 billed requests per rolling ~30 seconds.** Spacing is not what is counted — 25 calls
> back-to-back and 25 calls a second apart both stopped on the 26th. **Free responses do not
> count**: 45 consecutive 400s produced no 429, and free calls sail through while billed ones
> are being refused. **No `Retry-After` header is ever sent.**

Practical consequences:

- **1.5 s between calls is safe** (40/min → 20 per window, 20% headroom). 1.0 s is not; it
  trips on the 25th call.
- **Do not poll a 429.** Retrying every 5 s stayed blocked for 36 s; leaving it alone cleared
  in under a second. Wait out the window.
- A 429 is **not billed**, so a trip costs time, not credits.
- Parameter probing is unlimited as well as free — a 400 costs nothing and consumes no budget.

`capture.py` enforces this itself: it tracks real timestamps, waits only when 25 calls are
already inside the window, and returns the slot when a response turns out to be free. It ran
**28 billed calls back-to-back with no fixed sleep and took zero 429s**. `mock_server.py
--rate-limit` reproduces the ceiling for client-side backoff testing.

The docs' own banking-benchmark recipe recommends `sleep(0.3)` and calls it "not optional …
beyond 10 banks". That is roughly 3 requests/second — **fast enough to trip this limiter in
eight seconds**. Treat the recipe's figure as a minimum courtesy delay, not a safe rate.

---

## Sanity-check gotchas

1. **`Bearer` prefix**: REST = no, MCP = yes.
2. **Trailing slashes**: every documented path ends in `/`. Some servers redirect, some don't. Keep them.
3. **`sections` defaults to everything** — 8 credits for a company report you only needed one section of.
4. **404 costs a credit.** Validate tickers against a cached list before looping.
5. **Screener `q` is mutually exclusive with everything else.** If `q` is present, `where`, `order_by`, `desc`, `limit` and `offset` are all ignored.
6. **Free Float params are mutually exclusive** — at most one filter parameter per request.
7. **Smart FY handling:** "latest year" queries made between January and April default to the previous audited year. A query in early 2026 uses 2024 data. This will surprise you in a year-over-year calculation.
8. **Retry on 503** with backoff — it's the documented signal for a dropped database connection, and it's free.
9. **Old field names** (`idx_ticker`, `desc=true`) are v1. Old tutorials are full of them.
10. **`/v2/companies/top-changes/` hides small caps.** `min_mcap_billion` defaults to **5000** — IDR 5 trillion. Pass `min_mcap_billion=0` to see the whole market.
11. **Date ranges clamp silently.** Ask for two years and you get the most recent 90 days with no warning. `start` defaults to 30 days before `end`; `end` defaults to today; a future `end` returns 400.
12. **`approx=true` is the default on quarterly financials.** You may get the *nearest* quarter, not the one you asked for. Set `approx=false` when exactness matters, and always read the `report_date` back out of the response.
13. **Mining enums are title-case with spaces**, not kebab-case — `Coal`, `Mine Owner`, `Zinc and Lead` — and **the valid set differs per endpoint**. See [`06-parameter-cheatsheet.md`](06-parameter-cheatsheet.md).
14. **Response envelopes are not uniform.** Some endpoints return a bare array, some `{results, pagination}`, some a bespoke object. Check [`07-response-shapes.md`](07-response-shapes.md) before writing a parser.

---

## Security, per the docs' own recipe

The [API security recipe](https://docs.sectors.app/recipes/api-security/01-securing-api-usage)
is worth reading in full. The short version, and the parts the hackathon rules make
non-negotiable:

- Read the key from `SECTORS_API_KEY`; never hardcode, never commit
- `.env` in `.gitignore` from the first commit
- Never log the key, including in error handlers
- `raise_for_status()` and handle failures explicitly — don't let a 401 body flow into a log file
- **Scan git history before submitting**, not just the working tree

If a key does leak after you submit, the rules give you exactly one path: notify `#support`,
revoke and rotate first, then push a commit containing only the removal.
