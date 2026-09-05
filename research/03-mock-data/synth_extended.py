#!/usr/bin/env python3
"""
Extend the synthetic universe with the datasets `synth_universe.py` does not model.

`synth_universe.py` covers the screener, daily prices, foreign flow, per-broker rows
and news — about 22 of the 70 endpoints. This adds the rest of what the project ideas in
`04-build-plan/` actually need, in the same field naming the live API uses:

    mining/          19 endpoints' worth: licences, sites, auctions, companies,
                     ownership trees, production, reserves, commodity prices,
                     exports, sales destinations, contracts
    banking.json     NPL / special-mention / restructured / gross loan by year,
                     so Loan-at-Risk (LAR) is computable
    suspensions.json IDX suspensions with official-style reasons
    corporate_actions.json   splits, rights, warrants, bonus shares, AGM, dividends
    shareholders_composition.json  monthly local/foreign panel per company
    filings.json     insider and institutional buy/sell filings
    segments.json    revenue and cost segments, including key customers
    quarterly/       quarterly financials per symbol + the report-date helper
    free_float.json  public float percentage per company
    listing_performance.json   7/30/90/365-day performance since listing
    index_daily/     IHSG, LQ45, IDX30 and friends, on real IDX trading days
    idx_total.json   whole-market capitalisation series
    brokers.json     broker registry with origin and cohort
    broker_top/      top buyers and sellers per symbol, zero-sum consistent
    trading_days.json  the real IDX 2026 holiday calendar applied

Run `synth_universe.py` first — this reads its `companies.json` and `daily/`.

    python3 synth_universe.py --companies 200 --days 180
    python3 synth_extended.py

Deterministic: same --seed, same output. Plausible, not real — never present it as
market data, and never ship it as a product's data source.
"""
import argparse
import json
import os
import random
from datetime import date, timedelta

# Real IDX market holidays for 2026. No API endpoint exposes these.
# Source: sectors.app/indonesia/calendars/trading-calendar
IDX_HOLIDAYS_2026 = {
    (1, 1), (1, 16), (2, 16), (2, 17), (3, 18), (3, 19), (3, 20), (3, 23), (3, 24),
    (4, 3), (5, 1), (5, 14), (5, 15), (5, 27), (5, 28), (6, 1), (6, 16),
    (8, 17), (8, 25), (12, 24), (12, 25), (12, 31),
}

# Index codes confirmed from sectors.app/indonesia/index/<code>.
# All 17 codes the spec's own <Accordion title="Available index codes"> lists for
# /v2/index-daily/{index_code}/. An earlier version of this generator modelled only the 8
# that have a sectors.app product page, so any code path that iterated the mock's indices
# silently never saw idxv30, sminfra18, sti or idxvesta28.
INDEX_CODES = [
    "ihsg", "lq45", "idx30", "kompas100", "jii70", "idxbumn20", "srikehati", "idxesgl",
    "idxhidiv20", "idxq30", "idxg30", "idxv30", "economic30", "ftse", "sminfra18",
    "idxvesta28", "sti",
]

# Mining enums are title-case with spaces and differ per endpoint — see
# 02-sectors-platform/06-parameter-cheatsheet.md.
COMMODITIES = ["Coal", "Gold", "Nickel", "Copper"]
LICENSE_TYPES = ["IUP", "IUPK", "PKP2B", "KK", "IPR", "SIPB"]
LICENSE_ACTIVITIES = ["Eksplorasi", "Operasi Produksi"]
AREA_TYPES = ["WIUP", "WIUPK"]
COMPANY_TYPES = ["Mine Owner", "Contractor", "Holding", "Trader", "Manufacturer", "Consultant"]
MINING_PROVINCES = [
    "Kalimantan Timur", "Kalimantan Selatan", "Kalimantan Tengah", "Kalimantan Utara",
    "Sumatera Selatan", "Jambi", "Sulawesi Tenggara", "Sulawesi Selatan", "Sulawesi Tengah",
    "Maluku Utara", "Papua", "Papua Tengah", "Nusa Tenggara Barat", "Bengkulu", "Riau",
]
AUCTION_PROVINCES = [
    "Bengkulu", "Gorontalo", "Kalimantan Tengah", "Maluku Utara",
    "Nusa Tenggara Barat", "Sulawesi Selatan", "Sulawesi Utara", "Sumatera Selatan",
]
EXPORT_DESTINATIONS = ["China", "India", "Japan", "South Korea", "Taiwan", "Philippines",
                       "Vietnam", "Malaysia", "Bangladesh", "Thailand"]

SUSPENSION_REASONS = [
    "Unusual Market Activity (UMA)",
    "Pending disclosure of material information",
    "Failure to submit financial report",
    "Going concern doubt raised by auditor",
    "Significant price and volume movement",
    "Company request pending corporate action",
]

ACTION_TYPES = ["cash_dividend", "stock_split", "reverse_split", "rights_issue",
                "bonus_shares", "warrant", "agm", "egm", "public_expose"]

HOLDER_TYPES = ["insider", "institution", "corporate-investor"]

SEGMENT_LINES = ["Domestic Retail", "Export", "Wholesale", "Services", "Digital",
                 "Industrial", "Government Contracts", "Licensing"]
COST_LINES = ["Raw Materials", "Labour", "Logistics", "Energy", "Depreciation",
              "Marketing", "Administrative", "Financing"]
KEY_CUSTOMERS = ["PLN", "Pertamina", "Astra Group", "Unilever Indonesia", "Indofood",
                 "Telkom Indonesia", "Sinar Mas", "Salim Group", "Djarum Group",
                 "Government of Indonesia"]

BROKERS = [
    ("YP", "domestic", "retail"), ("PD", "domestic", "retail"), ("CC", "domestic", "mixed"),
    ("MG", "domestic", "retail"), ("KZ", "foreign", "institutional"), ("CS", "foreign", "institutional"),
    ("ZP", "foreign", "institutional"), ("BK", "foreign", "institutional"), ("DR", "domestic", "mixed"),
    ("NI", "domestic", "retail"), ("AK", "foreign", "institutional"), ("RX", "foreign", "institutional"),
]
BROKER_NAMES = {
    "YP": "Mirae Asset Sekuritas Indonesia", "PD": "Indo Premier Sekuritas",
    "CC": "Mandiri Sekuritas", "MG": "Semesta Indovest Sekuritas",
    "KZ": "CLSA Sekuritas Indonesia", "CS": "Credit Suisse Sekuritas Indonesia",
    "ZP": "Maybank Sekuritas Indonesia", "BK": "J.P. Morgan Sekuritas Indonesia",
    "DR": "RHB Sekuritas Indonesia", "NI": "BNI Sekuritas",
    "AK": "UBS Sekuritas Indonesia", "RX": "Macquarie Sekuritas Indonesia",
}


def is_trading_day(day):
    """IDX trades Monday-Friday excluding gazetted market holidays."""
    return day.weekday() < 5 and (day.month, day.day) not in IDX_HOLIDAYS_2026


def trading_days(end, count):
    days, cursor = [], end
    while len(days) < count:
        if is_trading_day(cursor):
            days.append(cursor)
        cursor -= timedelta(days=1)
    return sorted(days)


def slugify(name):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in name)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


# --------------------------------------------------------------------------- banking

def make_banking(rng, companies, years):
    """NPL, special-mention and restructured loans by year, so LAR is computable.

    Loan at Risk = (NPL + special mention + restructured performing) / gross loan.
    The live screener exposes every component as a yearly bracket field; nothing
    combines them, which is what makes it a defensible derived metric.
    """
    rows = []
    for company in companies:
        if company["sub_sector"] != "banks":
            continue
        base_gross = company.get("gross_loan_mrq") or int(company["total_assets_mrq"] * 0.6)
        quality = rng.uniform(0.6, 1.4)  # persistent per-bank credit-quality character
        for year in years:
            gross = int(base_gross * rng.uniform(0.9, 1.12) ** (years[-1] - year))
            npl_ratio = max(0.002, rng.gauss(0.025, 0.012) * quality)
            sml_ratio = max(0.003, rng.gauss(0.045, 0.02) * quality)
            restructured_ratio = max(0.001, rng.gauss(0.06, 0.03) * quality)
            rows.append({
                "symbol": company["symbol"],
                "year": year,
                "gross_loan": gross,
                "non_performing_loan": int(gross * npl_ratio),
                "special_mention_loan": int(gross * sml_ratio),
                "restructured_loan_current": int(gross * restructured_ratio),
                "allowance_for_loans": int(gross * npl_ratio * rng.uniform(0.8, 1.6)),
                # Convenience: the derived metric a project would compute itself.
                "lar_ratio": round(npl_ratio + sml_ratio + restructured_ratio, 6),
                "npl_ratio": round(npl_ratio, 6),
            })
    return rows


# --------------------------------------------------------------------------- events

def make_suspensions(rng, companies, days, count):
    rows = []
    for _ in range(count):
        company = rng.choice(companies)
        start = rng.choice(days)
        rows.append({
            "symbol": company["symbol"],
            "company_name": company["company_name"],
            "suspension_date": str(start),
            "resumption_date": str(start + timedelta(days=rng.randint(1, 21))),
            "reason": rng.choice(SUSPENSION_REASONS),
            "notice_url": f"https://example.invalid/idx/notice/{slugify(company['symbol'])}-{start}.pdf",
        })
    return sorted(rows, key=lambda r: r["suspension_date"])


def make_corporate_actions(rng, companies, days):
    rows = []
    for company in companies:
        for _ in range(rng.randint(0, 4)):
            action = rng.choice(ACTION_TYPES)
            day = rng.choice(days)
            row = {
                "symbol": company["symbol"],
                "date": str(day),
                "action_type": action,
            }
            if action == "cash_dividend":
                row["amount_per_share"] = int(max(1, company["last_close_price"] * rng.uniform(0.005, 0.05)))
                row["ex_date"] = str(day)
                row["payment_date"] = str(day + timedelta(days=rng.randint(14, 45)))
            elif action in ("stock_split", "reverse_split"):
                row["ratio"] = rng.choice(["1:2", "1:5", "1:10", "2:1", "5:1"])
            elif action == "rights_issue":
                row["ratio"] = rng.choice(["1:4", "1:10", "3:20"])
                row["exercise_price"] = int(company["last_close_price"] * rng.uniform(0.6, 0.95))
            elif action == "bonus_shares":
                row["ratio"] = rng.choice(["1:1", "1:2", "1:4"])
            rows.append(row)
    return sorted(rows, key=lambda r: r["date"])


def make_shareholders_composition(rng, companies, months):
    """Monthly investor-category panel, local vs foreign — the Stories-style dataset."""
    rows = []
    for company in companies:
        local = rng.uniform(0.35, 0.85)
        for month in months:
            local = min(0.95, max(0.05, local + rng.gauss(0, 0.012)))
            foreign = 1 - local
            rows.append({
                "symbol": company["symbol"],
                "month": month,
                "local_total": round(local, 6),
                "foreign_total": round(foreign, 6),
                "local_breakdown": {
                    "individual": round(local * rng.uniform(0.2, 0.5), 6),
                    "corporate": round(local * rng.uniform(0.2, 0.5), 6),
                    "mutual_fund": round(local * rng.uniform(0.05, 0.2), 6),
                    "insurance": round(local * rng.uniform(0.02, 0.12), 6),
                    "pension_fund": round(local * rng.uniform(0.02, 0.1), 6),
                },
                "foreign_breakdown": {
                    "individual": round(foreign * rng.uniform(0.02, 0.15), 6),
                    "corporate": round(foreign * rng.uniform(0.3, 0.7), 6),
                    "mutual_fund": round(foreign * rng.uniform(0.1, 0.4), 6),
                },
            })
    return rows


def make_filings(rng, companies, days, count):
    rows = []
    for i in range(count):
        company = rng.choice(companies)
        transaction = rng.choices(["buy", "sell", "others"], [0.45, 0.45, 0.10])[0]
        shares = rng.randint(10_000, 50_000_000)
        price = int(company["last_close_price"] * rng.uniform(0.92, 1.08))
        rows.append({
            "id": f"filing-{i:06d}",
            "symbol": company["symbol"],
            "date": str(rng.choice(days)),
            "holder_name": rng.choice([
                "PT Investama Nusantara", "Budi Santoso", "Sinar Mas Group",
                "BlackRock Fund Advisors", "PT Dana Abadi", "Siti Rahmawati",
                "Vanguard Emerging Markets", "PT Karya Sejahtera",
            ]),
            "holder_type": rng.choice(HOLDER_TYPES),
            "transaction_type": transaction,
            "share_amount": shares,
            "price": price,
            "transaction_value": shares * price,
            "share_percentage_before": round(rng.uniform(0.01, 0.35), 6),
            "share_percentage_after": round(rng.uniform(0.01, 0.35), 6),
        })
    return sorted(rows, key=lambda r: r["date"])


# --------------------------------------------------------------------------- fundamentals

def make_segments(rng, companies, years):
    """Revenue and cost segments, including the key-customer breakdown Sectors
    describes as first-party and available nowhere else."""
    out = {}
    for company in companies:
        if rng.random() > 0.45:      # not every company reports segments
            continue
        per_year = {}
        for year in years:
            revenue = int(company["total_revenue_mrq"] * 4 * rng.uniform(0.85, 1.15))
            lines = rng.sample(SEGMENT_LINES, rng.randint(2, 5))
            weights = [rng.uniform(0.5, 3.0) for _ in lines]
            total = sum(weights)
            revenue_segments = {
                name: int(revenue * w / total) for name, w in zip(lines, weights)
            }
            costs = rng.sample(COST_LINES, rng.randint(3, 6))
            cw = [rng.uniform(0.5, 3.0) for _ in costs]
            ctotal = sum(cw)
            cost_base = int(revenue * rng.uniform(0.55, 0.9))
            cost_segments = {
                name: int(cost_base * w / ctotal) for name, w in zip(costs, cw)
            }
            customers = rng.sample(KEY_CUSTOMERS, rng.randint(0, 4))
            kw = [rng.uniform(0.5, 3.0) for _ in customers]
            ktotal = sum(kw) or 1
            concentration = rng.uniform(0.1, 0.7)
            per_year[str(year)] = {
                "revenue_segments": revenue_segments,
                "cost_segments": cost_segments,
                "key_customers": {
                    name: int(revenue * concentration * w / ktotal)
                    for name, w in zip(customers, kw)
                },
                "total_revenue": revenue,
            }
        out[company["symbol"]] = per_year
    return out


def make_quarterly(rng, companies, quarters):
    """Quarterly financials plus the report-date helper feed."""
    financials, report_dates = {}, {}
    for company in companies:
        is_bank = company["sub_sector"] == "banks"
        rows, dates = [], {}
        for year, quarter in quarters:
            month_end = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}[quarter]
            report_date = str(date(year, month_end[0], month_end[1]))
            revenue = int(company["total_revenue_mrq"] * rng.uniform(0.8, 1.25))
            earnings = int(revenue * rng.gauss(0.12, 0.1))
            row = {
                "symbol": company["symbol"],
                "report_date": report_date,
                "quarter": f"Q{quarter}-{year}",
                "revenue": revenue,
                "earnings": earnings,
                "gross_profit": int(revenue * rng.uniform(0.15, 0.5)),
                "operating_pnl": int(revenue * rng.uniform(0.05, 0.35)),
                "total_assets": int(company["total_assets_mrq"] * rng.uniform(0.9, 1.15)),
                "total_equity": int(company["total_equity_mrq"] * rng.uniform(0.9, 1.15)),
                "total_liabilities": int(company["total_assets_mrq"] * rng.uniform(0.4, 0.8)),
                "operating_cash_flow": int(revenue * rng.gauss(0.15, 0.1)),
            }
            if is_bank:
                row.update({
                    "net_interest_income": int(revenue * rng.uniform(0.5, 0.8)),
                    "gross_loan": company.get("gross_loan_mrq", 0),
                    "total_deposit": company.get("total_deposit_mrq", 0),
                })
            rows.append(row)
            dates.setdefault(str(year), []).append({"quarter": f"Q{quarter}", "date": report_date})
        financials[company["symbol"]] = rows
        report_dates[company["symbol"]] = dates
    return financials, report_dates


def make_free_float(rng, companies):
    return sorted(
        [{"symbol": c["symbol"], "company_name": c["company_name"],
          "free_float": c.get("free_float", round(rng.uniform(0.05, 0.85), 4))}
         for c in companies],
        key=lambda r: -r["free_float"],
    )


def make_listing_performance(rng, companies):
    rows = []
    for company in companies:
        rows.append({
            "symbol": company["symbol"],
            "listing_date": company["listing_date"],
            "chg_7d": round(rng.gauss(0.01, 0.12), 6),
            "chg_30d": round(rng.gauss(0.03, 0.25), 6),
            "chg_90d": round(rng.gauss(0.05, 0.4), 6),
            "chg_365d": round(rng.gauss(0.10, 0.7), 6),
        })
    return rows


# --------------------------------------------------------------------------- market

def make_index_series(rng, days):
    """One series per real IDX index code, on real trading days."""
    out = {}
    for code in INDEX_CODES:
        level = rng.uniform(400, 7500)
        drift, vol = rng.gauss(0.0002, 0.0004), rng.uniform(0.006, 0.016)
        series = []
        for day in days:
            level = max(1.0, level * (1 + rng.gauss(drift, vol)))
            series.append({"index_code": code, "date": str(day), "close": round(level, 3)})
        out[code] = series
    return out


def make_idx_total(rng, days, companies):
    total = sum(c["market_cap"] for c in companies)
    series, level = [], float(total)
    for day in days:
        level = max(1.0, level * (1 + rng.gauss(0.0003, 0.008)))
        series.append({"date": str(day), "idx_total_market_cap": int(level)})
    return series


def make_broker_registry():
    return [{"code": code, "name": BROKER_NAMES[code], "origin": origin,
             "is_foreign": origin == "foreign", "cohort": cohort,
             "license_type": "PPE-PPEP"}
            for code, origin, cohort in BROKERS]


def make_broker_top(rng, companies, days, n_symbols):
    """Top buyers and sellers per symbol — deliberately zero-sum consistent.

    Summing every buyer's net and every seller's net cancels to ~0, exactly as it
    does on the live API. That is the 'zero-sum trap' documented in
    02-sectors-platform/10-domain-pitfalls.md. Keeping the property here means a
    project can reproduce the trap locally and verify its dominance-score fix.
    """
    out = {}
    for company in companies[:n_symbols]:
        traded = company["last_close_price"] * rng.randint(1_000_000, 200_000_000)
        picks = rng.sample(BROKERS, 10)
        buyers_codes, sellers_codes = picks[:5], picks[5:]
        weights = [rng.uniform(0.5, 3.0) for _ in buyers_codes]
        wtotal = sum(weights)
        buyers, running = [], 0
        for (code, origin, cohort), w in zip(buyers_codes, weights):
            net = int(traded * 0.25 * w / wtotal)
            running += net
            buyers.append({"broker_code": code, "origin": origin, "cohort": cohort,
                           "net_idr": net, "buy_idr": int(net * rng.uniform(1.2, 2.5))})
        sweights = [rng.uniform(0.5, 3.0) for _ in sellers_codes]
        stotal = sum(sweights)
        sellers = []
        for (code, origin, cohort), w in zip(sellers_codes, sweights):
            net = -int(running * w / stotal)          # mirrors the buy side exactly
            sellers.append({"broker_code": code, "origin": origin, "cohort": cohort,
                            "net_idr": net, "sell_idr": int(-net * rng.uniform(1.2, 2.5))})
        buyers.sort(key=lambda r: -r["net_idr"])
        sellers.sort(key=lambda r: r["net_idr"])
        out[company["symbol"]] = {
            "symbol": company["symbol"],
            "start": str(days[-14]), "end": str(days[-1]),
            "top_buyers": buyers, "top_sellers": sellers,
        }
    return out


# --------------------------------------------------------------------------- mining

def make_mining(rng, n_companies, n_sites, n_licenses, n_auctions, years):
    """The 19 mining endpoints' worth of data, including unlisted operators."""
    companies = []
    for i in range(n_companies):
        listed = rng.random() < 0.25
        name = f"PT {rng.choice(['Bara','Tambang','Mineral','Nusantara','Karya','Adhi','Bumi'])} " \
               f"{rng.choice(['Sejahtera','Utama','Mandiri','Persada','Energi','Jaya'])}"
        companies.append({
            "slug": slugify(name) + f"-{i}",
            "name": name,
            "symbol": ("".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(4)) + ".JK")
                      if listed else None,
            "is_listed": listed,
            "company_type": rng.choice(COMPANY_TYPES),
            "commodity_types": rng.sample(COMMODITIES, rng.randint(1, 2)),
            "province": rng.choice(MINING_PROVINCES),
            "site_count": rng.randint(1, 14),
        })

    sites = []
    for i in range(n_sites):
        owner = rng.choice(companies)
        commodity = rng.choice(owner["commodity_types"])
        province = owner["province"]
        sites.append({
            "slug": f"site-{i:04d}-{slugify(province)}",
            "name": f"{rng.choice(['Blok','Site','Pit'])} {rng.choice(['Utara','Selatan','Timur','Barat'])} {i}",
            "owner_slug": owner["slug"],
            "commodity_type": commodity,
            "province": province,
            "latitude": round(rng.uniform(-8.5, 5.5), 6),
            "longitude": round(rng.uniform(95.0, 141.0), 6),
            "production_volume": rng.randint(50_000, 40_000_000),
            "strip_ratio": round(rng.uniform(2.0, 12.0), 2),
            "year": rng.choice(years),
        })

    licenses = []
    for i in range(n_licenses):
        owner = rng.choice(companies)
        effective = date(rng.randint(2008, 2024), rng.randint(1, 12), rng.randint(1, 28))
        expiry = date(effective.year + rng.randint(3, 20), effective.month, effective.day)
        licenses.append({
            "license_id": f"IUP-{i:05d}",
            "company_slug": owner["slug"],
            "company_name": owner["name"],
            "license_type": rng.choice(LICENSE_TYPES),
            "activity": rng.choice(LICENSE_ACTIVITIES),
            "commodity_type": rng.choice(owner["commodity_types"]),
            "province": owner["province"],
            "licensed_area_ha": round(rng.uniform(50, 40_000), 2),
            "license_effective_date": str(effective),
            "license_expiry_date": str(expiry),
            "status": rng.choices(["Active", "Expired", "Suspended"], [0.8, 0.15, 0.05])[0],
        })

    auctions = []
    for i in range(n_auctions):
        province = rng.choice(AUCTION_PROVINCES)
        wiup = f"WIUP-{province[:3].upper()}-{i:04d}"
        participants = rng.randint(0, 9)
        auctions.append({
            "wiup_code": wiup,
            "province": province,
            "area_type": rng.choice(AREA_TYPES),
            "commodity_type": rng.choice(["Coal", "Copper", "Gold", "Nickel"]),
            "licensed_area_ha": round(rng.uniform(200, 25_000), 2),
            "participant_count": participants,
            "winner": participants > 0 and rng.random() < 0.6,
            "winner_date": str(date(rng.randint(2023, 2026), rng.randint(1, 12), rng.randint(1, 28))),
            "phases": [
                {"phase": name, "start": str(date(2025, m, 1)), "end": str(date(2025, m, 28))}
                for name, m in [("Pengumuman", 1), ("Pendaftaran", 2), ("Evaluasi", 3), ("Penetapan", 4)]
            ],
            "participants": [
                {"name": rng.choice(companies)["name"], "qualified": rng.random() < 0.7}
                for _ in range(participants)
            ],
        })

    ownership = {}
    for company in companies:
        ownership[company["slug"]] = {
            "slug": company["slug"],
            "parents": [
                {"name": rng.choice(companies)["name"], "stake": round(rng.uniform(0.05, 0.9), 4)}
                for _ in range(rng.randint(0, 2))
            ],
            "subsidiaries": [
                {"name": rng.choice(companies)["name"], "stake": round(rng.uniform(0.2, 1.0), 4)}
                for _ in range(rng.randint(0, 4))
            ],
        }

    financials = []
    for company in companies:
        for year in years:
            revenue = round(rng.uniform(5, 4000), 2)
            financials.append({
                "slug": company["slug"], "year": year,
                "revenue_usd_m": revenue,
                "assets_usd_m": round(revenue * rng.uniform(0.8, 4.0), 2),
                "profit_usd_m": round(revenue * rng.gauss(0.12, 0.15), 2),
            })

    # Gold history really does run back to 1968 on the live API.
    prices = []
    for commodity in COMMODITIES:
        start_year = 1968 if commodity == "Gold" else 2010
        level = {"Coal": 90.0, "Gold": 40.0, "Nickel": 12000.0, "Copper": 4000.0}[commodity]
        today = date.today()
        for year in range(start_year, today.year + 1):
            for month in range(1, 13):
                # Never emit a future observation — a series that runs past today
                # breaks any "latest price" logic built against it.
                if (year, month) > (today.year, today.month):
                    break
                level = max(1.0, level * (1 + rng.gauss(0.004, 0.05)))
                prices.append({
                    "name": commodity,
                    "date": f"{year}-{month:02d}-01",
                    "price_usd_per_ton": round(level, 2),
                })

    commodities_index = []
    for commodity in COMMODITIES:
        rows = [p for p in prices if p["name"] == commodity]
        commodities_index.append({
            "name": commodity, "data_points": len(rows),
            "earliest_date": rows[0]["date"], "latest_date": rows[-1]["date"],
        })

    exports = [
        {"commodity_type": commodity, "year": year, "country": country,
         "export_value_usd_m": round(rng.uniform(10, 9000), 2),
         "volume_tons": rng.randint(10_000, 40_000_000)}
        for commodity in ["Coal", "Copper", "Gold"]
        for year in years
        for country in rng.sample(EXPORT_DESTINATIONS, 6)
    ]

    sales_destination = {
        company["slug"]: {
            "slug": company["slug"], "year": years[-1],
            "destinations": {
                country: {"revenue_usd_m": round(rng.uniform(1, 900), 2),
                          "volume_tons": rng.randint(1000, 9_000_000)}
                for country in rng.sample(EXPORT_DESTINATIONS, rng.randint(2, 5))
            },
        }
        for company in companies if rng.random() < 0.4
    }

    reserves = []
    for province in MINING_PROVINCES:
        for year in years:
            for commodity in rng.sample(COMMODITIES, rng.randint(1, 3)):
                resources = round(rng.uniform(100, 90_000), 2)
                reserves.append({
                    "province": province, "year": year, "commodity_type": commodity,
                    "exploration_target": round(resources * rng.uniform(0.05, 0.3), 2),
                    "total_inventory": round(resources * rng.uniform(1.0, 1.4), 2),
                    "resources": resources,
                    "reserves": round(resources * rng.uniform(0.2, 0.5), 2),
                    "unit": "Mt",
                })

    production = [
        {"commodity_type": commodity, "year": year,
         "total_production": rng.randint(1_000_000, 700_000_000),
         "yoy_change_pct": round(rng.gauss(0.03, 0.12), 6)}
        for commodity in COMMODITIES for year in years
    ]

    contracts = [
        {"mine_owner_slug": rng.choice(companies)["slug"],
         "contractor_slug": rng.choice(companies)["slug"],
         "commodity_type": rng.choice(COMMODITIES),
         "start_year": rng.choice(years)}
        for _ in range(max(10, n_companies // 2))
    ]

    return {
        "companies.json": companies,
        "sites.json": sites,
        "licenses.json": licenses,
        "license_auctions.json": auctions,
        "ownership.json": ownership,
        "financials.json": financials,
        "commodity_prices.json": prices,
        "commodities.json": commodities_index,
        "exports.json": exports,
        "sales_destination.json": sales_destination,
        "resources_reserves.json": reserves,
        "total_production.json": production,
        "contracts.json": contracts,
    }


# --------------------------------------------------------------------------- main

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="indir", default=os.path.join(here, "synth"),
                    help="output directory of synth_universe.py")
    ap.add_argument("--out", default=os.path.join(here, "synth"))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--years", type=int, default=4)
    ap.add_argument("--quarters", type=int, default=8)
    ap.add_argument("--mining-companies", type=int, default=120)
    ap.add_argument("--mining-sites", type=int, default=300)
    ap.add_argument("--mining-licenses", type=int, default=400)
    ap.add_argument("--mining-auctions", type=int, default=60)
    args = ap.parse_args()

    companies_path = os.path.join(args.indir, "companies.json")
    if not os.path.exists(companies_path):
        raise SystemExit(f"missing {companies_path} — run synth_universe.py first")
    companies = json.load(open(companies_path))

    rng = random.Random(args.seed)
    today = date.today()
    days = trading_days(today, 260)
    years = list(range(today.year - args.years + 1, today.year + 1))
    months = [f"{y}-{m:02d}" for y in years[-2:] for m in range(1, 13)][-18:]
    quarters = []
    year, quarter = today.year, 3
    for _ in range(args.quarters):
        quarters.append((year, quarter))
        quarter -= 1
        if quarter == 0:
            quarter, year = 4, year - 1
    quarters.reverse()

    os.makedirs(args.out, exist_ok=True)
    for sub in ("mining", "quarterly", "index_daily", "broker_top"):
        os.makedirs(os.path.join(args.out, sub), exist_ok=True)

    quarterly, quarterly_dates = make_quarterly(rng, companies, quarters)
    indices = make_index_series(rng, days)
    broker_top = make_broker_top(rng, companies, days, min(len(companies), 60))

    simple = {
        "banking.json": make_banking(rng, companies, years),
        "suspensions.json": make_suspensions(rng, companies, days, max(15, len(companies) // 6)),
        "corporate_actions.json": make_corporate_actions(rng, companies, days),
        "shareholders_composition.json": make_shareholders_composition(rng, companies, months),
        "filings.json": make_filings(rng, companies, days, max(80, len(companies) * 3)),
        "segments.json": make_segments(rng, companies, years),
        "free_float.json": make_free_float(rng, companies),
        "listing_performance.json": make_listing_performance(rng, companies),
        "idx_total.json": make_idx_total(rng, days, companies),
        "brokers.json": make_broker_registry(),
        "quarterly_financial_dates.json": quarterly_dates,
        "trading_days.json": {"year": today.year,
                              "holidays": sorted(f"{m:02d}-{d:02d}" for m, d in IDX_HOLIDAYS_2026),
                              "trading_days": [str(d) for d in days]},
    }
    for name, payload in simple.items():
        json.dump(payload, open(os.path.join(args.out, name), "w"))

    for symbol, rows in quarterly.items():
        json.dump(rows, open(os.path.join(args.out, "quarterly", symbol.replace(".JK", "") + ".json"), "w"))
    for code, series in indices.items():
        json.dump(series, open(os.path.join(args.out, "index_daily", code + ".json"), "w"))
    for symbol, payload in broker_top.items():
        json.dump(payload, open(os.path.join(args.out, "broker_top", symbol.replace(".JK", "") + ".json"), "w"))

    mining = make_mining(rng, args.mining_companies, args.mining_sites,
                         args.mining_licenses, args.mining_auctions, years)
    for name, payload in mining.items():
        json.dump(payload, open(os.path.join(args.out, "mining", name), "w"))

    banks = len(simple["banking.json"])
    print(f"extended synthetic datasets -> {args.out}")
    print(f"  banking rows: {banks} ({len(set(r['symbol'] for r in simple['banking.json']))} banks × {len(years)} years)")
    print(f"  suspensions: {len(simple['suspensions.json'])} · corporate actions: {len(simple['corporate_actions.json'])}")
    print(f"  shareholder panels: {len(simple['shareholders_composition.json'])} · filings: {len(simple['filings.json'])}")
    print(f"  companies with segments: {len(simple['segments.json'])} · quarterly series: {len(quarterly)}")
    print(f"  index series: {len(indices)} · broker_top symbols: {len(broker_top)}")
    print(f"  mining: {len(mining['companies.json'])} companies, {len(mining['sites.json'])} sites, "
          f"{len(mining['licenses.json'])} licences, {len(mining['license_auctions.json'])} auctions, "
          f"{len(mining['commodity_prices.json'])} price points")
    print(f"  trading days modelled: {len(days)} (IDX 2026 holidays excluded)")


if __name__ == "__main__":
    main()
