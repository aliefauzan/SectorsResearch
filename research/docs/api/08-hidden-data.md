# What's Actually Inside the Payloads

> Third-pass finding. The endpoint summaries in the docs describe *what an endpoint is for*.
> They do not describe what comes back. Reading all 70 official example payloads field by
> field turned up data that is nowhere in the endpoint descriptions — including several of
> the most differentiated things Sectors has.
>
> Everything here is verified against the fixtures in
> [`harness/fixtures/`](../../harness/fixtures/).

---

## ⚠️ The screener does not return the fields you filter on

Covered in full in [`03-screener-query-language.md`](03-screener-query-language.md), repeated
here because it changes architecture: `/v2/companies/` returns `symbol`, `company_name` and a
nullable `query_values` — nothing else. Filtering on 219 fields gives you a **list of
tickers**, not their metrics. Name the fields in `where` and pass
`include_query_values=true` to have their values echoed back.

Plan your data flow around that before you write the pipeline, not after.

---

## Company Report — what each of the eight sections actually contains

Billing is **1 credit per section**, so knowing which section holds what is directly worth
credits. From the official `BBCA` example:

### `overview` — 1 credit
Listing board, industry/sub-industry/sector/sub-sector, market cap **and its market-wide
rank**, registered address, employee count **and its rank**, listing date, website, phone,
investor-relations email, last close + date + daily change, ESG score, analyst `tags`, index
memberships, and **`affiliates`** — the business groups the company belongs to (for BBCA:
`["Djarum", "Hartono"]`).

Plus `all_time_price`, a nested object with eight date→price pairs: `ytd_low`, `ytd_high`,
`52_w_low`, `52_w_high`, `90_d_low`, `90_d_high`, `all_time_low`, `all_time_high`. **Each
carries the date it occurred**, not just the level — enough to compute drawdown and time-since-
high without touching the daily-price endpoint.

### `valuation` — 1 credit
Forward PE, **`intrinsic_value`** (a per-share DCF estimate), and `historical_valuation`: a
per-year array of `pb`, `pe`, `ps`, `pcf`, `peg`, `enterprise_to_ebitda`,
`enterprise_to_revenue` — **each alongside its peer average** (`pb_peer_avg`, `pe_peer_avg`,
`ps_peer_avg`). Relative valuation without computing the peer set yourself.

### `future` — 1 credit
`company_value_forecasts` (EPS and revenue estimates by year),
`company_growth_forecasts` (EPS and revenue growth vs a base year), and
`analyst_rating_breakdown`: `strong_buy`, `buy`, `hold`, `sell`, `strong_sell`, `n_analyst`,
`updated_on`. Analyst consensus, timestamped.

### `financials` — 1 credit
EPS, `historical_eps` by year, `historical_financials` per year (revenue, earnings, EBIT,
EBITDA, tax, net debt, provisions, and bank fields like `net_loan`), and
`historical_financial_ratio` — pre-computed ratio *groups* per year:
`capital`, `leverage`, `liquidity`, `efficiency`, `profitability`.

### `dividend` — 1 credit
`historical_dividends` keyed by year, each with a per-payment `breakdown` (`date`, `total`,
`yield`) plus `total_dividend` and `total_yield`; `upcoming_dividends`; `yield_ttm`;
`dividend_ttm`; `payout_ratio`; `cash_payout_ratio`; `last_ex_dividend_date`; and
`dividend_yield_avg` with the `period` (number of years) it averages over.

### `management` — 1 credit
`key_executives` (name, position) and **`executives_shareholdings`** — name, position,
`share_amount`, `share_percentage`. Insider ownership per executive.

### `ownership` — 1 credit · **the most under-advertised section in the API**
- `major_shareholders` — name, `share_value`, `share_amount`, `share_percentage`
- `top_transactions` — a dated snapshot of `top_buyers` and `top_sellers` **named institution by institution**, with `changeAmount`. The official BBCA example names *Fidelity Institutional Asset Management* as a buyer and *Fidelity Management & Research Company LLC* as a seller — this is institutional flow attributed to specific asset managers, not an anonymous aggregate
- `institutional_transaction_flow` — a dated series of `net_transaction`
- **`whale_investors`** — named individuals (the BBCA example returns `["Anthoni Salim"]`)
- **`conglomerates_group`** — the business group the company sits in (`["Djarum Group"]`)

None of `whale_investors`, `conglomerates_group` or `institutional_transaction_flow` appear
in the endpoint's own description. For one credit per company this is the cheapest ownership-
network data in the API, and it is the raw material for a conglomerate-mapping or
follow-the-whale product.

### `peers` — 1 credit
`peers_data.companies[]` — each peer with market cap, net income, pretax income, total
revenue/assets/equity/liabilities, employee count, `pb_mrq`, `pe_ttm`, `yearly_mcap_chg`,
a `group` marker (`["self"]` identifies the subject company), plus:

- **`point_summaries`** — Sectors' own scored assessment, e.g. `{"name": "value", "point": 10.5, "maxpoint": 18}`
- **`revenue_breakdown`**, **`int_income_breakdown`**, **`operating_expense_breakdown`** — class/category/amount rows, e.g. interest income split into `Loans & Deposits`, opex split into `Salaries & Benefits`

`group_name` gives the sector/industry/sub-sector/sub-industry the peer group was drawn from.
**One credit buys the whole peer set with financials** — far cheaper than fetching each peer's
report separately.

> **Budget consequence.** For most comparative work, `peers` (1 credit) beats N× `overview`
> (N credits). For ownership work, `ownership` (1 credit) beats anything else in the API.

---

## Shareholders Composition — 22 investor categories, split local vs foreign

`/v2/company/shareholders-composition/{symbol}/` costs **1 credit** and returns a monthly series
where each row carries **every investor category twice** — once local (`_l`), once foreign
(`_f`):

`insurance`, `corporate`, `pension_fund`, `financial_institutions`, `individual`,
`mutual_fund`, `securities_companies`, `foundation`, `other`, `total`

…plus `date`, `shares_number`, **`numbers_of_shareholders`** and
**`change_in_shareholders`**.

That is a monthly, category-level, local-vs-foreign ownership panel per company. The endpoint
description says only "Monthly shareholder breakdown by investor category". It is considerably
more than that — you can track, for example, foreign pension funds entering a name while
domestic retail exits, month by month.

---

## Corporate Actions — six action types, one credit

`/v2/company/corporate-actions/{symbol}/` (**1 credit**) returns a `corporate_actions` object
with six keys, each null when absent:

| Key | Contents |
| --- | --- |
| `agm` | `agm_date`, `agm_time`, `agm_place`, **`agm_result`** (the resolution text) |
| `dividend` | `ex_date`, `payment_date`, `dividend_amount`, `dividend_yield` |
| `stock_split` | `date`, `split_ratio` |
| `right_issue` | rights issues |
| `warrant` | warrants |
| `bonus` | bonus shares |
| `upcoming_dividend` | forward-looking |

`agm_result` is free text of what the meeting decided — unusual, and useful for an
event-driven or NLP project.

---

## Daily Transaction — it's full OHLC

The endpoint summary says "daily close price, volume, and market cap". The actual payload is:

```json
{"symbol": "BBCA.JK", "date": "2025-05-02", "open": 9000, "high": 9000,
 "low": 8850, "close": 8975, "volume": 92219000, "market_cap": 1095329638012500}
```

**`open`, `high` and `low` are there.** That makes candlestick charts, true-range and
gap-analysis possible on 1 credit per ticker per 90-day window — none of which the summary
suggests.

---

## Listing Performance — a complete IPO record

`/v2/listing-performance/{symbol}/` is described as "price change percentages since listing".
It also returns the entire book-building and offering history:

`shares_offered`, `percent_total_shares`, `book_building_start_date`, `book_building_end_date`,
`book_building_lower_bound`, `book_building_upper_bound`, `offering_start_date`,
`offering_end_date`, `offering_price`, `distribution_date`, `listing_date`,
**`prospectus_url`**, `additional_info_url`, plus `chg_7d` / `chg_30d` / `chg_90d` / `chg_365d`.

Enough for a full IPO-pricing study — did the offer price land at the top or bottom of the
book-building range, and how did that predict aftermarket performance? — for 1 credit per IPO.

---

## Quarterly Financials — sector-specific metrics are nested

Rows carry a `financials_sector_metrics` sub-object populated only for the relevant sector.
For banks that means `interest_income`, `interest_expense`, `net_interest_income`,
`gross_loan`, `allowance_for_loans`, `net_loan`, `total_earning_assets`, `current_account`,
`savings_account`, `time_deposit`, `total_deposit`, `other_interest_bearing_liabilities`,
`total_cash_and_due_from_banks`. Insurance companies get premium fields at the top level
(`premium_income`, `premium_expense`).

**Don't look for `net_interest_income` at the top level of the row** — it's one level down.

---

## Subsector Report — risk statistics you would otherwise compute

`/v2/subsector/report/{sub_sector}/`, 1 credit per section, six sections:

| Section | Notable contents |
| --- | --- |
| `statistics` | `total_companies`, `filtered_median_pe`, `filtered_weighted_avg_pe`, `min_company_pe`, `max_company_pe` |
| `market_cap` | totals and averages, `quarterly_market_cap` (prev vs current TTM), `mcap_summary` with `monthly_performance` and **`performance_quantile`** |
| `stability` | **`weighted_max_drawdown`**, **`weighted_rsd_close`** (relative standard deviation of closes) |
| `valuation` | `historical_valuation` keyed by year |
| `growth` | `weighted_avg_growth_data` by year, **`growth_forecasts`** by forward year |
| `companies` | `top_companies` bucketed into `top_mcap` / `top_growth` / `top_profit` / `top_revenue`, plus `top_change_companies` keyed by ticker |

Sector-level drawdown and dispersion, pre-computed. Building those yourself would mean
pulling daily prices for every company in the sector — dozens of credits versus one.

---

## Company Filings — the insider is named

`/v2/filings/` rows carry `title`, `body`, `source`, `timestamp`, `sector`, `sub_sector`,
`tags`, `symbol`, `transaction_type`, `holder_type`, **`holder_name`**, **`holding_before`**.

So you get who transacted, what type of holder they are, and their position before the trade —
enough to compute the position *after* and to track one insider across filings over time.

---

## News — pre-classified along eight analytical dimensions

`/v2/news/` rows: `title`, `body`, `source`, **`thumbnail`**, `timestamp`, `sector`,
`sub_sector`, `tags`, `symbols`, **`dimension`**.

`dimension` is the find. It is not a string — it's a scored object across eight analytical
themes:

```json
{"future": 0, "dividend": 0, "ownership": 0, "technical": 0,
 "valuation": 0, "financials": 0, "management": 0, "sustainability": 0}
```

**Sectors has already classified every article by what kind of news it is.** You can route
dividend news to one channel and ownership news to another, or weight a signal by whether the
coverage is about fundamentals or price action — without running a classifier of your own.
Nothing in the endpoint description mentions this field exists.

`body` carries article text (~500 characters in the official example, so treat it as a
summary-length extract rather than guaranteed full text — check length on live data before
building a summarizer around it). `thumbnail` is a CDN image URL, free visual polish for a
brief or digest product, which helps the 30% video score for zero effort.

---

## Mining — the ownership graph and the licence register

**`/v2/mining/companies/ownership/{slug}/`** returns `parents[]` and `subsidiaries[]`, each
with `name`, `slug`, **`symbol`** (the listed ticker, when the entity is listed) and
`percentage_ownership`. Because entries carry both a slug and a ticker, **the graph links
private mining entities to their listed parents** — a corporate-structure network you can
traverse. Very little else in the API does that.

**`/v2/mining/licenses/`** rows: `wiup_code`, `license_number`, `license_type`, `province`,
`city`, `license_effective_date`, **`license_expiry_date`**, `activity`, `licensed_area_ha`,
**`location`** (GeoJSON), `commodity_type`, `company_name`, `company_slug`, `cnc`
(clean-and-clear status), `generation`.

**`/v2/mining/sites/`** rows: `name`, `project_name`, `year`, `commodity_type`,
`production_volume`, `unit`, **`strip_ratio`**, `province`, `city`, `company_slug`,
`company_name`, `slug`.

**`/v2/mining/companies/performance/{slug}/`** returns `year`, **`available_years`** (so you
can discover coverage without guessing) and per-commodity `commodity_stats` including
`commodity_sub_type` (e.g. "Sub-bituminous & Metallurgical Coal"),
`mining_operation_status`, `production_volume`, `sales_volume`.

Licence expiry dates + GeoJSON locations + production volumes + an ownership graph linking
private operators to listed tickers is, as far as this research found, unavailable anywhere
else programmatically.

---

## Pagination envelope is consistent where it exists

Endpoints that paginate return the same object:

```json
{"total_count": 942, "showing": 1, "limit": 30, "offset": 0,
 "has_next": true, "has_previous": false, "next_offset": 30, "previous_offset": null}
```

`next_offset` means you never compute paging arithmetic yourself — loop until
`has_next` is false. `total_count` lets you calculate the credit cost of a full sweep
**before** you start it:

```python
first = get("/v2/close/", limit=30)
pages = -(-first["pagination"]["total_count"] // 30)   # ceiling division
print(f"full sweep costs {pages} credits")             # ~32
```

Run that once before any bulk pull.

---

## Summary — biggest finds

| Find | Why it matters |
| --- | --- |
| Screener returns only symbol + name | Changes your whole data architecture; use `include_query_values` |
| `ownership` section has whale investors + conglomerate groups | 1 credit for ownership-network data nobody advertises |
| `peers` returns full financials for the whole peer set | 1 credit instead of N |
| Shareholders composition is 22 categories × local/foreign, monthly | A real ownership panel, not a snapshot |
| Daily is full OHLC | Candlesticks and true range, not just a close line |
| Listing performance includes the full book-building record | IPO pricing studies for 1 credit |
| Subsector `stability` gives weighted drawdown and dispersion | Sector risk stats for 1 credit instead of dozens |
| Mining ownership links private entities to listed tickers | A traversable corporate graph |
| Filings name the holder and prior holding | Track one insider over time |
| News rows carry a `dimension` object | Articles pre-classified across 8 analytical themes |
