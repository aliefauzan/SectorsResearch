#!/usr/bin/env python3
"""Task 17 — the SETEL step: the layer that changes its own parameters.

    python3 app/agent/evolve.py --dry-run    # propose, run the guards, write nothing
    python3 app/agent/evolve.py              # apply what passes all five guards
    python3 app/agent/evolve.py --reset      # kill switch: undo every evolve change

This is the piece Track 01's bar names explicitly — *lapisan yang mengubah
parameternya sendiri* — and the piece most easily turned into overfitting wearing
a changelog. `research/plan/pump-and-dump/agen-risiko-belajar-mandiri.md` says the
quiet part: `yunus-0x/meridian` moves its bars after five closed positions, and
five is far too few here; copying it produces an agent that learns noise and then
presents the noise as insight.

## The one rule that shapes the whole module: two regimes, never mixed

`riset/red-team.md` §A3 is a contradiction inside the spec itself. §6 asks for
twenty settled warnings per axis before a bar moves. With a base rate of 0,77% per
stock per ten sessions, fourteen days of live running yields three to five true
positives. No axis will ever reach twenty on forward data — so either the bars
never move, or the guards get broken for one video scene and the video shows
overfitting to a panel of judges.

The way out is not a smaller N. It is two regimes, kept apart in code:

    tuning     historical replay, walk-forward, hundreds of events   bars move here
    forward    the daily run from now on, 3-5 events                 validates only

Every warning carries its date in its own id (`w-YYYYMMDD-SYMBOL`), so the split
is a function of the row and needs nothing else. `propose()` is handed the tuning
slice and *only* the tuning slice; the hold-out slice reaches a different function
entirely. That is not a naming convention — `test_evolve.py` asserts the proposal
is byte-identical when the hold-out slice is replaced wholesale.

## What "hold-out" is allowed to do, and what it is not

Guard 4 is the one that is easy to get subtly wrong. A loop that refuses to move a
bar *because the hold-out number got worse* has used the hold-out to select, and
the moment it does that it is not a hold-out any more — it is a slower, more
expensive validation set, and the number it reports about itself means nothing.

So the hold-out here is report-only, and the guard is about **computability**, not
about direction:

  * it passes when a hold-out precision can be computed both before and after;
  * it fails when the axis has no hold-out lessons at all, or when the proposed bar
    would silence every hold-out warning, leaving no precision to compute;
  * it **never** fails because the number went down.

A shift that makes the hold-out worse is applied, recorded, and printed as having
made it worse. `research/plan/pump-and-dump/agen-risiko-belajar-mandiri.md` asks
for exactly that: *"Kalau performa hold-out tidak membaik, katakan itu di video"*.
The task's own §Jangan says the same thing in stronger words. Hiding it would be
the one failure this module cannot recover from.

## What moves a bar

Two numbers per axis, both already computed by task 16's `aggregate()`: the mean
margin of the true positives, and the mean margin of the false positives. Margin
is signed so positive always means "past the bar", whichever way that axis reads.

If the false positives cleared the bar by *less*, on average, than the true
positives did, then a bar sitting between the two means removes more misses than
hits — a one-dimensional separator, explainable out loud in a video. The bar moves
`LEARNING_RATE` of the way to the false-positive mean, capped by guard 2.

If the false positives cleared it by *more* — the margin does not separate hits
from misses on that axis — the bar does not move, and the reason says so. That is
a negative finding about the axis, not a failure of the run.

## The kill switch

`--reset` restores every axis to the value it held **before the first automatic
change** — the human-set bar, reconstructed from `thresholds.json.history` by
walking the `source: "evolve"` entries backwards.

It is deliberately not `ledger.rollback(1)`. Version 1 of the shipped file carried
one axis; the other three were added later by hand, and rolling back to it would
delete them — `ledger.rollback` refuses that outright, and correctly. The kill
switch's job is to undo what the machine did, not to undo what the team did. On a
document whose bars were all set by hand it is a no-op, and says so.

Zero credits. Lessons and thresholds are local files; no client is imported here,
so nothing in this module can open a socket.
"""
import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import backtest, labels, ledger  # noqa: E402
from app.agent import lessons as lessons_mod  # noqa: E402

# --- the five guards, as numbers --------------------------------------------
# Guard 1. Twenty settled warnings on that axis, in the tuning set. `spec.md` §6's
# number, kept rather than lowered: the whole point of the historical replay is
# that it is the regime where twenty is reachable.
MIN_RESOLVED = 20

# Guard 2. One iteration moves a bar by at most a tenth of its own value. A bigger
# jump is a symptom of noise, not of signal.
MAX_STEP_FRACTION = 0.10

# How far toward the false-positive mean margin one iteration travels. Below 1.0 on
# purpose: the mean of a sample of twenty is itself noisy, and stepping the whole
# way to it treats an estimate as a measurement. Guard 2 caps whatever comes out.
LEARNING_RATE = 0.5

# Guard 4. The date from which lessons are report-only. Imported rather than
# restated so the split this module honours is the same one `app.backtest` measured
# lift across; two different boundaries would make the two reports incomparable.
DEFAULT_HOLDOUT = backtest.DEFAULT_HOLDOUT

# The window of lessons a proposal is built from. `None` means "all of them" —
# unlike the screen, which only wants recent lessons, tuning wants every settled
# event it has, because guard 1 is a count.
DEFAULT_WINDOW_DAYS = None

# Which axes read their bar downwards, so tightening means *lowering* it. Taken
# from task 16, which takes it from `profile.DIRECTIONS`, so an axis that changes
# direction changes it in one place only.
FIRES_BELOW = lessons_mod.FIRES_BELOW

TUNING = backtest.SPLIT_TUNING
HOLDOUT = backtest.SPLIT_HOLDOUT

GUARD_NAMES = ("n_minimum", "batas_langkah", "lantai_langit", "hold_out")

# Every id `ledger.WARNING_ID_RE` accepts carries its date in the middle.
_ID_DATE_RE = re.compile(r"^w-(\d{4})(\d{2})(\d{2})-")


# --- the split --------------------------------------------------------------
def warning_date(warning_id):
    """The date a warning was issued, read out of its own id. None when unreadable.

    A lesson row does not carry the warning's date — only `written_on`, which is
    the day the lesson was written and can be months later. Using `written_on` to
    split would put a historical replay event into the hold-out slice purely
    because the replay was run today, which is the leak this split exists to stop.
    """
    match = _ID_DATE_RE.match(str(warning_id or ""))
    if not match:
        return None
    try:
        return date(*(int(part) for part in match.groups()))
    except ValueError:
        return None


def split_lessons(rows, holdout=None):
    """`{tuning: [...], hold_out: [...]}`. A row with no readable date is dropped.

    Dropped, not defaulted into the tuning set: a row that cannot be dated cannot
    be proven to precede the hold-out boundary, and "probably historical" is
    exactly the assumption that makes a leak invisible.
    """
    boundary = holdout or DEFAULT_HOLDOUT
    out = {TUNING: [], HOLDOUT: []}
    for row in rows or []:
        when = warning_date(row.get("warning_id"))
        if when is None:
            continue
        out[backtest.split_of(when, boundary)].append(row)
    return out


# --- the proposal -----------------------------------------------------------
@dataclass(frozen=True)
class Proposal:
    """One axis' suggested bar, and every number that produced it.

    Frozen: a proposal is evaluated by the guards and then either applied or
    recorded as refused. A guard that could edit the thing it is checking would be
    a formality.
    """

    axis: str
    current: float
    proposed: float
    delta: float                 # movement in margin units, always >= 0
    n: int                       # settled tuning lessons on this axis
    true_positive: int = 0
    false_positive: int = 0
    margin_true_positive: float = None
    margin_false_positive: float = None
    separation: float = None
    evidence: tuple = ()
    rationale: str = ""

    @property
    def fraction(self):
        """Movement as a share of the current bar. `None` when the bar is zero."""
        if not self.current:
            return None
        return abs(self.proposed - self.current) / abs(float(self.current))


def _number(value):
    """A float, or None. Booleans are values, never numbers."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _format(value):
    """A number the way the output should read it: no trailing zeros, no `1e-05`.

    Its own copy rather than a reach into task 16's private helper — each module in
    this package owns its display helpers (`backtest._pct`, `lessons._format`), and
    a formatter imported across a module boundary is a dependency that buys nothing.
    """
    number = _number(value)
    if number is None:
        return "tidak diukur"
    if number == int(number) and abs(number) < 1e15:
        return str(int(number))
    return f"{number:.4f}".rstrip("0").rstrip(".")


def _tighten(axis, bar, delta):
    """The bar moved `delta` in the direction that makes the axis harder to fire."""
    return bar - delta if axis in FIRES_BELOW else bar + delta


def propose(tuning_rows, doc, axes=None):
    """One `Proposal` per axis the tuning set has anything to say about.

    Reads `tuning_rows` and the threshold document. Nothing else — no hold-out
    rows are in scope here, and `test_evolve.py` holds this function to that by
    swapping the hold-out slice underneath it and demanding the same output.

    An axis with a proposal of zero movement is still returned: "twenty lessons and
    the margins do not separate" is a finding worth printing, and dropping it would
    make an axis that refuses to move indistinguishable from one nobody looked at.
    """
    counts = lessons_mod.aggregate(lessons=list(tuning_rows), days=None)["by_axis"]
    current = doc.get("current") or {}
    wanted = list(axes) if axes is not None else sorted(counts)

    out = []
    for axis in wanted:
        stats = counts.get(axis)
        bar = _number(current.get(axis))
        if not stats or bar is None:
            continue
        hits = _number(stats.get("margin_mean_true_positive"))
        misses = _number(stats.get("margin_mean_false_positive"))
        evidence = tuple(sorted(row["warning_id"] for row in tuning_rows
                                if row.get("axis_implicated") == axis
                                and row.get("warning_id")))
        separation = None if hits is None or misses is None else hits - misses

        delta, why = 0.0, ""
        if misses is None:
            why = ("belum ada peringatan meleset dengan margin terukur di sumbu ini, "
                   "jadi tidak ada jarak yang bisa dijadikan dasar pergeseran")
        elif misses <= 0:
            why = (f"peringatan yang meleset rata-rata tidak melewati ambang "
                   f"({_format(misses)}), jadi menggeser ambang tidak "
                   f"akan menyingkirkannya")
        elif separation is None:
            why = ("belum ada peringatan tepat dengan margin terukur, jadi tidak "
                   "bisa dibandingkan apakah ambang memisahkan tepat dari meleset")
        elif separation <= 0:
            why = (f"margin tidak memisahkan: yang meleset rata-rata melewati ambang "
                   f"{_format(misses)}, yang tepat hanya "
                   f"{_format(hits)}. Menggeser ambang akan membuang "
                   f"lebih banyak yang tepat daripada yang meleset")
        else:
            raw = LEARNING_RATE * misses
            cap = MAX_STEP_FRACTION * abs(bar)
            delta = min(raw, cap)
            why = (f"yang meleset rata-rata melewati ambang "
                   f"{_format(misses)}, yang tepat "
                   f"{_format(hits)}; ambang digeser "
                   f"{_format(delta)} ke arah yang lebih ketat"
                   + (" (dipotong batas langkah 10%)" if raw > cap else ""))

        out.append(Proposal(
            axis=axis, current=bar, proposed=_tighten(axis, bar, delta), delta=delta,
            n=int(stats.get("lessons") or 0),
            true_positive=int(stats.get("true_positive") or 0),
            false_positive=int(stats.get("false_positive") or 0),
            margin_true_positive=hits, margin_false_positive=misses,
            separation=separation, evidence=evidence, rationale=why))
    return out


# --- the hold-out numbers, computed after the proposal is already fixed ------
def _precision(rows):
    """Share of settled lessons that were true positives, or None for an empty set."""
    if not rows:
        return None
    hits = sum(1 for row in rows if row.get("outcome") == "true_positive")
    return round(hits / len(rows), 6)


@dataclass(frozen=True)
class Holdout:
    """What the untouched slice says about a proposal. Reported, never obeyed."""

    axis: str
    before: float = None
    after: float = None
    n_before: int = 0
    n_after: int = 0

    @property
    def computable(self):
        return self.before is not None and self.after is not None

    @property
    def improved(self):
        if not self.computable:
            return None
        return self.after > self.before


def holdout_numbers(proposal, holdout_rows):
    """Hold-out precision on this axis, before and after the proposed bar.

    "After" is simulated rather than replayed: a hold-out lesson recorded how far
    its axis cleared the bar, so a bar tightened by `delta` keeps exactly the rows
    whose margin was at least `delta`. That reuses the number already on the row
    and needs no second scoring path — the same discipline `app.backtest` keeps by
    never writing a second lift formula.
    """
    rows = [row for row in holdout_rows
            if row.get("axis_implicated") == proposal.axis
            and _number(row.get("margin")) is not None]
    survivors = [row for row in rows if _number(row["margin"]) >= proposal.delta]
    return Holdout(axis=proposal.axis, before=_precision(rows),
                   after=_precision(survivors),
                   n_before=len(rows), n_after=len(survivors))


# --- the guards -------------------------------------------------------------
@dataclass(frozen=True)
class Guard:
    name: str
    passed: bool
    detail: str


def check_guards(proposal, doc, holdout):
    """The four gates a proposal passes before a bar moves. Guard 5 is the CLI.

    Every guard is evaluated — none short-circuits — because "which guard stopped
    it" is the interesting half of a refusal, and a run that stops at the first
    failure can only ever name one.

    Note what guard 2 does on a proposal that asks for more than a tenth: it
    **refuses**, it does not clamp. `propose()` already caps its own step, so this
    fires only on a proposal from somewhere else — a hand-written one, a future
    proposer, a bug — and silently shrinking such a proposal to the legal maximum
    would apply a movement nobody computed.
    """
    axis, bar, new = proposal.axis, proposal.current, proposal.proposed
    row = ((doc.get("bounds") or {}).get(axis)) or {}
    floor, ceiling = _number(row.get("floor")), _number(row.get("ceiling"))

    out = [Guard("n_minimum", proposal.n >= MIN_RESOLVED,
                 f"{proposal.n} peringatan selesai di set penyetelan "
                 f"(minimum {MIN_RESOLVED})")]

    limit = MAX_STEP_FRACTION * abs(bar)
    moved = abs(new - bar)
    share = proposal.fraction
    out.append(Guard(
        "batas_langkah", moved <= limit + 1e-12,
        (f"pergeseran {_format(moved)} dari ambang "
         f"{_format(bar)}"
         + (f" = {share * 100:.1f}%" if share is not None else " (ambang nol)")
         + f", batas {MAX_STEP_FRACTION * 100:.0f}%")))

    inside = ((floor is None or new >= floor) and (ceiling is None or new <= ceiling))
    out.append(Guard(
        "lantai_langit", inside,
        f"usulan {_format(new)} terhadap lantai "
        f"{'—' if floor is None else _format(floor)} dan langit-langit "
        f"{'—' if ceiling is None else _format(ceiling)}"))

    if holdout.computable:
        detail = (f"presisi hold-out {holdout.before:.3f} ({holdout.n_before} "
                  f"pelajaran) -> {holdout.after:.3f} ({holdout.n_after} bertahan)")
    elif holdout.n_before == 0:
        detail = ("hold-out tidak memuat satu pelajaran pun di sumbu ini, jadi "
                  "tidak ada angka yang bisa dilaporkan tentang perubahan ini")
    else:
        detail = (f"usulan menyunyikan seluruh {holdout.n_before} peringatan "
                  f"hold-out di sumbu ini, jadi presisi sesudahnya tidak terdefinisi")
    out.append(Guard("hold_out", holdout.computable, detail))
    return out


# --- one decision -----------------------------------------------------------
@dataclass
class Decision:
    """A proposal, its hold-out numbers, its guards, and what was done about it."""

    proposal: Proposal
    holdout: Holdout
    guards: list = field(default_factory=list)
    applied: bool = False
    version: int = None

    @property
    def failed(self):
        return [g for g in self.guards if not g.passed]

    @property
    def allowed(self):
        """Every guard passed **and** the proposal actually asks for a movement."""
        return not self.failed and self.proposal.delta > 0

    def reason(self):
        """The sentence written into `thresholds.json.history`. Indonesian, factual."""
        p, h = self.proposal, self.holdout
        note = ""
        if h.computable:
            direction = ("naik" if h.improved else
                         "turun" if h.after < h.before else "tidak berubah")
            note = (f" Presisi hold-out {h.before:.3f} -> {h.after:.3f} ({direction}); "
                    f"hold-out tidak dipakai memilih pergeseran ini, hanya melaporkannya.")
        return (f"Sumbu {p.axis}: {p.n} peringatan selesai di set penyetelan "
                f"({p.true_positive} tepat, {p.false_positive} meleset). "
                f"{p.rationale}.{note}")

    def refusal(self):
        return "; ".join(f"{g.name}: {g.detail}" for g in self.failed)


def decide(tuning_rows, holdout_rows, doc, axes=None):
    """Every axis' proposal, its hold-out numbers and its guards. Writes nothing."""
    out = []
    for proposal in propose(tuning_rows, doc, axes=axes):
        holdout = holdout_numbers(proposal, holdout_rows)
        out.append(Decision(proposal=proposal, holdout=holdout,
                            guards=check_guards(proposal, doc, holdout)))
    return out


def plan(lessons=None, lessons_path=None, thresholds_path=None, holdout=None,
         days=DEFAULT_WINDOW_DAYS, today=None):
    """`(split, decisions, doc)` for the current state. Reads only, writes nothing."""
    doc = ledger.load_thresholds(thresholds_path)
    rows = (list(lessons) if lessons is not None
            else lessons_mod.recent(days=days, today=today, path=lessons_path))
    split = split_lessons(rows, holdout=holdout)
    return split, decide(split[TUNING], split[HOLDOUT], doc), doc


def run(lessons=None, lessons_path=None, thresholds_path=None, holdout=None,
        days=DEFAULT_WINDOW_DAYS, today=None, dry_run=False, on=None):
    """Apply every decision that cleared all four guards. `(split, decisions, doc)`.

    One `record_change` per axis, so one version carries one axis' evidence and one
    axis' hold-out pair. Batching two axes into a single version would attach one
    `n_resolved` to two different counts, and the history entry would be unreadable
    a month later.
    """
    split, decisions, doc = plan(lessons=lessons, lessons_path=lessons_path,
                                 thresholds_path=thresholds_path, holdout=holdout,
                                 days=days, today=today)
    if dry_run:
        return split, decisions, doc

    for decision in decisions:
        if not decision.allowed:
            continue
        p, h = decision.proposal, decision.holdout
        doc = ledger.record_change(
            {p.axis: p.proposed}, reason=decision.reason(), on=on, source="evolve",
            n_resolved=p.n, holdout_before=h.before, holdout_after=h.after,
            evidence=list(p.evidence), path=thresholds_path)
        decision.applied = True
        decision.version = doc["version"]
    return split, decisions, doc


# --- guard 5: the kill switch ------------------------------------------------
def baseline(doc):
    """Each axis' bar as it stood before the first automatic change.

    Walks the history backwards and, for every `source: "evolve"` entry, restores
    that entry's `from`. An axis no evolve entry ever touched keeps its current
    value — the kill switch undoes the machine, not the team.
    """
    out = dict(doc.get("current") or {})
    for entry in reversed(doc.get("history") or []):
        if entry.get("source") != "evolve":
            continue
        axis, previous = entry.get("axis"), entry.get("from")
        if axis in out and previous is not None:
            out[axis] = previous
    return out


def reset(reason=None, thresholds_path=None, on=None, dry_run=False):
    """Restore every automatically-moved bar to its pre-evolve value.

    Recorded as a *forward* version with `source: "rollback"`, the same way
    `ledger.rollback` does it and for the same reason: rewinding the version number
    would erase the record of the changes being undone, and a kill switch nobody
    can see was pressed is not an auditable one.
    """
    doc = ledger.load_thresholds(thresholds_path)
    target = baseline(doc)
    changes = {axis: value for axis, value in target.items()
               if doc["current"].get(axis) != value}
    if not changes or dry_run:
        return changes, doc
    text = reason or "tombol mati dijalankan dari app/agent/evolve.py --reset"
    doc = ledger.record_change(
        changes, reason=f"reset ke nilai awal sebelum evolusi: {text}",
        on=on, source="rollback", path=thresholds_path)
    return changes, doc


# --- CLI ---------------------------------------------------------------------
def _split_line(split, boundary):
    return (f"pelajaran: {len(split[TUNING])} di set penyetelan (T < {boundary}), "
            f"{len(split[HOLDOUT])} di hold-out (T >= {boundary}, tidak pernah "
            f"dipakai menyetel)")


def render(split, decisions, doc, boundary, dry_run):
    """A descriptive account of the step. No verdict on any stock, only on bars."""
    lines = [f"ambang versi {doc['version']} ({doc['updated_on']})",
             _split_line(split, boundary)]
    if not decisions:
        lines.append("tidak ada sumbu yang punya pelajaran selesai — "
                     "tidak ada ambang yang diusulkan bergerak.")
        return "\n".join(lines)

    for decision in decisions:
        p = decision.proposal
        if decision.applied:
            mark = f"DIGESER -> versi {decision.version}"
        elif decision.allowed:
            mark = "AKAN DIGESER" if dry_run else "DIGESER"
        elif decision.failed:
            mark = "DITOLAK"
        else:
            mark = "TIDAK DIGESER"
        lines.append(
            f"  {p.axis}: {_format(p.current)} -> "
            f"{_format(p.proposed)} · N={p.n} "
            f"({p.true_positive} tepat / {p.false_positive} meleset) · {mark}")
        lines.append(f"    dasar : {p.rationale}")
        for guard in decision.guards:
            lines.append(f"    [{'lolos' if guard.passed else 'GAGAL'}] "
                         f"{guard.name}: {guard.detail}")
        if decision.holdout.computable and decision.holdout.improved is False:
            lines.append("    catatan: hold-out TIDAK membaik. Pergeseran tetap "
                         "dijalankan — hold-out melaporkan, tidak memilih.")
    return "\n".join(lines)


def render_reset(changes, doc, dry_run):
    if not changes:
        return (f"tidak ada ambang yang pernah digeser evolve — "
                f"tombol mati tidak mengubah apa pun (versi {doc['version']}).")
    verb = "akan dikembalikan" if dry_run else "dikembalikan"
    lines = [f"{len(changes)} ambang {verb} ke nilai sebelum evolusi:"]
    for axis, value in sorted(changes.items()):
        lines.append(f"  {axis}: {_format(doc['current'].get(axis))} -> "
                     f"{_format(value)}")
    if not dry_run:
        lines.append(f"ambang sekarang versi {doc['version']} ({doc['updated_on']}).")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Langkah SETEL: ambang bergerak di set penyetelan, berpagar lima.")
    ap.add_argument("--dry-run", action="store_true",
                    help="usulkan dan jalankan pagarnya, jangan tulis apa pun")
    ap.add_argument("--reset", action="store_true",
                    help="tombol mati: kembalikan setiap ambang ke nilai sebelum "
                         "evolusi pertama")
    ap.add_argument("--holdout", metavar="YYYY-MM-DD",
                    default=DEFAULT_HOLDOUT.isoformat(),
                    help=f"batas hold-out (default {DEFAULT_HOLDOUT.isoformat()})")
    ap.add_argument("--days", type=int, default=None,
                    help="batasi pelajaran ke N hari terakhir (default: semuanya)")
    args = ap.parse_args(argv)

    if args.reset:
        changes, doc = reset(dry_run=args.dry_run)
        print(render_reset(changes, doc, args.dry_run))
        return 0

    boundary = labels.parse_date(args.holdout)
    if boundary is None:
        print(f"--holdout harus bertanggal YYYY-MM-DD; dapat {args.holdout!r}")
        return 2

    split, decisions, doc = run(holdout=boundary, days=args.days,
                                dry_run=args.dry_run)
    print(render(split, decisions, doc, boundary.isoformat(), args.dry_run))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
