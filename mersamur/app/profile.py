"""Profil konvergensi — how many axes lit, and which. Never one number.

`riset/spec.md` §5 is explicit that the score is **not** a weighted average:

    Skor bukan rata-rata tertimbang. Profilnya adalah berapa sumbu yang menyala
    dan mana. Konvergensi lintas pandangan independen adalah argumennya;
    agregasi ke satu angka justru membuangnya.

Two reasons, and only the first is about statistics.

**Flattening destroys the argument.** The product's claim is that four *independent*
views of the same stock agreed. Concentration reads the broker panel, volume reads
the tape, momentum reads the price distribution, catalyst reads the coverage — four
different endpoints, four different failure modes. "Three of four agreed, and here
they are" is a statement a reader can audit line by line. "0,72" is not: it hides
which view carried the weight, and a single mis-parsed field can move it without
anything on screen looking wrong.

**A single number reads as a recommendation.** `riset/red-team.md` §D11 rules out
verdicts, scores-as-recommendations, and red/green colour, for the exchange's
reasons as much as for the project's. A profile that says "sumbu konsentrasi
menyala, sumbu momentum tidak" is a description of measurements. The same content
compressed into one figure invites ranking, and a ranked list of live tickers beside
the word manipulation is precisely what §D11 forbids.

So this module adds no weights and sums nothing.

## The four axes, and the supporting one

`riset/spec.md` §5 names four axes plus supporting ones ("Sumbu pendukung: insider
(`filings`), riwayat masalah (`suspensions` **sebelum** jendela fitur)"). The
thinness axis in that table is built on `free_float`, which carries no date and is
therefore barred from anything with a label (§7, `test_no_leakage.py`); momentum,
measured as a percentile of the stock against itself, stands in its place. So:

    counted   concentration · volume_anomaly · momentum · catalyst
    supporting history

`history` is reported in full and deliberately **not counted**. It is also the
baseline the system has to beat (`app/baselines/previously_suspended.py`); letting
it raise the profile's own count would let the product take credit for the
competitor's answer.

## Three states, never two

Every axis reads `menyala`, `tidak_menyala`, or `tidak_diketahui`, and the third one
is the point. A missing broker panel, a series with no baseline, a symbol nobody
wrote about — none of those are evidence of calm. Folded into `False` they would
make an unmeasured stock look quiet, and a stock that is quiet *because it is
halted* look quietest of all. Unknown axes are excluded from the count and reported
by name (`axes_unknown`), so "1 of 4" and "1 of 4, two unmeasured" are never the
same sentence.

A halted stock is the sharpest case of that, so it gets its own handling: the
all-zero series and the all-zero broker panel are read as suspension, the
announcements inside the window are attached, and the axes that rest on those
numbers go `tidak_diketahui` rather than reporting zeroes
(`research/docs/api/10-domain-pitfalls.md` §2).

## Citations

Every number in the output carries where it came from: the endpoint and the fields
for a measurement, `state/thresholds.json` and the key for a bar. That is what makes
the profile checkable by someone who does not trust it — a reader can go to the same
call and the same field and see the same figure. It is also what keeps thresholds
honest: a bar with a citation to `current.concentration` cannot quietly be a
constant in this file.

Zero credits: every axis reads `research/harness/recorded/`. `SectorsClient` is
never imported here or in anything this module calls, and no socket is opened.
"""
from dataclasses import dataclass, field
from datetime import date

from app import axes, universe
from app.axes import catalyst, concentration, history, momentum, volume_anomaly

# The four that are counted, in reading order.
AXES = ("concentration", "volume_anomaly", "momentum", "catalyst")

# Reported, never counted — see the module docstring.
SUPPORTING_AXES = ("history",)

# The three states an axis may be in. Descriptive words, no colour, no verdict.
LIT = "menyala"
UNLIT = "tidak_menyala"
UNKNOWN = "tidak_diketahui"

THRESHOLDS_FILE = "state/thresholds.json"


@dataclass(frozen=True)
class Source:
    """Where one number came from — an endpoint and its fields, or the state file.

    `endpoint` is the API path as it is called; `origin` is `"api"` or `"state"`.
    Both forms exist because a threshold is as much a number on screen as a
    measurement is, and a reader who cannot trace the bar cannot check the axis.
    """

    endpoint: str
    fields: tuple = ()
    origin: str = "api"

    def to_dict(self):
        return {"origin": self.origin, "endpoint": self.endpoint,
                "fields": list(self.fields)}


# The measurement sources, per axis. Field paths are written the way the payload
# nests them so a reader can walk straight to them in `recorded/`.
SOURCES = {
    "concentration": (
        Source("/v2/broker-summary/{symbol}/top/",
               ("top_buyers[].broker_code", "top_buyers[].buy_idr",
                "top_buyers[].net_idr", "top_sellers[].net_idr", "start", "end")),
        Source("/v2/brokers/", ("code", "name", "cohort", "is_foreign")),
    ),
    "volume_anomaly": (
        Source("/v2/daily/{symbol}/", ("date", "volume")),
    ),
    "momentum": (
        Source("/v2/daily/{symbol}/", ("date", "close")),
    ),
    "catalyst": (
        Source("/v2/news/", ("timestamp", "symbols", "dimension.financials",
                             "dimension.future", "dimension.technical",
                             "pagination.has_next")),
    ),
    "history": (
        Source("/v2/suspensions/", ("symbol", "suspension_date", "reason")),
    ),
}


def threshold_source(axis, keys=()):
    """The state-file citation for a bar. `keys` names the entries actually read."""
    return Source(THRESHOLDS_FILE, tuple(keys) or (f"current.{axis}",), origin="state")


# What each axis measures, in one phrase, for the reader who never saw the code.
MEASURES = {
    "concentration": "pangsa akumulasi broker teratas terhadap nilai akumulasi panel",
    "volume_anomaly": "volume sesi terakhir terhadap median sesi bertransaksi sebelumnya",
    "momentum": "persentil kenaikan lima sesi terhadap distribusi saham itu sendiri",
    "catalyst": "pangsa artikel berdimensi fundamental terhadap seluruh artikel",
    "history": "suspensi yang sudah tercatat sebelum jendela fitur",
}

# `catalyst` is the one axis whose bar is read downwards: a *low* share of
# fundamental coverage is the notable reading, so it fires at or below the bar while
# the other three fire at or above theirs. Stated here rather than buried in a
# comparison so the direction is visible in the output too.
DIRECTIONS = {
    "concentration": "di atas atau sama dengan ambang",
    "volume_anomaly": "di atas atau sama dengan ambang",
    "momentum": "di atas atau sama dengan ambang",
    "catalyst": "di bawah atau sama dengan ambang",
}


@dataclass(frozen=True)
class Reading:
    """One axis' answer. Immutable — the profile never re-scores an axis.

    `fired` is a three-valued flag on purpose: `True`, `False`, and `None` for an
    axis that could not be measured. `None` is never counted as `False`; the reason
    it is unknown travels with it in `unknown_reason`.
    """

    axis: str
    measure: str = ""
    value: float = None
    unit: str = ""
    threshold: float = None
    threshold_detail: str = ""
    direction: str = ""
    state: str = UNKNOWN
    fired: bool = None
    unknown_reason: str = ""
    counted: bool = True
    context: tuple = ()
    sources: tuple = ()
    threshold_sources: tuple = ()

    @property
    def measured(self):
        return self.fired is not None

    def to_dict(self):
        out = {
            "axis": self.axis,
            "measure": self.measure,
            "counted": self.counted,
            "value": self.value,
            "unit": self.unit,
            "value_sources": [s.to_dict() for s in self.sources],
            "threshold": self.threshold,
            "threshold_detail": self.threshold_detail,
            "direction": self.direction,
            "threshold_sources": [s.to_dict() for s in self.threshold_sources],
            "state": self.state,
            "fired": self.fired,
            "unknown_reason": self.unknown_reason,
            "context": [{"name": name, "value": value, "unit": unit,
                         "sources": [s.to_dict() for s in sources]}
                        for name, value, unit, sources in self.context],
        }
        return out


def _reading(axis, value=None, unit="", threshold=None, threshold_detail="",
             threshold_keys=(), fired=None, unknown_reason="", context=(),
             counted=True):
    """Assemble a `Reading`, attaching the axis' citations. One construction path.

    Every reading goes through here so no axis can reach the output without its
    endpoint and fields — a number on screen with nothing behind it is exactly what
    the citation list exists to prevent.
    """
    if fired is None:
        state = UNKNOWN
    else:
        state = LIT if fired else UNLIT
    return Reading(
        axis=axis,
        measure=MEASURES.get(axis, ""),
        value=value,
        unit=unit,
        threshold=threshold,
        threshold_detail=threshold_detail,
        direction=DIRECTIONS.get(axis, ""),
        state=state,
        fired=fired,
        unknown_reason=unknown_reason,
        counted=counted,
        context=tuple(context),
        sources=SOURCES.get(axis, ()),
        threshold_sources=((threshold_source(axis, threshold_keys),)
                           if threshold is not None else ()),
    )


# --- the axes, one reader each ----------------------------------------------
def _read_concentration(symbol, cache=None, thresholds_path=None):
    axis = concentration.AXIS
    try:
        result = concentration.score(symbol, cache=cache,
                                     thresholds_path=thresholds_path)
    except concentration.NoBrokerDataError:
        return _reading(axis, unknown_reason=(
            "tidak ada panel broker terekam untuk simbol ini; panggilannya berbiaya "
            "1 kredit dan tidak dijalankan diam-diam"), counted=True), None

    if result.all_zero or result.top1_ratio is None:
        reason = ("panel nol seluruhnya — nilai transaksi tidak ada di sisi mana pun, "
                  "jadi tidak ada pangsa yang bisa dihitung")
        return _reading(axis, threshold=result.effective_threshold,
                        threshold_detail=_bar_detail(result),
                        threshold_keys=("current.concentration",
                                        f"cohort_factors.{result.cohort}"),
                        unknown_reason=reason,
                        context=_concentration_context(result)), result

    return _reading(
        axis,
        value=result.top1_ratio,
        unit="rasio",
        threshold=result.effective_threshold,
        threshold_detail=_bar_detail(result),
        threshold_keys=("current.concentration", f"cohort_factors.{result.cohort}"),
        fired=result.fired,
        context=_concentration_context(result),
    ), result


def _bar_detail(result):
    return (f"ambang dasar {_id('%.2f' % result.threshold)} dikali faktor kohort "
            f"{_id('%.2f' % result.cohort_factor)}, kohort {result.cohort}")


def _concentration_context(result):
    src = SOURCES["concentration"]
    return (
        ("pangsa_top3", result.top3_ratio, "rasio", src),
        ("dominansi_neto_idr", result.net_dominance, "IDR", src),
        ("nilai_panel_idr", result.panel_value_idr, "IDR", src),
        ("jumlah_akumulator", result.n_buyers, "baris", src),
        ("jumlah_distributor", result.n_sellers, "baris", src),
    )


def _read_volume(symbol, cache=None, thresholds_path=None, start=None, end=None):
    axis = volume_anomaly.AXIS
    try:
        result = volume_anomaly.score(symbol, cache=cache,
                                      thresholds_path=thresholds_path,
                                      start=start, end=end)
    except volume_anomaly.NoDailyDataError:
        return _reading(axis, unknown_reason=(
            "tidak ada deret harian terekam untuk simbol ini; /v2/daily/ berbiaya "
            "1 kredit dan tidak dijalankan diam-diam")), None

    context = (
        ("volume_sesi_terakhir", result.last_volume, "lembar", SOURCES[axis]),
        ("baseline_median", result.baseline_median, "lembar", SOURCES[axis]),
        ("sesi_bertransaksi", result.n_traded, "sesi", SOURCES[axis]),
        ("sesi_nol", result.n_zero, "sesi", SOURCES[axis]),
    )
    if result.all_zero:
        reason = ("deret nol seluruhnya — sahamnya dihentikan, bukan sepi peminat, "
                  "jadi tidak ada rasio volume yang bisa dibaca")
        return _reading(axis, threshold=result.threshold,
                        threshold_keys=("current.volume_anomaly",),
                        unknown_reason=reason, context=context), result
    if result.ratio is None:
        reason = (f"belum ada baseline — butuh "
                  f"{volume_anomaly.MIN_BASELINE_SESSIONS} sesi bertransaksi sebelum "
                  f"sesi terakhir, tersedia {result.n_baseline}")
        return _reading(axis, threshold=result.threshold,
                        threshold_keys=("current.volume_anomaly",),
                        unknown_reason=reason, context=context), result

    return _reading(axis, value=result.ratio, unit="x median",
                    threshold=result.threshold,
                    threshold_keys=("current.volume_anomaly",),
                    fired=result.fired, context=context), result


def _read_momentum(symbol, cache=None, thresholds_path=None, start=None, end=None):
    axis = momentum.AXIS
    try:
        result = momentum.score(symbol, cache=cache, thresholds_path=thresholds_path,
                                start=start, end=end)
    except momentum.NoDailyDataError:
        return _reading(axis, unknown_reason=(
            "tidak ada deret harian terekam untuk simbol ini; /v2/daily/ berbiaya "
            "1 kredit dan tidak dijalankan diam-diam")), None

    context = (
        ("kenaikan_lima_sesi", result.latest_gain, "rasio", SOURCES[axis]),
        ("median_kenaikan", result.median_gain, "rasio", SOURCES[axis]),
        ("jumlah_jendela", result.n_windows, "jendela", SOURCES[axis]),
    )
    if result.all_zero:
        reason = ("deret nol seluruhnya — harga penutupan hanya dibawa turun dari "
                  "sesi terakhir sebelum berhenti, jadi persentilnya artefak suspensi")
        return _reading(axis, threshold=result.threshold,
                        threshold_keys=("current.momentum",),
                        unknown_reason=reason, context=context), result
    if result.percentile is None:
        reason = (f"belum ada distribusi — butuh {momentum.MIN_WINDOWS} jendela "
                  f"{result.window} sesi, tersedia {result.n_windows}")
        return _reading(axis, threshold=result.threshold,
                        threshold_keys=("current.momentum",),
                        unknown_reason=reason, context=context), result

    return _reading(axis, value=result.percentile, unit="persentil",
                    threshold=result.threshold,
                    threshold_keys=("current.momentum",),
                    fired=result.fired, context=context), result


def _read_catalyst(symbol, cache=None, thresholds_path=None, before=None):
    """The one axis whose bar this module applies rather than reads off a result.

    `app/axes/catalyst.py` deliberately computes no `fired`: it refuses to invent a
    threshold, which is the right call for a module that has none. The bar lives in
    `state/thresholds.json` under `current.catalyst`, it is read here through the
    same `axes.threshold` clamp as every other bar, and it is read **downwards** —
    a low share of fundamental coverage is the notable reading.
    """
    axis = catalyst.AXIS
    try:
        result = catalyst.score(symbol, cache=cache, before=before)
    except catalyst.NoNewsDataError:
        return _reading(axis, unknown_reason=(
            "tidak ada rekaman /v2/news/?symbols= yang memuat simbol ini; panggilannya "
            "berbiaya 1 kredit untuk seluruh daftar dan tidak dijalankan diam-diam")), None

    bar = axes.threshold(axis, thresholds_path)
    context = (
        ("jumlah_artikel", result.n_articles, "artikel", SOURCES[axis]),
        ("artikel_fundamental", result.n_fundamental, "artikel", SOURCES[axis]),
        ("artikel_hanya_teknikal", result.n_technical_only, "artikel", SOURCES[axis]),
        ("artikel_tanpa_klasifikasi", result.n_unclassified, "artikel", SOURCES[axis]),
    )
    if result.ratio is None:
        # No articles at all. Nothing was measured, so nothing is concluded — this
        # is the case `catalyst.py` refuses to collapse into "zero fundamental".
        return _reading(axis, threshold=bar, threshold_keys=("current.catalyst",),
                        unknown_reason=("tidak ada artikel di jendela ini, jadi tidak "
                                        "ada penyebut untuk rasio fundamental"),
                        context=context), result

    return _reading(axis, value=result.ratio, unit="rasio", threshold=bar,
                    threshold_keys=("current.catalyst",),
                    fired=bool(result.ratio <= bar), context=context), result


def _read_history(symbol, cutoff, cache=None):
    """The supporting axis. Reported in full, never counted, never fires.

    No bar is read: `state/thresholds.json` carries none for it, and the plain "has
    ever been suspended" rule is a *competitor* the system has to beat
    (`app/baselines/previously_suspended.py`), not a component it may score with.
    """
    axis = history.AXIS
    try:
        result = history.score(symbol, cutoff, cache=cache)
    except (ValueError, LookupError) as exc:
        return _reading(axis, counted=False,
                        unknown_reason=f"riwayat tidak terbaca: {exc}"), None

    context = (
        ("suspensi_sebelum_cutoff", result.n_prior, "peristiwa", SOURCES[axis]),
        ("di_antaranya_cooling_down", result.n_prior_label, "peristiwa", SOURCES[axis]),
        ("hari_sejak_terakhir", result.days_since_last, "hari", SOURCES[axis]),
    )
    return _reading(axis, value=result.n_prior, unit="peristiwa", fired=None,
                    counted=False,
                    unknown_reason=("sumbu pendukung: dilaporkan, tidak ikut dihitung "
                                    "karena aturan riwayat adalah baseline pembanding"),
                    context=context), result


# --- the profile ------------------------------------------------------------
@dataclass(frozen=True)
class Profile:
    """One symbol's four axes plus the supporting one. Immutable, and countable.

    Mapping access (`profile["axes_fired"]`) reads the same dict `to_dict()`
    returns, so a caller writing to `state/warnings.jsonl` and a caller reading one
    field see identical content.
    """

    symbol: str
    as_of: str = ""
    cutoff: str = ""
    window_start: str = ""
    window_end: str = ""
    thresholds_version: int = None
    readings: tuple = ()
    supporting: tuple = ()
    suspended: bool = False
    suspension_events: tuple = ()
    _dict: dict = field(default=None, repr=False, compare=False)

    @property
    def counted(self):
        return tuple(r for r in self.readings if r.counted)

    @property
    def axes_total(self):
        return len(self.counted)

    @property
    def axes_fired(self):
        return sum(1 for r in self.counted if r.fired is True)

    @property
    def axes_unlit(self):
        return sum(1 for r in self.counted if r.fired is False)

    @property
    def axes_unknown(self):
        """Axes that could not be measured. Never folded into `axes_unlit`."""
        return sum(1 for r in self.counted if r.fired is None)

    @property
    def fired_axes(self):
        return tuple(r.axis for r in self.counted if r.fired is True)

    @property
    def unknown_axes(self):
        return tuple(r.axis for r in self.counted if r.fired is None)

    @property
    def citations(self):
        """Every endpoint and field this profile rests on, deduplicated."""
        seen, out = set(), []
        for reading in self.readings + self.supporting:
            for source in (reading.sources + reading.threshold_sources
                           + tuple(s for _, _, _, srcs in reading.context
                                   for s in srcs)):
                key = (source.origin, source.endpoint, source.fields)
                if key not in seen:
                    seen.add(key)
                    out.append(source)
        return tuple(out)

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "as_of": self.as_of,
            "cutoff": self.cutoff,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "thresholds_version": self.thresholds_version,
            "axes_total": self.axes_total,
            "axes_fired": self.axes_fired,
            "axes_unlit": self.axes_unlit,
            "axes_unknown": self.axes_unknown,
            "fired_axes": list(self.fired_axes),
            "unknown_axes": list(self.unknown_axes),
            "suspended": self.suspended,
            "suspension_events": [{"date": e.date.isoformat(),
                                   "reason_class": e.reason_class}
                                  for e in self.suspension_events],
            "readings": [r.to_dict() for r in self.readings],
            "supporting": [r.to_dict() for r in self.supporting],
            "citations": [s.to_dict() for s in self.citations],
        }

    def __getitem__(self, key):
        return self.to_dict()[key]

    def get(self, key, default=None):
        return self.to_dict().get(key, default)

    def keys(self):
        return self.to_dict().keys()

    def __str__(self):
        return describe(self)


def _suspension_evidence(results):
    """All-zero readings and the announcements dated inside their own window.

    A stock whose broker panel and daily series are both entirely zero is halted,
    not calm (`research/docs/api/10-domain-pitfalls.md` §2). The events are the
    window's own announcements, carried so the profile can say *which* halt — and
    they are evidence about the hole in the data, never a feature.
    """
    zero = [r for r in results if r is not None and getattr(r, "all_zero", False)]
    seen, events = set(), []
    for result in zero:
        for event in getattr(result, "suspensions_in_window", ()):
            key = (event.symbol, event.date, event.reason_class)
            if key not in seen:
                seen.add(key)
                events.append(event)
    events.sort(key=lambda e: e.date)
    return bool(zero), tuple(events)


def build(symbol, cache=None, thresholds_path=None, cutoff=None, before=None,
          start=None, end=None, as_of=None):
    """The convergence profile for one symbol. Reads recordings only, 0 credits.

    `cutoff` bounds the supporting history axis and defaults to the **first day of
    the daily window** rather than to today: anything dated inside the window is
    still future information relative to the window's own start. `before` is the
    catalyst axis' leak guard and stays `None` for a live run, where there is no
    future to exclude.

    `thresholds_path` is injectable so a test can prove the bars come from the file
    rather than from this module.
    """
    want = universe.normalize(symbol)

    volume_reading, volume_result = _read_volume(want, cache=cache,
                                                 thresholds_path=thresholds_path,
                                                 start=start, end=end)
    momentum_reading, momentum_result = _read_momentum(want, cache=cache,
                                                       thresholds_path=thresholds_path,
                                                       start=start, end=end)
    concentration_reading, concentration_result = _read_concentration(
        want, cache=cache, thresholds_path=thresholds_path)
    catalyst_reading, catalyst_result = _read_catalyst(want, cache=cache,
                                                       thresholds_path=thresholds_path,
                                                       before=before)

    window_start = volume_result.start if volume_result is not None else ""
    window_end = volume_result.end if volume_result is not None else ""
    when = cutoff or window_start or date.today().isoformat()
    history_reading, _ = _read_history(want, when, cache=cache)

    suspended, events = _suspension_evidence(
        (volume_result, momentum_result, concentration_result))

    return Profile(
        symbol=want,
        as_of=as_of or date.today().isoformat(),
        cutoff=str(when),
        window_start=window_start,
        window_end=window_end,
        thresholds_version=axes.version(thresholds_path),
        readings=(concentration_reading, volume_reading, momentum_reading,
                  catalyst_reading),
        supporting=(history_reading,),
        suspended=suspended,
        suspension_events=events,
    )


# --- description ------------------------------------------------------------
def _id(value):
    """Format a number the Indonesian way: comma as the decimal separator."""
    return str(value).replace(".", ",")


def _value(reading):
    if reading.value is None:
        return "tidak terukur"
    if reading.unit == "rasio":
        return _id("%.3f" % reading.value)
    if reading.unit == "persentil":
        return _id("%.0f" % reading.value)
    if reading.unit == "x median":
        return _id("%.1f" % reading.value) + "x"
    if isinstance(reading.value, float):
        return _id("%.2f" % reading.value)
    return _id(reading.value)


def _bar(reading):
    if reading.threshold is None:
        return "tidak ada ambang untuk sumbu ini"
    text = _id("%.3f" % reading.threshold) + f" · {reading.direction}"
    if reading.threshold_detail:
        text += f" ({reading.threshold_detail})"
    return text


def describe(profile):
    """A descriptive account of one profile. No verdict, no colour, no ranking."""
    lines = [f"Profil konvergensi {profile.symbol} — {profile.window_start} .. "
             f"{profile.window_end} (0 kredit, dari rekaman)",
             f"  ambang           : versi {profile.thresholds_version}, dibaca dari "
             f"{THRESHOLDS_FILE}",
             f"  sumbu menyala    : {profile.axes_fired} dari {profile.axes_total}"
             + (f" — {', '.join(profile.fired_axes)}" if profile.fired_axes else ""),
             f"  sumbu tidak menyala: {profile.axes_unlit}",
             f"  sumbu tidak terukur: {profile.axes_unknown}"
             + (f" — {', '.join(profile.unknown_axes)}"
                if profile.unknown_axes else "")]

    if profile.suspended:
        lines.append("  Saham ini berhenti diperdagangkan di dalam jendela: deret "
                     "harian dan/atau panel brokernya nol seluruhnya. Nol di sini "
                     "berarti tidak ada perdagangan, bukan tidak ada temuan.")
        for event in profile.suspension_events:
            lines.append(f"  suspensi di dalam jendela: {event.date} — "
                         f"{event.reason_class}")
        if not profile.suspension_events:
            lines.append("  Tidak ada pengumuman suspensi tercatat di jendela ini, "
                         "jadi sebab deret nol belum diketahui.")

    for reading in profile.readings:
        lines.append(f"  · {reading.axis} — {reading.measure}")
        lines.append(f"      nilai        : {_value(reading)}"
                     + (f" ({reading.unit})"
                        if reading.value is not None
                        and reading.unit in ("rasio", "persentil") else ""))
        lines.append(f"      ambang       : {_bar(reading)}")
        lines.append(f"      keadaan      : {reading.state}")
        if reading.unknown_reason:
            lines.append(f"      sebab        : {reading.unknown_reason}")
        lines.append(f"      sitasi       : "
                     + " · ".join(s.endpoint for s in reading.sources))

    for reading in profile.supporting:
        lines.append(f"  · {reading.axis} (pendukung, tidak dihitung) — "
                     f"{reading.measure}")
        lines.append(f"      nilai        : {_value(reading)} sebelum "
                     f"{profile.cutoff}")
        lines.append(f"      sitasi       : "
                     + " · ".join(s.endpoint for s in reading.sources))

    lines += [
        "  Profil ini menghitung berapa pandangan independen yang sejalan, bukan "
        "menjumlahkan bobot: satu angka tunggal akan menyembunyikan sumbu mana yang "
        "menopangnya.",
        "  Seluruh isi profil bersifat deskriptif — catatan atas angka yang "
        "dikembalikan API, bukan penilaian atas emitennya maupun anjuran tindakan.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    for arg in (sys.argv[1:] or ["LIFE", "PACK"]):
        print(build(arg))
        print()
