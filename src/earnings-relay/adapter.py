#!/usr/bin/env python3
"""
The only module in this product that can open a socket, and it can only reach localhost.

Two modes, and the default opens nothing at all:

  * `direct` — reads through `sources.load()`. No socket, no server, no credit. This is
    what every gate and every test uses, and it is what `./run.sh poll` uses unless it is
    told otherwise.
  * `http` — talks to `research/harness/src/mock_server.py` on 127.0.0.1, for the
    unattended-poll demo where the point is that a real client, with a real retry path,
    is doing the work.

    from adapter import Adapter

    adapter = Adapter(mode="http")               # RefuseLiveAPI unless the host is local
    payload, meta = adapter.fetch_quarterly("ADRO")

`RefuseLiveAPI` is raised when the adapter is CONSTRUCTED, not when a request is made:
this product must be structurally incapable of billing a credit, and a hostname check at
construction is cheaper than trusting discipline. There is no code path here that reaches
the live API host — the only place its name appears in this file is the gate that proves
it is refused — and `relay.check_ledger` fails the suite if the credit ledger ever moves.

Three behaviours copied from the live API rather than from the spec, because the mock
reproduces them and the spec does not:

  * `X-Mock-Source: spec-example` means the answer is the OpenAPI example rather than
    this company's data — a fabricated fact under a real ticker's name. Hard failure
    (`Fabricated`), the same treatment as `src/tunanetra/reader.py:70`.
  * Retry is 3 attempts on 429/5xx/network, exponential backoff **with jitter**, and 4xx
    schema or auth errors are never retried (PRD §15). Retrying into a 429 extends the
    live lockout; against the mock it merely wastes the demo.
  * Cloudflare rejects `Python-urllib` outright on the live API, with a body that says
    nothing about user agents. Irrelevant on localhost, but the browser `User-Agent` is
    set anyway so this file does not become a trap if somebody repoints it.

    python3 adapter.py --self-test           # direct mode, and the live-URL refusal
    python3 adapter.py --self-test --http    # the same, against a running mock
"""
import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import periods
import sources

MOCK_URL = os.environ.get("ER_MOCK_URL", "http://127.0.0.1:8787")

#: Hosts this product is allowed to speak to. Anything else is a live API as far as this
#: file is concerned, whatever it calls itself.
LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1", "0.0.0.0")

#: A browser UA. Cloudflare blocks `Python-urllib` on the live API (CLAUDE.md), and a
#: client that only works by accident is a client that will fail at the wrong moment.
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

#: The mock requires an Authorization header and answers 403 with the live API's exact
#: body when it is missing. The value is irrelevant to the mock; no real key is read,
#: stored or printed anywhere in this product.
MOCK_AUTHORIZATION = "mock-local-no-credit"

MAX_ATTEMPTS = 3
BACKOFF_BASE = 0.4
RETRYABLE_STATUS = (429, 500, 502, 503, 504)

#: `recording` is a payload replayed verbatim; `recording-slice` is that same payload
#: paginated by the mock so a `?limit=` answer is truthful. Both are real. Anything else
#: is not.
TRUSTED_MOCK_SOURCES = ("recording", "recording-slice")


class RefuseLiveAPI(Exception):
    """A base URL that is not localhost.

    The grant is 1,000 credits, non-transferable, with no top-up, and 623 remain. This
    product is a workflow demo built entirely on payloads that were already paid for, so
    a client that *could* reach the live API is a liability with no upside.
    """


class Fabricated(Exception):
    """A payload the mock invented rather than replayed.

    `X-Mock-Source: spec-example` means the OpenAPI example came back under a real
    ticker's name. Treated as a hard failure, not a warning: every downstream number
    would carry a real symbol and a fictional value.
    """


class FetchFailed(Exception):
    """Retries are exhausted, or the failure was never retryable.

    Carries `status` and `retryable` so `relay.py` can tell a transient failure (retry,
    same idempotency key) from a permanent one (a human has to look).
    """

    def __init__(self, message, status=None, retryable=False, attempts=0):
        super().__init__(message)
        self.status = status
        self.retryable = retryable
        self.attempts = attempts


def _host_of(url):
    return (urllib.parse.urlparse(url).hostname or "").lower()


class Adapter:
    """One fetch path per dataset, and the same return shape from both modes."""

    def __init__(self, mode="direct", base_url=MOCK_URL, source="recorded",
                 as_of=None, sleeper=time.sleep, rng=None):
        if mode not in ("direct", "http"):
            raise ValueError(f"unknown adapter mode {mode!r}")
        # Checked in both modes: a `direct` adapter constructed with a live base URL is a
        # mode switch away from spending money.
        host = _host_of(base_url)
        if host not in LOCAL_HOSTS:
            raise RefuseLiveAPI(
                f"{base_url} is not local. This product reads recordings that were "
                f"already paid for; it has no path to the live API and must not grow one.")
        self.mode = mode
        self.base_url = base_url.rstrip("/")
        self.source = source
        self.as_of = as_of or sources.CAPTURE_AS_OF
        self._sleep = sleeper
        self._rng = rng or random.Random(20260910)

    # ------------------------------------------------------------------ HTTP plumbing

    def _get(self, path, query=None):
        """One HTTP GET with the PRD §15 retry policy. Returns `(payload, headers)`."""
        url = self.base_url + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        last = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            request = urllib.request.Request(url, headers={
                "Authorization": MOCK_AUTHORIZATION,
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            })
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    headers = {k.lower(): v for k, v in response.headers.items()}
                    return payload, headers, attempt
            except urllib.error.HTTPError as exc:
                status = exc.code
                # 4xx that is not 429 is a schema or auth problem: the same request will
                # fail the same way forever, so retrying only burns the demo clock.
                if status not in RETRYABLE_STATUS:
                    raise FetchFailed(f"{url}: HTTP {status}", status=status,
                                      retryable=False, attempts=attempt)
                last = FetchFailed(f"{url}: HTTP {status}", status=status,
                                   retryable=True, attempts=attempt)
            except (urllib.error.URLError, TimeoutError, ConnectionError,
                    json.JSONDecodeError) as exc:
                last = FetchFailed(f"{url}: {exc}", status=None, retryable=True,
                                   attempts=attempt)
            if attempt < MAX_ATTEMPTS:
                # Exponential, with jitter. No Retry-After is ever sent by the live API,
                # and retrying into a 429 extends the lockout — so back off, do not hammer.
                self._sleep(BACKOFF_BASE * (2 ** (attempt - 1)) * (1 + self._rng.random()))
        raise last or FetchFailed(f"{url}: no attempt was made", retryable=True,
                                  attempts=MAX_ATTEMPTS)

    @staticmethod
    def _refuse_fabricated(path, headers):
        mock_source = (headers or {}).get("x-mock-source")
        if mock_source and mock_source not in TRUSTED_MOCK_SOURCES:
            raise Fabricated(
                f"{path}: X-Mock-Source: {mock_source} — this is the OpenAPI example, "
                f"not this company's data")

    # ------------------------------------------------------------------------ fetches

    def fetch_trigger(self):
        """The quarterly-financial-dates sweep. `(rows, meta)`; rows are normalized."""
        started = time.time()
        if self.mode == "direct":
            payload = sources.load(self.source, "trigger")
            rows, note = sources.trigger_window(payload, self.source)
            meta = {"endpoint": sources.ENDPOINT["trigger"], "attempts": 1,
                    "source_as_of": self.as_of, "transport": "direct", "note": note,
                    "pages": 1, "fetched_at": self._stamp(started)}
            return rows, meta

        # The mock slices the merged sweep, so this is the one place that pages. It stops
        # at `has_next == false`, and never re-requests a page it already has.
        collected, offset, pages, attempts = [], 0, 0, 0
        while True:
            payload, headers, attempt = self._get(sources.ENDPOINT["trigger"],
                                                  {"limit": 30, "offset": offset})
            self._refuse_fabricated(sources.ENDPOINT["trigger"], headers)
            attempts += attempt
            pages += 1
            collected.extend(sources.rows_of(payload))
            pagination = (payload or {}).get("pagination") or {}
            if not pagination.get("has_next") or pages >= 40:
                break
            offset = pagination.get("next_offset") or (offset + 30)
        rows = sources.trigger_rows({"results": collected}, "recorded")
        meta = {"endpoint": sources.ENDPOINT["trigger"], "attempts": attempts,
                "source_as_of": self.as_of, "transport": "http", "pages": pages,
                "note": f"{len(collected)} baris dalam {pages} halaman dari mock lokal",
                "fetched_at": self._stamp(started)}
        return rows, meta

    def fetch_quarterly(self, symbol):
        """One symbol's quarterly financials. `(rows, meta)`; rows are normalized."""
        started = time.time()
        symbol = sources.bare_symbol(symbol)
        endpoint = sources.ENDPOINT["quarterly"]
        if self.mode == "direct":
            rows = sources.quarterly_rows(self.source, symbol)
            meta = {"endpoint": endpoint.format(symbol=symbol), "attempts": 1,
                    "source_as_of": self.as_of, "transport": "direct",
                    "fetched_at": self._stamp(started)}
            return rows, meta

        payload, headers, attempts = self._get(f"/v2/financials/quarterly/{symbol}/",
                                               {"n_quarters": 4})
        self._refuse_fabricated(endpoint, headers)
        rows = [sources.normalize_quarterly(r, "recorded")
                for r in sources.rows_of(payload)]
        rows = sorted((r for r in rows if r["report_date"]),
                      key=lambda r: r["report_date"])
        meta = {"endpoint": endpoint.format(symbol=symbol), "attempts": attempts,
                "source_as_of": self.as_of, "transport": "http",
                "fetched_at": self._stamp(started)}
        return rows, meta

    def poll_trigger(self, watchlist, cursor=None):
        """ER-FR-02: fetch, then filter to the watchlist and to what is new.

        The filtering is client-side on purpose and not by accident: the mock ignores
        `?since=` entirely, and PRD §10 specifies "filter watchlist setelah fetch" for
        the live API too, because the sweep is billed by the page and not by the row.
        """
        rows, meta = self.fetch_trigger()
        wanted = {sources.bare_symbol(s) for s in watchlist}
        matched = [r for r in rows if r["symbol"] in wanted]
        # One row per symbol, the newest. The live trigger endpoint returns the latest
        # report per issuer and the recorded sweep is exactly that; only the synthetic
        # trigger carries a multi-year history, and treating that history as a stack of
        # new reports would announce 2024's Q4 as news. Divergence 1, reconciled here so
        # both layers behave the same on the way in.
        newest = {}
        for row in matched:
            if row["report_date"] > newest.get(row["symbol"], {}).get("report_date", ""):
                newest[row["symbol"]] = row
        in_watchlist = sorted(newest.values(), key=lambda r: r["symbol"])
        fresh = [r for r in in_watchlist
                 if cursor is None or r["report_date"] > cursor]
        meta = dict(meta)
        meta.update({
            "detected": len(rows),
            "in_watchlist": len(in_watchlist),
            "after_cursor": len(fresh),
            "cursor": cursor,
            "next_cursor": max([r["report_date"] for r in in_watchlist], default=cursor),
        })
        return fresh, meta

    @staticmethod
    def _stamp(started):
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(started))


def usage(base_url=MOCK_URL):
    """The mock's own credit meter, for the run log. Never the live one — there is none."""
    if _host_of(base_url) not in LOCAL_HOSTS:
        raise RefuseLiveAPI(base_url)
    request = urllib.request.Request(base_url.rstrip("/") + "/__usage",
                                     headers={"Authorization": MOCK_AUTHORIZATION,
                                              "User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def mock_is_up(base_url=MOCK_URL):
    try:
        usage(base_url)
        return True
    except Exception:
        return False


# ------------------------------------------------------------------------------ gates


def check_refusal():
    """Every non-local base URL is refused at construction, in both modes."""
    failures = []
    live = ["https://api.sectors.app", "http://api.sectors.app",
            "https://api.sectors.app:8787", "http://sectors.app/v2/"]
    for url in live:
        for mode in ("direct", "http"):
            try:
                Adapter(mode=mode, base_url=url)
            except RefuseLiveAPI:
                continue
            failures.append(f"{mode}: {url} was accepted")
    for url in ("http://127.0.0.1:8787", "http://localhost:9999"):
        Adapter(mode="direct", base_url=url)      # must not raise
    # No live hostname may appear in this file at all outside the refusal test above.
    with open(os.path.abspath(__file__)) as handle:
        body = handle.read()
    marker = "api." + "sectors.app"
    outside_test = body.split("def check_refusal")[0]
    if marker in outside_test:
        failures.append("a live hostname appears in the working code, not just the gate")
    return failures, len(live) * 2 + 3


def check_direct_fetch():
    """Direct mode reads the recordings, normalizes them, and opens no socket."""
    failures = []
    adapter = Adapter(mode="direct")
    rows, meta = adapter.fetch_trigger()
    if len(rows) != 960:
        failures.append(f"the trigger sweep read {len(rows)} rows, expected 960")
    if meta["transport"] != "direct" or meta["attempts"] != 1:
        failures.append("direct mode reported a transport it did not use")
    if not meta["source_as_of"]:
        failures.append("no source_as_of was recorded for the fetch")

    quarterly, qmeta = adapter.fetch_quarterly("ADRO")
    if len(quarterly) != 4:
        failures.append(f"ADRO returned {len(quarterly)} quarters, expected 4")
    if quarterly[-1]["period_key"] != "q1-2026":
        failures.append(f"ADRO's latest quarter is {quarterly[-1]['period_key']}")
    if "ADRO" not in qmeta["endpoint"]:
        failures.append("the fetch did not record which endpoint it read")

    fresh, pmeta = adapter.poll_trigger(["ADRO", "BBCA"], cursor=None)
    if {r["symbol"] for r in fresh} != {"ADRO", "BBCA"}:
        failures.append(f"the watchlist filter returned {[r['symbol'] for r in fresh]}")
    if pmeta["detected"] != 960 or pmeta["in_watchlist"] != 2:
        failures.append(f"poll meta is wrong: {pmeta['detected']}/{pmeta['in_watchlist']}")

    # The cursor is applied after the fetch, and a cursor at today's dates yields nothing.
    none_left, _ = adapter.poll_trigger(["ADRO", "BBCA"], cursor="2026-12-31")
    if none_left:
        failures.append("the cursor did not suppress an already-seen report")
    # A symbol outside the watchlist never reaches the caller.
    if any(r["symbol"] == "TLKM" for r in fresh):
        failures.append("a symbol outside the watchlist was returned")
    return failures, 10


def check_retry_policy():
    """Three attempts on a transient failure, none on a 4xx, and the backoff sleeps."""
    failures = []
    slept = []
    adapter = Adapter(mode="http", sleeper=slept.append, rng=random.Random(1))

    class _Response:
        def __init__(self, status):
            self.code = status

    def failing(status):
        def _get(request, timeout=None):
            raise urllib.error.HTTPError(request.full_url, status, "boom", {}, None)
        return _get

    original = urllib.request.urlopen
    try:
        urllib.request.urlopen = failing(503)
        try:
            adapter._get("/v2/subsectors/")
        except FetchFailed as exc:
            if exc.attempts != MAX_ATTEMPTS:
                failures.append(f"a 503 was attempted {exc.attempts} times, "
                                f"expected {MAX_ATTEMPTS}")
            if not exc.retryable:
                failures.append("a 503 was not marked retryable")
        else:
            failures.append("a 503 did not fail")
        if len(slept) != MAX_ATTEMPTS - 1:
            failures.append(f"{len(slept)} backoffs between {MAX_ATTEMPTS} attempts")
        if slept and not (slept[1] > slept[0]):
            failures.append(f"the backoff is not increasing: {slept}")

        slept.clear()
        urllib.request.urlopen = failing(400)
        try:
            adapter._get("/v2/subsectors/")
        except FetchFailed as exc:
            if exc.attempts != 1 or exc.retryable:
                failures.append(f"a 400 was retried {exc.attempts} times")
        else:
            failures.append("a 400 did not fail")
        if slept:
            failures.append("a 400 slept before giving up")
    finally:
        urllib.request.urlopen = original
    return failures, 6


def check_fabricated():
    """A spec example under a real ticker's name is a hard failure, not a warning."""
    failures = []
    for header in ("spec-example", "synthetic", "made-up"):
        try:
            Adapter._refuse_fabricated("/v2/financials/quarterly/ADRO/",
                                       {"x-mock-source": header})
        except Fabricated:
            continue
        failures.append(f"X-Mock-Source: {header} was accepted")
    for header in TRUSTED_MOCK_SOURCES:
        Adapter._refuse_fabricated("/v2/x/", {"x-mock-source": header})   # must not raise
    Adapter._refuse_fabricated("/v2/x/", {})                              # nor this
    return failures, 3 + len(TRUSTED_MOCK_SOURCES) + 1


def check_http_mode(base_url=MOCK_URL):
    """Against a running mock: real rows, real headers, and the sweep pages to the end."""
    failures = []
    if not mock_is_up(base_url):
        print(f"        mock tidak berjalan di {base_url} — lewati (jalankan "
              f"`./run.sh` atau mock_server.py untuk mengujinya)")
        return failures, 0
    adapter = Adapter(mode="http", base_url=base_url)
    rows, meta = adapter.fetch_trigger()
    if len(rows) < 900:
        failures.append(f"the paged sweep collected {len(rows)} rows")
    if meta["pages"] < 2:
        failures.append("the sweep did not page at all — the mock stopped slicing")

    quarterly, qmeta = adapter.fetch_quarterly("ADRO")
    if len(quarterly) != 4 or quarterly[-1]["period_key"] != "q1-2026":
        failures.append(f"ADRO over HTTP: {[r['period_key'] for r in quarterly]}")
    direct = Adapter(mode="direct").fetch_quarterly("ADRO")[0]
    if [r["revenue"] for r in quarterly] != [r["revenue"] for r in direct]:
        failures.append("HTTP and direct mode disagree about the same symbol")
    print(f"        mock · {len(rows)} baris dalam {meta['pages']} halaman · "
          f"ADRO {len(quarterly)} kuartal · sama dengan mode direct")
    return failures, 4


def self_test(base_url=MOCK_URL, http=False):
    results = [("live-API refusal", *check_refusal()),
               ("direct fetch", *check_direct_fetch()),
               ("retry policy", *check_retry_policy()),
               ("fabricated payloads", *check_fabricated())]
    if http:
        results.append(("http mode", *check_http_mode(base_url)))

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)
    print("\nthis client cannot reach anything but localhost" if not failed
          else f"\n{failed} adapter failure(s)")
    return 1 if failed else 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="adapter.py", description=__doc__.split("\n")[1])
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--http", action="store_true",
                        help="also exercise HTTP mode against a running mock")
    parser.add_argument("--base-url", default=MOCK_URL)
    args = parser.parse_args(argv)
    if not args.self_test:
        parser.print_help()
        return 0
    return self_test(args.base_url, http=args.http)


if __name__ == "__main__":
    raise SystemExit(main())
