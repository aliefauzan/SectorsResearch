#!/usr/bin/env python3
"""
Prove the mock behaves like the API we actually captured — no credits, every run.

Three checks, in order of how much they would cost to get wrong:

  1. **Replay parity.** Every recorded 200 is requested again from the mock with the same
     parameters and the body must come back byte-identical, sourced from the recording
     rather than a spec example.
  2. **Error parity.** Each failure mode observed live on 2026-09-06 — a 404 on an unknown
     identifier, a free 400 on a missing required parameter, the phantom report roots, an
     invalid enum — must produce the same status from the mock, with the same message where
     the live body was captured.
  3. **Header parity.** The live API returns no spend headers. Neither may the mock, unless
     it was started with --credit-headers.

    python3 verify_mock.py                  # starts its own server on a free port
    python3 verify_mock.py --port 8787      # or check one already running

Exit status is 0 only when every check passes, so this can gate a commit.
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RECORDED = os.path.join(HERE, "recorded")

# Observed live, 2026-09-06. Status is what the API returned; `body` is the verbatim error
# string where one was captured. See ../99-raw/live-capture-2026-09-06.md.
LIVE_BEHAVIOUR = [
    ("unknown IDX symbol is a billed 404",
     "/v2/company/report/ZZQQ/", {"sections": "overview"}, 404,
     "Given stock symbol does not exist for this data."),
    ("known IDX symbol answers",
     "/v2/company/report/BBCA/", {"sections": "overview"}, 200, None),
    ("symbol accepted with or without .JK",
     "/v2/daily/BBCA.JK/", None, 200, None),
    ("missing one required query parameter is a free 400",
     "/v2/mining/total-production/", None, 400,
     "Query parameter 'commodity_type' is required."),
    ("missing two required query parameters is a free 400",
     "/v2/mining/exports/", None, 400,
     "Query parameters 'commodity_type' and 'year' are required."),
    ("supplying them answers",
     "/v2/mining/exports/", {"commodity_type": "Coal", "year": 2024}, 200, None),
    ("phantom root: company report",
     "/v2/company/report/", {"symbol": "BBCA"}, 400,
     "Please provide a valid stock symbol."),
    ("phantom root: subsector report",
     "/v2/subsector/report/", {"sub_sector": "banks"}, 400,
     "Please provide a valid sector."),
    ("phantom root: SGX report",
     "/v2/sgx/company/report/", {"symbol": "D05.SI"}, 400,
     "Please provide a valid SGX symbol."),
    ("mining detail 404s for a company with no records",
     "/v2/mining/companies/financials/pt-abm-investama-tbk/", None, 404,
     "Company not found or no financial data available."),
    ("mining detail answers for one of the nine that have them",
     "/v2/mining/companies/financials/pt-adaro-andalan-indonesia-tbk/", None, 200, None),
    ("IDX classification vocabulary is rejected by SGX",
     "/v2/sgx/companies/top/", {"classifications": "top_gainers"}, 400, None),
    ("no Authorization header is a 403, not a 401",
     "/v2/subsectors/", None, 403, "Authentication credentials were not provided."),
    ("an unrouted path 404s with the details/urls body, not an error string",
     "/v2/does-not-exist/", None, 404, None),
    ("an index code outside the documented 17 is a free 400",
     "/v2/index-daily/klse/", None, 400, "Please provide a valid index code."),
    ("sti is a valid index code",
     "/v2/index-daily/sti/", None, 200, None),
    ("a symbol is accepted lowercase",
     "/v2/company/report/bbca/", {"sections": "overview"}, 200, None),
    ("a symbol is accepted with the .JK suffix",
     "/v2/company/report/BBCA.JK/", {"sections": "overview"}, 200, None),
    ("the trailing slash is optional",
     "/v2/subsectors", None, 200, None),
]


def request(base, path, params=None, auth=True):
    url = base + path + ("?" + urllib.parse.urlencode(params) if params else "")
    headers = {"Authorization": "verify-mock"} if auth else {}
    try:
        response = urllib.request.urlopen(urllib.request.Request(url, headers=headers))
        return response.status, json.load(response), dict(response.headers)
    except urllib.error.HTTPError as exc:
        try:
            body = json.load(exc)
        except ValueError:
            body = None
        return exc.code, body, dict(exc.headers)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def check_replay(base):
    manifest_path = os.path.join(RECORDED, "_manifest.json")
    if not os.path.exists(manifest_path):
        return ["no recordings on disk — run capture.py first"], 0
    with open(manifest_path) as fh:
        manifest = json.load(fh)
    failures, checked = [], 0
    probe_markers = ("__options", "__post", "__put", "__patch", "__delete",
                     "__noauth", "__noslash")
    for key, meta in manifest.items():
        if meta.get("status") != 200 or meta.get("incomplete"):
            continue
        # Probe captures are recorded under the same path as the endpoint itself — an
        # OPTIONS body, a no-trailing-slash duplicate. They are evidence, not the
        # endpoint's answer, so they are checked by the behaviour suite, not here.
        if meta.get("method", "GET") != "GET" or meta.get("no_auth"):
            continue
        if any(marker in key for marker in probe_markers):
            continue
        checked += 1
        status, body, headers = request(base, meta["path"], meta.get("params"))
        with open(os.path.join(RECORDED, key + ".json")) as fh:
            disk = json.load(fh)
        source = headers.get("X-Mock-Source")
        merged = isinstance(disk, dict) and (disk.get("pagination") or {}).get("merged")
        if status != 200:
            failures.append(f"{meta['path']}: replay returned {status}")
        elif merged:
            # A merged sweep is served one page at a time, so the body cannot match the
            # 960-row blob on disk — but the rows it does return must be that blob's, in
            # order, and the envelope must be internally consistent.
            if source != "recording-slice":
                failures.append(f"{meta['path']}: merged sweep served as {source}")
            else:
                rows = body.get("results", [])
                page = body.get("pagination", {})
                if rows != disk["results"][:len(rows)]:
                    failures.append(f"{meta['path']}: sliced rows are not the recorded rows")
                elif len(rows) > page.get("limit", 0):
                    failures.append(f"{meta['path']}: returned {len(rows)} rows for "
                                    f"limit={page.get('limit')}")
                elif page.get("total_count") != (disk["pagination"] or {}).get("total_count"):
                    failures.append(f"{meta['path']}: total_count changed under slicing")
        elif source != "recording":
            failures.append(f"{meta['path']}: served a {source}, not the recording")
        elif body != disk:
            failures.append(f"{meta['path']}: replayed body differs from the recording")
    return failures, checked


def check_behaviour(base):
    failures = []
    for label, path, params, want_status, want_body in LIVE_BEHAVIOUR:
        status, body, _ = request(base, path, params, auth=(want_status != 403))
        if status != want_status:
            failures.append(f"{label}: got {status}, live gives {want_status}")
            continue
        if want_body and isinstance(body, dict) and body.get("error") != want_body:
            failures.append(f"{label}: message is {body.get('error')!r}, "
                            f"live says {want_body!r}")
    return failures, len(LIVE_BEHAVIOUR)


def check_methods(base):
    """The spec declares 70 GET operations and nothing else. Live 405s the rest, free."""
    failures = []
    for method in ("POST", "PUT", "DELETE"):
        url = base + "/v2/subsectors/"
        req = urllib.request.Request(url, method=method,
                                     headers={"Authorization": "verify-mock"})
        try:
            urllib.request.urlopen(req)
            failures.append(f"{method} was accepted; live answers 405")
        except urllib.error.HTTPError as exc:
            if exc.code != 405:
                failures.append(f"{method} returned {exc.code}, live answers 405")
            else:
                try:
                    body = json.load(exc)
                except ValueError:
                    body = {}
                want = f'Method "{method}" not allowed.'
                if body.get("error") != want:
                    failures.append(f"{method} message is {body.get('error')!r}, "
                                    f"live says {want!r}")
        except OSError as exc:
            failures.append(f"{method}: {exc}")
    return failures, 3


def check_rate_limit():
    """Start a second server with --rate-limit and confirm it trips exactly where live did.

    Live, 6 September 2026: the 26th billed request in a rolling 30 s window is refused,
    and free 400s are not counted at all.
    """
    port = free_port()
    server = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "mock_server.py"), "--port", str(port),
         "--rate-limit"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(50):
        time.sleep(0.1)
        try:
            # Readiness probe on the FREE path: a billed one would eat a slot out of the
            # very window this check is measuring, and the count would come up one short.
            request(base, "/v2/index-daily/klse/")
            break
        except OSError:
            continue
    failures = []
    try:
        statuses = [request(base, "/v2/subsectors/")[0] for _ in range(28)]
        if 429 not in statuses:
            failures.append("no 429 in 28 billed calls; live refuses the 26th")
        elif statuses.index(429) != 25:
            failures.append(f"first 429 at call {statuses.index(429)}; live refuses at 25")
        free = [request(base, "/v2/index-daily/klse/")[0] for _ in range(5)]
        if any(code == 429 for code in free):
            failures.append("free 400s were rate limited; live does not count them")
    finally:
        server.terminate()
    return failures, 2


def check_headers(base):
    _, _, headers = request(base, "/v2/subsectors/")
    leaked = [k for k in headers if k.lower().startswith("x-credits")]
    if leaked:
        return [f"emits {leaked} — the live API returns no spend headers; "
                f"only --credit-headers should turn these on"], 1
    return [], 1


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int,
                        help="check a server already running on this port instead of "
                             "starting one")
    args = parser.parse_args()

    server = None
    port = args.port
    if port is None:
        port = free_port()
        server = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "mock_server.py"), "--port", str(port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            time.sleep(0.1)
            try:
                request(f"http://127.0.0.1:{port}", "/v2/subsectors/")
                break
            except OSError:
                continue

    base = f"http://127.0.0.1:{port}"
    try:
        results = [("replay parity", *check_replay(base)),
                   ("error parity", *check_behaviour(base)),
                   ("method parity", *check_methods(base)),
                   ("rate-limit parity", *check_rate_limit()),
                   ("header parity", *check_headers(base))]
    finally:
        if server:
            server.terminate()

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:16} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)

    print("\nmock matches the captured API" if not failed
          else f"\n{failed} divergence(s) from the captured API")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
