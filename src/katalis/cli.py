#!/usr/bin/env python3
"""
The terminal surface: one symbol in, one card out. Everything here is free.

    ./run.sh pilar BBCA 2026-08-14
    ./run.sh symbols
    ./run.sh method
    ./run.sh test

Nothing in this folder reaches the live API. When it does — that is Fase 7 — the call will
go through a budgeted gate of its own, not through here.
"""
import argparse
import sys

import card
import classify
import pillars as P
import sources
import thresholds as T


def cmd_pilar(args):
    return card.show(args.symbol, args.date, source=args.source)


def cmd_symbols(args):
    """What can actually be scored on each source, and why the rest cannot."""
    for source in (args.source,) if args.source != "all" else ("recorded", "synth"):
        print(f"\n{source}")
        print("  simbol        hari  jendela                  aliran broker  status")
        for symbol in sources.available_symbols(source):
            rows = sources.daily(source, symbol)
            try:
                flow = sources.broker_flow(source, symbol)
            except (sources.NotRecorded, ValueError):
                flow = []
            span = f"{rows[0]['date']}..{rows[-1]['date']}" if rows else "—"
            days = {r["date"] for r in flow}
            status = "siap"
            if not flow:
                status = "tanpa_broker"
            elif len(rows) < T.get("baseline_days") // 2:
                status = "baseline_tipis"
            print(f"  {symbol:<12} {len(rows):>4}  {span:<24} {len(days):>13}  {status}")
    print("\n`baseline_tipis` bukan bug: /v2/daily/ menyimpan 90 hari, rekaman hanya membeli 20.")
    return 0


def cmd_method(args):
    print(card.method())
    return 0


def cmd_test(args):
    """This product's gates. Each module is its own suite and its own exit code."""
    import importlib
    failed = []
    for name in ("thresholds", "sources", "classify", "pillars", "card", "server",
                 "publish"):
        print(f"\n{name}.py")
        module = importlib.import_module(name)
        if module.main() != 0:
            failed.append(name)
    print()
    if failed:
        print(f"GAGAL: {', '.join(failed)}")
        return 1
    print("Semua gate hijau.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="katalis", description=__doc__)
    parser.add_argument("--source", default="recorded",
                        choices=["recorded", "synth", "all"],
                        help="lapisan data lokal (default: recorded)")
    sub = parser.add_subparsers(dest="command")

    one = sub.add_parser("pilar", help="kartu empat pilar untuk satu simbol")
    one.add_argument("symbol")
    one.add_argument("date", nargs="?", default=None,
                     help="tanggal as-of; default hari terakhir yang ada")
    one.set_defaults(run=cmd_pilar)

    sub.add_parser("symbols", help="apa yang bisa dinilai, dan kenapa sisanya tidak") \
        .set_defaults(run=cmd_symbols)
    sub.add_parser("method", help="tiap ambang, batasnya, dan asalnya") \
        .set_defaults(run=cmd_method)
    sub.add_parser("test", help="seluruh gate produk ini").set_defaults(run=cmd_test)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    try:
        return args.run(args)
    except classify.UnknownClassifier as exc:
        # Named, on stderr, with a non-zero exit. The alternative — falling back to `rules`
        # — would print a card that says CLASSIFIER=rules to someone who asked for something
        # else, which is the one failure mode Fase 3 exists to make impossible.
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
