"""Sumbu katalis — whether the coverage says *why* the price moved, or only *that* it did.

The first formulation of this axis was "there is no news", and the feasibility pass
on 9 September 2026 killed it (`riset/temuan-kelayakan.md` §Q2). All ten suspended
names had coverage — 112 articles for 10 symbols. Third-liner stocks are not dark.

What the same 30 articles do show is the shape of that coverage:

    technical 21 · valuation 7 · future 4 · financials 3 · ownership 3

Twenty-one of thirty articles are `technical` — reports *about the price move*, and
about the halt that followed it. Three are `financials`. So the axis measures the
**share of articles carrying a fundamental dimension**, not the presence of articles:

    ratio = #{articles with dimension.financials > 0 or dimension.future > 0} / #articles

A low ratio says the move was covered without a reported reason behind it. That is a
statement about the coverage, never about the company and never about what to do.

Three states, and they are deliberately not merged (`tasks/07-sumbu-katalis.md` §4):

  * **no articles at all** — nothing was measured. `ratio` is `None`, not `0.0`.
  * **articles, zero of them fundamental** — something *was* measured, and the answer
    is zero. `ratio` is `0.0`.
  * **articles with a fundamental dimension** — `ratio > 0`.

Collapsing the first two would report "no fundamental coverage" for a symbol nobody
wrote about, which is an absence of data dressed up as a finding.

A fourth case exists in the recording and is carried separately rather than folded
into either: `dimension` comes back **null** on 3 of the 30 articles. An unclassified
article is not a non-fundamental one, so `n_unclassified` is reported and `describe`
says so.

`dimension` is Sectors' own eight-theme score (`future`, `dividend`, `ownership`,
`technical`, `valuation`, `financials`, `management`, `sustainability`). It is
already computed; this module reads it and never builds a classifier. Likewise
`body` is a ~500-character extract, carried verbatim as an extract — no summariser
is built on top of it, and no news is scraped from anywhere: `/v2/news/` is complete
and classified, and scraping would break the eligibility test.

**Leak safety.** `score(symbol, before=...)` mirrors `labels.history_before`: `before`
is exclusive, so an article dated on or after the cutoff can never reach a feature.
Same-day articles are excluded too — a piece published the morning of the halt is
still the event talking about itself.

Zero credits: reads only `research/harness/recorded/`. `/v2/news/?symbols=` takes a
comma-separated list and bills **1 credit for the whole batch, not 1 per symbol**
(`news_params` builds that form), but nothing here calls it — `SectorsClient` is
never imported and no socket is opened.
"""
from dataclasses import dataclass
from datetime import date, datetime

from app import universe
from app.cache import Cache

AXIS = "catalyst"

NEWS_PATH = "/v2/news/"

# Sectors' eight themes, in the order the API returns them.
DIMENSIONS = ("future", "dividend", "ownership", "technical",
              "valuation", "financials", "management", "sustainability")

# The two that answer "is there a reported reason behind this move?". `valuation`
# is deliberately not among them: a valuation note is a reading of the price, not a
# fact about the business that moved it.
FUNDAMENTAL_DIMENSIONS = ("financials", "future")

# `body` is an extract of roughly this length, not an article. Recorded on purpose:
# a caller that finds it short should quote less, not summarise more.
EXTRACT_CHARS = 500

# The batch form is one credit however many symbols it names, so the product asks
# for the whole watchlist at once or not at all.
DEFAULT_LIMIT = 30


class NoNewsDataError(LookupError):
    """No settled `/v2/news/?symbols=` payload covering this symbol in the recording.

    Raised instead of fetching. The call bills a credit, so a missing batch is a
    decision for `capture.py` to make deliberately — never a side effect of scoring.
    """


# --- the live call, if one is ever bought -----------------------------------
def news_params(symbols, start=None, end=None, limit=DEFAULT_LIMIT):
    """Params for one batched `/v2/news/` call — many symbols, 1 credit.

    `start`/`end` are the window bound (§6 of the task). They are passed through as
    given rather than defaulted here: a silent default window would be the same
    class of bug as the bare `/v2/daily/` call that quietly returns 21 sessions.
    """
    names = symbols if isinstance(symbols, str) else ",".join(
        universe.normalize(s) for s in symbols)
    params = {"symbols": names, "limit": int(limit)}
    if start is not None:
        params["start"] = str(start)
    if end is not None:
        params["end"] = str(end)
    return params


# --- reading the recording --------------------------------------------------
def parse_timestamp(text):
    """`2026-09-08T07:00:00` to a `datetime`, or None when the row carries no date."""
    if not isinstance(text, str):
        return None
    raw = text.strip().replace("Z", "").replace(" ", "T")
    for length in (19, 16, 10):
        try:
            return datetime.fromisoformat(raw[:length])
        except ValueError:
            continue
    return None


@dataclass(frozen=True)
class Article:
    """One `/v2/news/` row. Immutable — nobody re-classifies it.

    `dimension` is `None` when the API returned null for it. That is not the same as
    an all-zero dimension object, and `classified` is the property that keeps the two
    apart.
    """

    title: str = ""
    body: str = ""
    source: str = ""
    published: datetime = None
    sector: str = ""
    tags: tuple = ()
    symbols: tuple = ()
    dimension: tuple = None      # ((name, score), ...) or None when unclassified

    @property
    def key(self):
        """Identity across overlapping recordings: same link, same headline, same time."""
        return (self.source, self.title, self.published)

    @property
    def date(self):
        return self.published.date() if self.published else None

    @property
    def classified(self):
        """False when the API returned `dimension: null` for this article."""
        return self.dimension is not None

    @property
    def scores(self):
        return dict(self.dimension or ())

    @property
    def fundamental(self):
        """`financials > 0` or `future > 0`. False for an unclassified article.

        False, not None: an unclassified article cannot be counted as a reported
        reason. It is carried separately as `n_unclassified` so the reader is told
        how much of the denominator is unknown rather than negative.
        """
        scores = self.scores
        return any((scores.get(name) or 0) > 0 for name in FUNDAMENTAL_DIMENSIONS)

    @property
    def technical_only(self):
        """Covers the price move and nothing fundamental — §Q2's dominant shape."""
        return (self.scores.get("technical") or 0) > 0 and not self.fundamental

    @property
    def extract(self):
        """The ~500-character body, verbatim. An extract; never summarise it."""
        return self.body


def _article(row):
    dimension = row.get("dimension")
    scores = None
    if isinstance(dimension, dict):
        scores = tuple((name, dimension.get(name) or 0) for name in DIMENSIONS)
    return Article(
        title=str(row.get("title") or ""),
        body=str(row.get("body") or ""),
        source=str(row.get("source") or ""),
        published=parse_timestamp(row.get("timestamp")),
        sector=str(row.get("sector") or ""),
        tags=tuple(row.get("tags") or ()),
        symbols=tuple(universe.normalize(s) for s in (row.get("symbols") or ())),
        dimension=scores,
    )


def _rows(payload):
    """The article rows, whichever envelope the payload uses."""
    if isinstance(payload, dict):
        payload = payload.get("results") or payload.get("data") or []
    return [r for r in (payload or []) if isinstance(r, dict)]


def _truncated(payload):
    """True when the recording holds one page of a longer result set.

    `pagination.has_next` was true on the captured batch — 30 rows of 112 — so every
    count derived from it is a **lower bound**, and saying so is the difference
    between a measurement and a guess.
    """
    if not isinstance(payload, dict):
        return False, None
    page = payload.get("pagination") or {}
    return bool(page.get("has_next")), page.get("total_count")


def _batches_naming(symbol, source):
    """Settled `/v2/news/` recordings whose `symbols` param names `symbol`.

    Only the `?symbols=` form is read. The general `?extension=idx` feed is a
    different question — the market's front page, not this symbol's coverage — and
    mixing the two would make a ratio whose denominator depends on which feeds
    happened to be captured.
    """
    out = []
    for entry in source.manifest().values():
        if (entry.get("path") or "") != NEWS_PATH:
            continue
        params = entry.get("params") or {}
        named = [universe.normalize(s) for s in str(params.get("symbols") or "").split(",")]
        if symbol in named:
            out.append(params)
    out.sort(key=lambda p: sorted(p.items()))
    return out


def articles(symbol, cache=None, before=None, after=None):
    """Recorded articles mentioning `symbol`, newest first.

    `before` is exclusive and `after` inclusive — the same convention as
    `labels.events`, so a window bound here means what it means there. Duplicates
    across overlapping recordings are dropped by `Article.key`.
    """
    want = universe.normalize(symbol)
    source = cache if cache is not None else Cache()

    forms = _batches_naming(want, source)
    if not forms:
        raise NoNewsDataError(
            f"Tidak ada rekaman /v2/news/?symbols= yang memuat {want!r}. "
            f"Panggilan ini berbiaya 1 kredit untuk seluruh daftar simbol dan tidak "
            f"dijalankan diam-diam — ambil lewat capture.py."
        )

    seen, found, truncated, total = set(), [], False, None
    for params in forms:
        hit = source.get(NEWS_PATH, params)
        if hit is None or not hit.found:
            continue
        page_truncated, page_total = _truncated(hit.payload)
        truncated = truncated or page_truncated
        total = page_total if total is None else total
        for row in _rows(hit.payload):
            item = _article(row)
            if want not in item.symbols:
                continue
            if item.published is None:
                continue          # an undated article cannot be placed in a window
            if before is not None and item.date >= before:
                continue          # leak guard: on or after the cutoff is the future
            if after is not None and item.date < after:
                continue
            if item.key in seen:
                continue
            seen.add(item.key)
            found.append(item)

    found.sort(key=lambda a: a.published, reverse=True)
    return tuple(found), truncated, total


# --- the result -------------------------------------------------------------
@dataclass(frozen=True)
class Catalyst:
    """One symbol's coverage quality. Immutable — no re-scoring.

    `ratio` is `None` when there were no articles and `0.0` when there were articles
    and none of them fundamental. Those are different findings and the type keeps
    them apart.
    """

    symbol: str
    window_start: str = ""
    window_end: str = ""
    cutoff: str = ""
    n_articles: int = 0
    n_fundamental: int = 0
    n_technical_only: int = 0
    n_unclassified: int = 0
    ratio: float = None
    dimension_counts: tuple = ()
    page_truncated: bool = False
    total_count: int = None
    top_fundamental: tuple = ()

    @property
    def status(self):
        """`tanpa_artikel` · `tanpa_fundamental` · `ada_fundamental`. Descriptive only."""
        if self.n_articles == 0:
            return "tanpa_artikel"
        if self.n_fundamental == 0:
            return "tanpa_fundamental"
        return "ada_fundamental"

    def __str__(self):
        return describe(self)


def score(symbol, cache=None, before=None, after=None):
    """Measure the catalyst axis for one symbol. Reads the recording only.

    No threshold is read and nothing fires: `state/thresholds.json` carries no bar
    for this axis (`riset/spec.md` §5 lists it with `threshold: null`), and inventing
    one here would be exactly the hardcoded constant the package refuses.
    """
    want = universe.normalize(symbol)
    found, truncated, total = articles(want, cache=cache, before=before, after=after)

    fundamental = [a for a in found if a.fundamental]
    counts = tuple((name, sum(1 for a in found if (a.scores.get(name) or 0) > 0))
                   for name in DIMENSIONS)

    return Catalyst(
        symbol=want,
        window_start=found[-1].date.isoformat() if found else "",
        window_end=found[0].date.isoformat() if found else "",
        cutoff=before.isoformat() if isinstance(before, date) else (before or ""),
        n_articles=len(found),
        n_fundamental=len(fundamental),
        n_technical_only=sum(1 for a in found if a.technical_only),
        n_unclassified=sum(1 for a in found if not a.classified),
        # None when nothing was measured; 0.0 when something was and the answer is zero.
        ratio=(len(fundamental) / len(found)) if found else None,
        dimension_counts=counts,
        page_truncated=truncated,
        total_count=total,
        top_fundamental=tuple(a.title for a in fundamental[:3]),
    )


# --- description ------------------------------------------------------------
def _id(value):
    """Format a number the Indonesian way: comma as the decimal separator."""
    return str(value).replace(".", ",")


def describe(result):
    """A descriptive account of one symbol's coverage. No verdict, no colour."""
    lines = [f"Katalis {result.symbol} — kualitas liputan (0 kredit, dari rekaman)"]
    if result.cutoff:
        lines.append(f"  batas kebocoran  : artikel sejak {result.cutoff} tidak dihitung")

    if result.n_articles == 0:
        lines += [
            "  artikel          : tidak ada satu pun di jendela ini",
            f"  rasio fundamental: tidak terukur — tanpa artikel tidak ada penyebut",
            f"  status           : {result.status}",
            "  Ini ketiadaan data, bukan temuan tentang emitennya.",
        ]
        return "\n".join(lines)

    named = ", ".join(f"{n} {c}" for n, c in result.dimension_counts if c)
    lines += [
        f"  jendela          : {result.window_start} .. {result.window_end}",
        f"  artikel          : {result.n_articles}"
        + (f" (halaman terpotong dari {result.total_count} hasil — angka ini batas bawah)"
           if result.page_truncated else ""),
        f"  berdimensi fundamental: {result.n_fundamental} "
        f"({' atau '.join(FUNDAMENTAL_DIMENSIONS)} > 0)",
        f"  hanya teknikal   : {result.n_technical_only} — membahas pergerakan harga, "
        f"bukan alasan di baliknya",
        f"  rasio fundamental: {_id('%.2f' % result.ratio)}",
        f"  dimensi terisi   : {named or 'tidak ada dimensi bernilai di atas nol'}",
    ]
    if result.n_unclassified:
        lines.append(f"  tanpa klasifikasi: {result.n_unclassified} artikel datang dengan "
                     f"dimension null — tidak terhitung fundamental maupun teknikal")
    for title in result.top_fundamental:
        lines.append(f"  artikel fundamental: {title}")
    lines += [
        f"  status           : {result.status}",
        "  Angka ini deskriptif: bentuk liputan atas saham itu, bukan penilaian atas "
        "emitennya maupun anjuran tindakan.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    for arg in (sys.argv[1:] or ["LIFE"]):
        print(score(arg))
        print()
