"""What the output surface must never do: invent a number, or pass a verdict.

The paragraph is the product. Everything upstream — four axes, three states, a
threshold file with a version — reaches a reader only through these sentences, so
the failures that matter are the ones that survive every other test in the suite
and still ship a wrong sentence:

  * **a number with nothing behind it.** A figure written from a local variable
    reads exactly like a checked one, which is why the verifier walks the finished
    text rather than trusting the code that produced it, and why it refuses instead
    of rendering. `test_an_uncited_number_is_refused` proves the refusal happens on
    the real path, not only when called directly.
  * **a citation that names the wrong source.** Worse than an absent one: it passes
    the check that exists to catch it.
  * **a verdict.** `riset/red-team.md` §D11 rules out buy/sell, safe/dangerous,
    recommendations, price targets and red/green outright. `BANNED` is that rule as
    data and it is enforced on every symbol the product can render, including the
    halted and the unmeasurable ones.
  * **missing data rendered as zero.** Four axes with no recording is the absence of
    a measurement; printed as `0` it would read as the strongest finding of nothing.
  * **the prototype's paragraph.** `tools/profile_demo.py` chained every finding into
    one sentence; by the fourth clause the reader had lost the first. Sentence count
    and length are asserted so the fix cannot quietly be undone.

Zero credits: every test reads `research/harness/recorded/` or a temp directory.
Nothing here opens a socket.
"""
import json
import re
from datetime import date

import pytest

from app import cache as cache_mod
from app import labels as labels_mod
from app import profile as profile_mod
from app.axes import catalyst, concentration, volume_anomaly
from app.cache import Cache
from app.render import paragraph as par
from app.render.paragraph import (BannedVocabularyError, Cited, Paragraph,
                                  UncitedNumberError, render, render_symbol, verify)

# Symbols with recorded payloads behind every axis.
LIVE = ("LIFE", "ASLI", "PACK")


# --- fixtures ---------------------------------------------------------------
def daily_rows(symbol, dates, closes, volumes):
    return [{"symbol": f"{symbol}.JK", "date": d, "close": c, "open": c,
             "high": c, "low": c, "volume": v, "market_cap": c * 1_000_000}
            for d, c, v in zip(dates, closes, volumes)]


def build_cache(tmp_path, dailies=(), brokers=(), panels=(), news=(),
                suspensions=()):
    """A recorded corpus written the way `capture.py` writes one, manifest and all."""
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
    return build_cache(tmp_path / "empty")


def halted_cache(tmp_path):
    """A symbol whose whole window is zero volume, with the announcement to match."""
    dates = ["2026-08-%02d" % d for d in range(3, 29) if date(2026, 8, d).weekday() < 5]
    return build_cache(
        tmp_path / "halted",
        dailies=[("AAAA", {}, {"results": daily_rows("AAAA", dates,
                                                     [100] * len(dates),
                                                     [0] * len(dates))})],
        panels=[("AAAA", {"n_brokers": 10},
                 {"start": dates[0], "end": dates[-1],
                  "top_buyers": [{"broker_code": "XL", "buy_idr": 0, "net_idr": 0}],
                  "top_sellers": [{"broker_code": "YP", "sell_idr": 0,
                                   "net_idr": 0}]})],
        brokers=[{"code": "XL", "name": "XL Sekuritas", "cohort": "retail",
                  "is_foreign": False}],
        suspensions=[{"symbol": "AAAA.JK", "suspension_date": "2026-08-10",
                      "reason": "cooling down period"}])


def unavailable(tmp_path):
    return render_symbol("ZZZZ", cache=empty_cache(tmp_path),
                         thresholds_path=thresholds_file(tmp_path))


def halted(tmp_path):
    cache = halted_cache(tmp_path)
    return render(profile_mod.build("AAAA", cache=cache,
                                    thresholds_path=thresholds_file(tmp_path)),
                  cache=cache)


def every_paragraph(tmp_path):
    """Everything the product can render: measured, halted, and unmeasurable."""
    return [render_symbol(s) for s in LIVE] + [halted(tmp_path), unavailable(tmp_path)]


# --- shape: sentences, not a wall -------------------------------------------
def test_the_output_is_two_or_three_sentences(tmp_path):
    for paragraph in every_paragraph(tmp_path):
        assert 2 <= len(paragraph.sentences) <= par.MAX_SENTENCES, paragraph.symbol


def test_no_sentence_runs_past_the_ceiling(tmp_path):
    """The prototype's failure was length, so length is asserted, not intended."""
    for paragraph in every_paragraph(tmp_path):
        for sentence in paragraph.sentences:
            assert len(sentence.split()) <= par.SENTENCE_WORD_CEILING, sentence


def test_every_sentence_ends_as_one():
    for paragraph in (render_symbol(s) for s in LIVE):
        for sentence in paragraph.sentences:
            assert sentence.endswith(".")


def test_the_first_sentence_names_the_axis_furthest_past_its_bar():
    """Findings in computation order buried the strongest one. Ranked, it leads."""
    for symbol in LIVE:
        profile = profile_mod.build(symbol)
        lead = par._lead(profile.counted)
        first = render(profile).sentences[0]
        assert par.AXIS_PROSE[lead.axis] in first, (symbol, first)


def test_lifes_leading_sentence_is_the_volume_reading():
    """LIFE fires on two axes; 24,5x against a 5,0x bar is the one that leads."""
    first = render_symbol("LIFE").sentences[0]
    assert "volume" in first
    assert "24,5x" in first


# --- numbers are spoken -----------------------------------------------------
def test_money_is_spoken_not_printed_in_full():
    """ASLI leads on concentration, so its panel value reaches the sentence."""
    text = render_symbol("ASLI").text
    assert "Rp290,3 miliar" in text
    assert "290305" not in text


def test_counts_use_indonesian_separators():
    assert par.ribuan(147000) == "147.000"
    assert par.desimal(24.5) == "24,5"
    assert par.persen(0.8381869162312745) == "83,8%"
    assert par.rupiah(1_200_000_000_000) == "Rp1,2 triliun"
    assert par.rupiah(9_923_485_000) == "Rp9,9 miliar"


def test_no_raw_float_reaches_the_text():
    """`0.8381869162312745` in a sentence is the internal representation leaking."""
    for symbol in LIVE:
        profile = profile_mod.build(symbol)
        text = render(profile).text
        for reading in profile.readings + profile.supporting:
            values = [reading.value, reading.threshold]
            values += [value for _n, value, _u, _s in reading.context]
            for value in values:
                if isinstance(value, float):
                    assert str(value) not in text, (symbol, value)
        assert not re.search(r"\de[+-]?\d", text), symbol


# --- every number carries its source ----------------------------------------
def test_every_figure_names_an_endpoint_and_its_fields(tmp_path):
    for paragraph in every_paragraph(tmp_path):
        for cited in paragraph.cited:
            assert cited.sources, cited.text
            for source in cited.sources:
                assert source.endpoint and source.fields, cited.text


def test_no_numeric_token_in_the_text_is_unaccounted_for(tmp_path):
    """The verifier's own claim, checked independently of the verifier."""
    for paragraph in every_paragraph(tmp_path):
        allowed = {t for c in paragraph.cited for t in c.tokens}
        assert not [t for t in par.TOKEN.findall(paragraph.text) if t not in allowed]


def test_a_threshold_is_cited_to_the_state_file_not_to_an_endpoint():
    cited = {c.what: c for c in render_symbol("LIFE").cited}
    bar = cited["ambang volume"]
    assert [s.origin for s in bar.sources] == ["state"]
    assert bar.sources[0].endpoint == profile_mod.THRESHOLDS_FILE


def test_the_run_date_is_not_attributed_to_an_endpoint(tmp_path):
    """No window means the history bound is the clock, and it says so.

    Citing it to `/v2/suspensions/` would pass every check in this file while
    telling the reader something untrue about where the date came from.
    """
    paragraph = unavailable(tmp_path)
    bound = [c for c in paragraph.cited if c.what == "batas riwayat"]
    assert bound and all(s.origin == "profile" for s in bound[0].sources)


def test_the_paragraph_lists_every_source_it_rests_on():
    endpoints = {s.endpoint for s in render_symbol("LIFE").sources}
    assert {"/v2/broker-summary/{symbol}/top/", "/v2/brokers/", "/v2/daily/{symbol}/",
            "/v2/news/", "/v2/suspensions/",
            profile_mod.THRESHOLDS_FILE} <= endpoints


def test_a_repeated_figure_is_cited_once():
    """The same measurement quoted twice is one source line, not two."""
    cited = render_symbol("LIFE").cited
    assert len(cited) == len({(c.text, c.what) for c in cited})


# --- fail closed ------------------------------------------------------------
def test_an_uncited_number_is_refused_not_invented(monkeypatch):
    """A clause that writes a figure without registering it stops the output.

    Patched at the clause, so the refusal is proven on the path a real edit would
    take — not by hand-building a `Paragraph` the renderer would never produce.
    """
    def rogue(reading, phrase):
        return "harganya bergerak 12% dalam sepekan", "momentum 12%"

    monkeypatch.setitem(par.CLAUSES, "momentum", rogue)
    with pytest.raises(UncitedNumberError) as excinfo:
        render_symbol("LIFE")
    assert "12" in str(excinfo.value)


def test_the_refusal_names_the_symbol_and_the_orphan_number():
    paragraph = Paragraph(symbol="LIFE", sentences=("Volumenya 24,5x median.",))
    with pytest.raises(UncitedNumberError) as excinfo:
        verify(paragraph)
    assert "LIFE" in str(excinfo.value) and "24,5" in str(excinfo.value)


def test_a_citation_without_a_source_is_refused():
    """Registering the figure is not enough — it has to point somewhere."""
    paragraph = Paragraph(symbol="LIFE", sentences=("Volumenya 24,5x median.",),
                          cited=(Cited("24,5x", "rasio volume", ()),))
    with pytest.raises(UncitedNumberError):
        verify(paragraph)


def test_a_citation_with_an_empty_field_list_is_refused():
    """An endpoint with no field is a gesture at provenance, not provenance."""
    source = profile_mod.Source("/v2/daily/{symbol}/", ())
    paragraph = Paragraph(symbol="LIFE", sentences=("Volumenya 24,5x median.",),
                          cited=(Cited("24,5x", "rasio volume", (source,)),))
    with pytest.raises(UncitedNumberError):
        verify(paragraph)


def test_a_dated_fact_counts_as_a_number_too():
    """`2025-08-22` is as checkable as `24,5x`, and is checked the same way."""
    paragraph = Paragraph(symbol="LIFE",
                          sentences=("Terakhir pada 2025-08-22.",))
    with pytest.raises(UncitedNumberError):
        verify(paragraph)


def test_a_paragraph_with_no_numbers_at_all_passes():
    """Fail-closed is about unattributed figures, not about prose."""
    assert verify(Paragraph(symbol="LIFE",
                            sentences=("Data tidak tersedia untuk LIFE.",)))


# --- descriptive only, per red-team.md §D11 ---------------------------------
def test_the_banned_list_holds_the_words_the_rule_names():
    """§D11's vocabulary, written down so the ban is data rather than discipline."""
    for word in ("beli", "jual", "aman", "bahaya", "rekomendasi", "target harga",
                 "merah", "hijau"):
        assert word in par.BANNED


def test_no_banned_vocabulary_in_any_output(tmp_path):
    for paragraph in every_paragraph(tmp_path):
        assert par.banned_words_in(paragraph.text) == [], paragraph.symbol


def test_no_banned_vocabulary_across_the_whole_watchlist():
    """Every symbol the daily cycle can render, not only the three in the demo."""
    from app import config

    for symbol in config.WATCHLIST:
        assert par.banned_words_in(render_symbol(symbol).text) == [], symbol


def test_no_banned_vocabulary_in_the_serialised_form(tmp_path):
    for paragraph in every_paragraph(tmp_path):
        payload = json.dumps(paragraph.to_dict(), ensure_ascii=False)
        assert par.banned_words_in(payload) == [], paragraph.symbol


def test_a_verdict_word_stops_the_output():
    paragraph = Paragraph(symbol="LIFE", sentences=("Sahamnya aman.",))
    with pytest.raises(BannedVocabularyError):
        verify(paragraph)


def test_the_ban_is_on_the_verdict_not_on_the_letters():
    """`pembeli` and `penjualan` contain the banned strings and are not verdicts."""
    assert par.banned_words_in("pembeli dan penjualan di halaman itu") == []


def test_the_output_carries_no_ranking_or_single_score(tmp_path):
    """A count of axes, never a figure that reads as a rating."""
    for paragraph in every_paragraph(tmp_path):
        lowered = paragraph.text.lower()
        assert "skor" not in lowered and "peringkat" not in lowered


# --- history is a dated fact, not a charge ----------------------------------
def test_suspension_history_is_dated_and_sourced():
    paragraph = render_symbol("LIFE")
    assert "2025-08-22" in paragraph.text
    dated = [c for c in paragraph.cited if c.text == "2025-08-22"]
    assert dated and dated[0].sources[0].endpoint == "/v2/suspensions/"


def test_suspension_history_states_the_announcement_not_a_conclusion():
    text = render_symbol("LIFE").text
    assert "IDX tercatat menghentikan perdagangan" in text
    assert par.banned_words_in(text) == []


def test_a_symbol_with_no_record_says_so_rather_than_implying_one(tmp_path):
    assert "tidak ada suspensi" in unavailable(tmp_path).text


def test_a_halted_symbol_names_the_announcement_and_its_date(tmp_path):
    text = halted(tmp_path).text
    assert "berhenti diperdagangkan" in text
    assert "2026-08-10" in text
    assert "bukan tidak ada temuan" in text


# --- missing data is not zero -----------------------------------------------
def test_missing_data_says_data_tidak_tersedia(tmp_path):
    assert "data tidak tersedia" in unavailable(tmp_path).text.lower()


def test_missing_data_reports_no_number_at_all(tmp_path):
    """Not "0 dari 4" — an unmeasured axis has no reading to print, including zero."""
    paragraph = unavailable(tmp_path)
    first_two = " ".join(paragraph.sentences[:2])
    assert par.TOKEN.findall(first_two) == []
    assert "tidak terukur" in first_two


def test_missing_data_says_why_zero_would_be_wrong(tmp_path):
    assert "bukan pengukuran yang menghasilkan nol" in unavailable(tmp_path).text


# --- the disclaimer travels with the sentences ------------------------------
def test_every_output_carries_the_disclaimer(tmp_path):
    for paragraph in every_paragraph(tmp_path):
        assert paragraph.disclaimer == par.DISCLAIMER
        assert par.DISCLAIMER in paragraph.text


def test_the_disclaimer_survives_serialisation_and_printing(tmp_path):
    paragraph = unavailable(tmp_path)
    assert par.DISCLAIMER in json.dumps(paragraph.to_dict(), ensure_ascii=False)
    assert par.DISCLAIMER.split(":")[0] in par.describe(paragraph)


def test_the_disclaimer_says_the_output_is_descriptive():
    assert "Deskriptif" in par.DISCLAIMER
    assert par.banned_words_in(par.DISCLAIMER) == []


# --- it is prose, not a dashboard -------------------------------------------
def test_the_rendered_block_is_prose_with_its_sources_underneath():
    block = par.describe(render_symbol("LIFE"))
    assert "sumber tiap angka:" in block
    assert "/v2/daily/{symbol}/" in block


def test_nothing_here_draws():
    """Track 03 disqualifies re-displaying the API. No chart, no colour, no bars."""
    import inspect

    source = inspect.getsource(par).lower()
    for word in ("matplotlib", "plotly", "seaborn", "<html", "<svg", "\\x1b["):
        assert word not in source
