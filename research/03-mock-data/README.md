# Simulating Sectors Offline

**Short answer to "can we generate dummy data to simulate what Sectors can do?": yes, two
ways, and one of them is exact.**

| Approach | Fidelity | Volume | Use it for |
| --- | --- | --- | --- |
| **1. OpenAPI fixtures + mock server** | **Exact** — official example payloads for all 70 endpoints | One example per endpoint | Building against real response shapes, agent loops, CI, demos, offline dev |
| **2. Synthetic universe generator** | Plausible, not real | Unlimited | Screener logic, backtests, anomaly detection, load tests, charts that need many rows |

Both are standard-library Python. No pip install, no API key, no credits.

> **Why this matters for the hackathon.** Your grant is 1,000 credits and there is no top-up.
> Development iteration is what burns credits — not the demo. Running the whole build loop
> against a local mock and switching to the live API only to verify and record realistically
> saves 60–80% of the grant. See [`../02-sectors-platform/05-credit-budget.md`](../02-sectors-platform/05-credit-budget.md).

---

## Approach 1 — The mock server (start here)

Sectors publishes a complete OpenAPI 3.0.3 spec at
<https://docs.sectors.app/schema.json>, and **every one of the 70 endpoints carries a real
example response**. Those examples are the exact field names, nesting, units and null-handling
the live API returns — the most faithful offline stand-in obtainable without spending a credit.

### Files

| File | What it does |
| --- | --- |
| `extract_fixtures.py` | Pulls every example response out of the spec into `fixtures/<endpoint>.json` plus an `_index.json` with parameters and credit costs |
| `mock_server.py` | Serves those fixtures as a local `api.sectors.app` |
| `fixtures/` | 70 fixtures + `_index.json`, already generated and committed |

### Run it

```bash
python3 mock_server.py --port 8787 --credits 1000
```

```bash
curl -H "Authorization: dev-key" http://localhost:8787/v2/subsectors/
```

Then point your app at `http://localhost:8787` instead of `https://api.sectors.app`. Same
paths, same shapes, same auth header, zero credits.

### What it emulates

It is deliberately more than a static file server — it reproduces the failure modes that
otherwise only show up in production:

- **`Authorization` required** — 401 with `code: subscription_not_active` if missing
- **A credit meter** charging the documented per-endpoint cost, including the per-section,
  per-classification×period, and per-quarter formulas, and 3 credits for a screener `?q=`.
  The per-item default is read from each endpoint's own description, so an unconstrained
  IDX company report bills 8, a subsector report 6, and an SGX or KLSE report 4 — they are
  **not** all 8, which is what this mock charged until the third verification pass
- **402 `insufficient_credits`** when the budget runs out
- **`X-Credits-Charged` / `X-Credits-Remaining`** response headers
- **410 Gone on any `/v1/*` path**, matching the real v1 sunset
- **Path templating** — `/v2/company/report/BBCA/` matches `/v2/company/report/{symbol}/`
- **`GET /__usage`** — a spend report broken down by endpoint
- **`--chaos 0.1`** — random 429/503 responses so you can prove your retry logic works, using the **real body shapes from the spec**: 429 returns `{"error": "RATE_LIMIT_EXCEEDED", "message": ...}` while middleware errors return a `code` field. Endpoint-level 404s return a bare `{"error": "<sentence>"}`. Code that assumes one shape breaks on the other — this is how you find out locally instead of at the deadline
- **`--latency-ms 250`** — so your timeouts and spinners get exercised

- **A *billed* 404** — `--unknown ZZZZ,XXXX,NOTREAL` (the default). A well-formed request
  naming one of those as a `symbol` or `slug` returns 404 **and charges 1 credit**, exactly
  as the real API bills it: the lookup ran. This is the only error path that costs money, so
  it is the one worth rehearsing. An *unknown endpoint path* still 404s for free, as it does
  live.

### What it deliberately does not emulate

- **Two documented error codes.** `subscription_does_not_allow` and `monthly_limit_exceeded`
  appear in the changelog's list of middleware `code` values but are never emitted here.
  The mock's `version_gone` on `/v1/*` is invented — the real 410 body is undocumented.
- **Empty results.** The Postman collection states that a filter matching nothing returns
  `200` with an empty collection **and still consumes credits**. Fixtures are always
  non-empty, so the mock never produces that case; your parser should still handle it.
- **Parameter validation.** The mock never checks an enum. `?sections=bogus,alsobogus` is
  served as a 200 and **billed 2 credits**; live, "unknown sections" is a `400`, which is
  free. So the mock over-bills a typo instead of teaching you about it. Same for a
  `commodity_type` or `classifications` value outside its enum.
- **Response slicing.** `?sections=overview` bills 1 credit and still returns the whole
  eight-section fixture, because the fixture is served whole. A parser developed here can
  therefore depend on fields the same call would not return live. Constrain `sections` in
  your code *and* assume you only get what you asked for.
- **Per-row billing on `/v2/free-float/`.** The spec bills 1 credit per 100 companies rounded
  up (~10 for the whole market); the fixture has a handful of rows, so the mock charges 1.
  This is the whole of the 9-credit gap between `capture.py`'s ledger (176) and the mock's
  meter (167) on a full-plan rehearsal — expected, not a defect.

### Worked example: budget rehearsal

Run your app against the mock with the *real* grant size and find out whether your design
fits before you spend anything:

```bash
python3 mock_server.py --credits 1000 &
# ... run your full pipeline, or your agent's eval suite ...
curl -s localhost:8787/__usage | python3 -m json.tool
```

```json
{
  "calls": 11,
  "credits_spent": 20,
  "credits_remaining": 980,
  "by_endpoint": {
    "/v2/company/report/{symbol}/": 8,
    "/v2/tags/": 8,
    "/v2/companies/": 3,
    "/v2/subsectors/": 1
  }
}
```

That `by_endpoint` breakdown is where you discover that one careless `company/report` call
inside a loop is eating your grant.

### Regenerate the fixtures

```bash
curl -sL -o ../99-raw/schema.json https://docs.sectors.app/schema.json
python3 extract_fixtures.py
```

### Limitation

One example per endpoint. Query parameters are parsed for billing but do **not** filter the
response — asking for `BBRI` returns the `BBCA` example. That is fine for shape correctness,
wiring, error handling, and agent-loop development. When you need many distinct rows, use
approach 2.

---

## Approach 2 — The synthetic universe

`synth_universe.py` generates an arbitrarily large IDX-shaped dataset using the same field
names, units and taxonomy slugs as the live API.

```bash
python3 synth_universe.py --companies 300 --days 180 --news 500 --out synth/
python3 synth_universe.py --companies 950 --days 365 --seed 7 --out synth/
```

Deterministic — the same `--seed` always produces the same universe, so tests stay stable.

### What it produces

| File | Shape it mimics | Contents |
| --- | --- | --- |
| `companies.json` | `/v2/companies/` | Screener rows: market cap, PE/PB/PS, ROE/ROA, DER, dividends, ESG, free float, growth, tags, indices — plus bank-specific fields (CASA, LDR, NIM, CAR) for `sub_sector = banks` |
| `daily/<SYM>.json` | `/v2/daily/{symbol}/` | Daily close, volume, market cap. Geometric Brownian motion per ticker, walked backwards so the final close matches the company's `last_close_price` |
| `foreign_flow.json` | `/v2/foreign-flow/{symbol}/` | Daily net foreign inflow in IDR, with a per-ticker directional bias |
| `broker_summary.json` | `/v2/broker-summary/{symbol}/` | Per-broker daily buy/sell/net rows using real IDX broker codes, tagged foreign/domestic and retail/mixed/institutional |
| `news.json` | `/v2/news/` | Headlines with symbols, sector, tags, sentiment, timestamps |
| `subsectors.json` | `/v2/subsectors/` | The real IDX sector/subsector taxonomy |

Internally consistent in the ways that matter: market cap = price × shares, PE = market cap ÷
earnings, `market_cap_rank` follows market cap, weekday-only trading days, and the last point
of each price series equals the company's stated last close.

### Why the shapes are realistic

- **Real taxonomy slugs** (`financials`/`banks`, `energy`/`oil-gas-coal`, …) so your sector filters exercise the same code paths as production
- **Real broker codes** (YP, PD, CC, KZ, CS, ZP, …) with foreign/domestic and cohort classification, matching the `/v2/brokers/` registry fields
- **IDR magnitudes** — market caps in the 10¹²–10¹⁵ range, prices in the 50–15,000 range, the same orders of magnitude as IDX
- **Log-normal volume** and GBM prices, so momentum, moving averages, volatility and correlation calculations behave like they will on real data

---

## Approach 2b — the extended datasets (`synth_extended.py`)

`synth_universe.py` models about 22 of the 70 endpoints. The research passes surfaced a lot
of data it did not cover — and it happened to be exactly the data the differentiated project
ideas depend on. `synth_extended.py` fills that in.

```bash
python3 synth_universe.py --companies 200 --days 180   # run this first
python3 synth_extended.py                              # then this
```

It reads `synth/companies.json` and adds:

| Output | Shape it mimics | Unlocks |
| --- | --- | --- |
| `banking.json` | screener yearly bank fields | **Loan at Risk** — NPL + special-mention + restructured, per bank per year, with `gross_loan` so the ratio is computable (idea 3.4) |
| `mining/` (13 files) | the 19 mining endpoints | Licences with types and expiry dates, sites with coordinates, WIUP/WIUPK auctions with phases and participants, ownership trees, production, reserves by province, commodity prices, exports, sales destinations, contracts (idea 3.2) |
| `suspensions.json` | `/v2/suspensions/` | Post-suspension event studies (idea 3.5) |
| `corporate_actions.json` | `/v2/company/corporate-actions/{symbol}/` | Splits, rights, warrants, bonus shares, AGM, dividends |
| `shareholders_composition.json` | `/v2/company/shareholders-composition/{symbol}/` | Monthly local/foreign panel with investor-category breakdown |
| `filings.json` | `/v2/filings/` | Insider and institutional buy/sell with holder types (idea 2.3) |
| `segments.json` | `/v2/company/get-segments/{symbol}/` | Revenue and cost segments **plus key customers** — the concentration dataset (idea 3.3) |
| `quarterly/<SYM>.json` + `quarterly_financial_dates.json` | quarterly financials and the freshness helper | Quarter-over-quarter momentum, freshness polling (idea 2.2) |
| `free_float.json` | `/v2/free-float/` | Crowding screens (idea 3.6) |
| `listing_performance.json` | `/v2/listing-performance/{symbol}/` | IPO performance windows |
| `index_daily/<code>.json` | `/v2/index-daily/{index_code}/` | The eight real index codes: `ihsg`, `lq45`, `idx30`, `kompas100`, `jii70`, `idxbumn20`, `srikehati`, `idxesgl` |
| `idx_total.json` | `/v2/idx-total/` | Whole-market capitalisation series |
| `brokers.json` | `/v2/brokers/` | Broker registry with origin and cohort |
| `broker_top/<SYM>.json` | `/v2/broker-summary/{symbol}/top/` | Top buyers and sellers — see below |
| `trading_days.json` | *(no endpoint exists)* | The real IDX 2026 holiday calendar |

### Two properties it deliberately preserves

**1. The zero-sum trap reproduces.** Summing every buyer's net and every seller's net in
`broker_top/` cancels to approximately zero — exactly as it does on the live API, and exactly
as the organizers' own recipe warns. Verified on generated output:

```
naive sum = 2          (0.00% of the top buyer's net)
dominance = 57,296,263 (top buyer + top seller)
```

That means you can reproduce [the trap](../02-sectors-platform/10-domain-pitfalls.md) locally,
watch your naive implementation return nothing, and verify the dominance-score fix — before
spending a credit.

**2. Holidays are excluded from trading days.** `synth_universe.py` uses a weekdays-only
approximation. This generator applies the real 2026 IDX holiday set, so a scheduled job tested
against it hits the same blank days it will hit in production. `trading_days.json` ships the
holiday list so your job can gate on it.

### Verified on generation

```
banking rows: 32 (8 banks × 4 years)     LAR 0.2035 > NPL 0.0675 ✓
suspensions: 33 · corporate actions: 371
shareholder panels: 3600 · filings: 600
companies with segments: 87 · quarterly series: 200
index series: 8 · broker_top symbols: 60
mining: 120 companies, 300 sites, 400 licences, 60 auctions, 705 gold price points back to 1968
trading days: 260, holidays leaked: 0 ✓
```

Roughly 14 MB at these settings. All flags (`--mining-companies`, `--mining-sites`,
`--mining-licenses`, `--mining-auctions`, `--years`, `--quarters`, `--seed`) scale it.

### What it still does not model

SGX beyond the screener (buybacks, short-sell, filings), KLSE, subsector reports, company
reports, and the ranking endpoints. Those are all covered by the **fixtures** in approach 1 —
exact shapes, one example each — which is enough for wiring and parsing. Use the fixtures for
correctness and the synthetic sets for volume.

### Good uses

- Testing screener and scoring logic across hundreds of companies
- Backtesting a signal over a year of history without paying 5 credits per ticker for the 90-day windows
- Anomaly detection — inject a deliberate outlier and check your detector catches it
- Load-testing a dashboard with 950 companies × 365 days
- Recording a UI walkthrough while the live pull is rate-limited or you're offline

### ⚠️ Do not

- **Never present synthetic numbers as market data.** Not in the demo, not in a screenshot, not in the README.
- **Never ship it as the product's data source.** The rules require Sectors data as a *core* source — the product must lose its core functionality without it. A product running on generated data fails the eligibility check outright.
- If synthetic data appears anywhere in a video, **label it on screen**.

The honest framing, which is also the one that scores well: synthetic data is your
**development and test harness**; Sectors is your **data source**. Saying so in the video
("we developed against a local fixture harness so every live credit went into the product")
reads as engineering maturity, which is exactly what the 30% technical-depth criterion is
looking for.

---

## Recommended workflow

```
day 1        →  extract fixtures, start the mock, build against it
days 2–20    →  all iteration on the mock; live API only to verify a shape you're unsure of
               synthetic universe for anything needing volume
last week    →  switch to live, run the real pipeline, tune, cache aggressively
demo day     →  fresh live pull, record the video
fallback     →  keep the mock working, so a network failure mid-recording is a one-line switch
```

That last point is not paranoia. The judging video is 30% of your score and there are no live
sessions — a rate limit or an outage while recording is a real risk, and having a
`--base-url` flag that falls back to the mock costs you nothing today.

---

## A drop-in client that switches between them

```python
import os
import requests

# One environment variable is the entire switch.
BASE = os.environ.get("SECTORS_BASE_URL", "https://api.sectors.app")
KEY = os.environ.get("SECTORS_API_KEY", "dev-key")


def sectors_get(path, **params):
    response = requests.get(
        f"{BASE}{path}",
        headers={"Authorization": KEY},
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
```

```bash
# development — free
SECTORS_BASE_URL=http://localhost:8787 python3 app.py

# live — costs credits
SECTORS_API_KEY=sk_xxx python3 app.py
```

Build that switch on day one. It is the highest-leverage twelve lines in the project.
