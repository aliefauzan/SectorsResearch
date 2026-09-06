# Live capture evidence — 6 September 2026

Machine-generated from `harness/recorded/_ledger.jsonl` and `_rate_probe.jsonl`.
Every row is one attempt against `https://api.sectors.app`. No value here is hand-typed.

## Totals

- capture attempts: 168
  - HTTP 200: 129
  - HTTP 400: 20
  - HTTP 403: 6
  - HTTP 404: 10
  - HTTP 405: 1
  - HTTP 429: 2
- credits billed by the capture (sum of ledger `billed_cost`): **265**
- rate-limit probe attempts: 140
  - HTTP 200: 84
  - HTTP 400: 45
  - HTTP 429: 11
- credits billed by the probe (200s): **84** logged, plus 28 in the window-gating proof = **112**
- **total credits billed: 377**
- payloads on disk: 128
- responses carrying any credit/quota/rate-limit header: **0**

## Rate-limit bisect

| run | spacing | sent | 200 | 429 | first 429 at |
| --- | --- | --- | --- | --- | --- |
| phase0 | 0.0 | 45 | 0 | 0 | — |
| confirm | 0.0 | 27 | 25 | 2 | 25 |
| recovery | poll | 9 | 2 | 7 | 0 |
| sustained-1.0 | 1.0 | 27 | 25 | 2 | 25 |
| sustained-1.5 | 1.5 | 32 | 32 | 0 | — |

No response in the entire probe carried a `Retry-After` header.

## Every capture attempt, in order

| # | method | path | params | status | billed |
| --- | --- | --- | --- | --- | --- |
| 1 | GET | `/v2/subsectors/` |  | 403 | 0 |
| 2 | GET | `/v2/industries/` |  | 403 | 0 |
| 3 | GET | `/v2/subindustries/` |  | 403 | 0 |
| 4 | GET | `/v2/tags/` |  | 403 | 0 |
| 5 | GET | `/v2/brokers/` |  | 403 | 0 |
| 6 | GET | `/v2/subsectors/` |  | 200 | 1 |
| 7 | GET | `/v2/industries/` |  | 200 | 1 |
| 8 | GET | `/v2/subindustries/` |  | 200 | 1 |
| 9 | GET | `/v2/tags/` |  | 200 | 1 |
| 10 | GET | `/v2/brokers/` |  | 200 | 1 |
| 11 | GET | `/v2/companies/` | `{"limit": 200, "order_by": "-market_cap", "where": "market_cap > 1000000000000"}` | 200 | 1 |
| 12 | GET | `/v2/companies/` | `{"limit": 200, "order_by": "-market_cap", "where": "sub_sector = 'banks'"}` | 200 | 1 |
| 13 | GET | `/v2/companies/` | `{"limit": 200, "order_by": "-yield_ttm", "where": "yield_ttm > 0.03 and payout_ratio < 0.9"}` | 200 | 1 |
| 14 | GET | `/v2/idx-total/` |  | 200 | 1 |
| 15 | GET | `/v2/companies/top-changes/` | `{"classifications": "top_gainers", "min_mcap_billion": 0, "periods": "1d"}` | 200 | 1 |
| 16 | GET | `/v2/companies/top-changes/` | `{"classifications": "top_losers", "min_mcap_billion": 0, "periods": "1d"}` | 200 | 1 |
| 17 | GET | `/v2/news/` | `{"extension": "idx"}` | 200 | 1 |
| 18 | GET | `/v2/filings/` |  | 200 | 1 |
| 19 | GET | `/v2/suspensions/` |  | 200 | 1 |
| 20 | GET | `/v2/index-daily/ihsg/` |  | 200 | 1 |
| 21 | GET | `/v2/index-daily/lq45/` |  | 200 | 1 |
| 22 | GET | `/v2/index-daily/idx30/` |  | 200 | 1 |
| 23 | GET | `/v2/company/report/BBCA/` | `{"sections": "overview"}` | 200 | 1 |
| 24 | GET | `/v2/daily/BBCA/` |  | 200 | 1 |
| 25 | GET | `/v2/company/report/BBRI/` | `{"sections": "overview"}` | 200 | 1 |
| 26 | GET | `/v2/daily/BBRI/` |  | 200 | 1 |
| 27 | GET | `/v2/company/report/BMRI/` | `{"sections": "overview"}` | 200 | 1 |
| 28 | GET | `/v2/daily/BMRI/` |  | 200 | 1 |
| 29 | GET | `/v2/company/report/TLKM/` | `{"sections": "overview"}` | 200 | 1 |
| 30 | GET | `/v2/daily/TLKM/` |  | 200 | 1 |
| 31 | GET | `/v2/company/report/ASII/` | `{"sections": "overview"}` | 200 | 1 |
| 32 | GET | `/v2/daily/ASII/` |  | 200 | 1 |
| 33 | GET | `/v2/company/report/ADRO/` | `{"sections": "overview"}` | 200 | 1 |
| 34 | GET | `/v2/daily/ADRO/` |  | 200 | 1 |
| 35 | GET | `/v2/company/report/BREN/` | `{"sections": "overview"}` | 200 | 1 |
| 36 | GET | `/v2/daily/BREN/` |  | 200 | 1 |
| 37 | GET | `/v2/company/report/ANTM/` | `{"sections": "overview"}` | 200 | 1 |
| 38 | GET | `/v2/daily/ANTM/` |  | 200 | 1 |
| 39 | GET | `/v2/foreign-flow/BBCA/` |  | 200 | 1 |
| 40 | GET | `/v2/foreign-flow/BBRI/` |  | 200 | 1 |
| 41 | GET | `/v2/foreign-flow/BMRI/` |  | 200 | 1 |
| 42 | GET | `/v2/foreign-flow/TLKM/` |  | 200 | 1 |
| 43 | GET | `/v2/foreign-flow/ASII/` |  | 200 | 1 |
| 44 | GET | `/v2/foreign-flow/ADRO/` |  | 200 | 1 |
| 45 | GET | `/v2/foreign-flow/BREN/` |  | 200 | 1 |
| 46 | GET | `/v2/foreign-flow/ANTM/` |  | 200 | 1 |
| 47 | GET | `/v2/broker-summary/BBCA/top/` |  | 200 | 2 |
| 48 | GET | `/v2/financials/quarterly/BBCA/` | `{"n_quarters": 4}` | 200 | 4 |
| 49 | GET | `/v2/company/get-segments/BBCA/` |  | 200 | 1 |
| 50 | GET | `/v2/company/corporate-actions/BBCA/` |  | 200 | 1 |
| 51 | GET | `/v2/company/shareholders-composition/BBCA/` |  | 200 | 1 |
| 52 | GET | `/v2/listing-performance/BBCA/` |  | 404 | 1 |
| 53 | GET | `/v2/broker-summary/BBRI/top/` |  | 200 | 2 |
| 54 | GET | `/v2/financials/quarterly/BBRI/` | `{"n_quarters": 4}` | 200 | 4 |
| 55 | GET | `/v2/company/get-segments/BBRI/` |  | 200 | 1 |
| 56 | GET | `/v2/company/corporate-actions/BBRI/` |  | 200 | 1 |
| 57 | GET | `/v2/company/shareholders-composition/BBRI/` |  | 200 | 1 |
| 58 | GET | `/v2/listing-performance/BBRI/` |  | 404 | 1 |
| 59 | GET | `/v2/broker-summary/TLKM/top/` |  | 200 | 2 |
| 60 | GET | `/v2/financials/quarterly/TLKM/` | `{"n_quarters": 4}` | 200 | 4 |
| 61 | GET | `/v2/company/get-segments/TLKM/` |  | 200 | 1 |
| 62 | GET | `/v2/company/corporate-actions/TLKM/` |  | 200 | 1 |
| 63 | GET | `/v2/company/shareholders-composition/TLKM/` |  | 200 | 1 |
| 64 | GET | `/v2/listing-performance/TLKM/` |  | 404 | 1 |
| 65 | GET | `/v2/broker-summary/ADRO/top/` |  | 200 | 2 |
| 66 | GET | `/v2/financials/quarterly/ADRO/` | `{"n_quarters": 4}` | 200 | 4 |
| 67 | GET | `/v2/company/get-segments/ADRO/` |  | 200 | 1 |
| 68 | GET | `/v2/company/corporate-actions/ADRO/` |  | 200 | 1 |
| 69 | GET | `/v2/company/shareholders-composition/ADRO/` |  | 200 | 1 |
| 70 | GET | `/v2/listing-performance/ADRO/` |  | 404 | 1 |
| 71 | GET | `/v2/brokers/top/` | `{"metric": "net"}` | 200 | 2 |
| 72 | GET | `/v2/most-traded/` |  | 200 | 2 |
| 73 | GET | `/v2/subsector/report/banks/` | `{"sections": "statistics"}` | 200 | 1 |
| 74 | GET | `/v2/subsector/report/oil-gas-coal/` | `{"sections": "statistics"}` | 200 | 1 |
| 75 | GET | `/v2/subsector/report/telecommunication/` | `{"sections": "statistics"}` | 200 | 1 |
| 76 | GET | `/v2/mining/commodities/` |  | 200 | 1 |
| 77 | GET | `/v2/mining/companies/` |  | 200 | 1 |
| 78 | GET | `/v2/mining/sites/` |  | 200 | 1 |
| 79 | GET | `/v2/mining/licenses/` |  | 200 | 1 |
| 80 | GET | `/v2/mining/license-auctions/` |  | 200 | 1 |
| 81 | GET | `/v2/mining/total-production/` |  | 400 | 0 |
| 82 | GET | `/v2/mining/resources-reserves/` |  | 200 | 1 |
| 83 | GET | `/v2/mining/exports/` |  | 400 | 0 |
| 84 | GET | `/v2/mining/contracts/` |  | 200 | 1 |
| 85 | GET | `/v2/mining/commodities/Gold/price/` | `{"end_year": 2025, "start_year": 2023}` | 200 | 1 |
| 86 | GET | `/v2/mining/commodities/Coal/price/` | `{"end_year": 2025, "start_year": 2023}` | 200 | 1 |
| 87 | GET | `/v2/sgx/sectors/` |  | 200 | 1 |
| 88 | GET | `/v2/sgx/companies/` | `{"limit": 100, "order_by": "-market_cap"}` | 200 | 1 |
| 89 | GET | `/v2/klse/sectors/` |  | 200 | 1 |
| 90 | GET | `/v2/free-float/` |  | 200 | 10 |
| 91 | GET | `/v2/close/` | `{"limit": 30}` | 429 | 25 |
| 92 | GET | `/v2/companies/quarterly-financial-dates/` | `{"limit": 30}` | 429 | 31 |
| 93 | GET | `/v2/close/` | `{"limit": 30}` | 200 | 7 |
| 94 | GET | `/v2/companies/quarterly-financial-dates/` | `{"limit": 30}` | 200 | 1 |
| 95 | GET | `/v2/companies/list_companies_with_segments/` |  | 200 | 1 |
| 96 | GET | `/v2/sgx/subsectors/` |  | 200 | 1 |
| 97 | GET | `/v2/sgx/tags/` |  | 200 | 1 |
| 98 | GET | `/v2/mining/global-commodity/` | `{"commodity_type": "Coal", "limit": 20}` | 200 | 1 |
| 99 | GET | `/v2/mining/total-production/` | `{"commodity_type": "Coal"}` | 200 | 1 |
| 100 | GET | `/v2/mining/exports/` | `{"commodity_type": "Coal", "year": 2024}` | 200 | 1 |
| 101 | GET | `/v2/company/get_quarterly_financial_dates/BBCA/` |  | 200 | 1 |
| 102 | GET | `/v2/company/report/` | `{"sections": "overview", "symbol": "BBCA"}` | 400 | 0 |
| 103 | GET | `/v2/subsector/report/` | `{"sections": "overview", "sub_sector": "banks"}` | 400 | 0 |
| 104 | GET | `/v2/broker-activity/AD/` | `{"end": "2026-08-14", "start": "2026-08-01"}` | 200 | 1 |
| 105 | GET | `/v2/broker-activity/AD/top/` | `{"end": "2026-08-14", "start": "2026-08-01"}` | 200 | 1 |
| 106 | GET | `/v2/broker-summary/BBCA/` | `{"end": "2026-08-14", "start": "2026-08-01"}` | 200 | 1 |
| 107 | GET | `/v2/mining/companies/pt-adaro-indonesia/` |  | 200 | 1 |
| 108 | GET | `/v2/mining/companies/financials/pt-adaro-indonesia/` |  | 404 | 1 |
| 109 | GET | `/v2/mining/companies/ownership/pt-adaro-indonesia/` |  | 200 | 1 |
| 110 | GET | `/v2/mining/companies/performance/pt-adaro-indonesia/` | `{"commodity_type": "Coal"}` | 200 | 1 |
| 111 | GET | `/v2/mining/sales-destination/pt-adaro-indonesia/` |  | 404 | 1 |
| 112 | GET | `/v2/mining/sites/tutupan-utara/` |  | 200 | 1 |
| 113 | GET | `/v2/mining/license-auctions/1473242122023001/` |  | 200 | 1 |
| 114 | GET | `/v2/mining/resources-reserves/Aceh/` | `{"commodity_type": "Coal"}` | 200 | 1 |
| 115 | GET | `/v2/sgx/companies/top/` | `{"classifications": "top_gainers", "n_stock": 5}` | 400 | 0 |
| 116 | GET | `/v2/sgx/filings/` | `{"limit": 20}` | 200 | 1 |
| 117 | GET | `/v2/sgx/news/` | `{"limit": 20}` | 200 | 1 |
| 118 | GET | `/v2/sgx/buybacks/` | `{"limit": 20}` | 200 | 1 |
| 119 | GET | `/v2/sgx/short-sell/` | `{"limit": 20}` | 200 | 1 |
| 120 | GET | `/v2/sgx/company/report/` | `{"sections": "overview", "symbol": "D05.SI"}` | 400 | 0 |
| 121 | GET | `/v2/sgx/company/report/D05.SI/` | `{"sections": "overview"}` | 200 | 1 |
| 122 | GET | `/v2/sgx/daily/D05.SI/` | `{"end": "2026-08-14", "start": "2026-08-01"}` | 200 | 1 |
| 123 | GET | `/v2/klse/companies/` | `{"sector": "consumer-non-cyclicals"}` | 200 | 1 |
| 124 | GET | `/v2/klse/companies/top/` | `{"classifications": "top_gainers", "n_stock": 5}` | 400 | 0 |
| 125 | GET | `/v2/mining/companies/pt-abm-investama-tbk/` |  | 200 | 1 |
| 126 | GET | `/v2/mining/companies/financials/pt-abm-investama-tbk/` |  | 404 | 1 |
| 127 | GET | `/v2/mining/companies/ownership/pt-abm-investama-tbk/` |  | 200 | 1 |
| 128 | GET | `/v2/mining/companies/performance/pt-abm-investama-tbk/` | `{"commodity_type": "Coal"}` | 404 | 1 |
| 129 | GET | `/v2/mining/sales-destination/pt-abm-investama-tbk/` |  | 404 | 1 |
| 130 | GET | `/v2/sgx/companies/top/` | `{"classifications": "market_cap", "n_stock": 5}` | 200 | 1 |
| 131 | GET | `/v2/klse/companies/top/` | `{"classifications": "market_cap", "n_stock": 5}` | 200 | 1 |
| 132 | GET | `/v2/klse/company/report/2089/` | `{"sections": "overview"}` | 200 | 1 |
| 133 | GET | `/v2/mining/companies/` | `{"has_financials": "true", "limit": 20}` | 200 | 1 |
| 134 | GET | `/v2/mining/companies/pt-adaro-andalan-indonesia-tbk/` |  | 200 | 1 |
| 135 | GET | `/v2/mining/companies/financials/pt-adaro-andalan-indonesia-tbk/` |  | 200 | 1 |
| 136 | GET | `/v2/mining/companies/ownership/pt-adaro-andalan-indonesia-tbk/` |  | 200 | 1 |
| 137 | GET | `/v2/mining/companies/performance/pt-adaro-andalan-indonesia-tbk/` | `{"commodity_type": "Coal"}` | 200 | 1 |
| 138 | GET | `/v2/mining/sales-destination/pt-adaro-andalan-indonesia-tbk/` |  | 200 | 1 |
| 139 | GET | `/v2/listing-performance/BREN/` |  | 200 | 1 |
| 140 | GET | `/v2/company/report/` | `{"symbol": "BBCA"}` | 400 | 0 |
| 141 | GET | `/v2/company/report/` | `{"symbols": "BBCA"}` | 400 | 0 |
| 142 | GET | `/v2/company/report/` | `{"ticker": "BBCA"}` | 400 | 0 |
| 143 | GET | `/v2/company/report/` | `{"stock": "BBCA"}` | 400 | 0 |
| 144 | GET | `/v2/company/report/` | `{"q": "BBCA"}` | 400 | 0 |
| 145 | GET | `/v2/company/report/` |  | 400 | 0 |
| 146 | GET | `/v2/subsector/report/` | `{"sub_sector": "banks"}` | 400 | 0 |
| 147 | GET | `/v2/subsector/report/` | `{"sector": "banks"}` | 400 | 0 |
| 148 | GET | `/v2/subsector/report/` | `{"subsector": "banks"}` | 400 | 0 |
| 149 | GET | `/v2/sgx/company/report/` | `{"symbol": "D05.SI"}` | 400 | 0 |
| 150 | GET | `/v2/klse/company/report/` | `{"symbol": "2089"}` | 400 | 0 |
| 151 | GET | `/v2/company/report/bbca/` | `{"sections": "overview"}` | 200 | 1 |
| 152 | GET | `/v2/company/report/BBCA.JK/` | `{"sections": "overview"}` | 200 | 1 |
| 153 | GET | `/v2/does-not-exist/` |  | 404 | 1 |
| 154 | GET | `/v2/index-daily/sti/` |  | 200 | 1 |
| 155 | GET | `/v2/index-daily/klse/` |  | 400 | 0 |
| 156 | GET | `/v2/subsectors` |  | 200 | 1 |
| 157 | GET | `/v2/subsectors/` |  | 405 | 0 |
| 158 | GET | `/v2/subsectors/` |  | 200 | 1 |
| 159 | GET | `/v2/index-daily/klse/` |  | 400 | 0 |
| 160 | GET | `/v2/company/report/BBCA/` |  | 200 | 8 |
| 161 | GET | `/v2/subsector/report/banks/` |  | 200 | 6 |
| 162 | GET | `/v2/companies/top-changes/` |  | 200 | 10 |
| 163 | GET | `/v2/sgx/company/report/D05.SI/` |  | 200 | 4 |
| 164 | GET | `/v2/klse/company/report/2089/` |  | 200 | 4 |
| 165 | GET | `/v2/sgx/companies/top/` |  | 200 | 5 |
| 166 | GET | `/v2/klse/companies/top/` |  | 200 | 5 |
| 167 | GET | `/v2/companies/` | `{"limit": 20, "q": "banks with return on equity above 15 percent"}` | 200 | 3 |
| 168 | GET | `/v2/subsectors/` |  | 403 | 0 |

## Failures, with the body the API returned

- `/v2/subsectors/`  **403**, billed 0 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/industries/`  **403**, billed 0 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/subindustries/`  **403**, billed 0 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/tags/`  **403**, billed 0 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/brokers/`  **403**, billed 0 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/listing-performance/BBCA/`  **404**, billed 1 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/listing-performance/BBRI/`  **404**, billed 1 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/listing-performance/TLKM/`  **404**, billed 1 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/listing-performance/ADRO/`  **404**, billed 1 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/mining/total-production/`  **400**, billed 0 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/mining/exports/`  **400**, billed 0 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/close/` {"limit": 30} **429**, billed 25 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/companies/quarterly-financial-dates/` {"limit": 30} **429**, billed 31 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/company/report/` {"symbol": "BBCA", "sections": "overview"} **400**, billed 0 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/subsector/report/` {"sub_sector": "banks", "sections": "overview"} **400**, billed 0 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/mining/companies/financials/pt-adaro-indonesia/`  **404**, billed 1 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/mining/sales-destination/pt-adaro-indonesia/`  **404**, billed 1 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/sgx/companies/top/` {"classifications": "top_gainers", "n_stock": 5} **400**, billed 0 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/sgx/company/report/` {"symbol": "D05.SI", "sections": "overview"} **400**, billed 0 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/klse/companies/top/` {"classifications": "top_gainers", "n_stock": 5} **400**, billed 0 — (not captured — the ledger only began storing bodies mid-run)
- `/v2/mining/companies/financials/pt-abm-investama-tbk/`  **404**, billed 1 — {"error": "Company not found or no financial data available."}
- `/v2/mining/companies/performance/pt-abm-investama-tbk/` {"commodity_type": "Coal"} **404**, billed 1 — {"error": "No performance data found."}
- `/v2/mining/sales-destination/pt-abm-investama-tbk/`  **404**, billed 1 — {"error": "No sales destination data found for company 'pt-abm-investama-tbk'."}
- `/v2/company/report/` {"symbol": "BBCA"} **400**, billed 0 — {"error": "Please provide a valid stock symbol."}
- `/v2/company/report/` {"symbols": "BBCA"} **400**, billed 0 — {"error": "Please provide a valid stock symbol."}
- `/v2/company/report/` {"ticker": "BBCA"} **400**, billed 0 — {"error": "Please provide a valid stock symbol."}
- `/v2/company/report/` {"stock": "BBCA"} **400**, billed 0 — {"error": "Please provide a valid stock symbol."}
- `/v2/company/report/` {"q": "BBCA"} **400**, billed 0 — {"error": "Please provide a valid stock symbol."}
- `/v2/company/report/`  **400**, billed 0 — {"error": "Please provide a valid stock symbol."}
- `/v2/subsector/report/` {"sub_sector": "banks"} **400**, billed 0 — {"error": "Please provide a valid sector."}
- `/v2/subsector/report/` {"sector": "banks"} **400**, billed 0 — {"error": "Please provide a valid sector."}
- `/v2/subsector/report/` {"subsector": "banks"} **400**, billed 0 — {"error": "Please provide a valid sector."}
- `/v2/sgx/company/report/` {"symbol": "D05.SI"} **400**, billed 0 — {"error": "Please provide a valid SGX symbol."}
- `/v2/klse/company/report/` {"symbol": "2089"} **400**, billed 0 — {"error": "Please provide a valid KLSE symbol."}
- `/v2/does-not-exist/`  **404**, billed 1 — {"details": "The requested endpoint does not exist", "urls": {"homepage": "https://sectors.app/", "API docs": "https://docs.sectors.app/"}}
- `/v2/index-daily/klse/`  **400**, billed 0 — {"error": "Please provide a valid index code."}
- `/v2/subsectors/`  **405**, billed 0 — {"error": "Method \"POST\" not allowed."}
- `/v2/index-daily/klse/`  **400**, billed 0 — {"error": "Please provide a valid index code."}
- `/v2/subsectors/`  **403**, billed 0 — {"error": "Authentication credentials were not provided."}
