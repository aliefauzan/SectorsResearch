#!/usr/bin/env python3
"""
Generate a synthetic IDX-shaped universe in Sectors' response schema.

The OpenAPI fixtures give you one *real* example per endpoint — perfect for
shape correctness, useless for volume. This generates as many companies,
price series, broker rows and news items as you want, using the same field
names and units the live API uses, so you can build screeners, backtests,
anomaly detectors and dashboards before you ever spend a credit.

Deterministic: the same --seed always produces the same universe.

    python3 src/synth_universe.py --companies 300 --days 180 --out synth/
    python3 src/synth_universe.py --companies 950 --days 365 --seed 7 --out synth/

Outputs (all JSON, all in Sectors field naming):
    companies.json        screener rows       (/v2/companies/ shape)
    daily/<SYM>.json      daily OHLC series   (/v2/daily/{symbol}/ shape)
    foreign_flow.json     net foreign inflow  (/v2/foreign-flow/{symbol}/ shape)
    broker_summary.json   per-broker rows     (/v2/broker-summary/{symbol}/ shape)
    news.json             news articles       (/v2/news/ shape)
    subsectors.json       taxonomy            (/v2/subsectors/ shape)

Caveat: the numbers are plausible, not real. Never present synthetic output as
market data — use it for development, load tests, and demo fallbacks only.
"""
import argparse
import json
import math
import os
import random
import string
from datetime import date, timedelta

# Real IDX taxonomy slugs, so sector filters exercise the same code paths.
TAXONOMY = [
    ("financials", "banks", "Banks & Credit Services"),
    ("financials", "insurance", "Insurance"),
    ("financials", "financing-service", "Financing Service"),
    ("basic-materials", "basic-materials", "Basic Materials"),
    ("energy", "oil-gas-coal", "Oil, Gas & Coal"),
    ("energy", "alternative-energy", "Alternative Energy"),
    ("consumer-non-cyclicals", "food-beverage", "Food & Beverage"),
    ("consumer-non-cyclicals", "tobacco", "Tobacco"),
    ("consumer-cyclicals", "retailing", "Retailing"),
    ("consumer-cyclicals", "automobiles-components", "Automobiles & Components"),
    ("healthcare", "healthcare-equipment-providers", "Healthcare Equipment & Providers"),
    ("healthcare", "pharmaceuticals-health-care-research", "Pharmaceuticals"),
    ("industrials", "industrial-goods", "Industrial Goods"),
    ("infrastructures", "telecommunication", "Telecommunication"),
    ("infrastructures", "heavy-constructions-civil-engineering", "Heavy Constructions"),
    ("properties-real-estate", "properties-real-estate", "Properties & Real Estate"),
    ("technology", "software-it-services", "Software & IT Services"),
    ("transportation-logistic", "transportation", "Transportation"),
]

BROKERS = [
    ("YP", "domestic", "retail"), ("PD", "domestic", "retail"), ("CC", "domestic", "mixed"),
    ("MG", "domestic", "retail"), ("KZ", "foreign", "institutional"), ("CS", "foreign", "institutional"),
    ("ZP", "foreign", "institutional"), ("BK", "foreign", "institutional"), ("DR", "domestic", "mixed"),
    ("NI", "domestic", "retail"), ("AK", "foreign", "institutional"), ("RX", "foreign", "institutional"),
]

TAGS = ["blue-chip", "dividend", "52-w-high", "52-w-low", "esg-under-25",
        "public-float-under-25", "top-90d-transaction-value", "high-growth"]

INDICES = ["LQ45", "IDX30", "KOMPAS100", "IDXHIDIV20", "IDXESGL", "SRIKEHATI", "IDXQ30"]

HEADLINES = [
    "{name} reports {pct}% growth in quarterly revenue",
    "{name} announces dividend of IDR {amt} per share",
    "Analysts raise target price on {sym} after strong earnings",
    "{name} completes expansion in {sector} segment",
    "{sym} shares move on heavy foreign broker activity",
    "{name} signs strategic partnership to expand {sector} footprint",
]

NAME_PARTS = ["Sinar", "Cipta", "Nusa", "Mitra", "Bumi", "Karya", "Graha", "Aneka", "Surya", "Prima"]
NAME_SUFFIX = ["Sejahtera", "Makmur", "Abadi", "Persada", "Utama", "Lestari"]


def trading_days(end, count):
    """Weekdays only — a good enough proxy for the IDX calendar."""
    days, cursor = [], end
    while len(days) < count:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor -= timedelta(days=1)
    return sorted(days)


def make_symbol(rng, used):
    while True:
        symbol = "".join(rng.choice(string.ascii_uppercase) for _ in range(4))
        if symbol not in used:
            used.add(symbol)
            return symbol


def make_company(rng, symbol, sector, sub_sector, industry):
    """One screener row, matching /v2/companies/ field names and IDR units."""
    price = rng.choice([rng.randint(50, 500), rng.randint(500, 3000), rng.randint(3000, 15000)])
    shares = rng.randint(2, 400) * 10 ** 9
    market_cap = price * shares
    revenue = int(market_cap * rng.uniform(0.15, 1.6))
    earnings = int(revenue * rng.uniform(-0.05, 0.35))
    equity = int(market_cap * rng.uniform(0.2, 1.4))
    assets = int(equity * rng.uniform(1.2, 8.0))

    name = f"PT {rng.choice(NAME_PARTS)}{rng.choice(NAME_PARTS).lower()} {rng.choice(NAME_SUFFIX)} Tbk."
    row = {
        "symbol": symbol + ".JK",
        "company_name": name,
        "sector": sector,
        "sub_sector": sub_sector,
        "industry": industry,
        "sub_industry": industry,
        "listing_board": rng.choices(["Main", "Development", "Acceleration"], [0.6, 0.3, 0.1])[0],
        "listing_date": str(date(rng.randint(1995, 2025), rng.randint(1, 12), rng.randint(1, 28))),
        "market_cap": market_cap,
        "employee_num": rng.randint(50, 60000),
        "last_close_price": price,
        "daily_close_change": round(rng.gauss(0, 0.018), 6),
        "outstanding_shares": shares,
        "pe_ttm": round(market_cap / earnings, 4) if earnings > 0 else None,
        "pb_mrq": round(market_cap / equity, 4) if equity > 0 else None,
        "ps_ttm": round(market_cap / revenue, 4) if revenue > 0 else None,
        "roe_ttm": round(earnings / equity, 6) if equity > 0 else None,
        "roa_ttm": round(earnings / assets, 6) if assets > 0 else None,
        "der_mrq": round(rng.uniform(0.05, 3.5), 4),
        "total_assets_mrq": assets,
        "total_equity_mrq": equity,
        "total_revenue_mrq": revenue // 4,
        "earnings_mrq": earnings // 4,
        "yield_ttm": round(max(0.0, rng.gauss(0.03, 0.025)), 6),
        "dividend_ttm": int(max(0, price * rng.gauss(0.03, 0.02))),
        "payout_ratio": round(min(1.2, max(0.0, rng.gauss(0.4, 0.25))), 4),
        "esg_score": round(rng.uniform(8, 45), 2),
        "free_float": round(rng.uniform(0.05, 0.85), 4),
        "yoy_quarter_revenue_growth": round(rng.gauss(0.08, 0.22), 6),
        "yoy_quarter_earnings_growth": round(rng.gauss(0.10, 0.45), 6),
        "tags": rng.sample(TAGS, rng.randint(0, 3)),
        "indices": rng.sample(INDICES, rng.randint(0, 3)),
    }

    if sub_sector == "banks":
        deposits = int(assets * rng.uniform(0.6, 0.85))
        row.update({
            "net_interest_income_mrq": int(revenue * rng.uniform(0.5, 0.8) / 4),
            "gross_loan_mrq": int(deposits * rng.uniform(0.6, 1.0)),
            "total_deposit_mrq": deposits,
            "casa_ratio": round(rng.uniform(0.35, 0.82), 4),
            "loan_to_deposit_ratio": round(rng.uniform(0.6, 1.05), 4),
            "net_interest_margin": round(rng.uniform(0.02, 0.08), 4),
            "capital_adequacy_ratio": round(rng.uniform(0.15, 0.30), 4),
        })
    return row


def make_price_series(rng, company, days):
    """Geometric-Brownian-motion OHLC series, in /v2/daily/{symbol}/ shape.

    The live endpoint returns open, high, low, close, volume and market_cap —
    not close alone — so the synthetic rows carry all six.
    """
    drift = rng.gauss(0.0003, 0.0006)
    volatility = rng.uniform(0.012, 0.045)
    shares = company["outstanding_shares"]
    price = float(company["last_close_price"])
    base_volume = max(10_000, int(company["market_cap"] / price / rng.uniform(200, 4000)))

    # Walk backwards from today's price so last_close_price stays consistent.
    closes = [price]
    for _ in range(len(days) - 1):
        closes.append(max(1.0, closes[-1] / math.exp(rng.gauss(drift, volatility))))
    closes.reverse()

    series = []
    previous_close = closes[0]
    for day, close in zip(days, closes):
        close = round(close)
        # Open gaps from the prior close; the day's range brackets both.
        open_ = max(1, round(previous_close * math.exp(rng.gauss(0, volatility / 2))))
        spread = max(1, round(close * rng.uniform(0.003, 0.02)))
        high = max(open_, close) + rng.randint(0, spread)
        low = max(1, min(open_, close) - rng.randint(0, spread))
        series.append({
            "symbol": company["symbol"],
            "date": str(day),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": int(base_volume * math.exp(rng.gauss(0, 0.7))),
            "market_cap": close * shares,
        })
        previous_close = close
    return series


def make_foreign_flow(rng, company, series):
    bias = rng.gauss(0, 1)
    return [
        {
            "symbol": company["symbol"],
            "date": point["date"],
            "net_foreign_inflow": int(point["close"] * point["volume"] * rng.gauss(bias * 0.05, 0.25)),
        }
        for point in series
    ]


def make_broker_rows(rng, company, series, per_day):
    rows = []
    for point in series[-per_day:]:
        traded_value = point["close"] * point["volume"]
        for code, origin, cohort in rng.sample(BROKERS, rng.randint(3, 7)):
            share = rng.uniform(0.02, 0.30)
            buy = int(traded_value * share * rng.uniform(0.3, 0.7))
            sell = int(traded_value * share) - buy
            rows.append({
                "symbol": company["symbol"],
                "date": point["date"],
                "broker_code": code,
                "origin": origin,
                "cohort": cohort,
                "buy_value": buy,
                "sell_value": sell,
                "net_value": buy - sell,
                "avg_price": point["close"],
            })
    return rows


def make_news(rng, companies, count, days):
    articles = []
    for i in range(count):
        company = rng.choice(companies)
        articles.append({
            "id": "synth-%06d" % i,
            "title": rng.choice(HEADLINES).format(
                name=company["company_name"].replace("PT ", "").replace(" Tbk.", ""),
                sym=company["symbol"].replace(".JK", ""),
                sector=company["sub_sector"].replace("-", " "),
                pct=rng.randint(3, 45),
                amt=rng.randint(10, 500),
            ),
            "source": rng.choice(["idnfinancials", "kontan", "bisnis", "emitennews"]),
            "timestamp": "%s %02d:%02d:00" % (rng.choice(days), rng.randint(7, 18), rng.randint(0, 59)),
            "symbols": [company["symbol"]],
            "sector": company["sector"],
            "sub_sector": company["sub_sector"],
            "tags": rng.sample(TAGS, rng.randint(1, 3)),
            "sentiment": rng.choice(["positive", "neutral", "negative"]),
        })
    return articles


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--companies", type=int, default=300)
    ap.add_argument("--days", type=int, default=180)
    ap.add_argument("--news", type=int, default=500)
    ap.add_argument("--broker-days", type=int, default=14, help="days of per-broker detail (the API caps at 14)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--as-of", default="2026-09-04", metavar="YYYY-MM-DD",
                    help="anchor date for the price window. Defaults to the date the "
                         "committed synth/ was built so a diff against it is a real "
                         "reproducibility check; pass `today` for a window ending now.")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "synth"))
    args = ap.parse_args()

    if args.companies < 1 or args.days < 1:
        raise SystemExit("--companies and --days must be >= 1 "
                         f"(got companies={args.companies}, days={args.days})")
    if args.as_of == "today":
        anchor = date.today()
    else:
        try:
            anchor = date(*(int(p) for p in args.as_of.split("-")))
        except (TypeError, ValueError):
            raise SystemExit(f"--as-of must be YYYY-MM-DD or `today`, got {args.as_of!r}")

    rng = random.Random(args.seed)
    days = trading_days(anchor, args.days)
    for sub in ("market", "flow"):
        os.makedirs(os.path.join(args.out, sub), exist_ok=True)
    os.makedirs(os.path.join(args.out, "market", "daily"), exist_ok=True)

    used, companies = set(), []
    for _ in range(args.companies):
        sector, sub_sector, industry = rng.choice(TAXONOMY)
        companies.append(make_company(rng, make_symbol(rng, used), sector, sub_sector, industry))

    companies.sort(key=lambda c: -c["market_cap"])
    for rank, company in enumerate(companies, 1):
        company["market_cap_rank"] = rank

    foreign_flow, broker_rows = [], []
    for company in companies:
        series = make_price_series(rng, company, days)
        ticker = company["symbol"].replace(".JK", "")
        with open(os.path.join(args.out, "market", "daily", ticker + ".json"), "w") as fh:
            json.dump(series, fh)
        foreign_flow.extend(make_foreign_flow(rng, company, series))
        broker_rows.extend(make_broker_rows(rng, company, series, args.broker_days))

    outputs = {
        "market/companies.json": companies,
        "flow/foreign_flow.json": foreign_flow,
        "flow/broker_summary.json": broker_rows,
        "market/news.json": make_news(rng, companies, args.news, [str(d) for d in days]),
        "market/subsectors.json": [{"sector": s, "sub_sector": ss} for s, ss, _ in TAXONOMY],
    }
    for name, payload in outputs.items():
        with open(os.path.join(args.out, *name.split("/")), "w") as fh:
            json.dump(payload, fh)

    print("synthetic universe -> %s" % args.out)
    print("  %d companies · %d trading days" % (len(companies), len(days)))
    print("  %d price points · %d broker rows · %d news items"
          % (len(companies) * len(days), len(broker_rows), len(outputs["market/news.json"])))


if __name__ == "__main__":
    main()
