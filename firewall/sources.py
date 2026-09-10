#!/usr/bin/env python3
"""
One shared way to read a Sectors payload, so no parser is ever written twice.

`recorded/` and `synth/` disagree about shape in six measured places, and every one of
them is a `KeyError` waiting for the demo. The disagreements are handled here and
nowhere else — `fragility.py` never sees a raw payload, and `firewall.py` never reaches
into a dict with `[]`. When a seventh divergence turns up, this is the only file that
changes.

    from sources import load, results_of, normalize_broker_top, cohort_index

    rows = [normalize_daily(r) for r in results_of(load("recorded", "daily", "ADRO"))]

The measured divergences, all re-checked against the 2026-09-06 capture:

  1. news is `{results, pagination}` in `recorded/`, a bare list in `synth/`
  2. suspensions carry `pdf_url` in `recorded/`, `notice_url` in `synth/`
  3. broker-top echoes `origin`/`cohort` in `recorded/`, omits them in `synth/`
  4. `/v2/brokers/` has **no `origin`** in `recorded/` but does in `synth/` — the
     research's §B8 claim (correction C1) is true of the synthetic file only, which is
     exactly how a parser written against dummy data breaks on real payloads
  5. broker-top *buyer rows* carry `rank` and `sell_idr` in `recorded/`, and instead
     carry inline `origin`/`cohort` in `synth/`. Real cohort needs the join to
     `/v2/brokers/`; synthetic cohort is free. Code that relies on the free one silently
     stops working on the payload that matters
  6. news rows carry `body`/`thumbnail`/`dimension` in `recorded/` and `id`/`sentiment`
     in `synth/` — there is no `dimension` to score on synthetic news

Normalization fills a missing field with None rather than dropping the key, so the two
sources always present the same key set and a caller cannot accidentally depend on a
field that only one of them has.

    python3 src/sources.py    # asserts real and synth normalize to identical key sets
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: The three data layers live in the research harness, not beside the product. They were
#: paid for in credits and they are evidence, so they stay where the capture tooling and
#: the ledger that records what they cost can see them. This is the only file that knows
#: the path; everything else imports RECORDED/SYNTH from here.
HARNESS = os.path.join(ROOT, "research", "harness")
RECORDED = os.path.join(HARNESS, "recorded")
SYNTH = os.path.join(HARNESS, "synth")

#: Which `reason` strings mark a suspension as pump-related, per source.
#:
#: Kept as one table with two entries because the vocabularies genuinely differ: the
#: real notices are Indonesian IDX cooling-down text (18 of the 20 captured rows), while
#: `synth_extended.py` writes generic English reasons and only 4 of its 20 rows are
#: pump-shaped at all. A single merged list would quietly label synthetic rows with real
#: IDX language that never appears in them.
#:
#: The real list covers only the 20 rows that were paid for. The remaining 563 reasons
#: are unread — that is the ~30-credit Phase 2 pull, and until it happens this vocabulary
#: is a floor, not the whole language.
LABEL_VOCAB = {
    "real": ["peningkatan harga kumulatif yang signifikan"],
    "synth": ["Significant price and volume movement", "Unusual Market Activity (UMA)"],
}

#: Endpoint path per dataset, for the citation a figure has to carry.
ENDPOINT = {
    "daily": "/v2/daily/{symbol}/",
    "broker_top": "/v2/broker-summary/{symbol}/top/",
    "brokers": "/v2/brokers/",
    "news": "/v2/news/",
    "suspensions": "/v2/suspensions/",
    "most_traded": "/v2/most-traded/",
}


class NotRecorded(Exception):
    """Asked for a payload this source does not hold.

    Raised rather than returning an empty list, because "no data" and "no file" lead to
    different sentences: the first is a clear axis, the second is "not fetched". Only
    the caller knows which it is looking at.
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
            "daily": f"v2_daily_{symbol}",
            "broker_top": f"v2_broker-summary_{symbol}_top",
            "brokers": "v2_brokers",
            "news": "v2_news__extension-idx",
            "suspensions": "v2_suspensions",
            "most_traded": "v2_most-traded",
        }
        return _read(os.path.join(RECORDED, slugs[dataset] + ".json"))
    if source == "synth":
        paths = {
            "daily": os.path.join(SYNTH, "market", "daily", f"{symbol}.json"),
            "broker_top": os.path.join(SYNTH, "flow", "broker_top", f"{symbol}.json"),
            "brokers": os.path.join(SYNTH, "flow", "brokers.json"),
            "news": os.path.join(SYNTH, "market", "news.json"),
            "suspensions": os.path.join(SYNTH, "company", "suspensions.json"),
        }
        if dataset not in paths:
            raise NotRecorded(f"synth has no {dataset}")
        return _read(paths[dataset])
    raise ValueError(f"unknown source {source!r}")


def results_of(payload):
    """The rows of a payload, whether it wraps them in `results` or is already a list."""
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
    """The `pagination` block, or None on a source that does not paginate."""
    return payload.get("pagination") if isinstance(payload, dict) else None


def bare_symbol(symbol):
    """`BBCA.JK` and `BBCA` are the same stock. Recorded rows use the suffix, CLI does not."""
    return (symbol or "").upper().replace(".JK", "")


def normalize_daily(row):
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


def normalize_suspension(row):
    """Divergence 2: `notice_url` becomes `pdf_url`; synth-only fields survive as None."""
    return {
        "symbol": bare_symbol(row.get("symbol")),
        "company_name": row.get("company_name"),
        "suspension_date": row.get("suspension_date"),
        "resumption_date": row.get("resumption_date"),
        "reason": row.get("reason"),
        "pdf_url": row.get("pdf_url") or row.get("notice_url"),
    }


def normalize_news(row):
    """Divergence 6: `dimension` is real-only, `sentiment` is synth-only. Both keys exist."""
    return {
        "title": row.get("title"),
        "source": row.get("source"),
        "timestamp": row.get("timestamp"),
        "symbols": [bare_symbol(s) for s in (row.get("symbols") or [])],
        "sector": row.get("sector"),
        "sub_sector": row.get("sub_sector"),
        "tags": row.get("tags") or [],
        "dimension": row.get("dimension"),
        "sentiment": row.get("sentiment"),
    }


def normalize_broker(row):
    """Divergence 4: `origin` is dropped even though synth has it — real payloads do not.

    Keeping it would let a caller write `broker["origin"]` against `synth/` and ship a
    KeyError to the demo. `is_foreign` is the field that exists in both, and it carries
    the same information.
    """
    return {
        "code": row.get("code"),
        "name": row.get("name"),
        "is_foreign": row.get("is_foreign"),
        "cohort": row.get("cohort"),
        "license_type": row.get("license_type"),
    }


def normalize_broker_row(row):
    """Divergence 5: `rank`/`sell_idr` are real-only, inline `cohort` is synth-only.

    The inline cohort is preserved so a synthetic run does not need the join, but nothing
    may *depend* on it — `cohort_index` from `/v2/brokers/` is the path that works on both.
    """
    return {
        "rank": row.get("rank"),
        "broker_code": row.get("broker_code"),
        "net_idr": row.get("net_idr"),
        "buy_idr": row.get("buy_idr"),
        "sell_idr": row.get("sell_idr"),
        "cohort": row.get("cohort"),
    }


def normalize_broker_top(payload):
    """Divergence 3: the `origin`/`cohort` echoes are request parameters, not data.

    Read with `.get()` because `synth/` omits them entirely, and remember what they are:
    correction C2 — on a real payload these are the strings that were *sent*, not a
    property of the brokers that came back.
    """
    payload = payload or {}
    return {
        "symbol": bare_symbol(payload.get("symbol")),
        "start": payload.get("start"),
        "end": payload.get("end"),
        "origin_echo": payload.get("origin"),
        "cohort_echo": payload.get("cohort"),
        "top_buyers": [normalize_broker_row(r) for r in (payload.get("top_buyers") or [])],
        "top_sellers": [normalize_broker_row(r) for r in (payload.get("top_sellers") or [])],
    }


def cohort_index(brokers_payload):
    """`{broker_code: cohort}` — the join correction C2 says the response will not do for you."""
    return {b["code"]: b["cohort"]
            for b in (normalize_broker(r) for r in results_of(brokers_payload))
            if b["code"]}


def is_pump_label(reason, source):
    """Does this suspension `reason` belong to the pump vocabulary for its source?"""
    if not reason:
        return False
    vocab = LABEL_VOCAB["real" if source == "recorded" else "synth"]
    return any(term.lower() in reason.lower() for term in vocab)


def news_for(payload, symbol, start=None, end=None):
    """Company news mentioning `symbol`, optionally windowed. Dates compare as ISO strings."""
    wanted = bare_symbol(symbol)
    hits = []
    for row in (normalize_news(r) for r in results_of(payload)):
        if wanted not in row["symbols"]:
            continue
        stamp = (row["timestamp"] or "")[:10]
        if start and stamp < start:
            continue
        if end and stamp > end:
            continue
        hits.append(row)
    return hits


def company_name(source, symbol):
    """Best-effort display name. None when no local payload happens to carry one.

    The screener is the only recorded call that pairs a symbol with a name, and it holds
    200 of them — so this resolves for large caps and returns None for the rest. A name is
    cosmetic; nothing scores on it, and it is never worth a credit to look one up.
    """
    wanted = bare_symbol(symbol)
    patterns = ([os.path.join(RECORDED, "v2_companies*.json"),
                 os.path.join(RECORDED, "v2_most-traded.json")] if source != "synth"
                else [os.path.join(SYNTH, "market", "companies.json")])
    for pattern in patterns:
        for path in sorted(glob.glob(pattern)):
            try:
                payload = _read(path)
            except (NotRecorded, ValueError):
                continue
            groups = payload.values() if isinstance(payload, dict) and "results" not in payload \
                else [results_of(payload)]
            for group in groups:
                if not isinstance(group, list):
                    continue
                for row in group:
                    if isinstance(row, dict) and bare_symbol(row.get("symbol")) == wanted \
                            and row.get("company_name"):
                        return row["company_name"]
    return None


def _synth_symbol(dataset):
    pattern = {"daily": os.path.join(SYNTH, "market", "daily", "*.json"),
               "broker_top": os.path.join(SYNTH, "flow", "broker_top", "*.json")}[dataset]
    paths = sorted(glob.glob(pattern))
    return os.path.splitext(os.path.basename(paths[0]))[0] if paths else None


def check_key_parity():
    """The point of the file: the same dataset from either source normalizes identically."""
    failures = []
    checked = 0
    # `diverges` records whether the two sources are *known* to disagree on raw keys.
    # daily is the one dataset that agrees by construction — it is the MVP's main input,
    # and if it ever starts diverging that is news, so it is asserted in both directions.
    cases = [
        ("daily", normalize_daily, "ADRO", _synth_symbol("daily"), False),
        ("suspensions", normalize_suspension, None, None, True),
        ("news", normalize_news, None, None, True),
        ("brokers", normalize_broker, None, None, True),
    ]
    for dataset, normalize, real_symbol, synth_symbol, diverges in cases:
        try:
            real = results_of(load("recorded", dataset, real_symbol))
            synth = results_of(load("synth", dataset, synth_symbol))
        except NotRecorded as exc:
            failures.append(f"{dataset}: {exc}")
            continue
        if not real or not synth:
            failures.append(f"{dataset}: a source returned no rows "
                            f"(real={len(real)}, synth={len(synth)})")
            continue
        checked += 1
        raw_real, raw_synth = set(real[0]), set(synth[0])
        if diverges and raw_real == raw_synth:
            failures.append(f"{dataset}: raw key sets already match — "
                            f"the divergence this normalizer exists for is gone")
        if not diverges and raw_real != raw_synth:
            failures.append(f"{dataset}: raw key sets have started to diverge — "
                            f"only-real={sorted(raw_real - raw_synth)} "
                            f"only-synth={sorted(raw_synth - raw_real)}")
        keys_real, keys_synth = set(normalize(real[0])), set(normalize(synth[0]))
        if keys_real != keys_synth:
            failures.append(f"{dataset}: normalized keys differ — "
                            f"only-real={sorted(keys_real - keys_synth)} "
                            f"only-synth={sorted(keys_synth - keys_real)}")

    checked += 1
    real_top = normalize_broker_top(load("recorded", "broker_top", "ADRO"))
    synth_top = normalize_broker_top(load("synth", "broker_top", _synth_symbol("broker_top")))
    if set(real_top) != set(synth_top):
        failures.append("broker_top: normalized envelope keys differ")
    if set(real_top["top_buyers"][0]) != set(synth_top["top_buyers"][0]):
        failures.append("broker_top: normalized buyer keys differ")
    if real_top["origin_echo"] is None or synth_top["origin_echo"] is not None:
        failures.append("broker_top: the origin echo is no longer real-only — "
                        "divergence 3 has changed shape")
    return failures, checked


def check_shape_helpers():
    """`results_of` and the url/symbol normalizations, including the empty cases."""
    failures = []
    if results_of({"results": [1, 2]}) != [1, 2]:
        failures.append("results_of did not unwrap a paginated payload")
    if results_of([1, 2]) != [1, 2]:
        failures.append("results_of did not pass a bare list through")
    if results_of(None) != [] or results_of({}) != []:
        failures.append("results_of did not degrade to an empty list")
    if pagination_of(load("recorded", "suspensions")) is None:
        failures.append("recorded suspensions lost their pagination block")
    if pagination_of(load("synth", "suspensions")) is not None:
        failures.append("synth suspensions grew a pagination block")

    synth_row = normalize_suspension(results_of(load("synth", "suspensions"))[0])
    if not synth_row["pdf_url"]:
        failures.append("notice_url was not mapped onto pdf_url")
    if bare_symbol("ADRO.JK") != "ADRO" or bare_symbol(None) != "":
        failures.append("bare_symbol did not strip the .JK suffix")

    if normalize_broker_row({}) is None or normalize_broker_row({})["buy_idr"] is not None:
        failures.append("a broker row without buy_idr did not read as None")
    return failures, 8


def check_label_vocab():
    """Each vocabulary must actually match rows in its own source, and not in the other."""
    failures = []
    real = [normalize_suspension(r) for r in results_of(load("recorded", "suspensions"))]
    synth = [normalize_suspension(r) for r in results_of(load("synth", "suspensions"))]

    real_hits = sum(1 for r in real if is_pump_label(r["reason"], "recorded"))
    synth_hits = sum(1 for r in synth if is_pump_label(r["reason"], "synth"))
    if real_hits != 18:
        failures.append(f"expected 18 of 20 recorded rows to be cooling-down, got {real_hits}")
    if synth_hits != 4:
        failures.append(f"expected 4 of 20 synthetic rows to be pump-shaped, got {synth_hits}")

    crossed = sum(1 for r in real if is_pump_label(r["reason"], "synth"))
    if crossed:
        failures.append(f"the synth vocabulary matched {crossed} real rows — "
                        f"the two vocabularies are not separable")
    print(f"        recorded {real_hits}/{len(real)} cooling-down · "
          f"synth {synth_hits}/{len(synth)} pump-shaped · "
          f"563 real reasons still unread (Phase 2, ~30 credits)")
    return failures, 3


def main():
    results = [("key parity", *check_key_parity()),
               ("shape helpers", *check_shape_helpers()),
               ("label vocabulary", *check_label_vocab())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:18} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)

    print("\nreal and synth normalize identically" if not failed
          else f"\n{failed} normalization divergence(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
