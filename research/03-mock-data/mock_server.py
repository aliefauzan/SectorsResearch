#!/usr/bin/env python3
"""
Offline stand-in for https://api.sectors.app.

Serves the official example response for every one of the 70 documented v2
endpoints, and emulates the parts of the real API that break your code if you
only discover them in production:

  * `Authorization` header is required (401 + structured error code otherwise)
  * a credit meter that charges the documented per-endpoint cost and returns
    402 `insufficient_credits` when the budget runs out
  * `X-Credits-Charged` / `X-Credits-Remaining` response headers
  * 404 for unknown paths (free), and a *billed* 404 for a well-formed request
    naming a resource that does not exist -- `/v2/company/report/ZZZZ/` costs a
    credit, exactly as the real API bills it ("404 = lookup performed")
  * 410 Gone for any `/v1/*` path (matching the real v1 sunset on 2026-05-11)
  * optional injected latency and random 429/503 so you can prove your retry
    and back-off logic actually works

It serves **recorded live responses in preference to spec examples** when
`capture.py` has been run: a request whose (path, params) was captured replays the
real payload, and everything else falls back to the documented example. That is the
whole point of the loop — pay for a response once, then develop against it forever.

Standard library only — no pip install.

    python3 mock_server.py --port 8787 --credits 1000
    curl -H "Authorization: dev-key" http://localhost:8787/v2/subsectors/

Point your app at http://localhost:8787 instead of https://api.sectors.app and
develop all day for zero credits.
"""
import argparse
import json
import os
import random
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
RECORDED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recorded")


class Recordings:
    """Real responses captured by capture.py, keyed by (path, params).

    A recording is preferred over a spec example whenever one exists: it is the
    actual payload the live API returned, so parsers built against it cannot be
    surprised later by a field the documentation omitted.
    """

    def __init__(self, recorded_dir: str):
        self.dir = recorded_dir
        self.by_path = {}
        self.partial = []
        manifest_path = os.path.join(recorded_dir, "_manifest.json")
        if not os.path.exists(manifest_path):
            return
        for key, meta in json.load(open(manifest_path)).items():
            if meta.get("status") != 200:
                continue
            # A sweep that stopped partway is written with status 200 and
            # `incomplete: true`. Replaying it as a complete response would serve a
            # fraction of the universe as if it were all of it -- the single most
            # misleading thing this server could do, because it looks authoritative.
            if meta.get("incomplete"):
                self.partial.append((meta["path"], meta.get("pages_fetched"),
                                     meta.get("pages_expected")))
                continue
            self.by_path.setdefault(meta["path"], []).append((key, meta.get("params") or {}))

    def __len__(self):
        return sum(len(v) for v in self.by_path.values())

    def lookup(self, path: str, query: dict):
        """Exact param match only.

        Returns (payload, exact) so the handler can tell the caller which request the
        body actually answers. An earlier version fell back to `candidates[0]` -- any
        recording for the same path, whatever its parameters -- so
        `?sections=financials` silently replayed a `?sections=overview` capture and
        labelled it `X-Mock-Source: recording`. That is worse than falling back to the
        spec example: it looks like observed truth while answering a different
        question. Params must match; otherwise the caller falls back to the fixture.
        """
        candidates = self.by_path.get(path)
        if not candidates:
            return None
        flat = {k: v[0] for k, v in query.items()}
        for key, params in candidates:
            if {str(k): str(v) for k, v in params.items()} == {str(k): str(v) for k, v in flat.items()}:
                return self._load(key)
        return None

    def _load(self, key):
        try:
            return json.load(open(os.path.join(self.dir, key + ".json")))
        except (OSError, ValueError):
            # OSError: recording gone. ValueError (JSONDecodeError): recording
            # truncated by a crash mid-write. Either way, fall back to the spec
            # example rather than killing the request with a 500-shaped connection
            # drop -- a corrupt file in recorded/ must not take the server down.
            return None


class Catalog:
    """Maps request paths onto fixtures, honouring OpenAPI path templates."""

    def __init__(self, fixtures_dir: str):
        self.fixtures_dir = fixtures_dir
        with open(os.path.join(fixtures_dir, "_index.json")) as fh:
            self.index = json.load(fh)
        self.routes = []
        for template, meta in self.index.items():
            pattern = re.escape(template)
            pattern = re.sub(r"\\\{(\w+)\\\}", r"(?P<\1>[^/]+)", pattern)
            self.routes.append((re.compile("^" + pattern + "$"), template, meta))
        # Longest template first so /v2/company/report/{symbol}/ wins over
        # /v2/company/report/ when a symbol is actually present.
        self.routes.sort(key=lambda r: len(r[1]), reverse=True)

    def match(self, path: str):
        if not path.endswith("/"):
            path += "/"
        for regex, template, meta in self.routes:
            m = regex.match(path)
            if m:
                return template, meta, m.groupdict()
        return None, None, None

    def payload(self, meta: dict):
        with open(os.path.join(self.fixtures_dir, meta["fixture"])) as fh:
            return json.load(fh)


def validate(meta: dict, query: dict):
    """Return an error string when a query parameter is invalid, else None.

    The real API answers a bad parameter with a 400, and **400s are free** -- that is
    one of the few billing facts the docs state outright. A mock that instead bills a
    typo teaches the wrong lesson and, worse, mis-states the budget. Three concrete
    failures this closes, all found by fuzzing the server rather than reading it:

      * `?n_quarters=abc` raised ValueError inside cost_for and dropped the connection
        with no HTTP response at all.
      * `?n_quarters=-5` was charged as -5 credits, which *increased* the balance:
        five such calls moved the meter from 51 spent to -449 spent. The mock's one
        job is a truthful meter.
      * `?sections=,,,` counted four empty strings and charged four credits.
    """
    for spec in meta.get("parameters") or []:
        if spec.get("in") != "query":
            continue
        name = spec.get("name")
        if name not in query:
            continue
        raw = query[name][0]
        enum = spec.get("enum")
        if spec.get("type") == "array":
            if raw == "":
                continue                      # empty means "unset" -> defaults apply
            values = raw.split(",")
            if any(v.strip() == "" for v in values):
                return f"Invalid value for `{name}`: empty item in list."
            if enum:
                bad = [v for v in values if v not in enum]
                if bad:
                    return (f"Invalid value(s) for `{name}`: {', '.join(bad)}. "
                            f"Valid values: {', '.join(enum)}.")
            continue
        if enum and raw not in enum:
            return (f"Invalid value for `{name}`: {raw}. "
                    f"Valid values: {', '.join(map(str, enum))}.")
        if spec.get("type") in ("integer", "number"):
            if raw == "":
                continue
            try:
                number = float(raw) if spec["type"] == "number" else int(raw)
            except (TypeError, ValueError):
                return f"Invalid value for `{name}`: {raw} is not a {spec['type']}."
            low, high = spec.get("minimum"), spec.get("maximum")
            if low is not None and number < low:
                return f"`{name}` must be >= {low} (got {raw})."
            if high is not None and number > high:
                return f"`{name}` must be <= {high} (got {raw})."
        if spec.get("type") == "boolean" and raw.lower() not in ("true", "false", "1", "0"):
            return f"Invalid value for `{name}`: {raw} is not a boolean."
    return None


class CreditMeter:
    """Charges the documented cost per call; refuses once the budget is spent."""

    def __init__(self, budget: int):
        self.remaining = budget
        self.spent = 0
        self.calls = 0
        self.by_endpoint = {}
        self.lock = threading.Lock()

    @staticmethod
    def cost_for(meta: dict, query: dict) -> int:
        text = (meta.get("credit_cost") or "").lower()
        if "natural-language" in text or "?q=" in text:
            pass  # handled by the caller for the screener
        if "per requested section" in text:
            sections = query.get("sections", [None])[0]
            if sections:
                return len(sections.split(","))
            # The default section count differs per endpoint: 8 for the IDX
            # company report, 6 for the subsector report, 4 for SGX and KLSE.
            return meta.get("credit_default_items") or 8
        if "per requested classification × period" in text:
            classifications = query.get("classifications", [None])[0]
            periods = query.get("periods", [None])[0]
            n_class = (len(classifications.split(","))
                       if classifications else meta.get("credit_default_items") or 2)
            n_period = len(periods.split(",")) if periods else 5
            return n_class * n_period
        if "per requested classification" in text:
            classifications = query.get("classifications", [None])[0]
            if classifications:
                return len(classifications.split(","))
            return meta.get("credit_default_items") or 5
        if "per quarter returned" in text:
            return int(query.get("n_quarters", ["1"])[0] or 1)
        if text.startswith("2 api credits"):
            return 2
        if text.startswith("3 api credits"):
            return 3
        return 1

    def charge(self, template: str, amount: int):
        with self.lock:
            if amount > self.remaining:
                return False
            self.remaining -= amount
            self.spent += amount
            self.calls += 1
            self.by_endpoint[template] = self.by_endpoint.get(template, 0) + amount
            return True

    def report(self) -> dict:
        with self.lock:
            return {
                "calls": self.calls,
                "credits_spent": self.spent,
                "credits_remaining": self.remaining,
                "by_endpoint": dict(sorted(self.by_endpoint.items(), key=lambda kv: -kv[1])),
            }


class Handler(BaseHTTPRequestHandler):
    catalog: Catalog
    recordings: "Recordings"
    meter: CreditMeter
    options: argparse.Namespace

    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        if self.options.verbose:
            super().log_message(fmt, *args)

    def _send(self, status: int, body, extra_headers: dict = None):
        raw = json.dumps(body, ensure_ascii=False, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        for key, value in (extra_headers or {}).items():
            self.send_header(key, str(value))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        path, query = parsed.path, parse_qs(parsed.query)

        if path == "/__usage":
            return self._send(200, self.meter.report())
        if path == "/__health":
            return self._send(200, {"status": "ok",
                                    "endpoints": len(self.catalog.index),
                                    "recordings": len(self.recordings)})

        if path.startswith("/v1/"):
            return self._send(410, {
                "error": "Sectors Financial API v1 was discontinued on 2026-05-11.",
                "code": "version_gone",
                "hint": "Use /v2/* — see docs.sectors.app/get-started/v2/migration-guide",
            })

        if self.options.latency_ms:
            time.sleep(self.options.latency_ms / 1000.0)

        if self.options.chaos and random.random() < self.options.chaos:
            # The real API does not bill 429/5xx, and neither do we. Body shapes
            # match the spec: 429 carries error+message, middleware errors carry code.
            if random.random() < 0.5:
                return self._send(429, {
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded. Consider upgrading.",
                }, {"Retry-After": "2"})
            return self._send(503, {
                "error": "Service temporarily unavailable.",
                "code": "service_unavailable",
            }, {"Retry-After": "2"})

        if not self.headers.get("Authorization"):
            return self._send(401, {
                "error": "Missing Authorization header.",
                "code": "subscription_not_active",
            })

        template, meta, path_params = self.catalog.match(path)

        # A well-formed request for a resource that does not exist is billed: the real
        # API charges 1 credit because the lookup ran ("404 = lookup performed"). Without
        # this, the mock can never exercise the one error path that costs money.
        if template and self.options.unknown:
            named = {str(v).upper() for v in (path_params or {}).values()}
            if named & self.options.unknown:
                if not self.meter.charge(template, 1):
                    return self._send(402, {
                        "error": "Not enough API credits remaining.",
                        "code": "insufficient_credits",
                    })
                return self._send(404, {"error": "Company not found."},
                                  {"X-Credits-Charged": "1",
                                   "X-Credits-Remaining": str(self.meter.remaining)})

        if not template:
            # Endpoint-level errors carry a single human-readable `error` string,
            # matching the 400/404 examples in the spec.
            return self._send(404, {
                "error": f"No such endpoint: {path}.",
            })

        # Validate before charging: a 400 is free on the real API, so billing an
        # invalid parameter would over-state every budget rehearsed here.
        problem = validate(meta, query)
        if problem:
            return self._send(400, {"error": problem})

        cost = self.meter.cost_for(meta, query)
        # Screener natural-language mode is billed at 3 credits. Both screeners:
        # /v2/companies/ and /v2/sgx/companies/ document the same 1-vs-3 split.
        if query.get("q") and "structured queries" in (meta.get("credit_cost") or ""):
            cost = 3

        if not self.meter.charge(template, cost):
            return self._send(402, {
                "error": "Not enough API credits remaining.",
                "code": "insufficient_credits",
            })

        # A real recording beats a documented example every time.
        recorded = self.recordings.lookup(path, query) if self.recordings else None
        payload = recorded if recorded is not None else self.catalog.payload(meta)

        return self._send(200, payload, {
            "X-Credits-Charged": cost,
            "X-Credits-Remaining": self.meter.remaining,
            "X-Mock-Endpoint": template,
            "X-Mock-Source": "recording" if recorded is not None else "spec-example",
        })


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--credits", type=int, default=1000, help="simulated credit budget (hackathon grant = 1000)")
    ap.add_argument("--latency-ms", type=int, default=0, help="artificial latency per request")
    ap.add_argument("--chaos", type=float, default=0.0, help="probability (0-1) of a 429/503 per request")
    ap.add_argument("--fixtures", default=FIXTURES_DIR)
    ap.add_argument("--recorded", default=RECORDED_DIR,
                    help="capture.py output; recordings are served in preference to examples")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--unknown", default="ZZZZ,XXXX,NOTREAL",
                    help="comma-separated path values treated as non-existent resources: "
                         "they return 404 AND consume 1 credit, like the real API")
    options = ap.parse_args()
    options.unknown = {v.strip().upper() for v in options.unknown.split(",") if v.strip()}

    Handler.catalog = Catalog(options.fixtures)
    Handler.recordings = Recordings(options.recorded)
    Handler.meter = CreditMeter(options.credits)
    Handler.options = options

    server = ThreadingHTTPServer((options.host, options.port), Handler)
    print(f"Sectors mock API on http://{options.host}:{options.port}")
    print(f"  {len(Handler.catalog.index)} endpoints · {options.credits} simulated credits")
    print(f"  {len(Handler.recordings)} real recordings replayed (rest fall back to spec examples)")
    for path, got, want in Handler.recordings.partial:
        print(f"  ! {path} is an INCOMPLETE capture ({got}/{want} pages) — not replayed; "
              f"re-run capture.py to finish the sweep")
    print(f"  usage report: GET /__usage")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n" + json.dumps(Handler.meter.report(), indent=2))


if __name__ == "__main__":
    main()
