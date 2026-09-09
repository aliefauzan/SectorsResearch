"""Static configuration for the daily cycle: schedule, watchlist, state paths.

Kept free of logic so a reader can answer "when does it run, over what, writing
where" without reading `tick.py`.
"""
import os
from datetime import date

# --- paths ------------------------------------------------------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(APP_DIR)                    # mersamur/
REPO_ROOT = os.path.dirname(PKG_ROOT)                  # repository root
STATE_DIR = os.path.join(PKG_ROOT, "state")
RUNS_PATH = os.path.join(STATE_DIR, "runs.jsonl")
TOOLS_DIR = os.path.join(PKG_ROOT, "tools")
RECORDED_DIR = os.path.join(REPO_ROOT, "research", "harness", "recorded")
HARNESS_SRC_DIR = os.path.join(REPO_ROOT, "research", "harness", "src")
# Every billed call the product makes appends one line here. Separate from the
# harness ledger on purpose: that one records what capture.py bought, this one
# records what the product spent, and mixing them would make neither reconcilable.
LEDGER_PATH = os.path.join(STATE_DIR, "credits.jsonl")

# --- schedule ---------------------------------------------------------------
# 04:00 UTC = 11:00 WIB, weekdays. Deliberately not 07:00 WIB: /v2/suspensions/ —
# the primary label source — is only refreshed at 10:00 WIB, so an earlier job
# would adjudicate yesterday's warnings against stale data. See riset/spec.md §6.
CRON_UTC = "0 4 * * 1-5"
TICK_HOUR_WIB = 11

# --- watchlist --------------------------------------------------------------
# Only symbols that already appeared in a previous API response. A guessed
# identifier costs a credit on the 404. Every one of these has cached
# broker-summary and daily payloads under research/harness/recorded/.
WATCHLIST = ["LIFE", "ASLI", "NICK", "TRUK", "PPGL",
             "SAFE", "PACK", "CSMI", "TMPO", "AGAR"]

# How many of the four axes must fire before the cycle counts a warning.
# A starting value, not a tuned one — the evolve step owns this later.
WARNING_AXES_THRESHOLD = 3

# --- IDX trading calendar ---------------------------------------------------
# Copied from research/harness/src/synth_extended.py (IDX_HOLIDAYS_2026), which
# sources it from sectors.app/indonesia/calendars/trading-calendar. Copied rather
# than imported: the harness is a standard-library research tool that the product
# must not take a runtime dependency on.
IDX_HOLIDAYS_2026 = {
    (1, 1), (1, 16), (2, 16), (2, 17), (3, 18), (3, 19), (3, 20), (3, 23), (3, 24),
    (4, 3), (5, 1), (5, 14), (5, 15), (5, 27), (5, 28), (6, 1), (6, 16),
    (8, 17), (8, 25), (12, 24), (12, 25), (12, 31),
}


def is_trading_day(day=None):
    """IDX trades Monday-Friday excluding gazetted market holidays.

    The holiday set is 2026's and is applied to 2026 only: Indonesian public
    holidays are largely lunar and move weeks between years, so matching on
    (month, day) in another year would exclude the wrong dates. Outside 2026 this
    models weekdays only — incomplete rather than confidently wrong.
    """
    day = day or date.today()
    if day.weekday() >= 5:
        return False
    if day.year == 2026:
        return (day.month, day.day) not in IDX_HOLIDAYS_2026
    return True
