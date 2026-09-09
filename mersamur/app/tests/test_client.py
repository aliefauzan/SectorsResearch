"""The client's guards, tested without a socket or a credit.

Each test builds its own recorded corpus in a temp directory and injects a stub
transport, so nothing here depends on what `research/harness/recorded/` happens to
contain today — except `test_slug_matches_capture_py`, which is the one place that
*must* compare against the harness, because a drift there silently turns every
cache hit into a paid call.
"""
import json
import os
import sys

import pytest

from app import cache as cache_mod
from app.cache import Cache
from app.sectors_client import (
    ApiError,
    BudgetExceededError,
    CacheMissError,
    NotFoundError,
    ParameterPolicyError,
    RateWindow,
    SectorsClient,
    check_params,
    estimate_cost,
    unrouted_404,
)

FAKE_KEY = "sk_test_do_not_use_9f3c1a7b5e2d4086"


def exploding_transport(url, headers, timeout=60):
    """Any call to this is a bug: the code under test must not reach the network."""
    raise AssertionError(f"network touched: {url}")


def stub_transport(status=200, payload=None, headers=None, record=None):
    def transport(url, request_headers, timeout=60):
        if record is not None:
            record.append((url, request_headers))
        return status, payload if payload is not None else {"ok": True}, headers or {}
    return transport


def build_cache(tmp_path, entries):
    """Write a manifest plus payload files the way capture.py does."""
    manifest = {}
    for path, params, status, payload in entries:
        key = cache_mod.slug(path, params)
        manifest[key] = {"path": path, "params": params, "status": status,
                         "est_cost": 1, "fetched_at": 0, "cost_headers": {}}
        if payload is not None:
            (tmp_path / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return Cache(root=str(tmp_path))


def client(tmp_path, cache, **kwargs):
    kwargs.setdefault("transport", exploding_transport)
    kwargs.setdefault("api_key", FAKE_KEY)
    kwargs.setdefault("budget", 100)
    kwargs.setdefault("base_url", "https://api.sectors.app")
    kwargs.setdefault("ledger_path", str(tmp_path / "credits.jsonl"))
    kwargs.setdefault("sleep", lambda _seconds: None)
    return SectorsClient(cache=cache, **kwargs)


# --- 1. a cached call never touches the network -----------------------------
def test_cached_call_does_not_touch_the_network(tmp_path):
    corpus = build_cache(tmp_path, [
        ("/v2/broker-summary/LIFE/top/", {"n_brokers": 10}, 200,
         {"top_buyers": [{"broker_code": "XL", "buy_idr": 1_000}]}),
    ])
    c = client(tmp_path, corpus)   # transport raises if it is ever called

    payload = c.get("/v2/broker-summary/LIFE/top/", {"n_brokers": 10})

    assert payload["top_buyers"][0]["broker_code"] == "XL"
    assert c.spent == 0
    assert not os.path.exists(c.ledger_path), "a free cache hit must not write a ledger line"


def test_recorded_404_is_not_paid_for_twice(tmp_path):
    """A 404 already cost a credit. Re-asking pays for the same answer again."""
    corpus = build_cache(tmp_path, [("/v2/daily/ZZZZ/", {"start": "2026-08-01",
                                                        "end": "2026-08-31"}, 404, None)])
    c = client(tmp_path, corpus)

    with pytest.raises(NotFoundError):
        c.get("/v2/daily/ZZZZ/", {"start": "2026-08-01", "end": "2026-08-31"})


def test_recorded_400_is_a_miss_not_an_answer(tmp_path):
    """A 400 was free and the condition is transient, so it must not be cached as settled."""
    corpus = build_cache(tmp_path, [("/v2/subsectors/", None, 400, None)])
    c = client(tmp_path, corpus, allow_network=False)

    with pytest.raises(CacheMissError):
        c.get("/v2/subsectors/")


def test_offline_client_refuses_a_miss(tmp_path):
    c = client(tmp_path, build_cache(tmp_path, []), allow_network=False)

    with pytest.raises(CacheMissError):
        c.get("/v2/subsectors/")


def test_slug_matches_capture_py():
    """Cache keys must be byte-identical to the harness's, or every lookup misses.

    A miss is not a visible failure — it is a paid call for data already on disk —
    so this parity is asserted against the harness itself rather than a copy.
    """
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), "..", "research", "harness", "src"))
    import capture   # noqa: E402

    cases = [
        ("/v2/subsectors/", None, "GET"),
        ("/v2/broker-summary/LIFE/top/", {"n_brokers": 10}, "GET"),
        ("/v2/daily/BBCA/", {"start": "2026-06-01", "end": "2026-08-30"}, "GET"),
        ("/v2/subsectors", None, "GET"),
        ("/v2/subsectors/", None, "POST"),
    ]
    for path, params, method in cases:
        assert cache_mod.slug(path, params, method) == capture.slug(path, params, method)


def test_real_recorded_corpus_answers_a_watchlist_call():
    """The corpus the team paid 52 credits for is reachable through this client."""
    from app import config

    real = Cache()
    if not os.path.exists(real.manifest_path):
        pytest.skip("no recorded corpus checked out")
    assert len(real) > 0
    hit = real.get("/v2/broker-summary/LIFE/top/", {"n_brokers": 10})
    assert hit is not None and hit.found
    assert config.RECORDED_DIR.endswith(os.path.join("harness", "recorded"))


# --- 2. the budget raises before the request is sent ------------------------
def test_budget_exceeded_raises_before_the_request(tmp_path):
    sent = []
    c = client(tmp_path, build_cache(tmp_path, []), budget=0,
               transport=stub_transport(record=sent))

    with pytest.raises(BudgetExceededError):
        c.get("/v2/subsectors/")

    assert sent == [], "the budget must be checked before the socket opens"
    assert not os.path.exists(c.ledger_path)


def test_budget_counts_credits_already_on_the_ledger(tmp_path):
    ledger = tmp_path / "credits.jsonl"
    ledger.write_text(json.dumps({"path": "/v2/subsectors/", "status": 200,
                                  "est_cost": 1, "billed_cost": 9}) + "\n", encoding="utf-8")
    sent = []
    c = client(tmp_path, build_cache(tmp_path, []), budget=9,
               ledger_path=str(ledger), transport=stub_transport(record=sent))

    assert c.spent == 9
    with pytest.raises(BudgetExceededError):
        c.get("/v2/subsectors/")
    assert sent == []


def test_a_call_inside_the_budget_goes_through_and_is_ledgered(tmp_path):
    sent = []
    c = client(tmp_path, build_cache(tmp_path, []), budget=2,
               transport=stub_transport(payload={"rows": []}, record=sent))

    assert c.get("/v2/subsectors/") == {"rows": []}
    assert len(sent) == 1
    rows = [json.loads(line) for line in open(c.ledger_path, encoding="utf-8")]
    assert rows[0]["status"] == 200
    assert rows[0]["est_cost"] == 1 and rows[0]["billed_cost"] == 1
    assert c.spent == 1


# --- 3. per-item parameters must be explicit --------------------------------
@pytest.mark.parametrize("path, params", [
    ("/v2/company/report/BBCA/", None),
    ("/v2/company/report/BBCA/", {"sections": ""}),
    ("/v2/subsector/report/banks/", {}),
    ("/v2/financials/quarterly/BBCA/", None),
    ("/v2/financials/quarterly/BBCA/", {"approx": "false"}),
    ("/v2/companies/top-changes/", {"classifications": "top_gainers"}),
    ("/v2/companies/top/", None),
])
def test_defaulted_per_item_parameters_are_refused(path, params, tmp_path):
    c = client(tmp_path, build_cache(tmp_path, []))
    with pytest.raises(ParameterPolicyError):
        c.get(path, params)


@pytest.mark.parametrize("path, params", [
    ("/v2/company/report/BBCA/", {"sections": "overview"}),
    ("/v2/financials/quarterly/BBCA/", {"n_quarters": 4}),
    ("/v2/companies/top-changes/", {"classifications": "top_gainers", "periods": "1d"}),
])
def test_explicit_per_item_parameters_are_accepted(path, params):
    check_params(path, params)   # must not raise


def test_the_policy_runs_before_the_cache_and_the_budget(tmp_path):
    """An 8-credit default is refused even when a payload for it is on disk.

    Otherwise the rule holds in development and evaporates the first time the cache
    is cold — which is the only time it matters.
    """
    corpus = build_cache(tmp_path, [("/v2/company/report/BBCA/", None, 200, {"x": 1})])
    c = client(tmp_path, corpus, budget=0)
    with pytest.raises(ParameterPolicyError):
        c.get("/v2/company/report/BBCA/")


def test_cost_estimates_match_the_published_rules():
    assert estimate_cost("/v2/company/report/BBCA/", {"sections": "overview"}) == 1
    assert estimate_cost("/v2/company/report/BBCA/",
                         {"sections": "overview,financials,dividend"}) == 3
    assert estimate_cost("/v2/companies/top-changes/",
                         {"classifications": "top_gainers,top_losers",
                          "periods": "1d,1w,1m,3m,1y"}) == 10
    assert estimate_cost("/v2/financials/quarterly/BBCA/", {"n_quarters": 8}) == 8
    assert estimate_cost("/v2/companies/", {"q": "bank termurah"}) == 3
    assert estimate_cost("/v2/companies/", {"where": "pe < 10"}) == 1
    assert estimate_cost("/v2/broker-summary/LIFE/top/", {"n_brokers": 10}) == 2
    assert estimate_cost("/v2/subsectors/") == 1


# --- 4. /v2/daily/ must carry start and end ---------------------------------
@pytest.mark.parametrize("params", [
    None,
    {},
    {"start": "2026-06-01"},
    {"end": "2026-08-30"},
    {"start": "", "end": "2026-08-30"},
])
def test_daily_without_an_explicit_window_is_refused(params, tmp_path):
    """Live on 9 September 2026 the default window came back as 21 days, not 90.

    It bills the same either way, so nothing complains — the momentum baseline is
    just computed over a quarter of the intended history.
    """
    c = client(tmp_path, build_cache(tmp_path, []))
    with pytest.raises(ParameterPolicyError):
        c.get("/v2/daily/LIFE/", params)


def test_daily_with_an_explicit_window_is_accepted(tmp_path):
    corpus = build_cache(tmp_path, [
        ("/v2/daily/LIFE/", {"start": "2026-06-01", "end": "2026-08-30"}, 200,
         [{"date": "2026-06-01", "close": 50}]),
    ])
    c = client(tmp_path, corpus)
    rows = c.get("/v2/daily/LIFE/", {"start": "2026-06-01", "end": "2026-08-30"})
    assert rows[0]["close"] == 50


# --- 5. the key never reaches the ledger, a log line, or a repr -------------
def test_the_api_key_never_appears_in_the_ledger_or_output(tmp_path, capsys):
    sent = []
    c = client(tmp_path, build_cache(tmp_path, []), budget=50,
               transport=stub_transport(payload={"ok": True}, record=sent))

    c.get("/v2/subsectors/")
    c.get("/v2/companies/", {"where": "market_cap < 1000"})
    with pytest.raises(NotFoundError):
        SectorsClient(cache=build_cache(tmp_path, []), api_key=FAKE_KEY, budget=50,
                      ledger_path=str(tmp_path / "credits.jsonl"),
                      base_url="https://api.sectors.app",
                      sleep=lambda _s: None,
                      transport=stub_transport(
                          404, {"error": "Given stock symbol does not exist for this data."}),
                      ).get("/v2/daily/ZZZZ/", {"start": "2026-08-01", "end": "2026-08-31"})

    ledger_text = open(c.ledger_path, encoding="utf-8").read()
    assert FAKE_KEY not in ledger_text
    assert "Authorization" not in ledger_text
    assert repr(c) == ("<SectorsClient https://api.sectors.app budget=50 "
                       f"spent={c.spent} key=set>")
    assert FAKE_KEY not in repr(c)

    captured = capsys.readouterr()
    assert FAKE_KEY not in captured.out and FAKE_KEY not in captured.err
    # And it *is* sent, on the header, raw — the REST API takes no `Bearer ` prefix.
    assert sent[0][1]["Authorization"] == FAKE_KEY
    assert not sent[0][1]["Authorization"].startswith("Bearer ")


def test_the_key_is_not_reachable_as_a_public_attribute(tmp_path):
    c = client(tmp_path, build_cache(tmp_path, []))
    assert not [name for name, value in vars(c).items()
                if not name.startswith("_") and value == FAKE_KEY]


def test_an_api_error_message_does_not_carry_the_key(tmp_path):
    c = client(tmp_path, build_cache(tmp_path, []), budget=50,
               transport=stub_transport(403, {"error": "error code: 1010"}))
    with pytest.raises(ApiError) as excinfo:
        c.get("/v2/subsectors/")
    assert FAKE_KEY not in str(excinfo.value)


# --- transport-level behaviour, still offline -------------------------------
def test_a_browser_user_agent_is_sent(tmp_path):
    """Cloudflare answers `Python-urllib` with 403 "error code: 1010" — an edge block
    whose body never mentions user agents, so it reads like an auth failure."""
    sent = []
    c = client(tmp_path, build_cache(tmp_path, []), budget=5,
               transport=stub_transport(record=sent))
    c.get("/v2/subsectors/")
    agent = sent[0][1]["User-Agent"]
    assert "urllib" not in agent.lower() and agent.startswith("Mozilla/5.0")


def test_free_responses_are_ledgered_at_zero_and_do_not_spend(tmp_path):
    c = client(tmp_path, build_cache(tmp_path, []), budget=5,
               transport=stub_transport(400, {"error": "Use a valid date format."}))
    with pytest.raises(ApiError):
        c.get("/v2/subsectors/")
    row = json.loads(open(c.ledger_path, encoding="utf-8").read().strip())
    assert row["billed_cost"] == 0 and c.spent == 0


def test_a_routed_404_bills_one_and_an_unrouted_one_bills_nothing(tmp_path):
    routed = client(tmp_path, build_cache(tmp_path, []), budget=5,
                    ledger_path=str(tmp_path / "a.jsonl"),
                    transport=stub_transport(404, {"error": "Given stock symbol does not exist."}))
    with pytest.raises(NotFoundError):
        routed.get("/v2/daily/ZZZZ/", {"start": "2026-08-01", "end": "2026-08-31"})
    assert routed.spent == 1

    nowhere = client(tmp_path, build_cache(tmp_path, []), budget=5,
                     ledger_path=str(tmp_path / "b.jsonl"),
                     transport=stub_transport(404, {"details": "The requested endpoint "
                                                               "does not exist", "urls": {}}))
    with pytest.raises(NotFoundError):
        nowhere.get("/v2/nope/")
    assert nowhere.spent == 0
    assert unrouted_404({"details": "x", "urls": {}})
    assert not unrouted_404({"error": "Given stock symbol does not exist."})


def test_a_free_response_gives_its_rate_slot_back(tmp_path):
    """Free responses are not counted by the limiter, so throttling on them is waste."""
    window = RateWindow(calls=25, window=30, sleep=lambda _s: None)
    c = client(tmp_path, build_cache(tmp_path, []), budget=5, rate_window=window,
               transport=stub_transport(429, {"error": "RATE_LIMIT_EXCEEDED",
                                              "message": "Rate limit exceeded."}))
    with pytest.raises(ApiError) as excinfo:
        c.get("/v2/subsectors/")
    assert excinfo.value.code == "RATE_LIMIT_EXCEEDED"
    assert window.stamps == []


def test_the_rate_window_waits_only_when_it_is_full():
    slept = []
    window = RateWindow(calls=3, window=30, sleep=slept.append)
    for _ in range(3):
        window.wait()
    assert slept == []
    window.wait()
    assert len(slept) == 1 and 0 < slept[0] <= 30.2
