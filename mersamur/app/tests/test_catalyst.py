"""The catalyst axis, and the four ways it would go wrong quietly.

Each test is built to fail against the plausible wrong implementation rather than
merely to pass against the right one:

  * **collapsing "no articles" into "no fundamental articles".** They are opposite
    findings — one is missing data, the other is a measurement — and a `ratio` of
    `0.0` for a symbol nobody wrote about is a fabricated result.
    `test_no_articles_is_not_zero_fundamental` pins `None` against `0.0`.
  * **counting an unclassified article as non-fundamental evidence.** Three of the
    thirty recorded articles come back with `dimension: null`. They are carried as
    `n_unclassified` rather than silently swelling the denominator's negative side.
  * **letting an article dated after the cutoff into the feature.** The whole axis is
    news about a price move, so the article describing the halt is the single most
    tempting leak in the product. `before` is exclusive, same-day included.
  * **treating `valuation` as fundamental.** A valuation note is a reading of the
    price, not a reported reason behind it. §Q2's own tally separates them.

Zero credits: everything reads `research/harness/recorded/` or a temp directory.
`test_missing_news_raises_instead_of_fetching` is the one that proves no socket is
opened.
"""
import json
import re
from datetime import date, datetime

import pytest

from app import cache as cache_mod
from app.axes import catalyst
from app.axes.catalyst import (
    DIMENSIONS,
    FUNDAMENTAL_DIMENSIONS,
    Article,
    NoNewsDataError,
    articles,
    news_params,
    parse_timestamp,
    score,
)
from app.cache import Cache

RECORDED_BATCH = {"limit": 30,
                  "symbols": "ASLI,LIFE,NICK,TRUK,PPGL,SAFE,PACK,CSMI,TMPO,AGAR"}


def recorded_rows():
    """The captured batch, read straight off disk — the independent yardstick.

    Recomputing the expected counts from the raw payload rather than hardcoding them
    means the test measures the axis against the recording, not against a number that
    was copied out of the axis.
    """
    hit = Cache().get(catalyst.NEWS_PATH, RECORDED_BATCH)
    assert hit is not None and hit.found, "rekaman /v2/news/ batch tidak ditemukan"
    return hit.payload["results"]


def rows_for(symbol, rows=None):
    rows = recorded_rows() if rows is None else rows
    return [r for r in rows if f"{symbol}.JK" in (r.get("symbols") or [])]


def is_fundamental(row):
    dim = row.get("dimension") or {}
    return any((dim.get(name) or 0) > 0 for name in FUNDAMENTAL_DIMENSIONS)


def build_cache(tmp_path, batches=()):
    """A recorded corpus of `/v2/news/` batches, written the way `capture.py` writes it."""
    manifest = {}
    for params, payload in batches:
        key = cache_mod.slug(catalyst.NEWS_PATH, params)
        (tmp_path / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")
        manifest[key] = {"path": catalyst.NEWS_PATH, "params": params, "status": 200,
                         "est_cost": 1, "fetched_at": 0, "cost_headers": {}}
    (tmp_path / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return Cache(root=str(tmp_path))


def article_row(symbol, when, title="berita", dimension=None, source=None):
    return {"title": title, "body": "x" * 500, "source": source or f"https://x/{title}",
            "timestamp": when, "sector": "basic-materials", "tags": [],
            "symbols": [f"{symbol}.JK"],
            "dimension": dimension if dimension is None or dimension == {}
            else {name: dimension.get(name, 0) for name in DIMENSIONS}}


def page(rows, has_next=False, total=None):
    return {"results": list(rows),
            "pagination": {"total_count": total if total is not None else len(rows),
                           "showing": len(rows), "has_next": has_next}}


# --- the headline number ----------------------------------------------------
def test_life_article_count_matches_the_task_figure():
    """The task's own criterion: LIFE shows 8 articles in the recording."""
    result = score("LIFE")
    assert result.n_articles == 8
    assert result.n_articles == len(rows_for("LIFE"))


def test_life_fundamental_count_is_what_the_recording_holds():
    """LIFE reads **1** fundamental article, not the 2 the task's criterion states.

    Recomputed from the payload rather than asserted from the axis, so the number is
    the recording's and not the implementation's. Of LIFE's eight articles exactly one
    carries `future`/`financials` above zero (`2026-08-31`, future 1 · financials 2).
    A second article (`2026-09-04`) carries `valuation 2` and no fundamental score —
    which is where a count of 2 comes from if `valuation` is folded in, and §Q2 keeps
    it out on purpose. Discrepancy reported rather than papered over; the formula in
    the task body and `riset/spec.md` §5 is the one implemented.
    """
    expected = sum(1 for r in rows_for("LIFE") if is_fundamental(r))
    assert expected == 1
    assert score("LIFE").n_fundamental == expected


def test_valuation_alone_is_not_a_catalyst():
    """A `valuation`-only article is coverage of the price, not a reported reason."""
    item = Article(dimension=tuple((n, 2 if n == "valuation" else 0) for n in DIMENSIONS))
    assert item.fundamental is False
    assert item.technical_only is False       # no technical score either


def test_the_ratio_is_fundamental_over_total():
    result = score("LIFE")
    assert result.ratio == pytest.approx(result.n_fundamental / result.n_articles)
    assert result.status == "ada_fundamental"


def test_technical_coverage_dominates_as_the_feasibility_note_found():
    """§Q2's shape: most of the coverage discusses the move, not a reason for it."""
    result = score("LIFE")
    counts = dict(result.dimension_counts)
    assert counts["technical"] > counts["financials"]
    assert result.n_technical_only > result.n_fundamental


# --- the three states, kept apart -------------------------------------------
def test_no_articles_is_not_zero_fundamental(tmp_path):
    """Nothing measured reads `None`; measured-and-zero reads `0.0`. Never merged."""
    cache = build_cache(tmp_path, [({"symbols": "AAAA,BBBB"},
                                    page([article_row("BBBB", "2026-09-01T08:00:00")]))])
    empty = score("AAAA", cache=cache)
    assert empty.n_articles == 0
    assert empty.ratio is None
    assert empty.status == "tanpa_artikel"

    covered = score("BBBB", cache=cache)
    assert covered.n_articles == 1
    assert covered.ratio == 0.0
    assert covered.status == "tanpa_fundamental"


def test_articles_with_a_fundamental_dimension_are_the_third_state(tmp_path):
    cache = build_cache(tmp_path, [({"symbols": "CCCC"}, page([
        article_row("CCCC", "2026-09-01T08:00:00", "teknikal", {"technical": 2}),
        article_row("CCCC", "2026-09-02T08:00:00", "fundamental", {"financials": 2}),
    ]))])
    result = score("CCCC", cache=cache)
    assert (result.n_articles, result.n_fundamental) == (2, 1)
    assert result.ratio == 0.5
    assert result.status == "ada_fundamental"


def test_a_null_dimension_is_unclassified_not_non_fundamental(tmp_path):
    """3 of the 30 recorded articles come back with `dimension: null`. Carried apart."""
    cache = build_cache(tmp_path, [({"symbols": "DDDD"}, page([
        article_row("DDDD", "2026-09-01T08:00:00", "tanpa dimensi", None),
        article_row("DDDD", "2026-09-02T08:00:00", "fundamental", {"future": 1}),
    ]))])
    result = score("DDDD", cache=cache)
    assert result.n_unclassified == 1
    assert result.n_fundamental == 1
    assert "dimension null" in str(result)
    # and the recording really does hold such rows
    assert sum(1 for r in recorded_rows() if r.get("dimension") is None) == 3


# --- leak safety ------------------------------------------------------------
def test_an_article_dated_after_the_cutoff_never_counts(tmp_path):
    """The task's criterion: nothing published on or after the event date enters."""
    cache = build_cache(tmp_path, [({"symbols": "EEEE"}, page([
        article_row("EEEE", "2026-09-01T08:00:00", "sebelum", {"financials": 2}),
        article_row("EEEE", "2026-09-05T08:00:00", "hari peristiwa", {"financials": 2}),
        article_row("EEEE", "2026-09-08T08:00:00", "sesudah", {"financials": 2}),
    ]))])
    cutoff = date(2026, 9, 5)
    result = score("EEEE", cache=cache, before=cutoff)
    assert result.n_articles == 1
    assert result.top_fundamental == ("sebelum",)
    assert all(a.date < cutoff for a in articles("EEEE", cache=cache, before=cutoff)[0])
    assert f"artikel sejak {cutoff.isoformat()} tidak dihitung" in str(result)

    # the same-day article is only visible without a cutoff
    assert score("EEEE", cache=cache).n_articles == 3


def test_the_cutoff_holds_on_the_real_recording():
    """LIFE's window collapses as the cutoff walks back through it."""
    assert score("LIFE", before=date(2026, 9, 3)).n_articles == 4
    assert score("LIFE", before=date(2026, 8, 31)).n_articles == 0
    assert score("LIFE", before=date(2026, 8, 31)).ratio is None


def test_after_is_inclusive_like_labels_events(tmp_path):
    cache = build_cache(tmp_path, [({"symbols": "FFFF"}, page([
        article_row("FFFF", "2026-09-01T08:00:00", "lama"),
        article_row("FFFF", "2026-09-02T08:00:00", "baru"),
    ]))])
    found, _truncated, _total = articles("FFFF", cache=cache, after=date(2026, 9, 2))
    assert [a.title for a in found] == ["baru"]


# --- reading the recording --------------------------------------------------
def test_missing_news_raises_instead_of_fetching(tmp_path):
    """An uncovered symbol is an error, never a silent 1-credit call."""
    cache = build_cache(tmp_path, [({"symbols": "GGGG"}, page([]))])
    with pytest.raises(NoNewsDataError):
        score("HHHH", cache=cache)


def test_a_truncated_page_is_reported_as_a_lower_bound():
    """The captured batch holds 30 of 112 rows, so every count is a floor."""
    result = score("LIFE")
    assert result.page_truncated is True
    assert result.total_count == 112
    assert "batas bawah" in str(result)


def test_symbols_are_matched_after_normalisation(tmp_path):
    """`LIFE.JK` in the payload, `life.jk` from the caller, one symbol."""
    cache = build_cache(tmp_path, [({"symbols": "IIII"},
                                    page([article_row("IIII", "2026-09-01T08:00:00")]))])
    assert score(" iiii.jk ", cache=cache).n_articles == 1


def test_duplicate_articles_across_recordings_are_counted_once(tmp_path):
    """Two batches naming the same symbol must not double the denominator."""
    row = article_row("JJJJ", "2026-09-01T08:00:00", "sama", source="https://x/sama")
    cache = build_cache(tmp_path, [({"symbols": "JJJJ,KKKK"}, page([row])),
                                   ({"symbols": "JJJJ"}, page([dict(row)]))])
    assert score("JJJJ", cache=cache).n_articles == 1


def test_an_undated_article_is_dropped(tmp_path):
    """Without a timestamp an article cannot be placed in a window, so it is not one."""
    cache = build_cache(tmp_path, [({"symbols": "LLLL"}, page([
        article_row("LLLL", None, "tanpa tanggal"),
        article_row("LLLL", "2026-09-01T08:00:00", "bertanggal"),
    ]))])
    assert score("LLLL", cache=cache).n_articles == 1


def test_parse_timestamp_forms():
    assert parse_timestamp("2026-09-08T07:00:00") == datetime(2026, 9, 8, 7, 0)
    assert parse_timestamp("2026-09-08") == datetime(2026, 9, 8)
    assert parse_timestamp("rusak") is None
    assert parse_timestamp(None) is None


# --- the live call, if one is ever bought -----------------------------------
def test_news_params_batches_symbols_into_one_call():
    """Many symbols, one call, one credit — never one call per symbol."""
    params = news_params(["life.jk", "ASLI"], start="2026-06-01", end="2026-09-01")
    assert params["symbols"] == "LIFE,ASLI"
    assert (params["start"], params["end"]) == ("2026-06-01", "2026-09-01")
    assert params["limit"] == catalyst.DEFAULT_LIMIT


def test_news_params_does_not_invent_a_window():
    """An omitted window stays omitted rather than being silently defaulted."""
    params = news_params("LIFE")
    assert "start" not in params and "end" not in params


# --- descriptive output -----------------------------------------------------
def test_the_description_never_gives_a_verdict():
    """Descriptive only. Matched on whole words — `rekaman` contains `aman`."""
    words = set(re.findall(r"[a-z]+", str(score("LIFE")).lower()))
    for banned in ("beli", "jual", "rekomendasi", "sinyal", "hindari", "aman",
                   "bahaya", "waspada"):
        assert banned not in words


def test_the_body_is_carried_as_an_extract(tmp_path):
    """~500 characters, verbatim. No summariser is built on top of it."""
    cache = build_cache(tmp_path, [({"symbols": "MMMM"},
                                    page([article_row("MMMM", "2026-09-01T08:00:00")]))])
    found, _truncated, _total = articles("MMMM", cache=cache)
    assert found[0].extract == found[0].body == "x" * catalyst.EXTRACT_CHARS
