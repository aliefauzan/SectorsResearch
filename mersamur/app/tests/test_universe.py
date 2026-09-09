"""The universe's two jobs: naming the right tier, and refusing every other name.

The headline counts are asserted against the live recording on purpose — 200 / 98
/ 102 are the numbers in `riset/temuan-kelayakan.md` §"Satu temuan yang mengubah
penentuan universe", and silent drift between that note and the code is what this
file exists to catch. The resolution rules are asserted against a corpus the test
builds itself, because "a guessed symbol never reaches the client" has to hold for
any recording, not only today's.

Zero credits: every test reads the recording or a temp directory. Nothing here
opens a socket, and `test_resolve_refuses_before_any_client_call` is the one that
proves it.
"""
import json

import pytest

from app import cache as cache_mod
from app import labels as labels_mod
from app.cache import Cache
from app.universe import (
    DEFAULT_SIZE,
    SCREENER_PARAMS,
    SCREENER_PATH,
    UnknownSymbolError,
    companies,
    control_group,
    is_known,
    known_symbols,
    market_cap,
    normalize,
    resolve,
    summary,
    watchlist,
)


def build_cache(tmp_path, rows, suspensions=(), extra=None):
    """A recorded corpus holding the screener call, and optionally the suspensions.

    Written the way `capture.py` writes it — payload file per slug plus a manifest
    row — so the test exercises the same lookup path the product uses in
    production. `extra` takes raw `{slug: (entry, payload_or_None)}` for the cases
    that need a 404 or an unsettled entry on disk.
    """
    manifest = {}

    def add(path, params, status, payload):
        key = cache_mod.slug(path, params)
        if payload is not None:
            (tmp_path / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")
        manifest[key] = {"path": path, "params": params, "status": status,
                         "est_cost": 1, "fetched_at": 0, "cost_headers": {}}

    add(SCREENER_PATH, SCREENER_PARAMS, 200, {"results": list(rows)})
    if suspensions:
        add(labels_mod.SUSPENSIONS_PATH, labels_mod.SUSPENSIONS_PARAMS, 200,
            {"results": list(suspensions)})
    for key, (entry, payload) in (extra or {}).items():
        if payload is not None:
            (tmp_path / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")
        manifest[key] = entry

    (tmp_path / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return Cache(root=str(tmp_path))


def row(symbol, cap, name=None):
    """One screener row, in the shape `/v2/companies/` actually returns."""
    return {"symbol": f"{symbol}.JK",
            "company_name": name or f"PT {symbol} Tbk",
            "query_values": {"market_cap": cap}}


def suspension(symbol, day, reason="dalam rangka cooling down"):
    return {"symbol": f"{symbol}.JK", "suspension_date": day, "reason": reason}


# --- the tier ---------------------------------------------------------------

def test_watchlist_and_control_group_match_the_feasibility_note():
    """200 smallest, 98 with a suspension on record, 102 clean. The whole premise."""
    universe = watchlist()
    clean = control_group()
    assert len(universe) == 200
    assert len(clean) == 102
    assert len(universe) - len(clean) == 98
    assert set(clean) <= set(universe)


def test_default_size_is_the_tier_the_49_percent_was_measured_on():
    assert DEFAULT_SIZE == 200
    assert watchlist() == watchlist(size=DEFAULT_SIZE)


def test_the_universe_is_the_smallest_caps_ascending():
    rows = companies()
    caps = [c.market_cap for c in rows]
    assert caps == sorted(caps)
    assert rows[0].market_cap <= rows[-1].market_cap
    # This is a small-cap tier, not the market: nothing here is near a trillion.
    assert rows[-1].market_cap < 1_000_000_000_000


def test_size_narrows_the_tier_from_the_bottom(tmp_path):
    c = build_cache(tmp_path, [row("DDDD", 40), row("AAAA", 10),
                               row("CCCC", 30), row("BBBB", 20)])
    assert watchlist(size=2, cache=c) == ["AAAA", "BBBB"]


def test_rows_without_a_market_cap_sort_last_not_first(tmp_path):
    """A missing cap must not masquerade as the smallest company on the exchange."""
    blank = row("ZZZA", None)
    blank["query_values"] = {}
    c = build_cache(tmp_path, [blank, row("AAAA", 10)])
    assert watchlist(cache=c) == ["AAAA", "ZZZA"]


# --- the control group ------------------------------------------------------

def test_control_group_excludes_every_reason_class_and_every_year(tmp_path):
    """A 2019 late-report halt still disqualifies a control. Any prior halt does."""
    c = build_cache(
        tmp_path,
        [row("AAAA", 10), row("BBBB", 20), row("CCCC", 30), row("DDDD", 40)],
        suspensions=[
            suspension("BBBB", "2026-03-01"),                              # label class
            suspension("CCCC", "2019-04-02", "belum menyampaikan laporan"),  # pre-2025, other class
        ])
    assert control_group(cache=c) == ["AAAA", "DDDD"]


def test_control_group_is_a_subset_of_the_watchlist(tmp_path):
    c = build_cache(tmp_path, [row("AAAA", 10), row("BBBB", 20)],
                    suspensions=[suspension("BBBB", "2026-03-01"),
                                 suspension("XXXX", "2026-03-01")])
    universe = watchlist(cache=c)
    assert control_group(cache=c) == ["AAAA"]
    assert "XXXX" not in universe


# --- symbol resolution ------------------------------------------------------

def test_invented_symbol_is_refused_and_never_reaches_the_client():
    """ZZZZ stops here. A routed 404 bills one credit, because the lookup ran."""
    with pytest.raises(UnknownSymbolError):
        resolve("ZZZZ")
    assert is_known("ZZZZ") is False


def test_resolve_refuses_before_any_client_call(monkeypatch):
    """The guard is upstream of the network: no HTTP path is even constructed."""
    import app.sectors_client as client_mod

    def explode(*a, **k):
        raise AssertionError("resolve() must not reach the client")

    monkeypatch.setattr(client_mod.SectorsClient, "get", explode)
    with pytest.raises(UnknownSymbolError):
        resolve("ZZZZ")


def test_resolve_accepts_a_symbol_that_came_back_in_a_paid_response():
    assert resolve("life.jk") == "LIFE"
    assert resolve(" LIFE ") == "LIFE"
    assert is_known("LIFE") is True


def test_every_watchlist_member_resolves():
    """The universe cannot contain a name the product is not allowed to ask about."""
    assert [resolve(s) for s in watchlist()] == watchlist()


def test_empty_and_malformed_symbols_are_refused():
    for bad in ("", "   ", None, 42, "LIF", "LIFEX", "life-jk"):
        with pytest.raises(UnknownSymbolError):
            resolve(bad)


def test_sgx_and_klse_symbols_are_refused_even_though_they_are_real():
    """`1D0.SI` and `1155` are in the recording. They are not this product's market."""
    for foreign in ("1D0.SI", "1155", "D05.SI"):
        with pytest.raises(UnknownSymbolError):
            resolve(foreign)


def test_a_symbol_known_only_from_a_billed_404_is_not_known(tmp_path):
    """One paid-for miss must not authorise the next one."""
    key = cache_mod.slug("/v2/listing-performance/QQQQ/", None)
    c = build_cache(tmp_path, [row("AAAA", 10)], extra={key: (
        {"path": "/v2/listing-performance/QQQQ/", "params": None, "status": 404,
         "est_cost": 1, "fetched_at": 0, "cost_headers": {}}, None)})
    assert "QQQQ" not in known_symbols(cache=c)
    assert "AAAA" in known_symbols(cache=c)
    with pytest.raises(UnknownSymbolError):
        resolve("QQQQ", cache=c)


def test_known_symbols_reads_tickers_out_of_nested_payloads(tmp_path):
    """Symbols come back from every endpoint, not only the screener."""
    key = cache_mod.slug("/v2/companies/top-changes/", None)
    c = build_cache(tmp_path, [row("AAAA", 10)], extra={key: (
        {"path": "/v2/companies/top-changes/", "params": None, "status": 200,
         "est_cost": 1, "fetched_at": 0, "cost_headers": {}},
        {"top_gainers": {"1d": [{"symbol": "BBBB.JK", "change": 0.35}]}})})
    assert {"AAAA", "BBBB"} <= known_symbols(cache=c)


# --- the .JK suffix, handled in one place -----------------------------------

def test_normalize_is_the_single_place_the_jk_suffix_dies():
    assert normalize(" life.jk ") == "LIFE"
    assert normalize("LIFE.JK") == "LIFE"
    assert normalize("LIFE") == "LIFE"
    assert normalize(None) == ""
    assert normalize(1155) == ""
    # Only .JK. A foreign suffix survives, and therefore fails the IDX shape test.
    assert normalize("1D0.SI") == "1D0.SI"


def test_watchlist_symbols_are_bare_tickers():
    assert all(".JK" not in s and s == s.upper() for s in watchlist())


# --- market_cap, the only metric the screener carries ------------------------

def test_market_cap_comes_from_query_values(tmp_path):
    c = build_cache(tmp_path, [row("AAAA", 4_752_982_378)])
    assert market_cap("AAAA", cache=c) == 4_752_982_378
    assert market_cap("aaaa.jk", cache=c) == 4_752_982_378


def test_market_cap_is_none_outside_the_tier():
    """Not an exception: "not in this universe" is an answer, not a failure."""
    assert market_cap("BBCA") is None
    assert market_cap("ZZZZ") is None


def test_companies_expose_only_what_the_screener_returns(tmp_path):
    c = build_cache(tmp_path, [row("AAAA", 10, name="PT Contoh Tbk")])
    company = companies(cache=c)[0]
    assert (company.symbol, company.name, company.market_cap) == ("AAAA", "PT Contoh Tbk", 10)
    with pytest.raises(Exception):
        company.market_cap = 99


# --- degradation and tone ---------------------------------------------------

def test_missing_recording_yields_an_empty_universe_not_a_crash(tmp_path):
    (tmp_path / "_manifest.json").write_text("{}", encoding="utf-8")
    c = Cache(root=str(tmp_path))
    assert watchlist(cache=c) == []
    assert control_group(cache=c) == []
    assert known_symbols(cache=c) == frozenset()
    assert "kosong" in summary(cache=c)


def test_summary_is_descriptive_and_carries_no_verdict():
    text = summary()
    assert "200" in text and "102" in text and "49%" in text
    for verdict in ("beli", "jual", "rekomendasi", "sinyal", "waspada"):
        assert verdict not in text.lower()
