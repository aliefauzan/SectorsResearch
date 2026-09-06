# SGX & KLSE — Coverage, Fields, and Where They Fall Short

> Fourth-pass gap fill. The IDX screener is documented in
> [`03-screener-query-language.md`](03-screener-query-language.md). The **SGX screener is a
> separate field set with its own limits**, and KLSE is thinner still. If a project depends
> on either, read this before committing — several things that work on IDX simply do not exist.

## The short version

| | IDX | SGX | KLSE |
| --- | --- | --- | --- |
| Companies covered | ~950 (99.99%) | 617 (~80%) | sector-level only |
| Screener | ✅ 219 fields | ✅ 85 fields | ❌ none |
| Natural language `?q=` | ✅ | ✅ (auto USD→SGD) | ❌ |
| Quarterly data | ✅ | ❌ **annual only** | ❌ |
| Peer averages | ✅ | ❌ | ❌ |
| Ownership / executives / major shareholders | ✅ | ❌ | ❌ |
| Free float | ✅ | ❌ | ❌ |
| Broker / bandarmology data | ✅ | ❌ | ❌ |
| Insider filings | ✅ | ✅ | ❌ |
| News | ✅ | ✅ | ❌ |
| Buybacks | ❌ | ✅ | ❌ |
| Short-sell data | ❌ | ✅ | ❌ |
| Corporate actions / suspensions | ✅ | ❌ | ❌ |
| REST endpoints | **34** | **12** | **5** |

**SGX has two things IDX does not**: share buybacks (`/v2/sgx/buybacks/`) and short-sell
data (`/v2/sgx/short-sell/`). Everything else is a subset.

Counts are actual REST paths in the OpenAPI spec (34 + 12 + 5 + 19 mining = 70). MCP tool
counts differ slightly because two endpoints expose the same tool via path and query variants.

---

## ⚠️ Three SGX traps

### 1. Duplicate sector labels in the source data

Straight from the field documentation for `sector`:

> "NB: source data contains duplicate labels (e.g. `Consumer Cyclical` vs `Consumer Cyclicals`,
> `Financial Services` vs `Financials`) — pending upstream cleanup."

**A filter on `sector = 'Financials'` silently misses every company labelled
`Financial Services`.** You will get a plausible-looking result set that is missing an
arbitrary fraction of the sector, with no error and no warning.

Defend against it — use `in` with both spellings, or filter on `sub_sector` instead:

```
where=sector in ['Financials', 'Financial Services']
```

Fetch `/v2/sgx/sectors/` (1 credit) and **look for near-duplicate pairs before you trust
any sector filter.** This is the kind of thing that quietly invalidates an analysis.

### 2. Most financial fields are populated for ~22 companies only

Twenty of the 34 yearly fields are marked **`[Big caps only]`** — populated for roughly
**22 large-caps** out of 617:

`operating_cash_flow`, `investing_cash_flow`, `financing_cash_flow`, `free_cash_flow`, `net_cash_flow`, `capital_expenditure`, `ebit`, `ebitda`, `gross_income`, `cost_of_revenue`, `operating_income`, `operating_expense`, `pretax_income`, `income_taxes`, `total_asset`, `total_equity`, `total_liabilities`, `working_capital`, `total_current_asset`, `total_non_current_asset`

That is the entire cash-flow statement, the entire income statement below revenue, and most
of the balance sheet. A screener over "all SGX companies by EBITDA" is really a screener
over about twenty of them.

### 3. Ten more fields exist for three banks

Fields marked **`[Banks only]`** are populated for **DBS, OCBC and UOB** — that's it:

`net_interest_income`, `interest_income`, `interest_expense`, `net_fee_and_commission_income`, `net_trading_income`, `net_loan`, `gross_loan`, `total_deposit`, `core_capital_tier1`, `total_risk_weighted_asset`

Contrast with IDX, where banking metrics (CASA, LDR, NIM, CAR, NPL, HQLA) are available
across the whole banking sub-sector.

---

## What SGX does *not* have that IDX does

Quoting the SGX-specific limitations block directly:

- **No person / entity ownership queries** — no `executives`, `major_shareholders`, or `affiliates` fields
- **No peer averages** — no `pe_peer_avg`, `pb_peer_avg`, etc.
- **No `free_float` field**
- **No quarterly data** — only annual fields like `revenue[2024]`. Quarterly bracket notation returns `400 QUARTERLY_NOT_SUPPORTED`

So every one of the ownership-network, whale-investor, conglomerate-mapping and
bandarmology ideas is **IDX-only**. So is anything peer-relative, anything free-float-based,
and anything that needs quarter-over-quarter momentum.

> **Practical read for the hackathon:** build on IDX. SGX is a reasonable *secondary*
> market for a comparison feature, but a project whose core depends on SGX depth will hit
> a wall — and IDX is the market the judges care about anyway.

---

## SGX screener fields (85)

Same query interface as IDX: `where` + `order_by` (1 credit) or `q` (3 credits), and
natural-language queries auto-convert USD to SGD via a live FX feed cached 24h.

### Direct Fields (Top-level columns) — 34

| Field | Description |
| --- | --- |
| `symbol` | SGX ticker symbol (3-4 characters, e.g. `D05`, `U11`, `Z74`, `TCPD`; accepts optional `.SI` suffix on input, always returned with it) |
| `company_name` | Full registered company name |
| `sector` | SGX sector classification. NB: source data contains duplicate labels (e.g. `Consumer Cyclical` vs `Consumer Cyclicals`, `Financial Services` vs `Financials`) — pending upstream cleanup. |
| `sub_sector` | SGX sub-sector classification (126 distinct values) |
| `market_cap` | Market capitalisation in SGD |
| `volume` | Recent average daily trading volume (shares) |
| `last_close_price` | Most recent close price in SGD |
| `employee_num` | Total number of employees |
| `pe` | Price-to-earnings ratio |
| `eps` | Earnings per share (SGD) |
| `beta` | Beta vs SGX market |
| `ps` | Price-to-sales ratio |
| `pcf` | Price-to-cash-flow ratio |
| `pb` | Price-to-book ratio |
| `gross_margin` | Gross profit margin (decimal, e.g. 0.45 = 45%) |
| `operating_margin` | Operating profit margin (decimal) |
| `net_profit_margin` | Net profit margin (decimal) |
| `quick_ratio` | Quick ratio (acid test) |
| `current_ratio` | Current ratio |
| `debt_to_equity` | Debt-to-equity ratio |
| `one_year_eps_growth` | 1-year EPS growth (decimal) |
| `one_year_sales_growth` | 1-year sales (revenue) growth (decimal) |
| `forward_dividend` | Forward annual dividend per share in SGD |
| `forward_dividend_yield` | Forward annual dividend yield (decimal) |
| `dividend_ttm` | Trailing-twelve-month dividend per share in SGD |
| `dividend_yield_5y_avg` | 5-year average dividend yield (decimal) |
| `dividend_growth_rate` | Year-over-year dividend growth rate (decimal) |
| `payout_ratio` | Dividend payout ratio (decimal) |
| `change_1d` | 1-day price change (decimal) |
| `change_7d` | 7-day price change (decimal) |
| `change_1m` | 1-month price change (decimal) |
| `change_ytd` | Year-to-date price change (decimal) |
| `change_1y` | 1-year price change (decimal) |
| `change_3y` | 3-year price change (decimal) |

### Array Fields — 1

| Field | Description |
| --- | --- |
| `tags` | Analyst sentiment / classification tags |

### JSON Object Fields (Most Recent Data) — 16

| Field | Description |
| --- | --- |
| `ytd_low_price` | Year-to-date lowest closing price in SGD |
| `ytd_low_date` | Date of the year-to-date lowest closing price |
| `ytd_high_price` | Year-to-date highest closing price in SGD |
| `ytd_high_date` | Date of the year-to-date highest closing price |
| `52_w_low_price` | 52-week lowest closing price in SGD |
| `52_w_low_date` | Date of the 52-week lowest closing price |
| `52_w_high_price` | 52-week highest closing price in SGD |
| `52_w_high_date` | Date of the 52-week highest closing price |
| `90_d_low_price` | 90-day lowest closing price in SGD |
| `90_d_low_date` | Date of the 90-day lowest closing price |
| `90_d_high_price` | 90-day highest closing price in SGD |
| `90_d_high_date` | Date of the 90-day highest closing price |
| `all_time_low_price` | All-time lowest closing price in SGD |
| `all_time_low_date` | Date of the all-time lowest closing price |
| `all_time_high_price` | All-time highest closing price in SGD |
| `all_time_high_date` | Date of the all-time highest closing price |

### Yearly JSON Fields (Historical & Forecast Data) — 34

| Field | Description |
| --- | --- |
| `revenue` | Annual revenue in SGD. Use: `revenue[2024]`. |
| `earnings` | Annual net profit/loss in SGD. Use: `earnings[2024]`. |
| `total_dividend` | Total dividends paid per share for the year (SGD). Use: `total_dividend[2024]`. |
| `total_yield` | Total dividend yield for the year (decimal). Use: `total_yield[2024]`. |
| `operating_cash_flow` | Operating cash flow in SGD. Use: `operating_cash_flow[2024]`. _(coverage: Big caps only)_ |
| `investing_cash_flow` | Investing cash flow in SGD. Use: `investing_cash_flow[2024]`. _(coverage: Big caps only)_ |
| `financing_cash_flow` | Financing cash flow in SGD. Use: `financing_cash_flow[2024]`. _(coverage: Big caps only)_ |
| `free_cash_flow` | Free cash flow in SGD. Use: `free_cash_flow[2024]`. _(coverage: Big caps only)_ |
| `net_cash_flow` | Net cash flow in SGD. Use: `net_cash_flow[2024]`. _(coverage: Big caps only)_ |
| `capital_expenditure` | Capital expenditure in SGD. Use: `capital_expenditure[2024]`. _(coverage: Big caps only)_ |
| `ebit` | EBIT (earnings before interest and tax) in SGD. Use: `ebit[2024]`. _(coverage: Big caps only)_ |
| `ebitda` | EBITDA in SGD. Use: `ebitda[2024]`. _(coverage: Big caps only)_ |
| `gross_income` | Gross income in SGD. Use: `gross_income[2024]`. _(coverage: Big caps only)_ |
| `cost_of_revenue` | Cost of revenue in SGD. Use: `cost_of_revenue[2024]`. _(coverage: Big caps only)_ |
| `operating_income` | Operating income in SGD. Use: `operating_income[2024]`. _(coverage: Big caps only)_ |
| `operating_expense` | Operating expense in SGD. Use: `operating_expense[2024]`. _(coverage: Big caps only)_ |
| `pretax_income` | Pre-tax income in SGD. Use: `pretax_income[2024]`. _(coverage: Big caps only)_ |
| `income_taxes` | Income taxes paid in SGD. Use: `income_taxes[2024]`. _(coverage: Big caps only)_ |
| `total_asset` | Total assets in SGD. Use: `total_asset[2024]`. _(coverage: Big caps only)_ |
| `total_equity` | Total equity in SGD. Use: `total_equity[2024]`. _(coverage: Big caps only)_ |
| `total_liabilities` | Total liabilities in SGD. Use: `total_liabilities[2024]`. _(coverage: Big caps only)_ |
| `working_capital` | Working capital in SGD. Use: `working_capital[2024]`. _(coverage: Big caps only)_ |
| `total_current_asset` | Total current assets in SGD. Use: `total_current_asset[2024]`. _(coverage: Big caps only)_ |
| `total_non_current_asset` | Total non-current assets in SGD. Use: `total_non_current_asset[2024]`. _(coverage: Big caps only)_ |
| `net_interest_income` | Net interest income in SGD. Use: `net_interest_income[2024]`. _(coverage: Banks only)_ |
| `interest_income` | Total interest income in SGD. Use: `interest_income[2024]`. _(coverage: Banks only)_ |
| `interest_expense` | Total interest expense in SGD. Use: `interest_expense[2024]`. _(coverage: Banks only)_ |
| `net_fee_and_commission_income` | Net fee and commission income in SGD. Use: `net_fee_and_commission_income[2024]`. _(coverage: Banks only)_ |
| `net_trading_income` | Net trading income in SGD. Use: `net_trading_income[2024]`. _(coverage: Banks only)_ |
| `net_loan` | Net loans outstanding in SGD. Use: `net_loan[2024]`. _(coverage: Banks only)_ |
| `gross_loan` | Gross loans outstanding in SGD. Use: `gross_loan[2024]`. _(coverage: Banks only)_ |
| `total_deposit` | Total customer deposits in SGD. Use: `total_deposit[2024]`. _(coverage: Banks only)_ |
| `core_capital_tier1` | Core capital (Tier 1) in SGD. Use: `core_capital_tier1[2024]`. _(coverage: Banks only)_ |
| `total_risk_weighted_asset` | Total risk-weighted assets in SGD. Use: `total_risk_weighted_asset[2024]`. _(coverage: Banks only)_ |

Categories with zero fields on SGX (`Quarterly Financial Data`, `JSON List Fields`) are
absent by design — see the limitations above.

---

## KLSE — four endpoints, no screener

| Endpoint | Returns |
| --- | --- |
| `/v2/klse/sectors/` | Flat array of sector slugs |
| `/v2/klse/companies/` | `symbol` + `company_name` pairs for a sector |
| `/v2/klse/companies/top/` | Top companies by `dividend_yield`, `earnings`, `market_cap`, `pe`, `revenue` |
| `/v2/klse/company/report/{symbol}/` | Report with `overview`, `valuation`, `financials`, `dividend` sections |

Symbols are **4-digit numeric codes** (`1155`, `4197`, `5225`), not letters.

There is no KLSE screener, no news, no filings, no daily price endpoint, and no
transaction data. KLSE is sufficient for a "look up a Malaysian company" feature and
nothing more ambitious than that.

---

## If you still want a regional angle

The comparison that actually works across all three markets is limited to what all three
expose: company report `overview` / `valuation` / `financials` / `dividend`, and top-companies
rankings by market cap, PE, revenue, earnings and dividend yield.

That is enough for a "same sector, three exchanges" comparison — a legitimate and
under-explored angle, since almost everyone will build IDX-only. Just scope it to those
four sections and five classifications, and don't promise depth the data can't support.

Costs: 4 credits per SGX/KLSE company report (all sections), 5 credits for a full
top-companies pull. Constrain `sections` and `classifications` as always.
