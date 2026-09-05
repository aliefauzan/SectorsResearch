#!/usr/bin/env python3
"""
Fetch the Sectors API once, record everything, replay forever.

The grant is 1,000 credits with no top-up, and the thing that burns credits is
*iteration*, not the demo. So: make each live call at most once, write the raw
response to disk, and develop against the recording from then on.

    python3 capture.py --plan plan.json --dry-run          # cost it, call nothing
    python3 capture.py --plan plan.json --tier 0           # helper lists, 5 credits
    python3 capture.py --plan plan.json --tier 0 --tier 1  # + core, ~45 credits
    python3 capture.py --plan plan.json --budget 200       # hard cap
    python3 capture.py --plan plan.json --report           # what has been spent

Safety properties, in order of how much money they save:

  * **Idempotent, but only for calls that actually settled.** A 2xx (payload on disk)
    or a 404 (a credit already paid for the lookup) is skipped on re-run. An unbilled
    failure --- 402, 400, an exhausted 429/5xx retry, a network error --- is *retried*,
    because it cost nothing and the condition is transient.
  * **Hard budget cap.** Refuses to start a call that would push estimated spend
    past --budget. Default 250.
  * **Dry run.** Prints the full plan with per-call and cumulative cost, calls nothing.
  * **Ledger.** Every attempt appends to recorded/_ledger.jsonl with status, the
    estimated cost, and any cost header the API actually returned — so you can
    reconcile the guess against reality after the first run.
  * **Never re-fetches a 404.** A 404 costs a credit; it is recorded as a negative
    result so the same bad symbol is never paid for twice.
  * **Resumable sweeps.** A paginated entry that dies partway keeps the pages it paid
    for, records them as `incomplete`, and is resumed on the next run rather than
    silently counting as done.
  * **Rate limited.** 0.35s between calls, above the 0.3s the docs call mandatory.
  * **Retries only what is free.** 429 and 5xx are not billed, so they back off and
    retry; 4xx do not.

The key is read from SECTORS_API_KEY and never logged or written to disk.

Recordings land in recorded/<slug>.json alongside recorded/_manifest.json, which
mock_server.py picks up automatically and serves in preference to the spec examples.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# One shared loader, so every script on the team reads configuration the same way.
# Precedence: real environment variable > .env at the repository root > default.
from sectors_env import api_key as env_api_key, base_url as env_base_url  # noqa: E402
from sectors_env import budget as env_budget, dotenv_path                 # noqa: E402

DOTENV_PATH = dotenv_path()

# Overridable so the whole harness can be rehearsed against mock_server.py before a
# single live credit is spent. Same switch the drop-in client in README.md uses.
BASE = env_base_url()
HERE = os.path.dirname(os.path.abspath(__file__))
RECORDED = os.path.join(HERE, "recorded")
LEDGER = os.path.join(RECORDED, "_ledger.jsonl")
MANIFEST = os.path.join(RECORDED, "_manifest.json")

USER_AGENT = os.environ.get(
    "SECTORS_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
)

# Measured against the live API on 6 September 2026, not guessed: the limiter allows
# **25 billed requests per rolling 30 seconds**. 0 s and 1.0 s spacing both stopped dead on
# the 25th call; 1.5 s ran 32 calls clean. Free responses (a 400 on a bad parameter) are not
# counted at all — 45 back-to-back produced no 429 — so the budget is spent by billable
# calls only. 1.5 s keeps 20 requests in any window, a 20% margin under the ceiling.
RATE_LIMIT_SLEEP = float(os.environ.get("SECTORS_RATE_LIMIT_SLEEP", "1.5"))
RATE_WINDOW_SECONDS = float(os.environ.get("SECTORS_RATE_WINDOW", "30"))
RATE_WINDOW_CALLS = int(os.environ.get("SECTORS_RATE_CALLS", "25"))


class RateWindow:
    """Self-throttles to the measured ceiling instead of discovering it with a 429.

    A fixed sleep cannot protect a paginated sweep: 32 pages at any spacing tight enough to
    be useful will eventually put 25 calls inside one window. This tracks the actual
    timestamps and waits only when the window is full, so short runs pay nothing for the
    protection and long sweeps slow down exactly as much as they must.

    Retrying into a 429 appears to extend the lockout — the first recovery probe, polling
    every 5 s, stayed blocked for 36 s, while a single probe after the next drain succeeded
    immediately. So the answer to a 429 is to wait out the window, not to poll it.
    """

    def __init__(self, calls=RATE_WINDOW_CALLS, window=RATE_WINDOW_SECONDS):
        self.calls, self.window, self.stamps = calls, window, []

    def release(self):
        """Hand back the most recently reserved slot — the call turned out to be free."""
        if self.stamps:
            self.stamps.pop()

    def wait(self):
        now = time.time()
        self.stamps = [t for t in self.stamps if now - t < self.window]
        if len(self.stamps) >= self.calls:
            sleep_for = self.window - (now - self.stamps[0]) + 0.2
            if sleep_for > 0:
                print(f"  ...rate window full ({self.calls}/{self.window:g}s), "
                      f"waiting {sleep_for:.1f}s")
                time.sleep(sleep_for)
                now = time.time()
                self.stamps = [t for t in self.stamps if now - t < self.window]
        self.stamps.append(time.time())


# Statuses the live API does not bill: a validation failure, an auth failure, a wrong
# method, a rate-limit rejection, a server error. Confirmed against the ledger — every one
# of these rows carries billed_cost 0.
UNBILLED_STATUSES = {400, 401, 403, 405, 429, 500, 502, 503, 504}

RATE_WINDOW = RateWindow()   # docs call 0.3s mandatory beyond ~10 sequential calls
RETRY_STATUSES = {429, 500, 502, 503, 504}   # all free, so retrying costs nothing


def slug(path, params, method="GET"):
    """Stable filename for a (path, params, method) triple.

    The method is only appended for non-GET so every existing recording keeps its name.
    Without it a `POST /v2/subsectors/` probe collides with the recorded GET and is
    skipped as already settled — which is exactly how the first method probe silently did
    nothing. `path.strip("/")` likewise makes `/v2/subsectors` and `/v2/subsectors/` the
    same key, so a trailing-slash probe needs its own marker too.
    """
    base = path.strip("/").replace("/", "_")
    if not path.endswith("/"):
        base += "__noslash"
    if method != "GET":
        base += f"__{method.lower()}"
    if params:
        tail = "_".join(f"{k}-{str(v)[:24]}" for k, v in sorted(params.items()))
        base = f"{base}__{tail}"
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", base)[:180]


def load_manifest():
    if os.path.exists(MANIFEST):
        return json.load(open(MANIFEST))
    return {}


def save_manifest(manifest):
    os.makedirs(RECORDED, exist_ok=True)
    json.dump(manifest, open(MANIFEST, "w"), indent=2, sort_keys=True)


def log(entry):
    os.makedirs(RECORDED, exist_ok=True)
    with open(LEDGER, "a") as fh:
        fh.write(json.dumps(entry) + "\n")


def spent_so_far():
    """Sum of estimated cost across every billed attempt in the ledger."""
    if not os.path.exists(LEDGER):
        return 0
    total = 0
    for line in open(LEDGER):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get("billed"):
            # `billed_cost` is what the call actually cost (a partial sweep bills only
            # the pages that returned). Older ledger lines only carry `est_cost`.
            total += entry.get("billed_cost", entry.get("est_cost", 0))
    return total


def is_settled(entry: dict) -> bool:
    """True when a manifest entry represents a call that must never be repeated.

    Only two outcomes are settled: a 2xx (we have the payload) and a 404 (we paid a
    credit for the lookup, and the answer will not change). Everything else --- 402
    insufficient credits, 400, a 429/5xx that outlived its retries, a network failure
    recorded as status 0 --- cost nothing and is a transient condition, so re-running
    the plan must retry it rather than treat it as done. An earlier version skipped on
    the mere presence of a manifest key, which meant one connection blip permanently
    dropped a call from the plan.
    """
    status = entry.get("status")
    if not isinstance(status, int):
        return False
    if 200 <= status < 300:
        # A partial sweep that stopped on a *billed* 404 is settled even though it is
        # incomplete: resuming it re-issues the same 404 and pays for it again, every
        # run, forever. "Never pay for the same 404 twice" has to hold inside a sweep
        # as well as outside one.
        if entry.get("incomplete"):
            return entry.get("stopped_on") == 404
        return True
    return status == 404


def has_next(payload) -> bool:
    """True when a `{results, pagination}` envelope reports another page."""
    if isinstance(payload, dict):
        return bool((payload.get("pagination") or {}).get("has_next"))
    return False


def merge_pages(pages: list):
    """Concatenate the `results` of a paginated sweep into one payload."""
    if not isinstance(pages[0], dict) or "results" not in pages[0]:
        return [row for page in pages for row in (page if isinstance(page, list) else [page])]
    merged = dict(pages[0])
    merged["results"] = [row for page in pages for row in (page.get("results") or [])]
    # `has_next` / `next_offset` come from the LAST page (they describe where the sweep
    # stopped), but `offset`, `previous_offset` and `limit` must describe the MERGED
    # payload, not that final page: copying the last page's envelope wholesale yields
    # `offset: 900` in front of rows that start at 0, and a consumer that resumes from
    # `previous_offset` re-buys pages it already holds.
    last = dict(pages[-1].get("pagination") or {})
    merged["pagination"] = {
        **last,
        "offset": (pages[0].get("pagination") or {}).get("offset", 0),
        "previous_offset": None,
        "showing": len(merged["results"]),
        "pages_fetched": len(pages),
        "merged": True,
    }
    return merged


def fetch(path, params, api_key, retries=3, base_url=BASE, method="GET", send_auth=True):
    """One request. Returns (status, payload, headers).

    `method` exists only so the probe plan can ask whether the API answers anything but
    GET — the spec declares 70 GET operations and no others, and that claim had never been
    tested against the running service.
    """
    url = f"{base_url}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {
        # Cloudflare fronts api.sectors.app and answers the stdlib's default
        # "Python-urllib/3.x" agent with 403 "error code: 1010" — an edge block, not an
        # auth failure, and unbilled. A normal browser agent is accepted.
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if send_auth:
        headers["Authorization"] = api_key
    request = urllib.request.Request(url, method=method, headers=headers)

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read().decode("utf-8", "replace")
                return response.status, json.loads(body), dict(response.headers)
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")
            try:
                payload = json.loads(body)
            except ValueError:
                payload = {"error": body[:400]}
            # Unbilled outcomes do not spend the live rate budget, so give the reserved
            # slot back rather than throttling the next call for nothing.
            if err.code in UNBILLED_STATUSES:
                RATE_WINDOW.release()
            if err.code in RETRY_STATUSES and attempt < retries - 1:
                # Free to retry — but a 429 answered by an immediate retry stays blocked;
                # the live probe recovered in 36 s while polling every 5 s, and instantly
                # when left alone. Wait out the window instead of hammering it.
                time.sleep(max(2 ** attempt + 1, RATE_WINDOW_SECONDS if err.code == 429 else 0))
                RATE_WINDOW.wait()
                continue
            return err.code, payload, dict(err.headers or {})
        except Exception as err:                      # network-level failure
            if attempt < retries - 1:
                time.sleep(2 ** attempt + 1)
                continue
            return 0, {"error": f"{type(err).__name__}: {err}"}, {}
    return 0, {"error": "exhausted retries"}, {}


def unrouted_404(payload):
    """True when a 404 means "no such endpoint" rather than "no such resource".

    Live shapes, captured 2026-09-06:
        routed, resource missing -> {"error": "Given stock symbol does not exist ..."}   billed 1
        unrouted path            -> {"details": "The requested endpoint does not exist",
                                     "urls": {...}}                                     free
    """
    return isinstance(payload, dict) and "details" in payload and "error" not in payload


def cost_headers(headers):
    """Pull whatever the API reports about spend, under any plausible name.

    The OpenAPI spec documents no spend headers. This records anything that looks
    like one so the first real run tells us what they are actually called.
    """
    found = {}
    for key, value in headers.items():
        if re.search(r"credit|quota|rate.?limit|usage|balance", key, re.I):
            found[key] = value
    return found


def run(plan, tiers, budget, dry_run, api_key, only, base_url=BASE):
    manifest = load_manifest()
    already = spent_so_far()
    calls = [c for c in plan["calls"] if (not tiers or c.get("tier") in tiers)]
    if only:
        calls = [c for c in calls if only in c["path"]]

    print(f"plan: {plan.get('name','(unnamed)')}")
    if DOTENV_PATH:
        print(f"env:  {DOTENV_PATH}")
    print(f"base: {base_url}")
    print(f"key:  {'set' if api_key else 'MISSING'}"
          f"   (never logged, never written to disk)")
    print(f"calls selected: {len(calls)}   budget: {budget}   already spent (ledger): {already}\n")

    projected = already
    todo = []
    for call in calls:
        key = slug(call["path"], call.get("params"), call.get("method", "GET"))
        if call.get("no_auth"):
            key += "__noauth"
        if key in manifest and is_settled(manifest[key]):
            print(f"  SKIP  {call['path']:52} (recorded, {manifest[key]['status']})")
            continue
        if key in manifest:
            print(f"  RETRY {call['path']:52} (unbilled {manifest[key]['status']}, "
                  f"retrying)")
        projected += call["est_cost"]
        todo.append((call, key))
        flag = "" if projected <= budget else "  << OVER BUDGET"
        print(f"  CALL  {call['path']:52} est {call['est_cost']:>3}  cum {projected:>4}{flag}")

    print(f"\nto fetch: {len(todo)} calls, estimated {projected - already} credits, "
          f"projected total {projected}")

    if dry_run:
        print("\ndry run — nothing was called.")
        return
    if not todo:
        print("\nnothing to do; every selected call is already recorded.")
        return
    if not api_key:
        sys.exit(
            "SECTORS_API_KEY is not set — refusing to run.\n"
            "Copy .env.example to .env at the repository root, put the team key in it, "
            "and re-run. A shell export still works and takes precedence."
        )

    os.makedirs(RECORDED, exist_ok=True)
    running = already
    for call, key in todo:
        if running + call["est_cost"] > budget:
            print(f"\nSTOP: next call would exceed budget ({running} + "
                  f"{call['est_cost']} > {budget}). Raise --budget to continue.")
            break

        # A plan entry may cover a paginated sweep ("pages": 32). Walk the offsets
        # so the recording actually contains the whole universe the entry budgets
        # for; a single call would record one page while billing for all of them.
        pages = int(call.get("pages") or 1)
        page_size = int((call.get("params") or {}).get("limit") or 0)
        if pages > 1 and page_size <= 0:
            print(f"  SKIP  {call['path']:52} (pages={pages} but no `limit` in params; "
                  f"every page would repeat offset 0)")
            continue
        # Resume a sweep that died partway: the pages already on disk were paid for
        # once, so start at the first page we do not have rather than re-buying them.
        collected = []
        prior = manifest.get(key) or {}
        start_page = 0
        if prior.get("incomplete") and prior.get("pages_fetched"):
            try:
                kept = json.load(open(os.path.join(RECORDED, key + ".json")))
                collected = [kept]
                start_page = int(prior["pages_fetched"])
                print(f"  RESUME{call['path']:52} from page {start_page}/{pages}")
            except (OSError, ValueError) as err:
                # OSError: the recording is gone. ValueError (JSONDecodeError): it is
                # truncated or corrupt — a half-written file from a crash during
                # json.dump. Either way the prefix is unusable, so re-buy the sweep
                # from page 0 rather than aborting the whole run: an unhandled decode
                # error here would strand every remaining plan entry behind one bad
                # file, permanently, on every future run.
                print(f"  RESET {call['path']:52} (unusable partial recording: "
                      f"{type(err).__name__}; refetching from page 0)")
                collected, start_page = [], 0
        # A plan edited to fewer pages than are already on disk would otherwise loop
        # forever: range(start_page, pages) is empty, nothing is fetched, and the entry
        # is rewritten as `incomplete` on every run without ever settling.
        if start_page >= pages and collected:
            print(f"  DONE  {call['path']:52} (have {start_page} pages, plan now asks "
                  f"for {pages}; marking settled)")
            payload = merge_pages(collected)
            if isinstance(payload, dict) and isinstance(payload.get("pagination"), dict):
                payload["pagination"]["pages_fetched"] = start_page
            json.dump(payload, open(os.path.join(RECORDED, key + ".json"), "w"),
                      indent=1, ensure_ascii=False)
            manifest[key] = {"path": call["path"], "params": call.get("params"),
                             "method": call.get("method", "GET"),
                             "no_auth": bool(call.get("no_auth")),
                             "status": 200, "tier": call.get("tier"),
                             "pages_fetched": start_page, "pages_expected": pages,
                             "est_cost": call["est_cost"],
                             "billed_cost": prior.get("billed_cost", 0),
                             "fetched_at": time.time(), "cost_headers": {}}
            save_manifest(manifest)
            continue
        status = payload = None
        headers = {}
        for page in range(start_page, pages):
            page_params = dict(call.get("params") or {})
            if pages > 1:
                page_params["offset"] = page * page_size
            status, payload, headers = fetch(call["path"], page_params, api_key,
                                             method=call.get("method", "GET"),
                                             send_auth=not call.get("no_auth"),
                                             base_url=base_url)
            if not (200 <= status < 300):
                break
            collected.append(payload)
            if pages > 1 and not has_next(payload):
                break
            if pages > 1 and page + 1 < pages:
                time.sleep(RATE_LIMIT_SLEEP)
        failure = None if 200 <= (status or 0) < 300 else (status, payload)
        # collected[0] is the resumed prefix when start_page > 0, so it already holds
        # start_page pages that were paid for; the rest are new this session.
        new_pages = len(collected) - (1 if start_page else 0)
        total_pages = start_page + new_pages
        if pages > 1 and collected:
            payload = merge_pages(collected)
            if isinstance(payload, dict) and isinstance(payload.get("pagination"), dict):
                payload["pagination"]["pages_fetched"] = total_pages
        observed = cost_headers(headers)
        # 400s and 429/5xx are not billed; 2xx and 404 are. A sweep that died partway
        # still paid for the pages that came back, so bill those rather than nothing:
        # the whole point of the ledger is that it matches the real meter.
        pages_billed = new_pages if pages > 1 else 0
        if failure is None:
            billed_cost = call["est_cost"] if pages == 1 else max(pages_billed, 1)
        elif failure[0] == 404 and not unrouted_404(payload):
            # A 404 on a real endpoint bills 1 — the lookup ran. A 404 because the *path*
            # routes nowhere bills nothing, and the two are told apart by their body: the
            # unrouted one carries `details`/`urls` and no `error` key. The portal's usage
            # log confirms it — /v2/does-not-exist/ appears there charged 0, while this
            # harness had counted it as 1.
            billed_cost = pages_billed + 1
        else:
            billed_cost = pages_billed
        billed = billed_cost > 0
        running += billed_cost

        entry = {"ts": time.time(), "path": call["path"], "params": call.get("params"),
                 "status": status, "est_cost": call["est_cost"], "billed": billed,
                 "billed_cost": billed_cost, "pages_fetched": pages_billed,
                 "cost_headers": observed}
        # A 4xx body is where the API says which enum value or parameter it wanted, and
        # nothing else records it — the payload file is only written for calls that
        # succeeded. Truncated so a stack-trace-sized body cannot bloat the ledger.
        if status >= 400 and payload is not None:
            entry["error_body"] = json.dumps(payload)[:400]
        log(entry)

        # A sweep that fetched some pages and then failed is written to disk anyway ---
        # those pages were paid for --- but flagged `incomplete` so the next run
        # resumes it instead of treating the entry as settled.
        if failure is not None and collected:
            json.dump(payload, open(os.path.join(RECORDED, key + ".json"), "w"),
                      indent=1, ensure_ascii=False)
            manifest[key] = {"path": call["path"], "params": call.get("params"),
                             "method": call.get("method", "GET"),
                             "no_auth": bool(call.get("no_auth")),
                             "status": 200, "tier": call.get("tier"),
                             "incomplete": True, "pages_fetched": total_pages,
                             "pages_expected": pages, "stopped_on": failure[0],
                             "error": str(failure[1])[:200],
                             "est_cost": call["est_cost"], "billed_cost": billed_cost,
                             "fetched_at": time.time(), "cost_headers": observed}
            save_manifest(manifest)
            verb = ("truncated by a billed 404, settled"
                    if failure[0] == 404 else "kept, will resume")
            print(f"  PART  {call['path']:52} {failure[0]}  {total_pages}/{pages} pages "
                  f"{verb}  spent {running}")
            time.sleep(RATE_LIMIT_SLEEP)
            continue

        if failure is None:
            json.dump(payload, open(os.path.join(RECORDED, key + ".json"), "w"),
                      indent=1, ensure_ascii=False)
            manifest[key] = {"path": call["path"], "params": call.get("params"),
                             "method": call.get("method", "GET"),
                             "no_auth": bool(call.get("no_auth")),
                             "status": status, "tier": call.get("tier"),
                             "est_cost": call["est_cost"], "fetched_at": time.time(),
                             "cost_headers": observed}
            save_manifest(manifest)
            size = len(json.dumps(payload))
            print(f"  OK    {call['path']:52} {status}  {size:>8}B  spent {running}")
        else:
            # Record negative results too, so a bad symbol is never paid for twice.
            manifest[key] = {"path": call["path"], "params": call.get("params"),
                             "method": call.get("method", "GET"),
                             "no_auth": bool(call.get("no_auth")),
                             "status": status, "error": str(payload)[:200],
                             "billed": billed, "fetched_at": time.time()}
            save_manifest(manifest)
            print(f"  FAIL  {call['path']:52} {status}  {str(payload)[:70]}")

        time.sleep(RATE_LIMIT_SLEEP)

    print(f"\ndone. estimated spend this session: {running - already}. "
          f"cumulative: {running}.")
    if any(m.get("cost_headers") for m in manifest.values()):
        print("cost headers observed — reconcile these against est_cost:")
        for m in manifest.values():
            if m.get("cost_headers"):
                print("   ", m["path"], m["cost_headers"])
                break


def report():
    if not os.path.exists(LEDGER):
        sys.exit("no ledger yet — nothing has been captured.")
    rows = [json.loads(line) for line in open(LEDGER) if line.strip()]
    billed = [r for r in rows if r.get("billed")]
    by_path = {}
    def cost_of(r):
        return r.get("billed_cost", r.get("est_cost", 0))
    for r in billed:
        by_path[r["path"]] = by_path.get(r["path"], 0) + cost_of(r)
    print(f"attempts: {len(rows)}   billed: {len(billed)}   "
          f"estimated credits: {sum(cost_of(r) for r in billed)}")
    print("\nby endpoint:")
    for path, cost in sorted(by_path.items(), key=lambda kv: -kv[1]):
        print(f"  {cost:>5}  {path}")
    statuses = {}
    for r in rows:
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    print("\nstatuses:", statuses)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", default=os.path.join(HERE, "plan.json"))
    ap.add_argument("--tier", type=int, action="append", default=[],
                    help="tier(s) to run; repeatable. Omit for all tiers.")
    ap.add_argument("--budget", type=int, default=env_budget(),
                    help="hard credit cap (default from SECTORS_BUDGET, else 250)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--only", help="substring filter on endpoint path")
    ap.add_argument("--base-url", default=BASE,
                    help="API base URL; point at http://localhost:8787 to rehearse "
                         "the whole run against mock_server.py for zero credits")
    args = ap.parse_args()

    if args.report:
        return report()

    plan = json.load(open(args.plan))
    run(plan, set(args.tier), args.budget, args.dry_run,
        env_api_key(required=False), args.only, args.base_url)


if __name__ == "__main__":
    main()
