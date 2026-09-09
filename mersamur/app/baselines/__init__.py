"""The competitors — the rules the four-axis system has to beat to exist.

`riset/red-team.md` §A1 names one (five-day momentum) and calls failing to beat it
fatal: *"Kalau tidak mengalahkannya, Anda tidak punya produk."* The feasibility
pass found a second one, because 78% of cooling-down events belong to symbols that
were suspended before (`riset/temuan-kelayakan.md` §Q4), so "warn every stock with
a record" is a serious rule with no model in it at all.

Both live here rather than inside `app/axes/` for a reason that is about honesty
rather than tidiness: a baseline must not be able to drift toward the system it is
scored against. Nothing in this package reads `state/thresholds.json`, so task 17's
evolve step cannot move a baseline's bar, and nothing here is used by
`app.profile`. The two rules are fixed yardsticks.

**One shared shape.** Every baseline exposes

    NAME
    run(cutoff, symbols=None, size=…, cache=None) -> tuple[Prediction]
    warned(predictions) -> tuple[Prediction]
    describe(predictions) -> str

and every `Prediction` carries at least `(symbol, cutoff, warned)`. That is what
lets `app.evaluate` score all contenders through a single function instead of one
scoring path per system — `tasks/11-baseline-pembanding.md` §1 makes any difference
in the evaluation path grounds for calling the comparison invalid.

`run()` returns one prediction per member of the universe, **including the ones it
does not warn**. A rule scored only over its own hits is scored against a different
denominator and looks better for it.

`warned` is a mechanical offline output. No baseline reaches a reader: what the
product shows is `app.axes.history.describe`, which states a record and draws no
conclusion.

Zero credits: everything here reads `research/harness/recorded/`.
"""
from app.baselines import momentum, previously_suspended

# Registry, in the order §A1 and §Q4 raised them. `app.evaluate` iterates this so
# adding a competitor is a one-line change there and no change at all in the
# scoring path.
BASELINES = (momentum, previously_suspended)
NAMES = tuple(module.NAME for module in BASELINES)


def get(name):
    """The baseline module registered under `name`, or KeyError."""
    for module in BASELINES:
        if module.NAME == name:
            return module
    raise KeyError(f"baseline {name!r} tidak terdaftar; yang ada: {', '.join(NAMES)}")


def run(name, cutoff, symbols=None, cache=None, **kwargs):
    """One baseline's predictions over one universe at one cutoff."""
    return get(name).run(cutoff, symbols=symbols, cache=cache, **kwargs)


def run_all(cutoff, symbols=None, cache=None):
    """`{name: predictions}` for every registered baseline, same universe, same date.

    No per-baseline keyword arguments are threaded through: each competitor runs
    with the rule as written, and a caller that wants to vary one has to say so
    explicitly through `run()`.
    """
    return {module.NAME: module.run(cutoff, symbols=symbols, cache=cache)
            for module in BASELINES}
