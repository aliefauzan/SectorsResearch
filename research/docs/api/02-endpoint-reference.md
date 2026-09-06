# Sectors Financial API — Complete Endpoint Reference (v2)

> Generated from the official OpenAPI 3.0.3 spec at `https://docs.sectors.app/schema.json`
> (`info.version` = 2.0.0). Raw copy kept at [`evidence/spec/schema.json`](../../evidence/spec/schema.json).

**Base URL:** `https://api.sectors.app`
**Auth:** `Authorization: <YOUR_API_KEY>` header (raw key, *no* `Bearer` prefix for the REST API).

The key comes from the git-ignored `.env` at the repository root — `from sectors_env import api_key` — never from a literal in code. See [`SETUP.md`](../../../SETUP.md).

**Method:** every endpoint is `GET`.
**Endpoint count:** 70

Legend for the Params column: `name` = optional, **`name`** = required.

---

## Indonesia (IDX)

### Company Screener

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/companies/` | Companies Screener | 1 API credit for structured queries | where, q, order_by, desc, limit, offset, include_query_values |
| `/v2/free-float/` | Free Float Market Analysis | 1 API credit per 100 companies returned, rounded up | sector, sub_sector, industry, sub_industry |

### Helper Lists

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/companies/list_companies_with_segments/` | Companies with Revenue Segments | 1 API credit | — |
| `/v2/companies/quarterly-financial-dates/` | Latest Quarterly Financial Dates (Universe) | 1 API credit per page | year, limit, offset, since |
| `/v2/company/get_quarterly_financial_dates/{symbol}/` | Quarterly Financial Dates | 1 API credit | **symbol** |
| `/v2/industries/` | Industries | 1 API credit | — |
| `/v2/subindustries/` | Subindustries | 1 API credit | — |
| `/v2/subsectors/` | Subsectors | 1 API credit | — |
| `/v2/tags/` | News Tags | 1 API credit | — |

### Detailed Reports

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/company/corporate-actions/{symbol}/` | Corporate Actions | 1 API credit | **symbol** |
| `/v2/company/get-segments/{symbol}/` | Company Revenue Segments | 1 API credit | **symbol**, financial_year |
| `/v2/company/report/` | Company Report | 1 API credit per requested section | **symbol**, sections |
| `/v2/company/report/{symbol}/` | Company Report | 1 API credit per requested section | **symbol**, sections |
| `/v2/company/shareholders-composition/{symbol}/` | Shareholders Composition | 1 API credit | **symbol**, year |
| `/v2/financials/quarterly/{symbol}/` | Company Quarterly Financials | 1 API credit per quarter returned | **symbol**, report_date, approx, n_quarters |
| `/v2/subsector/report/` | Subsector Report | 1 API credit per requested section | **sub_sector**, sections |
| `/v2/subsector/report/{sub_sector}/` | Subsector Report | 1 API credit per requested section | **sub_sector**, sections |

### Transaction Data

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/close/` | Daily Full-Universe Close | 1 API credit per page | limit, offset, date |
| `/v2/daily/{symbol}/` | Daily Transaction Data | 1 API credit | **symbol**, start, end |
| `/v2/idx-total/` | IDX Market Summary | 1 API credit | start, end |
| `/v2/index-daily/{index_code}/` | Index Daily Transaction Data | 1 API credit | **index_code**, start, end |

### Rankings

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/companies/top-changes/` | Top Company Movers | 1 API credit per requested classification × period combination | sub_sector, n_stock, classifications, periods, min_mcap_billion |
| `/v2/most-traded/` | Most Traded Stocks | 2 API credits | sub_sector, start, end, adjusted, n_stock |

### IPO & Performance

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/listing-performance/{symbol}/` | Company IPO & Listing Performance | 1 API credit | **symbol** |

### News & Filings

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/filings/` | Company Filings | 1 API credit | symbol, sector, sub_sector, start, end, limit, offset, transaction_type, tags, holder_type |
| `/v2/news/` | News Articles | 1 API credit | sector, sub_sector, commodity_type, start, end, limit, offset, tags, extension, keyword, symbols |
| `/v2/suspensions/` | Stock Suspensions | 1 API credit | symbol, start, end, limit, offset |

### Brokers

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/broker-activity/{broker_code}/` | Broker Activity By Code | 1 API credit | **broker_code**, symbol, start, end |
| `/v2/broker-activity/{broker_code}/top/` | Top Accumulations and Distributions Per Broker | 2 API credits | **broker_code**, start, end, n_brokers |
| `/v2/broker-summary/{symbol}/` | Broker Activity Per Symbol | 1 API credit | **symbol**, broker_code, start, end |
| `/v2/broker-summary/{symbol}/top/` | Top Buyers and Sellers Per Symbol | 2 API credits | **symbol**, start, end, cohort, n_brokers, origin |
| `/v2/brokers/` | Broker Registry | 1 API credit | cohort, origin |
| `/v2/brokers/top/` | Top Brokers Daily Ranking | 2 API credits | cohort, date, metric, n_brokers, origin |
| `/v2/foreign-flow/{symbol}/` | Daily Net Foreign Inflow | 1 API credit | **symbol**, start, end |

## Singapore (SGX)

### SGX - Company Screener

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/sgx/companies/` | SGX Companies Screener | 1 API credit for structured queries | where, q, order_by, desc, limit, offset, include_query_values |

### SGX - Helper Lists

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/sgx/sectors/` | List all SGX sectors | 1 API credit | — |
| `/v2/sgx/subsectors/` | SGX Subsectors | 1 API credit | — |
| `/v2/sgx/tags/` | SGX News Tags | 1 API credit | — |

### SGX - Detailed Reports

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/sgx/company/report/` | Full company report for an SGX-listed symbol | 1 API credit per requested section | **symbol**, sections |
| `/v2/sgx/company/report/{symbol}/` | Full company report for an SGX-listed symbol | 1 API credit per requested section | **symbol**, sections |

### SGX - Transaction Data

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/sgx/buybacks/` | SGX Share Buybacks | 1 API credit | symbol, start, end, limit, offset |
| `/v2/sgx/daily/{symbol}/` | SGX Daily Price Data | 1 API credit | **symbol**, start, end |
| `/v2/sgx/short-sell/` | SGX Short Sell | 1 API credit | symbol, start, end, limit, offset |

### SGX - Rankings

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/sgx/companies/top/` | Top SGX companies by classification | 1 API credit per requested classification | sector, n_stock, classifications, min_mcap_million |

### SGX - News & Filings

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/sgx/filings/` | SGX Insider Filings | 1 API credit | symbol, start, end, limit, offset, transaction_type, holder_type |
| `/v2/sgx/news/` | SGX News | 1 API credit | sector, sub_sector, start, end, limit, offset, tags, symbols |

## Malaysia (KLSE)

### KLSE

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/klse/companies/` | List KLSE companies filtered by sector | 1 API credit | **sector** |
| `/v2/klse/companies/top/` | Top KLSE companies by classification | 1 API credit per requested classification | sector, n_stock, classifications, min_mcap_million |
| `/v2/klse/company/report/` | Full company report for a KLSE-listed symbol | 1 API credit per requested section | **symbol**, sections |
| `/v2/klse/company/report/{symbol}/` | Full company report for a KLSE-listed symbol | 1 API credit per requested section | **symbol**, sections |
| `/v2/klse/sectors/` | List all KLSE sectors | 1 API credit | — |

## Mining extension (Indonesia)

### Companies

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/mining/companies/` | List Mining Companies | 1 API credit | commodity_type, limit, offset, keyword, company_type, has_financials |
| `/v2/mining/companies/financials/{slug}/` | Mining Company Financials | 1 API credit | **slug**, year |
| `/v2/mining/companies/ownership/{slug}/` | Mining Company Ownership | 1 API credit | **slug** |
| `/v2/mining/companies/performance/{slug}/` | Mining Company Performance | 1 API credit | **slug**, commodity_type, year |
| `/v2/mining/companies/{slug}/` | Mining Company Detail | 1 API credit | **slug** |

### Commodities & Trade

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/mining/commodities/` | List Commodities | 1 API credit | — |
| `/v2/mining/commodities/{commodity_name}/price/` | Commodity Price History | 1 API credit | **commodity_name**, start_year, end_year |
| `/v2/mining/exports/` | Top Export Destinations | 1 API credit | **commodity_type**, **year**, limit |
| `/v2/mining/global-commodity/` | Global Commodity Data | 1 API credit | commodity_type, country, limit |
| `/v2/mining/sales-destination/{slug}/` | Company Sales Destinations | 1 API credit | **slug**, year |

### Production & Sites

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/mining/resources-reserves/` | Resources & Reserves Index | 1 API credit | — |
| `/v2/mining/resources-reserves/{province}/` | Resources & Reserves Detail | 1 API credit | **province**, commodity_type, year |
| `/v2/mining/sites/` | Mining Sites | 1 API credit | province, commodity_type, company, year, order_by, min_production, limit, offset |
| `/v2/mining/sites/{slug}/` | Mining Site Detail | 1 API credit | **slug** |
| `/v2/mining/total-production/` | Total Commodity Production | 1 API credit | **commodity_type** |

### Contracts & Licenses

| Endpoint | What it returns | Credit cost | Params |
| --- | --- | --- | --- |
| `/v2/mining/contracts/` | Mining Contracts | 1 API credit | contractor, mine_owner |
| `/v2/mining/license-auctions/` | Mining License Auctions | 1 API credit | province, commodity_type, order_by, limit, offset, area_type, status, participant, qualified, min_participants |
| `/v2/mining/license-auctions/{wiup_code}/` | Mining License Auction Detail | 1 API credit | **wiup_code** |
| `/v2/mining/licenses/` | Mining Licenses | 1 API credit | province, commodity_type, company, order_by, limit, offset, expiring_soon, license_type, activity, cnc |

---

## Per-endpoint detail

### `GET /v2/companies/`

**Companies Screener** — Company Screener

High-performance API for filtering and sorting IDX-listed companies. Supports both structured SQL-like queries (`where`, `order_by`) and natural language queries (`q`). Returns a paginated list of companies. **Query modes** (mutually exclusive — `q` overrides all others): - `q`: Natural language, e.g. `top 10 tech companies by revenue in 2023` - `where` + `order_by`: SQL-like structured query For the most precise natural language results, filter by sector/industry slugs. Retrieve the complete slug list from the Subsectors, Industries, or Subindustries endpoints. To account for reporting lags, 'latest year' queries made between January and April default to the previous audited year (e.g. a qu…

- **Credit cost:** 1 API credit for structured queries
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `where` | query | string | no | SQL-like conditions for advanced filtering. Ignored if `q` is present. Supports operators `=`, `!=`, `>`, `>=`, ` 100000… |
  | `q` | query | string | no | A natural language query (e.g. `top 10 tech companies by revenue in 2023`). When `q` is provided, all other query parame… |
  | `order_by` | query | string | no | Field to sort results by. Use `-` prefix for descending order (e.g. `-market_cap`). Supports arithmetic expressions (e.g… |
  | `desc` | query | boolean | no | Sort in descending order. Ignored if `q` is present. |
  | `limit` | query | integer | no | Maximum number of results to return. Max: 200. Ignored if `q` is present. |
  | `offset` | query | integer | no | Number of results to skip for pagination. Ignored if `q` is present. |
  | `include_query_values` | query | boolean | no | If `true`, the response includes a `query_values` object showing the interpreted year and country extracted from the que… |

### `GET /v2/free-float/`

**Free Float Market Analysis** — Company Screener

Returns the free float percentage for IDX-listed companies, optionally filtered by one level of the sector taxonomy. Results are ordered by `free_float` descending. Free float is calculated as the `share_percentage` of the **Public** entry in a company's major shareholders list. Query parameters are **mutually exclusive**. Provide at most one filter parameter per request. Costs 1 API credit per 100 companies returned, rounded up.

- **Credit cost:** 1 API credit per 100 companies returned, rounded up
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `sector` | query | string | no | Kebab-case sector slug. E.g. `infrastructures`, `healthcare`, `transportation-logistic`. Retrieve valid values from the … |
  | `sub_sector` | query | string | no | Kebab-case subsector slug. E.g. `banks`, `basic-materials`, `food-beverage`. Retrieve valid values from the Subsectors e… |
  | `industry` | query | string | no | Kebab-case industry slug. E.g. `oil-gas`, `electrical`, `chemicals`. Retrieve valid values from the Industries endpoint. |
  | `sub_industry` | query | string | no | Kebab-case sub-industry slug. E.g. `coal-production`, `gold`, `healthcare-providers`. Retrieve valid values from the Sub… |

### `GET /v2/companies/list_companies_with_segments/`

**Companies with Revenue Segments** — Helper Lists

Returns a dictionary of all companies that have revenue and cost segment data available, along with their available financial years. **Used by:** Company Revenue and Cost Segments Costs 1 API credit.

- **Credit cost:** 1 API credit

### `GET /v2/companies/quarterly-financial-dates/`

**Latest Quarterly Financial Dates (Universe)** — Helper Lists

Returns the **latest** available quarterly report date (and its quarter label) for **every** IDX company in one paginated feed — instead of calling the per-symbol Quarterly Financial Dates helper once per ticker. Built for **freshness polling**: store the dates you've seen, then re-poll with `?since=` to fetch only the companies that have since reported a new quarter, keeping repeat polls cheap. **Related:** Quarterly Financials for the actual figures on a given `report_date`. One row per company (~950), sorted by symbol. Companies with no quarterly data are omitted. Costs 1 API credit per page. The full universe is ~32 pages at the maximum `limit` of 30 (~32 credits per full sweep). Use `si…

- **Credit cost:** 1 API credit per page
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `year` | query | integer | no | Restrict to report dates within this calendar year, then return each company's latest quarter within it (e.g. `2024`). |
  | `limit` | query | integer | no | Maximum number of companies to return per page. Max: 30. |
  | `offset` | query | integer | no | Number of companies to skip for pagination. |
  | `since` | query | string | no | Return only companies whose latest quarter-end date is on or after this date (`YYYY-MM-DD`). Use it to poll for newly-re… |

### `GET /v2/company/get_quarterly_financial_dates/{symbol}/`

**Quarterly Financial Dates** — Helper Lists

Returns all available quarterly financial report dates for a given symbol, grouped by year. Use the `report_date` values returned here as inputs to the `report_date` parameter in the Quarterly Financials endpoint. **Used by:** Company Quarterly Financials IDX symbol: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `ASII`, `BBCA`, `BMRI`. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | IDX symbol symbol. E.g. `ASII`, `BBCA`. |

### `GET /v2/industries/`

**Industries** — Helper Lists

Returns all available subsector/industry pairs as kebab-case slugs. Use these values as inputs to the `industry` parameter. **Used by:** Companies Screener, Free Float Market Analysis Costs 1 API credit.

- **Credit cost:** 1 API credit

### `GET /v2/subindustries/`

**Subindustries** — Helper Lists

Returns all available industry/sub-industry pairs as kebab-case slugs. Use these values as inputs to the `sub_industry` parameter. **Used by:** Companies Screener, Free Float Market Analysis Costs 1 API credit.

- **Credit cost:** 1 API credit

### `GET /v2/subsectors/`

**Subsectors** — Helper Lists

Returns all available sector/subsector pairs as kebab-case slugs. Use these values as inputs to `sector` and `sub_sector` parameters. **Used by:** Companies Screener, Sector Report, Free Float Market Analysis Costs 1 API credit.

- **Credit cost:** 1 API credit

### `GET /v2/tags/`

**News Tags** — Helper Lists

Returns a sorted alphabetical array of all available tag slugs used across news articles and company filings. Use these values as inputs to the `tags` parameter. **Used by:** News Articles, Company Filings Costs 1 API credit.

- **Credit cost:** 1 API credit

### `GET /v2/company/corporate-actions/{symbol}/`

**Corporate Actions** — Detailed Reports

IDX symbol: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BBCA`, `BMRI`, `TLKM`. Returns all corporate action history for a given IDX-listed company: stock splits, right issues, warrants, bonus shares, AGM events, upcoming dividends, and historical dividends. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | IDX symbol. E.g. `BBCA`, `BMRI`. |

### `GET /v2/company/get-segments/{symbol}/`

**Company Revenue Segments** — Detailed Reports

Returns a Sankey-graph-ready revenue and cost segment breakdown for a given company and financial year. Not all companies have segment data — use the Companies with Revenue Segments endpoint to check availability. IDX symbol: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BUMI`, `TLKM`, `ASII`. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | IDX symbol symbol. E.g. `BUMI`, `TLKM`. Not all companies have segment data — check the Companies with Revenue Segments … |
  | `financial_year` | query | integer | no | Financial year to retrieve. Defaults to the latest available year. |

### `GET /v2/company/report/`

**Company Report** — Detailed Reports

Returns a comprehensive company report organized into distinct sections. By default all sections are included. Use `sections` to request only the data you need and reduce response size. IDX symbol: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BREN`, `BBCA`, `TLKM`. - **overview**: Company identity, market cap, price history, ESG score, tags, indices, affiliates - **valuation**: Close price, forward PE, intrinsic value, historical valuation (PB, PE, PS, PCF, PEG by year) - **future**: Analyst forecasts, EPS growth estimates - **peers**: Peer comparison within the same subsector - **financials**: Historical annual financials (revenue, earnings, assets, equity, margins) - *…

- **Credit cost:** 1 API credit per requested section
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | IDX symbol symbol. E.g. `BREN`, `BBCA`. |
  | `sections` | query | array | no | Comma-separated list of sections to include. Default to all. |

### `GET /v2/company/report/{symbol}/`

**Company Report** — Detailed Reports

Returns a comprehensive company report organized into distinct sections. By default all sections are included. Use `sections` to request only the data you need and reduce response size. IDX symbol: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BREN`, `BBCA`, `TLKM`. - **overview**: Company identity, market cap, price history, ESG score, tags, indices, affiliates - **valuation**: Close price, forward PE, intrinsic value, historical valuation (PB, PE, PS, PCF, PEG by year) - **future**: Analyst forecasts, EPS growth estimates - **peers**: Peer comparison within the same subsector - **financials**: Historical annual financials (revenue, earnings, assets, equity, margins) - *…

- **Credit cost:** 1 API credit per requested section
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | IDX symbol symbol. E.g. `BREN`, `BBCA`. |
  | `sections` | query | array | no | Comma-separated list of sections to include. Default to all. |

### `GET /v2/company/shareholders-composition/{symbol}/`

**Shareholders Composition** — Detailed Reports

IDX symbol: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BBCA`, `BMRI`, `TLKM`. Returns monthly shareholder composition snapshots for a given IDX-listed company within a single calendar year, broken down by investor category (insurance, corporate, pension fund, financial institutions, individual, mutual fund, securities companies, foundation, other) for both local (`_l`) and foreign (`_f`) investors. Data is available from 2021 onwards. Querying earlier years returns an empty `data` array. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | IDX symbol. E.g. `BBCA`, `BMRI`. |
  | `year` | query | integer | no | Calendar year (e.g. `2025`). Defaults to the current year. Data is available from 2021; earlier years return an empty `d… |

### `GET /v2/financials/quarterly/{symbol}/`

**Company Quarterly Financials** — Detailed Reports

Returns quarterly financial data for a given IDX symbol. Fields vary by sector — financial-sector companies (banks, insurance) have additional metrics like `net_interest_income`, `gross_loan`, `total_deposit`. Use the Quarterly Financial Dates endpoint to get valid `report_date` values for a symbol. IDX symbol: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BMRI`, `BBCA`, `TLKM`. Costs 1 API credit per quarter returned.

- **Credit cost:** 1 API credit per quarter returned
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | IDX symbol symbol. E.g. `BMRI`, `BBCA`. |
  | `report_date` | query | string | no | Specific report date (YYYY-MM-DD). Use the Quarterly Financial Dates endpoint to get valid values. |
  | `approx` | query | boolean | no | If `true` (default), use approximate quarter matching when an exact date is not found. |
  | `n_quarters` | query | integer | no | Number of most recent quarters to return. |

### `GET /v2/subsector/report/`

**Subsector Report** — Detailed Reports

Returns a comprehensive report for an IDX subsector, organized into distinct sections. Use `sections` to fetch only the data you need. The `sub_sector` path parameter must be in **kebab-case** format. Get valid values from the Subsectors endpoint. E.g. `banks`, `utilities`, `food-beverage`. - **statistics**: Company count, median PE, weighted avg PE, min/max PE - **market_cap**: Total and avg market cap, quarterly market cap trend, mcap change (1w/1y/YTD) - **stability**: Weighted max drawdown, weighted relative standard deviation - **valuation**: Historical PB, PE, PS, PCF by year - **growth**: Weighted avg revenue and earnings growth - **companies**: List of companies in the subsector with…

- **Credit cost:** 1 API credit per requested section
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `sub_sector` | path | string | yes | Kebab-case subsector slug. E.g. `banks`, `utilities`. Get valid values from the Subsectors endpoint. |
  | `sections` | query | array | no | Comma-separated sections to include. Default to all. |

### `GET /v2/subsector/report/{sub_sector}/`

**Subsector Report** — Detailed Reports

Returns a comprehensive report for an IDX subsector, organized into distinct sections. Use `sections` to fetch only the data you need. The `sub_sector` path parameter must be in **kebab-case** format. Get valid values from the Subsectors endpoint. E.g. `banks`, `utilities`, `food-beverage`. - **statistics**: Company count, median PE, weighted avg PE, min/max PE - **market_cap**: Total and avg market cap, quarterly market cap trend, mcap change (1w/1y/YTD) - **stability**: Weighted max drawdown, weighted relative standard deviation - **valuation**: Historical PB, PE, PS, PCF by year - **growth**: Weighted avg revenue and earnings growth - **companies**: List of companies in the subsector with…

- **Credit cost:** 1 API credit per requested section
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `sub_sector` | path | string | yes | Kebab-case subsector slug. E.g. `banks`, `utilities`. Get valid values from the Subsectors endpoint. |
  | `sections` | query | array | no | Comma-separated sections to include. Default to all. |

### `GET /v2/close/`

**Daily Full-Universe Close** — Transaction Data

Returns the daily closing price for **every** IDX ticker on a single trading day, in one paginated feed — instead of calling the per-symbol Daily Transaction Data endpoint once per ticker. Defaults to the most recent trading day. Pass `date` (`YYYY-MM-DD`) to pull a specific day. Future dates return 400. Tickers with no recorded close for the requested day are omitted. Costs 1 API credit per page. The full ~950-ticker universe is ~32 pages at the maximum `limit` of 30 (~32 credits per full pull).

- **Credit cost:** 1 API credit per page
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `limit` | query | integer | no | Maximum number of tickers to return per page. Max: 30. |
  | `offset` | query | integer | no | Number of tickers to skip for pagination. |
  | `date` | query | string | no | Trading day to pull, in `YYYY-MM-DD` format. Defaults to the most recent trading day with data. Future dates return 400. |

### `GET /v2/daily/{symbol}/`

**Daily Transaction Data** — Transaction Data

Returns daily close price, volume, and market cap for a given IDX symbol over a date range of up to 90 days. IDX symbol: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BBCA`, `GOTO`, `TLKM`. Date range: defaults to last 30 days. Max window 90 days; wider ranges are clamped to the most recent 90 days ending at `end`. Future `end` dates return 400. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | IDX symbol. E.g. `BBCA`, `GOTO`, `TLKM`. |
  | `start` | query | string | no | Start date in `YYYY-MM-DD` format. Defaults to 30 days before `end`. Wider ranges are clamped to the most recent 90 days… |
  | `end` | query | string | no | End date in `YYYY-MM-DD` format. Defaults to today. Future dates return 400. |

### `GET /v2/idx-total/`

**IDX Market Summary** — Transaction Data

Returns historical total IDX market capitalization for a date range of up to 90 days. Earliest available data is from **January 1, 2021**. Requesting earlier dates returns 400. Date range: defaults to last 30 days. Max window 90 days; wider ranges are clamped to the most recent 90 days ending at `end`. Future `end` dates return 400. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `start` | query | string | no | Start date in `YYYY-MM-DD` format. Earliest valid: `2021-01-01`. Defaults to 30 days before `end`. Wider ranges are clam… |
  | `end` | query | string | no | End date in `YYYY-MM-DD` format. Defaults to today. Future dates return 400. |

### `GET /v2/index-daily/{index_code}/`

**Index Daily Transaction Data** — Transaction Data

Returns daily closing price for a given IDX index over a date range of up to 90 days. Earliest available data is from **January 2, 2019**. `ftse`, `idx30`, `idxbumn20`, `idxesgl`, `idxg30`, `idxhidiv20`, `idxq30`, `idxv30`, `ihsg`, `jii70`, `kompas100`, `lq45`, `sminfra18`, `srikehati`, `sti`, `economic30`, `idxvesta28` Date range: defaults to last 30 days. Max window 90 days; wider ranges are clamped to the most recent 90 days ending at `end`. Future `end` dates return 400. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `index_code` | path | string | yes | Index code. E.g. `lq45`, `ihsg`, `idx30`. |
  | `start` | query | string | no | Start date in `YYYY-MM-DD` format. Defaults to 30 days before `end`. Wider ranges are clamped to the most recent 90 days… |
  | `end` | query | string | no | End date in `YYYY-MM-DD` format. Defaults to today. Future dates return 400. |

### `GET /v2/companies/top-changes/`

**Top Company Movers** — Rankings

Returns top gainers and losers across multiple time periods. Supports two classifications (`top_gainers`, `top_losers`) and five periods (`1d`, `7d`, `14d`, `30d`, `365d`). Costs 1 API credit per requested classification × period combination. Default behavior (2 classifications × 5 periods) consumes 10 credits.

- **Credit cost:** 1 API credit per requested classification × period combination
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `sub_sector` | query | string | no | Filter by kebab-case subsector slug. E.g. `banks`. Get valid values from the Subsectors endpoint. |
  | `n_stock` | query | integer | no | Number of companies per period. Default 5, max 10. |
  | `classifications` | query | array | no | Comma-separated. Choices: `top_gainers`, `top_losers`. Default: both. |
  | `periods` | query | array | no | Comma-separated periods. Choices: `1d`, `7d`, `14d`, `30d`, `365d`. Default: all. |
  | `min_mcap_billion` | query | integer | no | Minimum market cap filter in billion IDR. Default 5000. |

### `GET /v2/most-traded/`

**Most Traded Stocks** — Rankings

Returns the most traded IDX stocks by transaction volume over a date range of up to 90 days. Results are keyed by date. Date range: defaults to last 30 days. Max window 90 days; wider ranges are clamped to the most recent 90 days ending at `end`. Future `end` dates return 400. Costs 2 API credits.

- **Credit cost:** 2 API credits
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `sub_sector` | query | string | no | Filter by kebab-case subsector slug. E.g. `banks`. Get valid values from the Subsectors endpoint. |
  | `start` | query | string | no | Start date in `YYYY-MM-DD` format. Defaults to 30 days before `end`. Wider ranges are clamped to the most recent 90 days… |
  | `end` | query | string | no | End date in `YYYY-MM-DD` format. Defaults to today. Future dates return 400. |
  | `adjusted` | query | boolean | no | If `true`, rank by volume × closing price instead of raw volume. |
  | `n_stock` | query | integer | no | Number of tickers per day. Default 5, max 10. |

### `GET /v2/listing-performance/{symbol}/`

**Company IPO & Listing Performance** — IPO & Performance

Returns price change percentages since listing date for a given IDX-listed symbol, across 7, 30, 90, and 365-day windows. Listing performance data is only available for tickers listed **after May 2005**. IDX symbol: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `GOTO`, `BREN`, `BUKA`. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | IDX symbol symbol. E.g. `ARTO`, `BREN`, `GOTO`. |

### `GET /v2/filings/`

**Company Filings** — News & Filings

Returns IDX insider trading filings — buy/sell transactions by company insiders and major shareholders. Supports filtering by sector, subsector, tags, symbol, transaction type, holder_type, and date range. IDX symbol: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BBCA`, `BMRI`, `TLKM`. Date filters: both `start` and `end` are independent and optional — omit either side to leave that bound unconstrained. Future `end` dates return 400. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | query | string | no | IDX symbol symbol to filter by. E.g. `BBCA`, `BMRI`. |
  | `sector` | query | string | no | Kebab-case sector slug. E.g. `healthcare`, `financials`. Get valid values from the Subsectors endpoint. |
  | `sub_sector` | query | string | no | Kebab-case subsector slug. E.g. `banks`, `tobacco`. Get valid values from the Subsectors endpoint. |
  | `start` | query | string | no | Start date in `YYYY-MM-DD` format. Optional; if omitted, no lower bound is applied. Filters on `timestamp`. |
  | `end` | query | string | no | End date in `YYYY-MM-DD` format. Optional; if omitted, no upper bound is applied. Future dates return 400. |
  | `limit` | query | integer | no | Number of results to return. Maximum: 30. |
  | `offset` | query | integer | no | Number of results to skip for pagination. |
  | `transaction_type` | query | string enum(buy, others, sell) | no | Filter by transaction direction: `buy`, `sell`, or `others`. |
  | `tags` | query | string | no | Comma-separated tag slugs. E.g. `Bullish,insider-trading`. Get valid values from the News Tags endpoint. |
  | `holder_type` | query | string enum(corporate-investor, insider, institution) | no | Filter by holder type (case-insensitive). |

### `GET /v2/news/`

**News Articles** — News & Filings

Returns paginated news articles from either the IDX (Indonesian Stock Exchange) or mining news sources. Use the `extension` parameter to choose the data source — each extension has its own set of valid filter parameters. Mixing IDX and mining parameters will return a 400 error. E.g. passing `sector` with `extension=mining` is invalid. - **sector**: Comma-separated sector slugs (kebab-case). Get values from the Subsectors endpoint. - **sub_sector**: Comma-separated subsector slugs (kebab-case). E.g. `banks`, `insurance`, `retailing`. Get valid values from the Subsectors endpoint. - **tags**: Comma-separated tag slugs. Get values from the News Tags endpoint. - **symbols**: Comma-separated IDX …

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `sector` | query | string | no | **IDX only.** Comma-separated sector slugs (kebab-case). |
  | `sub_sector` | query | string | no | **IDX only.** Comma-separated subsector slugs (kebab-case). |
  | `commodity_type` | query | string enum(Bauxite, Coal, Copper, Gold, Iron, Nickel, Non-Metallic Mineral, Sand, Stone, Gravel, …) | no | **Mining only.** Filter by commodity type. E.g. `Coal`, `Nickel`. |
  | `start` | query | string | no | Start date in `YYYY-MM-DD` format. Optional; if omitted, no lower bound is applied. Filters on `timestamp`. |
  | `end` | query | string | no | End date in `YYYY-MM-DD` format. Optional; if omitted, no upper bound is applied. Future dates return 400. |
  | `limit` | query | integer | no | Items per page. Max 30. |
  | `offset` | query | integer | no | Items to skip for pagination. |
  | `tags` | query | string | no | **IDX only.** Comma-separated tag slugs. Get valid values from the News Tags endpoint. |
  | `extension` | query | string enum(idx, mining) | no | Data source. Default `idx`. |
  | `keyword` | query | string | no | Case-insensitive substring match on article title. Works for both IDX and mining. |
  | `symbols` | query | string | no | **IDX only.** Comma-separated IDX symbols. E.g. `BBCA,BBRI`. |

### `GET /v2/suspensions/`

**Stock Suspensions** — News & Filings

Returns a paginated list of historical IDX-listed stock suspensions, including the date a stock was suspended, the official reason, and a link to the IDX PDF notice. Filter by `symbol` to look up a specific company's suspension history, or by `start` / `end` to scope to a date window. Date filters: both `start` and `end` are independent and optional — omit either side to leave that bound unconstrained. Future `end` dates return 400. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | query | string | no | Optional filter by IDX symbol (case-insensitive). E.g. `BBCA`, `GOTO`. |
  | `start` | query | string | no | Start date in `YYYY-MM-DD` format. Optional; if omitted, no lower bound is applied. Filters on `suspension_date`. |
  | `end` | query | string | no | End date in `YYYY-MM-DD` format. Optional; if omitted, no upper bound is applied. Future dates return 400. |
  | `limit` | query | integer | no | Items per page. Max 30. |
  | `offset` | query | integer | no | Number of items to skip. |

### `GET /v2/broker-activity/{broker_code}/`

**Broker Activity By Code** — Brokers

All (stock, day) trading activity for one broker over a date range up to 14 days, grouped by date. Optionally filter to a single stock via `symbol`. Each entry in `data` lists every stock the broker touched that day with buy/sell/net values. Broker codes are the two-letter exchange-member identifiers (e.g. `MG`, `AK`, `CC`). Retrieve the full list of valid codes from the Broker Registry endpoint. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `broker_code` | path | string | yes | Broker code. E.g. `MG`, `AK`, `CC`. |
  | `symbol` | query | string | no | Optional filter to a single stock ticker (e.g. `BBCA`). |
  | `start` | query | string | no | Start date (YYYY-MM-DD). Default: end - 14 days. |
  | `end` | query | string | no | End date (YYYY-MM-DD). Default: today. |

### `GET /v2/broker-activity/{broker_code}/top/`

**Top Accumulations and Distributions Per Broker** — Brokers

Returns the stocks a single broker has been most actively accumulating and distributing over a date range. `top_accumulations` ranks stocks the broker has net bought (largest positive net IDR first); `top_distributions` ranks stocks the broker has net sold (largest negative net IDR first). Useful for tracking a specific broker's directional positioning across the IDX universe. Broker codes are the two-letter exchange-member identifiers (e.g. `MG`, `AK`, `CC`). Retrieve the full list of valid codes from the Broker Registry endpoint. Costs 2 API credits.

- **Credit cost:** 2 API credits
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `broker_code` | path | string | yes | Broker code. E.g. `MG`, `AK`, `CC`. |
  | `start` | query | string | no | Start date (YYYY-MM-DD). Default: end - 30 days. |
  | `end` | query | string | no | End date (YYYY-MM-DD). Default: today. |
  | `n_brokers` | query | integer | no | How many accumulations and distributions to return each (default 10, max 90). |

### `GET /v2/broker-summary/{symbol}/`

**Broker Activity Per Symbol** — Brokers

Per-broker daily trading rows for one IDX ticker over a date range up to 14 days, grouped by date. Optionally filter to a single broker via `broker_code`. Each entry in `data` lists every broker active on that day with buy/sell/net values, lots, frequency, and weighted avg price per share. IDX symbol: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BBCA`, `GOTO`. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | IDX ticker symbol. E.g. `BBCA`, `GOTO`. |
  | `broker_code` | query | string | no | Optional filter to a single broker code (e.g. `MG`). |
  | `start` | query | string | no | Start date (YYYY-MM-DD). Default: end - 14 days. |
  | `end` | query | string | no | End date (YYYY-MM-DD). Default: today. |

### `GET /v2/broker-summary/{symbol}/top/`

**Top Buyers and Sellers Per Symbol** — Brokers

Returns the brokers most actively accumulating and distributing a single IDX ticker over a date range. `top_buyers` ranks brokers by net buy value (largest positive net IDR first); `top_sellers` ranks brokers by net sell value (largest negative net IDR first). Useful for spotting institutional accumulation or distribution patterns on a specific stock. IDX symbol: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BBCA`, `GOTO`. Costs 2 API credits.

- **Credit cost:** 2 API credits
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | IDX ticker symbol. E.g. `BBCA`, `GOTO`. |
  | `start` | query | string | no | Start date (YYYY-MM-DD). Default: end - 30 days. |
  | `end` | query | string | no | End date (YYYY-MM-DD). Default: today. |
  | `cohort` | query | string enum(all, institutional, mixed, retail, unknown) | no | Filter brokers by cohort (case-insensitive). Default `all`. |
  | `n_brokers` | query | integer | no | How many buyers and sellers to return each (default 10, max 90). |
  | `origin` | query | string enum(all, domestic, foreign) | no | Filter brokers by origin. Default `all`. |

### `GET /v2/brokers/`

**Broker Registry** — Brokers

Curated registry of IDX exchange-member brokers with name, origin (foreign / domestic), cohort (retail / mixed / institutional / unknown), and license type. Use this as the authoritative source for valid broker codes when calling broker-scoped endpoints such as `/v2/broker-activity/{broker_code}/`. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `cohort` | query | string enum(institutional, mixed, retail, unknown) | no | Optional filter by broker cohort (case-insensitive). |
  | `origin` | query | string enum(domestic, foreign) | no | Optional filter by broker origin. |

### `GET /v2/brokers/top/`

**Top Brokers Daily Ranking** — Brokers

Brokers ranked by gross trade value (default) or absolute net flow for a single date. Optionally filter by `origin` (foreign/domestic) and `cohort` (retail/mixed/institutional/unknown). Returns all matching brokers if `n_brokers` is omitted. Origin and cohort classifications come from the broker registry. Retrieve the full list with these classifications from the Broker Registry endpoint. Costs 2 API credits.

- **Credit cost:** 2 API credits
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `cohort` | query | string enum(all, institutional, mixed, retail, unknown) | no | Filter by broker cohort (case-insensitive). Default `all`. |
  | `date` | query | string | no | Target date (YYYY-MM-DD). Default: latest available. |
  | `metric` | query | string enum(gross, net) | no | `gross` ranks by total buy + sell value; `net` ranks by absolute net flow. Default `gross`. |
  | `n_brokers` | query | integer | no | How many brokers to return. Default: all matching (~88 total). Max 90. |
  | `origin` | query | string enum(all, domestic, foreign) | no | Filter by broker origin. Default `all`. |

### `GET /v2/foreign-flow/{symbol}/`

**Daily Net Foreign Inflow** — Brokers

Daily net foreign-broker inflow (IDR) for one IDX ticker over a date range up to 90 days. Positive `net_foreign_inflow` means foreign brokers were net buyers that day; negative means foreign brokers were net sellers. Useful for tracking foreign sentiment and capital flow on a specific stock. IDX symbol: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BBCA`, `GOTO`. Only foreign flow is returned because the exchange is a closed market: for any `(symbol, date)`, foreign and domestic net values always sum to zero, so domestic flow is simply `-net_foreign_inflow`. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | IDX ticker symbol. E.g. `BBCA`, `GOTO`. |
  | `start` | query | string | no | Start date (YYYY-MM-DD). Default: end - 30 days. |
  | `end` | query | string | no | End date (YYYY-MM-DD). Default: today. |

### `GET /v2/sgx/companies/`

**SGX Companies Screener** — SGX - Company Screener

High-performance API for filtering and sorting SGX-listed companies. Supports both structured SQL-like queries (`where`, `order_by`) and natural language queries (`q`). Returns a paginated list of companies. **Query modes** (mutually exclusive — `q` overrides all others): - `q`: Natural language, e.g. `top 5 SGX banks by market cap` - `where` + `order_by`: SQL-like structured query SGX symbol: 3-4 characters (letters or digits), optional `.SI` suffix on input. E.g. `D05`, `U11`, `Z74`, `TCPD`. Output always carries the `.SI` suffix. SGX sector column contains duplicate variants (e.g. `Consumer Cyclical` / `Consumer Cyclicals`, `Financial Services` / `Financials`, `Real Estate` / `Properties …

- **Credit cost:** 1 API credit for structured queries
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `where` | query | string | no | SQL-like conditions for advanced filtering. Ignored if `q` is present. Supports operators `=`, `!=`, `>`, `>=`, ` 100000… |
  | `q` | query | string | no | A natural language query (e.g. `top 5 SGX banks by market cap`). When `q` is provided, all other query parameters (`wher… |
  | `order_by` | query | string | no | Field to sort results by. Use `-` prefix for descending order (e.g. `-market_cap`). Supports arithmetic expressions (e.g… |
  | `desc` | query | boolean | no | Sort in descending order. Ignored if `q` is present. |
  | `limit` | query | integer | no | Maximum number of results to return. Max: 200. Ignored if `q` is present. |
  | `offset` | query | integer | no | Number of results to skip for pagination. Ignored if `q` is present. |
  | `include_query_values` | query | boolean | no | If `true`, the response includes a `query_values` object showing the field values used in filtering/sorting. |

### `GET /v2/sgx/sectors/`

**List all SGX sectors** — SGX - Helper Lists

Returns all available SGX sector slugs as a flat array. **Used by:** SGX Companies, SGX Top Companies Costs 1 API credit.

- **Credit cost:** 1 API credit

### `GET /v2/sgx/subsectors/`

**SGX Subsectors** — SGX - Helper Lists

Returns all available SGX sector/subsector pairs as kebab-case slugs. Use these values as inputs to `sector` and `sub_sector` parameters. **Used by:** SGX Companies Costs 1 API credit.

- **Credit cost:** 1 API credit

### `GET /v2/sgx/tags/`

**SGX News Tags** — SGX - Helper Lists

Returns the complete list of distinct tag slugs found across all SGX news articles. Use these values with the `tags` parameter of the SGX News endpoint. Costs 1 API credit.

- **Credit cost:** 1 API credit

### `GET /v2/sgx/company/report/`

**Full company report for an SGX-listed symbol** — SGX - Detailed Reports

SGX symbol: 3-4 characters (letters or digits), optionally followed by `.SI` (case-insensitive) on input. E.g. `D05`, `U11`, `Z74`. Output always carries the `.SI` suffix. Returns a comprehensive company report organized into distinct sections. Use `sections` to fetch only the data you need and reduce response size. - **overview**: Market cap, volume, sector, sub-sector, price changes (1d/7d/1m/1y/3y/ytd), all-time price highs/lows - **valuation**: PE, PS, PCF, PB ratios - **financials**: Historical revenue and earnings by year, EPS, margins, ratios - **dividend**: Dividend yield, growth rate, payout ratio, historical dividends Costs 1 API credit per requested section. Default behavior (all …

- **Credit cost:** 1 API credit per requested section
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | SGX symbol symbol. E.g. `D05`, `U11`, `Z74`. |
  | `sections` | query | array | no | Comma-separated sections to include. Options: `overview`, `valuation`, `financials`, `dividend`. Default: all sections. |

### `GET /v2/sgx/company/report/{symbol}/`

**Full company report for an SGX-listed symbol** — SGX - Detailed Reports

SGX symbol: 3-4 characters (letters or digits), optionally followed by `.SI` (case-insensitive) on input. E.g. `D05`, `U11`, `Z74`. Output always carries the `.SI` suffix. Returns a comprehensive company report organized into distinct sections. Use `sections` to fetch only the data you need and reduce response size. - **overview**: Market cap, volume, sector, sub-sector, price changes (1d/7d/1m/1y/3y/ytd), all-time price highs/lows - **valuation**: PE, PS, PCF, PB ratios - **financials**: Historical revenue and earnings by year, EPS, margins, ratios - **dividend**: Dividend yield, growth rate, payout ratio, historical dividends Costs 1 API credit per requested section. Default behavior (all …

- **Credit cost:** 1 API credit per requested section
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | SGX symbol symbol. E.g. `D05`, `U11`, `Z74`. |
  | `sections` | query | array | no | Comma-separated sections to include. Options: `overview`, `valuation`, `financials`, `dividend`. Default: all sections. |

### `GET /v2/sgx/buybacks/`

**SGX Share Buybacks** — SGX - Transaction Data

Returns SGX share buyback records. Each row includes the purchase date, buyback type, price range, total value, total shares purchased, treasury shares after purchase, and mandate details. SGX symbol: 3-4 characters (letters or digits). E.g. `D05`, `U11`, `Z74`, `TCPD`. Output always carries the `.SI` suffix. Date filters: both `start` and `end` are independent and optional — omit either side to leave that bound unconstrained. Future `end` dates return 400. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | query | string | no | SGX symbol to filter by. E.g. `D05`, `U11`. |
  | `start` | query | string | no | Start date in `YYYY-MM-DD` format. Optional; if omitted, no lower bound is applied. Filters on `purchase_date`. |
  | `end` | query | string | no | End date in `YYYY-MM-DD` format. Optional; if omitted, no upper bound is applied. Future dates return 400. |
  | `limit` | query | integer | no | Items per page. Max 30. |
  | `offset` | query | integer | no | Number of items to skip. |

### `GET /v2/sgx/daily/{symbol}/`

**SGX Daily Price Data** — SGX - Transaction Data

Returns daily close price and volume for a given SGX-listed company over a date range of up to 90 days. SGX symbol: 3-4 characters (letters or digits). E.g. `D05`, `U11`, `Z74`, `TCPD`. Output always carries the `.SI` suffix. Date range: defaults to last 30 days. Max window 90 days; wider ranges are clamped to the most recent 90 days ending at `end`. Future `end` dates return 400. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | SGX symbol. E.g. `D05`, `U11`. |
  | `start` | query | string | no | Start date in `YYYY-MM-DD` format. Defaults to 30 days before `end`. Wider ranges are clamped to the most recent 90 days… |
  | `end` | query | string | no | End date in `YYYY-MM-DD` format. Defaults to today. Future dates return 400. |

### `GET /v2/sgx/short-sell/`

**SGX Short Sell** — SGX - Transaction Data

Returns SGX short sell data. Supports filtering by symbol and date range. SGX symbol: 3-4 characters (letters or digits). E.g. `D05`, `U11`, `Z74`, `TCPD`. Output always carries the `.SI` suffix. Date filters: both `start` and `end` are independent and optional — omit either side to leave that bound unconstrained. Future `end` dates return 400. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | query | string | no | SGX symbol to filter by. E.g. `D05`, `U11`. |
  | `start` | query | string | no | Start date in `YYYY-MM-DD` format. Optional; if omitted, no lower bound is applied. Filters on `date`. |
  | `end` | query | string | no | End date in `YYYY-MM-DD` format. Optional; if omitted, no upper bound is applied. Future dates return 400. |
  | `limit` | query | integer | no | Items per page. Max 30. |
  | `offset` | query | integer | no | Number of items to skip. |

### `GET /v2/sgx/companies/top/`

**Top SGX companies by classification** — SGX - Rankings

Returns top SGX-listed companies ranked by one or more classifications. `dividend_yield`, `revenue`, `earnings`, `market_cap`, `pe` Get valid sector slugs from the SGX Sectors endpoint. Costs 1 API credit per requested classification. Default behavior (all 5 classifications) consumes 5 credits.

- **Credit cost:** 1 API credit per requested classification
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `sector` | query | string | no | Filter by sector slug. E.g. `financial-services`, `technology`. Default: all sectors. |
  | `n_stock` | query | integer | no | Number of top companies to return per classification. Max 10. Default: 5. |
  | `classifications` | query | array | no | Comma-separated list of classifications. Options: `dividend_yield`, `revenue`, `earnings`, `market_cap`, `pe`. Default: … |
  | `min_mcap_million` | query | integer | no | Minimum market cap in million SGD. Default: 1000. |

### `GET /v2/sgx/filings/`

**SGX Insider Filings** — SGX - News & Filings

Returns SGX insider trading filings — buy/sell transactions by company insiders and major shareholders. Supports filtering by symbol, transaction type, holder type, and date range. SGX symbol: 3-4 characters (letters or digits). E.g. `D05`, `U11`, `Z74`, `TCPD`. Output always carries the `.SI` suffix. Date filters: both `start` and `end` are independent and optional — omit either side to leave that bound unconstrained. Future `end` dates return 400. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | query | string | no | SGX symbol to filter by. E.g. `D05`, `U11`. |
  | `start` | query | string | no | Start date in `YYYY-MM-DD` format. Optional; if omitted, no lower bound is applied. Filters on `timestamp`. |
  | `end` | query | string | no | End date in `YYYY-MM-DD` format. Optional; if omitted, no upper bound is applied. Future dates return 400. |
  | `limit` | query | integer | no | Number of results to return. Maximum: 30. |
  | `offset` | query | integer | no | Number of results to skip for pagination. |
  | `transaction_type` | query | string enum(award, buy, others, sell, transfer) | no | Filter by transaction type (case-insensitive). |
  | `holder_type` | query | string enum(insider, institution) | no | Filter by holder type (case-insensitive). |

### `GET /v2/sgx/news/`

**SGX News** — SGX - News & Filings

Returns paginated SGX news articles. Supports filtering by sector, sub-sector, tags, symbols, and date range. SGX symbol: 3-4 characters (letters or digits). E.g. `D05`, `U11`, `Z74`, `TCPD`. Output always carries the `.SI` suffix. Date filters: both `start` and `end` are independent and optional — omit either side to leave that bound unconstrained. Future `end` dates return 400. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `sector` | query | string | no | Filter by sector (case-insensitive). |
  | `sub_sector` | query | string | no | Filter by sub-sector (case-insensitive). |
  | `start` | query | string | no | Start date in `YYYY-MM-DD` format. Optional; if omitted, no lower bound is applied. Filters on `timestamp`. |
  | `end` | query | string | no | End date in `YYYY-MM-DD` format. Optional; if omitted, no upper bound is applied. Future dates return 400. |
  | `limit` | query | integer | no | Items per page. Max 30. |
  | `offset` | query | integer | no | Number of items to skip. |
  | `tags` | query | string | no | Comma-separated tag slugs. Get values from SGX Tags. |
  | `symbols` | query | string | no | Comma-separated SGX symbols. E.g. `D05,U11`. |

### `GET /v2/klse/companies/`

**List KLSE companies filtered by sector** — KLSE

Returns all KLSE-listed companies in a given sector as `symbol` + `company_name` pairs. Get valid sector slugs from the KLSE Sectors endpoint. Format: **kebab-case** (lowercase, hyphen-separated). E.g. `financials`, `healthcare`, `consumer-cyclicals`. **Used by:** KLSE Company Report Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `sector` | query | string | yes | Kebab-case sector slug. E.g. `financials`, `healthcare`. Get valid values from the KLSE Sectors endpoint. |

### `GET /v2/klse/companies/top/`

**Top KLSE companies by classification** — KLSE

Returns top KLSE-listed companies ranked by one or more classifications. `dividend_yield`, `revenue`, `earnings`, `market_cap`, `pe` Get valid sector slugs from the KLSE Sectors endpoint. Costs 1 API credit per requested classification. Default behavior (all 5 classifications) consumes 5 credits.

- **Credit cost:** 1 API credit per requested classification
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `sector` | query | string | no | Filter by sector slug. E.g. `financials`, `healthcare`. Default: all sectors. |
  | `n_stock` | query | integer | no | Number of top companies to return per classification. Max 10. Default: 5. |
  | `classifications` | query | array | no | Comma-separated list of classifications. Options: `dividend_yield`, `revenue`, `earnings`, `market_cap`, `pe`. Default: … |
  | `min_mcap_million` | query | integer | no | Minimum market cap in million MYR. Default: 1000. |

### `GET /v2/klse/company/report/`

**Full company report for a KLSE-listed symbol** — KLSE

KLSE symbol: 4-digit numeric code. E.g. `1155`, `4197`, `5225`. Returns a comprehensive company report organized into distinct sections. Use `sections` to fetch only the data you need and reduce response size. - **overview**: Market cap, volume, sector, sub-sector, price changes (1d/7d) - **valuation**: PE, PB, PS, PCF ratios (TTM and historical) - **financials**: Historical revenue and earnings by year, EPS, margins, ratios - **dividend**: Dividend history and yield Costs 1 API credit per requested section. Default behavior (all 4 sections) consumes 4 credits.

- **Credit cost:** 1 API credit per requested section
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | KLSE symbol symbol (4-digit numeric code). E.g. `1155`, `4197`. |
  | `sections` | query | array | no | Comma-separated sections to include. Options: `overview`, `valuation`, `financials`, `dividend`. Default: all sections. |

### `GET /v2/klse/company/report/{symbol}/`

**Full company report for a KLSE-listed symbol** — KLSE

KLSE symbol: 4-digit numeric code. E.g. `1155`, `4197`, `5225`. Returns a comprehensive company report organized into distinct sections. Use `sections` to fetch only the data you need and reduce response size. - **overview**: Market cap, volume, sector, sub-sector, price changes (1d/7d) - **valuation**: PE, PB, PS, PCF ratios (TTM and historical) - **financials**: Historical revenue and earnings by year, EPS, margins, ratios - **dividend**: Dividend history and yield Costs 1 API credit per requested section. Default behavior (all 4 sections) consumes 4 credits.

- **Credit cost:** 1 API credit per requested section
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `symbol` | path | string | yes | KLSE symbol symbol (4-digit numeric code). E.g. `1155`, `4197`. |
  | `sections` | query | array | no | Comma-separated sections to include. Options: `overview`, `valuation`, `financials`, `dividend`. Default: all sections. |

### `GET /v2/klse/sectors/`

**List all KLSE sectors** — KLSE

Returns all available KLSE sector slugs as a flat array. **Used by:** KLSE Companies, KLSE Top Companies Costs 1 API credit.

- **Credit cost:** 1 API credit

### `GET /v2/mining/companies/`

**List Mining Companies** — Companies

Searches for Indonesian mining companies by name, symbol, slug, or key operation. Supports filtering by commodity type and company type. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `commodity_type` | query | string enum(Aluminium, Coal, Copper, Gold, Nickel, Silver, Zinc and Lead) | no | Filter by commodity. E.g. `Coal`, `Nickel`, `Gold`. |
  | `limit` | query | integer | no | Results per page. Default 20. |
  | `offset` | query | integer | no | Items to skip for pagination. |
  | `keyword` | query | string | no | Search across company name, IDX symbol, slug, and key operations (case-insensitive). |
  | `company_type` | query | string enum(Consultant, Contractor, Holding, Manufacturer, Mine Owner, Trader) | no | Filter by company type. |
  | `has_financials` | query | boolean | no | If `true`, return only companies with financial data available. |

### `GET /v2/mining/companies/financials/{slug}/`

**Mining Company Financials** — Companies

Returns annual financial records (assets, revenue, profit with breakdowns) for a mining company. All monetary values are in USD millions. Defaults to the latest available year. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `slug` | path | string | yes | Company slug. |
  | `year` | query | integer | no | Year to retrieve. Defaults to the latest available year. |

### `GET /v2/mining/companies/ownership/{slug}/`

**Mining Company Ownership** — Companies

Returns the corporate ownership tree for a mining company — showing parent companies (who owns it) and subsidiaries (what it owns) with percentage stakes. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `slug` | path | string | yes | Company slug. |

### `GET /v2/mining/companies/performance/{slug}/`

**Mining Company Performance** — Companies

Returns production volume, sales volume, strip ratio, and resources/reserves data for a mining company for a given year. Defaults to the latest available year. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `slug` | path | string | yes | Company slug. |
  | `commodity_type` | query | string enum(Coal, Copper, Gold, Nickel, Silver) | no | Filter by commodity. E.g. `Coal`, `Nickel`. Case-insensitive. |
  | `year` | query | integer | no | Year to retrieve. Defaults to the latest available year. |

### `GET /v2/mining/companies/{slug}/`

**Mining Company Detail** — Companies

Returns comprehensive operational details for a single mining company including activities, commodity types, licenses, contracts, and site count. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `slug` | path | string | yes | Company slug. Get valid slugs from the Mining Companies List endpoint. |

### `GET /v2/mining/commodities/`

**List Commodities** — Commodities & Trade

Lists all commodities available in the price database with coverage metadata. Use this as a discovery endpoint before querying Commodity Price History endpoint. Most commodities only have data in the price table. Cross-table data (production, exports, reserves, sites) is limited to: **Coal**, **Gold**, **Nickel**, **Copper** — and partially Silver, Cobalt, Bauxite. Costs 1 API credit.

- **Credit cost:** 1 API credit

### `GET /v2/mining/commodities/{commodity_name}/price/`

**Commodity Price History** — Commodities & Trade

Retrieves historical price data for a commodity by year range. Data is monthly (bi-weekly for recent Coal entries). Maximum range: 3 years. Use List Commodities to discover all available commodity names. Requesting more than 3 years will return a 400 error. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `commodity_name` | path | string | yes | The commodity name (e.g., `Gold`, `Coal`). Get valid names from the List Commodities endpoint. |
  | `start_year` | query | integer | no | Start year (e.g., `2022`). Defaults to current year − 2. |
  | `end_year` | query | integer | no | End year inclusive (e.g., `2024`). Defaults to current year. Maximum 3-year range from `start_year`. |

### `GET /v2/mining/exports/`

**Top Export Destinations** — Commodities & Trade

Ranks countries by total export value for a given year and commodity, showing the top destinations for Indonesian commodity exports. Available `commodity_type` values: `Gold`, `Copper`, `Coal`. `export_usd` is in base USD. Volume unit is specified per row in `volume_unit` (typically `Mt`). Two volume sources are provided: **BPS** (Badan Pusat Statistik) and **ESDM** (Energi Sumber Daya Mineral) — values may differ due to methodology. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `commodity_type` | query | string enum(Coal, Copper, Gold) | yes | The commodity to analyze (e.g., `Gold`, `Coal`). |
  | `year` | query | integer | yes | The year to analyze export data for (e.g., `2024`). |
  | `limit` | query | integer | no | Number of top countries to return. Maximum: 30. |

### `GET /v2/mining/global-commodity/`

**Global Commodity Data** — Commodities & Trade

Retrieves global commodity data including production, reserves, and trade information. At least one of `commodity_type` or `country` must be provided. Available `commodity_type` values: `Coal`, `Gold`, `Nickel`, `Copper`, `Bauxite`. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `commodity_type` | query | string enum(Bauxite, Coal, Copper, Gold, Nickel) | no | Filter by commodity type. Required if `country` not provided. |
  | `country` | query | string | no | Filter by country (exact match, e.g., `Australia`). Required if `commodity_type` not provided. |
  | `limit` | query | integer | no | Number of results to return. Maximum: 30. |

### `GET /v2/mining/sales-destination/{slug}/`

**Company Sales Destinations** — Commodities & Trade

Retrieves sales destination breakdown for a specific mining company by its slug, showing revenue and volume distribution by country for a specific year. Defaults to the latest available year if none is specified. `revenue_usd` is in base USD. Volume unit is specified per country entry in `unit` (e.g., `Mt`). Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `slug` | path | string | yes | The company's unique identifier slug (e.g., `adaro-energy`). |
  | `year` | query | integer | no | The year to retrieve. Defaults to the latest available year. |

### `GET /v2/mining/resources-reserves/`

**Resources & Reserves Index** — Production & Sites

Discovery index showing which provinces, years, and commodities have resources and reserves data available. Use this before querying the detail endpoint to confirm data availability. This index endpoint does not accept any query parameters. Use Resources & Reserves Detail to retrieve actual values. Costs 1 API credit.

- **Credit cost:** 1 API credit

### `GET /v2/mining/resources-reserves/{province}/`

**Resources & Reserves Detail** — Production & Sites

Returns resources and reserves data for a single province, nested by year then by commodity. Each commodity entry contains the full breakdown: `exploration_target`, `total_inventory`, `resources`, `reserves`, and `unit`. Available `commodity_type` values: `Coal`, `Gold`, `Silver`, `Copper`, `Nickel`, `Cobalt`, `Tin`. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `province` | path | string enum(Aceh, Banten, Bengkulu, Gorontalo, Jambi, Jawa Barat, Jawa Tengah, Jawa Timur, …) | yes | Exact province name (e.g., `Kalimantan Timur`). Case-insensitive. |
  | `commodity_type` | query | string enum(Coal, Cobalt, Copper, Gold, Nickel, Silver, Tin) | no | Restrict results to a specific commodity. |
  | `year` | query | integer | no | Restrict results to a specific year. |

### `GET /v2/mining/sites/`

**Mining Sites** — Production & Sites

Lists mining sites with advanced filtering for location, commodity type, and production volume, plus sorting capabilities and detailed site information. Available `commodity_type` values: `Coal`, `Gold`, `Nickel`, `Copper`. Prefix `order_by` with `-` for descending order (e.g. `-production_volume`). Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `province` | query | string enum(Aceh, Banten, Gorontalo, Jambi, Jawa Timur, Kalimantan Selatan, Kalimantan Tengah, Kalimantan Timur, …) | no | Filter by exact province name (e.g., `Kalimantan Timur`). |
  | `commodity_type` | query | string enum(Coal, Copper, Gold, Nickel) | no | Filter by commodity type. Case-insensitive. |
  | `company` | query | string | no | Filter by company slug. |
  | `year` | query | integer | no | Filter by reporting year. |
  | `order_by` | query | string enum(-production_volume, -strip_ratio, -year, production_volume, strip_ratio, year) | no | Sort field. Prefix with `-` for descending. Default: `-year`. |
  | `min_production` | query | number | no | Filter for sites with `production_volume` ≥ this value. |
  | `limit` | query | integer | no | Number of results to return. Maximum: 30. |
  | `offset` | query | integer | no | Number of results to skip. |

### `GET /v2/mining/sites/{slug}/`

**Mining Site Detail** — Production & Sites

Returns full details for a single mining site by its slug, including parsed resources/reserves and location (with latitude and longitude). Use Mining Sites to discover site slugs. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `slug` | path | string | yes | URL-friendly identifier for the mining site. |

### `GET /v2/mining/total-production/`

**Total Commodity Production** — Production & Sites

Returns total national production for a commodity across all years, including year-over-year percentage change. Results are ordered by year descending. Available `commodity_type` values: `Coal`, `Nickel`, `Gold`, `Copper`. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `commodity_type` | query | string enum(Coal, Copper, Gold, Nickel) | yes | The commodity to analyze (e.g., `Coal`). Required. |

### `GET /v2/mining/contracts/`

**Mining Contracts** — Contracts & Licenses

Returns active mining contracts linking mine owners to their service contractors. Optionally filter by owner or contractor slug. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `contractor` | query | string | no | Filter by contractor company slug. |
  | `mine_owner` | query | string | no | Filter by mine owner company slug. |

### `GET /v2/mining/license-auctions/`

**Mining License Auctions** — Contracts & Licenses

Lists mining license auctions scraped from the ESDM Minerba portal. Phases and participants are omitted from list results — use the detail endpoint for the full auction record. Available `commodity_type` values: `Nickel`, `Coal`, `Gold`, `Copper`. Use `participant` + `qualified=true` to find auctions where a specific company passed pre-qualification. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `province` | query | string enum(Bengkulu, Gorontalo, Kalimantan Tengah, Maluku Utara, Nusa Tenggara Barat, Sulawesi Selatan, Sulawesi Utara, Sumatera Selatan) | no | Filter by province (e.g., `Sulawesi Selatan`). Case-insensitive. |
  | `commodity_type` | query | string enum(Coal, Copper, Gold, Nickel) | no | Filter by commodity (e.g., `Nickel`, `Coal`). Case-insensitive. |
  | `order_by` | query | string enum(-commodity_type, -licensed_area_ha, -participant_count, -winner_date, commodity_type, licensed_area_ha, participant_count, winner_date) | no | Sort field. Prefix with `-` for descending. Default: `-winner_date`. |
  | `limit` | query | integer | no | Number of results to return. Maximum: 30. |
  | `offset` | query | integer | no | Number of results to skip. |
  | `area_type` | query | string enum(WIUP, WIUPK) | no | Filter by area type (e.g., `WIUPK`). Case-insensitive. |
  | `status` | query | string | no | Filter by auction status (e.g., `Lelang Selesai`). Case-insensitive. |
  | `participant` | query | string | no | Filter auctions where a company name (partial match) participated. |
  | `qualified` | query | boolean | no | When `true`, only return auctions where the `participant` passed qualification. Requires `participant`. |
  | `min_participants` | query | integer | no | Only return auctions with at least this many participants. |

### `GET /v2/mining/license-auctions/{wiup_code}/`

**Mining License Auction Detail** — Contracts & Licenses

Retrieves the full record for a single mining license auction by its WIUP code, including the parsed phases timeline and participant qualification list. Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `wiup_code` | path | string | yes | The unique WIUP code identifier for the auction. |

### `GET /v2/mining/licenses/`

**Mining Licenses** — Contracts & Licenses

Lists mining licenses (IUP/IUPK) from the ESDM Minerba portal with filters for status, commodity, location, and expiry date. Top `commodity_type` values: `Coal`, `Nickel`, `Non-Metallic Mineral`, `Sand/Stone/Gravel`, `Limestone`, `Gold`, `Tin`, `Iron`, `Bauxite`, `Clay`, `Copper`. Prefix `order_by` with `-` for descending order. Default sort: `license_expiry_date` (soonest expiring first). Costs 1 API credit.

- **Credit cost:** 1 API credit
- **Parameters:**

  | Name | In | Type | Required | Description |
  | --- | --- | --- | --- | --- |
  | `province` | query | string enum(Aceh, Bali, Banten, Bengkulu, Gorontalo, Jambi, Jawa Barat, Jawa Tengah, …) | no | Filter by province. Exact match. |
  | `commodity_type` | query | string enum(Bauxite, Clay, Coal, Copper, Gold, Granite, Iron, Limestone, …) | no | Filter by commodity. Case-insensitive. |
  | `company` | query | string | no | Filter by company slug. |
  | `order_by` | query | string enum(-commodity_type, -license_effective_date, -license_expiry_date, -licensed_area_ha, commodity_type, license_effective_date, license_expiry_date, licensed_area_ha) | no | Sort field. Prefix with `-` for descending. Default: `license_expiry_date`. |
  | `limit` | query | integer | no | Number of results to return. Maximum: 30. |
  | `offset` | query | integer | no | Number of results to skip. |
  | `expiring_soon` | query | boolean | no | Set to `true` to find licenses expiring within the next 365 days. |
  | `license_type` | query | string enum(IPR, IUP, IUPK, KK, PKP2B, SIPB) | no | Filter by license type (e.g., `IUP`, `IUPK`). Case-insensitive. |
  | `activity` | query | string enum(Eksplorasi, Operasi Produksi) | no | Filter by activity stage (e.g., `Eksplorasi`, `Operasi Produksi`). Case-insensitive. |
  | `cnc` | query | boolean | no | Filter by Clear & Clean status. Case-insensitive. |

