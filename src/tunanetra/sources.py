#!/usr/bin/env python3
"""
One shared way to read the six payloads this product narrates.

Everything here exists because `recorded/` and `synth/` disagree, and every disagreement
is a `KeyError` waiting for the demo. `narrate.py` never sees a raw payload and
`reader.py` never reaches into a dict with `[]`.

    from sources import load, rows_of, normalize_daily, available_symbols

    rows = [normalize_daily(r) for r in rows_of(load("recorded", "daily", "ADRO"))]

The measured divergences, all re-checked against the 2026-09-06 capture on 2026-09-10:

  1. segments — `recorded/` is `{symbol, financial_year, revenue_breakdown[]}`, a
     Sankey edge list for ONE year. `synth/` is `{symbol: {year: {revenue_segments{},
     cost_segments{}}}}` with FOUR years. The synthetic file makes a multi-year segment
     trend look buildable; on real data it is not. See `refuse_multiyear_segments`.
  2. shareholders — `recorded/` is a dated monthly panel of absolute share counts with
     9 `_l` + 9 `_f` investor classes; `synth/` is fractions in
     `local_breakdown`/`foreign_breakdown` with 5 classes and a `month` string.
  3. quarterly — `recorded/` keys the period on `date` and carries 40 fields;
     `synth/` uses `report_date` + `quarter` and carries 11, with no capex field at all.
  4. quarterly again — the capex slot is SECTOR-DEPENDENT in `recorded/`: banks
     (BBCA, BBRI) carry `realized_capital_goods_investment`, everyone else
     (ADRO, TLKM) carries `capital_expenditure`, and never both. A parser written
     against the spec example silently drops capex for the whole non-bank market.
  5. foreign flow — `recorded/` wraps rows in `{symbol, start, end, data[]}` so the
     window is stated; `synth/` is a bare list with no window at all.
  6. segments graph shape — banks route revenue through
     `Interest Income -> Net Interest Income -> Total Revenue`, non-banks through
     `Total Revenue -> Gross Profit -> Operating Income`. Summing the flat edge list
     double-counts the intermediate nodes. `narrate.py` walks the graph; this file only
     hands it a consistent envelope.

Normalization fills a missing field with None rather than dropping the key, so the two
sources always present the same key set and a caller cannot depend on a field only one
of them has.

    python3 sources.py    # asserts the divergences above are still exactly these
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))          # src/tunanetra/
ROOT = os.path.dirname(os.path.dirname(HERE))              # the repository root

#: The data layers live in the research harness, not beside the product: they were paid
#: for in credits, they are evidence, and the ledger that records what they cost lives
#: next to them. This is the only file that knows the path.
HARNESS = os.path.join(ROOT, "research", "harness")
RECORDED = os.path.join(HARNESS, "recorded")
SYNTH = os.path.join(HARNESS, "synth")

#: Endpoint path per dataset. Every figure this product prints carries one of these,
#: plus the field it came from, plus the date the series actually covers.
ENDPOINT = {
    "overview": "/v2/company/report/{symbol}/?sections=overview",
    "segments": "/v2/company/get-segments/{symbol}/",
    "daily": "/v2/daily/{symbol}/",
    "shareholders": "/v2/company/shareholders-composition/{symbol}/",
    "quarterly": "/v2/financials/quarterly/{symbol}/?n_quarters=4",
    "foreign_flow": "/v2/foreign-flow/{symbol}/",
    "peers": "/v2/company/report/{symbol}/?sections=peers",
}

#: The six datasets a full reading needs. `peers` is deliberately not in this list:
#: it exists in the recordings for BBCA alone, so it is asked for separately and is
#: allowed to be absent.
CORE_DATASETS = ("overview", "segments", "daily", "shareholders", "quarterly",
                 "foreign_flow")

#: What can actually be read offline, today. This is the intersection of the five
#: symbol-scoped recordings, computed once here rather than discovered at render time
#: by a `NotRecorded` in the middle of a page.
OFFLINE_SYMBOLS = ("ADRO", "BBCA", "BBRI", "TLKM")

#: Which sub-sectors are banks. The quarterly capex field and the segment graph root
#: both depend on it, and both are wrong in the same silent way if it is guessed. Read
#: off `overview.sub_sector` at load time.
#:
#: Both spellings are listed on purpose: the company report returns the display form
#: `"Banks"`, while the screener's `sub_sector` filter takes the slug `"banks"`. Matching
#: only one of them makes every bank read as a non-bank on the other source, which is
#: precisely divergence 4 arriving through a different door.
BANK_SUBSECTORS = ("banks",)


class NotRecorded(Exception):
    """Asked for a payload this source does not hold.

    Raised rather than returning an empty list, because "no data" and "no file" produce
    different sentences: the first is a finding, the second is *belum diambil*. Only the
    caller knows which it is looking at, so this never degrades on its own.
    """


class SyntheticOnly(Exception):
    """A claim that only the synthetic layer can support.

    The hackathon rules forbid shipping synthetic data as the product's data source.
    A multi-year segment trend is buildable in `synth/` and nowhere else, so asking for
    one is a bug in the caller, not a gap in the data.
    """


def _read(path):
    if not os.path.exists(path):
        raise NotRecorded(path)
    with open(path) as handle:
        return json.load(handle)


def load(source, dataset, symbol=None):
    """Read one dataset from `recorded/` or `synth/`. Raises NotRecorded when absent."""
    if source == "recorded":
        slugs = {
            "overview": f"v2_company_report_{symbol}__sections-overview",
            "segments": f"v2_company_get-segments_{symbol}",
            "daily": f"v2_daily_{symbol}",
            "shareholders": f"v2_company_shareholders-composition_{symbol}",
            "quarterly": f"v2_financials_quarterly_{symbol}__n_quarters-4",
            "foreign_flow": f"v2_foreign-flow_{symbol}",
            # The only peers payload that was ever paid for is inside the one bare
            # company report, which cost 8 credits because no `sections` was named.
            # It exists for BBCA and for nothing else.
            "peers": f"v2_company_report_{symbol}",
        }
        if dataset not in slugs:
            raise NotRecorded(f"recorded has no {dataset}")
        return _read(os.path.join(RECORDED, slugs[dataset] + ".json"))

    if source == "synth":
        paths = {
            "overview": os.path.join(SYNTH, "market", "companies.json"),
            "segments": os.path.join(SYNTH, "company", "segments.json"),
            "daily": os.path.join(SYNTH, "market", "daily", f"{symbol}.json"),
            "shareholders": os.path.join(SYNTH, "flow",
                                         "shareholders_composition.json"),
            "quarterly": os.path.join(SYNTH, "company", "quarterly", f"{symbol}.json"),
            "foreign_flow": os.path.join(SYNTH, "flow", "foreign_flow.json"),
        }
        if dataset not in paths:
            raise NotRecorded(f"synth has no {dataset}")
        return _read(paths[dataset])

    raise ValueError(f"unknown source {source!r}")


def rows_of(payload):
    """The rows of a payload, whether it wraps them or is already a list."""
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "results"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def bare_symbol(symbol):
    """`BBCA.JK` and `BBCA` are the same stock. Payloads use the suffix, the CLI does not."""
    if not symbol:
        return ""
    return symbol.split(".")[0].upper()


def available_symbols(source="recorded"):
    """Which symbols have every core dataset. Never guesses — it opens the files."""
    if source != "recorded":
        return sorted({bare_symbol(r["symbol"])
                       for r in rows_of(load("synth", "overview"))})[:8]
    found = []
    for symbol in OFFLINE_SYMBOLS:
        try:
            for dataset in CORE_DATASETS:
                load("recorded", dataset, symbol)
        except NotRecorded:
            continue
        found.append(symbol)
    return found


# --------------------------------------------------------------------------- windows
#
# Every recorded series is a fixed, stale window — these are 2026-09-06 captures, not a
# feed. A sentence that says "the last 90 days" about a 20-row recording is false, and
# it is false in the direction that flatters the demo. Each normalizer returns the
# window it actually read, and `narrate.py` prints it.


def window_of(rows, key="date"):
    """(first, last) date actually present, or (None, None) on an empty series."""
    dates = sorted(r[key] for r in rows if r.get(key))
    return (dates[0], dates[-1]) if dates else (None, None)


def normalize_daily(row):
    """One price bar, identical keys from either source."""
    return {
        "symbol": bare_symbol(row.get("symbol")),
        "date": row.get("date"),
        "open": row.get("open"),
        "high": row.get("high"),
        "low": row.get("low"),
        "close": row.get("close"),
        "volume": row.get("volume"),
        "market_cap": row.get("market_cap"),
    }


def normalize_flow(row):
    """One net foreign inflow row."""
    return {
        "symbol": bare_symbol(row.get("symbol")),
        "date": row.get("date"),
        "net_foreign_inflow": row.get("net_foreign_inflow"),
    }


def flow_window(payload):
    """The stated window of a foreign-flow payload, or the observed one on synth.

    Divergence 5: `recorded/` states `start`/`end` in the envelope, `synth/` is a bare
    list. Returning the observed range for synth keeps callers from having to know.
    """
    if isinstance(payload, dict) and payload.get("start"):
        return payload["start"], payload["end"]
    return window_of(rows_of(payload))


#: The nine investor classes the recorded panel carries, in the order a sentence should
#: read them. `_l` is local (domestic), `_f` is foreign — the suffix is the whole
#: distinction the ownership chart normally draws as two stacked bands.
INVESTOR_CLASSES = ("individual", "corporate", "mutual_fund", "pension_fund",
                    "insurance", "financial_institutions", "securities_companies",
                    "foundation", "other")


def normalize_shareholders(payload):
    """The ownership panel as `{date: {class: {"local": x, "foreign": y}}}`, newest last.

    Divergence 2. `recorded/` gives absolute share counts per class per month; `synth/`
    gives fractions under different names for five classes. Both come out here as
    fractions of the month's total, because the sentence that matters is "the share
    rose", and a share is comparable across sources while a share count is not.
    """
    out = {}
    rows = rows_of(payload)
    for row in rows:
        if "month" in row:                                  # synth
            date = row["month"]
            local = row.get("local_breakdown") or {}
            foreign = row.get("foreign_breakdown") or {}
            month = {
                cls: {"local": local.get(cls), "foreign": foreign.get(cls)}
                for cls in INVESTOR_CLASSES
            }
        else:                                               # recorded
            date = row.get("date")
            total = (row.get("total_l") or 0) + (row.get("total_f") or 0)
            month = {}
            for cls in INVESTOR_CLASSES:
                local_shares = row.get(f"{cls}_l")
                foreign_shares = row.get(f"{cls}_f")
                month[cls] = {
                    "local": (local_shares / total) if total and local_shares is not None else None,
                    "foreign": (foreign_shares / total) if total and foreign_shares is not None else None,
                }
        out[date] = month
    return dict(sorted(out.items()))


#: The capex field is not one field. Divergence 4, verified against the recordings:
#: BBCA and BBRI carry the first, ADRO and TLKM carry the second, and no payload
#: carries both.
CAPEX_FIELDS = ("realized_capital_goods_investment", "capital_expenditure")


def capex_field(row):
    """Which capex key this row actually has, or None. Never assumes a sector."""
    for field in CAPEX_FIELDS:
        if row.get(field) is not None:
            return field
    return None


def normalize_quarter(row):
    """One quarter, with the capex slot resolved to a single key plus its real name.

    `capex_source_field` is kept so the citation can name the field the API used, not
    the one this product invented. A blind reader who asks where a number came from
    gets `realized_capital_goods_investment`, which is what a bank's payload says.
    """
    field = capex_field(row)
    return {
        "symbol": bare_symbol(row.get("symbol")),
        "date": row.get("date") or row.get("report_date"),
        "revenue": row.get("revenue"),
        "earnings": row.get("earnings"),
        "gross_profit": row.get("gross_profit"),
        "operating_pnl": row.get("operating_pnl"),
        "total_assets": row.get("total_assets"),
        "total_equity": row.get("total_equity"),
        "total_liabilities": row.get("total_liabilities"),
        "capex": row.get(field) if field else None,
        "capex_source_field": field,
    }


def normalize_overview(payload, source="recorded", symbol=None):
    """Company identity and the one-line market snapshot, from either source."""
    if source == "synth":
        wanted = bare_symbol(symbol)
        for row in rows_of(payload):
            if bare_symbol(row.get("symbol")) == wanted:
                return {
                    "symbol": wanted,
                    "company_name": row.get("company_name"),
                    "sub_sector": row.get("sub_sector"),
                    "market_cap": row.get("market_cap"),
                    "listing_date": row.get("listing_date"),
                    "last_close_price": None,
                    "latest_close_date": None,
                }
        raise NotRecorded(f"synth overview has no {wanted}")

    overview = (payload or {}).get("overview") or {}
    return {
        "symbol": bare_symbol(payload.get("symbol")),
        "company_name": payload.get("company_name"),
        "sub_sector": overview.get("sub_sector"),
        "market_cap": overview.get("market_cap"),
        "listing_date": overview.get("listing_date"),
        "last_close_price": overview.get("last_close_price"),
        "latest_close_date": overview.get("latest_close_date"),
    }


def is_bank(overview):
    """Sector decides the capex field and the segment graph root. Read, never guessed."""
    sub_sector = ((overview or {}).get("sub_sector") or "").strip().lower()
    return sub_sector in BANK_SUBSECTORS


def normalize_segments(payload, source="recorded", symbol=None):
    """The revenue Sankey as `{financial_year, edges[{source, target, value}]}`.

    Divergence 1 and 6. `recorded/` is already an edge list. `synth/` is a per-year map
    of flat category totals, so it is converted into the same edge shape against a
    `Total Revenue` root — which is the *non-bank* shape, and one more reason the
    synthetic layer must never reach the product's default source.
    """
    if source == "synth":
        wanted = bare_symbol(symbol)
        book = {bare_symbol(k): v for k, v in (payload or {}).items()}
        if wanted not in book:
            raise NotRecorded(f"synth segments has no {wanted}")
        years = book[wanted]
        year = max(years)                       # one year only — see refuse_multiyear
        edges = [{"source": name, "target": "Total Revenue", "value": value}
                 for name, value in (years[year].get("revenue_segments") or {}).items()]
        return {"financial_year": int(year), "edges": edges}

    return {
        "financial_year": (payload or {}).get("financial_year"),
        "edges": list((payload or {}).get("revenue_breakdown") or []),
    }


def refuse_multiyear_segments(source):
    """The one claim the synthetic layer can support and the real API cannot.

    `research/plan/tunanetra/ringkas.md` §8 offers *"tiga perempat pendapatan berasal
    dari satu segmen, dan porsinya naik tiga tahun berturut-turut"* as a model sentence.
    `/v2/company/get-segments/` returns exactly ONE `financial_year`. The four-year
    series exists only in `synth/company/segments.json`. Building the sentence would
    mean shipping synthetic data as the product's data source, which the rules forbid
    outright — so it is refused here, on every source, rather than left to discipline.
    """
    raise SyntheticOnly(
        "a multi-year segment trend needs a series /v2/company/get-segments/ does not "
        "return; only synth/ has one, and synthetic data may not be the product's "
        "data source")


# ------------------------------------------------------------------------------ gates


def _synth_symbol(dataset):
    pattern = {"daily": os.path.join(SYNTH, "market", "daily", "*.json"),
               "quarterly": os.path.join(SYNTH, "company", "quarterly", "*.json")}[dataset]
    paths = sorted(glob.glob(pattern))
    return os.path.splitext(os.path.basename(paths[0]))[0] if paths else None


def check_key_parity():
    """The point of the file: the same dataset from either source normalizes identically."""
    failures = []
    checked = 0

    real_daily = [normalize_daily(r) for r in rows_of(load("recorded", "daily", "ADRO"))]
    synth_daily = [normalize_daily(r)
                   for r in rows_of(load("synth", "daily", _synth_symbol("daily")))]
    checked += 1
    if set(real_daily[0]) != set(synth_daily[0]):
        failures.append("daily: normalized keys differ")

    real_q = [normalize_quarter(r)
              for r in rows_of(load("recorded", "quarterly", "BBCA"))]
    synth_q = [normalize_quarter(r)
               for r in rows_of(load("synth", "quarterly", _synth_symbol("quarterly")))]
    checked += 1
    if set(real_q[0]) != set(synth_q[0]):
        failures.append("quarterly: normalized keys differ")
    if synth_q[0]["capex_source_field"] is not None:
        failures.append("quarterly: synth grew a capex field — divergence 3 has changed")

    checked += 1
    real_panel = normalize_shareholders(load("recorded", "shareholders", "BBCA"))
    synth_panel = normalize_shareholders(load("synth", "shareholders"))
    real_month = real_panel[max(real_panel)]
    synth_month = synth_panel[max(synth_panel)]
    if set(real_month) != set(synth_month) != set(INVESTOR_CLASSES):
        failures.append("shareholders: normalized class sets differ")

    checked += 1
    real_seg = normalize_segments(load("recorded", "segments", "TLKM"))
    if not real_seg["edges"] or set(real_seg["edges"][0]) != {"source", "target", "value"}:
        failures.append("segments: recorded edges are no longer source/target/value")

    return failures, checked


def check_capex_divergence():
    """Divergence 4 is the one that silently corrupts a whole sector. Assert it exists."""
    failures = []
    seen = {}
    for symbol in OFFLINE_SYMBOLS:
        rows = [normalize_quarter(r)
                for r in rows_of(load("recorded", "quarterly", symbol))]
        fields = {r["capex_source_field"] for r in rows if r["capex_source_field"]}
        if len(fields) > 1:
            failures.append(f"{symbol}: carries both capex fields at once — {fields}")
        seen[symbol] = fields.pop() if fields else None

    banks = {s for s in OFFLINE_SYMBOLS
             if is_bank(normalize_overview(load("recorded", "overview", s)))}
    if banks != {"BBCA", "BBRI"}:
        failures.append(f"the bank set moved: expected BBCA/BBRI, read {sorted(banks)}")
    for symbol, field in seen.items():
        expected = ("realized_capital_goods_investment" if symbol in banks
                    else "capital_expenditure")
        if field != expected:
            failures.append(f"{symbol}: capex field is {field}, expected {expected}")
    print(f"        capex field by symbol · " +
          " · ".join(f"{s}={f}" for s, f in sorted(seen.items())))
    return failures, len(OFFLINE_SYMBOLS) + 1


def check_windows():
    """Every recorded series is a fixed stale window. Print it, so no sentence invents one."""
    failures = []
    daily = [normalize_daily(r) for r in rows_of(load("recorded", "daily", "BBCA"))]
    first, last = window_of(daily)
    if len(daily) != 20:
        failures.append(f"daily is {len(daily)} rows, not the 20 that were captured — "
                        f"a '90 hari' sentence would now be even further from the data")
    flow_payload = load("recorded", "foreign_flow", "BBCA")
    flow_first, flow_last = flow_window(flow_payload)
    panel = normalize_shareholders(load("recorded", "shareholders", "BBCA"))
    if len(panel) != 8:
        failures.append(f"the ownership panel is {len(panel)} months, not 8")
    print(f"        daily {len(daily)} rows {first}..{last} · "
          f"foreign flow {len(rows_of(flow_payload))} rows {flow_first}..{flow_last} · "
          f"ownership {len(panel)} months {min(panel)}..{max(panel)}")
    return failures, 3


def check_multiyear_refusal():
    """A multi-year segment claim must be impossible to build, not merely discouraged."""
    failures = []
    for source in ("recorded", "synth"):
        try:
            refuse_multiyear_segments(source)
        except SyntheticOnly:
            continue
        failures.append(f"{source}: a multi-year segment trend was not refused")

    real = normalize_segments(load("recorded", "segments", "BBCA"))
    if not isinstance(real["financial_year"], int):
        failures.append("recorded segments lost their single financial_year")
    synth_book = load("synth", "segments")
    any_symbol = next(iter(synth_book))
    if len(synth_book[any_symbol]) < 2:
        failures.append("synth segments no longer carry the multi-year series that "
                        "makes the forbidden sentence look buildable")
    return failures, 4


def check_offline_symbols():
    """What the product can actually read today, opened rather than asserted."""
    failures = []
    found = available_symbols("recorded")
    if found != list(OFFLINE_SYMBOLS):
        failures.append(f"the offline intersection moved: {found}")
    try:
        load("recorded", "peers", "TLKM")
    except NotRecorded:
        pass
    else:
        failures.append("a peers payload appeared for TLKM — the peer section can now "
                        "be built for more than BBCA, so update reader.py's degradation")
    load("recorded", "peers", "BBCA")       # must still exist; raises if it does not
    print(f"        readable offline · {', '.join(found)} · "
          f"peers: BBCA only (the other three cost 2 credits each)")
    return failures, len(OFFLINE_SYMBOLS) + 2


def main():
    results = [("key parity", *check_key_parity()),
               ("capex divergence", *check_capex_divergence()),
               ("series windows", *check_windows()),
               ("multi-year refusal", *check_multiyear_refusal()),
               ("offline symbols", *check_offline_symbols())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:20} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)

    print("\nreal and synth normalize identically" if not failed
          else f"\n{failed} normalization divergence(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
