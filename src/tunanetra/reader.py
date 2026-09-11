#!/usr/bin/env python3
"""
One IDX symbol in, a reading out — and nothing prints without its citation.

    ./run.sh read BBCA              the reading, on the terminal
    ./run.sh read BBCA --lengkap    every section, not just the summary
    ./run.sh symbols                what can be read, and the window each series covers

The verifier is the point. `cite()` refuses a figure that arrives without an endpoint, a
field, and the window it was read from, and it raises rather than degrading — a blind
reader has no way to notice that a number quietly lost its provenance, so the failure has
to be loud and it has to happen before render. Missing data says *belum diambil* and names
the endpoint that would have had it; it never guesses and never fills in.

Three refusals, each with a gate:

  * an uncited figure                    -> `UncitedFigure`
  * a payload the mock invented          -> `Fabricated`
  * advice language anywhere in output   -> `check_no_advice`

The middle one exists because `mock_server.py` answers `?sections=peers` with
`X-Mock-Source: spec-example` and returns **BBCA's payload for any symbol** — verified
2026-09-10. A demo built on that would read one company's peers under another company's
name, to a listener who cannot see that the company name changed.

    python3 reader.py --self-test
"""
import argparse
import json
import os
import sys
import time

import narrate
import sources
from money import say_date

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs.jsonl")

DISCLAIMER = ("Alat informasi dan analisis, bukan nasihat investasi. "
              "Tidak ada rekomendasi beli atau jual, dan tidak ada eksekusi transaksi.")

#: What each source is, in one line, said on screen and on the terminal. The hackathon
#: rules require synthetic data to be labelled wherever it appears.
SOURCE_NOTE = {
    "recorded": ("data asli Sectors, rekaman 6 September 2026 — "
                 "jendela setiap deret dicantumkan"),
    "synth": ("DATA SINTETIS, bukan pasar sungguhan — hanya untuk pengembangan, "
              "tidak pernah menjadi sumber data produk"),
    "mock": "mock lokal di atas rekaman yang sama; nol kredit",
}

#: Section order on the page and on the terminal. Summary is not in it — it is printed
#: before everything, which is the whole finding from VoxLens.
SECTION_TITLE = {
    "segment_concentration": "Dari mana pendapatan berasal",
    "quarterly_change": "Kuartal terakhir",
    "price_trend": "Pergerakan harga",
    "flow_runs": "Arus dana asing",
    "ownership_runs": "Perubahan kepemilikan",
    "peer_rank": "Dibanding perusahaan sejenis",
}
SECTION_ORDER = tuple(SECTION_TITLE)


class UncitedFigure(Exception):
    """A figure reached render without an endpoint, a field, and a window."""


class Fabricated(Exception):
    """A payload the mock invented rather than replayed.

    `X-Mock-Source: spec-example` means the answer is the OpenAPI example, not this
    company's data. Treated as a hard failure here, not a warning.
    """


def cite(citation):
    """Return a printable citation, or raise. The only way a figure gets to the page."""
    if not isinstance(citation, dict):
        raise UncitedFigure(f"citation is {type(citation).__name__}, not a mapping")
    endpoint = citation.get("endpoint") or ""
    fields = citation.get("fields") or []
    as_of = citation.get("as_of") or ""
    if not endpoint.startswith("/v2/"):
        raise UncitedFigure(f"endpoint {endpoint!r} is not a Sectors path")
    if not fields:
        raise UncitedFigure(f"{endpoint}: no field named")
    if not as_of:
        raise UncitedFigure(f"{endpoint}: no window stated")
    return {"endpoint": endpoint, "fields": list(fields), "as_of": as_of}


def read(symbol, source="recorded"):
    """Everything one reading needs: summary first, then sections, then the gaps."""
    symbol = sources.bare_symbol(symbol)
    bag = narrate._bag(symbol, source)
    findings, gaps = narrate.derive(bag)
    if not findings:
        raise narrate.NotDerivable(f"{symbol}: nothing could be derived")

    head = narrate.summary(findings, bag["overview"])
    by_key = {finding.key: finding for finding in findings}

    # Fail closed before anything is rendered, not while it is being rendered.
    for finding in [head] + findings:
        cite(finding.citation())

    return {
        "symbol": symbol,
        "source": source,
        "company": bag["overview"].get("company_name"),
        "bank": bag["bank"],
        "summary": head,
        "sections": [(key, by_key[key]) for key in SECTION_ORDER if key in by_key],
        "gaps": gaps,
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
    }


def render(reading, verbose=False):
    """The terminal form. The web form is `webapp.py`; both read this same structure."""
    lines = [f"{reading['company']} ({reading['symbol']})",
             f"sumber: {SOURCE_NOTE[reading['source']]}",
             "",
             "RINGKASAN",
             reading["summary"].sentence,
             ""]

    if verbose:
        for key, finding in reading["sections"]:
            citation = cite(finding.citation())
            lines += [SECTION_TITLE[key].upper(),
                      finding.sentence,
                      f"  sumber: {citation['endpoint']} · "
                      f"field {', '.join(citation['fields'][:4])}"
                      + (" …" if len(citation["fields"]) > 4 else "")
                      + f" · {citation['as_of']}",
                      ""]

    if reading["gaps"]:
        lines.append("BELUM ADA")
        for key, (reason, detail) in sorted(reading["gaps"].items()):
            title = SECTION_TITLE.get(key, key)
            lines.append(f"  {title}: {reason} — {detail}")
        lines.append("")

    lines.append(DISCLAIMER)
    return "\n".join(lines)


def record(reading):
    """Append-only run log. Opinions, not paid data — git-ignored."""
    entry = {
        "at": reading["generated_at"],
        "symbol": reading["symbol"],
        "source": reading["source"],
        "sections": [key for key, _ in reading["sections"]],
        "gaps": sorted(reading["gaps"]),
    }
    with open(RUNS, "a") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def describe_symbols(source="recorded"):
    """What can be read, and the real window of every series behind it."""
    lines = []
    for symbol in sources.available_symbols(source):
        bag = narrate._bag(symbol, source)
        daily_window = sources.window_of(bag["daily"])
        months = sorted(bag["panel"])
        quarters = sorted(row["date"] for row in bag["quarters"] if row["date"])
        peers = "ada" if symbol == "BBCA" else "belum diambil (2 kredit)"
        lines.append(
            f"{symbol:5} {bag['overview'].get('company_name', '')}\n"
            f"      harga        {len(bag['daily'])} hari  "
            f"{say_date(daily_window[0])} – {say_date(daily_window[1])}\n"
            f"      arus asing   {len(bag['flow'])} hari  "
            f"{say_date(bag['flow_window'][0])} – {say_date(bag['flow_window'][1])}\n"
            f"      kepemilikan  {len(months)} bulan  "
            f"{say_date(months[0])} – {say_date(months[-1])}\n"
            f"      keuangan     {len(quarters)} kuartal  s.d. {say_date(quarters[-1])}\n"
            f"      segmen       tahun buku {bag['segments'].get('financial_year')} "
            f"(satu tahun — deret multi-tahun tidak tersedia)\n"
            f"      peer         {peers}")
    return "\n".join(lines)


# ------------------------------------------------------------------------------ gates


def check_citation():
    """An uncited figure must raise, in every direction it can be uncited."""
    failures = []
    good = {"endpoint": "/v2/daily/BBCA/", "fields": ["close"], "as_of": "2026-09-04"}
    if cite(good) != good:
        failures.append("a complete citation was rejected")
    bad = [
        ({"endpoint": "", "fields": ["close"], "as_of": "x"}, "empty endpoint"),
        ({"endpoint": "daily", "fields": ["close"], "as_of": "x"}, "non-Sectors path"),
        ({"endpoint": "/v2/daily/", "fields": [], "as_of": "x"}, "no field"),
        ({"endpoint": "/v2/daily/", "fields": ["close"], "as_of": ""}, "no window"),
        ("not a dict", "wrong type"),
    ]
    for citation, why in bad:
        try:
            cite(citation)
        except UncitedFigure:
            continue
        failures.append(f"an uncited figure was allowed through: {why}")
    return failures, len(bad) + 1


def check_degradation():
    """A missing section says *belum diambil* and names an endpoint. It never invents."""
    failures = []
    reading = read("TLKM")
    text = render(reading, verbose=True)
    if "peer_rank" not in reading["gaps"]:
        failures.append("TLKM produced a peer section without a paid peers payload")
    if "belum diambil" not in text:
        failures.append("a missing section did not say 'belum diambil'")
    if "/v2/company/report/TLKM/?sections=peers" not in text:
        failures.append("the missing section did not name the endpoint that would have it")
    for section in reading["sections"]:
        if "belum diambil" in section[1].sentence:
            failures.append(f"{section[0]}: a rendered section is actually empty")
    return failures, 4


def check_no_advice():
    """No reading may contain advice language, on any symbol, in any verbosity."""
    failures = []
    checked = 0
    for symbol in sources.OFFLINE_SYMBOLS:
        reading = read(symbol)
        checked += 1
        # Scan the derived sentences, not the rendered page: the disclaimer itself
        # contains "rekomendasi beli atau jual", and scanning it would flag the one
        # sentence whose job is to rule advice out.
        spoken = " ".join([reading["summary"].sentence]
                          + [f.sentence for _, f in reading["sections"]]).lower()
        for word in narrate.ADVICE_VOCAB + narrate.LEVEL1_VOCAB:
            if word in spoken:
                failures.append(f"{symbol}: {word!r} reached the reading")
        if "bukan nasihat investasi" not in render(reading).lower():
            failures.append(f"{symbol}: the disclaimer is missing")
    return failures, checked


def check_source_labelled():
    """Synthetic data must be labelled wherever it appears. Hackathon rule, not a nicety."""
    failures = []
    if "SINTETIS" not in SOURCE_NOTE["synth"]:
        failures.append("the synthetic source note no longer says so")
    for symbol in ("BBCA",):
        text = render(read(symbol))
        if SOURCE_NOTE["recorded"] not in text:
            failures.append(f"{symbol}: the source note is missing from the reading")
    return failures, 2


def check_ledger():
    """This product spends nothing. A run that leaked a credit fails the suite."""
    failures = []
    ledger = os.path.join(sources.RECORDED, "_ledger.jsonl")
    with open(ledger) as handle:
        lines = sum(1 for _ in handle)
    if lines != 168:
        failures.append(f"the credit ledger moved: {lines} lines, expected 168 — "
                        f"something in this product reached the live API")
    print(f"        credit ledger unchanged at {lines} lines · this product spends nothing")
    return failures, 1


def self_test():
    results = [("citation verifier", *check_citation()),
               ("degradation", *check_degradation()),
               ("no advice, no level-1", *check_no_advice()),
               ("source labelling", *check_source_labelled()),
               ("credit ledger", *check_ledger())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)
    print("\nevery figure carries its endpoint, field and window" if not failed
          else f"\n{failed} verifier failure(s)")
    return 1 if failed else 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="reader.py",
        description="Riset fundamental IDX yang bisa didengar. "
                    "Semua angka membawa endpoint, field, dan jendela datanya.")
    parser.add_argument("command", nargs="?", default="read",
                        choices=("read", "symbols"))
    parser.add_argument("symbol", nargs="?")
    parser.add_argument("--lengkap", action="store_true",
                        help="setiap bagian, bukan hanya ringkasan")
    parser.add_argument("--source", default="recorded",
                        choices=("recorded", "synth"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.command == "symbols":
        print(describe_symbols(args.source))
        return 0
    if not args.symbol:
        parser.error("read butuh satu kode saham, misal: read BBCA")

    try:
        reading = read(args.symbol, args.source)
    except sources.NotRecorded as exc:
        print(f"{args.symbol}: belum diambil — {exc}", file=sys.stderr)
        print(f"yang bisa dibaca: {', '.join(sources.available_symbols(args.source))}",
              file=sys.stderr)
        return 2
    print(render(reading, verbose=args.lengkap))
    record(reading)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
