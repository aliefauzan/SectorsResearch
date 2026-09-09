"""The only module in `app/` allowed to open a socket.

Everything else in the product is handed data; nothing else fetches it. That is
what makes the whole system testable for zero credits, and it is why this file is
mostly guards rather than transport.

The order of operations is the design:

    1. parameter policy   — refuse calls whose defaults would bill 8 or 10 instead of 1
    2. cache              — `research/harness/recorded/` answers first, always
    3. budget             — a call that would cross the cap raises before the socket opens
    4. rate window        — 25 billed requests per rolling 30s, measured, not guessed
    5. request            — browser User-Agent, raw key, no `Bearer`
    6. ledger             — one append-only line per billed call

Steps 1-3 are pure and run before any network access exists, so every one of them
is testable offline. The grant is 1,000 credits with no top-up; a client that only
warns about overspending is a client that overspends.

    from app.sectors_client import SectorsClient

    client = SectorsClient()
    rows = client.get("/v2/broker-summary/LIFE/top/", {"n_brokers": 10})   # cache hit, free

The key is read through `research/harness/src/sectors_env.py` — never `os.environ`
directly — and is never logged, never written to the ledger, and never included in
a repr or an exception message.
"""
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from app import config
from app.cache import Cache

# The one piece of the research harness the product depends on at runtime: a single
# shared way to read the git-ignored .env, so nobody reimplements key handling.
sys.path.insert(0, config.HARNESS_SRC_DIR)
import sectors_env  # noqa: E402

# Cloudflare fronts api.sectors.app and answers the stdlib's default
# "Python-urllib/3.x" with `403 {"error": "error code: 1010"}` — a body that says
# nothing about user agents and reads like an auth failure. Confirmed live on
# 6 September 2026. A normal browser agent is accepted.
USER_AGENT = os.environ.get(
    "SECTORS_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
)

# Measured live, not published: 25 *billed* requests per rolling ~30 seconds.
# Spacing is not what is counted, and free responses (a 400) do not count at all.
RATE_WINDOW_CALLS = int(os.environ.get("SECTORS_RATE_CALLS", "25"))
RATE_WINDOW_SECONDS = float(os.environ.get("SECTORS_RATE_WINDOW", "30"))
RATE_LIMIT_SLEEP = float(os.environ.get("SECTORS_RATE_LIMIT_SLEEP", "1.5"))

# Statuses the live API does not bill, confirmed against the portal usage log.
UNBILLED_STATUSES = {400, 401, 403, 405, 429, 500, 502, 503, 504}
RETRY_STATUSES = {429, 500, 502, 503, 504}


# --- errors -----------------------------------------------------------------
class SectorsError(Exception):
    """Base class, so a caller can catch every failure this module raises."""


class ParameterPolicyError(SectorsError):
    """A call was refused because a per-item parameter was left to default."""


class BudgetExceededError(SectorsError):
    """The call would have pushed cumulative spend past the hard cap."""


class CacheMissError(SectorsError):
    """Not in the recording, and this client was told not to go to the network."""


class NotFoundError(SectorsError):
    """A 404 — the identifier does not exist. Already billed one credit."""


class ApiError(SectorsError):
    """Any other non-2xx. `code` is the machine-readable middleware field."""

    def __init__(self, status, code, message):
        super().__init__(f"{status} {code or ''} {message}".strip())
        self.status, self.code, self.message = status, code, message


# --- parameter policy -------------------------------------------------------
# Four endpoint families bill per requested item and default to *all* items. The
# documented damage: a company report defaults to 8 sections (8 credits), and
# top-changes defaults to 2 classifications x 5 periods (10 credits). Rather than
# guessing a default here — which would just move the mistake into this file — the
# client refuses the call and makes the caller state what it wants.
#
# `/v2/daily/` is a fifth case and a different failure: it bills 1 either way, but
# it silently returns **21 days**, not the 90 the range cap implies. Proven live on
# 9 September 2026 (riset/temuan-kelayakan.md, correction 1). A momentum baseline
# computed over a window four times shorter than intended is wrong without ever
# looking wrong, so `start` and `end` are mandatory.
REQUIRED_PARAMS = (
    ("/report/", ("sections",)),
    ("/companies/top-changes/", ("classifications", "periods")),
    ("/companies/top/", ("classifications",)),
    ("/financials/quarterly/", ("n_quarters",)),
    ("/daily/", ("start", "end")),
)


def _normalised(path):
    """Compare paths with a guaranteed trailing slash — the API accepts both forms."""
    return path if path.endswith("/") else path + "/"


def check_params(path, params):
    """Raise `ParameterPolicyError` if a mandatory-explicit parameter is missing.

    Emptiness counts as missing: `sections=""` bills exactly like no `sections` at
    all, so an empty string must not be a way around the rule.
    """
    path = _normalised(path)
    params = params or {}
    for marker, required in REQUIRED_PARAMS:
        if marker not in path:
            continue
        missing = [name for name in required
                   if params.get(name) is None or str(params[name]).strip() == ""]
        if missing:
            raise ParameterPolicyError(
                f"{path} requires explicit {', '.join(missing)} — "
                f"letting it default is a correctness or credit bug, not a shortcut."
            )


def _count(value):
    """How many items a comma-separated per-item parameter asks for."""
    if isinstance(value, (list, tuple, set)):
        return max(len(value), 1)
    return max(len([p for p in str(value).split(",") if p.strip()]), 1)


def estimate_cost(path, params=None):
    """What this call should cost, from the published per-endpoint rules.

    The live API returns **no spend headers at all** — settled across 116 successful
    calls on 6 September 2026 — so this estimate is the only figure a client can
    compute. The portal usage log is the only independent check.
    """
    path = _normalised(path)
    params = params or {}

    if "/report/" in path:
        return _count(params.get("sections"))
    if path.endswith("/companies/top-changes/"):
        return _count(params.get("classifications")) * _count(params.get("periods"))
    if path.endswith("/companies/top/"):
        return _count(params.get("classifications"))
    if "/financials/quarterly/" in path:
        try:
            return max(int(params.get("n_quarters")), 1)
        except (TypeError, ValueError):
            return 1
    if "/free-float/" in path:
        # 1 credit per 100 companies, rounded up. Without a count parameter the
        # request is for the whole market; the caller can override via `est_cost`.
        try:
            return max(math.ceil(int(params["limit"]) / 100), 1)
        except (KeyError, TypeError, ValueError):
            return 10
    if path.endswith(("/most-traded/", "/brokers/top/")) or (
            path.endswith("/top/") and "/broker-" in path):
        return 2
    if path.endswith(("/companies/", "/sgx/companies/")) and params.get("q"):
        # Natural language costs 3x the identical structured query. Run it once,
        # read `llm_translation` out of the response, hardcode what it produced.
        return 3
    return 1


# --- rate limiting ----------------------------------------------------------
class RateWindow:
    """Self-throttles to the measured ceiling instead of discovering it with a 429.

    A fixed sleep cannot protect a long run: at any spacing tight enough to be
    useful, enough calls eventually land inside one window. This tracks real
    timestamps and waits only when the window is actually full.

    `release()` hands a slot back when the response turns out to be free — free
    responses are not counted by the limiter, so throttling on them would slow the
    product down for nothing.
    """

    def __init__(self, calls=RATE_WINDOW_CALLS, window=RATE_WINDOW_SECONDS, sleep=time.sleep):
        self.calls, self.window, self.stamps, self._sleep = calls, window, [], sleep

    def release(self):
        if self.stamps:
            self.stamps.pop()

    def wait(self):
        now = time.time()
        self.stamps = [t for t in self.stamps if now - t < self.window]
        if len(self.stamps) >= self.calls:
            # No `Retry-After` is ever sent, and retrying into a 429 extends the
            # lockout: polling every 5s stayed blocked for 36s while a single probe
            # after the window drained succeeded immediately. So wait it out.
            sleep_for = self.window - (now - self.stamps[0]) + 0.2
            if sleep_for > 0:
                self._sleep(sleep_for)
                now = time.time()
                self.stamps = [t for t in self.stamps if now - t < self.window]
        self.stamps.append(time.time())


# --- transport --------------------------------------------------------------
def urllib_transport(url, headers, timeout=60):
    """One request. Returns (status, payload, headers) and never raises for HTTP.

    Injectable so every test in this package runs against a stub. The real one is
    plain `urllib` — the product carries no third-party dependency.
    """
    request = urllib.request.Request(url, method="GET", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
            return response.status, _parse(body), dict(response.headers)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        return err.code, _parse(body), dict(err.headers or {})
    except Exception as err:                        # network-level failure
        # The type and message only; a socket error carrying a URL with the key in
        # it is not a thing this API does, but the ledger writes this string.
        return 0, {"error": f"{type(err).__name__}: {err}"}, {}


def _parse(body):
    try:
        return json.loads(body)
    except ValueError:
        return {"error": body[:400]}


def unrouted_404(payload):
    """True when a 404 means "no such endpoint" (free) rather than "no such row" (billed).

    Live shapes, captured 6 September 2026:
        routed, resource missing -> {"error": "Given stock symbol does not exist ..."}
        unrouted path            -> {"details": "...", "urls": {...}}   and no `error`
    """
    return isinstance(payload, dict) and "details" in payload and "error" not in payload


# --- the client -------------------------------------------------------------
class SectorsClient:
    """Cache-first, ledgered, budget-aware access to the Sectors API."""

    def __init__(self, base_url=None, api_key=None, budget=None, cache=None,
                 ledger_path=None, transport=None, allow_network=True,
                 rate_window=None, sleep=time.sleep):
        self.base_url = (base_url or sectors_env.base_url()).rstrip("/")
        # Read through sectors_env, never os.environ. Held privately and never
        # rendered: no repr, no log line, no ledger field ever contains it.
        self.__key = api_key if api_key is not None else sectors_env.api_key(required=False)
        self.budget = sectors_env.budget() if budget is None else int(budget)
        self.cache = cache if cache is not None else Cache()
        self.ledger_path = ledger_path or config.LEDGER_PATH
        self.transport = transport or urllib_transport
        self.allow_network = allow_network
        self.rate_window = rate_window or RateWindow(sleep=sleep)
        self._sleep = sleep
        self.spent = self._spent_so_far()

    # --- ledger ------------------------------------------------------------
    def _spent_so_far(self):
        """Cumulative billed credits already on the ledger. Missing file means zero."""
        total = 0
        try:
            with open(self.ledger_path, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                    except ValueError:
                        continue
                    total += entry.get("billed_cost", 0) or 0
        except OSError:
            return 0
        return total

    def _log(self, entry):
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        with open(self.ledger_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # --- the one public method --------------------------------------------
    def get(self, path, params=None, est_cost=None, allow_network=None):
        """Fetch `path`. Returns the payload; raises rather than overspending.

        Raises `ParameterPolicyError` (before anything else), `CacheMissError`,
        `BudgetExceededError` (before the socket opens), `NotFoundError` or
        `ApiError`.
        """
        params = dict(params or {})
        check_params(path, params)

        hit = self.cache.get(path, params)
        if hit is not None:
            if hit.found:
                return hit.payload
            # A recorded 404 is an answer, not a gap. Re-asking pays again for it.
            raise NotFoundError(
                f"{path} is recorded as 404 — the identifier does not exist. "
                f"That lookup already cost a credit; it is not re-run."
            )

        network = self.allow_network if allow_network is None else allow_network
        if not network:
            raise CacheMissError(
                f"{path} {params} is not in {self.cache.root} and this client is "
                f"offline. Capture it with capture.py, or rehearse against the mock."
            )

        cost = estimate_cost(path, params) if est_cost is None else int(est_cost)
        if self.spent + cost > self.budget:
            # Raised *before* the request, not after: a warning after the fact is a
            # record of money already gone.
            raise BudgetExceededError(
                f"{path} would cost {cost}, cumulative {self.spent + cost} > "
                f"budget {self.budget}. Raise SECTORS_BUDGET deliberately or stop."
            )

        if not self.__key:
            raise SectorsError(
                "SECTORS_API_KEY is not set — refusing to call. Put the team key in "
                "the git-ignored .env at the repository root."
            )

        return self._request(path, params, cost)

    def _request(self, path, params, cost, retries=3):
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            # Raw key. The REST API takes no `Bearer ` prefix; only the MCP server does.
            "Authorization": self.__key,
        }

        status, payload, response_headers = 0, {"error": "not attempted"}, {}
        for attempt in range(retries):
            self.rate_window.wait()
            status, payload, response_headers = self.transport(url, headers)
            if status in UNBILLED_STATUSES:
                self.rate_window.release()
            if status in RETRY_STATUSES and attempt < retries - 1:
                # 429 and 5xx are free, so retrying costs time only. A 429 needs the
                # whole window to drain; a 5xx wants ordinary backoff.
                self._sleep(RATE_WINDOW_SECONDS if status == 429 else 2 ** attempt + 1)
                continue
            break

        billed_cost = self._billed_cost(status, payload, cost, response_headers)
        self.spent += billed_cost
        self._log({
            "ts": time.time(),
            "path": path,
            # `params` is what the product asked for. The key travels in a header and
            # is never a parameter, so nothing secret can reach this line.
            "params": params,
            "status": status,
            "est_cost": cost,
            "billed_cost": billed_cost,
            "cumulative": self.spent,
        })

        if 200 <= status < 300:
            return payload
        if status == 404:
            raise NotFoundError(f"{path}: {self._message(payload)}")
        code, message = self._code(payload), self._message(payload)
        raise ApiError(status, code, message)

    @staticmethod
    def _billed_cost(status, payload, cost, headers):
        """What the call actually cost.

        There are no spend headers on the live API — the header read here exists so
        the mock server keeps this path exercised, and it is never trusted over the
        status rules when absent.
        """
        for name, value in headers.items():
            if name.lower() == "x-credits-charged":
                try:
                    return int(value)
                except (TypeError, ValueError):
                    break
        if 200 <= status < 300:
            return cost
        if status == 404:
            # A routed 404 bills 1 — the database lookup ran. A path that routes
            # nowhere bills nothing, and the bodies are what tell them apart.
            return 0 if unrouted_404(payload) else 1
        return 0

    @staticmethod
    def _code(payload):
        """The machine-readable middleware field. Branch on this, not on prose."""
        if not isinstance(payload, dict):
            return None
        if payload.get("code"):
            return payload["code"]
        # A 429 puts a symbol in `error` and prose in `message`; a 400/404 puts prose
        # in `error` and has no `message`. That difference is the only way to tell.
        return payload.get("error") if payload.get("message") else None

    @staticmethod
    def _message(payload):
        if not isinstance(payload, dict):
            return str(payload)[:200]
        return str(payload.get("message") or payload.get("error") or payload)[:200]

    def __repr__(self):
        # Deliberately says whether a key is present, never what it is.
        return (f"<SectorsClient {self.base_url} budget={self.budget} "
                f"spent={self.spent} key={'set' if self.__key else 'missing'}>")
