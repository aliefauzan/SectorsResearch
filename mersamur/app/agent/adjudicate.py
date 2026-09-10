#!/usr/bin/env python3
"""Task 15 — the first step of the daily tick: warnings judged against reality.

    python3 app/agent/adjudicate.py --dry-run    # prints every verdict, writes nothing
    python3 app/agent/adjudicate.py              # appends the new outcomes
    python3 app/agent/adjudicate.py --live       # +1 credit: refresh /v2/suspensions/

`riset/spec.md` §6 puts this first in the tick because everything after it reads
what it writes: task 16 turns each new outcome into a lesson, task 17 moves a bar
only once twenty outcomes agree. A tick that judged nothing has nothing to learn
from, so this is the step that makes the system self-correcting rather than merely
repetitive.

## Why 11:00 WIB and not 07:00

`/v2/suspensions/` is refreshed **daily at 10:00 WIB** — read off the cron in
`sectors_idx_suspension`, recorded in `research/docs/api/11-data-provenance.md`.
It is this module's only label source. A 07:00 job would adjudicate yesterday's
warnings against a corpus that has not been updated since the morning before, and
would therefore report `false_positive` for suspensions that were announced and
simply not yet published to the API. That is the single worst failure available
here: it is silent, it is one-directional, and it makes the product look wrong
about the very events it got right. The other cadences that bound this loop:
filings every 2 hours, news every 4, `index-daily` weekdays at 18:00 WIB.

## Four outcomes, and the asymmetry between them

`true_positive` · `false_positive` · `still_open` · `expired` (§4). Three of them
close a warning; `still_open` does not, and that distinction carries the rule this
task is most emphatic about — **a warning whose horizon has not run out yet is not
a failure**. It is a prediction still in flight. Counting it as a miss would make
every honest run of the system look worse than the system is, and would do so most
strongly on the day a judge happens to read the file.

`expired` is the fourth case, and it is not a synonym for "no event". It is what
this module reports when the label source *cannot see* the window it was asked
about: the corpus was read to a date earlier than the window's last session, or it
does not reach back as far as the window's first. A `false_positive` is a claim
that nothing happened; `expired` is the admission that we could not have known.
Collapsing the two would let a stale fetch or a single-page read manufacture
misses, which is the same failure as the 07:00 job in a different disguise.

## One suspension read per tick

Step 6 of the task, and the reason is cost: judging N warnings with N calls scales
the tick's credit bill with the watchlist. `suspension_corpus()` is called exactly
once and the same event list is handed to every warning. Offline that is the
recorded archive — 585 rows, already paid for, zero credits. With `--live` it is
one page of `/v2/suspensions/` (1 credit) **merged onto** the archive rather than
replacing it, so the fresh page contributes today's rows and the archive keeps the
depth the page cannot reach.

## Idempotent, because the scheduler retries

A tick that runs twice in a day must leave `outcomes.jsonl` byte-identical. Two
mechanisms, not one:

  * terminal outcomes are filtered by `ledger.open_warnings()` — a warning already
    closed is never picked up again, so it cannot be closed twice;
  * a `still_open` note is written at most once per `(warning_id, resolved_on)`,
    because it is not terminal and would otherwise be re-appended on every retry.

The daily note is kept rather than suppressed: a row saying "checked on the 14th,
horizon runs to the 25th, waiting" is the evidence that the system was watching,
and it is what distinguishes a deliberate wait from a job that never ran.

Zero credits by default: the archive and the daily payloads all come from
`research/harness/recorded/`.
"""
import argparse
import os
import sys
from dataclasses import dataclass, field
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import backtest, config, labels, ledger, universe  # noqa: E402
from app.axes import volume_anomaly  # noqa: E402
from app.cache import Cache  # noqa: E402

# The label source. Named through `labels` so there is still exactly one module
# that knows where suspension history lives.
SUSPENSION_SOURCE = labels.SUSPENSIONS_PATH
SUSPENSION_PARAMS = dict(labels.SUSPENSIONS_PARAMS)

# Price behaviour after the warning. Read through `volume_anomaly.series`, which
# only ever reads settled payloads, so this never opens a socket.
DAILY_SOURCE = volume_anomaly.DAILY_PATH

# The prediction horizon, imported rather than restated: the tick must judge a
# warning over exactly the window `app.backtest` measured lift over, or the daily
# numbers and the backtest numbers are answers to two different questions.
HORIZON_SESSIONS = backtest.HORIZON_SESSIONS


# --- the single suspension read ---------------------------------------------
@dataclass(frozen=True)
class Corpus:
    """The one suspension read of this tick, plus what it can and cannot see.

    `reaches_back_to` and `fresh_through` are the corpus' own temporal bounds, and
    they are what separates `false_positive` from `expired`. `fresh_through` is the
    date the source was *read to*, not the date of its last event: a week with no
    suspensions is not a week the source failed to cover.
    """

    events: tuple = ()
    reaches_back_to: date = None
    fresh_through: date = None
    credits: int = 0
    source: str = SUSPENSION_SOURCE
    live: bool = False

    def labels_for(self, symbol, first, last):
        """Cooling-down events for `symbol` inside `[first, last]`, earliest first.

        `is_label` is `labels`' rule, not a local one: only `cooling_down`, only
        2025 onward. A `going_concern` halt inside the window is a real event and a
        different question, and it is reported as context rather than as a hit.
        """
        want = universe.normalize(symbol)
        return tuple(e for e in self.events
                     if e.symbol == want and e.is_label and first <= e.date <= last)

    def others_for(self, symbol, first, last):
        """Non-label suspensions in the same window — context, never a hit."""
        want = universe.normalize(symbol)
        return tuple(e for e in self.events
                     if e.symbol == want and not e.is_label and first <= e.date <= last)

    def covers(self, first, last):
        """True when the corpus can actually answer "did nothing happen in here?"."""
        if self.fresh_through is None or self.reaches_back_to is None:
            return False
        return self.reaches_back_to <= first and self.fresh_through >= last


def _rows(payload):
    """Suspension rows, whichever envelope the payload arrives in."""
    if isinstance(payload, dict):
        payload = payload.get("results") or payload.get("data") or []
    return [r for r in (payload or []) if isinstance(r, dict)]


def _events_from_rows(rows):
    """Rows to `labels.Event`, using `labels`' own classifier and date parser.

    The nine reason classes are not re-derived here. `labels.classify` carries the
    patterns that the feasibility pass proved are needed — a naive regex loses 17
    cooling-down events — and a second copy of them would drift.
    """
    out = []
    for row in rows:
        when = labels.parse_date(row.get("suspension_date"))
        if when is None:
            continue          # an undated announcement cannot be placed in a window
        reason = row.get("reason") or ""
        out.append(labels.Event(
            symbol=universe.normalize(row.get("symbol") or ""),
            date=when,
            reason_class=labels.classify(reason),
            reason=reason,
            pdf_url=row.get("pdf_url") or "",
        ))
    return out


def recorded_freshness(cache=None):
    """The date the recorded suspension corpus was actually fetched, or None.

    Read from the manifest's `fetched_at` rather than from the last event on
    record, because those are different facts. The corpus was read to 9 September;
    the newest suspension in it happens to be dated the same day, but on a quiet
    week it would not be, and treating the last event as the coverage bound would
    turn every quiet week into `expired`.
    """
    source = cache if cache is not None else Cache()
    entry = source.entry(SUSPENSION_SOURCE, SUSPENSION_PARAMS)
    stamp = (entry or {}).get("fetched_at")
    if not stamp:
        return None
    try:
        return date.fromtimestamp(float(stamp))
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def suspension_corpus(cache=None, client=None, today=None):
    """The one suspension read of this tick. Called once, shared by every warning.

    Offline (`client=None`) this is the recorded archive and costs nothing. With a
    client it is one page of `/v2/suspensions/` — 1 credit — merged onto the
    archive: the page brings today, the archive brings the depth one page cannot.
    """
    today = today or date.today()
    events = list(labels.load_events(cache=cache))
    fresh = recorded_freshness(cache=cache)
    credits, live = 0, False

    if client is not None:
        payload = client.get(SUSPENSION_SOURCE, SUSPENSION_PARAMS)
        fetched = _events_from_rows(_rows(payload))
        seen = {(e.symbol, e.date, e.reason_class) for e in events}
        for event in fetched:
            if (event.symbol, event.date, event.reason_class) not in seen:
                events.append(event)
                seen.add((event.symbol, event.date, event.reason_class))
        credits, live = 1, True
        # The page was read now, so the corpus is fresh to today regardless of what
        # the recording's own timestamp says.
        fresh = today

    events.sort(key=lambda e: (e.date, e.symbol))
    return Corpus(
        events=tuple(events),
        reaches_back_to=events[0].date if events else None,
        fresh_through=fresh,
        credits=credits,
        source=SUSPENSION_SOURCE,
        live=live,
    )


# --- price behaviour after the warning --------------------------------------
def price_evidence(symbol, first, last, cache=None):
    """What the price did inside the horizon, or None when no session is recorded.

    Descriptive only: first and last close, the highest close, the move between the
    two ends, and how many sessions inside the window traded nothing. Every figure
    carries the dates it was measured between, because a number without its window
    is not evidence. `None` means "not observed" and is written as an absent key —
    never as zeros, which would read as a flat market.
    """
    try:
        series = volume_anomaly.series(symbol, cache=cache)
    except volume_anomaly.NoDailyDataError:
        return None

    inside = [s for s in series.sessions if first <= s.date <= last]
    if not inside:
        return None

    closes = [s.close for s in inside if s.close]
    block = {
        "source": DAILY_SOURCE.format(symbol=universe.normalize(symbol)),
        "from": inside[0].date.isoformat(),
        "through": inside[-1].date.isoformat(),
        "sessions": len(inside),
        "sessions_without_trade": sum(1 for s in inside if not s.traded),
        # False means the payload came from a call with no start/end and therefore
        # holds 21 sessions whatever was asked for. Carried so a reader is told.
        "explicit_window": series.explicit_window,
    }
    if closes:
        block["close_first"] = closes[0]
        block["close_last"] = closes[-1]
        block["close_high"] = max(closes)
        if closes[0]:
            block["change_pct"] = round((closes[-1] / closes[0] - 1) * 100, 2)
    return block


# --- one verdict ------------------------------------------------------------
@dataclass
class Verdict:
    """One warning judged, and whether this tick still has to write it down."""

    warning_id: str
    symbol: str
    outcome: str
    resolved_on: str
    days_elapsed: int
    evidence: dict = field(default_factory=dict)
    duplicate: bool = False

    @property
    def terminal(self):
        return self.outcome in ledger.TERMINAL_OUTCOMES

    def row(self):
        """The `outcomes.jsonl` row, in §4's field order."""
        return {
            "warning_id": self.warning_id,
            "resolved_on": self.resolved_on,
            "outcome": self.outcome,
            "days_elapsed": self.days_elapsed,
            "evidence": self.evidence,
        }

    def __str__(self):
        return f"{self.warning_id} {self.symbol} {self.outcome} ({self.days_elapsed} hari)"


def _window(warning):
    """`(when, first, last)` for a warning, or `(when, None, None)`.

    `backtest.horizon` is open at T: an event dated the day of the warning already
    happened when the warning was written, so it is not an outcome of it.
    """
    when = labels.parse_date(warning.get("date"))
    if when is None:
        return None, None, None
    span = backtest.horizon(when, HORIZON_SESSIONS)
    if span is None:
        return when, None, None
    return when, span[0], span[1]


def _elapsed(start, end):
    """Calendar days between two dates, never negative. §4's `days_elapsed`."""
    return max((end - start).days, 0)


def judge(warning, corpus, today=None, cache=None):
    """One warning against one corpus. Pure: reads, decides, writes nothing.

    The order of the branches is the substance of this function:

      1. an observed cooling-down suspension inside the window wins outright;
      2. otherwise, a window that has not finished is `still_open` — never a miss;
      3. a finished window the corpus cannot see is `expired`, not a miss either;
      4. only a finished window, fully covered, with nothing in it, is a
         `false_positive`.
    """
    today = today or date.today()
    symbol = universe.normalize(warning.get("symbol") or "")
    wid = warning.get("id") or ""
    when, first, last = _window(warning)
    stamp = today.isoformat()

    if when is None or first is None:
        return Verdict(
            warning_id=wid, symbol=symbol, outcome="expired", resolved_on=stamp,
            days_elapsed=0,
            evidence={"source": corpus.source, "checked_through": stamp,
                      "note": "tanggal peringatan tidak menghasilkan jendela hasil "
                              "yang bisa dinilai."})

    window = {"first_session": first.isoformat(), "last_session": last.isoformat(),
              "sessions": HORIZON_SESSIONS}
    price = price_evidence(symbol, first, last, cache=cache)

    hits = corpus.labels_for(symbol, first, last)
    if hits:
        hit = hits[0]
        evidence = {
            "source": corpus.source,
            "suspension_date": hit.date.isoformat(),
            "reason_class": hit.reason_class,
            # Required even when the announcement carries no link: "" says
            # "checked, none published", a missing key says nothing.
            "pdf_url": hit.pdf_url or "",
            "reason": hit.reason,
            "window": window,
        }
        if price:
            evidence["price"] = price
        return Verdict(warning_id=wid, symbol=symbol, outcome="true_positive",
                       resolved_on=stamp, days_elapsed=_elapsed(when, hit.date),
                       evidence=evidence)

    remaining = [d for d in backtest.trading_days_forward(when, HORIZON_SESSIONS)
                 if d > today]
    if remaining:
        evidence = {
            "source": corpus.source,
            "checked_through": stamp,
            "window": window,
            "sessions_remaining": len(remaining),
            "note": "jendela hasil belum habis; peringatan tetap terbuka.",
        }
        if price:
            evidence["price"] = price
        return Verdict(warning_id=wid, symbol=symbol, outcome="still_open",
                       resolved_on=stamp, days_elapsed=_elapsed(when, today),
                       evidence=evidence)

    if not corpus.covers(first, last):
        reach = corpus.reaches_back_to.isoformat() if corpus.reaches_back_to else None
        through = corpus.fresh_through.isoformat() if corpus.fresh_through else None
        evidence = {
            "source": corpus.source,
            "checked_through": through or stamp,
            "window": window,
            "corpus_reaches_back_to": reach,
            "corpus_fresh_through": through,
            "note": "sumber label tidak menjangkau seluruh jendela; tidak dinilai "
                    "sebagai gagal karena peristiwanya tidak akan terlihat.",
        }
        if price:
            evidence["price"] = price
        return Verdict(warning_id=wid, symbol=symbol, outcome="expired",
                       resolved_on=stamp, days_elapsed=_elapsed(when, last),
                       evidence=evidence)

    evidence = {
        "source": corpus.source,
        "checked_through": corpus.fresh_through.isoformat(),
        "window": window,
        "note": "jendela hasil habis tanpa suspensi cooling-down.",
    }
    others = corpus.others_for(symbol, first, last)
    if others:
        evidence["other_suspensions"] = [
            {"suspension_date": e.date.isoformat(), "reason_class": e.reason_class,
             "pdf_url": e.pdf_url or ""} for e in others]
    if price:
        evidence["price"] = price
    return Verdict(warning_id=wid, symbol=symbol, outcome="false_positive",
                   resolved_on=stamp, days_elapsed=_elapsed(when, last),
                   evidence=evidence)


# --- the tick step ----------------------------------------------------------
def _pending(warnings, outcomes):
    """Open warnings, one row per id, latest line wins.

    Two lines can share an id — it is `date`+`symbol` — and writing an outcome for
    each would break byte-identical re-runs within a single tick.
    """
    unique = {}
    for row in ledger.open_warnings(warnings=warnings, outcomes=outcomes):
        unique[row["id"]] = row
    return list(unique.values())


def plan(today=None, warnings_path=None, outcomes_path=None, cache=None, client=None):
    """Every verdict this tick would write. `(corpus, verdicts)`. Writes nothing.

    `duplicate` is set on any verdict already on record, which is what makes a
    retry a no-op instead of a second opinion.
    """
    today = today or date.today()
    warnings = ledger.read_warnings(warnings_path)
    outcomes = ledger.read_outcomes(outcomes_path)
    corpus = suspension_corpus(cache=cache, client=client, today=today)

    closed = {r["warning_id"] for r in outcomes if r["outcome"] in ledger.TERMINAL_OUTCOMES}
    noted = {(r["warning_id"], r["resolved_on"], r["outcome"]) for r in outcomes}

    verdicts = []
    for warning in _pending(warnings, outcomes):
        verdict = judge(warning, corpus, today=today, cache=cache)
        verdict.duplicate = (
            verdict.warning_id in closed
            or (verdict.warning_id, verdict.resolved_on, verdict.outcome) in noted)
        verdicts.append(verdict)
    return corpus, verdicts


def run(today=None, warnings_path=None, outcomes_path=None, cache=None, client=None,
        dry_run=False):
    """Adjudicate, then append what is not already there. `(corpus, verdicts, written)`."""
    corpus, verdicts = plan(today=today, warnings_path=warnings_path,
                            outcomes_path=outcomes_path, cache=cache, client=client)
    written = []
    if not dry_run:
        for verdict in verdicts:
            if verdict.duplicate:
                continue
            ledger.append_outcome(verdict.row(), path=outcomes_path)
            written.append(verdict)
    return corpus, verdicts, written


# --- CLI --------------------------------------------------------------------
def _corpus_line(corpus):
    reach = corpus.reaches_back_to.isoformat() if corpus.reaches_back_to else "—"
    fresh = corpus.fresh_through.isoformat() if corpus.fresh_through else "tidak diketahui"
    origin = "satu halaman live + arsip terekam" if corpus.live else "arsip terekam"
    return (f"sumber label: {corpus.source} ({origin}) — {len(corpus.events)} peristiwa, "
            f"{reach} s.d. {fresh}, {corpus.credits} kredit")


def render(corpus, verdicts, written, dry_run):
    """A descriptive account of the step. No verdict on any stock, only on predictions."""
    lines = [_corpus_line(corpus)]
    counts = {}
    for verdict in verdicts:
        counts[verdict.outcome] = counts.get(verdict.outcome, 0) + 1

    if not verdicts:
        lines.append("tidak ada peringatan terbuka — tidak ada yang dinilai.")
        return "\n".join(lines)

    lines.append(f"peringatan terbuka: {len(verdicts)}"
                 + (" — " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
                    if counts else ""))
    for verdict in verdicts:
        mark = "sudah tercatat" if verdict.duplicate else (
            "akan ditulis" if dry_run else "ditulis")
        lines.append(f"  {verdict} · {mark}")
    if not dry_run:
        lines.append(f"{len(written)} baris ditambahkan ke outcomes.jsonl")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Langkah NILAI: peringatan terbuka diadu dengan kenyataan.")
    ap.add_argument("--dry-run", action="store_true",
                    help="nilai dan cetak, jangan tulis apa pun")
    ap.add_argument("--as-of", metavar="YYYY-MM-DD",
                    help="tanggal penilaian (default: hari ini)")
    ap.add_argument("--live", action="store_true",
                    help="segarkan /v2/suspensions/ — 1 kredit; tanpa ini semuanya "
                         "dibaca dari rekaman dan tidak ada kredit terpakai")
    args = ap.parse_args(argv)

    today = labels.parse_date(args.as_of) if args.as_of else date.today()
    if today is None:
        print(f"--as-of harus bertanggal YYYY-MM-DD; dapat {args.as_of!r}")
        return 2

    client = None
    if args.live:
        from app.sectors_client import SectorsClient
        client = SectorsClient(allow_network=True)

    corpus, verdicts, written = run(today=today, client=client, dry_run=args.dry_run)

    print(f"Penilaian peringatan — {today.isoformat()}"
          + (" [dry-run: tidak ada yang ditulis]" if args.dry_run else ""))
    print(render(corpus, verdicts, written, args.dry_run))
    if not config.is_trading_day(today):
        print("catatan: hari ini bukan hari bursa IDX; penilaian tetap sah karena "
              "jendelanya diukur dalam sesi, bukan hari kalender.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
