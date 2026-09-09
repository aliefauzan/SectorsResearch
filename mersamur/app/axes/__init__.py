"""The axes, and the one place their thresholds come from.

A profile is *how many axes fired and which* — not a weighted average
(`riset/spec.md` §5). Each module in this package answers one question about one
symbol, from data that is already paid for, and says nothing about what to do
about the answer.

**Thresholds are data, never constants.** Every number that decides `fired` is
read from `state/thresholds.json` at call time, because task 17 moves those
numbers automatically and a threshold compiled into a module cannot be moved,
rolled back, or pointed at in a video. That file also carries its own change
history, so any version of it can be reconstructed — the writer and its schema
validation belong to task 14; this module only reads.

Two things are read here:

  * `current[axis]`   — the bar an axis fires against, clamped into `bounds[axis]`;
  * `cohort_factors`  — a multiplier on that bar, per broker cohort.

The factor moves the **bar**, never the measurement. A stock's measured
concentration is a fact about the tape and stays exactly what it is; what changes
by cohort is how notable that fact is. Retail-dominated concentration in a thin
stock is the pattern the product is looking for (`riset/temuan-kelayakan.md` §Q1:
one retail broker, `XL`, was top buyer in 7 of 10 suspended names), so a retail
top buyer lowers the bar and an institutional one raises it. Mutating the ratio
instead would leave a number on screen that matches nothing in the API response.

Zero credits: nothing in this package opens a socket.
"""
import json
import os

from app import config

THRESHOLDS_PATH = os.path.join(config.STATE_DIR, "thresholds.json")

# Applied when a cohort is absent from `cohort_factors` — including the registry's
# own literal `"unknown"` cohort, and the case where the top buyer's code is not in
# `/v2/brokers/` at all. Neutral: an unrecognised cohort must not silently move a bar.
NEUTRAL_FACTOR = 1.0


class ThresholdsUnavailable(Exception):
    """`state/thresholds.json` is missing or unreadable.

    Raised rather than defaulted. A fallback constant here would be exactly the
    hardcoded threshold this package exists to avoid, and it would fire silently:
    the axis would keep answering, against a bar nobody chose and no history
    records.
    """


_CACHED = {}


def load_thresholds(path=None, reload=False):
    """The threshold document, loaded once per path.

    `path` is injectable so a test can assert that the bar really does come from
    the file — an implementation with the number baked in passes every test that
    only ever reads the shipped document.
    """
    key = path or THRESHOLDS_PATH
    if reload or key not in _CACHED:
        try:
            with open(key, encoding="utf-8") as fh:
                _CACHED[key] = json.load(fh)
        except (OSError, ValueError) as exc:
            raise ThresholdsUnavailable(
                f"Ambang tidak terbaca di {key}: {exc}. "
                f"Sumbu tidak dijalankan dengan angka bawaan — ambang adalah data, "
                f"bukan konstanta di dalam kode."
            ) from None
    return _CACHED[key]


def version(path=None):
    """Which version of the thresholds an answer was computed against."""
    return load_thresholds(path).get("version")


def bounds(axis, path=None):
    """`(floor, ceiling)` for an axis, or `(None, None)` when it has none."""
    row = (load_thresholds(path).get("bounds") or {}).get(axis) or {}
    return row.get("floor"), row.get("ceiling")


def threshold(axis, path=None):
    """The current bar for `axis`, clamped into its own floor/ceiling.

    The clamp is a safety net for task 17: the evolve step moves these values
    automatically, and a run that walks a threshold past the human-set bound should
    be capped at the bound rather than obeyed. Reading it back through the clamp
    means every consumer sees the same capped number.
    """
    current = load_thresholds(path).get("current") or {}
    if axis not in current:
        raise ThresholdsUnavailable(
            f"Ambang untuk sumbu {axis!r} tidak ada di {path or THRESHOLDS_PATH}."
        )
    value = float(current[axis])
    floor, ceiling = bounds(axis, path)
    if floor is not None:
        value = max(value, float(floor))
    if ceiling is not None:
        value = min(value, float(ceiling))
    return value


def cohort_factor(cohort, path=None):
    """The multiplier applied to a bar for a given broker cohort. 1,0 when unknown."""
    factors = load_thresholds(path).get("cohort_factors") or {}
    try:
        return float(factors[cohort])
    except (KeyError, TypeError, ValueError):
        return NEUTRAL_FACTOR
