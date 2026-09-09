"""Baseline "pernah disuspensi" — the second competitor, and it may well win.

`riset/red-team.md` §A1 named one baseline to beat: five-day momentum. The
feasibility pass found a second one. 353 of 452 cooling-down events (78%) belong to
symbols that appear in the label set more than once (`riset/temuan-kelayakan.md`
§Q4 finding 3), so a rule with no model in it at all —

    warn every stock that has ever been suspended

— is a serious opponent. In the working universe it fires on **98 of 200** names,
which is both its strength and the thing that will be held against it: a rule that
warns half the board buys its recall very expensively. Measuring that trade-off is
task 11's job, not this module's; this module only has to make the competitor real,
and make it play on exactly the same field.

**Same field means three things, all enforced here.**

1. *Same universe.* `run()` defaults to `universe.watchlist()` and returns one
   `Prediction` per member — including the ones it does **not** warn. A baseline
   evaluated only over the names it fired on would be scored against a different
   denominator than the four-axis system and would look better for it.
2. *Same time separation.* The cutoff is a required argument and the only path to
   history is `app.axes.history`, hence `labels.history_before`. The baseline gets
   no privilege the main system does not have; if it wins, it wins on data that was
   visible on the day.
3. *Same code path later.* `Prediction` is deliberately a plain record of
   `(symbol, cutoff, warned, features)` so task 11's `evaluate.py` can score all
   three contenders through one function.

**This is not a straw man** (`tasks/08-sumbu-riwayat.md` §Jangan). If it beats the
four-axis system, that is the finding and it gets reported. Worth knowing before
the comparison is run: measured with a cutoff instead of in hindsight, only 225 of
452 cooling-down events (50%) had any prior suspension visible on the day — so the
78% headline overstates what this rule can actually see.

`warned` here is a baseline's mechanical output for an offline comparison. It is not
product output and never reaches a reader: what the product shows is
`app.axes.history.describe`, which states the record and draws no conclusion.

Zero credits: reads only what `app.labels` and `app.universe` already hold.
"""
from dataclasses import dataclass

from app import universe
from app.axes import history

NAME = "pernah_disuspensi"

# The rule, in full: one prior suspension of any class is enough. Not a tuned
# parameter and not read from `state/thresholds.json` — a baseline that moves with
# the system it is measuring against stops being a fixed yardstick.
MIN_PRIOR = 1


@dataclass(frozen=True)
class Prediction:
    """One symbol's baseline call at one cutoff, warned or not.

    Carries the features it fired on so a disagreement with the four-axis system can
    be read rather than guessed at.
    """

    symbol: str
    cutoff: str
    warned: bool
    n_prior: int = 0
    n_prior_label: int = 0
    days_since_last: int = None
    last_reason_class: str = ""

    @property
    def baseline(self):
        return NAME


def predict(symbol, cutoff, cache=None):
    """The baseline's call for one symbol as of `cutoff`.

    Every field comes from the history axis, which reads through
    `labels.history_before`. There is no second route, so this cannot see an event
    dated on or after the cutoff even by accident.
    """
    measured = history.score(symbol, cutoff, cache=cache)
    return Prediction(
        symbol=measured.symbol,
        cutoff=measured.cutoff,
        warned=measured.n_prior >= MIN_PRIOR,
        n_prior=measured.n_prior,
        n_prior_label=measured.n_prior_label,
        days_since_last=measured.days_since_last,
        last_reason_class=measured.last_reason_class,
    )


def run(cutoff, symbols=None, size=universe.DEFAULT_SIZE, cache=None):
    """A prediction for **every** member of the universe, in universe order.

    `symbols=None` means the same working universe the four-axis system screens, so
    the two are comparable by construction. Passing an explicit list is for tests
    and for task 11's own splits; it is not a way to quietly narrow the field.
    """
    names = list(symbols) if symbols is not None else universe.watchlist(
        size=size, cache=cache)
    return tuple(predict(name, cutoff, cache=cache) for name in names)


def warned(predictions):
    """Only the symbols the rule fired on — a view, never the evaluation set."""
    return tuple(p for p in predictions if p.warned)


# --- description ------------------------------------------------------------
def _id(value):
    """Format a number the Indonesian way: comma as the decimal separator."""
    return str(value).replace(".", ",")


def describe(predictions):
    """A descriptive account of what the baseline would have flagged. No verdict."""
    if not predictions:
        return (f"Baseline {NAME}: universe kosong — tidak ada yang bisa dinilai.")

    hits = warned(predictions)
    cutoff = predictions[0].cutoff
    share = len(hits) / len(predictions) * 100
    repeat_cooling = sum(1 for p in hits if p.n_prior_label > 0)
    recent = [p.days_since_last for p in hits if p.days_since_last is not None]

    lines = [
        f"Baseline {NAME} — lawan tanding, per {cutoff} (0 kredit, dari rekaman)",
        f"  aturan           : peringatkan tiap saham dengan >= {MIN_PRIOR} suspensi "
        f"sebelum cutoff, kelas apa pun",
        f"  universe         : {len(predictions)} emiten — sama persis dengan yang "
        f"di-screen sistem utama",
        f"  diperingatkan    : {len(hits)} ({_id('%.0f' % share)}%)",
        f"  di antaranya pernah cooling-down: {repeat_cooling}",
    ]
    if recent:
        recent.sort()
        median = recent[len(recent) // 2]
        lines.append(f"  jarak dari suspensi terakhir: {min(recent)} .. {max(recent)} hari, "
                     f"median {median}")
    lines += [
        "  Baseline ini tidak dipakai sebagai keluaran produk. Ia ada untuk dikalahkan, "
        "dan kalau ia menang itu dilaporkan (tugas 11).",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    from datetime import date

    when = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    print(describe(run(when)))
