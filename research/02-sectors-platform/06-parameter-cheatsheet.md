# Parameter Cheat Sheet — Valid Values, Defaults, and Silent Filters

> Extracted from the OpenAPI spec's parameter enums and defaults. These values are **not**
> listed together anywhere in the human documentation, and several of them will silently
> change your results if you don't pass them.

---

## ⚠️ The four defaults that will surprise you

**1. `/v2/companies/top-changes/` silently excludes small caps.**

`min_mcap_billion` defaults to **5000** — IDR 5 trillion. Every gainer or loser below that
market cap is invisible unless you override it. If you're building a "top movers" product
and wondering why the interesting small caps never appear, this is why.

```
# Default: only companies above IDR 5T
GET /v2/companies/top-changes/

# The whole market
GET /v2/companies/top-changes/?min_mcap_billion=0&classifications=top_gainers&periods=1d
```

That same call also costs **10 credits by default** (2 classifications × 5 periods) versus
**1 credit** constrained. Passing the parameters fixes both problems at once.

**2. `/v2/financials/quarterly/{symbol}/` has `approx=True` by default.**

The endpoint will return the *nearest* available quarter rather than failing when your exact
`report_date` doesn't exist. Convenient for exploration, dangerous for a pipeline that
assumes it got the quarter it asked for. Set `approx=false` when the exact quarter matters,
and read the `report_date` in the response either way.

**3. Report endpoints default to *all* sections.**

`sections` defaults to everything: 8 sections for the IDX company report, 6 for the subsector
report, 4 for SGX/KLSE. Billing is per section, so the default is the most expensive possible
call. Always pass `sections`.

**4. Date ranges default quietly and clamp silently.**

`start` defaults to 30 days before `end`; `end` defaults to today. **Wider ranges are clamped
to the most recent 90 days** rather than erroring — so a request for two years of history
returns 90 days and no warning. Future `end` dates return 400.

---

## Numeric defaults, minimums and maximums

| Parameter | Endpoint | Default | Min | Max |
| --- | --- | --- | --- | --- |
| `limit` | `/v2/companies/` (screener) | 50 | 1 | **200** |
| `limit` | `/v2/close/`, quarterly-dates universe | 20 | 1 | **30** |
| `offset` | paginated endpoints | 0 | 0 | — |
| `order_by` | `/v2/companies/` | `symbol` | — | — |
| `desc` | `/v2/companies/` | `false` | — | — |
| `include_query_values` | `/v2/companies/` | `false` | — | — |
| `n_stock` | `/v2/companies/top-changes/` | 5 | 1 | 10 |
| `n_stock` | `/v2/klse/companies/top/` | — | 1 | 10 |
| `min_mcap_billion` | `/v2/companies/top-changes/` | **5000** | 0 | — |
| `min_mcap_million` | `/v2/klse/companies/top/` | — | 0 | — |
| `classifications` | `/v2/companies/top-changes/` | **all** | — | — |
| `periods` | `/v2/companies/top-changes/` | **all** | — | — |
| `n_brokers` | `/v2/broker-activity/{code}/top/` | — | 1 | 90 |
| `n_quarters` | `/v2/financials/quarterly/{symbol}/` | — | 1 | — |
| `approx` | `/v2/financials/quarterly/{symbol}/` | **true** | — | — |
| `adjusted` | `/v2/most-traded/` | `false` | — | — |
| `extension` | `/v2/news/` | `idx` | — | — |
| `year` | quarterly-dates universe | — | 1900 | 2026 |
| `financial_year` | `/v2/company/get-segments/{symbol}/` | — | 1900 | 2026 |
| `start_year` / `end_year` | commodity price | — | 1900 | 2026 |
| `min_participants` | mining license auctions | — | 0 | — |

---

## Enumerated values

Passing anything outside these lists returns a 400 — which is free, but wastes a round trip.

### Reports

| Endpoint | `sections` values |
| --- | --- |
| `/v2/company/report/{symbol}/` (IDX) | `overview`, `valuation`, `future`, `peers`, `financials`, `dividend`, `management`, `ownership` |
| `/v2/subsector/report/{sub_sector}/` | `companies`, `growth`, `market_cap`, `stability`, `statistics`, `valuation` |
| `/v2/sgx/company/report/`, `/v2/klse/company/report/` | `overview`, `valuation`, `financials`, `dividend` |

### Rankings

| Parameter | Endpoint | Values |
| --- | --- | --- |
| `classifications` | `/v2/companies/top-changes/` | `top_gainers`, `top_losers` |
| `periods` | `/v2/companies/top-changes/` | `1d`, `7d`, `14d`, `30d`, `365d` |
| `classifications` | SGX / KLSE top companies | `dividend_yield`, `earnings`, `market_cap`, `pe`, `revenue` |

### Brokers

| Parameter | Endpoint | Values |
| --- | --- | --- |
| `origin` | broker-summary top, broker-activity top | `all`, `domestic`, `foreign` |
| `origin` | `/v2/brokers/` registry | `domestic`, `foreign` |
| `cohort` | broker-summary top, broker-activity top | `all`, `institutional`, `mixed`, `retail`, `unknown` |
| `cohort` | `/v2/brokers/` registry | `institutional`, `mixed`, `retail`, `unknown` |
| `metric` | `/v2/brokers/top/` | `gross`, `net` |

> The `origin` × `cohort` grid is the whole basis of a bandarmology product:
> `origin=foreign&cohort=institutional` isolates exactly the flow retail traders care about.

### News & filings

| Parameter | Endpoint | Values |
| --- | --- | --- |
| `extension` | `/v2/news/` | `idx` (default), `mining` |
| `transaction_type` | `/v2/filings/` (IDX) | `buy`, `sell`, `others` |
| `transaction_type` | `/v2/sgx/filings/` | `award`, `buy`, `sell`, `transfer`, `others` |
| `holder_type` | `/v2/filings/` (IDX) | `insider`, `institution`, `corporate-investor` |
| `holder_type` | `/v2/sgx/filings/` | `insider`, `institution` |

> `extension` changes which *other* filter parameters are valid on `/v2/news/` — each
> extension has its own set. Don't carry IDX filters over to `extension=mining`.

### Indices

`index_code` on `/v2/index-daily/{index_code}/` carries **no JSON-schema enum**, and the
parameter description gives only `lq45`, `ihsg`, `idx30` as examples — which is why an earlier
draft of this page called the valid set undocumented. It is not. The endpoint's own description
carries an **`<Accordion title="Available index codes">` listing all 17**:

| Code | Index | Confirmed by |
| --- | --- | --- |
| `ihsg` | Jakarta Composite (IDX Total) | spec · product page |
| `lq45` | LQ45 — 45 most liquid | spec · product page · CSV |
| `idx30` | IDX30 | spec · product page · CSV |
| `kompas100` | KOMPAS100 | spec · product page · CSV |
| `jii70` | Jakarta Islamic Index 70 | spec · product page · CSV |
| `idxbumn20` | IDX BUMN20 — state-owned enterprises | spec · product page · CSV |
| `srikehati` | SRI-KEHATI — sustainability index | spec · product page · CSV |
| `idxesgl` | IDX ESG Leaders | spec · product page · CSV |
| `idxhidiv20` | IDX High Dividend 20 | spec · CSV |
| `idxq30` | IDX Quality 30 | spec · CSV |
| `idxg30` | IDX Growth 30 | spec · CSV |
| `idxv30` | IDX Value 30 | spec · CSV |
| `economic30` | IDX Economic 30 | spec · CSV |
| `ftse` | FTSE Indonesia | spec · CSV |
| `sminfra18` | SMinfra18 — infrastructure | spec · CSV |
| `idxvesta28` | IDX Vesta 28 | spec · CSV |
| `sti` | Straits Times Index (Singapore) | spec |

Three independent sources agree: the spec accordion (all 17), the product's own
`sectors.app/indonesia/index/<code>` pages (8), and the public
[`supertypeai/sectors_indices_company_list`](https://github.com/supertypeai/sectors_indices_company_list)
repository, which publishes a constituent CSV per index for 15 of them. **`idxv30`,
`sminfra18`, `sti` and `idxvesta28` appear in no product page** — the spec is the only place
they are listed, and an earlier draft of this dossier missed all four.

Note `sti` is Singapore's index on an otherwise IDX-only endpoint; treat it as unverified
until a live call confirms it resolves. Codes are lower-case in the spec, though the `indices`
array inside company reports renders them upper-case (`LQ45`, `IDX30`).

### Mining — commodity types

The valid set **differs per endpoint**. This is the single most error-prone area of the API.

| Endpoint | Valid `commodity_type` |
| --- | --- |
| `/v2/mining/companies/` | Aluminium, Coal, Copper, Gold, Nickel, Silver, Zinc and Lead |
| `/v2/mining/companies/performance/{slug}/` | Coal, Copper, Gold, Nickel, Silver |
| `/v2/mining/exports/` | Coal, Copper, Gold |
| `/v2/mining/global-commodity/` | Bauxite, Coal, Copper, Gold, Nickel |
| `/v2/mining/license-auctions/`, `/v2/mining/sites/` | Coal, Copper, Gold, Nickel |
| `/v2/mining/licenses/` | Bauxite, Clay, Coal, Copper, Gold, Granite, Iron, Limestone, Nickel, Non-Metallic Mineral, Others, Sand, "Sand, Stone, Gravel", Tin |
| `/v2/mining/resources-reserves/{province}/` | Coal, Cobalt, Copper, Gold, Nickel, Silver, Tin |
| `/v2/news/?extension=mining` | Bauxite, Coal, Copper, Gold, Iron, Nickel, Non-Metallic Mineral, Sand, "Sand, Stone, Gravel", Tin |

Values are **title-case with spaces**, not kebab-case slugs — unlike the equity taxonomy.
Note `Zinc and Lead` and `Sand, Stone, Gravel` are single values containing spaces and a comma.

### Mining — other enums

| Parameter | Endpoint | Values |
| --- | --- | --- |
| `company_type` | `/v2/mining/companies/` | `Consultant`, `Contractor`, `Holding`, `Manufacturer`, `Mine Owner`, `Trader` |
| `license_type` | `/v2/mining/licenses/` | `IPR`, `IUP`, `IUPK`, `KK`, `PKP2B`, `SIPB` |
| `activity` | `/v2/mining/licenses/` | `Eksplorasi`, `Operasi Produksi` (Indonesian, not translated) |
| `area_type` | `/v2/mining/license-auctions/` | `WIUP`, `WIUPK` |
| `order_by` | `/v2/mining/licenses/` | `commodity_type`, `license_effective_date`, `license_expiry_date`, `licensed_area_ha` (each with a `-` descending variant) |
| `order_by` | `/v2/mining/license-auctions/` | `commodity_type`, `licensed_area_ha`, `participant_count`, `winner_date` (± `-`) |
| `order_by` | `/v2/mining/sites/` | `production_volume`, `strip_ratio`, `year` (± `-`) |

### Mining — provinces

Also endpoint-specific, because coverage differs:

- **`/v2/mining/licenses/`** — 37 values, effectively all Indonesian provinces including the new Papuan ones (Papua Barat Daya, Papua Tengah).
- **`/v2/mining/resources-reserves/{province}/`** — 33 provinces.
- **`/v2/mining/sites/`** — 22 provinces (only those with recorded sites).
- **`/v2/mining/license-auctions/`** — 8 provinces only: Bengkulu, Gorontalo, Kalimantan Tengah, Maluku Utara, Nusa Tenggara Barat, Sulawesi Selatan, Sulawesi Utara, Sumatera Selatan.

Indonesian spellings, title case: `Kalimantan Timur`, not `East Kalimantan`.

> If you're building the mining-licence idea from
> [`../04-build-plan/what-we-can-build.md`](../04-build-plan/what-we-can-build.md), that
> 8-province auction list is your actual scope. Design around it rather than discovering it
> two days before the deadline.

---

## Rate limits

**The API is rate limited, but the limit is not published numerically.** What the docs do say:

- Exceeding it returns **429 Too Many Requests** (which is **free** — 429s are not billed).
- The official banking-benchmark recipe puts `sleep(0.3)` between sequential calls and states
  plainly that it "is not optional if you expand the universe beyond 10 banks. Omitting it on
  the free/Insider tier will result in 429 Too Many Requests errors."

So the documented guidance is the **0.3 s sleep**; **~3 requests/second is what that implies**,
not a published rate. For anything that loops
over tickers, insert the sleep and add exponential backoff on 429. Since 429s cost nothing,
retrying is free — but a tight loop that trips the limit repeatedly will still stall your job.

```python
import time

for symbol in symbols:
    fetch(symbol)
    time.sleep(0.3)   # documented as not optional beyond ~10 sequential calls
```

---

## Quick validation snippet

Fetch the taxonomy once, cache it forever, and validate before you spend credits on a 404
(remember: **404s are billed, 400s are not**).

```python
import json
import os
from pathlib import Path

import requests

CACHE = Path(".cache/taxonomy.json")
HEADERS = {"Authorization": os.environ["SECTORS_API_KEY"]}
BASE = "https://api.sectors.app/v2"


def taxonomy():
    """Four helper endpoints, 4 credits, once for the whole project."""
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    data = {
        name: requests.get(f"{BASE}/{name}/", headers=HEADERS, timeout=30).json()
        for name in ("subsectors", "industries", "subindustries", "tags")
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data))
    return data
```
