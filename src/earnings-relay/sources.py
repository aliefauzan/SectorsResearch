#!/usr/bin/env python3
"""
One shared way to read the two payloads this product turns into evidence.

Everything here exists because `recorded/` and `synth/` disagree, and every disagreement
is a `KeyError` waiting for the demo. `relay.py` never sees a raw payload and no other
module reaches into a dict with `[]`.

    from sources import load, rows_of, trigger_rows, normalize_quarterly

    rows = [normalize_quarterly(r, "recorded")
            for r in rows_of(load("recorded", "quarterly", "ADRO"))]

The measured divergences, all re-checked against the 2026-09-06 capture on 2026-09-10:

  1. trigger shape — `recorded/` is `{"results":[{symbol,date,quarter}],"pagination":{…}}`:
     a single MERGED full sweep, one latest row per symbol, 960 symbols, `quarter`
     lowercase (`"q1"`). `synth/` is `{symbol: {year: [{quarter,date}]}}` — nested,
     multi-year, `quarter` uppercase (`"Q1"`). Both come out of `trigger_rows()` as
     `{"symbol","report_date","quarter","period_key","source"}`.
  2. period key — `recorded/` keys the quarterly period on `date` and carries no quarter
     label at all; `synth/` uses `report_date` plus a `quarter` of `"Q1-2025"`. Neither
     label is trusted: `periods.period_key()` derives the key from the date on both
     sides, so a mislabelled payload cannot mislabel a comparison.
  3. field count — `recorded/` quarterly carries 40 fields, `synth/` carries 11
     (`revenue, earnings, gross_profit, operating_pnl, total_assets, total_equity,
     total_liabilities, operating_cash_flow` plus keys). Normalization fills what is
     absent with `None` rather than dropping the key, so a caller cannot come to depend
     on a field only one layer has.
  4. the capex slot is SECTOR-DEPENDENT in `recorded/` — banks (BBCA, BBRI) carry
     `realized_capital_goods_investment`, everyone else (ADRO, TLKM) carries
     `capital_expenditure`, and no payload carries both. Earnings Relay does not use
     capex in any of its three metrics, but `factset.validate()` must not read the
     absent one as a null failure, which is why the resolved field name travels with
     the row. Same finding as `src/tunanetra/sources.py:24`.
  5. symbol suffix — every payload says `ADRO.JK`; the watchlist, the CLI and the
     `event_hash` say `ADRO`. One `bare_symbol()` on the way in, and the synth quarterly
     FILE is named `AHRL.json` while the synth trigger KEY is `AHRL.JK` — the same
     divergence arriving through a second door.
  6. series depth — `recorded/` holds 4 trailing quarters, `synth/` holds 8 spanning
     `Q4-2024 … Q3-2026`. **On `recorded/` the prior-year quarter does not exist for any
     symbol**, so the PRD's default year-over-year comparator is unavailable there and
     `comparable_symbols()` is computed by opening the files, never assumed.

Normalization fills a missing field with None rather than dropping the key. `load()`
raises `NotRecorded` rather than returning an empty list, because "no data" and "no file"
produce different sentences and only the caller knows which one it is looking at.

    python3 sources.py    # asserts the six divergences above are still exactly these
"""
import json
import os

import periods

HERE = os.path.dirname(os.path.abspath(__file__))          # src/earnings-relay/
ROOT = os.path.dirname(os.path.dirname(HERE))              # the repository root

#: The data layers live in the research harness, not beside the product: they were paid
#: for in credits, they are evidence, and the ledger that records what they cost lives
#: next to them. This is the only file that knows the path.
HARNESS = os.path.join(ROOT, "research", "harness")
RECORDED = os.path.join(HARNESS, "recorded")
SYNTH = os.path.join(HARNESS, "synth")

#: Endpoint path per dataset. Every fact this product locks carries one of these, plus
#: the field it came from, plus the `as_of` of the capture it was read out of.
#:
#: `quarterly_yoy` is never called. It is the string an `unknown` metric quotes when it
#: says which call would make the year-over-year comparator computable — 8 quarters at
#: `cost_for`'s per-quarter rate, against the 623 credits that remain.
ENDPOINT = {
    "trigger": "/v2/companies/quarterly-financial-dates/",
    "quarterly": "/v2/financials/quarterly/{symbol}/?n_quarters=4",
    "quarterly_yoy": "/v2/financials/quarterly/{symbol}/?n_quarters=8",
}

#: When the recordings were taken. Every fact carries it, because a 2026-09-06 capture
#: read on 2026-09-10 is four days stale and the evidence drawer has to say so.
CAPTURE_AS_OF = "2026-09-06"

#: What can actually be read offline, today: the intersection of the recorded quarterly
#: payloads. Computed by `available_symbols()` opening the files; listed here so a
#: caller gets a usable error message instead of a `NotRecorded` mid-render.
OFFLINE_SYMBOLS = ("ADRO", "BBCA", "BBRI", "TLKM")

#: The fixed key set every quarterly row presents, whichever layer it came from.
QUARTERLY_FIELDS = ("revenue", "earnings", "gross_profit", "operating_pnl",
                    "total_assets", "total_equity", "total_liabilities",
                    "operating_cash_flow")

#: Divergence 4: the capex field is not one field. BBCA and BBRI carry the first,
#: ADRO and TLKM carry the second, and no payload carries both.
CAPEX_FIELDS = ("realized_capital_goods_investment", "capital_expenditure")


class NotRecorded(Exception):
    """Asked for a payload this source does not hold.

    Raised rather than returning an empty list, because "no data" and "no file" produce
    different outcomes: the first is a validation finding, the second is *belum diambil*
    plus the endpoint that would have had it. Only the caller knows which it is looking
    at, so this never degrades on its own.
    """


class SyntheticOnly(Exception):
    """A claim that only the synthetic layer can support.

    The hackathon rules forbid shipping synthetic data as the product's data source. A
    year-over-year comparison is computable in `synth/` and nowhere else on disk, so
    asking for one against `recorded/` is a bug in the caller, not a gap in the data.
    """


def _read(path):
    if not os.path.exists(path):
        raise NotRecorded(path)
    with open(path) as handle:
        return json.load(handle)


def load(source, dataset, symbol=None):
    """Read one dataset from `recorded/` or `synth/`. Raises NotRecorded when absent."""
    symbol = bare_symbol(symbol) if symbol else None
    if source == "recorded":
        slugs = {
            "trigger": "v2_companies_quarterly-financial-dates__limit-30",
            "quarterly": f"v2_financials_quarterly_{symbol}__n_quarters-4",
        }
        if dataset not in slugs:
            raise NotRecorded(f"recorded has no {dataset}")
        return _read(os.path.join(RECORDED, slugs[dataset] + ".json"))

    if source == "synth":
        paths = {
            "trigger": os.path.join(SYNTH, "company", "quarterly_financial_dates.json"),
            # Divergence 5, second door: the synth file is `AHRL.json`, the synth
            # trigger key is `AHRL.JK`.
            "quarterly": os.path.join(SYNTH, "company", "quarterly", f"{symbol}.json"),
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
    return str(symbol).split(".")[0].upper()


# ------------------------------------------------------------------------- the trigger


def trigger_rows(payload, source):
    """Every report date in a trigger payload, from either shape (divergence 1).

    Rows whose date is not an IDX quarter end are dropped with their reason rather than
    guessed at — see `periods.UnknownPeriod`. The dropped ones come back from
    `trigger_anomalies()` so a poll can report them instead of silently seeing fewer
    events than the sweep contained.
    """
    rows, _ = _trigger_split(payload, source)
    return rows


def trigger_anomalies(payload, source):
    """The trigger rows this product refused to key, and why."""
    _, dropped = _trigger_split(payload, source)
    return dropped


def _trigger_split(payload, source):
    kept, dropped = [], []

    def keep(symbol, date, quarter):
        try:
            key = periods.period_key(date)
        except periods.UnknownPeriod as exc:
            dropped.append({"symbol": bare_symbol(symbol), "report_date": date,
                            "reason": str(exc)})
            return
        kept.append({"symbol": bare_symbol(symbol), "report_date": date,
                     # The label the payload supplied, kept for the evidence drawer and
                     # never used to derive anything.
                     "quarter": (quarter or "").lower(),
                     "period_key": key, "source": source})

    if source == "synth":
        # {symbol: {year: [{quarter, date}]}} — nested, multi-year.
        for symbol, by_year in (payload or {}).items():
            for _year, entries in (by_year or {}).items():
                for entry in entries or ():
                    keep(symbol, entry.get("date"), entry.get("quarter"))
    else:
        # {"results": [{symbol, date, quarter}], "pagination": {…merged sweep…}}
        for row in rows_of(payload):
            keep(row.get("symbol"), row.get("date"), row.get("quarter"))

    kept.sort(key=lambda r: (r["symbol"], r["report_date"]))
    return kept, dropped


def trigger_window(payload, source):
    """`(rows, note)` — what the sweep actually is, for the run log.

    The recorded sweep is `merged`: 32 pages already paid for and stitched into one file.
    It is not paginated at read time and it holds exactly one latest row per symbol, so
    nothing in this product walks pages.
    """
    rows = trigger_rows(payload, source)
    if source == "recorded":
        pagination = (payload or {}).get("pagination") or {}
        note = (f"sweep gabungan {pagination.get('pages_fetched')} halaman · "
                f"{pagination.get('showing')} dari {pagination.get('total_count')} emiten · "
                f"satu baris terbaru per emiten")
    else:
        note = f"DATA SINTETIS · {len(payload or {})} emiten × beberapa tahun"
    return rows, note


# ----------------------------------------------------------------------- the quarterly


def capex_field(row):
    """Which capex key this row actually has, or None. Never assumes a sector."""
    for field in CAPEX_FIELDS:
        if row.get(field) is not None:
            return field
    return None


def normalize_quarterly(row, source="recorded"):
    """One quarter, identical keys from either layer (divergences 2, 3, 4, 5).

    `capex_source_field` is kept so an evidence drawer can name the field the API used,
    not the one this product invented. `period_key` is derived from the date; the label
    the payload supplied is carried alongside as `quarter_label_seen` and is never used.
    """
    report_date = row.get("date") or row.get("report_date")
    field = capex_field(row)
    out = {
        "symbol": bare_symbol(row.get("symbol")),
        "report_date": report_date,
        "period_key": None,
        "quarter_label_seen": row.get("quarter"),
        "capex": row.get(field) if field else None,
        "capex_source_field": field,
        "source": source,
    }
    for name in QUARTERLY_FIELDS:
        out[name] = row.get(name)
    try:
        out["period_key"] = periods.period_key(report_date)
    except periods.UnknownPeriod:
        out["period_key"] = None                # a finding for the validator, not a crash
    return out


def quarterly_rows(source, symbol):
    """Every normalized quarter for one symbol, newest last. Raises NotRecorded."""
    rows = [normalize_quarterly(r, source)
            for r in rows_of(load(source, "quarterly", symbol))]
    return sorted((r for r in rows if r["report_date"]), key=lambda r: r["report_date"])


def period_index(rows):
    """`{period_key: row}` for a symbol's quarters. Rows with no key are left out."""
    return {r["period_key"]: r for r in rows if r["period_key"]}


# -------------------------------------------------------------------------- capability


def available_symbols(source="recorded"):
    """Which symbols have a quarterly payload. Never guesses — it opens the files."""
    if source == "synth":
        directory = os.path.join(SYNTH, "company", "quarterly")
        if not os.path.isdir(directory):
            raise NotRecorded(directory)
        return sorted(name[:-5] for name in os.listdir(directory)
                      if name.endswith(".json"))
    found = []
    for symbol in OFFLINE_SYMBOLS:
        try:
            load("recorded", "quarterly", symbol)
        except NotRecorded:
            continue
        found.append(symbol)
    return found


def comparable_symbols(source="recorded", comparator="yoy"):
    """Symbols whose LATEST quarter has the comparator period present, opened not assumed.

    This is divergence 6 made operational: on `recorded/` with `comparator="yoy"` the
    answer is an empty list, and that is the honest answer — the product then renders
    `unknown` and names `/v2/financials/quarterly/{symbol}/?n_quarters=8`.
    """
    ok = []
    for symbol in available_symbols(source):
        try:
            rows = quarterly_rows(source, symbol)
        except NotRecorded:
            continue
        keys = [r["period_key"] for r in rows if r["period_key"]]
        if not keys:
            continue
        _, status, _ = periods.select_comparator(keys[-1], keys, comparator)
        if status == "ok":
            ok.append(symbol)
    return ok


def describe(source="recorded"):
    """One paragraph on what this layer can actually support. Printed by `symbols`."""
    readable = available_symbols(source)
    lines = []
    for symbol in readable[:12]:
        rows = quarterly_rows(source, symbol)
        keys = [r["period_key"] for r in rows if r["period_key"]]
        yoy = periods.select_comparator(keys[-1], keys, "yoy")[1] if keys else "unavailable"
        seq = periods.select_comparator(keys[-1], keys, "sequential")[1] if keys else "unavailable"
        lines.append(f"  {symbol:6} {len(keys)} kuartal  {keys[0]}..{keys[-1]}  "
                     f"yoy={yoy}  sequential={seq}")
    if len(readable) > 12:
        lines.append(f"  … dan {len(readable) - 12} emiten lain")
    return "\n".join(lines)


# ------------------------------------------------------------------------------ gates


def _synth_symbol():
    return available_symbols("synth")[0]


def check_trigger_shape():
    """Divergence 1: two shapes in, one shape out — and the sweep is merged, not paged."""
    failures = []
    recorded = load("recorded", "trigger")
    pagination = recorded.get("pagination") or {}
    if not pagination.get("merged"):
        failures.append("the recorded sweep is no longer merged — pagination-walking "
                        "code would now be needed, and none exists in this product")
    if pagination.get("showing") != 960 or pagination.get("total_count") != 962:
        failures.append(f"the sweep moved: showing={pagination.get('showing')} of "
                        f"{pagination.get('total_count')}, expected 960 of 962")

    rows = trigger_rows(recorded, "recorded")
    symbols = [r["symbol"] for r in rows]
    if len(symbols) != len(set(symbols)):
        failures.append("the recorded sweep now holds more than one row per symbol")
    if rows and rows[0]["quarter"] != rows[0]["quarter"].lower():
        failures.append("the recorded quarter label is no longer lowercase")

    synth_rows = trigger_rows(load("synth", "trigger"), "synth")
    if not synth_rows:
        failures.append("the synth trigger flattened to nothing")
    if set(rows[0]) != set(synth_rows[0]):
        failures.append("the two trigger shapes no longer normalize to the same keys")
    per_symbol = {}
    for row in synth_rows:
        per_symbol.setdefault(row["symbol"], []).append(row)
    if max(len(v) for v in per_symbol.values()) < 2:
        failures.append("the synth trigger lost its multi-year depth")

    print(f"        trigger · recorded {len(rows)} baris (satu per emiten, sweep "
          f"gabungan) · synth {len(synth_rows)} baris / {len(per_symbol)} emiten")
    return failures, 6


def check_key_parity():
    """Divergence 3: the same quarter from either source normalizes to the same keys."""
    failures = []
    real = quarterly_rows("recorded", "ADRO")
    synth = quarterly_rows("synth", _synth_symbol())
    if set(real[0]) != set(synth[0]):
        failures.append("quarterly: normalized keys differ between the two layers")
    if len(set(QUARTERLY_FIELDS) - set(real[0])) or len(set(QUARTERLY_FIELDS) - set(synth[0])):
        failures.append("a canonical quarterly field went missing from a layer")

    raw_real = rows_of(load("recorded", "quarterly", "ADRO"))[0]
    raw_synth = rows_of(load("synth", "quarterly", _synth_symbol()))[0]
    if len(raw_real) < 30:
        failures.append(f"recorded quarterly is now {len(raw_real)} fields, not ~40")
    if len(raw_synth) > 15:
        failures.append(f"synth quarterly grew to {len(raw_synth)} fields — the "
                        f"field-count divergence this file exists for has changed")
    print(f"        quarterly · recorded {len(raw_real)} field mentah, synth "
          f"{len(raw_synth)} · dinormalkan ke {len(real[0])} kunci yang sama")
    return failures, 4


def check_period_derivation():
    """Divergence 2: neither label is trusted; the key comes off the date."""
    failures = []
    real = quarterly_rows("recorded", "BBCA")
    if any(r["quarter_label_seen"] for r in real):
        failures.append("recorded quarterly grew a quarter label — it never had one, "
                        "and nothing may start trusting it")
    synth = quarterly_rows("synth", _synth_symbol())
    labels = {r["quarter_label_seen"] for r in synth}
    if not labels or not all(str(l)[0] == "Q" for l in labels):
        failures.append(f"the synth quarter label changed shape: {sorted(labels)[:3]}")
    for row in synth:
        # `"Q1-2025"` must agree with the date-derived `"q1-2025"`, but the derived one
        # is what everything downstream uses.
        if str(row["quarter_label_seen"]).lower() != row["period_key"]:
            failures.append(f"synth {row['report_date']}: label "
                            f"{row['quarter_label_seen']} vs derived {row['period_key']}")
    return failures, 2 + len(synth)


def check_capex_divergence():
    """Divergence 4 silently corrupts a whole sector elsewhere. Assert it still exists."""
    failures = []
    seen = {}
    for symbol in OFFLINE_SYMBOLS:
        fields = {r["capex_source_field"] for r in quarterly_rows("recorded", symbol)
                  if r["capex_source_field"]}
        if len(fields) > 1:
            failures.append(f"{symbol}: carries both capex fields at once — {fields}")
        seen[symbol] = fields.pop() if fields else None
    expected = {"BBCA": "realized_capital_goods_investment",
                "BBRI": "realized_capital_goods_investment",
                "ADRO": "capital_expenditure",
                "TLKM": "capital_expenditure"}
    for symbol, field in seen.items():
        if field != expected[symbol]:
            failures.append(f"{symbol}: capex field is {field}, expected {expected[symbol]}")
    if any(r["capex_source_field"] for r in quarterly_rows("synth", _synth_symbol())):
        failures.append("synth grew a capex field — divergence 4 has changed")
    print("        capex · " + " · ".join(f"{s}={f}" for s, f in sorted(seen.items())))
    return failures, len(OFFLINE_SYMBOLS) + 1


def check_symbol_suffix():
    """Divergence 5: `.JK` in every payload, bare everywhere else, both doors."""
    failures = []
    raw = rows_of(load("recorded", "quarterly", "ADRO"))[0]
    if not str(raw.get("symbol", "")).endswith(".JK"):
        failures.append("the recorded payload lost its .JK suffix")
    if bare_symbol(raw["symbol"]) != "ADRO":
        failures.append("bare_symbol no longer strips the suffix")
    synth_trigger_keys = list(load("synth", "trigger"))
    if not str(synth_trigger_keys[0]).endswith(".JK"):
        failures.append("the synth trigger key lost its .JK suffix")
    if any(name.endswith(".JK.json")
           for name in os.listdir(os.path.join(SYNTH, "company", "quarterly"))):
        failures.append("the synth quarterly files grew a .JK suffix — the second door "
                        "of divergence 5 has closed and the load() path must change")
    # The `.JK` key must still find the bare file.
    quarterly_rows("synth", synth_trigger_keys[0])
    return failures, 5


def check_series_depth():
    """Divergence 6, the one that decides which comparator this product can honour."""
    failures = []
    depths = {}
    for symbol in OFFLINE_SYMBOLS:
        rows = quarterly_rows("recorded", symbol)
        depths[symbol] = len(rows)
        if len(rows) != 4:
            failures.append(f"{symbol}: {len(rows)} recorded quarters, not 4")
    synth_depth = len(quarterly_rows("synth", _synth_symbol()))
    if synth_depth != 8:
        failures.append(f"synth is {synth_depth} quarters, not 8")

    yoy = comparable_symbols("recorded", "yoy")
    if yoy:
        failures.append(f"year-over-year became computable on recorded data for {yoy} — "
                        f"the `unknown` comparator path is no longer the honest one, so "
                        f"revisit metrics.py and template.py before shipping")
    sequential = comparable_symbols("recorded", "sequential")
    if sorted(sequential) != sorted(OFFLINE_SYMBOLS):
        failures.append(f"the sequential comparator is no longer available for every "
                        f"recorded symbol: {sequential}")
    if not comparable_symbols("synth", "yoy"):
        failures.append("year-over-year is no longer computable on synth either — the "
                        "product has no layer left that can exercise the YoY path")
    print(f"        depth · recorded {sorted(set(depths.values()))} kuartal, synth "
          f"{synth_depth} · yoy recorded={len(yoy)} emiten, sequential="
          f"{len(sequential)} emiten")
    return failures, len(OFFLINE_SYMBOLS) + 4


def main():
    results = [("trigger shape", *check_trigger_shape()),
               ("key parity", *check_key_parity()),
               ("period derivation", *check_period_derivation()),
               ("capex divergence", *check_capex_divergence()),
               ("symbol suffix", *check_symbol_suffix()),
               ("series depth", *check_series_depth())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)
    print("\nall six divergences are still exactly these" if not failed
          else f"\n{failed} divergence(s) moved")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
