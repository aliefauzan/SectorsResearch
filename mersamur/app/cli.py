#!/usr/bin/env python3
"""The "paste a ticker" surface. One symbol in, one paragraph out.

    python3 -m app.cli LIFE
    python3 -m app.cli LIFE ASLI --json

This is deliberately a command line and not a web app. `riset/spec.md` §9 lists the
interface as the first thing cut when time runs out, and it is the right thing to
cut: the product's claim is the measurement and the citation behind every figure,
and a terminal shows both at full fidelity for the cost of one file. A page would
have added a framework, a build step and a deploy target to say exactly the same
sentences.

What it prints is `app/render/paragraph.py`'s block: the prose, the disclaimer that
travels with it, and then every number with the endpoint and field it came from. A
reader who does not trust the paragraph can walk each line back to the same call.

Exit codes matter here, because this is the surface a person and a script share:

    0   a paragraph was produced
    1   the paragraph was refused — an uncited figure, or a symbol with no
        recording behind it. Refusing is task 18's design, not a bug: a plausible
        unattributed number is worse than a loud failure.

Zero credits. Everything is read from `research/harness/recorded/`; no socket is
opened, and no argument to this command can cause one to be.
"""
import argparse
import json
import os
import sys

if __package__ in (None, ""):                    # `python3 app/cli.py` still works
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import config, profile as profile_mod, universe
from app.cache import Cache
from app.render import paragraph as paragraph_mod


def one(symbol, cache=None, as_json=False):
    """Render one symbol. Returns the text to print, or raises."""
    profile = profile_mod.build(symbol, cache=cache)
    rendered = paragraph_mod.render(profile, cache=cache)
    if as_json:
        return json.dumps(rendered.to_dict(), ensure_ascii=False, indent=2)
    return paragraph_mod.describe(rendered)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Paragraf deskriptif untuk satu ticker IDX, dari data rekaman.")
    ap.add_argument("symbol", nargs="+",
                    help="kode saham IDX, misalnya LIFE (akhiran .JK boleh)")
    ap.add_argument("--json", action="store_true",
                    help="keluarkan paragraf beserta sitasinya sebagai JSON")
    args = ap.parse_args(argv)

    cache = Cache()
    failures = 0
    for index, raw in enumerate(args.symbol):
        want = universe.normalize(raw)
        if not want:
            print(f"{raw}: bukan kode saham yang bisa dibaca", file=sys.stderr)
            failures += 1
            continue
        try:
            block = one(want, cache=cache, as_json=args.json)
        except Exception as exc:
            # Named rather than swallowed: the two failures a reader will actually
            # hit are "no recording for this symbol" and "a figure had no citation",
            # and they call for different fixes.
            print(f"{want}: paragraf tidak dibuat — {type(exc).__name__}: {exc}",
                  file=sys.stderr)
            failures += 1
            continue
        if index:
            print()
        print(block)

    if failures:
        print(f"\n{failures} dari {len(args.symbol)} ticker tidak menghasilkan "
              f"paragraf. Daftar yang sudah punya rekaman: "
              f"{', '.join(config.WATCHLIST)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
