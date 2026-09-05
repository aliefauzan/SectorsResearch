# Screener Query Language — `/v2/companies/`

> The single most powerful endpoint in the API, and the one worth mastering first.
> Source: <https://docs.sectors.app/api-references/v2/indonesia/screener/companies>

`GET /v2/companies/` filters and sorts IDX-listed companies. `GET /v2/sgx/companies/` is the
same interface scoped to 617 SGX companies (annual data only).

## Two mutually exclusive query modes

| Mode | Parameter | Cost | When to use |
| --- | --- | --- | --- |
| **Natural language** | `q` | **3 credits** | Exploration, agent tool-calls, when the user phrases the filter |
| **Structured SQL-like** | `where` + `order_by` | **1 credit** | Production, scheduled jobs, anything repeated |

**`q` overrides everything.** If `q` is present, `where`, `order_by`, `desc`, `limit` and
`offset` are all ignored. Do not send both and expect them to combine.

For repeated queries, use structured mode: it is 3× cheaper and deterministic. Use `q` once
during exploration, read back the `llm_translation` field in the response to see the
structured query it produced, then hardcode that. That single trick can cut a screener-heavy
project's credit burn by two thirds.

## ⚠️ The screener is a filter, not a data fetcher

**This is the single most important thing to know about this endpoint, and it is easy to miss.**

`/v2/companies/` returns only three fields per row:

```json
{
  "results": [
    {
      "symbol": "BBCA.JK",
      "company_name": "PT Bank Central Asia Tbk.",
      "query_values": { "sub_sector": "Banks", "market_cap": 753611199412500 }
    }
  ],
  "pagination": { "total_count": 48, "showing": 1, "limit": 3, "offset": 0,
                  "has_next": true, "has_previous": false,
                  "next_offset": 3, "previous_offset": null },
  "llm_translation": { "…": "…" }
}
```

The OpenAPI schema for `CompanyScreenerItem` confirms it: `symbol`, `company_name`, and a
nullable `query_values`. **You can filter on 219 fields but the response does not contain
them.** Screening for `roe_ttm > 0.15` gives you a list of tickers, not their ROEs.

### The workaround: `include_query_values=true`

`query_values` echoes back **the values of the fields your query referenced**. So to get a
metric out of the screener, mention it in the query and turn the flag on:

```bash
curl -H "$AUTH" --get "https://api.sectors.app/v2/companies/" \
  --data-urlencode "where=roe_ttm > 0 and pe_ttm > 0 and der_mrq > 0 and market_cap > 1000000000000" \
  --data-urlencode "order_by=-market_cap" \
  --data-urlencode "limit=200" \
  --data-urlencode "include_query_values=true"
```

Every field named in `where` or `order_by` comes back inside `query_values` for each row —
still **1 credit** for up to 200 companies. That makes the screener a genuinely cheap bulk
metric source, but only for fields you deliberately referenced.

> The parameter's own description says it shows "the interpreted year and country extracted
> from the query", which undersells it — the official example clearly returns the queried
> field values (`sub_sector`, `market_cap`). Verify the exact behaviour on your first live
> call and adjust; it is 1 credit to find out and it determines your whole data architecture.

### If you need fields you can't express as a filter

Your options, cheapest first:

| Need | Approach | Cost |
| --- | --- | --- |
| Metrics you can name in a `where` clause | `include_query_values=true` | 1 credit / 200 companies |
| Latest close for the whole market | `/v2/close/` | ~32 credits for ~942 tickers |
| Free float for the whole market | `/v2/free-float/` | 1 credit / 100 companies |
| Gainers and losers with prices | `/v2/companies/top-changes/` | 1 credit per classification × period |
| Deep per-company data | `/v2/company/report/{symbol}/?sections=…` | 1 credit per section **per company** |

The last row is the trap: a 200-company scoring pipeline built on company reports costs at
least 200 credits, and 1,600 if you let `sections` default. Build the score out of screener
fields wherever the metric exists there.

---

Set `include_query_values=true` to have the response include a `query_values` object showing
the year and country the natural-language parser inferred — useful for debugging why a
query returned the wrong period.

## Parameters

| Param | Type | Notes |
| --- | --- | --- |
| `q` | string | Natural language, e.g. `top 10 tech companies by revenue in 2023`. Overrides all others |
| `where` | string | SQL-like conditions |
| `order_by` | string | Field(s) to sort by, **comma-separated for multi-level sorting with per-column direction** — e.g. `-total_yield[2024], market_cap`. **`-` prefix = descending**. Supports arithmetic |
| `desc` | boolean | Legacy; prefer the `-` prefix |
| `limit` | integer | **Max 200** |
| `offset` | integer | Pagination |
| `include_query_values` | boolean | Returns the interpreted year/country from a `q` query |

## Syntax

**Operators:** `=`, `!=`, `>`, `>=`, `<`, `<=`, `like`, `in`, **`is not null`**
**Logic:** combine with `and` / `or`, and **group with parentheses** — `(a and b) or c`
**Strings:** single or double quotes — `sector = 'Technology'`
**Lists (for `in`):** `tags in ['blue-chip', 'dividend']`
**Yearly / forecast data:** bracket notation — `revenue[2023]`, `forecast_eps_growth[2025]`
**Quarterly data:** `field[Qi-YYYY]` — `revenue_q[Q1-2024]`
**Arithmetic:** allowed on both sides — `revenue[2024] / total_assets[2024] > 0.5`,
`revenue[2024] > revenue[2023] * 1.2`. In `order_by`, an arithmetic expression **must be
parenthesised** — the 2026-01-09 changelog added "parentheses forcing for arithmetic expression
on `order_by` … to avoid ambiguity with the negative sign", since `-` is also the descending
prefix.

> **Where each construct is documented, and where it is not.** The spec's own *Syntax and
> Operators* accordion lists only `=`, `!=`, `>`, `>=`, `<`, `<=`, `like`, `in` and `and`/`or`.
> The three constructs beyond that list — `is not null`, parenthesised groups, and
> multi-column `order_by` — are evidenced instead by the **Deterministic Query Builder**, whose
> generated example is captured verbatim in
> [`99-raw/authenticated-session-captures.md`](../99-raw/authenticated-session-captures.md):
> `where=(sub_sector="banks" and eps[2024]>0 and total_yield[2024] is not null)&order_by=-total_yield[2024], -market_cap`.
> **`is null` is not attested anywhere** — not in the spec, not in the query builder, not in
> `llms-full.txt`. It is the obvious complement of `is not null` and probably works, but an
> earlier draft of this page listed it as documented and that was an assumption, not a finding.
> Treat it as unverified until a live call confirms it.

> **Smart FY handling.** To account for reporting lag, "latest year" queries made between
> January and April default to the **previous audited year** — a query in early 2026 uses 2024
> data. Pin the year explicitly in any year-over-year calculation.

> Filtering by **sector/industry slugs** gives far more precise natural-language results.
> Get the valid slugs from `/v2/subsectors/`, `/v2/industries/`, `/v2/subindustries/`.

---

## Available fields

**219 queryable fields** across six categories.
(The pricing page offers to "filter companies by more than 500 financial metrics" — that counts each year and quarter
of the bracketed fields as its own metric.)

### Direct Fields (Top-level columns) — 24 fields

Query directly with standard operators (`=`, `!=`, `>`, `<`, `like`, `in`). String comparisons are case-insensitive.

```
where=market_cap > 500000000000000
where=company_name like '%energi%'
where=sector = 'Financials' and listing_date > '2005-01-01'
```

| Field | Description |
| --- | --- |
| `symbol` | IDX ticker symbol (e.g. BBCA, TLKM) |
| `company_name` | Full registered company name |
| `listing_board` | IDX board: Main, Development, or Acceleration |
| `industry` | IDX industry classification |
| `sub_industry` | IDX sub-industry classification |
| `sector` | IDX sector classification (broader than industry) |
| `sub_sector` | IDX sub-sector classification |
| `market_cap` | Market capitalisation in IDR |
| `market_cap_rank` | Rank by market cap among all IDX companies (1 = largest) |
| `employee_num` | Total number of employees |
| `employee_num_rank` | Rank by employee count among all IDX companies |
| `listing_date` | Date the company was first listed on IDX |
| `last_ex_dividend_date` | Most recent ex-dividend date |
| `last_close_price` | Latest closing price in IDR |
| `daily_close_change` | Day-over-day closing price change as a decimal |
| `forward_pe` | Forward price-to-earnings ratio based on next year earnings estimate |
| `intrinsic_value` | Estimated intrinsic value per share in IDR |
| `esg_score` | ESG (Environmental, Social, Governance) composite score |
| `yield_ttm` | Dividend yield over the trailing twelve months |
| `dividend_ttm` | Total dividends paid per share over the trailing twelve months in IDR |
| `payout_ratio` | Proportion of earnings paid out as dividends |
| `cash_payout_ratio` | Proportion of free cash flow paid out as dividends |
| `yoy_quarter_earnings_growth` | Year-over-year earnings growth based on the most recent quarter |
| `yoy_quarter_revenue_growth` | Year-over-year revenue growth based on the most recent quarter |

### Array Fields — 3 fields

Query with the `in` operator — it checks whether any of your values exist in the array.

```
where=indices in ['LQ45', 'IDX30']
where=tags in ['52-w-high', 'public-float-under-25']
```

| Field | Description |
| --- | --- |
| `tags` | Analyst sentiment tags (e.g. 'bullish'). Filter with `in` operator. |
| `indices` | IDX indices this stock belongs to (e.g. LQ45, IDX30). Filter with `in` operator. |
| `affiliates` | Related company tickers (affiliates/group entities) |

### JSON Object Fields (Most Recent Data) — 31 fields

Stored as JSON but queried as if they were plain columns — the parser extracts the value for you.

```
where=pe_ttm < 15 and roe_ttm > 0.1
where=last_close_price < all_time_high_price
where=ytd_low_date > '2025-03-01'
```

| Field | Description |
| --- | --- |
| `pe_ttm` | Price-to-earnings ratio (trailing twelve months) |
| `pb_mrq` | Price-to-book ratio (most recent quarter) |
| `ps_ttm` | Price-to-sales ratio (trailing twelve months) |
| `dar_mrq` | Debt-to-assets ratio (most recent quarter) |
| `der_mrq` | Debt-to-equity ratio (most recent quarter) |
| `roa_ttm` | Return on assets (trailing twelve months) |
| `roe_ttm` | Return on equity (trailing twelve months) |
| `total_assets_mrq` | Total assets in IDR (most recent quarter) |
| `total_equity_mrq` | Total shareholders equity in IDR (most recent quarter) |
| `total_revenue_mrq` | Total revenue in IDR (most recent quarter) |
| `earnings_mrq` | Net profit/loss in IDR (most recent quarter) |
| `total_liabilities_mrq` | Total liabilities in IDR (most recent quarter) |
| `yearly_mcap_change` | Year-over-year market cap change as a decimal |
| `dividend_yield_avg_period` | Number of years used to compute average dividend yield |
| `dividend_yield_avg` | Average annual dividend yield over the period |
| `ytd_low_price` | Year-to-date lowest closing price in IDR |
| `ytd_low_date` | Date of the year-to-date lowest closing price |
| `ytd_high_price` | Year-to-date highest closing price in IDR |
| `ytd_high_date` | Date of the year-to-date highest closing price |
| `52_w_low_price` | 52-week lowest closing price in IDR |
| `52_w_low_date` | Date of the 52-week lowest closing price |
| `52_w_high_price` | 52-week highest closing price in IDR |
| `52_w_high_date` | Date of the 52-week highest closing price |
| `90_d_low_price` | 90-day lowest closing price in IDR |
| `90_d_low_date` | Date of the 90-day lowest closing price |
| `90_d_high_price` | 90-day highest closing price in IDR |
| `90_d_high_date` | Date of the 90-day highest closing price |
| `all_time_low_price` | All-time lowest closing price in IDR |
| `all_time_low_date` | Date of the all-time lowest closing price |
| `all_time_high_price` | All-time highest closing price in IDR |
| `all_time_high_date` | Date of the all-time highest closing price |

### Yearly JSON Fields (Historical & Forecast Data) — 107 fields

**Require bracket notation `field[YYYY]`.** Support every numeric operator, field-to-field comparison, and arithmetic.

```
where=revenue[2023] > earnings[2023] * 5
where=roe[2023] > 0.15 and roe[2022] > 0.15
where=pe[2024] < pe_peer_avg[2024]
```

| Field | Description |
| --- | --- |
| `eps` | Earnings per share for the year. Use: `eps[2024]`. |
| `eps_growth` | Year-over-year EPS growth rate. Use: `eps_growth[2024]`. |
| `total_dividend` | Total dividends paid per share for the year. Use: `total_dividend[2024]`. |
| `total_yield` | Total dividend yield for the year. Use: `total_yield[2024]`. |
| `earnings` | Annual net profit/loss in IDR. Use: `earnings[2024]`. |
| `allowance_for_loans` | Allowance for loan losses in IDR. Use: `allowance_for_loans[2024]`. (banking) |
| `capital_expenditure` | Capital expenditure in IDR. Use: `capital_expenditure[2024]`. |
| `cash_and_equivalents` | Cash and cash equivalents in IDR. Use: `cash_and_equivalents[2024]`. |
| `cash_inflow` | Total cash inflow in IDR. Use: `cash_inflow[2024]`. |
| `cash_only` | Cash excluding equivalents in IDR. Use: `cash_only[2024]`. |
| `cash_outflow` | Total cash outflow in IDR. Use: `cash_outflow[2024]`. |
| `core_capital_tier1` | Tier 1 core capital in IDR. Use: `core_capital_tier1[2024]`. (banking) |
| `cost_of_revenue` | Cost of goods sold / cost of revenue in IDR. Use: `cost_of_revenue[2024]`. |
| `credit_rwa` | Credit risk-weighted assets in IDR. Use: `credit_rwa[2024]`. (banking) |
| `current_account` | Current account deposits in IDR. Use: `current_account[2024]`. (banking) |
| `current_assets` | Total current assets in IDR. Use: `current_assets[2024]`. |
| `current_liabilities` | Total current liabilities in IDR. Use: `current_liabilities[2024]`. |
| `earnings_before_tax` | Earnings before income tax in IDR. Use: `earnings_before_tax[2024]`. |
| `ebit` | Earnings before interest and tax in IDR. Use: `ebit[2024]`. |
| `ebitda` | Earnings before interest, tax, depreciation and amortisation in IDR. Use: `ebitda[2024]`. |
| `end_cash_position` | Ending cash position from the cash flow statement in IDR. Use: `end_cash_position[2024]`. |
| `financing_cash_flow` | Net cash from financing activities in IDR. Use: `financing_cash_flow[2024]`. |
| `fixed_assets` | Net property, plant and equipment in IDR. Use: `fixed_assets[2024]`. |
| `free_cash_flow` | Operating cash flow minus capex in IDR. Use: `free_cash_flow[2024]`. |
| `gross_loan` | Gross loan portfolio before allowances in IDR. Use: `gross_loan[2024]`. (banking) |
| `gross_profit` | Revenue minus cost of revenue in IDR. Use: `gross_profit[2024]`. |
| `high_quality_liquid_asset` | High-quality liquid assets (HQLA) held in IDR. Use: `high_quality_liquid_asset[2024]`. (banking) |
| `interest_expense` | Total interest expense in IDR. Use: `interest_expense[2024]`. |
| `interest_expense_non_operating` | Non-operating interest expense in IDR. Use: `interest_expense_non_operating[2024]`. |
| `interest_income` | Total interest income in IDR. Use: `interest_income[2024]`. |
| `inventories` | Inventories on the balance sheet in IDR. Use: `inventories[2024]`. |
| `investing_cash_flow` | Net cash from investing activities in IDR. Use: `investing_cash_flow[2024]`. |
| `market_rwa` | Market risk-weighted assets in IDR. Use: `market_rwa[2024]`. (banking) |
| `net_cash_flow` | Net change in cash for the period in IDR. Use: `net_cash_flow[2024]`. |
| `net_interest_income` | Interest income minus interest expense in IDR. Use: `net_interest_income[2024]`. (banking) |
| `net_loan` | Net loans after allowances in IDR. Use: `net_loan[2024]`. (banking) |
| `net_premium_income` | Net insurance premium income in IDR. Use: `net_premium_income[2024]`. (insurance) |
| `non_current_liabilities` | Long-term liabilities in IDR. Use: `non_current_liabilities[2024]`. |
| `non_interest_bearing_liabilities` | Liabilities that do not accrue interest in IDR. Use: `non_interest_bearing_liabilities[2024]`. (banking) |
| `non_interest_income` | Fee and commission income outside of interest in IDR. Use: `non_interest_income[2024]`. (banking) |
| `non_loan_assets` | Total assets excluding loans in IDR. Use: `non_loan_assets[2024]`. (banking) |
| `non_loan_earning_assets` | Interest-earning assets excluding loans in IDR. Use: `non_loan_earning_assets[2024]`. (banking) |
| `non_loan_non_earning_assets` | Non-earning assets excluding loans in IDR. Use: `non_loan_non_earning_assets[2024]`. (banking) |
| `non_operating_income_or_loss` | Income or losses outside core operations in IDR. Use: `non_operating_income_or_loss[2024]`. |
| `operating_cash_flow` | Net cash generated from core operations in IDR. Use: `operating_cash_flow[2024]`. |
| `operating_expense` | Total operating expenses in IDR. Use: `operating_expense[2024]`. |
| `operating_pnl` | Operating profit/loss (revenue minus operating expenses) in IDR. Use: `operating_pnl[2024]`. |
| `operational_rwa` | Operational risk-weighted assets in IDR. Use: `operational_rwa[2024]`. (banking) |
| `other_interest_bearing_liabilities` | Other interest-bearing liabilities excluding deposits in IDR. Use: `other_interest_bearing_liabilities[2024]`. (banking) |
| `outstanding_shares` | Total shares outstanding. Use: `outstanding_shares[2024]`. |
| `prepaid_assets` | Prepaid expenses and other current assets in IDR. Use: `prepaid_assets[2024]`. |
| `premium_expense` | Insurance premium expenses in IDR. Use: `premium_expense[2024]`. (insurance) |
| `premium_income` | Gross insurance premium income in IDR. Use: `premium_income[2024]`. (insurance) |
| `provision` | Provision for loan losses or liabilities in IDR. Use: `provision[2024]`. |
| `realized_capital_goods_investment` | Realised investment in capital goods in IDR. Use: `realized_capital_goods_investment[2024]`. |
| `retained_earnings` | Cumulative retained earnings on balance sheet in IDR. Use: `retained_earnings[2024]`. |
| `revenue` | Annual total revenue in IDR. Use: `revenue[2024]`. |
| `savings_account` | Savings account deposits in IDR. Use: `savings_account[2024]`. (banking) |
| `supplementary_capital_tier2` | Tier 2 supplementary capital in IDR. Use: `supplementary_capital_tier2[2024]`. (banking) |
| `tax` | Income tax expense in IDR. Use: `tax[2024]`. |
| `time_deposit` | Time deposit liabilities in IDR. Use: `time_deposit[2024]`. (banking) |
| `total_assets` | Total assets on the balance sheet in IDR. Use: `total_assets[2024]`. |
| `total_capital` | Total regulatory capital in IDR. Use: `total_capital[2024]`. (banking) |
| `total_cash_and_due_from_banks` | Cash and amounts due from other banks in IDR. Use: `total_cash_and_due_from_banks[2024]`. (banking) |
| `total_debt` | Total interest-bearing debt in IDR. Use: `total_debt[2024]`. |
| `total_deposit` | Total customer deposits in IDR. Use: `total_deposit[2024]`. (banking) |
| `total_equity` | Total shareholders equity in IDR. Use: `total_equity[2024]`. |
| `total_liabilities` | Total liabilities on the balance sheet in IDR. Use: `total_liabilities[2024]`. |
| `total_risk_weighted_asset` | Total risk-weighted assets in IDR. Use: `total_risk_weighted_asset[2024]`. (banking) |
| `special_mention_loan` | Special mention (watch-list) loans in IDR. Use: `special_mention_loan[2024]`. (banking) |
| `non_performing_loan` | Non-performing loans (NPL) in IDR. Use: `non_performing_loan[2024]`. (banking) |
| `restructured_loan_current` | Restructured loans currently performing in IDR. Use: `restructured_loan_current[2024]`. (banking) |
| `forecast_eps_growth` | Analyst consensus EPS growth forecast. Use: `forecast_eps_growth[2025]`. |
| `forecast_revenue_growth` | Analyst consensus revenue growth forecast. Use: `forecast_revenue_growth[2025]`. |
| `forecast_eps_estimate` | Analyst consensus EPS estimate in IDR. Use: `forecast_eps_estimate[2025]`. |
| `forecast_revenue_estimate` | Analyst consensus revenue estimate in IDR. Use: `forecast_revenue_estimate[2025]`. |
| `pe` | Price-to-earnings ratio for the year. Use: `pe[2024]`. |
| `pb` | Price-to-book ratio for the year. Use: `pb[2024]`. |
| `ps` | Price-to-sales ratio for the year. Use: `ps[2024]`. |
| `pcf` | Price-to-cash-flow ratio for the year. Use: `pcf[2024]`. |
| `peg` | Price/earnings-to-growth ratio for the year. Use: `peg[2024]`. |
| `enterprise_to_ebitda` | Enterprise value to EBITDA for the year. Use: `enterprise_to_ebitda[2024]`. |
| `enterprise_to_revenue` | Enterprise value to revenue for the year. Use: `enterprise_to_revenue[2024]`. |
| `pb_peer_avg` | Peer average price-to-book ratio for the year. Use: `pb_peer_avg[2024]`. |
| `pe_peer_avg` | Peer average price-to-earnings ratio for the year. Use: `pe_peer_avg[2024]`. |
| `ps_peer_avg` | Peer average price-to-sales ratio for the year. Use: `ps_peer_avg[2024]`. |
| `debt_to_asset_ratio` | Total debt divided by total assets. Use: `debt_to_asset_ratio[2024]`. |
| `debt_to_equity_ratio` | Total debt divided by shareholders equity. Use: `debt_to_equity_ratio[2024]`. |
| `cash_flow_to_debt_ratio` | Operating cash flow divided by total debt. Use: `cash_flow_to_debt_ratio[2024]`. |
| `interest_coverage_ratio` | EBIT divided by interest expense. Use: `interest_coverage_ratio[2024]`. |
| `current_ratio` | Current assets divided by current liabilities. Use: `current_ratio[2024]`. |
| `operating_cash_flow_margin` | Operating cash flow as a percentage of revenue. Use: `operating_cash_flow_margin[2024]`. |
| `fixed_asset_turnover` | Revenue divided by net fixed assets. Use: `fixed_asset_turnover[2024]`. |
| `total_asset_turnover` | Revenue divided by total assets. Use: `total_asset_turnover[2024]`. |
| `roa` | Return on assets for the year. Use: `roa[2024]`. |
| `roe` | Return on equity for the year. Use: `roe[2024]`. |
| `net_profit_margin` | Net profit as a percentage of revenue. Use: `net_profit_margin[2024]`. |
| `gross_profit_margin` | Gross profit as a percentage of revenue. Use: `gross_profit_margin[2024]`. |
| `operating_profit_margin` | Operating profit as a percentage of revenue. Use: `operating_profit_margin[2024]`. |
| `capital_adequacy_ratio` | Regulatory capital as a percentage of risk-weighted assets. Use: `capital_adequacy_ratio[2024]`. (banking) |
| `casa_ratio` | Current and savings account deposits as a share of total deposits. Use: `casa_ratio[2024]`. (banking) |
| `leverage_ratio` | Tier 1 capital divided by total exposure. Use: `leverage_ratio[2024]`. (banking) |
| `loan_to_deposit_ratio` | Net loans divided by total deposits. Use: `loan_to_deposit_ratio[2024]`. (banking) |
| `liquidity_coverage_ratio` | HQLA divided by net cash outflows over 30 days. Use: `liquidity_coverage_ratio[2024]`. (banking) |
| `efficiency_ratio` | Operating expenses divided by net revenue. Use: `efficiency_ratio[2024]`. |
| `net_interest_margin` | Net interest income as a percentage of earning assets. Use: `net_interest_margin[2024]`. (banking) |
| `cost_to_income_ratio` | Operating costs divided by operating income. Use: `cost_to_income_ratio[2024]`. |

### Quarterly Financial Data — 44 fields

**Require bracket notation `field[Qi-YYYY]`.** IDX only — SGX returns `400 QUARTERLY_NOT_SUPPORTED`.

```
where=revenue_q[Q1-2024] > 1000000000
where=earnings_q[Q4-2023] > earnings_q[Q3-2023]
```

| Field | Description |
| --- | --- |
| `revenue_q` | Quarterly revenue in IDR. Use: `revenue_q[Q1-2024]`. |
| `earnings_q` | Quarterly net profit/loss in IDR. Use: `earnings_q[Q1-2024]`. |
| `net_loan_q` | Quarterly net loans in IDR. Use: `net_loan_q[Q1-2024]`. (banking) |
| `gross_profit_q` | Quarterly gross profit in IDR. Use: `gross_profit_q[Q1-2024]`. |
| `time_deposit_q` | Quarterly time deposits in IDR. Use: `time_deposit_q[Q1-2024]`. (banking) |
| `operating_pnl_q` | Quarterly operating profit/loss in IDR. Use: `operating_pnl_q[Q1-2024]`. |
| `total_deposit_q` | Quarterly total deposits in IDR. Use: `total_deposit_q[Q1-2024]`. (banking) |
| `ebit_q` | Quarterly EBIT in IDR. Use: `ebit_q[Q1-2024]`. |
| `ebitda_q` | Quarterly EBITDA in IDR. Use: `ebitda_q[Q1-2024]`. |
| `earnings_before_tax_q` | Quarterly earnings before tax in IDR. Use: `earnings_before_tax_q[Q1-2024]`. |
| `tax_q` | Quarterly income tax expense in IDR. Use: `tax_q[Q1-2024]`. |
| `cost_of_revenue_q` | Quarterly cost of revenue in IDR. Use: `cost_of_revenue_q[Q1-2024]`. |
| `current_account_q` | Quarterly current account deposits in IDR. Use: `current_account_q[Q1-2024]`. (banking) |
| `interest_income_q` | Quarterly interest income in IDR. Use: `interest_income_q[Q1-2024]`. (banking) |
| `premium_expense_q` | Quarterly premium expenses in IDR. Use: `premium_expense_q[Q1-2024]`. (insurance) |
| `savings_account_q` | Quarterly savings account deposits in IDR. Use: `savings_account_q[Q1-2024]`. (banking) |
| `interest_expense_q` | Quarterly interest expense in IDR. Use: `interest_expense_q[Q1-2024]`. |
| `operating_expense_q` | Quarterly operating expenses in IDR. Use: `operating_expense_q[Q1-2024]`. |
| `non_operating_income_or_loss_q` | Quarterly non-operating income/loss in IDR. Use: `non_operating_income_or_loss_q[Q1-2024]`. |
| `interest_expense_non_operating_q` | Quarterly non-operating interest expense in IDR. Use: `interest_expense_non_operating_q[Q1-2024]`. |
| `non_interest_bearing_liabilities_q` | Quarterly non-interest-bearing liabilities in IDR. Use: `non_interest_bearing_liabilities_q[Q1-2024]`. (banking) |
| `realized_capital_goods_investment_q` | Quarterly realised capital goods investment in IDR. Use: `realized_capital_goods_investment_q[Q1-2024]`. |
| `other_interest_bearing_liabilities_q` | Quarterly other interest-bearing liabilities in IDR. Use: `other_interest_bearing_liabilities_q[Q1-2024]`. (banking) |
| `total_assets_q` | Quarterly total assets in IDR. Use: `total_assets_q[Q1-2024]`. |
| `current_assets_q` | Quarterly current assets in IDR. Use: `current_assets_q[Q1-2024]`. |
| `total_liabilities_q` | Quarterly total liabilities in IDR. Use: `total_liabilities_q[Q1-2024]`. |
| `net_premium_income_q` | Quarterly net premium income in IDR. Use: `net_premium_income_q[Q1-2024]`. (insurance) |
| `allowance_for_loans_q` | Quarterly allowance for loan losses in IDR. Use: `allowance_for_loans_q[Q1-2024]`. (banking) |
| `current_liabilities_q` | Quarterly current liabilities in IDR. Use: `current_liabilities_q[Q1-2024]`. |
| `non_current_liabilities_q` | Quarterly non-current liabilities in IDR. Use: `non_current_liabilities_q[Q1-2024]`. |
| `total_equity_q` | Quarterly total equity in IDR. Use: `total_equity_q[Q1-2024]`. |
| `total_debt_q` | Quarterly total debt in IDR. Use: `total_debt_q[Q1-2024]`. |
| `cash_only_q` | Quarterly cash (excluding equivalents) in IDR. Use: `cash_only_q[Q1-2024]`. |
| `provision_q` | Quarterly provision for losses in IDR. Use: `provision_q[Q1-2024]`. |
| `gross_loan_q` | Quarterly gross loans before allowances in IDR. Use: `gross_loan_q[Q1-2024]`. (banking) |
| `total_cash_and_due_from_banks_q` | Quarterly cash and amounts due from banks in IDR. Use: `total_cash_and_due_from_banks_q[Q1-2024]`. (banking) |
| `operating_cash_flow_q` | Quarterly operating cash flow in IDR. Use: `operating_cash_flow_q[Q1-2024]`. |
| `investing_cash_flow_q` | Quarterly investing cash flow in IDR. Use: `investing_cash_flow_q[Q1-2024]`. |
| `financing_cash_flow_q` | Quarterly financing cash flow in IDR. Use: `financing_cash_flow_q[Q1-2024]`. |
| `net_interest_income_q` | Quarterly net interest income in IDR. Use: `net_interest_income_q[Q1-2024]`. (banking) |
| `non_interest_income_q` | Quarterly non-interest income in IDR. Use: `non_interest_income_q[Q1-2024]`. (banking) |
| `free_cash_flow_q` | Quarterly free cash flow in IDR. Use: `free_cash_flow_q[Q1-2024]`. |
| `premium_income_q` | Quarterly gross premium income in IDR. Use: `premium_income_q[Q1-2024]`. (insurance) |
| `capital_expenditure_q` | Quarterly capital expenditure in IDR. Use: `capital_expenditure_q[Q1-2024]`. |

### JSON List Fields — 10 fields

The query checks whether **any** object in the list matches. `=` or `like` for strings, numeric operators for numbers.

```
where=major_shareholders_name like 'PT%' and major_shareholders_share_percentage > 0.1
where=key_executives_name = 'Prajogo Pangestu'
```

| Field | Description |
| --- | --- |
| `key_executives_name` | Filter by executive name in the key_executives list. Use `like` operator. |
| `key_executives_position` | Filter by executive position/title in the key_executives list. Use `like` operator. |
| `executives_shareholdings_name` | Filter by executive name in the shareholdings list. |
| `executives_shareholdings_share_amount` | Filter by executive share amount (number of shares). |
| `executives_shareholdings_share_percentage` | Filter by executive ownership percentage. |
| `major_shareholders_name` | Filter by major shareholder name. Use `like` operator. |
| `major_shareholders_share_value` | Filter by major shareholder share value in IDR. |
| `major_shareholders_share_amount` | Filter by major shareholder number of shares. |
| `major_shareholders_share_percentage` | Filter by major shareholder ownership percentage. |
| `free_float` | Public (non-insider) ownership percentage from major_shareholders. Value is a decimal (0.45 = 45%). |

---

## Verified against the live Query Builder

Sectors ships a **Deterministic Query Builder** at
[sectors.app/api](https://sectors.app/api) → API Playground → Deterministic Query Builder
(login required). It generates `where` / `order_by` clauses from a visual condition builder
with AND/OR groups, and shows the equivalent SQL, the generated URL, and ready-to-paste
Python. It has separate IDX and SGX modes.

Its own worked example — confirming several things the written docs do not state:

```
GET https://api.sectors.app/v2/companies/
  ?where=sub_sector = "banks"
     and revenue[2024] > revenue[2022] * 1.21
     and total_yield[2024] is not null
  &order_by=-total_yield[2024], market_cap
  &limit=10
```

> "Retrieves banks whose `revenue[2024] > revenue[2022] * 1.21` (21% growth vs 2022 — a CAGR
> of 10% per year) and are dividend-paying (`total_yield[2024] is not null`). Results ordered
> by `total_yield[2024]` (desc), then `market_cap` (asc)."

What that confirms:

- **`is not null` / `is null` are valid operators** (see the correction below)
- **`order_by` takes a comma-separated list**, each with its own direction
- **Parentheses group conditions** — the builder emits `WHERE (a and b and c)`
- The underlying table is referred to as **`sectors_v2`** in the generated SQL
- **"Generate CSV from Query" costs 1 API credit** and is Insider-only

The builder is the fastest way to author a complex `where` clause without burning credits on
trial and error — compose visually, copy the URL, then run it once.

> ⚠️ **Playground Demo Mode.** Signed out — or signed in without an Insider plan — the
> Playground returns **mock data**, not live data: *"Whilst in Demo Mode, the returned values
> are mock data to demonstrate each API endpoint's functionality."* The shapes are right; the
> numbers are not. Don't screenshot Demo Mode output as evidence of a working product.

## Worked query patterns

Copy-paste starting points. All are 1 credit each in structured mode.

```bash
BASE=https://api.sectors.app/v2/companies/
AUTH="Authorization: $SECTORS_API_KEY"

# Large-cap banks, most valuable first
curl -H "$AUTH" --get "$BASE" \
  --data-urlencode "where=sub_sector = 'banks' and market_cap > 50000000000000" \
  --data-urlencode "order_by=-market_cap" --data-urlencode "limit=20"

# Quality-at-a-price: profitable, cheap, low leverage
curl -H "$AUTH" --get "$BASE" \
  --data-urlencode "where=roe_ttm > 0.15 and pe_ttm < 12 and der_mrq < 1.0" \
  --data-urlencode "order_by=-roe_ttm"

# Two consecutive years of >15% ROE — durable quality, not a one-off
curl -H "$AUTH" --get "$BASE" \
  --data-urlencode "where=roe[2024] > 0.15 and roe[2023] > 0.15 and roe[2022] > 0.15"

# Trading below peer-average PE (relative value inside a sector)
curl -H "$AUTH" --get "$BASE" \
  --data-urlencode "where=pe[2024] < pe_peer_avg[2024] and market_cap > 5000000000000"

# Revenue grew >20% year over year, computed inside the query
curl -H "$AUTH" --get "$BASE" \
  --data-urlencode "where=revenue[2024] > revenue[2023] * 1.2"

# Quarterly momentum: Q4 earnings beat Q3
curl -H "$AUTH" --get "$BASE" \
  --data-urlencode "where=earnings_q[Q4-2024] > earnings_q[Q3-2024]"

# Dividend payers inside LQ45 with a sustainable payout
curl -H "$AUTH" --get "$BASE" \
  --data-urlencode "where=indices in ['LQ45'] and yield_ttm > 0.04 and payout_ratio < 0.8" \
  --data-urlencode "order_by=-yield_ttm"

# Off their highs but still profitable — drawdown screen
curl -H "$AUTH" --get "$BASE" \
  --data-urlencode "where=last_close_price < 52_w_high_price * 0.7 and roe_ttm > 0.1"

# Bank-specific: strong CASA, healthy capital
curl -H "$AUTH" --get "$BASE" \
  --data-urlencode "where=sub_sector = 'banks' and casa_ratio[2024] > 0.6 and capital_adequacy_ratio[2024] > 0.2"

# Controlled by a specific major shareholder
curl -H "$AUTH" --get "$BASE" \
  --data-urlencode "where=major_shareholders_name like 'PT%' and major_shareholders_share_percentage > 0.5"

# Low free float — thin, easily moved names
curl -H "$AUTH" --get "$BASE" \
  --data-urlencode "where=free_float < 0.2 and market_cap > 1000000000000"

# Capital efficiency, expressed as arithmetic
curl -H "$AUTH" --get "$BASE" \
  --data-urlencode "where=revenue[2024] / total_assets[2024] > 0.5" \
  --data-urlencode "order_by=-revenue[2024]"
```

## Building a defensible Track 03 score

Track 03 rejects "raw Sectors data in a different visual form". The screener is how you
avoid that trap cheaply: a **composite score with stated weights**, computed over fields you
pulled in one or two structured queries, is derived insight by definition.

A worked shape — one query, 1 credit, then all the derivation happens locally:

```python
import os, requests

# Every metric the score uses is named in `where` so that query_values echoes it
# back — the screener does not return fields you did not reference.
WHERE = (
    "market_cap > 1000000000000 "
    "and roe_ttm > 0 and pe_ttm > 0 and der_mrq > 0"
)

payload = requests.get(
    "https://api.sectors.app/v2/companies/",
    headers={"Authorization": os.environ["SECTORS_API_KEY"]},
    params={
        "where": WHERE,
        "order_by": "-market_cap",
        "limit": 200,
        "include_query_values": "true",
    },
    timeout=30,
).json()

rows = payload["results"]

def percentile_rank(values, value):
    ranked = sorted(v for v in values if v is not None)
    if not ranked or value is None:
        return 0.0
    return sum(1 for v in ranked if v <= value) / len(ranked)

# Your own weights are the thing being judged — state and defend them.
WEIGHTS = {"quality": 0.4, "value": 0.35, "safety": 0.25}

def metric(row, name):
    """Screener metrics arrive inside query_values, not on the row itself."""
    return (row.get("query_values") or {}).get(name)

roes = [metric(r, "roe_ttm") for r in rows]
pes  = [metric(r, "pe_ttm")  for r in rows]
ders = [metric(r, "der_mrq") for r in rows]

for row in rows:
    quality = percentile_rank(roes, metric(row, "roe_ttm"))
    value   = 1 - percentile_rank(pes,  metric(row, "pe_ttm"))   # cheaper is better
    safety  = 1 - percentile_rank(ders, metric(row, "der_mrq"))  # less levered is better
    row["composite"] = round(
        WEIGHTS["quality"] * quality
        + WEIGHTS["value"] * value
        + WEIGHTS["safety"] * safety, 4)

top = sorted(rows, key=lambda r: -r["composite"])[:20]
```

Two hundred companies, three factors, one credit. Spend the rest of your budget on the
things that need it.

> The `where` clause does double duty here: it filters *and* it selects which metrics come
> back. Adding a field to the score means adding it to `where` — that is the screener's
> projection mechanism, and there isn't another one.
>
> **Correction (verified in the live Deterministic Query Builder):** null filtering *is*
> supported in `where`, as **`is not null` / `is null`** — an earlier draft of this document
> wrongly said it was not. Sectors' own generated example is
> `total_yield[2024] is not null`. Filtering nulls server-side is cheaper than filtering
> locally, so prefer it.
>
> `percentile_rank` above still skips `None` defensively, which is worth keeping: many fields
> are genuinely null where the metric is undefined (negative earnings gives no meaningful PE).
