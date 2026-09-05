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
            # Probe recordings are not GET-200s of the endpoint: a `POST` 405, an
            # `OPTIONS` body, a no-auth 403, a no-trailing-slash duplicate. Replaying one
            # of them as if it were the endpoint's answer is how `/v2/subsectors/` briefly
            # started returning a 199-byte OPTIONS body.
            if meta.get("method", "GET") != "GET" or meta.get("no_auth"):
                continue
            if any(key.endswith(suffix) or f"__{marker}__" in key
                   for suffix, marker in (("__options", "options"), ("__post", "post"),
                                          ("__put", "put"), ("__patch", "patch"),
                                          ("__delete", "delete"), ("__noauth", "noauth"),
                                          ("__noslash", "noslash"))):
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

    def slice(self, path: str, query: dict):
        """Serve a page out of a merged universe sweep.

        `capture.py` walks all 32 pages of `/v2/close/` and stores one merged payload, so
        an exact-parameter match only ever answers the first request. Any other
        `?limit=/?offset=` fell through to the single-row spec example — which is how a
        pagination bug survives development and appears on demo day. Slicing the merged
        recording gives real rows, a truthful `pagination` envelope, and a `has_next` that
        actually goes false at the end of the universe.

        Returns None unless a merged recording exists for this path, so nothing else
        changes behaviour.
        """
        for key, _params in self.by_path.get(path, []):
            payload = self._load(key)
            if not isinstance(payload, dict):
                continue
            page = payload.get("pagination") or {}
            if not page.get("merged"):
                continue
            rows = payload.get("results")
            if not isinstance(rows, list):
                continue
            try:
                limit = int(query.get("limit", [page.get("limit") or 30])[0])
                offset = int(query.get("offset", [0])[0])
            except (TypeError, ValueError):
                return None
            limit = max(1, min(limit, len(rows) or 1))
            offset = max(0, offset)
            window = rows[offset:offset + limit]
            return {
                "results": window,
                "pagination": {
                    "total_count": page.get("total_count", len(rows)),
                    "showing": len(window),
                    "limit": limit,
                    "offset": offset,
                    "has_next": offset + limit < len(rows),
                    "has_previous": offset > 0,
                    "next_offset": offset + limit if offset + limit < len(rows) else None,
                    "previous_offset": max(0, offset - limit) if offset > 0 else None,
                },
            }
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


class Universe:
    """Which identifiers actually exist, learned from the recordings.

    Before this existed the mock answered `/v2/company/report/ZZQQ/` with BBCA's fixture
    and a 200. The live API answers 404 and **bills a credit for it** — the single most
    expensive difference between the two, because a client that never sees a 404 in
    development is a client with no 404 handling on demo day.

    Only universes captured in full are enforced. `/v2/close/` and `/v2/free-float/` were
    swept to the last page, so an IDX symbol missing from them is genuinely unlisted.
    `?has_financials=true` returned 9 of 9, so the mining detail endpoints are complete
    too. Everything else (mining companies at large, SGX, KLSE) was sampled, not swept,
    and is deliberately NOT enforced: a partial universe would 404 valid symbols, which
    is a worse lie than the one being fixed.
    """

    # recording slug -> (jsonpath-ish field, universe name)
    COMPLETE_SOURCES = {
        "v2_close__limit-30": "idx_symbol",
        "v2_free-float": "idx_symbol",
        "v2_companies_quarterly-financial-dates__limit-30": "idx_symbol",
        "v2_mining_companies__has_financials-true_limit-20": "mining_detail_slug",
    }

    # endpoints whose path parameter is checked, and against which universe
    ENFORCED = {
        "/v2/company/report/{symbol}/": "idx_symbol",
        "/v2/daily/{symbol}/": "idx_symbol",
        "/v2/foreign-flow/{symbol}/": "idx_symbol",
        "/v2/financials/quarterly/{symbol}/": "idx_symbol",
        "/v2/company/get-segments/{symbol}/": "idx_symbol",
        "/v2/company/corporate-actions/{symbol}/": "idx_symbol",
        "/v2/company/shareholders-composition/{symbol}/": "idx_symbol",
        "/v2/company/get_quarterly_financial_dates/{symbol}/": "idx_symbol",
        "/v2/broker-summary/{symbol}/": "idx_symbol",
        "/v2/broker-summary/{symbol}/top/": "idx_symbol",
        # Only `financials` is enforced. The `has_financials=true` filter is named for
        # exactly that endpoint, and the live capture confirms it both ways: two slugs
        # outside the nine 404, one inside answers. `performance` and
        # `sales-destination` were NOT the same universe live —
        # `/v2/mining/companies/performance/pt-adaro-indonesia/` returned 200 despite the
        # slug being outside the nine — so enforcing them here would invent 404s.
        "/v2/mining/companies/financials/{slug}/": "mining_detail_slug",
    }

    # The 17 index codes the endpoint's own description lists. `sti` is among them and was
    # confirmed live on 2026-09-06 (200); `klse`, a candidate 18th found in an ingestion
    # repo, is NOT — live answers a free 400. The spec types `index_code` as a bare string,
    # so nothing else in this server would have caught either case.
    INDEX_CODES = {"ftse", "idx30", "idxbumn20", "idxesgl", "idxg30", "idxhidiv20", "idxq30",
                   "idxv30", "ihsg", "jii70", "kompas100", "lq45", "sminfra18", "srikehati",
                   "sti", "economic30", "idxvesta28"}

    # The 404 body each family returns, verbatim from the live API on 2026-09-06.
    MESSAGES = {
        "idx_symbol": "Given stock symbol does not exist for this data.",
        "mining_detail_slug": "Company not found or no financial data available.",
    }

    def __init__(self, recorded_dir: str):
        self.sets = {}
        for slug, name in self.COMPLETE_SOURCES.items():
            path = os.path.join(recorded_dir, slug + ".json")
            if not os.path.exists(path):
                continue
            try:
                with open(path) as fh:
                    payload = json.load(fh)
            except (OSError, ValueError):
                continue
            rows = payload.get("results", payload) if isinstance(payload, dict) else payload
            if not isinstance(rows, list):
                continue
            bucket = self.sets.setdefault(name, set())
            # Take the field the universe is actually keyed by. Mining rows carry BOTH a
            # `symbol` and a `slug`, and reading the wrong one builds a set of tickers that
            # no slug can ever match — every mining detail call then 404s.
            field = "slug" if name.endswith("slug") else "symbol"
            for row in rows:
                if not isinstance(row, dict):
                    continue
                value = row.get(field)
                if value:
                    # Live accepts BBCA and BBCA.JK for the same company.
                    bucket.add(str(value).upper())
                    bucket.add(str(value).upper().split(".")[0])

    def __len__(self):
        return sum(len(v) for v in self.sets.values())

    def bad_index_code(self, template: str, path_params: dict):
        """Live answers an unlisted index code with a free 400, not a billed 404."""
        if template != "/v2/index-daily/{index_code}/":
            return None
        code = str((path_params or {}).get("index_code", "")).lower()
        if code and code not in self.INDEX_CODES:
            return "Please provide a valid index code."
        return None

    def unknown(self, template: str, path_params: dict):
        """(message, True) when this identifier provably does not exist, else (None, False)."""
        name = self.ENFORCED.get(template)
        if not name or name not in self.sets or not path_params:
            return None, False
        for value in path_params.values():
            if str(value).upper() not in self.sets[name]:
                return self.MESSAGES[name], True
        return None, False


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


# The four spec entries that declare their identifier as a *path* parameter while
# carrying no template in the path. They are duplicates of the templated sibling, and
# the live API answers each with a free 400 — confirmed 2026-09-06.
PHANTOM_ROOTS = {
    "/v2/company/report/": "Please provide a valid stock symbol.",
    "/v2/subsector/report/": "Please provide a valid sector.",
    "/v2/sgx/company/report/": "Please provide a valid SGX symbol.",
    "/v2/klse/company/report/": "Please provide a valid KLSE symbol.",
}


def missing_required(meta: dict, query: dict):
    """The live 400 for an omitted required query parameter, or None.

    `/v2/mining/total-production/` and `/v2/mining/exports/` both bill nothing and refuse
    to answer without their filters. The mock used to serve a fixture instead, which is
    how two calls in plan.json shipped without their required parameters and were only
    caught by spending real credits.
    """
    absent = [p["name"] for p in (meta.get("parameters") or [])
              if p.get("in") == "query" and p.get("required") and p["name"] not in query]
    if not absent:
        return None
    if len(absent) == 1:
        return f"Query parameter '{absent[0]}' is required."
    quoted = " and ".join(f"'{name}'" for name in absent)
    return f"Query parameters {quoted} are required."


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


class RateLimiter:
    """The live limiter, measured on 6 September 2026 and reproduced here.

    **25 billed requests per rolling 30 seconds.** Spacing is irrelevant: 25 calls sent
    back-to-back and 25 sent a second apart both stopped on the 26th. Free responses (a
    400 on a bad parameter) are not counted — 45 in a row produced no 429 — so only
    billable calls consume the budget.

    Off by default: a test suite that fires two hundred requests at the mock should not
    have to wait for a window. Turn it on with --rate-limit when the thing under test is
    the client's own backoff.
    """

    def __init__(self, calls=25, window=30.0):
        self.calls, self.window, self.stamps = calls, window, []
        self.lock = threading.Lock()

    def allow(self):
        with self.lock:
            now = time.time()
            self.stamps = [t for t in self.stamps if now - t < self.window]
            if len(self.stamps) >= self.calls:
                return False
            self.stamps.append(now)
            return True


def free_float_universe(recorded_dir: str, default: int = 961) -> int:
    """How many companies an unfiltered /v2/free-float/ returns, read from the recording."""
    path = os.path.join(recorded_dir, "v2_free-float.json")
    try:
        with open(path) as fh:
            payload = json.load(fh)
    except (OSError, ValueError):
        return default
    rows = payload.get("results", payload) if isinstance(payload, dict) else payload
    return len(rows) if isinstance(rows, list) and rows else default


FREE_FLOAT_UNIVERSE = 961


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
        if "per 100 companies returned" in text:
            # Free float bills by result size, not by query, so the exact charge is only
            # knowable after the rows come back. The portal's usage log settles the
            # unfiltered case at **10** for the ~961-company market — this server had been
            # billing a flat 1, the largest single cost error it contained. A taxonomy
            # filter returns a slice, and every slice we have seen is under 100, so those
            # charge 1. FREE_FLOAT_UNIVERSE is read from the recording at startup.
            if any(k in query for k in ("sector", "sub_sector", "industry", "sub_industry")):
                return 1
            return max(1, -(-FREE_FLOAT_UNIVERSE // 100))
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
    universe: "Universe"
    limiter = None
    meter: CreditMeter
    options: argparse.Namespace

    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        if self.options.verbose:
            super().log_message(fmt, *args)

    def _credit_headers(self, charged):
        """Spend headers, off by default — the live API sends none.

        Confirmed 2026-09-06 across 116 successful live calls: no header matching
        `credit|quota|rate.?limit|usage|balance` is ever returned. A client that reads
        `X-Credits-Charged` gets None in production, so the mock must not hand it a value
        unless the operator asks for one with --credit-headers.
        """
        if not getattr(self.options, "credit_headers", False):
            return {}
        return {"X-Credits-Charged": str(charged),
                "X-Credits-Remaining": str(self.meter.remaining)}

    def _send(self, status: int, body, extra_headers: dict = None):
        raw = json.dumps(body, ensure_ascii=False, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        for key, value in (extra_headers or {}).items():
            self.send_header(key, str(value))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        return self._method_not_allowed("POST")

    def do_PUT(self):
        return self._method_not_allowed("PUT")

    def do_PATCH(self):
        return self._method_not_allowed("PATCH")

    def do_DELETE(self):
        return self._method_not_allowed("DELETE")

    def do_OPTIONS(self):
        # Live answers OPTIONS with 200 — and bills it, which is worth knowing before a
        # browser client fires a CORS preflight before every request.
        return self.do_GET()

    def _method_not_allowed(self, method: str):
        """Live: 405 `{"error": "Method \"POST\" not allowed."}`, free. Captured 2026-09-06.

        The spec declares 70 GET operations and no others; until this was probed, nothing
        said what the API does when asked for one of the others.
        """
        return self._send(405, {"error": f'Method "{method}" not allowed.'})

    def do_GET(self):
        parsed = urlparse(self.path)
        path, query = parsed.path, parse_qs(parsed.query)

        # Live serves /v2/subsectors and /v2/subsectors/ identically (confirmed 2026-09-06),
        # so normalise before anything looks the path up — otherwise a recording keyed on
        # the canonical form is missed and a client that omits the slash silently develops
        # against spec examples.
        if path.startswith("/v2/") and not path.endswith("/"):
            path += "/"

        if path == "/__usage":
            return self._send(200, self.meter.report())
        if path == "/__coverage":
            # Which endpoints answer with real data and which still fall back to a
            # documented example. A team member can see at a glance what is worth
            # capturing next, without reading the manifest.
            recorded_paths = set(self.recordings.by_path) if self.recordings else set()
            covered, uncovered, unreachable = [], [], []
            for template in sorted(self.catalog.index):
                if template in PHANTOM_ROOTS:
                    unreachable.append(template)
                    continue
                pattern = re.sub(r"\{[^}]+\}", "[^/]+", template)
                hit = any(re.match("^" + pattern + "$", p) for p in recorded_paths)
                (covered if hit else uncovered).append(template)
            return self._send(200, {
                "spec_operations": len(self.catalog.index),
                "callable_endpoints": len(covered) + len(uncovered),
                "served_from_recordings": len(covered),
                "served_from_spec_examples": len(uncovered),
                "unreachable_spec_duplicates": unreachable,
                "recordings": len(self.recordings) if self.recordings else 0,
                "covered": covered,
                "uncovered": uncovered,
            })
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

        # Optional, off by default: reproduce the Cloudflare edge block that answers the
        # Python standard library's default agent with 403 "error code: 1010". It is the
        # first thing the live API does to a naive client, it is not billed, and no error
        # body explains it — so it is worth being able to test against on purpose.
        if getattr(self.options, "cloudflare", False):
            agent = self.headers.get("User-Agent", "")
            if agent.startswith("Python-urllib") or agent.startswith("python-requests"):
                return self._send(403, {"error": "error code: 1010\n"})

        if not self.headers.get("Authorization"):
            # Live returns 403, not 401, and the body is this exact sentence — captured
            # 2026-09-06 by omitting the header. The mock used to answer 401 with a
            # `subscription_not_active` code that the API never sends, so any client
            # branching on 401 or on that code was branching on fiction.
            return self._send(403, {
                "error": "Authentication credentials were not provided.",
            })

        # The phantom report roots answer with a free 400 on the live API, whatever
        # parameters are supplied — they are spec duplicates, not endpoints.
        if path in PHANTOM_ROOTS:
            return self._send(400, {"error": PHANTOM_ROOTS[path]})

        template, meta, path_params = self.catalog.match(path)

        # A well-formed request for a resource that does not exist is billed: the real
        # API charges 1 credit because the lookup ran ("404 = lookup performed"). Without
        # this, the mock can never exercise the one error path that costs money.
        if template and self.universe:
            bad_code = self.universe.bad_index_code(template, path_params)
            if bad_code:
                return self._send(400, {"error": bad_code})

        unknown_message, is_unknown = (self.universe.unknown(template, path_params)
                                       if template and self.universe else (None, False))
        if is_unknown:
            if not self.meter.charge(template, 1):
                return self._send(402, {"error": "Not enough API credits remaining.",
                                        "code": "insufficient_credits"})
            return self._send(404, {"error": unknown_message}, self._credit_headers(1))

        if template and self.options.unknown:
            named = {str(v).upper() for v in (path_params or {}).values()}
            if named & self.options.unknown:
                if not self.meter.charge(template, 1):
                    return self._send(402, {
                        "error": "Not enough API credits remaining.",
                        "code": "insufficient_credits",
                    })
                return self._send(404, {"error": "Company not found."},
                                  self._credit_headers(1))

        if not template:
            # An unrouted path gets a different body shape from every other error: no
            # `error` key at all, but `details` plus a `urls` block. Captured live from
            # /v2/does-not-exist/.
            return self._send(404, {
                "details": "The requested endpoint does not exist",
                "urls": {
                    "homepage": "https://sectors.app",
                    "documentation": "https://docs.sectors.app",
                },
            })

        # Validate before charging: a 400 is free on the real API, so billing an
        # invalid parameter would over-state every budget rehearsed here.
        problem = missing_required(meta, query) or validate(meta, query)
        if problem:
            return self._send(400, {"error": problem})

        # Rate limiting happens after validation and before billing, which is where the
        # live API puts it: free 400s sail through a saturated window, billed calls do not.
        if self.limiter is not None and not self.limiter.allow():
            return self._send(429, {"error": "RATE_LIMIT_EXCEEDED",
                                    "message": "Rate limit exceeded. Consider upgrading."})

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
        # A merged universe sweep is 32 pages glued together — 960 rows in one payload.
        # Serving that blob back would answer `?limit=30` with 960 rows and a `showing`
        # that contradicts `limit`, which the live API never does. So slicing wins over an
        # exact parameter match wherever a merged recording exists: same real rows, a
        # truthful envelope, and `has_next` that actually terminates.
        recorded, source = None, "recording"
        if self.recordings:
            recorded = self.recordings.slice(path, query)
            if recorded is not None:
                source = "recording-slice"
            else:
                recorded = self.recordings.lookup(path, query)
        payload = recorded if recorded is not None else self.catalog.payload(meta)

        headers = self._credit_headers(cost)
        headers["X-Mock-Endpoint"] = template
        headers["X-Mock-Source"] = source if recorded is not None else "spec-example"
        return self._send(200, payload, headers)


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
    ap.add_argument("--credit-headers", action="store_true",
                    help="emit X-Credits-Charged / X-Credits-Remaining. OFF by default "
                         "because the live API sends no spend headers at all — turn this "
                         "on only to exercise ledger code, never to model production")
    ap.add_argument("--rate-limit", action="store_true",
                    help="enforce the measured live ceiling — 25 billed requests per "
                         "rolling 30s, free responses uncounted — answering 429 beyond it")
    ap.add_argument("--cloudflare", action="store_true",
                    help="reject Python-urllib / python-requests user agents with the live "
                         "403 \"error code: 1010\", as Cloudflare does in front of the real API")
    ap.add_argument("--no-universe", action="store_true",
                    help="serve a fixture for any identifier instead of 404ing the ones "
                         "the recordings prove do not exist")
    ap.add_argument("--unknown", default="ZZZZ,XXXX,NOTREAL",
                    help="comma-separated path values treated as non-existent resources: "
                         "they return 404 AND consume 1 credit, like the real API")
    options = ap.parse_args()
    options.unknown = {v.strip().upper() for v in options.unknown.split(",") if v.strip()}

    Handler.catalog = Catalog(options.fixtures)
    Handler.recordings = Recordings(options.recorded)
    Handler.universe = None if options.no_universe else Universe(options.recorded)
    Handler.limiter = RateLimiter() if options.rate_limit else None
    global FREE_FLOAT_UNIVERSE
    FREE_FLOAT_UNIVERSE = free_float_universe(options.recorded)
    Handler.meter = CreditMeter(options.credits)
    Handler.options = options

    server = ThreadingHTTPServer((options.host, options.port), Handler)
    print(f"Sectors mock API on http://{options.host}:{options.port}")
    print(f"  {len(Handler.catalog.index)} endpoints · {options.credits} simulated credits")
    print(f"  {len(Handler.recordings)} real recordings replayed (rest fall back to spec examples)")
    if Handler.universe:
        print(f"  {len(Handler.universe)} known identifiers — unknown ones 404 and bill 1, "
              f"as the live API does")
    if not options.credit_headers:
        print("  no spend headers (matches live); --credit-headers to emit them")
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
