#!/usr/bin/env python3
"""
The HTTP surface: the same card, over a URL instead of a terminal.

    GET /card/{symbol}?date=YYYY-MM-DD    the four-pillar card, as plain text
    GET /healthz                          200, one word, no data read
    GET /health                           the same, under a name Cloud Run lets through

`/healthz` is the name the plan asks for and it answers correctly inside the container — but
behind Cloud Run it never arrives: Google's front end answers `/healthz` itself with its own
HTML 404, and the request does not appear in the revision's request log. `/health` is the same
handler under a name that reaches the process, and it is the one a probe should use.

This module adds no logic. Every number it serves is produced by `card.show()` — the same
function `./run.sh pilar` calls — and the body is that function's stdout, captured verbatim.
The gate at the bottom compares the two byte for byte by actually running both, because a
wrapper that "should" be identical is a wrapper nobody checked.

It reads no secret, opens no socket outward, and never touches the live API. `SOURCE` and
`PORT` are the only environment it looks at; `PORT` defaults to 8080 because that is the
contract Cloud Run offers a container.
"""
import io
import os
import re
import sys
import threading
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

import card
import classify
import pillars as P

#: The two shapes a caller may put in a path or a query. Anything else is a 400 and is
#: refused before a single file is opened — a scanner should not be able to make this
#: process read the disk.
SYMBOL = re.compile(r"^[A-Za-z0-9]{1,10}(?:\.[A-Za-z]{2})?$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

SOURCE = os.environ.get("SOURCE", "recorded")
PORT = int(os.environ.get("PORT", "8080"))

USAGE = (
    "KATALIS — satu simbol masuk, empat pilar keluar.\n"
    "\n"
    "  GET /card/{symbol}?date=YYYY-MM-DD\n"
    "  GET /health\n"
    "\n"
    "Bukan nasihat investasi.\n"
)


def card_text(symbol, as_of=None, source=None):
    """The card exactly as the CLI prints it, plus the exit code the CLI would return.

    `card.show` writes to stdout and returns 0 or 1. Capturing that stream — rather than
    calling `card.render` again with arguments of our own choosing — is what makes the HTTP
    body identical to the terminal output instead of merely similar to it.
    """
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = card.show(symbol, as_of, source=source or SOURCE)
    return code, out.getvalue(), err.getvalue()


def route(method, path, query):
    """(status, content_type, body) for one request. Pure: no socket, no global state."""
    if method != "GET":
        return 405, "text/plain; charset=utf-8", "hanya GET\n"
    if path in ("/healthz", "/health"):
        return 200, "text/plain; charset=utf-8", "ok\n"
    if path in ("/", ""):
        return 200, "text/plain; charset=utf-8", USAGE
    parts = [p for p in path.split("/") if p]
    if len(parts) != 2 or parts[0] != "card":
        return 404, "text/plain; charset=utf-8", "tidak ada rute itu\n"
    symbol = unquote(parts[1])
    if not SYMBOL.match(symbol):
        return 400, "text/plain; charset=utf-8", "simbol tidak berbentuk simbol\n"
    dates = parse_qs(query).get("date", [])
    if len(dates) > 1:
        return 400, "text/plain; charset=utf-8", "satu tanggal, bukan dua\n"
    as_of = dates[0] if dates else None
    if as_of is not None and not DATE.match(as_of):
        return 400, "text/plain; charset=utf-8", "tanggal harus YYYY-MM-DD\n"
    try:
        code, body, err = card_text(symbol, as_of)
    except classify.UnknownClassifier as exc:
        # A misconfigured revision must say so rather than serve a card that names the
        # engine it fell back to. 500, because the fault is the deployment's, not the
        # caller's.
        return 500, "text/plain; charset=utf-8", f"{exc}\n"
    if code != 0:
        return 404, "text/plain; charset=utf-8", err or "tidak ada deret harga\n"
    return 200, "text/plain; charset=utf-8", body


class Handler(BaseHTTPRequestHandler):
    server_version = "katalis"
    sys_version = ""

    def do_GET(self):
        parsed = urlparse(self.path)
        status, content_type, body = route("GET", parsed.path, parsed.query)
        raw = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, fmt, *args):
        """One line per request on stderr, no request body, no query values echoed."""
        sys.stderr.write("%s %s\n" % (self.command, urlparse(self.path).path))


def serve(port=None):
    httpd = ThreadingHTTPServer(("0.0.0.0", port or PORT), Handler)
    sys.stderr.write(f"katalis http on :{httpd.server_address[1]} source={SOURCE}\n")
    httpd.serve_forever()


# --------------------------------------------------------------------------------- gates

def _get(port, path):
    """One real request over a real socket, so routing is tested and not only `route()`."""
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=30) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def _running():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, httpd.server_address[1]


def check_card_route_matches_the_cli():
    """The body must equal what `cli.py pilar` prints — byte for byte, via a subprocess.

    Comparing against `card.render` would only prove this module calls that function. The
    claim the phase makes is stronger: the URL returns what the developer's terminal returns.
    Only running the CLI as its own process proves that.

    Only the demo cases on the source this process serves can be compared; the HTTP surface
    exposes one `SOURCE`, deliberately, because a `?source=` parameter would let a caller ask
    for synthetic data over a URL that looks like the real one.
    """
    import subprocess
    failures = []
    cases = [c for c in P.DEMO_CASES if c[0] == SOURCE]
    if not cases:
        return [f"no demo case runs on SOURCE={SOURCE}; the route is untested"], 1
    httpd, port = _running()
    try:
        for source, symbol, as_of in cases:
            proc = subprocess.run(
                [sys.executable, "cli.py", "--source", source, "pilar", symbol, as_of],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True, text=True, check=True)
            status, body = _get(port, f"/card/{symbol}?date={as_of}")
            if status != 200:
                failures.append(f"{symbol} {as_of}: /card returned {status}, not 200")
            elif body != proc.stdout:
                failures.append(f"{symbol} {as_of}: HTTP body differs from `cli.py pilar` "
                                f"({len(body)} bytes vs {len(proc.stdout)})")
    finally:
        httpd.shutdown()
    return failures, len(cases)


def check_misconfigured_classifier_is_a_500():
    """`CLASSIFIER=nonsense` on a revision must produce a named 500, never a fallback card."""
    failures = []
    source, symbol, as_of = next(c for c in P.DEMO_CASES if c[0] == SOURCE)
    before = os.environ.get("CLASSIFIER")
    os.environ["CLASSIFIER"] = "tidak-ada"
    try:
        status, _ctype, body = route("GET", f"/card/{symbol}", f"date={as_of}")
        if status != 500:
            failures.append(f"a card was served with an unknown CLASSIFIER: {status}")
        if "tidak-ada" not in body:
            failures.append("the 500 body does not name the unknown value")
        if "KATALIS menyatakan" in body:
            failures.append("a card body was served despite the refusal")
    finally:
        if before is None:
            os.environ.pop("CLASSIFIER", None)
        else:
            os.environ["CLASSIFIER"] = before
    return failures, 3


def check_healthz_and_refusals():
    """200 on both health names, 404 on an unknown route, 400 on every malformed input."""
    failures = []
    httpd, port = _running()
    expected = [("/healthz", 200), ("/health", 200), ("/nope", 404), ("/card", 404),
                ("/card/LIFE/lagi", 404),
                ("/card/%2e%2e%2f%2e%2e%2fetc%2fpasswd", 400),
                ("/card/LIFE?date=01-09-2026", 400),
                ("/card/LIFE?date=2026-09-01&date=2026-09-02", 400)]
    try:
        for path, want in expected:
            status, _ = _get(port, path)
            if status != want:
                failures.append(f"GET {path} returned {status}, expected {want}")
    finally:
        httpd.shutdown()
    return failures, len(expected)


def check_no_secret_can_reach_a_response():
    """A key in the environment must not appear in any body this module produces."""
    failures = []
    sentinel = "KATALIS-SENTINEL-b7f3"
    before = os.environ.get("SECTORS_API_KEY")
    os.environ["SECTORS_API_KEY"] = sentinel
    try:
        source, symbol, as_of = next(c for c in P.DEMO_CASES if c[0] == SOURCE)
        for path in (f"/card/{symbol}?date={as_of}", "/healthz", "/nope"):
            _, _, body = route("GET", urlparse(path).path, urlparse(path).query)
            if sentinel in body:
                failures.append(f"the key in SECTORS_API_KEY reached the body of {path}")
    finally:
        if before is None:
            os.environ.pop("SECTORS_API_KEY", None)
        else:
            os.environ["SECTORS_API_KEY"] = before
    return failures, 3


def check_this_module_computes_nothing():
    """No figure may be built here. The card comes from `card.show`, or it does not come."""
    failures = []
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        text = handle.read()
    body = text.split("# ---", 1)[0]
    for forbidden in ("Figure(", "P.assess(", "P.bag_from(", "sources.", "thresholds."):
        if forbidden in body:
            failures.append(f"{forbidden!r} appears above the gates — the wrapper grew logic")
    return failures, 5


def main():
    total, bad = 0, []
    for check in (check_card_route_matches_the_cli, check_misconfigured_classifier_is_a_500,
                  check_healthz_and_refusals,
                  check_no_secret_can_reach_a_response, check_this_module_computes_nothing):
        failures, count = check()
        total += count
        bad += failures
        print(f"  {check.__name__:<34} {count - len(failures)}/{count}")
    for line in bad:
        print("FAIL", line)
    print(f"{total - len(bad)}/{total} checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        raise SystemExit(main())
    serve()
