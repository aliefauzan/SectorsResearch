# Sectors API -- Endpoint Quick-Lookup

All endpoints: `GET https://api.sectors.app/v1{path}`

## IDX (Indonesia Stock Exchange)

| # | Endpoint | Path | Key params |
|---|---|---|---|
| 1 | Get subsectors | `/subsectors/` | -- |
| 2 | Get industries | `/industries/` | -- |
| 3 | Get subindustries | `/subindustries/` | -- |
| 4 | Index data / companies by index | `/index/{index}/` | `index`: `lq45`, `idx30`, `kompas100`, etc. |
| 5 | Companies by subsector | `/companies/?sub_sector={sub_sector}` | `sub_sector` (kebab-case) |
| 6 | Companies by subindustry | `/companies/?sub_industry={sub_industry}` | `sub_industry` |
| 7 | Companies with segments | `/companies/list_companies_with_segments/` | -- |
| 8 | Listing performance | `/listing-performance/{ticker}/` | `ticker` |
| 9 | Quarterly financial dates | `/company/get_quarterly_financial_dates/{ticker}/` | `ticker` |
| 10 | Quarterly financials | `/financials/quarterly/{ticker}/` | `ticker`, `report_date?`, `approx?`, `n_quarters?` |
| 11 | Company segments | `/company/get-segments/{ticker}/` | `ticker`, `financial_year?` |
| 12 | Company report | `/company/report/{ticker}/` | `ticker`, `sections?` |
| 13 | Index daily data | `/index-daily/{index_code}/` | `index_code`, `start?`, `end?` |
| 14 | IDX total market cap | `/idx-total/` | `start?`, `end?` |
| 15 | Top movers (gainers/losers) | `/companies/top-changes/` | `classifications?`, `n_stock?`, `min_mcap_billion?`, `periods?`, `sub_sector?` |
| 16 | Most traded stocks | `/most-traded/` | `start?`, `end?`, `n_stock?`, `adjusted?`, `sub_sector?` |
| 17 | Top growth companies | `/companies/top-growth/` | `classifications?`, `n_stock?`, `min_mcap_billion?`, `sub_sector?` |
| 18 | Top companies by metrics | `/companies/top/` | `classifications?`, `filters?`, `logic?`, `n_stock?`, `min_mcap_billion?`, `sub_sector?`, `year?` |
| 19 | Daily transaction | `/daily/{ticker}` | `ticker`, `start?`, `end?` |

## SGX (Singapore Exchange)

| # | Endpoint | Path | Key params |
|---|---|---|---|
| 1 | SGX sectors | `/sgx/sectors/` | -- |
| 2 | SGX companies by sector | `/sgx/companies/?sector={sector}` | `sector` (kebab-case) |
| 3 | SGX company report | `/sgx/company/report/{ticker}` | `ticker` |
| 4 | SGX top companies | `/sgx/companies/top/` | `sector?`, `classifications?`, `min_mcap_million?` |

## Parameter conventions

| Convention | Rule |
|---|---|
| Dates | `YYYY-MM-DD` format |
| Tickers (IDX) | Uppercase, no `.JK` suffix |
| Tickers (SGX) | Uppercase, no `.SI` suffix |
| Subsectors / sectors | kebab-case (e.g. `banks`, `consumer-defensive`) |
| Multiple values | Comma-separated string (e.g. `top_gainers,top_losers`) |
| Market cap (IDX) | Billion IDR (`min_mcap_billion`) |
| Market cap (SGX) | Million SGD (`min_mcap_million`) |
| Auth header | `Authorization: <raw_api_key>` (no Bearer prefix) |
