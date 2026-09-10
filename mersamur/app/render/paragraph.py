"""The profile turned into Indonesian prose, with a fail-closed citation check.

`app/profile.py` produces the measurement: four axes, three states each, every
figure carrying the endpoint and fields it came from. This module is the surface a
person actually reads. It is deliberately not a dashboard — Track 03 disqualifies
"a product that only displays raw Sectors data in a different visual form", and a
bar chart of `top_buyers[].buy_idr` is exactly that. The output is two or three
sentences.

## What changed from `tools/profile_demo.py`

The prototype worked and proved the shape, but it wrote one long sentence that
chained every finding with commas — by the fourth clause the reader had lost the
first. Three fixes, and they are the whole point of this module:

  * **two or three sentences, not one.** `SENTENCE_WORD_CEILING` is enforced by the
    tests, so a future edit cannot quietly grow them back.
  * **the first sentence names the most prominent thing.** The prototype emitted
    findings in the order the code computed them, so a 24,5x volume reading could
    end up third behind a ratio barely over its bar. `_lead()` ranks by how far past
    its own threshold each axis landed, and that axis opens the paragraph.
  * **numbers are spoken.** `Rp9,9 miliar`, not `9923485000`; `147.000 lembar`, not
    `147000.0`.

## The verifier, and why it refuses rather than guesses

Every figure that reaches the text is registered as a `Cited` — the exact rendered
string, what it measures, and the `profile.Source` list behind it. `verify()` then
walks the *finished text*, pulls every numeric token out of it, and requires each
one to have been registered. A number nobody claimed raises `UncitedNumberError`
and no output is produced.

Fail-closed is the deliberate choice. The failure mode it exists for is a later
edit that writes `f"naik {pct}% dalam sepekan"` from a local variable and ships a
plausible figure with nothing behind it — plausible is precisely the problem, since
a reader cannot tell it from the checked ones. Refusing to render is loud and
recoverable; a rendered guess is neither.

The same walk enforces `BANNED`. `riset/red-team.md` §D11 rules out verdicts,
recommendations, and red/green colour outright, for the exchange's reasons as much
as the project's: this text can name a live ticker, and a public video showing one
beside a verdict is a legal exposure for the team and the organiser. Suspension
history is stated the way §D11 requires — a dated fact with its announcement,
never an accusation.

Zero credits: everything here reads a `Profile` plus `research/harness/recorded/`.
No socket is opened.
"""
import re
import textwrap
from dataclasses import dataclass

from app import config, profile as profile_mod
from app.axes import history as history_axis

# --- the rule from red-team.md §D11, written as data -------------------------
# Verdict vocabulary and colour-as-verdict. Matched on word boundaries so
# `pembeli`, `penjualan` or `halaman` inside an ordinary word is not a false hit —
# what is banned is the verdict, not the letters.
BANNED = (
    "beli", "jual", "aman", "bahaya", "berbahaya", "rekomendasi", "target harga",
    "merah", "hijau", "waspada", "layak", "hindari", "buy", "sell",
    "gorengan", "digoreng", "manipulasi", "pompa", "pasti naik", "pasti turun",
)

# Attached to every rendered paragraph, not only to the README. A paragraph gets
# forwarded, screenshotted and pasted into chats on its own; the disclaimer has to
# travel with the sentences or it is not attached to anything that matters.
DISCLAIMER = ("Deskriptif, bukan anjuran investasi: angka di atas adalah catatan "
              "atas respons Sectors API pada jendela yang disebut, bukan penilaian "
              "atas emitennya.")

# The prototype's failure was length. Enforced by the tests, not by good intentions.
SENTENCE_WORD_CEILING = 46
MAX_SENTENCES = 3

# Axis names as prose. `profile.AXES` holds the machine names; these are what a
# reader who never saw the code should see.
AXIS_PROSE = {
    "concentration": "konsentrasi broker",
    "volume_anomaly": "volume",
    "momentum": "momentum",
    "catalyst": "katalis",
    "history": "riwayat",
}

# The history bound when there is no daily window to take it from: `Profile.cutoff`
# falls back to the run date, and no endpoint ever returned that. Cited as what it
# actually is — a citation naming the wrong source is worse than a loud refusal,
# because it survives the check that exists to catch exactly this.
CUTOFF_SOURCE = profile_mod.Source("app/profile.py", ("Profile.cutoff",),
                                   origin="profile")

# Every numeric run in the text: digits plus the separators a number or a date may
# contain. `2026-08-10` is one token, `24,5` is one token, `147.000` is one token.
TOKEN = re.compile(r"[0-9][0-9.,:-]*[0-9]|[0-9]")


class UncitedNumberError(ValueError):
    """A figure reached the text with no endpoint and field behind it."""


class BannedVocabularyError(ValueError):
    """The text carries verdict or colour vocabulary. §D11 forbids both."""


# --- speaking numbers --------------------------------------------------------
def _localize(text):
    """`9,923,485.0` -> `9.923.485,0`. Indonesian separators, one swap."""
    return text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def desimal(value, places=1):
    return _localize(f"{value:,.{places}f}")


def ribuan(value):
    """A count of things: thousands separated, no decimals."""
    return _localize(f"{round(value):,d}")


def persen(value, places=1):
    """A ratio spoken as a percentage. `0.8381...` -> `83,8%`."""
    return desimal(value * 100, places) + "%"


def kali(value, places=1):
    """A multiple. `24.5` -> `24,5x`."""
    return desimal(value, places) + "x"


def rupiah(value):
    """`9923485000.0` -> `Rp9,9 miliar`. A number a person can hold in their head.

    The prototype's `1200000000000` is technically the same information and
    practically useless: nobody counts twelve digits, so the reader either skips it
    or miscounts it, and a miscounted figure is worse than an absent one.
    """
    magnitude = abs(value)
    for divisor, unit in ((1e12, "triliun"), (1e9, "miliar"), (1e6, "juta")):
        if magnitude >= divisor:
            return f"Rp{desimal(value / divisor, 1)} {unit}"
    return "Rp" + ribuan(value)


# --- citations ---------------------------------------------------------------
@dataclass(frozen=True)
class Cited:
    """One figure as it appears in the text, and where it came from.

    `text` is the rendered string, character for character, so the verifier can
    match it against the finished paragraph rather than against an intention.
    """

    text: str
    what: str
    sources: tuple = ()

    @property
    def tokens(self):
        return tuple(TOKEN.findall(self.text))

    def to_dict(self):
        return {"angka": self.text, "yang_diukur": self.what,
                "sumber": [s.to_dict() for s in self.sources]}

    def __str__(self):
        where = " · ".join(
            f"{s.endpoint} ({', '.join(s.fields)})" for s in self.sources)
        return f"{self.text} — {self.what} · {where}"


class Phrase:
    """Collects the figures a clause emits while the clause is being written.

    `n()` returns the rendered string so it can go straight into an f-string, and
    keeps the citation. The two cannot drift apart because they are the same call —
    which is the only reason a writer never has to remember to register anything.
    """

    def __init__(self):
        self.cited = []

    def n(self, text, what, sources):
        """Register one figure and return it, so the text and the citation are
        produced by the same call and cannot drift apart.

        A figure quoted twice — once in the leading clause, once in the summary —
        is one citation, not two: the list under the paragraph is for the reader,
        and a repeated line there reads as two different measurements.
        """
        entry = Cited(text=text, what=what, sources=tuple(sources))
        if entry not in self.cited:
            self.cited.append(entry)
        return text


def _context(reading, name):
    """One named context entry from a reading: `(value, sources)`, or `(None, ())`."""
    for entry_name, value, _unit, sources in reading.context:
        if entry_name == name:
            return value, sources
    return None, ()


def _axis_sources(profile):
    """Every source the counted axes rest on, deduplicated. Backs the axis count."""
    seen, out = set(), []
    for reading in profile.counted:
        for source in reading.sources:
            key = (source.origin, source.endpoint, source.fields)
            if key not in seen:
                seen.add(key)
                out.append(source)
    return tuple(out)


# --- the clauses, one per axis ----------------------------------------------
def _concentration(reading, phrase):
    panel, panel_src = _context(reading, "nilai_panel_idr")
    lead = (f"pangsa akumulasi broker teratas mencapai "
            f"{phrase.n(persen(reading.value), 'pangsa broker teratas', reading.sources)}")
    if panel:
        lead += (f" dari {phrase.n(rupiah(panel), 'nilai panel broker', panel_src)} "
                 f"nilai panel")
    lead += (f", dengan ambang "
             f"{phrase.n(persen(reading.threshold), 'ambang konsentrasi', reading.threshold_sources)}")
    short = (f"konsentrasi broker "
             f"{phrase.n(persen(reading.value), 'pangsa broker teratas', reading.sources)}")
    return lead, short


def _volume(reading, phrase):
    last, last_src = _context(reading, "volume_sesi_terakhir")
    median, median_src = _context(reading, "baseline_median")
    traded, traded_src = _context(reading, "sesi_bertransaksi")
    lead = (f"sesi terakhir tercatat "
            f"{phrase.n(kali(reading.value), 'rasio volume terhadap median', reading.sources)} "
            f"median")
    if traded:
        lead += (f" {phrase.n(str(traded), 'sesi bertransaksi di jendela', traded_src)} "
                 f"sesi bertransaksi sebelumnya")
    if last is not None and median:
        lead += (f" — {phrase.n(ribuan(last), 'volume sesi terakhir', last_src)} lembar "
                 f"terhadap {phrase.n(ribuan(median), 'median volume', median_src)} lembar")
    lead += (f", dengan ambang "
             f"{phrase.n(kali(reading.threshold), 'ambang volume', reading.threshold_sources)}")
    short = (f"volume "
             f"{phrase.n(kali(reading.value), 'rasio volume terhadap median', reading.sources)} "
             f"median")
    return lead, short


def _momentum(reading, phrase):
    lead = (f"kenaikan lima sesi berada di persentil "
            f"{phrase.n(desimal(reading.value, 0), 'persentil kenaikan lima sesi', reading.sources)} "
            f"terhadap distribusi saham itu sendiri, dengan ambang persentil "
            f"{phrase.n(desimal(reading.threshold, 0), 'ambang momentum', reading.threshold_sources)}")
    short = (f"momentum persentil "
             f"{phrase.n(desimal(reading.value, 0), 'persentil kenaikan lima sesi', reading.sources)}")
    return lead, short


def _catalyst(reading, phrase):
    articles, articles_src = _context(reading, "jumlah_artikel")
    fundamental, fundamental_src = _context(reading, "artikel_fundamental")
    if articles:
        lead = (f"{phrase.n(str(fundamental), 'artikel berdimensi fundamental', fundamental_src)} "
                f"dari {phrase.n(str(articles), 'artikel di jendela', articles_src)} "
                f"artikel berdimensi fundamental")
    else:
        lead = "liputannya diukur sebagai pangsa artikel berdimensi fundamental"
    lead += (f", rasio "
             f"{phrase.n(desimal(reading.value, 3), 'rasio artikel fundamental', reading.sources)} "
             f"terhadap ambang "
             f"{phrase.n(desimal(reading.threshold, 3), 'ambang katalis', reading.threshold_sources)}")
    short = (f"katalis rasio "
             f"{phrase.n(desimal(reading.value, 3), 'rasio artikel fundamental', reading.sources)}")
    return lead, short


CLAUSES = {
    "concentration": _concentration,
    "volume_anomaly": _volume,
    "momentum": _momentum,
    "catalyst": _catalyst,
}


def _clause(reading, phrase):
    """`(lead, short)` for a measured reading. Unmeasured axes never reach here."""
    return CLAUSES[reading.axis](reading, phrase)


def _exceedance(reading):
    """How far past its own bar an axis landed, comparable across axes.

    Axes measure different things on different scales, so "most prominent" cannot
    be the largest raw value — a 24,5x volume ratio and a 0,838 concentration ratio
    are not on the same ruler. Distance from each axis' own threshold is, and it is
    the same quantity that decided `fired`, so the sentence that opens the paragraph
    is led by the reading that carried the profile rather than by whichever axis the
    code happened to compute first.
    """
    if reading.value is None or not reading.threshold:
        return 0.0
    if reading.axis == "catalyst":              # read downwards: low is notable
        return (reading.threshold + 1e-9) / (reading.value + 1e-9)
    return reading.value / reading.threshold


def _lead(readings):
    """The reading that opens the paragraph: measured, and furthest past its bar."""
    measured = [r for r in readings if r.measured]
    if not measured:
        return None
    return max(measured, key=_exceedance)


# --- the sentences -----------------------------------------------------------
def _window_range(profile, phrase):
    """`2026-08-10 .. 2026-09-09`, or an empty string when nothing was measured."""
    if not (profile.window_start and profile.window_end):
        return ""
    sources = profile_mod.SOURCES["volume_anomaly"]
    return (f"{phrase.n(profile.window_start, 'awal jendela harian', sources)} .. "
            f"{phrase.n(profile.window_end, 'akhir jendela harian', sources)}")


def _names(readings):
    return ", ".join(AXIS_PROSE.get(r.axis, r.axis) for r in readings)


def _unavailable(profile, phrase):
    """Nothing could be measured. Says so — and says why that is not a zero.

    The bug this wording exists for is a reader taking an empty profile for a calm
    one. Four axes with no recording behind them is the absence of a measurement;
    rendered as `0` it would look like the strongest possible finding of nothing.
    """
    del phrase                                   # no figures in this branch
    return [
        f"Data tidak tersedia untuk {profile.symbol}: "
        f"{_names(profile.counted)} sama-sama tidak terukur dari rekaman yang ada.",
        "Tidak ada satu pun angka yang dilaporkan sebagai nol — rekaman yang belum "
        "ada bukan pengukuran yang menghasilkan nol.",
    ]


def _halted(profile, phrase):
    """A halted stock. The zeros are stated as an absence of trading, with the date."""
    window = _window_range(profile, phrase)
    opening = (f"{profile.symbol} berhenti diperdagangkan di dalam jendela"
               + (f" {window}" if window else ""))
    sources = profile_mod.SOURCES["history"]
    if profile.suspension_events:
        event = profile.suspension_events[-1]
        opening += (f": pengumuman IDX tertanggal "
                    f"{phrase.n(event.date.isoformat(), 'tanggal pengumuman suspensi', sources)} "
                    f"dengan klasifikasi {event.reason_class}.")
    else:
        opening += (", tetapi tidak ada pengumuman tercatat di jendela ini, jadi "
                    "sebab deret nolnya belum diketahui.")
    unknown = [r for r in profile.counted if not r.measured]
    second = ("Deret harian dan/atau panel brokernya nol seluruhnya, jadi "
              f"{_names(unknown)} tidak terukur — nol di sini berarti tidak ada "
              "perdagangan, bukan tidak ada temuan.")
    return [opening, second]


def _measured(profile, phrase):
    """The ordinary case: an axis leads, the rest follow in one sentence."""
    lead = _lead(profile.counted)
    lead_text, _ = _clause(lead, phrase)
    window = _window_range(profile, phrase)
    fired = [r for r in profile.counted if r.fired is True]
    prefix = f"Pada jendela {window}, " if window else ""

    if fired:
        first = (f"{prefix}{profile.symbol} paling menonjol pada sumbu "
                 f"{AXIS_PROSE[lead.axis]}: {lead_text}.")
    else:
        first = (f"{prefix}tidak satu pun sumbu {profile.symbol} tercatat menyala; "
                 f"yang paling dekat ke ambangnya adalah "
                 f"{AXIS_PROSE[lead.axis]}, {lead_text}.")

    rest = [r for r in profile.counted if r is not lead and r.measured]
    # A lit axis in the tail is marked where it stands rather than listed again by
    # name: naming the fired set and then repeating each reading made the second
    # sentence say everything twice, which is the prototype's own failure.
    shorts = [_clause(r, phrase)[1] + (" (menyala)" if r.fired else "")
              for r in rest]
    unknown = [r for r in profile.counted if not r.measured]

    if fired:
        # The count is only worth a figure when something lit; the "none fired"
        # opening already says it in words, and "0 dari 4" after it is the same
        # sentence twice.
        sources = _axis_sources(profile)
        second = (f"{phrase.n(str(profile.axes_fired), 'sumbu yang menyala', sources)}"
                  f" dari "
                  f"{phrase.n(str(profile.axes_total), 'sumbu yang dihitung', sources)}"
                  f" sumbu tercatat menyala")
        if shorts:
            second += "; sumbu lain terbaca " + ", ".join(shorts)
    else:
        second = "Sumbu lain terbaca " + ", ".join(shorts) if shorts else \
            "Tidak ada sumbu lain yang terukur"
    if unknown:
        second += f"; {_names(unknown)} tidak terukur"
    return [first, second + "."]


def _cutoff_sources(profile):
    """Where the history bound came from — the daily window, or the run's clock."""
    if profile.window_start and profile.cutoff == profile.window_start:
        return profile_mod.SOURCES["volume_anomaly"]
    return (CUTOFF_SOURCE,)


def _history_sentence(profile, phrase, cache=None):
    """The supporting axis as a dated fact with its announcement. Never a charge.

    §D11 is explicit that a live ticker beside the word manipulation is a legal
    exposure, and that the way out is dated fact: *what* the exchange announced and
    *when*. So this sentence reports the halts that already happened and stops
    there — it draws no line from them to the window's readings.
    """
    try:
        record = history_axis.score(profile.symbol, profile.cutoff, cache=cache)
    except (ValueError, LookupError):
        return None
    sources = profile_mod.SOURCES["history"]
    if not profile.cutoff:
        return None
    cutoff = phrase.n(profile.cutoff, "batas riwayat", _cutoff_sources(profile))
    if record.n_prior == 0:
        return (f"Sebelum {cutoff} tidak ada suspensi {profile.symbol} yang tercatat "
                f"pada pengumuman IDX.")
    times = phrase.n(str(record.n_prior), "suspensi tercatat sebelum batas", sources)
    last = phrase.n(record.last_date, "tanggal suspensi terakhir", sources)
    return (f"IDX tercatat menghentikan perdagangan {profile.symbol} sebanyak {times} "
            f"kali sebelum {cutoff}, terakhir pada {last} dengan klasifikasi "
            f"{record.last_reason_class}.")


# --- the paragraph -----------------------------------------------------------
@dataclass(frozen=True)
class Paragraph:
    """Two or three sentences, the figures behind them, and the disclaimer.

    `text` is what any consumer sends onward, and the disclaimer is part of it by
    construction — a caller cannot forward the sentences and leave it behind.
    """

    symbol: str
    sentences: tuple = ()
    cited: tuple = ()
    disclaimer: str = DISCLAIMER

    @property
    def body(self):
        return " ".join(self.sentences)

    @property
    def text(self):
        return f"{self.body}\n\n{self.disclaimer}"

    @property
    def sources(self):
        """Every source this paragraph rests on, deduplicated, in reading order."""
        seen, out = set(), []
        for cited in self.cited:
            for source in cited.sources:
                key = (source.origin, source.endpoint, source.fields)
                if key not in seen:
                    seen.add(key)
                    out.append(source)
        return tuple(out)

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "paragraf": self.body,
            "kalimat": list(self.sentences),
            "disclaimer": self.disclaimer,
            "angka": [c.to_dict() for c in self.cited],
            "sumber": [s.to_dict() for s in self.sources],
        }

    def __str__(self):
        return describe(self)


def banned_words_in(text):
    """Which entries of `BANNED` appear as whole words. Order follows `BANNED`."""
    lowered = text.lower()
    return [w for w in BANNED
            if re.search(r"\b" + re.escape(w) + r"\b", lowered)]


def verify(paragraph):
    """Fail closed. Returns the paragraph, or raises rather than emitting a guess."""
    allowed = set()
    for cited in paragraph.cited:
        if not cited.sources:
            raise UncitedNumberError(
                f"{paragraph.symbol}: angka {cited.text!r} ({cited.what}) tidak "
                f"membawa endpoint dan field — keluaran ditolak, bukan ditebak")
        for source in cited.sources:
            if not (source.endpoint and source.fields):
                raise UncitedNumberError(
                    f"{paragraph.symbol}: sitasi untuk {cited.text!r} tidak lengkap "
                    f"(endpoint={source.endpoint!r}, fields={source.fields!r})")
        allowed.update(cited.tokens)

    orphans = [t for t in TOKEN.findall(paragraph.text) if t not in allowed]
    if orphans:
        raise UncitedNumberError(
            f"{paragraph.symbol}: angka tanpa sitasi di paragraf — "
            f"{', '.join(sorted(set(orphans)))}; keluaran ditolak, bukan ditebak")

    found = banned_words_in(paragraph.text)
    if found:
        raise BannedVocabularyError(
            f"{paragraph.symbol}: kosakata vonis di paragraf — {', '.join(found)}")
    return paragraph


def render(profile, cache=None):
    """One symbol's paragraph. Raises rather than emitting an unattributed figure.

    `cache` is passed through to the history lookup only; the profile has already
    read everything else. Zero credits either way.
    """
    phrase = Phrase()
    if profile.suspended:
        sentences = _halted(profile, phrase)
    elif not any(r.measured for r in profile.counted):
        sentences = _unavailable(profile, phrase)
    else:
        sentences = _measured(profile, phrase)

    history_sentence = _history_sentence(profile, phrase, cache=cache)
    if history_sentence and len(sentences) < MAX_SENTENCES:
        sentences.append(history_sentence)

    return verify(Paragraph(symbol=profile.symbol, sentences=tuple(sentences),
                            cited=tuple(phrase.cited)))


def render_symbol(symbol, cache=None, **kwargs):
    """Build the profile and render it. The one call a caller normally needs."""
    return render(profile_mod.build(symbol, cache=cache, **kwargs), cache=cache)


def describe(paragraph, width=76):
    """The paragraph as a terminal block: prose, disclaimer, then every figure."""
    lines = [paragraph.symbol, ""]
    lines += textwrap.wrap(paragraph.body, width=width)
    lines.append("")
    lines += textwrap.wrap(paragraph.disclaimer, width=width)
    lines.append("")
    lines.append("sumber tiap angka:")
    for cited in paragraph.cited:
        lines.append(f"  - {cited}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    for arg in (sys.argv[1:] or config.WATCHLIST):
        print(describe(render_symbol(arg)))
        print()
