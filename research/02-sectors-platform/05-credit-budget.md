# Credit Budget — Making 1,000 Credits Last

Registered teams get **1,000 Sectors API credits**, claimable from the portal team page once
every member finishes onboarding. That is **one fifth of a single month** of an Insider
subscription (5,000/month). It is not a lot. This page is how not to run out on day three.

Credits expire when the event concludes, are non-transferable, and farming extra accounts is
a disqualifying offence.

---

## What things actually cost

| Call | Credits | Note |
| --- | --- | --- |
| Any helper list (`/v2/subsectors/`, `/v2/industries/`, `/v2/tags/`) | 1 | Cache once, forever |
| Screener, structured `where`/`order_by`, up to 200 companies | **1** | The best value in the whole API |
| Screener, natural language `?q=` | **3** | 3× the price of the same query written out |
| Daily transaction, one ticker, ≤90 days | 1 | |
| Foreign flow, one ticker, ≤90 days | 1 | |
| Broker summary, one ticker, ≤14 days | 1 | |
| Company report, **all sections (default)** | **8** | |
| Company report, `sections=overview` | **1** | |
| Subsector report, all sections (default) | 6 | |
| Top company movers, **defaults** | **10** | 2 classifications × 5 periods |
| Top company movers, `classifications=top_gainers&periods=1d` | 1 | |
| Quarterly financials, `n_quarters=8` | 8 | 1 per quarter |
| Full `/v2/close/` universe sweep | ~32 | ~32 pages at `limit=30` |
| Full quarterly-dates universe sweep | ~32 | but `?since=` makes repeat polls cheap |
| Free float, whole market (~950 companies) | 10 | 1 per 100, rounded up |
| A 404 on a bad ticker | **1** | the lookup ran |
| A 400 (bad params) | 0 | free — **one exception**: a `?q=` screener 400 that fails *after* the model ran costs **1** |
| A 429 or 5xx | 0 | free — retry safely |

---

## The five rules that save the most

**1. Never let `sections`, `classifications` or `periods` default.**
Three endpoints bill per-item and default to *all* items. Passing the one you need turns an
8-credit call into a 1-credit call. This alone is often the difference between finishing and
running dry.

The same parameters also fix a correctness bug on `/v2/companies/top-changes/`: it defaults
to `min_mcap_billion=5000`, silently excluding everything below IDR 5 trillion. Constraining
the call takes it from 10 credits to 1 *and* lets you see the whole market.

```python
# 8 credits
requests.get(f"{BASE}/company/report/BBCA/", headers=H)

# 1 credit
requests.get(f"{BASE}/company/report/BBCA/", headers=H, params={"sections": "overview"})
```

**2. Use `?q=` exactly once per query shape, then hardcode the translation.**
A natural-language query costs 3 credits; the identical structured query costs 1. Run `q`
once during exploration, read the `llm_translation` field out of the response, and paste the
`where`/`order_by` it produced into your code. Every subsequent run is a third of the price.

**3. Cache everything with a real TTL.**

| Data | TTL |
| --- | --- |
| Subsectors, industries, subindustries, tags, broker registry | Forever (the build is 6 weeks) |
| Company report sections | Until the next quarterly filing |
| Daily prices, foreign flow, broker rows | Until the next market close |
| Screener results | Hours, or until close |

A file-backed cache keyed on `(endpoint, sorted params)` is twenty lines and will save you
hundreds of credits. Write it on day one, not after you run out.

**4. Poll incrementally, never re-sweep.**
`/v2/companies/quarterly-financial-dates/?since=<last-seen>` returns only companies that have
reported since. A full sweep is ~32 credits; the incremental poll is a fraction. For a
scheduled Track 02 job that runs 40 times over the build period, this is the difference
between 1,280 credits and something affordable.

**5. Develop against the mock, not the API.**
[`../03-mock-data/`](../03-mock-data/) serves every one of the 70 endpoints offline from the
official OpenAPI examples, with a credit meter and the same error codes. Point your app at
`http://localhost:8787` while you're iterating. Switch to the live API only to verify shapes
and record the demo. Realistically this is worth 60–80% of your grant.

---

## Sample budgets

### Track 03 — screener/scoring product

| Item | Credits |
| --- | --- |
| Helper lists (subsectors, industries, subindustries, tags) | 4 |
| Screener development, ~40 structured queries | 40 |
| Free float, full market, twice | 20 |
| Company report `overview` for a 30-name shortlist | 30 |
| Daily prices, 30 tickers × 90 days | 30 |
| Foreign flow, 30 tickers | 30 |
| Demo-day fresh pull | 50 |
| Contingency | 100 |
| **Total** | **~304** |

Comfortable. Track 03 is by far the cheapest track to build in.

### Track 02 — scheduled daily brief

| Item | Credits |
| --- | --- |
| Helper lists | 4 |
| Per run: 1 screener + 1 movers (constrained) + 1 news + 1 idx-total | 4 |
| × 40 runs across the build period | 160 |
| Development and debugging runs | 60 |
| Multi-day "real history" runs for the video evidence | 80 |
| Contingency | 100 |
| **Total** | **~404** |

Fine — as long as the per-run cost stays near 4. If a single run defaults its way to 25
credits, 40 runs is 1,000 and you are finished.

### Track 01 — agent product

Hardest to budget, because the model decides how many calls to make.

| Item | Credits |
| --- | --- |
| Helper lists | 4 |
| Agent development — assume ~200 tool calls at ~2 credits average | 400 |
| Evaluation runs over a fixed question set | 150 |
| Demo recording, several takes | 100 |
| Contingency | 200 |
| **Total** | **~854** |

Uncomfortably close to the cap. Mitigations, in order of impact: run the whole development
loop against the mock; cap tool calls per turn; force `sections` in your tool wrapper; cache
by `(symbol, section)`.

---

## A metered client

Log the cost headers from the first request. You cannot manage what you don't measure, and
the API tells you the answer on every response.

```python
import json
import os
import time
from pathlib import Path

import requests

BASE = "https://api.sectors.app/v2"
CACHE = Path(".cache/sectors")
LEDGER = Path(".cache/credits.jsonl")


def get(path, params=None, ttl=3600, retries=3):
    """GET with an on-disk cache, retry on 429/5xx, and a credit ledger."""
    params = params or {}
    key = path.strip("/").replace("/", "_") + "_" + "_".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )
    cached = CACHE / (key + ".json")

    if cached.exists() and time.time() - cached.stat().st_mtime < ttl:
        return json.loads(cached.read_text())

    for attempt in range(retries):
        response = requests.get(
            f"{BASE}{path}",
            headers={"Authorization": os.environ["SECTORS_API_KEY"]},
            params=params,
            timeout=30,
        )
        # 429 and 5xx are free — retrying costs nothing but time.
        if response.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** attempt)
            continue
        break

    charged = response.headers.get("X-Credits-Charged")
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a") as fh:
        fh.write(json.dumps({
            "ts": time.time(),
            "path": path,
            "params": params,
            "status": response.status_code,
            "charged": charged,
        }) + "\n")

    response.raise_for_status()
    payload = response.json()

    CACHE.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(payload))
    return payload
```

Then `wc -l .cache/credits.jsonl` tells you how many calls you've made, and a one-line `jq`
sum over `charged` tells you what you've spent.

Add `time.sleep(0.3)` between sequential calls in any loop over tickers — the docs state
that omitting it beyond ~10 sequential calls produces 429s. 429s are free, but a stalled job
on demo day is not.

> Header names: the live API's exact spend headers are not documented in the OpenAPI spec —
> confirm them against a real response early and adjust the field name. The
> [mock server](../03-mock-data/) emits `X-Credits-Charged` and `X-Credits-Remaining` so the
> ledger logic is exercised either way.

---

## ⚠️ Signing up does not give you API access

Verified in a live signed-in session on 5 September 2026, on a free account created via Google:

**API Key Management** (`sectors.app/api` → API Key Management) shows:

> "Please upgrade your subscription to access Sectors API."

No key can be created, and the Active API Keys table is empty. Confirming what the docs say:
**the API is Insider-only.** A free Sectors account gets the app, not the API.

So for a hackathon team the sequence is not optional:

1. Every member creates a Sectors account and **completes onboarding**
2. Register the team at the hackathon portal by **22 September**
3. **Claim the 1,000 credits from the portal team page** — this is what unlocks API access without an Insider subscription

Until step 3, you cannot make a single live call. Plan your build around that: use the
[mock server and synthetic datasets](../03-mock-data/) from day one, and treat the live API as
something you switch on once, later.

The Key Management page also carries a **"Usage and Balances"** button and a per-key
**"API Usage"** column — this is the credit observability shipped in the August 2026 release.
Once your key exists, that page, not response headers, is the authoritative view of spend.

## Before you claim

Claiming the credits **locks your roster permanently**. Sequence it correctly:

1. Everyone creates a Sectors account and completes onboarding
2. Team is genuinely final — no "we might add someone"
3. Register by 22 September
4. *Then* claim

And remember the grant is per team, once. There is no top-up, and creating extra accounts to
get more is grounds for disqualification.
