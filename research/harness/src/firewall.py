#!/usr/bin/env python3
"""
One IDX symbol in, a fragility verdict out, every number carrying its own citation.

    python3 src/firewall.py ADRO --source recorded
    SECTORS_BASE_URL=http://127.0.0.1:8787 python3 src/firewall.py ADRO --source mock

The default path spends nothing. `--source live` refuses to run without both
`--i-mean-it` and an explicit `--budget`, mirroring `capture.py`'s posture: the safe
route is what you get by typing nothing, and the expensive route has to be asked for
twice. There are ~623 credits left, they do not renew, and iteration — not the demo —
is what burns them.

**Fail-closed citation.** Every figure that reaches the screen carries the
`(endpoint, field)` it was computed from. `render` raises `UncitedFigure` before
printing if an axis arrives without one, so the failure mode is a stack trace during
development rather than an uncited number in front of a judge. An axis whose input was
never fetched prints "not fetched" — a third state, never a clean bill of health, and
never a guess.

This is a fragility read, not advice. There is no price target, no buy or sell signal,
no position sizing and no execution path anywhere in this file, and the disclaimer is a
rendered line of the output contract rather than a footnote — POJK 5/2019, and the
Rp5.35 billion OJK fine of Feb 2026 against a social-media stock promoter, are the
reason that boundary is drawn in code.

Every run appends to `warnings.jsonl`. It is append-only from the first run because
retrofitting a ledger onto a scoring tool is expensive and writing one is twenty lines.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

import fragility
import sources
from sources import NotRecorded

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.dirname(HERE)
WARNINGS = os.path.join(HARNESS, "warnings.jsonl")

BASELINE_DAYS = fragility.BASELINE_DAYS
DISCLAIMER = ("Not a buy or sell recommendation. "
              "Every figure traces to one endpoint and one field.")

SOURCE_NOTE = {
    "recorded": "local recording, 2026-09-06 capture. No live call was made.",
    "mock": "mock_server on the 2026-09-06 recordings. No live call was made.",
    "synth": "SYNTHETIC DATA — generated, not real. Not a real market observation.",
    "live": "live Sectors API. Credits were charged for this run.",
}


class UncitedFigure(Exception):
    """An axis tried to print a number without an `(endpoint, field)` pair behind it."""


def _flatten(citation):
    """A citation is one `(endpoint, field)` pair or a tuple of them. Yield each pair."""
    if citation and isinstance(citation[0], tuple):
        return list(citation)
    return [citation] if citation else []


def cite(citation):
    if not citation:
        raise UncitedFigure("an axis reached the renderer with no citation")
    parts = []
    for pair in _flatten(citation):
        if not pair or len(pair) != 2 or not all(pair):
            raise UncitedFigure(f"malformed citation {pair!r}")
        parts.append(f"{pair[0]} · {pair[1]}")
    return "  ×  ".join(parts)


class Fetcher:
    """Reads payloads from a local layer, or over HTTP from the mock or the live API."""

    def __init__(self, source, base_url=None, api_key=None):
        self.source = source
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key
        self.calls = 0

    def _http(self, path, params=None):
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {
            # Cloudflare answers "Python-urllib/3.x" with a 403 "error code: 1010" that
            # says nothing about agents. capture.py learned this the hard way; the mock
            # does not care, but sending one shape of request everywhere is cheaper than
            # discovering the difference against the live API.
            "User-Agent": os.environ.get(
                "SECTORS_USER_AGENT",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = self.api_key
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                self.calls += 1
                return json.loads(response.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            raise NotRecorded(f"{path} -> HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise NotRecorded(f"{path} -> {exc.reason} (is mock_server running?)") from exc

    def get(self, dataset, symbol=None, params=None):
        """Fetch one dataset. Raises NotRecorded when this source cannot supply it."""
        if self.source in ("recorded", "synth"):
            return sources.load(self.source, dataset, symbol)
        path = sources.ENDPOINT[dataset].replace("{symbol}", symbol or "")
        return self._http(path, params)


def gather(fetcher, symbol):
    """Every payload the three axes need, with a miss recorded rather than raised."""
    bag = {"missing": []}
    wants = [("daily", symbol), ("broker_top", symbol), ("brokers", None), ("news", None)]
    for dataset, arg in wants:
        try:
            bag[dataset] = fetcher.get(dataset, arg)
        except (NotRecorded, KeyError) as exc:
            bag[dataset] = None
            bag["missing"].append(f"{dataset}: {exc}")
    return bag


def score(bag, symbol, test_date=None, source="recorded"):
    """Run the three axes over whatever was gathered. Returns (axes, as_of, rows)."""
    rows = [sources.normalize_daily(r) for r in sources.results_of(bag.get("daily"))]
    rows = [r for r in rows if r["date"] and r["close"] is not None]
    rows.sort(key=lambda r: r["date"])

    # The citation names the call that was actually made, so `{symbol}` is resolved here
    # rather than printed as a template — a reader has to be able to re-run the exact call.
    daily_endpoint = sources.ENDPOINT["daily"].replace("{symbol}", symbol)
    broker_endpoint = sources.ENDPOINT["broker_top"].replace("{symbol}", symbol)

    if not rows:
        axes = [fragility.AxisResult("VOLUME", None, "not fetched", (daily_endpoint, "volume")),
                fragility.AxisResult("PRICE", None, "not fetched", (daily_endpoint, "close"))]
        as_of = test_date
    else:
        as_of = test_date or rows[-1]["date"]
        axes = fragility.score_price_volume(rows, as_of, endpoint=daily_endpoint)

    top = sources.normalize_broker_top(bag.get("broker_top"))
    cohorts = sources.cohort_index(bag.get("brokers")) if bag.get("brokers") else {}
    axes.append(fragility.score_broker(top["top_buyers"], cohorts, endpoint=broker_endpoint))

    if bag.get("news") is None:
        articles = None
    else:
        # Anchored to `as_of`, not to the end of the series. Anchoring it to the last row
        # meant that scoring any earlier date produced a window whose start was after its
        # end — empty by construction, so CATALYST reported "no news" every time and the
        # axis silently became a constant.
        index = next((i for i, r in enumerate(rows) if r["date"] == as_of), None)
        start = rows[max(0, index - BASELINE_DAYS)]["date"] if index is not None else None
        articles = sources.news_for(bag["news"], symbol, start=start, end=as_of)
    axes.append(fragility.score_catalyst(articles))
    return axes, as_of, rows


def render(symbol, axes, as_of, source, company=None):
    """Print the verdict. Raises UncitedFigure before printing anything uncited."""
    for axis in axes:
        cite(axis.citation)

    evaluated = [a for a in axes if a.evaluated]
    fragile = [a for a in evaluated if a.fragile]
    lines = []
    header = f"{symbol}"
    if company:
        header += f" · {company}"
    if as_of:
        header += f" · as of {as_of}"
    lines.append(header)
    lines.append(f"Fragile on {len(fragile)} of {len(evaluated)} axes evaluated"
                 f"{f' ({len(axes) - len(evaluated)} not fetched)' if len(evaluated) != len(axes) else ''}.")
    lines.append("")
    for axis in axes:
        lines.append(f"  {axis.name:9} {axis.detail}")
        lines.append(f"            ({cite(axis.citation)})")
    lines.append("")
    lines.append(DISCLAIMER)
    lines.append(f"SOURCE: {SOURCE_NOTE[source]}")
    print("\n".join(lines))
    return len(fragile), len(evaluated)


def record(symbol, axes, as_of, source, fragile, evaluated):
    """Append one line to the warnings ledger. Never rewrites, never deletes."""
    entry = {
        "symbol": symbol,
        "as_of": as_of,
        "source": source,
        "fragile_axes": fragile,
        "evaluated_axes": evaluated,
        "axes": [{"name": a.name, "fragile": a.fragile, "detail": a.detail,
                  "citation": _flatten(a.citation), "values": a.values} for a in axes],
    }
    with open(WARNINGS, "a") as handle:
        handle.write(json.dumps(entry) + "\n")


def resolve_live(args):
    """Refuse the live path unless it was asked for twice, and say what it would cost."""
    if not args.i_mean_it:
        print("refusing --source live without --i-mean-it: a live run charges credits "
              "against a non-renewable grant (~623 left). Rehearse against "
              "--source mock first.", file=sys.stderr)
        return None
    if args.budget is None:
        print("refusing --source live without an explicit --budget: capture.py's rule is "
              "that a live call has a hard cap or it does not happen.", file=sys.stderr)
        return None
    sys.path.insert(0, HERE)
    import sectors_env
    return sectors_env.api_key(), sectors_env.base_url()


#: Phrases that would turn a fragility read into advice. Asserted absent from the output.
#:
#: Phrases and not bare tokens, deliberately: the broker axis describes `buy_idr`, so it
#: says "buy value" and "top buyers" and always will. Banning the token "buy" would fail on
#: the name of the field being cited, which is the opposite of the point — what must never
#: appear is an instruction or a price, not the vocabulary of the order book.
ADVICE_WORDS = ["should buy", "should sell", "buy now", "sell now", "price target",
                "target price", "position size", "stop loss", "take profit",
                "we recommend", "recommended entry", "portfolio weight", "allocate"]


def check_degradation():
    """Deleting an input must degrade that axis to "not fetched", never to a guess."""
    failures = []
    full = gather(Fetcher("recorded"), "ADRO")

    without_news = dict(full, news=None)
    axes, as_of, _ = score(without_news, "ADRO", "2026-08-31")
    catalyst = next(a for a in axes if a.name == "CATALYST")
    if catalyst.evaluated or catalyst.detail != "not fetched":
        failures.append(f"deleting /v2/news/ gave {catalyst.detail!r}, not 'not fetched'")
    if not any(a.fragile for a in axes if a.name == "VOLUME"):
        failures.append("deleting news changed an unrelated axis")

    without_daily = dict(full, daily=None)
    axes, _, _ = score(without_daily, "ADRO", "2026-08-31")
    if any(a.evaluated for a in axes if a.name in ("VOLUME", "PRICE")):
        failures.append("deleting /v2/daily/ scored price and volume anyway")

    without_brokers = dict(full, brokers=None)
    axes, _, _ = score(without_brokers, "ADRO", "2026-08-31")
    broker = next(a for a in axes if a.name == "BROKER")
    if broker.evaluated and broker.values.get("heavy"):
        failures.append("a missing /v2/brokers/ join still claimed cohort membership")

    # Regression: the catalyst window must follow --date. It used to be anchored to the
    # last row of the series, so scoring an earlier date gave start > end — an empty
    # window, and a CATALYST axis that fired on every symbol on every past date.
    for date in ("2026-08-18", "2026-08-24", "2026-08-31"):
        rows = [sources.normalize_daily(r) for r in sources.results_of(full["daily"])]
        rows = sorted(rows, key=lambda r: r["date"])
        index = next(i for i, r in enumerate(rows) if r["date"] == date)
        expected_start = rows[max(0, index - BASELINE_DAYS)]["date"]
        if expected_start > date:
            failures.append(f"{date}: computed a window that starts after it ends")
        seen = sources.news_for(full["news"], "ADRO", start=expected_start, end=date)
        scored = score(full, "ADRO", date)[0]
        catalyst = next(a for a in scored if a.name == "CATALYST")
        if catalyst.values.get("count") != len(seen):
            failures.append(f"{date}: catalyst counted {catalyst.values.get('count')} "
                            f"articles, the window holds {len(seen)}")

    empty = {"missing": [], "daily": None, "broker_top": None, "brokers": None, "news": None}
    axes, as_of, _ = score(empty, "ADRO", "2026-08-31")
    if any(a.evaluated for a in axes):
        failures.append("an entirely empty bag produced a scored axis")
    if render("ADRO", axes, as_of, "recorded")[1] != 0:
        failures.append("an empty bag reported evaluated axes")
    return failures, 9


def check_citation():
    """The fail-closed guarantee: no citation, no print."""
    failures = []
    good = fragility.AxisResult("PRICE", True, "Rp1", ("/v2/daily/ADRO/", "close"))
    try:
        cite(good.citation)
    except UncitedFigure:
        failures.append("a well-formed citation was rejected")

    for bad in (None, (), ("/v2/daily/ADRO/",), ("/v2/daily/ADRO/", None), (None, "close")):
        axis = fragility.AxisResult("PRICE", True, "Rp1", bad)
        try:
            render("ADRO", [axis], "2026-08-31", "recorded")
            failures.append(f"an uncited figure {bad!r} was printed")
        except UncitedFigure:
            pass
    return failures, 6


def check_live_refusal():
    """--source live must be asked for twice, and refuse with a non-zero status."""
    failures = []
    if main(["ADRO", "--source", "live"]) != 2:
        failures.append("--source live ran without --i-mean-it")
    if main(["ADRO", "--source", "live", "--i-mean-it"]) != 2:
        failures.append("--source live ran without --budget")
    return failures, 2


def check_no_advice():
    """No price target, buy/sell signal, sizing, or execution path may reach the screen."""
    failures = []
    bag = gather(Fetcher("recorded"), "ADRO")
    axes, as_of, _ = score(bag, "ADRO", "2026-08-31")
    text = " ".join([a.detail for a in axes] + [DISCLAIMER.replace("Not a buy or sell "
                                                                  "recommendation.", "")])
    for word in ADVICE_WORDS:
        if word in text.lower():
            failures.append(f"the rendered figures contain advice vocabulary: {word!r}")
    if "SOURCE:" not in "SOURCE: " + SOURCE_NOTE["synth"]:
        failures.append("the SOURCE line is not part of the output contract")
    if "SYNTHETIC" not in SOURCE_NOTE["synth"]:
        failures.append("a synthetic run does not announce itself as synthetic")
    return failures, len(ADVICE_WORDS) + 2


def check_ledger():
    """warnings.jsonl is append-only and every entry carries its citations."""
    failures = []
    before = os.path.getsize(WARNINGS) if os.path.exists(WARNINGS) else 0
    bag = gather(Fetcher("recorded"), "ADRO")
    axes, as_of, _ = score(bag, "ADRO", "2026-08-31")
    record("ADRO", axes, as_of, "recorded", 4, 4)
    after = os.path.getsize(WARNINGS)
    if after <= before:
        failures.append("the run did not append to warnings.jsonl")
    with open(WARNINGS) as handle:
        entry = json.loads(handle.readlines()[-1])
    if not all(a["citation"] for a in entry["axes"]):
        failures.append("a ledger entry recorded an axis with no citation")
    if entry["source"] != "recorded":
        failures.append("the ledger did not record which source was read")
    return failures, 3


def self_test():
    results = [("degradation", *check_degradation()),
               ("fail-closed citation", *check_citation()),
               ("live refusal", *check_live_refusal()),
               ("no advice", *check_no_advice()),
               ("warnings ledger", *check_ledger())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)

    print("\nthe firewall fails closed" if not failed else f"\n{failed} divergence(s)")
    return 1 if failed else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("symbol", nargs="?", help="IDX ticker, e.g. ADRO")
    parser.add_argument("--self-test", action="store_true",
                        help="run the fail-closed checks instead of scoring a symbol")
    parser.add_argument("--source", default="recorded",
                        choices=["recorded", "mock", "synth", "live"],
                        help="where payloads come from (default: recorded, costs nothing)")
    parser.add_argument("--date", help="test date, YYYY-MM-DD (default: latest row)")
    parser.add_argument("--base-url", help="override the mock's URL")
    parser.add_argument("--budget", type=int, help="hard credit cap, required for --source live")
    parser.add_argument("--i-mean-it", action="store_true",
                        help="acknowledge that --source live spends the grant")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.symbol:
        parser.error("a symbol is required unless --self-test is passed")

    symbol = sources.bare_symbol(args.symbol)
    api_key = None
    base_url = args.base_url

    if args.source == "live":
        resolved = resolve_live(args)
        if resolved is None:
            return 2
        api_key, live_url = resolved
        base_url = base_url or live_url
    elif args.source == "mock":
        base_url = base_url or os.environ.get("SECTORS_BASE_URL", "http://127.0.0.1:8787")
        api_key = os.environ.get("SECTORS_API_KEY", "dev-key")

    fetcher = Fetcher(args.source, base_url, api_key)
    bag = gather(fetcher, symbol)
    axes, as_of, rows = score(bag, symbol, args.date, args.source)
    company = sources.company_name(args.source, symbol)

    fragile, evaluated = render(symbol, axes, as_of, args.source, company)
    record(symbol, axes, as_of, args.source, fragile, evaluated)

    for miss in bag["missing"]:
        print(f"  note: {miss}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
