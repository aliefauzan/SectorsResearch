# Live Capture — 6 September 2026

The first pass that actually called the API. Five previous audits verified this corpus against
documentation only; every behavioural claim in it was the documentation's word. This pass
called **every endpoint the API exposes**, recorded each response to disk, and reconciled what
happened against what the corpus says.

**Result: 66 of 70 documented paths returned 200 — every endpoint that can be called. The
other four are duplicate spec entries, proven unreachable by eleven probes. 265 credits of the
1,000 grant. 127 payloads on disk, and the mock serves all 66 endpoints from real data with
zero spec-example fallbacks.**

Evidence: `03-mock-data/recorded/` (payloads, `_manifest.json`, `_ledger.jsonl`) and
[`99-raw/live-capture-2026-09-06.md`](99-raw/live-capture-2026-09-06.md).

---

## Ledger reconciliation

| | |
| --- | --- |
| Attempts | 168 |
| 200 | 129 |
| 404 (**billed 1 each**) | 10 |
| 400 (free) | 20 |
| 403 (free — 5 Cloudflare, 1 no-auth probe) | 6 |
| 405 (free) | 1 |
| 429 (free, mid-sweep) | 2 |
| **Credits billed** | **265** |
| Remaining of grant | ~735 |

Spend by stage: tier 0 helper lists 5 · tier 1 core 28 · tiers 3–4 detail 67 · tier 2 universe
sweeps 74 · coverage-completion plan 40 · root-cause probes 5 (the rest were free failures) ·
defaulted-form fidelity buys 46.

The plan's declared estimate was 176 credits for its 87 calls; it billed 174, the two-credit
difference being the two mining calls that failed free because they were missing required
parameters. The 30-call coverage plan added 40, including 9 billed 404s spent finding out
which identifiers carry data.

---

## Findings

### 1. The API returns no spend headers at all

The corpus flagged this as unresolved: the mock emits `X-Credits-Charged` and
`X-Credits-Remaining`, and `15-fetch-strategy.md` said tier 0 would reveal the real names.
It did. `capture.py` records every response header matching
`credit|quota|rate.?limit|usage|balance`, and across 116 successful live calls it captured
**none**. The `cost_headers` field is empty on every ledger row.

**Consequence:** a client cannot read its own spend. The ledger's `est_cost` is the only
running total available, so the declared cost table cannot be verified per-call from headers —
only by differencing a balance shown in the portal. Any code written against
`X-Credits-Charged` will silently read `None` forever. The mock's header is a convenience, and
must be understood as fiction.

### 2. Four of the "70 endpoints" cannot be called

`/v2/company/report/`, `/v2/subsector/report/`, `/v2/sgx/company/report/` and
`/v2/klse/company/report/` are separate entries in the OpenAPI spec, and five audits counted
them as endpoints. They are not. Each declares its identifier (`symbol`, `sub_sector`) as a
**path** parameter while having no template in the path — so they are duplicate entries for the
templated sibling directly below them. Called bare, all four return a free 400:

```
/v2/company/report/       400  "Please provide a valid stock symbol."
/v2/subsector/report/     400  "Please provide a valid sector."
/v2/sgx/company/report/   400  "Please provide a valid SGX symbol."
```

**The API surface is 66 distinct endpoints, not 70.** The count is not wrong — the spec really
does declare 70 operations — but a build plan that budgets for 70 integrations is budgeting for
four that do not exist.

### 3. `listing-performance` 404s on every blue chip — and each 404 costs a credit

`plan.json` called `/v2/listing-performance/{symbol}/` for BBCA, BBRI, TLKM and ADRO. All four
returned `404 "Given stock symbol does not exist for this data."` and **billed 4 credits**.

The spec's description says why, and no document in this corpus had picked it up: *listing
performance data exists only for tickers listed after May 2005*. Indonesia's blue chips all
listed earlier. `BREN` — the spec's own example — returns 200.

`plan.json` is corrected: the basket entries are replaced by a single `BREN` call.

### 4. SGX and KLSE use a different `classifications` vocabulary than IDX

`/v2/companies/top-changes/` takes `top_gainers` / `top_losers`. The SGX and KLSE equivalents
(`/v2/sgx/companies/top/`, `/v2/klse/companies/top/`) reject those and take
`dividend_yield | revenue | earnings | market_cap | pe`. Passing the IDX vocabulary is a free
400, but it is an easy way to lose an afternoon, and both families **bill per classification**,
so leaving the parameter to default costs five credits instead of one.

### 5. Only 9 of 366 mining companies have detail records

The mining detail endpoints — `companies/financials/{slug}`, `companies/performance/{slug}`,
`sales-destination/{slug}` — 404 for almost every slug in `/v2/mining/companies/`, and each
404 bills a credit. Six were spent discovering this on `pt-adaro-indonesia` and
`pt-abm-investama-tbk`, both of which appear in the sites and company lists.

`/v2/mining/companies/` accepts an undocumented-in-prose `has_financials` filter.
`?has_financials=true` returns **9 companies out of 366** — all listed coal holdings
(AADI, ADMR, ADRO, BYAN, BUMI, DSSA …). Those nine are the entire addressable universe for
three of the nineteen mining endpoints. Aim there; never guess a slug.

### 6. Two plan entries were missing required parameters

`/v2/mining/total-production/` requires `commodity_type`; `/v2/mining/exports/` requires both
`year` and `commodity_type`. `plan.json` sent neither and took two free 400s. Corrected, and
both now return 200.

### 7. The rate limit, measured: 25 billed requests per rolling 30 seconds

Bisected on 6 September 2026. The docs publish no number, and the corpus had only "429 at
0.35 s, clean at 2.0 s" — which was itself misleading, because the runs that "completed clean"
at 2.0 s were resume runs that only needed 7 and 1 more pages, never approaching the ceiling.

| Test | Offered rate | Result |
| --- | --- | --- |
| 45 × free 400 (`/v2/index-daily/klse/`), no spacing | 3.9 req/s | **no 429 at all** — free responses are not counted |
| 25 × billed, no spacing | 3.5 req/s | **429 on the 26th**, after 7 s |
| 25 × billed, 1.0 s spacing (60/min) | 1 req/s | **429 on the 26th**, after 26 s |
| 32 × billed, 1.5 s spacing (40/min) | 0.67 req/s | **32/32 clean**, 56 s |

Spacing is not what the limiter measures — both the 7-second burst and the 26-second one
stopped on exactly the 26th call. It is a **count within a window**: 25 billed requests per
rolling ~30 seconds. Every model fits: 1.5 s spacing puts 20 requests in any window and never
trips; 1.0 s puts 30 and trips at 25; back-to-back puts 25 in seven seconds and trips there.

**Free responses do not consume the budget.** Forty-five consecutive 400s produced no 429, and
ten more sailed through while a billed burst was being refused. So parameter probing is
unlimited as well as unbilled.

**No `Retry-After` header is ever sent**, on any 429.

**Retrying into a 429 appears to extend the lockout.** After the first drain, polling every
5 s stayed blocked for 36.5 s. After the second, a single probe succeeded immediately — 0.5 s
after the refusal. Wait out the window; do not poll it.

`capture.py` now enforces this itself. `RateWindow` tracks real timestamps, waits only when 25
calls are already inside the window, and hands the slot back when a response turns out to be
free. Proof: **28 billed calls back-to-back with no fixed sleep at all — 28/28, zero 429s**,
where 25 was previously the hard stop. The default spacing also moved from 0.35 s to 1.5 s.

`mock_server.py --rate-limit` reproduces the ceiling exactly, including the free-response
exemption, so client backoff can be tested without spending anything.

### 7b. Superseded: what the sweeps showed before the bisect

The docs publish no number. Both 32-page universe sweeps hit `429` mid-sweep at the
documented-safe 0.35 s spacing — `/v2/close/` after 25 pages, quarterly-financial-dates after
31 — with the retry budget exhausted. Neither 429 was billed, and `capture.py`'s resume logic
worked exactly as designed: pages already paid for were kept, and the resume run bought only
the missing pages (25 + 7, and 31 + 1 — not 32 + 32).

At **2.0 s** spacing both sweeps completed without a single 429. `capture.py` now reads
`SECTORS_RATE_LIMIT_SLEEP`; use 1.0 s for ordinary runs and 2.0 s for paginated sweeps.

### 8. Cloudflare blocks the Python standard library outright

The very first live attempt returned `403 {"error": "error code: 1010"}` on all five tier-0
calls. That is a Cloudflare edge block on the default `Python-urllib/3.x` user agent — not an
auth failure, and not billed. Sending a normal browser `User-Agent` fixes it completely.

**This would have been the team's first five minutes with the API**, and the error says nothing
about user agents. `capture.py` now sets one (overridable via `SECTORS_USER_AGENT`). Anyone
writing their own client with `urllib` or a bare `requests` call needs the same.

### 9. One response-shape difference the documentation does not show

Live payloads were diffed field-by-field against the spec's own example for all 66 reachable
endpoints. The shapes agree everywhere except one, and it matters:

`/v2/financials/quarterly/{symbol}/` returns a **sector-dependent** field name. Banks
(BBCA, BBRI) return `realized_capital_goods_investment` — the name in the spec example.
Non-banks (ADRO, TLKM) return `capital_expenditure` in the same slot, and no
`realized_capital_goods_investment` at all. `financials_sector_metrics` is likewise populated
for banks and an empty object for everyone else.

A parser written against the documented example handles banks and silently drops capex for
every other company in the market.

Everything else that differed was explained by our own constrained parameters — a report
requested with `sections=overview` returns only the overview key, a `top` call constrained to
one classification returns only that classification — which is confirmation that the
`sections`-slicing behaviour works as documented.

---

## Coverage

| | |
| --- | --- |
| Documented operations in the spec | 70 |
| Distinct, callable endpoints | **66** |
| Returned 200 and recorded | **66 / 66** |
| Recorded payloads on disk | 116 (1.3 MB) |
| Replayed by `mock_server.py` | all of them, `X-Mock-Source: recording` |

`plan.json` reaches 40 endpoints. The remaining 26 needed identifiers that only a previous
response can supply — a broker code, a mining slug, a WIUP code, an SGX ticker — so
[`03-mock-data/plan_live.py`](03-mock-data/plan_live.py) reads them out of `recorded/` and
writes `plan-live.json`. Run it again after any capture and it resolves identifiers that were
not yet on disk (the KLSE symbol needs `/v2/klse/companies/` fetched first). Nothing in it is
guessed, because a guessed identifier is a billed 404.

---

## What this means for the build

Development no longer needs the API. `mock_server.py` serves 116 real payloads at
`X-Mock-Source: recording`, falling back to spec examples elsewhere, with the same credit
meter and the same 401/404/429 behaviour. Point the app at it:

```bash
python3 mock_server.py --port 8787
SECTORS_BASE_URL=http://localhost:8787 python3 app.py
```

Roughly 786 credits remain. The expensive things left are per-symbol breadth (each company
report, daily series or foreign-flow call is 1 credit per ticker) and re-capturing anything
time-sensitive near demo day. Both universe sweeps and every endpoint shape are already paid
for and on disk.

---

## Mock fidelity audit — same day, after the capture

The capture is only worth what the mock does with it, so the mock was then audited against
it. `03-mock-data/verify_mock.py` reruns the whole audit for zero credits and exits non-zero
on any divergence.

**Replay: 116 of 116 recorded calls come back byte-identical**, sourced from the recording
rather than a spec example.

Eleven divergences were found and closed:

| Divergence | Live | Mock, before | Now |
| --- | --- | --- | --- |
| Unknown IDX symbol | 404, billed 1 | **200 with BBCA's fixture** unless the symbol was in a hardcoded `ZZZZ,XXXX,NOTREAL` list | 404 billed 1, checked against the 962-symbol universe the `/v2/close/` sweep proves |
| Mining company with no financials | 404, billed 1 | 200 | 404 billed 1, checked against the nine `?has_financials=true` returns |
| Missing required query parameter | free 400 | **200 with a fixture** | free 400, same message |
| The four bare `report/` roots | free 400 | 200, and one of them **charged 8 credits** | free 400, same message |
| Spend headers | none | `X-Credits-Charged` / `X-Credits-Remaining` on every response | none, unless `--credit-headers` |
| Missing `Authorization` | **403** `"Authentication credentials were not provided."` | 401 `subscription_not_active` — a status and a code the API never sends | 403, verbatim body |
| `POST` / `PUT` / `DELETE` | 405 `Method "POST" not allowed.` | connection error, no HTTP response | 405, verbatim body |
| `OPTIONS` | 200, billed | not handled | answered like GET |
| Unrouted path | 404 `{"details", "urls"}` | 404 `{"error": "No such endpoint…"}` | the live body shape |
| Path without trailing slash | 200 | matched the route but missed the recording | normalised before lookup |
| Index code outside the documented 17 | free 400 | 200 with a fixture — `sti`, `klse` and `nonsense` all "worked" | free 400; `sti` allowed, `klse` rejected, as live |

A sixth, subtler one: `capture.py` stores a 32-page sweep as one merged 960-row payload, and
the mock served that blob back for `?limit=30` — 960 rows in a response whose envelope claimed
`limit: 30`. It now **slices** merged recordings, so paging against the mock behaves like
paging against the API: real rows, a `has_next` that terminates, and `X-Mock-Source:
recording-slice`.

Deliberately **not** enforced: identifier checking for mining companies at large, SGX and KLSE.
Those universes were sampled, not swept, so 404ing an unknown identifier there would invent
failures for symbols that really exist. The live capture also proved the mining detail
endpoints are not one universe — `/v2/mining/companies/performance/pt-adaro-indonesia/` returns
200 for a slug that `financials` 404s — so only `financials` is checked.

`GET /__coverage` on the running mock now reports the state directly:

```json
{"spec_operations": 70, "callable_endpoints": 66,
 "served_from_recordings": 66, "served_from_spec_examples": 0,
 "unreachable_spec_duplicates": ["/v2/company/report/", "…"], "recordings": 127}
```

Three things the mock still cannot copy, and should not be trusted for: **per-call credit
cost** (unobservable live — no headers), the **Cloudflare user-agent block**, and **real rate
limiting** (`--chaos` fakes it).

## Every failing call, root-caused

Each failure from the capture was taken back to a cause and then either fixed or proven
unfixable. Nothing is left as "it 404s, we do not know why".

### Solved — the call now works

| Call | Why it failed | Fix |
| --- | --- | --- |
| All five tier-0 calls, `403 error code: 1010` | Cloudflare edge-blocks the stdlib's `Python-urllib/3.x` agent. Not auth, not billed | Send a browser `User-Agent`. `capture.py` does; `SECTORS_USER_AGENT` overrides |
| `/v2/mining/total-production/` `400` | `commodity_type` is required and the plan omitted it | Parameter supplied; **200** |
| `/v2/mining/exports/` `400` | `year` **and** `commodity_type` both required | Both supplied; **200** |
| `/v2/listing-performance/{BBCA,BBRI,TLKM,ADRO}/` `404` ×4, **billed** | The endpoint only holds tickers listed after May 2005; every Indonesian blue chip predates that | Use a post-2005 listing. `BREN` → **200** |
| `/v2/mining/companies/financials/{slug}/` `404` ×2, **billed** | Financial records exist for 9 of 366 companies | `?has_financials=true` names the nine. `pt-adaro-andalan-indonesia-tbk` → **200** |
| `/v2/mining/sales-destination/{slug}/` `404` ×2, **billed** | Same coverage limit | Same nine; → **200** |
| `/v2/mining/companies/performance/{slug}/` `404`, **billed** | Sparse per-slug coverage — but **not** the same universe as financials: `pt-adaro-indonesia` 404s on financials and **200s** on performance | Any slug with production records; → **200** |
| `/v2/sgx/companies/top/`, `/v2/klse/companies/top/` `400` | Sent the IDX vocabulary (`top_gainers`). These take `dividend_yield\|revenue\|earnings\|market_cap\|pe` | Correct vocabulary; → **200** |

### Proven unreachable — and it is not our mistake

The four bare `report/` roots were probed **eleven ways** before being called impossible:
`?symbol=`, `?symbols=`, `?ticker=`, `?stock=`, `?q=`, no parameters at all, and the sector
variants `?sub_sector=`, `?sector=`, `?subsector=`. Every one returns the same free 400:

```
/v2/company/report/       →  "Please provide a valid stock symbol."
/v2/subsector/report/     →  "Please provide a valid sector."
/v2/sgx/company/report/   →  "Please provide a valid SGX symbol."
/v2/klse/company/report/  →  "Please provide a valid KLSE symbol."
```

The identifier must be a **path segment**; no query form substitutes for it. These four are the
same route as their templated sibling with the segment omitted — a spec-generation artefact.
The documentation site agrees: it never lists three of the four. Cost of proving it: **0
credits**, since 400s are free.

### Transport behaviour, probed because nothing documented it

| Probe | Result |
| --- | --- |
| No `Authorization` header | **403** `"Authentication credentials were not provided."` — **not** the 401 the mock had been returning |
| `POST` on a documented GET | **405** `Method "POST" not allowed.`, free |
| `OPTIONS` | **200**, and **billed 1** — a browser CORS preflight costs a credit |
| Path without the trailing slash (`/v2/subsectors`) | **200**, identical payload |
| Lowercase symbol (`/v2/company/report/bbca/`) | **200** |
| Symbol with suffix (`BBCA.JK`) | **200** |
| Unrouted path (`/v2/does-not-exist/`) | **404** with a different body shape: `{"details": …, "urls": {…}}`, no `error` key |
| `/v2/index-daily/sti/` | **200 — the Straits Times index resolves.** Pass 3 called this unverifiable; pass 4 inferred it from a database table name. It is now observed |
| `/v2/index-daily/klse/` | **400** `"Please provide a valid index code."` — the candidate 18th code found in an ingestion repo **is not one**. The set is the documented 17 |

### Bought deliberately, to remove the last spec-example fallbacks

The expensive defaulted forms had never been called, so the mock could only guess at them.
46 credits closed that: the all-sections company report (8), subsector report (6), defaulted
top-changes (10), SGX and KLSE reports (4 each), defaulted SGX and KLSE `top` (5 each), and the
natural-language screener (3).

The screener call also settles a documented-but-unobserved claim: `?q=` returns an
`llm_translation` object carrying the exact structured query the model produced —
`{"where": "sub_sector = 'Banks' and roe[2025] > 0.15", "order_by": "-market_cap", …}` — and
it sets `include_query_values` on its own, so the rows come back with `query_values` populated
even though the request never asked for them.

## Endpoint census — is anything missing?

Three independent sources, all agreeing, none of them this corpus:

| Source | Count | Result |
| --- | --- | --- |
| `docs.sectors.app/schema.json` | 70 operations | 66 callable + 4 bare-root duplicates |
| The documentation site's own API reference (`llms.txt`, `llms-full.txt`) | 67 unique `GET /v2/…` literals | every one is in the spec; **none outside it**. The three the docs never mention are exactly the bare `subsector`, `sgx` and `klse` report roots |
| The live Sectors MCP server, enumerated this session | **66 tools** | maps **1:1 onto the 66 callable endpoints** — no tool without an endpoint, no endpoint without a tool |

Every `/v2/…` string in the whole `99-raw/` capture set was also resolved: the
`/v2/indonesia/…`, `/v2/singapore/…` and `/v2/malaysia/…` paths that appear there are
documentation URLs (`docs.sectors.app/api-references/v2/…`), not API routes.

**Nothing is missing.** The API is 66 endpoints, all 66 have been called, and all 66 are on
disk.

## Cost model — settled against the portal's own usage log

The portal exports a usage log: one row per request, with the credits actually charged. Five
pages of it (408 rows, the whole session) were exported on 6 September and are committed at
[`99-raw/usage-log/`](99-raw/usage-log/). `03-mock-data/reconcile_usage.py` diffs them against
the ledger and exits non-zero on any unexplained gap.

**Portal total: 377. Harness model: 377. Exact match** — across 131 endpoints.

| Status | Requests | Credits charged |
| --- | --- | --- |
| 200 | 303 | 368 |
| 400 | 95 | **0** |
| 404 | 9 | **9** (1 each) |
| 405 | 1 | **0** |

**429 and 403 do not appear in the log at all.** They are rejected before accounting — which
is why a rate-limit trip and a Cloudflare block cost nothing, now confirmed from the billing
side rather than inferred.

Every non-flat cost claim in the corpus is confirmed by a charged row:

| Charged | Call | Claim |
| --- | --- | --- |
| **10** | `/v2/free-float/` | 1 per 100 companies, ~961 companies |
| **10** | `/v2/companies/top-changes/` defaulted | 2 classifications × 5 periods |
| **8** | `/v2/company/report/BBCA/` defaulted | 1 per section |
| **6** | `/v2/subsector/report/banks/` defaulted | 1 per section |
| **5** | SGX and KLSE `companies/top/` defaulted | 1 per classification, 5 of them |
| **4** | `/v2/financials/quarterly/{symbol}/?n_quarters=4` | 1 per quarter |
| **4** | SGX and KLSE `company/report/` defaulted | 1 per section, 4 sections |
| **3** | `/v2/companies/?q=…` | natural language is 3× |
| **2** | `most-traded`, `brokers/top`, `broker-summary/{}/top`, `broker-activity/{}/top` | the four flat-2 endpoints |

**The match also caught two errors in this harness** — and it is worth being precise about how
close that came to hiding them, because the two cancelled out exactly:

1. `plan_live.py` hardcoded **1 credit** for `/v2/broker-activity/{code}/top/`. The spec says
   2, the portal charged 2. It now reads declared costs out of `fixtures/_index.json` instead
   of assuming.
2. `capture.py` billed **1 credit for every 404**, including `/v2/does-not-exist/`. An
   *unrouted* 404 is free; only a routed one — where the lookup actually ran — costs. The two
   are distinguishable by body shape, and `unrouted_404()` now does it.

A third divergence surfaced in the mock: it billed `/v2/free-float/` a flat **1** where the
portal charged **10**. That was its largest single cost error, and it is fixed — the
unfiltered call now bills `ceil(universe/100)` from the recording.

## Still unverified

- **Concurrency.** The rate window was measured with sequential requests only. Whether two
  parallel workers share one 25-per-30 s budget or get one each is untested; assume shared.
- **Whether the 30 s window is exactly 30 s.** Recovery was instant after one drain and took
  36.5 s after another, the difference being that the slow one was polled every 5 s. The
  ceiling of 25 is exact and reproducible; the window length is bracketed, not pinned.
- **Time-sensitivity.** Prices, news, filings and top-changes were captured on 6 September
  2026. Structure and shapes will not move; those values will. Re-capture the time-sensitive
  slice near demo day — `capture.py` will re-buy only what you delete.

Settled since the first draft of this section: the defaulted per-item billing forms, the `?q=`
screener and its `llm_translation`, the rate limit (§7), and **the entire per-call cost model,
against the portal's own billing record**.
