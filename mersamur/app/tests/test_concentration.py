"""The concentration axis, and the one arithmetic mistake that would hide inside it.

Half of this file is about a single line. Net dominance is
`top_buyers[0].net_idr + top_sellers[0].net_idr`, and the two ways to get it wrong
both look plausible:

  * summing **both sides in full** — the zero-sum trap the organizers warn about in
    `research/docs/api/10-domain-pitfalls.md` §1. Lands near zero for every symbol
    on the exchange, so the axis reads flat and nobody notices;
  * **subtracting** the top seller instead of adding it — `net_idr` is already
    negative on the sell side, so this inverts the axis. A distribution-led panel
    then reports accumulation.

`test_summing_both_sides_in_full_is_not_what_the_axis_reports` and
`test_sign_is_not_inverted_when_distribution_leads` are built so that either
implementation fails: the fixtures are constructed to make the wrong answers
numerically distinct from the right one, not merely close to it.

The headline numbers are asserted against the live recording, because 83,8% / `XL`
/ `retail` are the figures in `riset/temuan-kelayakan.md` §Q1 and silent drift
between that note and the code is what a test suite is for.

Zero credits: everything reads `research/harness/recorded/` or a temp directory.
`test_a_missing_panel_raises_instead_of_fetching` is the one that proves no socket
is opened.
"""
import json

import pytest

from app import axes as axes_mod
from app import cache as cache_mod
from app.axes import concentration
from app.axes.concentration import (
    AXIS,
    BOOK_FULL,
    NoBrokerDataError,
    broker,
    cohort_of,
    describe,
    registry,
    score,
)
from app.cache import Cache


# --- fixtures ---------------------------------------------------------------
def side(*rows):
    """`("XL", buy, sell)` triples into the shape the API returns, ranked."""
    out = []
    for rank, (code, buy, sell) in enumerate(rows, start=1):
        out.append({"rank": rank, "broker_code": code,
                    "net_idr": buy - sell, "buy_idr": buy, "sell_idr": sell})
    return out


def build_cache(tmp_path, panels=(), brokers=(), suspensions=()):
    """A recorded corpus holding broker panels, the registry and the label source.

    Written the way `capture.py` writes it — one payload file per slug plus a
    manifest row — so the test exercises the same lookup the product uses live.
    """
    from app import labels as labels_mod

    manifest = {}

    def add(path, params, payload):
        key = cache_mod.slug(path, params)
        (tmp_path / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")
        manifest[key] = {"path": path, "params": params, "status": 200,
                         "est_cost": 1, "fetched_at": 0, "cost_headers": {}}

    for symbol, payload in panels:
        add(concentration.BROKER_SUMMARY_PATH.format(symbol=symbol),
            {"n_brokers": 10}, payload)
    add(concentration.BROKERS_PATH, concentration.BROKERS_PARAMS, list(brokers))
    if suspensions:
        add(labels_mod.SUSPENSIONS_PATH, labels_mod.SUSPENSIONS_PARAMS,
            {"results": list(suspensions)})

    (tmp_path / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return Cache(root=str(tmp_path))


def panel(symbol, buyers, sellers, start="2026-06-11", end="2026-09-09"):
    return (symbol, {"symbol": f"{symbol}.JK", "start": start, "end": end,
                     "origin": "all", "cohort": "all",
                     "top_buyers": buyers, "top_sellers": sellers})


def broker_row(code, cohort="mixed", foreign=False, name=None):
    return {"code": code, "name": name or f"PT Sekuritas {code}",
            "is_foreign": foreign, "cohort": cohort,
            "license_type": "Perantara Pedagang Efek"}


def subdir(tmp_path, name):
    """A private directory, so two threshold documents in one test cannot collide."""
    path = tmp_path / name
    path.mkdir()
    return path


def thresholds_file(tmp_path, current=0.45, bounds=None, factors=None, version=9):
    doc = {"version": version, "updated_on": "2026-09-09",
           "current": {AXIS: current},
           "cohort_factors": factors if factors is not None
           else {"retail": 1.0, "mixed": 1.0, "institutional": 1.0},
           "history": []}
    if bounds is not None:
        doc["bounds"] = {AXIS: bounds}
    path = tmp_path / "thresholds.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


# --- the headline numbers ---------------------------------------------------
def test_life_matches_the_feasibility_note():
    """§Q1: LIFE 83,8% top-1, top buyer `XL`, cohort `retail`."""
    result = score("LIFE")
    assert round(result.top1_ratio, 2) == 0.84
    assert result.top_buyer == "XL"
    assert result.cohort == "retail"
    assert result.is_foreign is False
    assert result.fired is True


def test_top3_is_reported_alongside_top1():
    result = score("LIFE")
    assert round(result.top3_ratio, 3) == 0.900
    assert result.top3_ratio >= result.top1_ratio


def test_the_ratio_is_share_of_the_buy_side_not_of_the_whole_panel(tmp_path):
    """Denominator is `sum(buy_idr)` over the buyers, nothing else."""
    c = build_cache(tmp_path, panels=[panel(
        "AAAA", side(("XL", 750, 0), ("YP", 250, 0)), side(("DH", 0, 9000)))],
        brokers=[broker_row("XL")])
    assert score("AAAA", cache=c).top1_ratio == 0.75


def test_blue_chips_sit_far_below_the_suspended_names():
    """11-34% against a 61,6% median. The contrast is the whole axis."""
    for blue in ("BBCA", "BBRI", "TLKM"):
        assert score(blue).top1_ratio < 0.40
    for thin in ("LIFE", "TRUK", "AGAR", "CSMI", "TMPO"):
        assert score(thin).top1_ratio > 0.60


# --- the zero-sum trap ------------------------------------------------------
def test_summing_both_sides_in_full_is_not_what_the_axis_reports(tmp_path):
    """The documented mistake, reproduced: it lands on zero while the panel is loud.

    Buyers net +900/+100, sellers net -800/-200. Every net sums to exactly zero —
    an implementation that adds both sides in full reports 0 here, for a panel where
    the largest accumulator outweighs the largest distributor by 100.
    """
    buyers = side(("XL", 900, 0), ("YP", 100, 0))
    sellers = side(("DH", 0, 800), ("CC", 0, 200))
    c = build_cache(tmp_path, panels=[panel("AAAA", buyers, sellers)],
                    brokers=[broker_row("XL")])

    zero_sum = (sum(b["net_idr"] for b in buyers)
                + sum(s["net_idr"] for s in sellers))
    assert zero_sum == 0                       # the wrong answer, by construction

    result = score("AAAA", cache=c)
    assert result.net_dominance == 100         # 900 + (-800)
    assert result.net_dominance != zero_sum
    assert result.accumulating is True


def test_sign_is_not_inverted_when_distribution_leads(tmp_path):
    """Distribution-led panel: dominance must be negative.

    Top buyer +200, top seller -800. The correct sum is -600. Subtracting the seller
    instead — the intuitive reading of "buyer against seller" — gives +1000, which is
    positive, so an inverted implementation reports accumulation on a panel that is
    being distributed. Both the value and the direction are asserted.
    """
    c = build_cache(tmp_path, panels=[panel(
        "AAAA", side(("XL", 200, 0)), side(("DH", 0, 800)))],
        brokers=[broker_row("XL")])

    result = score("AAAA", cache=c)
    assert result.net_dominance == -600            # 200 + (-800)
    assert result.net_dominance != 1000            # 200 - (-800), the inverted form
    assert result.net_dominance < 0
    assert result.accumulating is False
    assert "distribusi" in describe(result)


def test_dominance_is_not_the_ratio_and_the_ratio_is_not_the_dominance(tmp_path):
    """Two measurements, two questions. A crowded buy side can still be distributing."""
    c = build_cache(tmp_path, panels=[panel(
        "AAAA", side(("XL", 1000, 900)), side(("DH", 0, 900)))],
        brokers=[broker_row("XL", cohort="retail")])
    result = score("AAAA", cache=c)
    assert result.top1_ratio == 1.0                # one broker is the entire buy side
    assert result.net_dominance == -800            # 100 + (-900): still distribution
    assert result.accumulating is False


# --- a short book -----------------------------------------------------------
def test_a_short_book_is_information_not_an_error():
    """NICK has five buyers because five brokers bought it. §Q1."""
    result = score("NICK")
    assert result.n_buyers == 5
    assert result.n_buyers < BOOK_FULL
    assert result.thin_book is True
    assert round(result.top1_ratio, 3) == 0.805
    assert "buku tipis" in describe(result)


def test_a_full_book_is_not_flagged_thin():
    assert score("LIFE").thin_book is False


def test_a_single_row_book_still_scores(tmp_path):
    c = build_cache(tmp_path, panels=[panel(
        "AAAA", side(("XL", 500, 0)), side(("DH", 0, 100)))],
        brokers=[broker_row("XL")])
    result = score("AAAA", cache=c)
    assert result.top1_ratio == 1.0 and result.top3_ratio == 1.0
    assert result.thin_book is True


# --- the registry -----------------------------------------------------------
def test_registry_reads_is_foreign_not_origin():
    """The spec misleads here: `origin` is a query parameter, not a broker field."""
    row = broker("XL")
    assert row["is_foreign"] is False
    assert "origin" not in row
    assert broker("AG")["is_foreign"] is True      # Kiwoom Sekuritas Indonesia


def test_the_panels_own_origin_field_is_not_a_broker_attribute():
    """`origin: "all"` echoes the request. Reading it as the broker's origin is the bug."""
    payload = concentration.panel("LIFE")
    assert payload["origin"] == "all"
    assert score("LIFE").is_foreign is False


def test_cohort_of_an_unlisted_broker_is_unknown_not_a_crash(tmp_path):
    c = build_cache(tmp_path, panels=[panel(
        "AAAA", side(("ZZ", 100, 0)), side(("DH", 0, 50)))], brokers=[broker_row("XL")])
    assert cohort_of("ZZ", cache=c) == "unknown"
    assert score("AAAA", cache=c).cohort == "unknown"


def test_the_registry_carries_the_whole_broker_list():
    assert len(registry()) == 88
    assert registry()["XL"]["cohort"] == "retail"


# --- thresholds are data ----------------------------------------------------
def test_the_bar_comes_from_the_file_not_from_the_module(tmp_path):
    """Same panel, two threshold documents, two answers."""
    low = thresholds_file(subdir(tmp_path, "low"), current=0.30)
    high = thresholds_file(subdir(tmp_path, "high"), current=0.95)
    assert score("LIFE", thresholds_path=low).fired is True
    assert score("LIFE", thresholds_path=high).fired is False
    assert score("LIFE", thresholds_path=high).top1_ratio == score("LIFE").top1_ratio


def test_the_threshold_is_clamped_into_its_own_bounds(tmp_path):
    """Task 17 moves these values automatically; the human bound wins."""
    path = thresholds_file(tmp_path, current=0.99, bounds={"floor": 0.30, "ceiling": 0.75})
    assert axes_mod.threshold(AXIS, path) == 0.75
    assert score("LIFE", thresholds_path=path).threshold == 0.75


def test_a_missing_thresholds_file_raises_rather_than_defaulting(tmp_path):
    """A fallback constant would be the hardcoded bar this design exists to avoid."""
    with pytest.raises(axes_mod.ThresholdsUnavailable):
        score("LIFE", thresholds_path=str(tmp_path / "absent.json"))


def test_cohort_moves_the_bar_and_never_the_measurement(tmp_path):
    """Retail concentration is the pattern sought, so the bar drops. The ratio does not."""
    lenient = thresholds_file(subdir(tmp_path, "lenient"), current=0.50,
                              factors={"retail": 0.5})
    strict = thresholds_file(subdir(tmp_path, "strict"), current=0.50,
                             factors={"retail": 2.0})

    soft = score("LIFE", thresholds_path=lenient)
    hard = score("LIFE", thresholds_path=strict)
    assert soft.effective_threshold == 0.25 and soft.fired is True
    assert hard.effective_threshold == 1.0 and hard.fired is False
    assert soft.top1_ratio == hard.top1_ratio      # the measurement is untouched


def test_an_unknown_cohort_leaves_the_bar_alone(tmp_path):
    c = build_cache(tmp_path, panels=[panel(
        "AAAA", side(("ZZ", 100, 0)), side(("DH", 0, 50)))], brokers=[broker_row("XL")])
    path = thresholds_file(tmp_path, current=0.40, factors={"retail": 0.5})
    result = score("AAAA", cache=c, thresholds_path=path)
    assert result.cohort_factor == axes_mod.NEUTRAL_FACTOR
    assert result.effective_threshold == 0.40


def test_the_answer_records_which_threshold_version_produced_it(tmp_path):
    path = thresholds_file(tmp_path, version=42)
    assert score("LIFE", thresholds_path=path).thresholds_version == 42


# --- all-zero panels --------------------------------------------------------
def test_an_all_zero_panel_is_never_scored_and_names_the_suspension(tmp_path):
    """A suspended IDX stock returns a well-formed all-zero series, not an error."""
    c = build_cache(
        tmp_path,
        panels=[panel("AAAA", side(("XL", 0, 0)), side(("DH", 0, 0)))],
        brokers=[broker_row("XL", cohort="retail")],
        suspensions=[{"symbol": "AAAA.JK", "suspension_date": "2026-07-01",
                      "reason": "dalam rangka cooling down"}])
    result = score("AAAA", cache=c)
    assert result.all_zero is True
    assert result.top1_ratio is None and result.top3_ratio is None
    assert result.fired is False
    assert [e.date.isoformat() for e in result.suspensions_in_window] == ["2026-07-01"]
    text = describe(result)
    assert "suspensi di dalam jendela" in text and "cooling_down" in text
    assert "sumbu tidak menyala" in text


def test_an_all_zero_panel_without_a_suspension_says_the_cause_is_unknown(tmp_path):
    """No suspension on record is not permission to conclude the stock is quiet."""
    c = build_cache(tmp_path,
                    panels=[panel("AAAA", side(("XL", 0, 0)), side(("DH", 0, 0)))],
                    brokers=[broker_row("XL")])
    result = score("AAAA", cache=c)
    assert result.all_zero is True and result.fired is False
    assert result.suspensions_in_window == ()
    assert "belum diketahui" in describe(result)


def test_a_zero_ratio_is_none_not_zero(tmp_path):
    """`0.0` would be a measurement. Nothing was measured."""
    c = build_cache(tmp_path,
                    panels=[panel("AAAA", side(("XL", 0, 0)), side(("DH", 0, 0)))],
                    brokers=[broker_row("XL")])
    assert score("AAAA", cache=c).top1_ratio is None


def test_a_suspension_outside_the_window_is_not_attached(tmp_path):
    c = build_cache(
        tmp_path,
        panels=[panel("AAAA", side(("XL", 0, 0)), side(("DH", 0, 0)),
                      start="2026-06-11", end="2026-09-09")],
        brokers=[broker_row("XL")],
        suspensions=[{"symbol": "AAAA.JK", "suspension_date": "2026-01-05",
                      "reason": "dalam rangka cooling down"}])
    assert score("AAAA", cache=c).suspensions_in_window == ()


# --- credits ----------------------------------------------------------------
def test_a_missing_panel_raises_instead_of_fetching(tmp_path):
    c = build_cache(tmp_path, panels=[], brokers=[broker_row("XL")])
    with pytest.raises(NoBrokerDataError):
        score("AAAA", cache=c)


def test_scoring_never_reaches_the_client(monkeypatch):
    """The axis is a reader. No path through it opens a socket."""
    import app.sectors_client as client_mod

    def explode(*a, **k):
        raise AssertionError("the concentration axis must not reach the client")

    monkeypatch.setattr(client_mod.SectorsClient, "get", explode)
    assert score("LIFE").top_buyer == "XL"


def test_a_symbol_with_no_recording_at_all_is_refused(tmp_path):
    c = build_cache(tmp_path, panels=[panel(
        "AAAA", side(("XL", 100, 0)), side(("DH", 0, 50)))], brokers=[broker_row("XL")])
    with pytest.raises(NoBrokerDataError):
        score("ZZZZ", cache=c)


def test_the_jk_suffix_is_accepted_the_way_the_screener_returns_it():
    assert score("life.jk").symbol == "LIFE"


# --- output -----------------------------------------------------------------
def test_the_description_is_descriptive_and_carries_no_verdict():
    text = describe(score("LIFE"))
    assert "83,8%" in text and "XL" in text and "retail" in text
    for verdict in ("beli", "jual", "rekomendasi", "sinyal", "waspada"):
        assert verdict not in text.lower()


def test_the_description_states_the_bar_it_was_measured_against():
    text = describe(score("LIFE"))
    assert "ambang" in text and "0,45" in text


def test_str_and_describe_agree():
    result = score("LIFE")
    assert str(result) == describe(result)
