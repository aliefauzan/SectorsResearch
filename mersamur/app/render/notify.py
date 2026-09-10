"""Delivery: the paragraph leaving the process, and the memory of what was sent.

`riset/spec.md` §4 keeps the run history in files a judge can read. This module is
the other half of that evidence — the half that accumulates in a place nobody can
retro-fit. Track 02's bar is explicit that a manual run is not enough:

    "show the schedule or trigger configuration together with logs, timestamps, or
    screenshots of unattended runs. A manual run without that evidence is not
    sufficient."

Several days of timestamped messages in a real channel is that evidence, and it is
the one artefact that cannot be produced on the last day — which is why the sender
ships before the interface does.

## Only transitions are sent, and that is a claim about the trigger

The rule this module exists to enforce: a message goes out when a symbol **enters**
the lit-axes state, never while it sits there. Two reasons, and the second matters
more than the first.

  * A daily re-send of the same five symbols is what makes a person mute the
    channel, and a muted channel is worth nothing on judging day.
  * Track 02 asks for a *trigger*. "Every weekday, here is the current screen" is a
    scheduled query whose output happens to be a list; "LIFE entered the state today
    and did not hold it yesterday" is an event. The second is defensible as an
    automation, the first is a cron job with a mailing list.

`state/notified.json` is what makes the distinction computable: it holds the set of
symbols currently in the state and the date each entered. A symbol that leaves the
set and comes back later is a new entrance, and is sent again — the state is a
membership record, not a permanent mute list.

## Failure is recorded, never raised

`send()` catches everything and returns a result. A tick whose delivery failed still
screened the market and still owes `state/runs.jsonl` its line; letting a Telegram
outage abort the cycle would put a gap in the very history this module exists to
grow, and would do it on exactly the days something was worth saying.

The state file is written **after** delivery and only for what actually left the
process, so a failed send is retried tomorrow rather than silently swallowed.

## The token

Read from the environment through `sectors_env`, the same path the API key takes,
and never written anywhere: not into `state/`, not into a run note, not into an
error string. `_scrub()` exists because Telegram echoes the request URL — token and
all — inside some of its error bodies, and that body would otherwise be copied into
`runs.jsonl` and committed by the scheduled workflow.

Zero credits: Telegram is not Sectors. Nothing here touches the grant.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from app import config
from app.render import paragraph as paragraph_mod

sys.path.insert(0, config.HARNESS_SRC_DIR)
import sectors_env  # noqa: E402  — one shared reader for .env, never os.environ

# --- configuration ----------------------------------------------------------
TOKEN_VAR = "TELEGRAM_BOT_TOKEN"
CHAT_VAR = "TELEGRAM_CHAT_ID"
API_ROOT = "https://api.telegram.org"
TIMEOUT_SECONDS = 15

# Telegram rejects anything longer outright. A paragraph is three sentences, so
# this only ever bites if a future edit starts batching symbols into one message.
MESSAGE_LIMIT = 4096

# Where the lit-axes membership is remembered between runs. Deliberately not one of
# the four files `app/ledger.py` owns: those are the evidential record of what the
# system said and what happened, and a delivery bookkeeping file has no business
# sitting among them.
NOTIFIED_PATH = os.path.join(config.STATE_DIR, "notified.json")


def _env(name):
    """One environment value, `.env` loaded on first use. Never logged."""
    sectors_env.load_dotenv()
    return os.environ.get(name) or ""


def configured():
    """True when both the token and the destination chat are set."""
    return bool(_env(TOKEN_VAR) and _env(CHAT_VAR))


def _scrub(text):
    """Remove the bot token from anything about to be printed or written."""
    token = _env(TOKEN_VAR)
    out = str(text)
    if token:
        out = out.replace(token, "<token>")
    return out


# --- the membership state ---------------------------------------------------
def load_state(path=None):
    """`{symbol: date entered}`. A missing or corrupt file reads as empty.

    Corrupt is treated as empty rather than fatal on purpose: the worst case is one
    duplicate message, and the alternative — a tick that dies because a bookkeeping
    file was hand-edited — costs a day of history to save a day of noise.
    """
    path = path or NOTIFIED_PATH
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return {}
    entered = doc.get("lit") if isinstance(doc, dict) else None
    if not isinstance(entered, dict):
        return {}
    return {str(k): str(v) for k, v in entered.items()}


def save_state(entered, path=None, when=None):
    """Write the membership set. Holds symbols and dates only — never the token."""
    path = path or NOTIFIED_PATH
    day = when or date.today()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc = {
        "updated_on": day.isoformat() if hasattr(day, "isoformat") else str(day),
        "lit": dict(sorted(entered.items())),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return path


def transitions(lit_now, previous):
    """`(entering, leaving, next_state)` for today's lit set against yesterday's.

    `entering` is what gets a message. `leaving` is returned so the caller can say
    in the run note that the set shrank — a symbol dropping out is not an event
    worth a notification, but a run log that never mentions it reads as if nothing
    ever cools down.
    """
    lit_now = [s for s in lit_now if s]
    entering = [s for s in lit_now if s not in previous]
    leaving = [s for s in previous if s not in lit_now]
    return entering, leaving, dict(previous)


# --- the message ------------------------------------------------------------
@dataclass(frozen=True)
class Message:
    """One symbol's message: what will be sent, and what it is about."""

    symbol: str
    text: str
    thresholds_version: int = None
    axes_fired: int = 0
    axes_total: int = 0


def format_message(profile, paragraph, when=None):
    """The paragraph with a header naming the day, the count, and the bar version.

    The version is in every message because the bars move (`app/agent/evolve.py`),
    and a channel of undated, unversioned messages cannot show that. Read back over
    several weeks, `ambang v3` -> `ambang v4` is the visible trace of a system that
    changed its own parameters — which is the claim, and this is its receipt.
    """
    day = when or date.today()
    day = day.isoformat() if hasattr(day, "isoformat") else str(day)
    version = profile.thresholds_version
    header = (f"MERSAMUR · {profile.symbol} memasuki keadaan sumbu menyala\n"
              f"{day} · {profile.axes_fired} dari {profile.axes_total} sumbu "
              f"tercatat menyala · ambang v{version}")
    text = f"{header}\n\n{paragraph.text}"

    # The §D11 vocabulary rule is checked again here rather than trusted from
    # `paragraph.verify()`: the header is written in this module and never passed
    # through that check, and a verdict word added to it later would otherwise
    # reach a public channel unexamined.
    found = paragraph_mod.banned_words_in(header)
    if found:
        raise paragraph_mod.BannedVocabularyError(
            f"{profile.symbol}: kosakata vonis di kepala pesan — {', '.join(found)}")

    if len(text) > MESSAGE_LIMIT:
        text = text[:MESSAGE_LIMIT - 1] + "…"
    return Message(symbol=profile.symbol, text=text, thresholds_version=version,
                   axes_fired=profile.axes_fired, axes_total=profile.axes_total)


# --- delivery ---------------------------------------------------------------
@dataclass(frozen=True)
class Delivery:
    """What happened to one message. `ok` false is a recorded fact, not an error."""

    symbol: str
    ok: bool
    detail: str = ""
    sent_at: str = ""


def _post(url, payload):
    """One JSON POST. Separated so a test can replace it without a socket."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "User-Agent": "mersamur-tick/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.status, response.read().decode("utf-8", "replace")


def send(text, chat_id=None, poster=None):
    """Send one message. Returns `(ok, detail)` and never raises.

    Every failure path returns rather than propagates — see the module docstring:
    the tick must survive a Telegram outage, because the days the channel is down
    are not the days the run history is allowed to have a hole in it.
    """
    token = _env(TOKEN_VAR)
    chat = chat_id or _env(CHAT_VAR)
    if not (token and chat):
        return False, f"{TOKEN_VAR}/{CHAT_VAR} belum diset"

    payload = {"chat_id": chat, "text": text,
               "disable_web_page_preview": True}
    try:
        status, body = (poster or _post)(f"{API_ROOT}/bot{token}/sendMessage",
                                         payload)
    except urllib.error.HTTPError as exc:                 # 4xx/5xx from Telegram
        try:
            detail = exc.read().decode("utf-8", "replace") if exc.fp else ""
        except Exception:
            detail = ""
        return False, _scrub(f"HTTP {exc.code} {exc.reason}: {detail}")[:300]
    except Exception as exc:                              # DNS, timeout, TLS, …
        return False, _scrub(f"{type(exc).__name__}: {exc}")[:300]

    if status != 200:
        return False, _scrub(f"HTTP {status}: {body}")[:300]
    try:
        if not json.loads(body).get("ok"):
            return False, _scrub(f"telegram menolak: {body}")[:300]
    except ValueError:
        return False, "respons telegram bukan JSON"
    return True, "terkirim"


@dataclass
class Outcome:
    """The delivery half of one tick, in the shape the run note is written from."""

    entering: list = field(default_factory=list)
    leaving: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    deliveries: list = field(default_factory=list)
    dry_run: bool = False
    configured: bool = True

    @property
    def sent(self):
        return [d for d in self.deliveries if d.ok]

    @property
    def failed(self):
        return [d for d in self.deliveries if not d.ok]

    def note(self):
        """One clause for `runs.jsonl`, in Indonesian, carrying no token."""
        if not self.entering:
            return "tidak ada transisi baru; tidak ada yang dikirim"
        names = ", ".join(m.symbol for m in self.messages) or \
            ", ".join(self.entering)
        if self.dry_run:
            return f"{len(self.entering)} transisi siap dikirim: {names} (dry-run)"
        if not self.configured:
            return (f"{len(self.entering)} transisi tidak dikirim: "
                    f"{TOKEN_VAR}/{CHAT_VAR} belum diset ({names})")
        parts = []
        if self.sent:
            parts.append(f"{len(self.sent)} transisi terkirim ke Telegram: "
                         + ", ".join(d.symbol for d in self.sent))
        for failure in self.failed:
            parts.append(f"{failure.symbol} gagal kirim: {failure.detail}")
        return "; ".join(parts)


def deliver(profiles, previous=None, dry_run=False, when=None, poster=None,
            state_path=None, cache=None):
    """Send the transitions among `profiles` and return what happened.

    `profiles` is every symbol whose axes lit **today**, keyed by symbol. The
    membership file decides which of them are new. Rendering is per-symbol and
    guarded: a paragraph that fails its own citation check (task 18 fails closed,
    on purpose) costs that one message, not the tick.
    """
    day = when or date.today()
    previous = load_state(state_path) if previous is None else dict(previous)
    entering, leaving, next_state = transitions(list(profiles), previous)
    outcome = Outcome(entering=entering, leaving=leaving, dry_run=dry_run,
                      configured=configured())

    for symbol in entering:
        profile = profiles[symbol]
        try:
            rendered = paragraph_mod.render(profile, cache=cache)
            outcome.messages.append(format_message(profile, rendered, when=day))
        except Exception as exc:                # a refused render is one message
            outcome.deliveries.append(Delivery(
                symbol=symbol, ok=False,
                detail=_scrub(f"paragraf ditolak — {type(exc).__name__}: {exc}")[:300]))

    if dry_run:
        return outcome

    for message in outcome.messages:
        ok, detail = send(message.text, poster=poster)
        outcome.deliveries.append(Delivery(
            symbol=message.symbol, ok=ok, detail=detail,
            sent_at=datetime.now(timezone.utc).isoformat(timespec="seconds")
                    .replace("+00:00", "Z") if ok else ""))

    # Recorded only for what left the process. A symbol whose send failed stays out
    # of the set, so tomorrow's tick treats it as a fresh entrance and tries again.
    delivered = {d.symbol for d in outcome.sent}
    day_text = day.isoformat() if hasattr(day, "isoformat") else str(day)
    for symbol in delivered:
        next_state[symbol] = day_text
    for symbol in leaving:
        next_state.pop(symbol, None)
    save_state(next_state, path=state_path, when=day)
    return outcome
