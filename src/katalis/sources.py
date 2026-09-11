#!/usr/bin/env python3
"""
One shared way to read a Sectors payload for the four pillars, so no parser is written twice.

`recorded/` (what the 6 Sep 2026 capture paid for) and `synth/` (120 generated companies)
disagree about shape in eight measured places, and every one of them is a KeyError waiting
for the demo. They are handled here and nowhere else: `pillars.py` never sees a raw payload
and `planner.py` never reaches into a dict with `[]`.

    from sources import load, results_of, broker_flow, registry_index

The eight measured divergences, each re-checked against the payloads on disk:

  1. index-daily carries `price` in `recorded/` and `close` in `synth/`, and the code is
     `IHSG` against `ihsg`. Getting this wrong silently removes the wrong market move.
  2. foreign-flow is `{symbol, start, end, data[]}` in `recorded/` and a flat, all-symbol
     list in `synth/` — one needs unwrapping, the other needs filtering.
  3. broker-summary day rows are `nval`/`nlot`/`bval` in `recorded/`, nested under
     `data[].summary[]`, and flat `net_value`/`buy_value` rows in `synth/`.
  4. **`synth/` has no lot counts at all.** Float absorbed is therefore recorded-only, and
     asking for it on synth returns None rather than a number that means nothing. This is
     the divergence most likely to be papered over, so it is asserted in the gates.
  5. `/v2/brokers/` has no `origin` in `recorded/` but does in `synth/`; `is_foreign` is the
     field both carry and the one the join uses.
  6. filings carry `share_percentage_transaction` in `recorded/` and only
     `share_percentage_before`/`_after` in `synth/`; the normalizer derives it when absent.
     Dates are `timestamp` against `date`.
  7. corporate actions are a dict of seven typed lists in `recorded/` (each with its own
     date key — `agm_date`, `ex_date`, `date`) and flat `{symbol, date, action_type}` rows
     in `synth/`.
  8. news is `{results, pagination}` in `recorded/` and a bare list in `synth/`; `dimension`
     is recorded-only, `sentiment` is synth-only.

Normalization fills a missing field with None rather than dropping the key, so both sources
present the same key set and no caller can depend on a field only one of them has.

    python3 sources.py     # asserts the two sources normalize to identical key sets

Lineage: the divergence-table idea and several normalizers come from
`src/pump-and-dump/sources.py`. The datasets differ enough — daily broker flow, free float,
index, filings, corporate actions — that this is a sibling, not an import.
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
HARNESS = os.path.join(ROOT, "research", "harness")
RECORDED = os.path.join(HARNESS, "recorded")
SYNTH = os.path.join(HARNESS, "synth")

#: Endpoint path per dataset — the citation every figure on a card has to carry.
ENDPOINT = {
    "daily": "/v2/daily/{symbol}/",
    "index_daily": "/v2/index-daily/ihsg/",
    "broker_flow": "/v2/broker-summary/{symbol}/",
    "broker_top": "/v2/broker-summary/{symbol}/top/",
    "brokers": "/v2/brokers/",
    "free_float": "/v2/free-float/",
    "foreign_flow": "/v2/foreign-flow/{symbol}/",
    "news": "/v2/news/",
    "filings": "/v2/filings/",
    "corporate_actions": "/v2/company/corporate-actions/{symbol}/",
    "suspensions": "/v2/suspensions/",
    "companies": "/v2/companies/",
    "company_report": "/v2/company/report/{symbol}/",
}

#: Credits per call, from research/docs/api/05-credit-budget.md. The planner spends against
#: this table, so a plan that looks cheap on paper is cheap in the ledger too.
COST = {
    "daily": 1, "index_daily": 1, "broker_flow": 1, "broker_top": 2, "brokers": 1,
    "free_float": 1, "foreign_flow": 1, "news": 1, "filings": 1,
    "corporate_actions": 1, "suspensions": 1, "companies": 1, "company_report": 1,
}


#: How much of a symbol's gross traded value may come from broker codes the registry does not
#: carry before the origin and cohort split stops being trustworthy. Measured at 0.08% on the
#: recorded BBCA tape (one code, `JB`), so this is roughly sixty times the observed gap.
UNMAPPED_TOLERANCE = 0.05


class NotRecorded(Exception):
    """Asked for a payload this source does not hold.

    Raised rather than returning an empty list, because "no rows" and "never fetched" lead
    to different sentences on the card, and only the caller knows which one it is looking at.
    """


def _read(path):
    if not os.path.exists(path):
        raise NotRecorded(path)
    with open(path) as handle:
        return json.load(handle)


def bare(symbol):
    """`BBCA.JK` and `BBCA` are the same stock. Payload rows use the suffix; the CLI does not."""
    return (symbol or "").upper().replace(".JK", "")


def _widest(*patterns):
    """First pattern that matches anything, and within it the file holding the most rows.

    `capture.py` names a recording after its query, so a call made with `start`/`end`
    lands as `v2_daily_LIFE__end-…_start-….json` rather than `v2_daily_LIFE.json`. The
    patterns are tried in order of preference — a symbol-specific capture before a
    market-wide one — and ties inside a pattern go to the longest series, because a
    wider window is what the 45-day baseline needs.
    """
    for pattern in patterns:
        hits = sorted(glob.glob(os.path.join(RECORDED, pattern)))
        if not hits:
            continue
        if len(hits) == 1:
            return hits[0]
        return max(hits, key=lambda path: len(results_of(_read(path)) or ()))
    return None


def load(source, dataset, symbol=None):
    """Read one dataset from `recorded/` or `synth/`. Raises NotRecorded when absent."""
    sym = bare(symbol)
    if source == "recorded":
        slugs = {
            "daily": f"v2_daily_{sym}",
            "index_daily": "v2_index-daily_ihsg",
            "broker_top": f"v2_broker-summary_{sym}_top",
            "brokers": "v2_brokers",
            "free_float": "v2_free-float",
            "foreign_flow": f"v2_foreign-flow_{sym}",
            "news": "v2_news__extension-idx",
            "filings": "v2_filings",
            "corporate_actions": f"v2_company_corporate-actions_{sym}",
            "suspensions": "v2_suspensions",
            # The full report and the 1-credit `sections=overview` slice were both captured
            # for some symbols. Prefer the full one: it is the only place
            # `outstanding_shares` lives, and preferring it here means the product uses the
            # exact denominator whenever it has been paid for.
            "company_report": (f"v2_company_report_{sym}"
                               if os.path.exists(os.path.join(
                                   RECORDED, f"v2_company_report_{sym}.json"))
                               else f"v2_company_report_{sym}__sections-overview"),
        }
        if dataset == "broker_flow":
            # The daily broker summary was captured with an explicit window, so its filename
            # carries the dates.
            hit = _widest(f"v2_broker-summary_{sym}__*.json")
            if not hit:
                raise NotRecorded(f"recorded has no daily broker summary for {sym}")
            return _read(hit)
        if dataset in ("daily", "index_daily", "news", "filings", "company_report"):
            # A windowed or filtered capture carries its query in the filename. Prefer the
            # symbol-specific file, then the widest bare one; `sections=financials` beats
            # `sections=overview` because only the former carries `outstanding_shares`.
            index = "ihsg"
            patterns = {
                "daily": (f"v2_daily_{sym}.json", f"v2_daily_{sym}__*.json"),
                "index_daily": (f"v2_index-daily_{index}__*.json",
                                f"v2_index-daily_{index}.json"),
                "news": (f"v2_news__*symbols-{sym}*.json", "v2_news__extension-idx.json",
                         "v2_news__*.json"),
                "filings": (f"v2_filings__*symbol-{sym}*.json", "v2_filings.json",
                            "v2_filings__*.json"),
                "company_report": (f"v2_company_report_{sym}.json",
                                   f"v2_company_report_{sym}__sections-financials.json",
                                   f"v2_company_report_{sym}__sections-overview.json"),
            }[dataset]
            hit = _widest(*patterns)
            if not hit:
                raise NotRecorded(f"recorded has no {dataset} for {sym or 'the market'}")
            return _read(hit)
        if dataset == "companies":
            hits = sorted(glob.glob(os.path.join(RECORDED, "v2_companies__*.json")))
            if not hits:
                raise NotRecorded("recorded has no screener payload")
            return [row for path in hits for row in results_of(_read(path))]
        if dataset not in slugs:
            raise NotRecorded(f"recorded has no {dataset}")
        return _read(os.path.join(RECORDED, slugs[dataset] + ".json"))

    if source == "synth":
        paths = {
            "daily": os.path.join(SYNTH, "market", "daily", f"{sym}.json"),
            "index_daily": os.path.join(SYNTH, "market", "index_daily", "ihsg.json"),
            "broker_flow": os.path.join(SYNTH, "flow", "broker_summary.json"),
            "broker_top": os.path.join(SYNTH, "flow", "broker_top", f"{sym}.json"),
            "brokers": os.path.join(SYNTH, "flow", "brokers.json"),
            "free_float": os.path.join(SYNTH, "market", "free_float.json"),
            "foreign_flow": os.path.join(SYNTH, "flow", "foreign_flow.json"),
            "news": os.path.join(SYNTH, "market", "news.json"),
            "filings": os.path.join(SYNTH, "flow", "filings.json"),
            "corporate_actions": os.path.join(SYNTH, "company", "corporate_actions.json"),
            "suspensions": os.path.join(SYNTH, "company", "suspensions.json"),
            "companies": os.path.join(SYNTH, "market", "companies.json"),
        }
        if dataset not in paths:
            raise NotRecorded(f"synth has no {dataset}")
        return _read(paths[dataset])
    raise ValueError(f"unknown source {source!r}")


def results_of(payload):
    """The rows of a payload, whether it wraps them in `results`/`data` or is already a list."""
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("results", "data"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def pagination_of(payload):
    return payload.get("pagination") if isinstance(payload, dict) else None


# --------------------------------------------------------------------------- normalizers

def normalize_daily(row):
    return {
        "symbol": bare(row.get("symbol")),
        "date": row.get("date"),
        "open": row.get("open"),
        "high": row.get("high"),
        "low": row.get("low"),
        "close": row.get("close"),
        "volume": row.get("volume"),
        "market_cap": row.get("market_cap"),
    }


def normalize_index(row):
    """Divergence 1: `price` in recorded, `close` in synth; the code case differs too."""
    return {
        "index_code": (row.get("index_code") or "").upper(),
        "date": row.get("date"),
        "close": row.get("price") if row.get("price") is not None else row.get("close"),
    }


def normalize_broker(row):
    """Divergence 5: `origin` is synth-only, so `is_foreign` is what the join may use."""
    return {
        "code": row.get("code"),
        "name": row.get("name"),
        "is_foreign": row.get("is_foreign"),
        "cohort": row.get("cohort"),
        "license_type": row.get("license_type"),
    }


def normalize_flow_row(date, row):
    """Divergences 3 and 4: one flat shape for a broker's day, lots absent on synth.

    `net_lot` stays None rather than being back-derived from value and price. Float absorbed
    is measured in lots, and a lot count invented from a rounded average price would put a
    fabricated percentage on the card — the one sentence the product cannot afford to fake.
    """
    net_value = row.get("nval") if row.get("nval") is not None else row.get("net_value")
    buy_value = row.get("bval") if row.get("bval") is not None else row.get("buy_value")
    sell_value = row.get("sval") if row.get("sval") is not None else row.get("sell_value")
    avg = row.get("bavg_per_share")
    if avg is None:
        avg = row.get("avg_price")
    return {
        "date": date,
        "broker_code": row.get("broker_code"),
        "buy_idr": buy_value,
        "sell_idr": sell_value,
        "net_idr": net_value,
        "net_lot": row.get("nlot"),
        "buy_lot": row.get("blot"),
        "buy_freq": row.get("bfreq"),
        "avg_buy_price": avg,
        "origin_inline": row.get("origin"),
        "cohort_inline": row.get("cohort"),
    }


def normalize_filing(row):
    """Divergence 6: derive the transaction percentage synth does not carry, date key differs."""
    before = row.get("share_percentage_before")
    after = row.get("share_percentage_after")
    moved = row.get("share_percentage_transaction")
    if moved is None and isinstance(before, (int, float)) and isinstance(after, (int, float)):
        moved = after - before
    stamp = row.get("timestamp") or row.get("date")
    return {
        "symbol": bare(row.get("symbol")),
        "date": (stamp or "")[:10] or None,
        "holder_name": row.get("holder_name"),
        "holder_type": row.get("holder_type"),
        "transaction_type": row.get("transaction_type"),
        "share_percentage_before": before,
        "share_percentage_after": after,
        "share_percentage_transaction": moved,
        "transaction_value": row.get("transaction_value"),
        "source": row.get("source"),
    }


def normalize_news(row):
    """Divergence 8: `dimension` is recorded-only, `sentiment` is synth-only. Both keys exist."""
    return {
        "title": row.get("title"),
        "body": row.get("body"),
        "source": row.get("source"),
        "timestamp": row.get("timestamp"),
        "symbols": [bare(s) for s in (row.get("symbols") or [])],
        "sector": row.get("sector"),
        "sub_sector": row.get("sub_sector"),
        "tags": row.get("tags") or [],
        "dimension": row.get("dimension"),
        "sentiment": row.get("sentiment"),
    }


def normalize_suspension(row):
    return {
        "symbol": bare(row.get("symbol")),
        "company_name": row.get("company_name"),
        "suspension_date": row.get("suspension_date"),
        "resumption_date": row.get("resumption_date"),
        "reason": row.get("reason"),
        "pdf_url": row.get("pdf_url") or row.get("notice_url"),
    }


# ------------------------------------------------------------------------- typed readers

def daily(source, symbol):
    """Ascending OHLCV rows for one symbol."""
    rows = [normalize_daily(r) for r in results_of(load(source, "daily", symbol))]
    return sorted((r for r in rows if r["date"] and r["close"] is not None),
                  key=lambda r: r["date"])


def index_daily(source):
    rows = [normalize_index(r) for r in results_of(load(source, "index_daily"))]
    return sorted((r for r in rows if r["date"] and r["close"] is not None),
                  key=lambda r: r["date"])


def broker_flow(source, symbol):
    """Per-broker, per-day rows for one symbol — the spine of Pilar 1.

    Recorded nests them under `data[].summary[]` with one entry per trading day; synth keeps
    one flat all-symbol list. Both come back as the same flat, dated rows.
    """
    payload = load(source, "broker_flow", symbol)
    sym = bare(symbol)
    rows = []
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        for day in payload["data"]:
            for entry in (day.get("summary") or []):
                rows.append(normalize_flow_row(day.get("date"), entry))
    else:
        for entry in results_of(payload):
            if bare(entry.get("symbol")) == sym:
                rows.append(normalize_flow_row(entry.get("date"), entry))
    return sorted((r for r in rows if r["date"] and r["broker_code"]),
                  key=lambda r: (r["date"], r["broker_code"]))


def registry_index(source):
    """`{code: {name, is_foreign, cohort}}` — the zero-credit join behind origin and cohort."""
    index = {}
    for raw in results_of(load(source, "brokers")):
        row = normalize_broker(raw)
        if row["code"]:
            index[row["code"]] = row
    return index


def free_float(source, symbol=None):
    """One symbol's float, or the whole market when `symbol` is None."""
    rows = results_of(load(source, "free_float"))
    table = {bare(r.get("symbol")): r.get("free_float") for r in rows if r.get("symbol")}
    return table if symbol is None else table.get(bare(symbol))


def foreign_flow(source, symbol):
    """Divergence 2: unwrap the recorded envelope, filter the synth all-symbol list."""
    payload = load(source, "foreign_flow", symbol)
    sym = bare(symbol)
    rows = []
    for row in results_of(payload):
        if "symbol" in row and bare(row.get("symbol")) != sym:
            continue
        if row.get("date"):
            rows.append({"date": row["date"],
                         "net_foreign_inflow": row.get("net_foreign_inflow")})
    return sorted(rows, key=lambda r: r["date"])


def news_for(source, symbol, start=None, end=None):
    """Company news mentioning `symbol`, windowed on ISO date prefixes."""
    sym = bare(symbol)
    hits = []
    for raw in results_of(load(source, "news")):
        row = normalize_news(raw)
        if sym not in row["symbols"]:
            continue
        stamp = (row["timestamp"] or "")[:10]
        if (start and stamp < start) or (end and stamp > end):
            continue
        hits.append(row)
    return sorted(hits, key=lambda r: r["timestamp"] or "")


def filings_for(source, symbol, start=None, end=None):
    sym = bare(symbol)
    hits = []
    for raw in results_of(load(source, "filings")):
        row = normalize_filing(raw)
        if row["symbol"] != sym or not row["date"]:
            continue
        if (start and row["date"] < start) or (end and row["date"] > end):
            continue
        hits.append(row)
    return sorted(hits, key=lambda r: r["date"])


def corporate_actions(source, symbol, start=None, end=None):
    """Divergence 7: seven typed lists with seven date keys, or flat rows. One shape out."""
    sym = bare(symbol)
    payload = load(source, "corporate_actions", symbol)
    rows = []
    if isinstance(payload, dict) and isinstance(payload.get("corporate_actions"), dict):
        for action_type, entries in payload["corporate_actions"].items():
            for entry in (entries or []):
                date = (entry.get("date") or entry.get("ex_date") or entry.get("agm_date")
                        or entry.get("payment_date"))
                rows.append({"symbol": sym, "date": date, "action_type": action_type,
                             "detail": entry})
    else:
        for entry in results_of(payload):
            if bare(entry.get("symbol")) != sym:
                continue
            rows.append({"symbol": sym, "date": entry.get("date"),
                         "action_type": entry.get("action_type"), "detail": entry})
    rows = [r for r in rows if r["date"]]
    if start:
        rows = [r for r in rows if r["date"] >= start]
    if end:
        rows = [r for r in rows if r["date"] <= end]
    return sorted(rows, key=lambda r: r["date"])


def available_symbols(source):
    """Symbols this source can actually carry a daily series for."""
    if source == "synth":
        paths = glob.glob(os.path.join(SYNTH, "market", "daily", "*.json"))
    else:
        paths = glob.glob(os.path.join(RECORDED, "v2_daily_*.json"))
    names = []
    for path in paths:
        stem = os.path.splitext(os.path.basename(path))[0]
        # `capture.py` appends the query to the slug, so `v2_daily_LIFE__end-…_start-….json`
        # is still LIFE. Everything from the double underscore on is the query, not the name.
        names.append(bare(stem.replace("v2_daily_", "").split("__")[0]))
    return sorted(set(names))


def company_name(source, symbol):
    """Best-effort display name; None when no local payload happens to carry one."""
    sym = bare(symbol)
    try:
        report = load(source, "company_report", sym)
        if isinstance(report, dict) and report.get("company_name"):
            return report["company_name"]
    except (NotRecorded, ValueError):
        pass
    for dataset in ("companies", "free_float"):
        try:
            rows = results_of(load(source, dataset))
        except (NotRecorded, ValueError):
            continue
        for row in rows:
            if isinstance(row, dict) and bare(row.get("symbol")) == sym and row.get("company_name"):
                return row["company_name"]
    return None


def shares_outstanding(source, symbol):
    """Shares in issue, as `(value, fields, exact)` — the denominator of float absorbed.

    Three places, in descending order of how much they can be trusted:

      1. `report.financials.historical_financials[].outstanding_shares` — the real figure.
         It is **not** in the `overview` section, so the cheap 1-credit overview call does
         not carry it; asking for `sections=financials` is a second credit. That cost is a
         product decision, so it is visible here rather than buried.
      2. the screener's own `outstanding_shares`, where the payload happens to hold it.
      3. `market_cap / last_close_price` from `overview`. Arithmetic on two cited fields,
         not an invention — but the close is rounded, so it comes back with `exact=False`
         and the card says the number was derived.

    Returns `(None, (), False)` when no local payload carries any of the three.
    """
    sym = bare(symbol)
    try:
        report = load(source, "company_report", sym)
    except (NotRecorded, ValueError):
        report = {}
    if isinstance(report, dict):
        history = ((report.get("financials") or {}).get("historical_financials") or [])
        for row in history:
            if isinstance(row, dict) and row.get("outstanding_shares"):
                return (row["outstanding_shares"],
                        ("financials.historical_financials[].outstanding_shares",), True)
        overview = report.get("overview") or {}
        for key in ("shares_outstanding", "outstanding_shares", "shares_number"):
            if overview.get(key):
                return overview[key], (f"overview.{key}",), True
    try:
        for row in results_of(load(source, "companies")):
            if bare(row.get("symbol")) == sym:
                for key in ("outstanding_shares", "shares_outstanding", "shares_number"):
                    if row.get(key):
                        return row[key], (key,), True
    except (NotRecorded, ValueError):
        pass
    if isinstance(report, dict):
        overview = report.get("overview") or {}
        cap, close = overview.get("market_cap"), overview.get("last_close_price")
        if cap and close:
            return cap / close, ("overview.market_cap", "overview.last_close_price"), False
    return None, (), False


# ------------------------------------------------------------------------------- gates

def check_key_parity():
    """The point of the file: the same dataset from either source normalizes identically."""
    failures, checked = [], 0
    synth_symbol = available_symbols("synth")[0]
    cases = [
        ("daily", daily, "BBCA", synth_symbol, False),
        ("index", lambda s, _sym=None: index_daily(s), None, None, True),
        ("broker_flow", broker_flow, "BBCA", None, True),
        ("foreign_flow", foreign_flow, "BBCA", None, True),
    ]
    for name, reader, real_symbol, synth_sym, diverges in cases:
        try:
            real = reader("recorded", real_symbol) if real_symbol else reader("recorded")
            synth = reader("synth", synth_sym or _flow_symbol()) if name != "index" \
                else reader("synth")
        except NotRecorded as exc:
            failures.append(f"{name}: {exc}")
            continue
        if not real or not synth:
            failures.append(f"{name}: a source returned no rows ({len(real)} / {len(synth)})")
            continue
        checked += 1
        if set(real[0]) != set(synth[0]):
            failures.append(f"{name}: normalized keys differ — "
                            f"only-real={sorted(set(real[0]) - set(synth[0]))} "
                            f"only-synth={sorted(set(synth[0]) - set(real[0]))}")
        if diverges and set(_raw_first(name, "recorded", real_symbol)) == \
                set(_raw_first(name, "synth", synth_sym)):
            failures.append(f"{name}: raw keys now match — the divergence this exists for is gone")
    return failures, checked


def _flow_symbol():
    for row in results_of(load("synth", "broker_flow")):
        if row.get("symbol"):
            return bare(row["symbol"])
    return None


def _raw_first(name, source, symbol):
    dataset = {"index": "index_daily", "broker_flow": "broker_flow",
               "foreign_flow": "foreign_flow", "daily": "daily"}[name]
    rows = results_of(load(source, dataset, symbol or _flow_symbol()))
    if dataset == "broker_flow" and rows and isinstance(rows[0], dict) \
            and isinstance(rows[0].get("summary"), list):
        return rows[0]["summary"][0]
    return rows[0] if rows else {}


def check_lots_are_recorded_only():
    """Divergence 4, asserted rather than remembered: synth must not grow lot counts.

    If it ever does, float absorbed becomes computable there and this check is the reminder
    to go and enable it — and until then, the None it returns is deliberate.
    """
    failures = []
    real = broker_flow("recorded", "BBCA")
    synth = broker_flow("synth", _flow_symbol())
    if not any(r["net_lot"] is not None for r in real):
        failures.append("recorded broker flow lost its lot counts — float absorbed is now dead")
    if any(r["net_lot"] is not None for r in synth):
        failures.append("synth broker flow grew lot counts — float absorbed can be enabled there")
    return failures, 2


def check_registry_join():
    """The zero-credit join has to cover the brokers that actually appear in the flow."""
    failures = []
    registry = registry_index("recorded")
    if len(registry) < 50:
        failures.append(f"broker registry has only {len(registry)} codes")
    # The registry does not cover the tape completely: `JB` trades BBCA and has no row in
    # `/v2/brokers/`. That is a real gap, not a parsing bug, so it is measured rather than
    # asserted away — `pillars.py` puts unmapped codes in an `unknown` cohort and the card
    # prints their share. The gate fails only if the gap grows large enough to change a
    # verdict.
    rows = broker_flow("recorded", "BBCA")
    gross = sum(abs(r["buy_idr"] or 0) + abs(r["sell_idr"] or 0) for r in rows)
    unmapped = sorted({r["broker_code"] for r in rows if r["broker_code"] not in registry})
    stray = sum(abs(r["buy_idr"] or 0) + abs(r["sell_idr"] or 0)
                for r in rows if r["broker_code"] in set(unmapped))
    share = stray / gross if gross else 0.0
    if share > UNMAPPED_TOLERANCE:
        failures.append(f"{len(unmapped)} unmapped broker codes carry {share:.2%} of gross "
                        f"value, over the {UNMAPPED_TOLERANCE:.0%} tolerance: {unmapped[:8]}")
    print(f"        registry {len(registry)} codes · flow {len({r['broker_code'] for r in rows})} "
          f"codes · unmapped {unmapped} at {share:.4%} of gross")
    if not any(b["is_foreign"] for b in registry.values()):
        failures.append("no broker in the registry is foreign — the origin split is dead")
    cohorts = {b["cohort"] for b in registry.values()}
    if len(cohorts) < 2:
        failures.append(f"registry carries a single cohort {cohorts} — the cohort split is dead")
    return failures, 4


def check_filing_percentage_is_derived():
    """Divergence 6: the field synth lacks must be derived, not left None."""
    failures = []
    row = normalize_filing({"symbol": "X.JK", "date": "2026-01-02",
                            "share_percentage_before": 0.10, "share_percentage_after": 0.16})
    if row["share_percentage_transaction"] is None:
        failures.append("a synth-shaped filing did not derive its transaction percentage")
    elif abs(row["share_percentage_transaction"] - 0.06) > 1e-9:
        failures.append("the derived transaction percentage is wrong")
    kept = normalize_filing({"symbol": "X.JK", "timestamp": "2026-01-02T00:00:00",
                             "share_percentage_transaction": 0.5,
                             "share_percentage_before": 1.0, "share_percentage_after": 9.0})
    if kept["share_percentage_transaction"] != 0.5:
        failures.append("a recorded filing's own percentage was overwritten by the derivation")
    return failures, 2


def check_shares_provenance():
    """The denominator must say where it came from, and say when it was derived."""
    failures = []
    value, fields, exact = shares_outstanding("recorded", "BBCA")
    if not value or value <= 0:
        failures.append("no share count for BBCA on recorded")
    if not fields:
        failures.append("the share count came back without a citation")
    if exact and "outstanding_shares" not in " ".join(fields):
        failures.append(f"an exact share count cited {fields}, which is not a share field")
    print(f"        BBCA shares {value:,.0f} from {fields[0]} "
          f"({'exact' if exact else 'diturunkan'})")
    missing = shares_outstanding("recorded", "ZZZZ")
    if missing != (None, (), False):
        failures.append("an unknown symbol did not degrade to (None, (), False)")
    return failures, 4


def check_shape_helpers():
    failures = []
    if results_of({"results": [1, 2]}) != [1, 2] or results_of([1, 2]) != [1, 2]:
        failures.append("results_of did not unwrap both envelopes")
    if results_of(None) != [] or results_of({}) != []:
        failures.append("results_of did not degrade to an empty list")
    if bare("BBCA.JK") != "BBCA" or bare(None) != "":
        failures.append("bare did not strip the .JK suffix")
    if pagination_of(load("recorded", "filings")) is None:
        failures.append("recorded filings lost their pagination block")
    ihsg = index_daily("recorded")
    if not ihsg or ihsg[0]["index_code"] != "IHSG" or ihsg[0]["close"] is None:
        failures.append("the recorded IHSG series did not normalize its price onto close")
    if free_float("recorded", "BBCA") is None:
        failures.append("BBCA is absent from the recorded free-float table")
    return failures, 6


def main():
    total, bad = 0, []
    for check in (check_key_parity, check_lots_are_recorded_only, check_registry_join,
                  check_filing_percentage_is_derived, check_shares_provenance,
                  check_shape_helpers):
        failures, count = check()
        total += count
        bad += failures
        print(f"  {check.__name__:<34} {count - len(failures)}/{count}")
    for line in bad:
        print("FAIL", line)
    print(f"{total - len(bad)}/{total} checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
