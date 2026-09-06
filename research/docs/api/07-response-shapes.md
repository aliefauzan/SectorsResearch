# Response Shapes — What Each Endpoint Actually Returns

> Generated from the official example response attached to every endpoint in the
> OpenAPI spec. Full payloads are in [`harness/fixtures/`](../../harness/fixtures/)
> — one JSON file per endpoint, named after the path.

The API is not uniform: some endpoints return a bare array, some a `{results, pagination}`
envelope, some a bespoke object with named sub-lists. **Check this page before writing a
parser** — assuming the wrong container is the most common integration bug against this API.

Legend: **Envelope** is the outermost container. **Row keys** are the fields on the
repeating record inside, where there is one.

---

## Indonesia (IDX)

### Company Screener

**`/v2/companies/`** — Companies Screener

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`, `llm_translation`
- Row keys (inside `results`): `symbol`, `company_name`, `query_values`
- Fixture: [`idx/v2_companies.json`](../../harness/fixtures/idx/v2_companies.json)

**`/v2/free-float/`** — Free Float Market Analysis

- Envelope: bare array
- Row keys: `symbol`, `company_name`, `free_float`
- Fixture: [`idx/v2_free_float.json`](../../harness/fixtures/idx/v2_free_float.json)

### Helper Lists

**`/v2/companies/list_companies_with_segments/`** — Companies with Revenue Segments

- Envelope: object
- Top-level keys: `AADI.JK`, `AALI.JK`, `ABDA.JK`, `ABMM.JK`, `ACES.JK`, `ADCP.JK`, `ADHI.JK`, `ADMF.JK`, `ADMR.JK`, `ADRO.JK`, `AGRO.JK`, `AGRS.JK`, `AKRA.JK`, `AMAR.JK`, `AMMN.JK`, `AMRT.JK`, `ANTM.JK`, `ARGO.JK` … (+201)
- Fixture: [`idx/v2_companies_list_companies_with_segments.json`](../../harness/fixtures/idx/v2_companies_list_companies_with_segments.json)

**`/v2/companies/quarterly-financial-dates/`** — Latest Quarterly Financial Dates (Universe)

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`
- Row keys (inside `results`): `symbol`, `date`, `quarter`
- Fixture: [`idx/v2_companies_quarterly_financial_dates.json`](../../harness/fixtures/idx/v2_companies_quarterly_financial_dates.json)

**`/v2/company/get_quarterly_financial_dates/{symbol}/`** — Quarterly Financial Dates

- Envelope: object
- Top-level keys: `2026`
- Fixture: [`idx/v2_company_get_quarterly_financial_dates_symbol.json`](../../harness/fixtures/idx/v2_company_get_quarterly_financial_dates_symbol.json)

**`/v2/industries/`** — Industries

- Envelope: bare array
- Row keys: `subsector`, `industry`
- Fixture: [`idx/v2_industries.json`](../../harness/fixtures/idx/v2_industries.json)

**`/v2/subindustries/`** — Subindustries

- Envelope: bare array
- Row keys: `industry`, `sub_industry`
- Fixture: [`idx/v2_subindustries.json`](../../harness/fixtures/idx/v2_subindustries.json)

**`/v2/subsectors/`** — Subsectors

- Envelope: bare array
- Row keys: `sector`, `subsector`
- Fixture: [`idx/v2_subsectors.json`](../../harness/fixtures/idx/v2_subsectors.json)

**`/v2/tags/`** — News Tags

- Envelope: bare array
- Row keys: array of `str`
- Fixture: [`idx/v2_tags.json`](../../harness/fixtures/idx/v2_tags.json)

### Detailed Reports

**`/v2/company/corporate-actions/{symbol}/`** — Corporate Actions

- Envelope: object
- Top-level keys: `symbol`, `corporate_actions`
- Fixture: [`idx/v2_company_corporate_actions_symbol.json`](../../harness/fixtures/idx/v2_company_corporate_actions_symbol.json)

**`/v2/company/get-segments/{symbol}/`** — Company Revenue Segments

- Envelope: object
- Top-level keys: `symbol`, `financial_year`, `revenue_breakdown`
- Row keys (inside `revenue_breakdown`): `value`, `source`, `target`
- Fixture: [`idx/v2_company_get_segments_symbol.json`](../../harness/fixtures/idx/v2_company_get_segments_symbol.json)

**`/v2/company/report/`** — Company Report

- Envelope: object
- Top-level keys: `symbol`, `company_name`, `overview`, `valuation`, `future`, `financials`, `dividend`, `management`, `ownership`, `peers`
- Row keys (inside `peers`): `peers_data`
- Fixture: [`idx/v2_company_report.json`](../../harness/fixtures/idx/v2_company_report.json)

**`/v2/company/report/{symbol}/`** — Company Report

- Envelope: object
- Top-level keys: `symbol`, `company_name`, `overview`, `valuation`, `future`, `financials`, `dividend`, `management`, `ownership`, `peers`
- Row keys (inside `peers`): `peers_data`
- Fixture: [`idx/v2_company_report_symbol.json`](../../harness/fixtures/idx/v2_company_report_symbol.json)

**`/v2/company/shareholders-composition/{symbol}/`** — Shareholders Composition

- Envelope: object
- Top-level keys: `symbol`, `year`, `data`
- Row keys (inside `data`): `date`, `shares_number`, `insurance_l`, `corporate_l`, `pension_fund_l`, `financial_institutions_l`, `individual_l`, `mutual_fund_l`, `securities_companies_l`, `foundation_l`, `other_l`, `total_l`, `insurance_f`, `corporate_f`, `pension_fund_f`, `financial_institutions_f`, `individual_f`, `mutual_fund_f` … (+6)
- Fixture: [`idx/v2_company_shareholders_composition_symbol.json`](../../harness/fixtures/idx/v2_company_shareholders_composition_symbol.json)

**`/v2/financials/quarterly/{symbol}/`** — Company Quarterly Financials

- Envelope: bare array
- Row keys: `symbol`, `financials_sector_metrics`, `date`, `premium_income`, `premium_expense`, `net_premium_income`, `non_interest_income`, `revenue`, `operating_expense`, `provision`, `operating_pnl`, `non_operating_income_or_loss`, `earnings_before_tax`, `tax`, `minorities`, `earnings`, `gross_profit`, `interest_expense_non_operating` … (+22)
- Fixture: [`idx/v2_financials_quarterly_symbol.json`](../../harness/fixtures/idx/v2_financials_quarterly_symbol.json)

**`/v2/subsector/report/`** — Subsector Report

- Envelope: object
- Top-level keys: `sector`, `sub_sector`, `statistics`, `market_cap`, `stability`, `valuation`, `growth`, `companies`
- Fixture: [`idx/v2_subsector_report.json`](../../harness/fixtures/idx/v2_subsector_report.json)

**`/v2/subsector/report/{sub_sector}/`** — Subsector Report

- Envelope: object
- Top-level keys: `sector`, `sub_sector`, `statistics`, `market_cap`, `stability`, `valuation`, `growth`, `companies`
- Fixture: [`idx/v2_subsector_report_sub_sector.json`](../../harness/fixtures/idx/v2_subsector_report_sub_sector.json)

### Transaction Data

**`/v2/close/`** — Daily Full-Universe Close

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`
- Row keys (inside `results`): `symbol`, `date`, `close`
- Fixture: [`idx/v2_close.json`](../../harness/fixtures/idx/v2_close.json)

**`/v2/daily/{symbol}/`** — Daily Transaction Data

- Envelope: bare array
- Row keys: `symbol`, `date`, `close`, `open`, `high`, `low`, `volume`, `market_cap`
- Fixture: [`idx/v2_daily_symbol.json`](../../harness/fixtures/idx/v2_daily_symbol.json)

**`/v2/idx-total/`** — IDX Market Summary

- Envelope: bare array
- Row keys: `date`, `idx_total_market_cap`
- Fixture: [`idx/v2_idx_total.json`](../../harness/fixtures/idx/v2_idx_total.json)

**`/v2/index-daily/{index_code}/`** — Index Daily Transaction Data

- Envelope: bare array
- Row keys: `index_code`, `date`, `price`
- Fixture: [`idx/v2_index_daily_index_code.json`](../../harness/fixtures/idx/v2_index_daily_index_code.json)

### Rankings

**`/v2/companies/top-changes/`** — Top Company Movers

- Envelope: object
- Top-level keys: `top_gainers`, `top_losers`
- Fixture: [`idx/v2_companies_top_changes.json`](../../harness/fixtures/idx/v2_companies_top_changes.json)

**`/v2/most-traded/`** — Most Traded Stocks

- Envelope: object
- Top-level keys: `2025-05-02`
- Row keys (inside `2025-05-02`): `symbol`, `company_name`, `volume`, `price`
- Fixture: [`idx/v2_most_traded.json`](../../harness/fixtures/idx/v2_most_traded.json)

### IPO & Performance

**`/v2/listing-performance/{symbol}/`** — Company IPO & Listing Performance

- Envelope: object
- Top-level keys: `symbol`, `chg_7d`, `chg_30d`, `chg_90d`, `chg_365d`, `company_name`, `listing_date`, `shares_offered`, `percent_total_shares`, `book_building_start_date`, `book_building_end_date`, `book_building_lower_bound`, `book_building_upper_bound`, `offering_start_date`, `offering_end_date`, `offering_price`, `distribution_date`, `prospectus_url` … (+1)
- Fixture: [`idx/v2_listing_performance_symbol.json`](../../harness/fixtures/idx/v2_listing_performance_symbol.json)

### News & Filings

**`/v2/filings/`** — Company Filings

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`
- Row keys (inside `results`): `title`, `body`, `source`, `timestamp`, `sector`, `sub_sector`, `tags`, `symbol`, `transaction_type`, `holder_type`, `holder_name`, `holding_before`, `holding_after`, `amount_transaction`, `price`, `transaction_value`, `price_transaction`, `share_percentage_before` … (+4)
- Fixture: [`idx/v2_filings.json`](../../harness/fixtures/idx/v2_filings.json)

**`/v2/news/`** — News Articles

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`
- Row keys (inside `results`): `title`, `body`, `source`, `thumbnail`, `timestamp`, `sector`, `sub_sector`, `tags`, `symbols`, `dimension`
- Fixture: [`idx/v2_news.json`](../../harness/fixtures/idx/v2_news.json)

**`/v2/suspensions/`** — Stock Suspensions

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`
- Row keys (inside `results`): `symbol`, `suspension_date`, `reason`, `pdf_url`
- Fixture: [`idx/v2_suspensions.json`](../../harness/fixtures/idx/v2_suspensions.json)

### Brokers

**`/v2/broker-activity/{broker_code}/`** — Broker Activity By Code

- Envelope: object
- Top-level keys: `broker_code`, `start`, `end`, `data`
- Row keys (inside `data`): `date`, `summary`
- Fixture: [`idx/v2_broker_activity_broker_code.json`](../../harness/fixtures/idx/v2_broker_activity_broker_code.json)

**`/v2/broker-activity/{broker_code}/top/`** — Top Accumulations and Distributions Per Broker

- Envelope: object
- Top-level keys: `broker_code`, `start`, `end`, `top_accumulations`, `top_distributions`
- Row keys (inside `top_accumulations`): `rank`, `symbol`, `net_idr`, `buy_idr`, `sell_idr`
- Fixture: [`idx/v2_broker_activity_broker_code_top.json`](../../harness/fixtures/idx/v2_broker_activity_broker_code_top.json)

**`/v2/broker-summary/{symbol}/`** — Broker Activity Per Symbol

- Envelope: object
- Top-level keys: `symbol`, `start`, `end`, `data`
- Row keys (inside `data`): `date`, `summary`
- Fixture: [`idx/v2_broker_summary_symbol.json`](../../harness/fixtures/idx/v2_broker_summary_symbol.json)

**`/v2/broker-summary/{symbol}/top/`** — Top Buyers and Sellers Per Symbol

- Envelope: object
- Top-level keys: `symbol`, `start`, `end`, `origin`, `cohort`, `top_buyers`, `top_sellers`
- Row keys (inside `top_buyers`): `rank`, `broker_code`, `net_idr`, `buy_idr`, `sell_idr`
- Fixture: [`idx/v2_broker_summary_symbol_top.json`](../../harness/fixtures/idx/v2_broker_summary_symbol_top.json)

**`/v2/brokers/`** — Broker Registry

- Envelope: bare array
- Row keys: `code`, `name`, `is_foreign`, `cohort`, `license_type`
- Fixture: [`idx/v2_brokers.json`](../../harness/fixtures/idx/v2_brokers.json)

**`/v2/brokers/top/`** — Top Brokers Daily Ranking

- Envelope: object
- Top-level keys: `date`, `metric`, `origin`, `cohort`, `results`
- Row keys (inside `results`): `rank`, `broker_code`, `gross`, `net`
- Fixture: [`idx/v2_brokers_top.json`](../../harness/fixtures/idx/v2_brokers_top.json)

**`/v2/foreign-flow/{symbol}/`** — Daily Net Foreign Inflow

- Envelope: object
- Top-level keys: `symbol`, `start`, `end`, `data`
- Row keys (inside `data`): `date`, `net_foreign_inflow`
- Fixture: [`idx/v2_foreign_flow_symbol.json`](../../harness/fixtures/idx/v2_foreign_flow_symbol.json)

## Singapore (SGX)

### SGX - Company Screener

**`/v2/sgx/companies/`** — SGX Companies Screener

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`, `llm_translation`
- Row keys (inside `results`): `symbol`, `company_name`, `query_values`
- Fixture: [`sgx/v2_sgx_companies.json`](../../harness/fixtures/sgx/v2_sgx_companies.json)

### SGX - Helper Lists

**`/v2/sgx/sectors/`** — List all SGX sectors

- Envelope: bare array
- Row keys: array of `str`
- Fixture: [`sgx/v2_sgx_sectors.json`](../../harness/fixtures/sgx/v2_sgx_sectors.json)

**`/v2/sgx/subsectors/`** — SGX Subsectors

- Envelope: bare array
- Row keys: `sector`, `subsector`
- Fixture: [`sgx/v2_sgx_subsectors.json`](../../harness/fixtures/sgx/v2_sgx_subsectors.json)

**`/v2/sgx/tags/`** — SGX News Tags

- Envelope: object
- Top-level keys: `tags`
- Fixture: [`sgx/v2_sgx_tags.json`](../../harness/fixtures/sgx/v2_sgx_tags.json)

### SGX - Detailed Reports

**`/v2/sgx/company/report/`** — Full company report for an SGX-listed symbol

- Envelope: object
- Top-level keys: `symbol`, `name`, `overview`, `valuation`, `financials`, `dividend`
- Fixture: [`sgx/v2_sgx_company_report.json`](../../harness/fixtures/sgx/v2_sgx_company_report.json)

**`/v2/sgx/company/report/{symbol}/`** — Full company report for an SGX-listed symbol

- Envelope: object
- Top-level keys: `symbol`, `name`, `overview`, `valuation`, `financials`, `dividend`
- Fixture: [`sgx/v2_sgx_company_report_symbol.json`](../../harness/fixtures/sgx/v2_sgx_company_report_symbol.json)

### SGX - Transaction Data

**`/v2/sgx/buybacks/`** — SGX Share Buybacks

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`
- Row keys (inside `results`): `symbol`, `purchase_date`, `type`, `price_per_share`, `total_value`, `total_shares_purchased`, `treasury_shares_after_purchase`, `mandate`
- Fixture: [`sgx/v2_sgx_buybacks.json`](../../harness/fixtures/sgx/v2_sgx_buybacks.json)

**`/v2/sgx/daily/{symbol}/`** — SGX Daily Price Data

- Envelope: bare array
- Row keys: `symbol`, `date`, `close`, `open`, `high`, `low`, `volume`
- Fixture: [`sgx/v2_sgx_daily_symbol.json`](../../harness/fixtures/sgx/v2_sgx_daily_symbol.json)

**`/v2/sgx/short-sell/`** — SGX Short Sell

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`
- Row keys (inside `results`): `name`, `symbol`, `date`, `volume`, `value`
- Fixture: [`sgx/v2_sgx_short_sell.json`](../../harness/fixtures/sgx/v2_sgx_short_sell.json)

### SGX - Rankings

**`/v2/sgx/companies/top/`** — Top SGX companies by classification

- Envelope: object
- Top-level keys: `dividend_yield`, `revenue`, `earnings`, `market_cap`, `pe`
- Row keys (inside `dividend_yield`): `symbol`, `forward_dividend_yield`, `company_name`
- Fixture: [`sgx/v2_sgx_companies_top.json`](../../harness/fixtures/sgx/v2_sgx_companies_top.json)

### SGX - News & Filings

**`/v2/sgx/filings/`** — SGX Insider Filings

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`
- Row keys (inside `results`): `symbol`, `timestamp`, `transaction_type`, `holder_name`, `holder_type`, `holding_before`, `holding_after`, `amount_transaction`, `transaction_value`, `price_per_share`, `share_percentage_before`, `share_percentage_after`, `share_percentage_transaction`
- Fixture: [`sgx/v2_sgx_filings.json`](../../harness/fixtures/sgx/v2_sgx_filings.json)

**`/v2/sgx/news/`** — SGX News

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`
- Row keys (inside `results`): `title`, `body`, `source`, `timestamp`, `sector`, `sub_sector`, `tags`, `symbols`, `dimension`
- Fixture: [`sgx/v2_sgx_news.json`](../../harness/fixtures/sgx/v2_sgx_news.json)

## Malaysia (KLSE)

### KLSE

**`/v2/klse/companies/`** — List KLSE companies filtered by sector

- Envelope: bare array
- Row keys: `symbol`, `company_name`
- Fixture: [`klse/v2_klse_companies.json`](../../harness/fixtures/klse/v2_klse_companies.json)

**`/v2/klse/companies/top/`** — Top KLSE companies by classification

- Envelope: object
- Top-level keys: `dividend_yield`, `revenue`, `earnings`, `market_cap`, `pe`
- Row keys (inside `revenue`): `symbol`, `revenue`, `company_name`
- Fixture: [`klse/v2_klse_companies_top.json`](../../harness/fixtures/klse/v2_klse_companies_top.json)

**`/v2/klse/company/report/`** — Full company report for a KLSE-listed symbol

- Envelope: object
- Top-level keys: `symbol`, `name`, `overview`, `valuation`, `financials`, `dividend`
- Fixture: [`klse/v2_klse_company_report.json`](../../harness/fixtures/klse/v2_klse_company_report.json)

**`/v2/klse/company/report/{symbol}/`** — Full company report for a KLSE-listed symbol

- Envelope: object
- Top-level keys: `symbol`, `name`, `overview`, `valuation`, `financials`, `dividend`
- Fixture: [`klse/v2_klse_company_report_symbol.json`](../../harness/fixtures/klse/v2_klse_company_report_symbol.json)

**`/v2/klse/sectors/`** — List all KLSE sectors

- Envelope: bare array
- Row keys: array of `str`
- Fixture: [`klse/v2_klse_sectors.json`](../../harness/fixtures/klse/v2_klse_sectors.json)

## Mining extension

### Companies

**`/v2/mining/companies/`** — List Mining Companies

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`
- Row keys (inside `results`): `slug`, `name`, `symbol`, `company_type`, `key_operation`, `commodity_type`
- Fixture: [`mining/v2_mining_companies.json`](../../harness/fixtures/mining/v2_mining_companies.json)

**`/v2/mining/companies/financials/{slug}/`** — Mining Company Financials

- Envelope: object
- Top-level keys: `year`, `available_years`, `data`
- Fixture: [`mining/v2_mining_companies_financials_slug.json`](../../harness/fixtures/mining/v2_mining_companies_financials_slug.json)

**`/v2/mining/companies/ownership/{slug}/`** — Mining Company Ownership

- Envelope: object
- Top-level keys: `slug`, `parents`, `subsidiaries`
- Row keys (inside `parents`): `name`, `slug`, `symbol`, `percentage_ownership`
- Fixture: [`mining/v2_mining_companies_ownership_slug.json`](../../harness/fixtures/mining/v2_mining_companies_ownership_slug.json)

**`/v2/mining/companies/performance/{slug}/`** — Mining Company Performance

- Envelope: object
- Top-level keys: `year`, `available_years`, `data`
- Row keys (inside `data`): `year`, `commodity_type`, `commodity_sub_type`, `commodity_stats`
- Fixture: [`mining/v2_mining_companies_performance_slug.json`](../../harness/fixtures/mining/v2_mining_companies_performance_slug.json)

**`/v2/mining/companies/{slug}/`** — Mining Company Detail

- Envelope: object
- Top-level keys: `name`, `slug`, `symbol`, `company_type`, `operation_province`, `operation_district`, `key_operation`, `representative_address`, `website`, `phone_number`, `email`, `activities`, `commodity_type`, `mining_license`, `mining_contract`, `mining_site_count`
- Row keys (inside `mining_license`): `license_type`, `license_number`, `wiup_code`, `province`, `city`, `license_effective_date`, `license_expiry_date`, `activity`, `licensed_area_ha`, `cnc`, `generation`, `location`, `commodity_type`
- Fixture: [`mining/v2_mining_companies_slug.json`](../../harness/fixtures/mining/v2_mining_companies_slug.json)

### Commodities & Trade

**`/v2/mining/commodities/`** — List Commodities

- Envelope: bare array
- Row keys: `name`, `data_points`, `earliest_date`, `latest_date`
- Fixture: [`mining/v2_mining_commodities.json`](../../harness/fixtures/mining/v2_mining_commodities.json)

**`/v2/mining/commodities/{commodity_name}/price/`** — Commodity Price History

- Envelope: bare array
- Row keys: `name`, `date`, `price_usd_per_ton`
- Fixture: [`mining/v2_mining_commodities_commodity_name_price.json`](../../harness/fixtures/mining/v2_mining_commodities_commodity_name_price.json)

**`/v2/mining/exports/`** — Top Export Destinations

- Envelope: bare array
- Row keys: `country`, `export_usd`, `export_volume_bps`, `export_volume_esdm`, `volume_unit`
- Fixture: [`mining/v2_mining_exports.json`](../../harness/fixtures/mining/v2_mining_exports.json)

**`/v2/mining/global-commodity/`** — Global Commodity Data

- Envelope: bare array
- Row keys: `country`, `commodity_type`, `resources_reserves`, `resources_reserves_share`, `resources_reserves_unit`, `export_import_usd`, `production_volume`, `production_share`, `production_volume_unit`
- Fixture: [`mining/v2_mining_global_commodity.json`](../../harness/fixtures/mining/v2_mining_global_commodity.json)

**`/v2/mining/sales-destination/{slug}/`** — Company Sales Destinations

- Envelope: object
- Top-level keys: `year`, `data`
- Fixture: [`mining/v2_mining_sales_destination_slug.json`](../../harness/fixtures/mining/v2_mining_sales_destination_slug.json)

### Production & Sites

**`/v2/mining/resources-reserves/`** — Resources & Reserves Index

- Envelope: object
- Top-level keys: `Aceh`
- Fixture: [`mining/v2_mining_resources_reserves.json`](../../harness/fixtures/mining/v2_mining_resources_reserves.json)

**`/v2/mining/resources-reserves/{province}/`** — Resources & Reserves Detail

- Envelope: object
- Top-level keys: `province`, `data`
- Fixture: [`mining/v2_mining_resources_reserves_province.json`](../../harness/fixtures/mining/v2_mining_resources_reserves_province.json)

**`/v2/mining/sites/`** — Mining Sites

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`
- Row keys (inside `results`): `name`, `project_name`, `year`, `commodity_type`, `production_volume`, `unit`, `strip_ratio`, `province`, `city`, `company_slug`, `company_name`, `slug`
- Fixture: [`mining/v2_mining_sites.json`](../../harness/fixtures/mining/v2_mining_sites.json)

**`/v2/mining/sites/{slug}/`** — Mining Site Detail

- Envelope: object
- Top-level keys: `name`, `project_name`, `year`, `commodity_type`, `production_volume`, `unit`, `overburden_removal_volume`, `strip_ratio`, `resources_reserves`, `location`, `company_slug`, `company_name`, `slug`
- Fixture: [`mining/v2_mining_sites_slug.json`](../../harness/fixtures/mining/v2_mining_sites_slug.json)

**`/v2/mining/total-production/`** — Total Commodity Production

- Envelope: bare array
- Row keys: `year`, `production_volume`, `prev_year_volume`, `unit`, `yoy_change_percent`
- Fixture: [`mining/v2_mining_total_production.json`](../../harness/fixtures/mining/v2_mining_total_production.json)

### Contracts & Licenses

**`/v2/mining/contracts/`** — Mining Contracts

- Envelope: bare array
- Row keys: `mine_owner_slug`, `mine_owner_name`, `contractor_slug`, `contractor_name`, `contract_period_end`
- Fixture: [`mining/v2_mining_contracts.json`](../../harness/fixtures/mining/v2_mining_contracts.json)

**`/v2/mining/license-auctions/`** — Mining License Auctions

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`
- Row keys (inside `results`): `commodity_type`, `city`, `province`, `company_name`, `winner_date`, `licensed_area_ha`, `license_number`, `area_type`, `kdi`, `wiup_code`, `auction_status`, `participant_count`, `winner`, `company_slug`
- Fixture: [`mining/v2_mining_license_auctions.json`](../../harness/fixtures/mining/v2_mining_license_auctions.json)

**`/v2/mining/license-auctions/{wiup_code}/`** — Mining License Auction Detail

- Envelope: object
- Top-level keys: `commodity_type`, `city`, `province`, `company_name`, `winner_date`, `licensed_area_ha`, `license_number`, `area_type`, `kdi`, `wiup_code`, `auction_status`, `participant_count`, `winner`, `created_at`, `last_modified`, `phases`, `participants`, `company_slug`
- Row keys (inside `phases`): `order`, `description`, `start_date`, `end_date`
- Fixture: [`mining/v2_mining_license_auctions_wiup_code.json`](../../harness/fixtures/mining/v2_mining_license_auctions_wiup_code.json)

**`/v2/mining/licenses/`** — Mining Licenses

- Envelope: `{results, pagination}` envelope
- Top-level keys: `results`, `pagination`
- Row keys (inside `results`): `wiup_code`, `license_number`, `license_type`, `province`, `city`, `license_effective_date`, `license_expiry_date`, `activity`, `licensed_area_ha`, `location`, `commodity_type`, `company_name`, `cnc`, `generation`, `company_slug`
- Fixture: [`mining/v2_mining_licenses.json`](../../harness/fixtures/mining/v2_mining_licenses.json)

