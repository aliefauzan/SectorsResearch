"""What a profile must never do: flatten, guess, or say what to do about it.

The four axes are already tested one by one. These tests are about the *shape* of
the combination, and each of them is aimed at a wrong implementation that would
otherwise look right:

  * **a weighted sum.** The whole argument of the product is that independent views
    agreed; one number throws that away and reads as a recommendation
    (`riset/spec.md` §5, `riset/red-team.md` §D11). `test_profile_carries_no_single_score`
    parses `profile.py` and asserts nothing in it holds weights or sums the axes.
  * **missing data counted as calm.** An axis with no payload is `unknown`, never
    `False`. Folding the two would let an unmeasured stock read as quiet and a
    *halted* one as quietest of all.
  * **a number with no provenance.** Every value and every bar must name where it
    came from — the endpoint and fields, or the state file and key.
  * **a threshold baked into the module.** The bars are injectable, so a profile
    computed against a different file must move.
  * **a verdict.** Nothing in the output may say buy, sell, safe, dangerous, or
    name a colour.

Zero credits: every test reads `research/harness/recorded/` or a temp directory.
Nothing here opens a socket.
"""
import ast
import inspect
import json
import re
from datetime import date

import pytest

from app import cache as cache_mod
from app import labels as labels_mod
from app import profile as profile_mod
from app.axes import catalyst, concentration, volume_anomaly
from app.cache import Cache
from app.profile import LIT, UNKNOWN, build, describe


# --- fixtures ---------------------------------------------------------------
def daily_rows(symbol, dates, closes, volumes):
    return [{"symbol": f"{symbol}.JK", "date": d, "close": c, "open": c,
             "high": c, "low": c, "volume": v, "market_cap": c * 1_000_000}
            for d, c, v in zip(dates, closes, volumes)]


def build_cache(tmp_path, dailies=(), brokers=(), panels=(), news=(),
                suspensions=()):
    """A recorded corpus, written the way `capture.py` writes one.

    One payload file per slug plus a manifest row, so the test walks the same lookup
    path the product uses live rather than a shortcut only tests take.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    manifest = {}

    def add(path, params, payload):
        key = cache_mod.slug(path, params)
        (tmp_path / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")
        manifest[key] = {"path": path, "params": params, "status": 200,
                         "est_cost": 1, "fetched_at": 0, "cost_headers": {}}

    for symbol, params, payload in dailies:
        add(volume_anomaly.DAILY_PATH.format(symbol=symbol), params, payload)
    for symbol, params, payload in panels:
        add(concentration.BROKER_SUMMARY_PATH.format(symbol=symbol), params, payload)
    if brokers:
        add(concentration.BROKERS_PATH, concentration.BROKERS_PARAMS,
            {"results": list(brokers)})
    for params, payload in news:
        add(catalyst.NEWS_PATH, params, payload)
    if suspensions:
        add(labels_mod.SUSPENSIONS_PATH, labels_mod.SUSPENSIONS_PARAMS,
            {"results": list(suspensions)})

    (tmp_path / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return Cache(root=str(tmp_path))


def thresholds_file(tmp_path, concentration_bar=0.45, volume=5.0, momentum_bar=90.0,
                    catalyst_bar=0.10, version=9):
    tmp_path.mkdir(parents=True, exist_ok=True)
    doc = {"version": version, "updated_on": "2026-09-09",
           "current": {"concentration": concentration_bar,
                       "volume_anomaly": volume,
                       "momentum": momentum_bar,
                       "catalyst": catalyst_bar},
           "bounds": {}, "cohort_factors": {}, "history": []}
    path = tmp_path / "thresholds.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


def empty_cache(tmp_path):
    """A corpus holding nothing but the suspension source. Every axis unmeasurable."""
    return build_cache(tmp_path / "empty", suspensions=[])


# --- the ranking the task names ---------------------------------------------
def test_life_outranks_pack_on_axes_fired():
    """The task's own criterion, and the reason the profile is a count at all."""
    life, pack = build("LIFE"), build("PACK")
    assert life["axes_fired"] > pack["axes_fired"]
    assert life.axes_fired == 2
    assert set(life.fired_axes) == {"concentration", "volume_anomaly"}
    assert pack.axes_fired == 0


def test_the_count_is_out_of_four_and_names_which():
    """Two of four, named. A bare "2" would be the single number §5 rules out."""
    life = build("LIFE")
    assert life.axes_total == 4
    assert life.axes_fired + life.axes_unlit + life.axes_unknown == 4
    assert [r.axis for r in life.readings] == list(profile_mod.AXES)


def test_history_is_reported_but_never_counted():
    """The supporting axis is also the baseline; counting it would score its answer."""
    life = build("LIFE")
    supporting = life.supporting[0]
    assert supporting.axis == "history"
    assert supporting.counted is False
    assert supporting.value == 2                      # two prior suspensions
    assert all(r.counted for r in life.readings)
    assert "history" not in life.fired_axes


# --- missing data is unknown, never quiet -----------------------------------
def test_an_axis_without_data_is_unknown(tmp_path):
    """No payload is not a measurement of zero. Every axis reads `unknown`."""
    result = build("LIFE", cache=empty_cache(tmp_path),
                   thresholds_path=thresholds_file(tmp_path))
    assert result.axes_unknown == 4
    assert all(r.fired is None and r.state == UNKNOWN for r in result.readings)


def test_unknown_axes_are_not_counted_as_unlit(tmp_path):
    """The bug this test exists for: `not fired` treated as "did not fire"."""
    result = build("LIFE", cache=empty_cache(tmp_path),
                   thresholds_path=thresholds_file(tmp_path))
    assert result.axes_unlit == 0
    assert result.axes_fired == 0
    assert set(result.unknown_axes) == set(profile_mod.AXES)


def test_every_unknown_axis_says_why(tmp_path):
    """An unmeasured axis with no reason is indistinguishable from a bug."""
    result = build("LIFE", cache=empty_cache(tmp_path),
                   thresholds_path=thresholds_file(tmp_path))
    for reading in result.readings:
        assert reading.unknown_reason.strip()


def test_a_symbol_nobody_wrote_about_is_unknown_not_zero(tmp_path):
    """`ratio is None` (no articles) and `ratio == 0.0` are different findings.

    Zero fundamental articles out of eleven is a measurement. No articles at all is
    the absence of one, and it must not light an axis whose bar is read downwards.
    """
    cache = build_cache(
        tmp_path / "nonews",
        news=[({"symbols": "AAAA", "limit": 30}, {"results": []})],
        suspensions=[])
    reading, _ = profile_mod._read_catalyst(
        "AAAA", cache=cache, thresholds_path=thresholds_file(tmp_path))
    assert reading.value is None
    assert reading.fired is None
    assert reading.state == UNKNOWN


def test_zero_fundamental_articles_is_a_measurement(tmp_path):
    """The other side of the same distinction: articles exist, none are fundamental."""
    rows = [{"title": "Harga naik", "body": "", "source": "x", "sector": "",
             "timestamp": "2026-09-0%dT07:00:00" % (i + 1), "symbols": ["AAAA.JK"],
             "dimension": {"technical": 90, "financials": 0, "future": 0}}
            for i in range(3)]
    cache = build_cache(
        tmp_path / "flat",
        news=[({"symbols": "AAAA", "limit": 30}, {"results": rows})],
        suspensions=[])
    reading, _ = profile_mod._read_catalyst(
        "AAAA", cache=cache, thresholds_path=thresholds_file(tmp_path))
    assert reading.value == 0.0
    assert reading.fired is True
    assert reading.state == LIT


# --- a halted stock is not a calm one ---------------------------------------
def suspended_corpus(tmp_path):
    """A symbol whose whole window is zero volume, with the announcement to match."""
    dates = ["2026-08-%02d" % d for d in range(3, 29) if date(2026, 8, d).weekday() < 5]
    dailies = [("AAAA", {}, {"results": daily_rows("AAAA", dates,
                                                   [100] * len(dates),
                                                   [0] * len(dates))})]
    panels = [("AAAA", {"n_brokers": 10},
               {"start": dates[0], "end": dates[-1],
                "top_buyers": [{"broker_code": "XL", "buy_idr": 0, "net_idr": 0}],
                "top_sellers": [{"broker_code": "YP", "sell_idr": 0, "net_idr": 0}]})]
    suspensions = [{"symbol": "AAAA.JK", "suspension_date": "2026-08-10",
                    "reason": "cooling down period"}]
    return build_cache(tmp_path / "halted", dailies=dailies, panels=panels,
                       brokers=[{"code": "XL", "name": "XL Sekuritas",
                                 "cohort": "retail", "is_foreign": False}],
                       suspensions=suspensions)


def test_a_suspended_symbol_is_stated_not_scored_as_zero(tmp_path):
    """Nol di semua sumbu is exactly the wrong reading of a halt."""
    result = build("AAAA", cache=suspended_corpus(tmp_path),
                   thresholds_path=thresholds_file(tmp_path))
    assert result.suspended is True
    assert result.axes_fired == 0
    assert result.axes_unlit == 0                      # nothing "failed to fire"
    assert {"concentration", "volume_anomaly", "momentum"} <= set(result.unknown_axes)


def test_a_suspended_symbol_names_the_announcement(tmp_path):
    """The halt is identified from the window's own announcements, not inferred."""
    result = build("AAAA", cache=suspended_corpus(tmp_path),
                   thresholds_path=thresholds_file(tmp_path))
    assert [e.date.isoformat() for e in result.suspension_events] == ["2026-08-10"]
    text = describe(result)
    assert "berhenti diperdagangkan" in text
    assert "2026-08-10" in text


def test_suspension_note_says_zero_means_no_trading(tmp_path):
    """The sentence that stops a reader concluding "nothing was found"."""
    text = describe(build("AAAA", cache=suspended_corpus(tmp_path),
                          thresholds_path=thresholds_file(tmp_path)))
    assert "bukan tidak ada temuan" in text


# --- citations --------------------------------------------------------------
def numbers_in(node, path=()):
    """Every numeric leaf in the profile dict, with the path that reached it."""
    if isinstance(node, bool) or node is None:
        return []
    if isinstance(node, (int, float)):
        return [(path, node)]
    if isinstance(node, dict):
        out = []
        for key, value in node.items():
            out += numbers_in(value, path + (key,))
        return out
    if isinstance(node, list):
        out = []
        for i, value in enumerate(node):
            out += numbers_in(value, path + (i,))
        return out
    return []


def test_every_measured_value_carries_an_endpoint_and_fields():
    for symbol in ("LIFE", "PACK"):
        for reading in build(symbol).readings + build(symbol).supporting:
            if reading.value is None:
                continue
            assert reading.sources, reading.axis
            for source in reading.sources:
                assert source.endpoint and source.fields
                assert source.origin == "api"


def test_every_threshold_cites_the_state_file_not_the_module():
    for reading in build("LIFE").readings:
        if reading.threshold is None:
            continue
        assert reading.threshold_sources
        for source in reading.threshold_sources:
            assert source.origin == "state"
            assert source.endpoint == profile_mod.THRESHOLDS_FILE
            assert any(f.startswith("current.") for f in source.fields)


def test_every_context_number_carries_its_source():
    for reading in build("LIFE").readings + build("LIFE").supporting:
        for name, value, _unit, sources in reading.context:
            assert sources, name
            assert all(s.endpoint and s.fields for s in sources)


def test_the_dict_form_has_a_citation_for_every_number():
    """Walk the serialised profile: no numeric leaf without provenance beside it."""
    payload = build("LIFE").to_dict()
    for reading in payload["readings"] + payload["supporting"]:
        if reading["value"] is not None:
            assert reading["value_sources"]
        if reading["threshold"] is not None:
            assert reading["threshold_sources"]
        for item in reading["context"]:
            if item["value"] is not None:
                assert item["sources"], item["name"]


def test_the_profile_lists_every_source_it_rests_on():
    citations = {s.endpoint for s in build("LIFE").citations}
    assert {"/v2/broker-summary/{symbol}/top/", "/v2/brokers/", "/v2/daily/{symbol}/",
            "/v2/news/", "/v2/suspensions/",
            profile_mod.THRESHOLDS_FILE} <= citations


# --- thresholds are data ----------------------------------------------------
def test_bars_come_from_the_file_not_from_this_module(tmp_path):
    """Move the bars and the same measurements must produce a different profile."""
    loose = thresholds_file(tmp_path / "loose", concentration_bar=0.30, volume=1.0,
                            momentum_bar=10.0, catalyst_bar=0.90, version=41)
    tight = thresholds_file(tmp_path / "tight", concentration_bar=0.99, volume=999.0,
                            momentum_bar=99.0, catalyst_bar=0.0, version=42)
    assert build("LIFE", thresholds_path=loose).axes_fired == 4
    assert build("LIFE", thresholds_path=tight).axes_fired == 0


def test_the_profile_records_which_threshold_version_answered(tmp_path):
    path = thresholds_file(tmp_path, version=42)
    assert build("LIFE", thresholds_path=path)["thresholds_version"] == 42


def test_the_catalyst_bar_is_read_downwards(tmp_path):
    """A *low* share of fundamental coverage is the notable reading, not a high one."""
    high = thresholds_file(tmp_path / "high", catalyst_bar=0.90)
    low = thresholds_file(tmp_path / "low", catalyst_bar=0.01)
    assert build("LIFE", thresholds_path=high).readings[3].fired is True
    assert build("LIFE", thresholds_path=low).readings[3].fired is False


# --- no single score --------------------------------------------------------
def test_profile_carries_no_single_score():
    """No weights, no total, no average. Parsed, not trusted.

    §5 rules out flattening the axes; a later edit that adds `WEIGHTS = {...}` and a
    sum would still pass every other test in this file, so the source itself is
    checked.
    """
    source = inspect.getsource(profile_mod)
    tree = ast.parse(source)
    names = {t.id for node in ast.walk(tree)
             if isinstance(node, ast.Assign)
             for t in node.targets if isinstance(t, ast.Name)}
    assert not {n for n in names if "WEIGHT" in n.upper() or "SCORE" in n.upper()}
    # The prose is allowed to say "bobot" — it explains why there are none. The
    # dataclass fields and the serialised profile are not.
    fields = {f for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
              for stmt in node.body if isinstance(stmt, ast.AnnAssign)
              and isinstance(stmt.target, ast.Name) for f in (stmt.target.id,)}
    assert not {f for f in fields
                if any(w in f.lower() for w in ("weight", "bobot", "score", "skor"))}
    payload = build("LIFE").to_dict()
    assert "score" not in payload and "skor" not in payload
    assert not any(w in json.dumps(payload).lower()
                   for w in ("weighted", "total_score"))


def test_the_count_is_not_a_ratio_of_the_axes():
    """`axes_fired` is a count, not a normalised fraction pretending not to be one."""
    life = build("LIFE").to_dict()
    assert isinstance(life["axes_fired"], int)
    assert life["axes_fired"] == 2


# --- descriptive only -------------------------------------------------------
# Verdict vocabulary and colour words. Matched on word boundaries so `pembeli` or
# `menjual` inside a legitimate phrase is not a false hit — the ban is on the
# verdict, not on the letters.
BANNED = ("beli", "jual", "aman", "bahaya", "berbahaya", "waspada", "rekomendasi",
          "merah", "hijau", "buy", "sell", "risiko tinggi", "layak", "hindari",
          "gorengan", "manipulasi", "digoreng")


def banned_words_in(text):
    lowered = text.lower()
    return [w for w in BANNED if re.search(r"\b" + re.escape(w) + r"\b", lowered)]


def test_no_verdict_vocabulary_in_the_description():
    for symbol in ("LIFE", "PACK"):
        assert banned_words_in(describe(build(symbol))) == []


def test_no_verdict_vocabulary_in_the_serialised_profile():
    for symbol in ("LIFE", "PACK"):
        payload = json.dumps(build(symbol).to_dict(), ensure_ascii=False)
        assert banned_words_in(payload) == []


def test_no_verdict_vocabulary_when_the_symbol_is_suspended(tmp_path):
    result = build("AAAA", cache=suspended_corpus(tmp_path),
                   thresholds_path=thresholds_file(tmp_path))
    assert banned_words_in(describe(result)) == []
    assert banned_words_in(json.dumps(result.to_dict(), ensure_ascii=False)) == []


def test_no_verdict_vocabulary_when_nothing_could_be_measured(tmp_path):
    result = build("LIFE", cache=empty_cache(tmp_path),
                   thresholds_path=thresholds_file(tmp_path))
    assert banned_words_in(describe(result)) == []


def test_the_description_says_the_profile_is_descriptive():
    text = describe(build("LIFE"))
    assert "deskriptif" in text
    assert "anjuran tindakan" in text


def test_the_description_names_which_axes_lit():
    text = describe(build("LIFE"))
    assert "concentration" in text and "volume_anomaly" in text
    assert "2 dari 4" in text


# --- leak safety of the supporting axis -------------------------------------
def test_history_cutoff_defaults_to_the_start_of_the_feature_window():
    """Anything dated inside the window is future information to the window itself."""
    result = build("LIFE")
    assert result.cutoff == result.window_start


def test_an_explicit_cutoff_is_honoured():
    early = build("LIFE", cutoff="2020-01-01")
    assert early.cutoff == "2020-01-01"
    assert early.supporting[0].value == 0


# --- zero credits -----------------------------------------------------------
def test_profile_never_imports_the_client():
    """The module reads recordings. A client import here is a credit leak waiting.

    Parsed rather than grepped: the docstring names `SectorsClient` precisely to say
    it is never imported, and a substring check would fail on the sentence that
    documents the rule.
    """
    tree = ast.parse(inspect.getsource(profile_mod))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported |= {a.name for a in node.names}
    assert not {n for n in imported if "client" in n.lower()}
    assert "urllib" not in " ".join(imported)


def test_mapping_access_matches_the_dict():
    result = build("LIFE")
    payload = result.to_dict()
    for key in ("symbol", "axes_fired", "axes_total", "axes_unknown", "citations"):
        assert result[key] == payload[key]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
