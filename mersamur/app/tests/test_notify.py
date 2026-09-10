"""Task 19 — the two delivery rules, and the token that must never leak.

The rules are in `tasks/19-pengiriman-telegram.md` §Langkah and §Jangan, and both
are the kind that only break in production:

  * **only transitions are sent.** A daily re-send of the same symbols is what makes
    a person mute the channel, and it turns the trigger back into a scheduled query.
  * **a failed send never fails the tick.** The run log's value is that it has no
    unexplained gaps; a Telegram outage aborting the cycle would put one in it on
    exactly the days something was worth saying.

No socket is opened here: `send()` takes its poster as an argument, so every path
below — success, rejection, HTTP error, timeout — is exercised against a function,
not against Telegram. Zero credits, and no Sectors call either.
"""
import io
import json
import os
import urllib.error

import pytest

from app import config, profile as profile_mod
from app.cache import Cache
from app.render import notify

TOKEN = "1234567:AAfake-token-value"


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv(notify.TOKEN_VAR, TOKEN)
    monkeypatch.setenv(notify.CHAT_VAR, "-1001234567890")


@pytest.fixture
def state(tmp_path):
    return str(tmp_path / "notified.json")


@pytest.fixture(scope="module")
def lit():
    """Two real profiles from the recordings, whatever their axes read today.

    Built from the watchlist rather than from a fabricated object so the message
    that gets asserted on is the message the product would actually send.
    """
    cache = Cache()
    out = {}
    for symbol in config.WATCHLIST:
        profile = profile_mod.build(symbol, cache=cache)
        if any(r.measured for r in profile.counted):
            out[profile.symbol] = profile
        if len(out) == 2:
            break
    assert len(out) == 2, "rekaman untuk dua simbol watchlist tidak terbaca"
    return out


def ok_poster(calls):
    def poster(url, payload):
        calls.append((url, payload))
        return 200, json.dumps({"ok": True, "result": {"message_id": len(calls)}})
    return poster


# --- rule one: only transitions ---------------------------------------------
def test_a_symbol_already_in_the_state_is_not_sent_again(env, state, lit):
    """The same lit set on two consecutive days sends once, not twice."""
    calls = []
    first = notify.deliver(lit, dry_run=False, when="2026-09-10",
                           poster=ok_poster(calls), state_path=state)
    assert sorted(first.entering) == sorted(lit)
    assert len(calls) == len(lit)

    second = notify.deliver(lit, dry_run=False, when="2026-09-11",
                            poster=ok_poster(calls), state_path=state)
    assert second.entering == []
    assert len(calls) == len(lit), "peringatan yang sama dikirim ulang keesokan harinya"


def test_leaving_the_state_and_returning_is_a_new_transition(env, state, lit):
    """Membership, not a permanent mute list: a re-entry is an event again."""
    calls = []
    symbol = sorted(lit)[0]
    one = {symbol: lit[symbol]}
    notify.deliver(one, dry_run=False, when="2026-09-10",
                   poster=ok_poster(calls), state_path=state)
    notify.deliver({}, dry_run=False, when="2026-09-11",
                   poster=ok_poster(calls), state_path=state)
    back = notify.deliver(one, dry_run=False, when="2026-09-14",
                          poster=ok_poster(calls), state_path=state)
    assert back.entering == [symbol]
    assert len(calls) == 2


def test_a_dry_run_sends_nothing_and_writes_nothing(env, state, lit):
    """`--dry-run` shows the messages and leaves the membership file absent."""
    calls = []
    outcome = notify.deliver(lit, dry_run=True, when="2026-09-10",
                             poster=ok_poster(calls), state_path=state)
    assert outcome.messages and not calls
    assert not os.path.exists(state)


# --- rule two: a failure is recorded, never raised ---------------------------
@pytest.mark.parametrize("poster", [
    lambda url, payload: (_ for _ in ()).throw(TimeoutError("timed out")),
    lambda url, payload: (500, "upstream sedang bermasalah"),
    lambda url, payload: (200, json.dumps({"ok": False, "description": "chat not found"})),
    lambda url, payload: (200, "bukan json"),
])
def test_delivery_failure_is_returned_not_raised(env, state, lit, poster):
    outcome = notify.deliver(lit, dry_run=False, when="2026-09-10",
                             poster=poster, state_path=state)
    assert outcome.failed and not outcome.sent
    assert "gagal kirim" in outcome.note()


def test_a_failed_send_is_retried_tomorrow(env, state, lit):
    """The state records what left the process, so a failure is not swallowed."""
    def broken(url, payload):
        raise urllib.error.URLError("no route to host")

    notify.deliver(lit, dry_run=False, when="2026-09-10", poster=broken,
                   state_path=state)
    calls = []
    again = notify.deliver(lit, dry_run=False, when="2026-09-11",
                           poster=ok_poster(calls), state_path=state)
    assert sorted(again.entering) == sorted(lit)
    assert len(calls) == len(lit)


def test_an_unconfigured_bot_leaves_the_cycle_intact(monkeypatch, state, lit):
    monkeypatch.delenv(notify.TOKEN_VAR, raising=False)
    monkeypatch.delenv(notify.CHAT_VAR, raising=False)
    monkeypatch.setattr(notify, "_env", lambda name: "")
    outcome = notify.deliver(lit, dry_run=False, when="2026-09-10",
                             state_path=state)
    assert "belum diset" in outcome.note()


# --- the token ---------------------------------------------------------------
def test_the_token_never_reaches_the_state_file_or_the_note(env, state, lit):
    """Telegram echoes the request URL inside some error bodies. It must not land
    in `runs.jsonl`, which the scheduled workflow commits."""
    def leaky(url, payload):
        # The shape Telegram actually returns: the request URL, token included,
        # quoted back inside the error body.
        body = io.BytesIO(json.dumps(
            {"ok": False, "description": f"Not Found: {url}"}).encode("utf-8"))
        raise urllib.error.HTTPError(url, 404, f"Not Found: {url}", {}, body)

    outcome = notify.deliver(lit, dry_run=False, when="2026-09-10", poster=leaky,
                             state_path=state)
    assert TOKEN not in outcome.note()
    assert "<token>" in outcome.note()

    calls = []
    notify.deliver(lit, dry_run=False, when="2026-09-11",
                   poster=ok_poster(calls), state_path=state)
    assert TOKEN not in open(state, encoding="utf-8").read()


# --- the message -------------------------------------------------------------
def test_every_message_carries_the_threshold_version(env, state, lit):
    """A channel of unversioned messages cannot show bars that moved."""
    outcome = notify.deliver(lit, dry_run=True, when="2026-09-10", state_path=state)
    for message in outcome.messages:
        version = lit[message.symbol].thresholds_version
        assert f"ambang v{version}" in message.text
        assert "2026-09-10" in message.text


def test_the_message_carries_the_disclaimer_and_no_verdict(env, state, lit):
    """§D11 applies to the header this module writes, not only to the paragraph."""
    from app.render import paragraph as paragraph_mod

    outcome = notify.deliver(lit, dry_run=True, when="2026-09-10", state_path=state)
    for message in outcome.messages:
        assert paragraph_mod.DISCLAIMER in message.text
        assert paragraph_mod.banned_words_in(message.text) == []
        assert len(message.text) <= notify.MESSAGE_LIMIT
