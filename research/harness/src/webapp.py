#!/usr/bin/env python3
"""
The firewall with a face — same engine, same citations, in a browser.

    cd research/harness && python3 src/webapp.py
    # then open http://127.0.0.1:8080

This is a view over `firewall.py`, not a second implementation of it. Every number on
the page comes back from `firewall.score()`, and the page refuses to render a figure
whose `(endpoint, field)` pair is missing — the same fail-closed rule the CLI has, moved
one layer out so that a broken citation is a visible red cell instead of a silent blank.

Three things the UI is responsible for that the CLI got for free:

  * **Only offering symbols that exist.** The picker is built from the files actually on
    disk, with the ones that have no broker recording marked. Typing BNBR into a box was
    how the original plan ended up demoing a symbol with no daily series; a picker that
    can only offer ADRO, ANTM, ASII, BBCA, BBRI, BMRI, BREN and TLKM cannot make that
    mistake.
  * **Showing the baseline, not just the verdict.** A sparkline with the five baseline
    days shaded and the test day marked is the difference between "trust me, 3.4 SD" and
    a reader seeing the spike for themselves.
  * **Making the source impossible to miss.** A synthetic run paints the banner red and
    says so in words. The hackathon rules require synthetic data to be labelled on screen,
    and a footnote is not a label.

Standard library only, like the rest of the harness — `http.server`, no framework, no
build step, no npm. Spends nothing: the default source is the local recordings.

    python3 src/webapp.py --self-test    # asserts the API contract without binding a port
"""
import argparse
import glob
import http.server
import json
import os
import socketserver
import sys
import urllib.parse

import firewall
import fragility
import sources

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.dirname(HERE)


def available(source):
    """Symbols this source can actually score, with their range and their flag dates.

    Built from the filesystem rather than from a hardcoded list, so a symbol can never be
    offered that has no series behind it.
    """
    if source == "synth":
        paths = sorted(glob.glob(os.path.join(HARNESS, "synth", "market", "daily", "*.json")))
        has_broker = lambda s: os.path.exists(
            os.path.join(HARNESS, "synth", "flow", "broker_top", f"{s}.json"))
    else:
        paths = sorted(glob.glob(os.path.join(HARNESS, "recorded", "v2_daily_*.json")))
        has_broker = lambda s: os.path.exists(
            os.path.join(HARNESS, "recorded", f"v2_broker-summary_{s}_top.json"))

    out = []
    for path in paths:
        with open(path) as handle:
            rows = [sources.normalize_daily(r) for r in json.load(handle)]
        rows = sorted((r for r in rows if r["date"] and r["close"] is not None),
                      key=lambda r: r["date"])
        if len(rows) <= fragility.BASELINE_DAYS:
            continue
        symbol = rows[0]["symbol"]
        flags = [rows[i]["date"] for i in range(fragility.BASELINE_DAYS, len(rows))
                 if fragility.pump_flag(rows[:i + 1], rows[i]["date"])]
        out.append({
            "symbol": symbol,
            "name": sources.company_name(source, symbol),
            "dates": [r["date"] for r in rows],
            "flags": flags,
            "broker": has_broker(symbol),
        })
    return out


def score_payload(symbol, date, source, base_url=None):
    """Run the real engine and shape it for the page, refusing anything uncited."""
    fetcher = firewall.Fetcher(source, base_url,
                               os.environ.get("SECTORS_API_KEY", "dev-key")
                               if source == "mock" else None)
    bag = firewall.gather(fetcher, symbol)
    axes, as_of, rows = firewall.score(bag, symbol, date, source)

    rendered = []
    for axis in axes:
        # The same fail-closed guarantee the CLI has: this raises rather than returning a
        # figure the page would have to draw without a source.
        citation = firewall.cite(axis.citation)
        rendered.append({
            "name": axis.name,
            "fragile": axis.fragile,
            "detail": axis.detail,
            "citation": citation,
            "values": {k: v for k, v in axis.values.items() if isinstance(v, (int, float))},
        })

    index = next((i for i, r in enumerate(rows) if r["date"] == as_of), None)
    baseline = []
    if index is not None:
        baseline = [r["date"] for r in rows[max(0, index - fragility.BASELINE_DAYS):index]]

    evaluated = [a for a in axes if a.evaluated]
    firewall.record(symbol, axes, as_of, source,
                    sum(1 for a in evaluated if a.fragile), len(evaluated))

    return {
        "symbol": symbol,
        "company": sources.company_name(source, symbol),
        "as_of": as_of,
        "source": source,
        "source_note": firewall.SOURCE_NOTE[source],
        "synthetic": source == "synth",
        "axes": rendered,
        "fragile": sum(1 for a in evaluated if a.fragile),
        "evaluated": len(evaluated),
        "series": [{"date": r["date"], "close": r["close"], "volume": r["volume"]}
                   for r in rows],
        "baseline": baseline,
        "missing": bag["missing"],
        "disclaimer": firewall.DISCLAIMER,
    }


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Firewall Tip Saham</title>
<style>
:root{--bg:#0f1115;--panel:#171a21;--line:#262b36;--ink:#e6e9ef;--dim:#8b93a7;
--red:#ff6b6b;--green:#4ec9a0;--amber:#e0a458;--blue:#6aa9ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
header{padding:22px 26px;border-bottom:1px solid var(--line)}
h1{margin:0;font-size:17px;letter-spacing:.2px}
h1 span{color:var(--dim);font-weight:400}
main{max-width:960px;margin:0 auto;padding:26px}
.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;margin-bottom:22px}
label{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.7px;
color:var(--dim);margin-bottom:5px}
select{background:var(--panel);color:var(--ink);border:1px solid var(--line);
border-radius:7px;padding:8px 11px;font:inherit;min-width:150px}
select:focus{outline:2px solid var(--blue);outline-offset:1px}
.verdict{font-size:24px;margin:0 0 4px}
.sub{color:var(--dim);margin-bottom:20px}
.axis{background:var(--panel);border:1px solid var(--line);border-left-width:3px;
border-radius:9px;padding:13px 16px;margin-bottom:10px}
.axis.fragile{border-left-color:var(--red)}
.axis.clear{border-left-color:var(--green)}
.axis.unknown{border-left-color:var(--dim)}
.axis .name{font-weight:600;letter-spacing:.6px;font-size:12px;margin-bottom:3px}
.axis.fragile .name{color:var(--red)} .axis.clear .name{color:var(--green)}
.axis.unknown .name{color:var(--dim)}
.cite{margin-top:7px;font:12px ui-monospace,SFMono-Regular,Menlo,monospace;
color:var(--dim);word-break:break-all}
.cite.bad{color:var(--red)}
.banner{border-radius:9px;padding:11px 15px;margin:20px 0;font-size:13px;
border:1px solid var(--line);background:var(--panel);color:var(--dim)}
.banner.synthetic{border-color:var(--red);background:#2a1416;color:#ffb3b3;font-weight:600}
.disclaimer{margin-top:22px;padding-top:16px;border-top:1px solid var(--line);
color:var(--dim);font-size:12px}
svg{width:100%;height:110px;display:block;background:var(--panel);
border:1px solid var(--line);border-radius:9px;margin-bottom:14px}
.legend{color:var(--dim);font-size:11px;margin:-8px 0 18px}
.err{color:var(--red)}
</style></head><body>
<header><h1>Firewall Tip Saham <span>— fragility, with every number cited</span></h1></header>
<main>
  <div class="controls">
    <div><label for="source">Source</label><select id="source">
      <option value="recorded">recorded — paid capture</option>
      <option value="synth">synth — GENERATED</option>
      <option value="mock">mock — via mock_server</option>
    </select></div>
    <div><label for="symbol">Symbol</label><select id="symbol"></select></div>
    <div><label for="date">Test date</label><select id="date"></select></div>
  </div>
  <div id="out"></div>
</main>
<script>
const $ = id => document.getElementById(id);
let universe = [];

async function loadUniverse() {
  const source = $("source").value;
  universe = await (await fetch("/api/symbols?source=" + source)).json();
  $("symbol").innerHTML = universe.map(s =>
    `<option value="${s.symbol}">${s.symbol}${s.broker ? "" : "  (no broker data)"}</option>`
  ).join("");
  loadDates();
}

function loadDates() {
  const s = universe.find(u => u.symbol === $("symbol").value);
  if (!s) return;
  // Only dates with a full baseline behind them are offered, and the ones the rule
  // already flags are marked — so a reader can go straight to a day worth looking at.
  const usable = s.dates.slice(5);
  $("date").innerHTML = usable.map(d =>
    `<option value="${d}">${d}${s.flags.includes(d) ? "  ● flagged" : ""}</option>`
  ).join("");
  const firstFlag = usable.find(d => s.flags.includes(d));
  if (firstFlag) $("date").value = firstFlag;
  run();
}

function spark(series, baseline, asOf, key, colour) {
  if (!series.length) return "";
  const vals = series.map(r => r[key]);
  const lo = Math.min(...vals), hi = Math.max(...vals), span = (hi - lo) || 1;
  const W = 900, H = 110, pad = 10;
  const x = i => pad + i * (W - 2 * pad) / Math.max(1, series.length - 1);
  const y = v => H - pad - (v - lo) / span * (H - 2 * pad);
  const line = series.map((r, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(r[key]).toFixed(1)}`).join("");
  const band = series.map((r, i) => baseline.includes(r.date)
    ? `<rect x="${(x(i) - 4).toFixed(1)}" y="0" width="8" height="${H}" fill="#6aa9ff" opacity=".13"/>` : "").join("");
  const mark = series.map((r, i) => r.date === asOf
    ? `<circle cx="${x(i).toFixed(1)}" cy="${y(r[key]).toFixed(1)}" r="4.5" fill="${colour}"/>` : "").join("");
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${key} series">
    ${band}<path d="${line}" fill="none" stroke="${colour}" stroke-width="1.8"/>${mark}</svg>`;
}

async function run() {
  const q = new URLSearchParams({ symbol: $("symbol").value, date: $("date").value,
                                  source: $("source").value });
  $("out").innerHTML = "<p class='sub'>scoring…</p>";
  const r = await fetch("/api/score?" + q);
  const d = await r.json();
  if (d.error) { $("out").innerHTML = `<p class="err">${d.error}</p>`; return; }

  const axes = d.axes.map(a => {
    const state = a.fragile === null ? "unknown" : (a.fragile ? "fragile" : "clear");
    // Fail-closed, carried into the DOM: no citation, no figure — a red cell instead.
    const cite = a.citation
      ? `<div class="cite">${a.citation}</div>`
      : `<div class="cite bad">NO CITATION — figure withheld</div>`;
    return `<div class="axis ${state}"><div class="name">${a.name}</div>
      <div>${a.citation ? a.detail : "withheld"}</div>${cite}</div>`;
  }).join("");

  $("out").innerHTML = `
    <p class="verdict">${d.symbol}${d.company ? " · " + d.company : ""}</p>
    <p class="sub">as of ${d.as_of} — fragile on ${d.fragile} of ${d.evaluated} axes evaluated${
      d.axes.length - d.evaluated ? ` (${d.axes.length - d.evaluated} not fetched)` : ""}.</p>
    ${spark(d.series, d.baseline, d.as_of, "close", "#e0a458")}
    ${spark(d.series, d.baseline, d.as_of, "volume", "#6aa9ff")}
    <p class="legend">close, then volume. Shaded band = the five baseline days. Dot = the test date.</p>
    ${axes}
    <div class="banner ${d.synthetic ? "synthetic" : ""}">SOURCE: ${d.source_note}</div>
    ${d.missing.length ? `<div class="banner">not fetched — ${d.missing.join("; ")}</div>` : ""}
    <p class="disclaimer">${d.disclaimer}</p>`;
}

$("source").onchange = loadUniverse;
$("symbol").onchange = loadDates;
$("date").onchange = run;
loadUniverse();
</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    base_url = None

    def _send(self, status, body, content_type):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}
        try:
            if parsed.path == "/":
                return self._send(200, PAGE, "text/html; charset=utf-8")
            if parsed.path == "/api/symbols":
                source = query.get("source", "recorded")
                return self._send(200, json.dumps(
                    available("synth" if source == "synth" else "recorded")),
                    "application/json")
            if parsed.path == "/api/score":
                payload = score_payload(sources.bare_symbol(query.get("symbol", "")),
                                        query.get("date") or None,
                                        query.get("source", "recorded"),
                                        self.base_url)
                return self._send(200, json.dumps(payload), "application/json")
            return self._send(404, json.dumps({"error": "no such path"}), "application/json")
        except firewall.UncitedFigure as exc:
            return self._send(500, json.dumps({"error": f"uncited figure: {exc}"}),
                              "application/json")
        except Exception as exc:                      # noqa: BLE001 — the page shows it
            return self._send(500, json.dumps({"error": f"{type(exc).__name__}: {exc}"}),
                              "application/json")

    def log_message(self, *args):
        pass                                          # one line per fetch is just noise


def check_api():
    """The contract the page depends on, asserted without binding a port."""
    failures = []
    universe = available("recorded")
    symbols = {s["symbol"] for s in universe}
    if "ADRO" not in symbols:
        failures.append("ADRO is missing from the recorded universe")
    if "BNBR" in symbols:
        failures.append("BNBR is offered but has no daily series — the picker can mislead")
    if any(len(s["dates"]) <= fragility.BASELINE_DAYS for s in universe):
        failures.append("a symbol with no usable baseline was offered")
    adro = next(s for s in universe if s["symbol"] == "ADRO")
    if "2026-08-31" not in adro["flags"]:
        failures.append("ADRO's known flag date is missing from the picker")
    if not adro["broker"]:
        failures.append("ADRO is marked as having no broker recording")

    payload = score_payload("ADRO", "2026-08-31", "recorded")
    if payload["fragile"] != 4 or payload["evaluated"] != 4:
        failures.append(f"expected 4 of 4 axes, got {payload['fragile']} of {payload['evaluated']}")
    if any(not a["citation"] for a in payload["axes"]):
        failures.append("an axis reached the page with no citation")
    if len(payload["baseline"]) != fragility.BASELINE_DAYS:
        failures.append(f"baseline band is {len(payload['baseline'])} days, not 5")
    if payload["as_of"] in payload["baseline"]:
        failures.append("the test date is inside its own baseline band")
    if not payload["synthetic"] and payload["source"] == "synth":
        failures.append("a synthetic run did not flag itself")

    synth_universe = available("synth")
    if not synth_universe:
        failures.append("the synth universe is empty")
    synth = score_payload(synth_universe[0]["symbol"], None, "synth")
    if not synth["synthetic"] or "SYNTHETIC" not in synth["source_note"]:
        failures.append("a synthetic run is not labelled as synthetic on screen")

    if "<title>Firewall Tip Saham</title>" not in PAGE:
        failures.append("the page lost its title")
    for word in firewall.ADVICE_WORDS:
        if word in PAGE.lower():
            failures.append(f"the page markup contains advice vocabulary: {word!r}")
    return failures, 11 + len(firewall.ADVICE_WORDS)


def self_test():
    failures, checked = check_api()
    mark = "PASS" if not failures else "FAIL"
    print(f"{mark}  webapp api        {checked} checked, {len(failures)} failed")
    for failure in failures:
        print(f"        {failure}")
    print("\nthe page renders only cited figures" if not failures
          else f"\n{len(failures)} divergence(s)")
    return 1 if failures else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--base-url", help="mock_server URL, for --source mock in the UI")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    Handler.base_url = args.base_url or os.environ.get("SECTORS_BASE_URL",
                                                       "http://127.0.0.1:8787")
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), Handler) as httpd:
        print(f"firewall UI on http://127.0.0.1:{args.port}  (recordings only, spends nothing)")
        print("  the mock source needs: python3 src/mock_server.py --port 8787 --credits 1000")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
