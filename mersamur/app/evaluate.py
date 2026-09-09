#!/usr/bin/env python3
"""Tugas 11 — the go/no-go gate: do the four axes beat the two naive rules?

`riset/red-team.md` §A1 states the question a judge will ask and what happens if
there is no numeric answer to it:

    "Apa bedanya model empat sumbu kalian dengan mengurutkan saham berdasarkan
    kenaikan lima hari terakhir?"

    Kalau tidak ada jawaban berangka, seluruh klaim kedalaman teknis runtuh.

This module produces that number, for three contenders and one combination, over
one universe, at one cutoff, through **one scoring function**. `tasks/11` §1 makes
any difference in the evaluation path grounds for calling the comparison invalid,
so `score()` is the only place a confusion matrix is built and every contender —
including the product's own system — reaches it as the same `(symbol, warned)`
records.

**The metric is lift, never accuracy and never bare precision** (§A2). The
market-wide cooling-down base rate is 0,77% per stock per 10 trading days, so a
model that warns about nothing at all is 99,2% accurate. Accuracy here measures the
rarity of the event, not the quality of the rule.

    lift = P(suspensi | aturan menyala) / P(suspensi)

**What this set is, and what it therefore cannot say.** The 20 symbols with a
recorded daily series over the pinned window are 10 that were halted for
cooling-down and 10 that have never been suspended at all — a case-control basket
assembled by tasks 03 and 10, not a random sample of the market. Its base rate is
50% by construction. Two consequences are stated on every run rather than buried:

  * lift is bounded above by 2,0 here and is **not** the 11x figure §A2 imagines
    for the market. It is only meaningful *between* contenders on this same set;
  * the feature window overlaps the outcome window. This measures **discrimination
    between two known groups**, which is what §A4 says the product actually claims
    ("karakterisasi pada saat keputusan"), not forward prediction. The clean
    hold-out belongs to task 12.

Nothing here tunes anything. The four-axis system runs at
`config.WARNING_AXES_THRESHOLD`, the momentum rule at the five names §A1 itself
names, and neither baseline reads `state/thresholds.json`. `tasks/11` §Jangan
forbids moving a bar to win this comparison, and a bar moved here would show up as
overfitting in task 12 anyway.

Zero credits: reads only `research/harness/recorded/`.
"""
import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date

# Run as a script (`python3 app/evaluate.py`), the way `tasks/11` §Kriteria selesai
# invokes it, so the package root has to be on the path before the first import.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import baselines, config, labels, profile, universe  # noqa: E402
from app.axes.volume_anomaly import NoDailyDataError, series  # noqa: E402
from app.cache import Cache  # noqa: E402

# The product's own system, named so it sits in the same table as its opponents.
SYSTEM = "empat_sumbu"
COMBINED = "momentum_5h+empat_sumbu"

DAILY_PREFIX = "/v2/daily/"


# --- the universe both arms come from ---------------------------------------
@dataclass(frozen=True)
class Basket:
    """The evaluation universe, split into the two arms it was bought as.

    `cases` are symbols with a cooling-down halt dated on or after the window
    start; `controls` are members of `universe.control_group()` — screener rows
    with zero suspension events on record across all nine reason classes and all
    years. Both are required to have a recorded daily series over the *same*
    window, which is what makes the comparison legal at all.

    The eight blue chips in the recording (ADRO … TLKM) fall out on their own:
    they carry no cooling-down label and they are not in the 200-smallest screener
    page, so they are in neither arm. That is deliberate —
    `riset/red-team.md` §B5 is that comparing third-liners against blue chips
    confounds size with manipulation.
    """

    cases: tuple = ()
    controls: tuple = ()
    window_start: str = ""
    window_end: str = ""
    excluded: tuple = ()

    @property
    def symbols(self):
        """Both arms, cases first, in one list. This is the evaluation set."""
        return tuple(self.cases) + tuple(self.controls)

    def __len__(self):
        return len(self.cases) + len(self.controls)


class BasketUnusable(Exception):
    """The two arms cannot be compared — different windows, or an empty arm.

    Raised rather than worked around. A comparison run over two arms measured on
    different dates produces a number that looks fine and means nothing.
    """


def recorded_daily_symbols(cache=None):
    """Every symbol with a settled 2xx `/v2/daily/` payload in the recording."""
    source = cache if cache is not None else Cache()
    out = set()
    for entry in source.manifest().values():
        if entry.get("status") != 200:
            continue
        path = entry.get("path") or ""
        if not path.startswith(DAILY_PREFIX):
            continue
        symbol = universe.normalize(path[len(DAILY_PREFIX):].strip("/").split("/")[0])
        if universe.IDX_SYMBOL.match(symbol):
            out.add(symbol)
    return out


def basket(cache=None, since=None):
    """The two arms, derived from the recording rather than listed by hand.

    A hardcoded roster would silently keep scoring the same twenty names after the
    next capture changes what is on disk. `since` bounds the label that defines a
    case and defaults to the window start, so a halt that predates the window is
    history — a feature — and not an outcome.
    """
    available = recorded_daily_symbols(cache=cache)
    windows, unreadable = {}, []
    for symbol in sorted(available):
        try:
            data = series(symbol, cache=cache)
        except (NoDailyDataError, ValueError, LookupError):
            unreadable.append(symbol)
            continue
        windows[symbol] = (data.start, data.end)

    controls = sorted(set(windows) & set(universe.control_group(cache=cache)))
    starts = {windows[s][0] for s in controls}
    if not controls or len(starts) != 1:
        raise BasketUnusable(
            "Lengan kontrol kosong atau jendelanya tidak seragam: "
            f"{sorted(starts)}. Perbandingan dibatalkan, bukan dipaksakan.")
    window_start, window_end = windows[controls[0]]

    cutoff = since or labels.parse_date(window_start)
    cases = sorted(
        s for s in windows
        if windows[s] == (window_start, window_end)
        and s not in controls
        and any(e.is_label and e.date >= cutoff
                for e in labels.events(symbol=s, cache=cache)))
    if not cases:
        raise BasketUnusable(
            "Tidak ada emiten berlabel dengan jendela yang sama seperti lengan "
            "kontrol. Tidak ada yang bisa dibandingkan.")

    # A control whose window differs from its own arm is already impossible — the
    # uniformity check above raised — and a case is only admitted on an exact
    # window match. So everything left over is genuinely out of the comparison:
    # the eight blue chips, plus anything whose series could not be read.
    excluded = tuple(sorted(set(windows) - set(cases) - set(controls)))
    return Basket(cases=tuple(cases), controls=tuple(controls),
                  window_start=window_start, window_end=window_end,
                  excluded=excluded + tuple(unreadable))


def positives(symbols, since, cache=None):
    """The outcome set: symbols with a cooling-down halt dated on or after `since`.

    One positive class only, and only in the 2025+ regime — `app.labels` is the
    single door onto that, and the filtering rules it enforces (§Q4) are not
    re-implemented here.
    """
    when = since if isinstance(since, date) else labels.parse_date(since)
    return frozenset(
        s for s in symbols
        if any(e.is_label and e.date >= when
               for e in labels.events(symbol=s, cache=cache)))


# --- the contenders, all reduced to the same record -------------------------
@dataclass(frozen=True)
class Call:
    """One contender's mechanical call on one symbol. The only input to `score()`."""

    system: str
    symbol: str
    cutoff: str
    warned: bool
    detail: str = ""


def _axes_calls(cutoff, symbols, cache=None, min_axes=None,
                thresholds_path=None):
    """The product's own system, expressed as the same record a baseline produces.

    It warns when at least `config.WARNING_AXES_THRESHOLD` of the four counted axes
    fire — the shipped value, read here rather than chosen here. An axis that could
    not be measured is `tidak_diketahui` and is not a fired axis, so a symbol whose
    broker panel was never bought can at best reach the number of axes that *were*
    measurable. That ceiling is reported by `measurability()` and is the single most
    important thing to read before believing this row.
    """
    bar = config.WARNING_AXES_THRESHOLD if min_axes is None else min_axes
    out = []
    for symbol in symbols:
        p = profile.build(symbol, cache=cache, cutoff=cutoff,
                          thresholds_path=thresholds_path)
        out.append(Call(system=SYSTEM, symbol=p.symbol, cutoff=str(cutoff),
                        warned=p.axes_fired >= bar,
                        detail=(f"{p.axes_fired}/{p.axes_total} menyala"
                                + (f", {p.axes_unknown} tidak terukur"
                                   if p.axes_unknown else "")
                                + (f" ({', '.join(p.fired_axes)})"
                                   if p.fired_axes else ""))))
    return tuple(out)


def _baseline_calls(name, cutoff, symbols, cache=None):
    """Any registered baseline, reduced to `Call`. No per-baseline branching."""
    out = []
    for p in baselines.run(name, cutoff, symbols=symbols, cache=cache):
        detail = getattr(p, "note", "") or ""
        if getattr(p, "gain", None) is not None:
            detail = f"peringkat {p.rank}, {p.gain * 100:+.1f}%"
        elif hasattr(p, "n_prior"):
            detail = f"{p.n_prior} suspensi sebelum cutoff"
        out.append(Call(system=name, symbol=p.symbol, cutoff=str(p.cutoff),
                        warned=bool(p.warned), detail=detail))
    return tuple(out)


def _combine(name, left, right):
    """Both rules must fire. The `and` is the point: step 4 asks what the axes add
    **on top of** momentum, not whether they beat it standing alone."""
    lookup = {c.symbol: c for c in right}
    return tuple(Call(system=name, symbol=c.symbol, cutoff=c.cutoff,
                      warned=c.warned and lookup[c.symbol].warned,
                      detail=f"{c.detail} · {lookup[c.symbol].detail}")
                 for c in left if c.symbol in lookup)


def contenders(cutoff, symbols, cache=None, min_axes=None, thresholds_path=None):
    """`{system: calls}` for every contender, same universe, same date, in order.

    This is the only place a contender is constructed. Anything scored by `score()`
    came through here, which is what makes "jalur kode yang sama" checkable rather
    than asserted.
    """
    axes_calls = _axes_calls(cutoff, symbols, cache=cache, min_axes=min_axes,
                             thresholds_path=thresholds_path)
    out = {SYSTEM: axes_calls}
    for name in baselines.NAMES:
        out[name] = _baseline_calls(name, cutoff, symbols, cache=cache)
    out[COMBINED] = _combine(COMBINED, out[baselines.momentum.NAME], axes_calls)
    return out


# --- scoring ----------------------------------------------------------------
@dataclass(frozen=True)
class Result:
    """One contender's full confusion matrix and the rates derived from it.

    `precision`, `recall` and `lift` are None rather than 0 when their denominator
    is empty: a rule that warned about nothing has an undefined precision, and
    printing 0,00 would read as a measured failure instead of an absent
    measurement.
    """

    system: str
    n: int = 0
    warnings: int = 0
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0
    base_rate: float = 0.0
    warned_symbols: tuple = ()
    missed_symbols: tuple = ()

    @property
    def precision(self):
        return self.tp / self.warnings if self.warnings else None

    @property
    def recall(self):
        got = self.tp + self.fn
        return self.tp / got if got else None

    @property
    def lift(self):
        if not self.warnings or not self.base_rate:
            return None
        return self.precision / self.base_rate

    def to_dict(self):
        return {
            "system": self.system, "n": self.n, "warnings": self.warnings,
            "tp": self.tp, "fp": self.fp, "fn": self.fn, "tn": self.tn,
            "base_rate": self.base_rate, "precision": self.precision,
            "recall": self.recall, "lift": self.lift,
            "warned_symbols": list(self.warned_symbols),
            "missed_symbols": list(self.missed_symbols),
        }


def score(system, calls, truth):
    """The single scoring path. Every contender is measured here or not at all.

    `truth` is the set of positive symbols. The denominator is the whole universe
    the calls cover, warned or not — scoring a rule over only its own hits gives it
    a different denominator and flatters it.
    """
    seen = tuple(c.symbol for c in calls)
    warned = tuple(c.symbol for c in calls if c.warned)
    positive = frozenset(truth) & frozenset(seen)
    tp = sum(1 for s in warned if s in positive)
    return Result(
        system=system, n=len(seen), warnings=len(warned),
        tp=tp, fp=len(warned) - tp,
        fn=len(positive) - tp, tn=len(seen) - len(warned) - (len(positive) - tp),
        base_rate=len(positive) / len(seen) if seen else 0.0,
        warned_symbols=warned,
        missed_symbols=tuple(s for s in seen if s in positive and s not in warned),
    )


def score_all(calls_by_system, truth):
    """`{system: Result}`, in the insertion order `contenders()` produced."""
    return {name: score(name, calls, truth)
            for name, calls in calls_by_system.items()}


def conditional_lift(base_calls, extra_calls, truth):
    """Step 4: what the four axes add **on top of** momentum, not instead of it.

    Returns `{n_base, n_both, p_base, p_both, lift}` — the positive rate among the
    names momentum warned about, and the positive rate among the subset of those
    the axes also warned about. `lift` is the ratio, and it is None when the
    intersection is empty, which is a statement that the question could not be
    answered rather than an answer of zero.
    """
    truth = frozenset(truth)
    base = [c.symbol for c in base_calls if c.warned]
    extra = {c.symbol for c in extra_calls if c.warned}
    both = [s for s in base if s in extra]
    p_base = (sum(1 for s in base if s in truth) / len(base)) if base else None
    p_both = (sum(1 for s in both if s in truth) / len(both)) if both else None
    return {
        "n_base": len(base), "n_both": len(both),
        "p_base": p_base, "p_both": p_both,
        "lift": (p_both / p_base) if (p_base and p_both is not None) else None,
    }


def measurability(cutoff, symbols, truth, cache=None, thresholds_path=None):
    """How many axes could even be measured, per arm. Read this before the table.

    An axis with no payload behind it never fires, so an arm whose broker panels
    and news coverage were never bought carries a lower ceiling on `axes_fired`
    than the arm that has them. When the two arms differ here, the four-axis row in
    the table is measuring the purchase record and not the model.
    """
    truth = frozenset(truth)
    arms = {"kasus": [], "kontrol": []}
    missing = {"kasus": {}, "kontrol": {}}
    for symbol in symbols:
        p = profile.build(symbol, cache=cache, cutoff=cutoff,
                          thresholds_path=thresholds_path)
        arm = "kasus" if symbol in truth else "kontrol"
        arms[arm].append(p.axes_total - p.axes_unknown)
        for axis in p.unknown_axes:
            missing[arm][axis] = missing[arm].get(axis, 0) + 1
    return {arm: {"n": len(values),
                  "min_measurable": min(values) if values else 0,
                  "max_measurable": max(values) if values else 0,
                  "mean_measurable": (sum(values) / len(values)) if values else 0.0,
                  "missing": dict(sorted(missing[arm].items()))}
            for arm, values in arms.items()}


# --- the gate ---------------------------------------------------------------
@dataclass(frozen=True)
class Gate:
    """The go/no-go decision of `tasks/11`, and the reasons behind it.

    `passed` is True only when the four-axis system's lift is strictly greater than
    **both** baselines'. An undefined lift — the system warned about nothing — is
    not a pass and not a tie; it is a comparison that did not take place.
    """

    passed: bool = False
    adjudicable: bool = True
    reasons: tuple = ()
    blockers: tuple = ()


def gate(results, measured, basket_arms):
    """Decide the gate, and say separately whether it could be decided at all."""
    system = results[SYSTEM]
    opponents = [results[name] for name in baselines.NAMES]
    reasons, blockers = [], []

    ceiling = measured["kontrol"]["max_measurable"]
    case_ceiling = measured["kasus"]["max_measurable"]
    if ceiling != case_ceiling:
        blockers.append(
            f"Ketersediaan data tidak simetris: lengan kasus punya sampai "
            f"{case_ceiling} sumbu terukur, lengan kontrol hanya {ceiling}. "
            f"Sumbu yang datanya tidak dibeli tidak pernah menyala, jadi baris "
            f"empat sumbu mengukur catatan pembelian, bukan modelnya.")
    if system.warnings == 0:
        blockers.append(
            f"Sistem empat sumbu tidak mengeluarkan satu peringatan pun pada "
            f"ambang {config.WARNING_AXES_THRESHOLD} dari 4: lift tidak "
            f"terdefinisi, jadi tidak ada angka untuk dibandingkan.")
    # The circularity, stated with its own evidence. `basket()` builds the control
    # arm out of `universe.control_group()`, whose membership rule is "no suspension
    # of any class on record" — the exact variable this baseline reads. So its false
    # positives cannot exist here, and a rule that cannot be wrong cannot be beaten.
    history_rule = results[baselines.previously_suspended.NAME]
    if basket_arms.controls and history_rule.warnings and history_rule.fp == 0:
        blockers.append(
            f"Lengan kontrol dipilih dengan kriteria 'tidak pernah disuspensi' — "
            f"variabel yang persis dibaca baseline "
            f"{baselines.previously_suspended.NAME}. Di universe ini ia mustahil "
            f"salah ({history_rule.fp} false positive dari {history_rule.warnings} "
            f"peringatan), jadi gerbang 'harus mengalahkan keduanya' tidak bisa "
            f"dimenangkan siapa pun, sebaik apa pun modelnya.")

    for opponent in opponents:
        if system.lift is None or opponent.lift is None:
            reasons.append(f"{system.system} vs {opponent.system}: lift tidak "
                           f"terdefinisi di salah satu sisi — tidak dibandingkan.")
        elif system.lift > opponent.lift:  # strictly greater: a tie is not a win
            reasons.append(f"{system.system} lift {system.lift:.2f} > "
                           f"{opponent.system} {opponent.lift:.2f}")
        else:
            reasons.append(f"{system.system} lift "
                           f"{'-' if system.lift is None else '%.2f' % system.lift}"
                           f" tidak melampaui {opponent.system} "
                           f"{opponent.lift:.2f}")

    passed = (system.lift is not None
              and all(o.lift is not None and system.lift > o.lift for o in opponents))
    return Gate(passed=passed, adjudicable=not blockers,
                reasons=tuple(reasons), blockers=tuple(blockers))


# --- report -----------------------------------------------------------------
def _id(value):
    """Format a number the Indonesian way: comma as the decimal separator."""
    return str(value).replace(".", ",")


def _pct(value):
    return "-" if value is None else _id("%.1f" % (value * 100)) + "%"


def _num(value, fmt="%.2f"):
    return "-" if value is None else _id(fmt % value)


def _lift(value):
    """A lift with no denominator prints as `-`, never as `0,00x`.

    A rule that warned about nothing has an undefined lift. Printing a number
    there would read as a measured defeat instead of an absent measurement, and
    the gate treats the two differently.
    """
    return "-" if value is None else _id("%.2f" % value) + "x"


def report(cutoff=None, cache=None, min_axes=None, thresholds_path=None):
    """Everything `tasks/11` asks for, as one dict. `render()` turns it into text."""
    arms = basket(cache=cache)
    cutoff = cutoff or arms.window_start
    symbols = arms.symbols
    truth = positives(symbols, cutoff, cache=cache)

    calls = contenders(cutoff, symbols, cache=cache, min_axes=min_axes,
                       thresholds_path=thresholds_path)
    results = score_all(calls, truth)
    measured = measurability(cutoff, symbols, truth, cache=cache,
                             thresholds_path=thresholds_path)
    market = labels.base_rates(cache=cache)

    return {
        "cutoff": str(cutoff),
        "window": [arms.window_start, arms.window_end],
        "arms": {"kasus": list(arms.cases), "kontrol": list(arms.controls),
                 "dikeluarkan": list(arms.excluded)},
        "min_axes": config.WARNING_AXES_THRESHOLD if min_axes is None else min_axes,
        "top_n": baselines.momentum.TOP_N,
        "results": {name: r.to_dict() for name, r in results.items()},
        "calls": {name: [c.__dict__ for c in rows] for name, rows in calls.items()},
        "conditional": conditional_lift(calls[baselines.momentum.NAME],
                                        calls[SYSTEM], truth),
        "measurability": measured,
        "market_base_rate": market[-1]["per_stock_10d"] if market else None,
        "gate": gate(results, measured, arms).__dict__,
    }


def render(data):
    """The comparison table, the confusion matrices, and the gate. Descriptive."""
    arms, results = data["arms"], data["results"]
    lines = [
        f"Perbandingan baseline — tugas 11 (0 kredit, dari rekaman)",
        f"  jendela fitur    : {data['window'][0]} .. {data['window'][1]}",
        f"  cutoff           : {data['cutoff']}",
        f"  universe         : {len(arms['kasus']) + len(arms['kontrol'])} emiten "
        f"— {len(arms['kasus'])} kasus, {len(arms['kontrol'])} kontrol",
        f"    kasus          : {', '.join(arms['kasus'])}",
        f"    kontrol        : {', '.join(arms['kontrol'])}",
        f"  ambang sistem    : {data['min_axes']} dari 4 sumbu menyala"
        f"  ·  baseline momentum: {data['top_n']} teratas",
        "",
        "  Setiap pesaing dinilai lewat satu fungsi yang sama (score()), universe "
        "yang sama, dan tanggal yang sama.",
        "",
        f"  {'SISTEM':<24}{'PERINGATAN':>11}{'TRUE POS':>9}{'BASE RATE':>11}"
        f"{'LIFT':>7}{'PRESISI':>9}{'RECALL':>8}",
    ]
    for name, r in results.items():
        lines.append(
            f"  {name:<24}{r['warnings']:>11}{r['tp']:>9}"
            f"{_pct(r['base_rate']):>11}{_lift(r['lift']):>7}"
            f"{_pct(r['precision']):>9}{_pct(r['recall']):>8}")

    lines += ["", "  Confusion matrix penuh (TP / FP / FN / TN):"]
    for name, r in results.items():
        lines.append(
            f"    {name:<24} TP {r['tp']:>2}  FP {r['fp']:>2}  FN {r['fn']:>2}  "
            f"TN {r['tn']:>2}   (n={r['n']})")
        if r["warned_symbols"]:
            lines.append(f"      diperingatkan : {', '.join(r['warned_symbols'])}")
        if r["missed_symbols"]:
            lines.append(f"      terlewat      : {', '.join(r['missed_symbols'])}")

    cond = data["conditional"]
    lines += [
        "",
        "  Kombinasi — apakah empat sumbu menambah sesuatu DI ATAS momentum:",
        f"    momentum menyala pada {cond['n_base']} emiten, "
        f"{_pct(cond['p_base'])} di antaranya berlabel",
        f"    dari situ, {cond['n_both']} juga dinyalakan empat sumbu, "
        f"{_pct(cond['p_both'])} di antaranya berlabel",
        f"    angkat bersyarat : {_lift(cond['lift'])}"
        + ("" if cond["n_both"] else
           "  — irisannya kosong, jadi pertanyaannya tidak terjawab, bukan terjawab nol"),
    ]

    m = data["measurability"]
    lines += ["", "  Sumbu yang benar-benar terukur per lengan (baca ini dulu):"]
    for arm in ("kasus", "kontrol"):
        row = m[arm]
        missing = ", ".join(f"{k} {v}x" for k, v in row["missing"].items()) or "-"
        lines.append(
            f"    {arm:<8} n={row['n']:<3} terukur {row['min_measurable']}.."
            f"{row['max_measurable']} dari 4 (rata-rata "
            f"{_num(row['mean_measurable'], '%.1f')})   tidak terukur: {missing}")

    market = data["market_base_rate"]
    lines += [
        "",
        "  Cara membaca angka di atas:",
        f"    Base rate di set ini {_pct(results[SYSTEM]['base_rate'])} karena "
        f"setnya dirakit kasus-kontrol, bukan sampel pasar. Lift di sini terbatas "
        f"di 2,00x dan hanya berarti untuk membandingkan antar pesaing.",
        f"    Base rate pasar sebenarnya {_pct(market)} per saham per 10 hari bursa "
        f"(app.labels). Lift di set ini bukan lift pasar dan tidak boleh dikutip "
        f"sebagai lift pasar." if market else "",
        "    Jendela fitur beririsan dengan jendela hasil, jadi ini uji pembedaan "
        "antara dua kelompok yang sudah diketahui — bukan uji ramalan. Hold-out "
        "bersih adalah tugas 12.",
        "    Tidak ada ambang yang digeser untuk perbandingan ini.",
    ]

    g = data["gate"]
    lines += ["", "  GERBANG GO/NO-GO:"]
    for reason in g["reasons"]:
        lines.append(f"    - {reason}")
    if g["blockers"]:
        lines.append("")
        lines.append("    Gerbang ini TIDAK BISA DIPUTUSKAN pada universe ini:")
        for blocker in g["blockers"]:
            lines.append(f"    ! {blocker}")
    lines.append("")
    if g["passed"] and g["adjudicable"]:
        lines.append("    HASIL: sistem empat sumbu melampaui kedua baseline. "
                     "Lanjut ke tugas 12.")
    elif g["adjudicable"]:
        lines.append("    HASIL: sistem empat sumbu TIDAK melampaui kedua baseline. "
                     "Berhenti — jangan lanjut ke tugas 12.")
    else:
        lines.append("    HASIL: BERHENTI. Bukan karena modelnya kalah, tapi karena "
                     "perbandingannya belum sah. Perbaiki penghalang di atas "
                     "sebelum tugas 12; menyetel ambang untuk memenangkannya "
                     "dilarang (tugas 11 §Jangan).")
    return "\n".join(line for line in lines if line is not None)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Bandingkan sistem empat sumbu dengan baseline naif. 0 kredit.")
    parser.add_argument("--compare-baselines", action="store_true",
                        help="cetak tabel perbandingan dan putusan gerbang")
    parser.add_argument("--cutoff", default=None,
                        help="tanggal cutoff; bawaan: awal jendela rekaman")
    parser.add_argument("--json", action="store_true",
                        help="keluarkan JSON mentah, bukan tabel")
    args = parser.parse_args(argv)

    if not args.compare_baselines and not args.json:
        parser.print_help()
        return 0

    data = report(cutoff=args.cutoff)
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str)
          if args.json else render(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
