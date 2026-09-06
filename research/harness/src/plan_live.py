#!/usr/bin/env python3
"""
Build `plan-live.json` — the calls that finish coverage of all 70 documented endpoints.

`plan.json` reaches 40 of them. The remaining 30 all need a path parameter (a broker code,
a mining slug, a WIUP code, an SGX symbol) or a required query parameter, and the only safe
source for those values is a payload already on disk: a 404 on a guessed identifier costs a
credit, so nothing here is invented.

    python3 src/plan_live.py                 # writes plans/plan-live.json from recorded/
    python3 src/capture.py --plan plans/plan-live.json --budget 60

Run it again after a capture: values that were unresolvable on the first pass (an SGX or KLSE
symbol needs its market's company list fetched first) resolve on the second, and the plan
grows. Calls already recorded are skipped by capture.py, so re-running costs nothing.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # harness/
RECORDED = os.path.join(ROOT, "recorded")


def load(slug):
    path = os.path.join(RECORDED, slug + ".json")
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        return json.load(fh)


def rows(payload):
    """Every recording is either a bare list or {results, pagination}."""
    if payload is None:
        return []
    if isinstance(payload, dict):
        payload = payload.get("results", payload.get("data", []))
    return payload if isinstance(payload, list) else []


def first(payload, field, where=None):
    for row in rows(payload):
        if not isinstance(row, dict):
            continue
        if where and not where(row):
            continue
        value = row.get(field)
        if value:
            return value
    return None


def build():
    unresolved = []

    def need(name, value):
        if not value:
            unresolved.append(name)
        return value

    brokers = load("v2_brokers")
    mining_companies = load("v2_mining_companies")
    mining_sites = load("v2_mining_sites")
    auctions = load("v2_mining_license-auctions")
    reserves = load("v2_mining_resources-reserves")
    sgx = load("v2_sgx_companies__limit-100_order_by--market_cap")
    klse_sectors = load("v2_klse_sectors")

    broker_code = need("broker_code", first(brokers, "code"))
    # A slug that appears in the sites table is one with operational data behind it,
    # which the bare company list does not guarantee.
    # Financials, ownership and sales-destination only hold data for *listed* miners —
    # `pt-adaro-indonesia` (a site operator) 404s on two of the five. Prefer a slug whose
    # row carries a ticker.
    with_financials = load("v2_mining_companies__has_financials-true_limit-20")
    mining_slug = need("mining company slug",
                       first(with_financials, "slug")
                       or first(mining_companies, "slug", where=lambda r: r.get("symbol"))
                       or first(mining_sites, "company_slug"))
    site_slug = need("mining site slug", first(mining_sites, "slug"))
    wiup_code = need("wiup_code", first(auctions, "wiup_code"))
    province = need("province", next(iter(reserves), None) if isinstance(reserves, dict) else None)
    sgx_symbol = need("SGX symbol", first(sgx, "symbol"))
    klse_sector = need("KLSE sector",
                       next((s for s in rows(klse_sectors) if isinstance(s, str)), None))
    # Second pass only: available once /v2/klse/companies/ has been recorded.
    klse_symbol = first(load(f"v2_klse_companies__sector-{klse_sector}"), "symbol") if klse_sector else None

    # Declared cost per endpoint, straight from the spec, so a plan entry can never
    # under-state a call the way an earlier version did: it hardcoded 1 credit for
    # /v2/broker-activity/{broker_code}/top/, which the spec and the portal both put at 2.
    with open(os.path.join(ROOT, "fixtures", "_index.json")) as fh:
        catalog = json.load(fh)
    declared = {}
    for template, meta in catalog.items():
        match = re.search(r"(\d+)\s*API credit", meta.get("credit_cost") or "")
        declared[template] = int(match.group(1)) if match else 1
    templates = [(re.compile("^" + re.sub(r"\{[^}]+\}", "[^/]+", t) + "$"), t)
                 for t in sorted(declared, key=len, reverse=True)]

    def declared_cost(path):
        for regex, template in templates:
            if regex.match(path):
                return declared[template]
        return 1

    calls = []

    def add(path, params=None, cost=None, note=""):
        calls.append({"tier": 5, "path": path, "params": params or {},
                      "est_cost": cost if cost is not None else declared_cost(path),
                      "note": note})

    # --- no path or query parameters at all -------------------------------------
    add("/v2/companies/list_companies_with_segments/", note="every company's revenue segments")
    add("/v2/sgx/subsectors/", note="SGX taxonomy")
    add("/v2/sgx/tags/", note="SGX taxonomy")
    add("/v2/mining/global-commodity/", {"commodity_type": "Coal", "limit": 20},
        note="constrained; the endpoint defaults limit to 20 anyway")

    # --- the two calls plan.json sent without their required parameters ---------
    add("/v2/mining/total-production/", {"commodity_type": "Coal"},
        note="commodity_type is required — plan.json omitted it and got a free 400")
    add("/v2/mining/exports/", {"commodity_type": "Coal", "year": 2024},
        note="year and commodity_type both required")

    # --- IDX, identifiers already proven by tier 0/1 -----------------------------
    add("/v2/company/get_quarterly_financial_dates/{}/".format("BBCA"),
        note="the per-symbol form of the universe sweep")
    # `/v2/company/report/`, `/v2/subsector/report/`, `/v2/sgx/company/report/` and
    # `/v2/klse/company/report/` are NOT list endpoints. The spec declares their `symbol` /
    # `sub_sector` as a *path* parameter, so each is a duplicate entry for the templated
    # path below it. Called bare they return a free 400 ("Please provide a valid stock
    # symbol"). Confirmed live; not planned again.

    if broker_code:
        add(f"/v2/broker-activity/{broker_code}/", {"start": "2026-08-01", "end": "2026-08-14"},
            note="≤14-day window keeps this at 1 credit")
        add(f"/v2/broker-activity/{broker_code}/top/", {"start": "2026-08-01", "end": "2026-08-14"})
    add("/v2/broker-summary/BBCA/", {"start": "2026-08-01", "end": "2026-08-14"},
        note="non-top form; ≤14 days")
    # Listing performance holds data only for tickers listed after May 2005, so the
    # blue chips in plan.json's basket all 404 (billed). The spec's own example is BREN.
    add("/v2/listing-performance/BREN/",
        note="post-2005 listing; BBCA/BBRI/TLKM/ADRO all 404 here")

    # --- mining, every remaining shape ------------------------------------------
    # Discovery call: the detail endpoints (financials, performance, sales-destination)
    # 404 for most slugs — a 404 that costs a credit each time. `has_financials` filters
    # the company list down to the ones that actually carry those records, so the detail
    # calls below can be aimed rather than guessed.
    add("/v2/mining/companies/", {"has_financials": "true", "limit": 20},
        note="discovery: slugs that actually have detail records behind them")
    if mining_slug:
        add(f"/v2/mining/companies/{mining_slug}/")
        add(f"/v2/mining/companies/financials/{mining_slug}/")
        add(f"/v2/mining/companies/ownership/{mining_slug}/")
        add(f"/v2/mining/companies/performance/{mining_slug}/", {"commodity_type": "Coal"})
        add(f"/v2/mining/sales-destination/{mining_slug}/")
    if site_slug:
        add(f"/v2/mining/sites/{site_slug}/")
    if wiup_code:
        add(f"/v2/mining/license-auctions/{wiup_code}/")
    if province:
        add(f"/v2/mining/resources-reserves/{province}/", {"commodity_type": "Coal"})

    # --- SGX ---------------------------------------------------------------------
    add("/v2/sgx/companies/top/", {"classifications": "market_cap", "n_stock": 5},
        note="SGX/KLSE take dividend_yield|revenue|earnings|market_cap|pe — NOT the IDX "
             "top_gainers/top_losers vocabulary; this family bills per classification")
    add("/v2/sgx/filings/", {"limit": 20})
    add("/v2/sgx/news/", {"limit": 20})
    add("/v2/sgx/buybacks/", {"limit": 20})
    add("/v2/sgx/short-sell/", {"limit": 20})
    if sgx_symbol:
        add(f"/v2/sgx/company/report/{sgx_symbol}/", {"sections": "overview"})
        add(f"/v2/sgx/daily/{sgx_symbol}/", {"start": "2026-08-01", "end": "2026-08-14"})

    # --- KLSE --------------------------------------------------------------------
    if klse_sector:
        add("/v2/klse/companies/", {"sector": klse_sector})
    add("/v2/klse/companies/top/", {"classifications": "market_cap", "n_stock": 5})
    if klse_symbol:
        add(f"/v2/klse/company/report/{klse_symbol}/", {"sections": "overview"})
    else:
        unresolved.append("KLSE symbol (run this plan once, then re-run plan_live.py)")

    plan = {
        "name": "Coverage completion — the 30 endpoints plan.json never calls",
        "grant": 1000,
        "notes": [
            "Every path parameter here is read out of a payload already in recorded/.",
            "Nothing is guessed: a 404 on an invented identifier costs 1 credit.",
            "Report endpoints are constrained to sections=overview; they bill per section.",
            "Re-run plan_live.py after a capture to pick up identifiers that were not yet on disk.",
        ],
        "resolved": {
            "broker_code": broker_code, "mining_slug": mining_slug, "site_slug": site_slug,
            "wiup_code": wiup_code, "province": province, "sgx_symbol": sgx_symbol,
            "klse_sector": klse_sector, "klse_symbol": klse_symbol,
        },
        "calls": calls,
    }
    return plan, unresolved


if __name__ == "__main__":
    plan, unresolved = build()
    out = os.path.join(ROOT, "plans", "plan-live.json")
    with open(out, "w") as fh:
        json.dump(plan, fh, indent=2)
        fh.write("\n")
    print(f"wrote {out}: {len(plan['calls'])} calls, "
          f"{sum(c['est_cost'] for c in plan['calls'])} estimated credits")
    for key, value in plan["resolved"].items():
        print(f"  {key:14} {value}")
    if unresolved:
        print("\nunresolved (no recording to read them from yet):")
        for item in unresolved:
            print("  -", item)
