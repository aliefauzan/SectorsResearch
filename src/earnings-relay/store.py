#!/usr/bin/env python3
"""
Workflow state, in a database that can refuse things a convention cannot.

SQLite, from the standard library, at `state/relay.db`. It is here rather than in a JSONL
file for two reasons that are both PRD requirements: §15 makes a database unique
constraint the **last** line of deduplication, and §12 requires a state transition to be
atomic together with the audit row it produces. A file cannot do either.

    from store import Store, event_hash

    store = Store()                       # state/relay.db, created on first use
    event = store.create_event(workspace, "ADRO", "q1-2026", "2026-03-31", "2026-09-06")
    store.transition(event["event_id"], "discovered", "fetching", "service:poll", None, run)

What this file guarantees:

  * `UNIQUE(event_hash)` on `report_event` — a second poll of the same report raises
    `Duplicate` carrying the canonical `event_id` (ER-FR-03, AT-02). Two `poll`
    processes racing on the same database produce one event and one `duplicate`, not a
    crash and not two drafts.
  * `UNIQUE(idempotency_key)` on `delivery` — replaying a failed run delivers once
    (ER-FR-12, AT-09).
  * `transition()` refuses a move whose `from_state` is not the current state, and
    writes the new state and its `audit_event` row inside one transaction. A concurrent
    writer cannot skip a step, and a half-written transition cannot exist.
  * `audit_event` is append-only. There is no UPDATE or DELETE against it anywhere in
    this file, and `check_audit_append_only` greps this module's own source to keep it
    that way.

`runs.jsonl` is kept alongside as the human-readable ledger, matching the other two
products in `src/`.

    python3 store.py    # duplicate suppression, out-of-order refusal, append-only audit
"""
import hashlib
import json
import os
import sqlite3
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(HERE, "state")
DB_PATH = os.path.join(STATE_DIR, "relay.db")
RUNS = os.path.join(HERE, "runs.jsonl")

#: PRD §12, exactly. `no_op` and `duplicate` are terminal operational states, not
#: failures: nothing was wrong, there was simply nothing to do.
STATES = ("discovered", "fetching", "validated", "fact_locked", "drafted",
          "needs_review", "approved", "rejected", "revised",
          "no_op", "duplicate", "failed")

TERMINAL = ("no_op", "duplicate")

#: Every legal move. Anything not in here is refused with the current state named, which
#: is what stops a concurrent writer from jumping `discovered` straight to `approved`.
ALLOWED = {
    "discovered": ("fetching", "no_op", "duplicate", "failed"),
    # A fetch that came back with an unusable payload is a human problem, not a retry.
    "fetching": ("validated", "needs_review", "failed"),
    "validated": ("fact_locked", "failed"),
    "fact_locked": ("drafted", "failed"),
    "drafted": ("needs_review", "failed"),
    # needs_review -> needs_review is a revalidation in place (ER-FR-11).
    "needs_review": ("approved", "rejected", "needs_review", "failed"),
    "rejected": ("revised",),
    "revised": ("needs_review",),
    # A restatement can pull an approved draft back for review (ER-FR-07, AT-05).
    "approved": ("needs_review",),
    # A failed run is replayable with the same idempotency key (PRD §12).
    "failed": ("fetching", "no_op"),
    "no_op": (),
    "duplicate": (),
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS workspace (
    workspace_id      TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    timezone          TEXT NOT NULL DEFAULT 'Asia/Jakarta',
    schedule          TEXT NOT NULL DEFAULT 'harian 08:00',
    reviewer_id       TEXT,
    prohibited_claims TEXT NOT NULL DEFAULT '[]',
    comparator_mode   TEXT NOT NULL DEFAULT 'yoy',
    status            TEXT NOT NULL DEFAULT 'active',
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watchlist_item (
    workspace_id        TEXT NOT NULL REFERENCES workspace(workspace_id),
    symbol              TEXT NOT NULL,
    active              INTEGER NOT NULL DEFAULT 1,
    content_template_id TEXT NOT NULL DEFAULT 'er-carousel-1',
    PRIMARY KEY (workspace_id, symbol)
);

CREATE TABLE IF NOT EXISTS report_event (
    event_id      TEXT PRIMARY KEY,
    workspace_id  TEXT NOT NULL REFERENCES workspace(workspace_id),
    symbol        TEXT NOT NULL,
    period_key    TEXT NOT NULL,
    report_date   TEXT NOT NULL,
    source_as_of  TEXT NOT NULL,
    event_hash    TEXT NOT NULL UNIQUE,
    state         TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run (
    run_id         TEXT PRIMARY KEY,
    workspace_id   TEXT NOT NULL REFERENCES workspace(workspace_id),
    trigger_type   TEXT NOT NULL,
    started_at     TEXT NOT NULL,
    completed_at   TEXT,
    cursor         TEXT,
    next_cursor    TEXT,
    status         TEXT NOT NULL,
    attempt        INTEGER NOT NULL DEFAULT 1,
    error_code     TEXT,
    detected_count INTEGER NOT NULL DEFAULT 0,
    new_count      INTEGER NOT NULL DEFAULT 0,
    duplicate_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fact_set (
    fact_set_id  TEXT PRIMARY KEY,
    event_id     TEXT NOT NULL REFERENCES report_event(event_id),
    version      INTEGER NOT NULL,
    source_hash  TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    locked_at    TEXT,
    payload      TEXT NOT NULL,
    UNIQUE (event_id, version)
);

CREATE TABLE IF NOT EXISTS metric (
    metric_id      TEXT PRIMARY KEY,
    fact_set_id    TEXT NOT NULL REFERENCES fact_set(fact_set_id),
    type           TEXT NOT NULL,
    value          REAL,
    display        TEXT,
    comparator     TEXT NOT NULL,
    quality_status TEXT NOT NULL,
    reason_code    TEXT,
    payload        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS draft (
    draft_id         TEXT PRIMARY KEY,
    event_id         TEXT NOT NULL REFERENCES report_event(event_id),
    fact_set_id      TEXT NOT NULL REFERENCES fact_set(fact_set_id),
    template_version TEXT NOT NULL,
    version          INTEGER NOT NULL DEFAULT 1,
    status           TEXT NOT NULL,
    content          TEXT NOT NULL,
    created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claim (
    claim_id          TEXT PRIMARY KEY,
    draft_id          TEXT NOT NULL REFERENCES draft(draft_id),
    slide             INTEGER NOT NULL,
    text              TEXT NOT NULL,
    kind              TEXT NOT NULL,
    fact_ids          TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    reason_codes      TEXT NOT NULL,
    checked_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_decision (
    decision_id TEXT PRIMARY KEY,
    draft_id    TEXT NOT NULL REFERENCES draft(draft_id),
    reviewer_id TEXT NOT NULL,
    decision    TEXT NOT NULL,
    comment     TEXT,
    decided_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS delivery (
    delivery_id     TEXT PRIMARY KEY,
    draft_id        TEXT NOT NULL REFERENCES draft(draft_id),
    destination     TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    status          TEXT NOT NULL,
    delivered_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_event (
    audit_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id       TEXT,
    from_state     TEXT,
    to_state       TEXT,
    actor          TEXT NOT NULL,
    reason_code    TEXT,
    correlation_id TEXT,
    detail         TEXT,
    at             TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_event_workspace ON report_event(workspace_id, symbol);
CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_event(event_id);
CREATE INDEX IF NOT EXISTS idx_claim_draft ON claim(draft_id);
"""


class Duplicate(Exception):
    """This report has already been seen. Carries the canonical `event_id` (PRD §12)."""

    def __init__(self, event_id, event_hash):
        super().__init__(f"event_hash {event_hash[:12]} already exists as {event_id}")
        self.event_id = event_id
        self.event_hash = event_hash


class IllegalTransition(Exception):
    """A state move that PRD §12 does not allow, or that raced another writer.

    The message names the state the row is actually in, because the usual cause is not a
    bug in the caller but a second process that got there first.
    """


class AlreadyDelivered(Exception):
    """This idempotency key has already been delivered. Replay is a no-op, not a resend."""

    def __init__(self, delivery_id, key):
        super().__init__(f"idempotency key {key} already delivered as {delivery_id}")
        self.delivery_id = delivery_id


def _now(now=None):
    return now if now is not None else time.strftime("%Y-%m-%dT%H:%M:%S")


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def event_hash(workspace_id, symbol, period_key, report_date, source_version):
    """ER-FR-03. The five inputs PRD §13 names, in a fixed order, hashed.

    `source_version` is the payload's `source_as_of`: the same period re-published from a
    new capture is a *restatement candidate* and therefore a different event hash, which
    is what makes AT-05 distinguishable from AT-02.
    """
    return _sha(f"{workspace_id}|{symbol}|{period_key}|{report_date}|{source_version}")


class Store:
    """One connection, one schema, and every write that changes state going through it."""

    def __init__(self, path=DB_PATH):
        self.path = path
        if path != ":memory:":
            os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        # SQLite ignores foreign keys unless asked, per connection, every time.
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    # ------------------------------------------------------------------ configuration

    def upsert_workspace(self, workspace_id, name, reviewer_id=None,
                         prohibited_claims=(), comparator_mode="yoy", now=None):
        with self.conn:
            self.conn.execute(
                """INSERT INTO workspace (workspace_id, name, reviewer_id,
                                          prohibited_claims, comparator_mode, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(workspace_id) DO UPDATE SET
                       name=excluded.name, reviewer_id=excluded.reviewer_id,
                       prohibited_claims=excluded.prohibited_claims,
                       comparator_mode=excluded.comparator_mode""",
                (workspace_id, name, reviewer_id, json.dumps(list(prohibited_claims)),
                 comparator_mode, _now(now)))
        return self.workspace(workspace_id)

    def workspace(self, workspace_id):
        row = self.conn.execute("SELECT * FROM workspace WHERE workspace_id=?",
                                (workspace_id,)).fetchone()
        return dict(row) if row else None

    def set_watchlist(self, workspace_id, symbols):
        with self.conn:
            self.conn.execute("DELETE FROM watchlist_item WHERE workspace_id=?",
                              (workspace_id,))
            self.conn.executemany(
                "INSERT INTO watchlist_item (workspace_id, symbol) VALUES (?, ?)",
                [(workspace_id, s) for s in symbols])
        return self.watchlist(workspace_id)

    def watchlist(self, workspace_id):
        rows = self.conn.execute(
            "SELECT symbol FROM watchlist_item WHERE workspace_id=? AND active=1 "
            "ORDER BY symbol", (workspace_id,)).fetchall()
        return [r["symbol"] for r in rows]

    # ------------------------------------------------------------------------- events

    def create_event(self, workspace_id, symbol, period_key, report_date, source_as_of,
                     actor="service:poll", correlation_id=None, now=None):
        """A new report event, or `Duplicate` naming the canonical one (ER-FR-03)."""
        digest = event_hash(workspace_id, symbol, period_key, report_date, source_as_of)
        event_id = digest[:12]
        stamp = _now(now)
        try:
            with self.conn:
                self.conn.execute(
                    """INSERT INTO report_event (event_id, workspace_id, symbol,
                           period_key, report_date, source_as_of, event_hash, state,
                           created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 'discovered', ?)""",
                    (event_id, workspace_id, symbol, period_key, report_date,
                     source_as_of, digest, stamp))
                self._audit(event_id, None, "discovered", actor, None, correlation_id,
                            None, stamp)
        except sqlite3.IntegrityError:
            existing = self.conn.execute(
                "SELECT event_id FROM report_event WHERE event_hash=?",
                (digest,)).fetchone()
            # The constraint is the last line of deduplication (PRD §15) — reaching here
            # means two writers raced and the database settled it.
            raise Duplicate(existing["event_id"] if existing else None, digest)
        return self.event(event_id)

    def event(self, event_id):
        row = self.conn.execute("SELECT * FROM report_event WHERE event_id=?",
                                (event_id,)).fetchone()
        return dict(row) if row else None

    def events(self, workspace_id=None):
        sql = "SELECT * FROM report_event"
        args = ()
        if workspace_id:
            sql += " WHERE workspace_id=?"
            args = (workspace_id,)
        sql += " ORDER BY created_at, event_id"
        return [dict(r) for r in self.conn.execute(sql, args).fetchall()]

    def transition(self, event_id, from_state, to_state, actor, reason_code=None,
                   correlation_id=None, detail=None, now=None):
        """One atomic move plus its audit row. Refuses a move off the wrong state."""
        if to_state not in STATES:
            raise IllegalTransition(f"{to_state!r} is not a state")
        if to_state not in ALLOWED.get(from_state, ()):
            raise IllegalTransition(
                f"{from_state} -> {to_state} is not allowed by the state machine")
        stamp = _now(now)
        with self.conn:
            # The WHERE clause carries the expected state, so two writers cannot both
            # win: the loser updates zero rows and is told what the state actually is.
            cursor = self.conn.execute(
                "UPDATE report_event SET state=? WHERE event_id=? AND state=?",
                (to_state, event_id, from_state))
            if cursor.rowcount != 1:
                current = self.conn.execute(
                    "SELECT state FROM report_event WHERE event_id=?",
                    (event_id,)).fetchone()
                raise IllegalTransition(
                    f"{event_id}: expected {from_state}, found "
                    f"{current['state'] if current else 'no such event'}")
            self._audit(event_id, from_state, to_state, actor, reason_code,
                        correlation_id, detail, stamp)
        return self.event(event_id)

    # --------------------------------------------------------------------------- runs

    def start_run(self, run_id, workspace_id, trigger_type, cursor=None, attempt=1,
                  now=None):
        with self.conn:
            self.conn.execute(
                """INSERT INTO run (run_id, workspace_id, trigger_type, started_at,
                                    cursor, status, attempt)
                   VALUES (?, ?, ?, ?, ?, 'running', ?)""",
                (run_id, workspace_id, trigger_type, _now(now), cursor, attempt))
        return run_id

    def finish_run(self, run_id, status, detected=0, new=0, duplicate=0,
                   next_cursor=None, error_code=None, now=None):
        with self.conn:
            self.conn.execute(
                """UPDATE run SET status=?, completed_at=?, detected_count=?,
                       new_count=?, duplicate_count=?, next_cursor=?, error_code=?
                   WHERE run_id=?""",
                (status, _now(now), detected, new, duplicate, next_cursor, error_code,
                 run_id))
        return self.run(run_id)

    def run(self, run_id):
        row = self.conn.execute("SELECT * FROM run WHERE run_id=?", (run_id,)).fetchone()
        return dict(row) if row else None

    def runs(self, limit=50):
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM run ORDER BY started_at DESC, run_id DESC LIMIT ?",
            (limit,)).fetchall()]

    # ---------------------------------------------------------------- facts and drafts

    def save_factset(self, event_id, factset):
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO fact_set (fact_set_id, event_id, version,
                       source_hash, rule_version, locked_at, payload)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (factset["fact_set_id"], event_id, factset["version"],
                 factset["source_hash"], factset["rule_version"],
                 factset.get("locked_at"), json.dumps(factset, default=str)))
        return factset["fact_set_id"]

    def factsets(self, event_id):
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM fact_set WHERE event_id=? ORDER BY version",
            (event_id,)).fetchall()]

    def latest_factset(self, event_id):
        rows = self.factsets(event_id)
        return json.loads(rows[-1]["payload"]) if rows else None

    def save_metrics(self, fact_set_id, results):
        with self.conn:
            for result in results:
                metric_id = _sha(f"{fact_set_id}|{result['type']}")[:12]
                self.conn.execute(
                    """INSERT OR REPLACE INTO metric (metric_id, fact_set_id, type,
                           value, display, comparator, quality_status, reason_code,
                           payload)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (metric_id, fact_set_id, result["type"], result["value"],
                     result["display"], result["comparator"], result["status"],
                     result["reason_code"], json.dumps(result, default=str)))

    def metrics(self, fact_set_id):
        return [json.loads(r["payload"]) for r in self.conn.execute(
            "SELECT payload FROM metric WHERE fact_set_id=? ORDER BY type",
            (fact_set_id,)).fetchall()]

    def save_draft(self, draft_id, event_id, fact_set_id, template_version, content,
                   status="drafted", version=1, now=None):
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO draft (draft_id, event_id, fact_set_id,
                       template_version, version, status, content, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (draft_id, event_id, fact_set_id, template_version, version, status,
                 json.dumps(content, default=str), _now(now)))
        return draft_id

    def draft(self, draft_id):
        row = self.conn.execute("SELECT * FROM draft WHERE draft_id=?",
                                (draft_id,)).fetchone()
        if not row:
            return None
        out = dict(row)
        out["content"] = json.loads(out["content"])
        return out

    def drafts(self, event_id=None):
        sql = "SELECT * FROM draft"
        args = ()
        if event_id:
            sql += " WHERE event_id=?"
            args = (event_id,)
        sql += " ORDER BY created_at, draft_id"
        out = []
        for row in self.conn.execute(sql, args).fetchall():
            item = dict(row)
            item["content"] = json.loads(item["content"])
            out.append(item)
        return out

    def set_draft_status(self, draft_id, status, bump_version=False):
        with self.conn:
            if bump_version:
                self.conn.execute(
                    "UPDATE draft SET status=?, version=version+1 WHERE draft_id=?",
                    (status, draft_id))
            else:
                self.conn.execute("UPDATE draft SET status=? WHERE draft_id=?",
                                  (status, draft_id))
        return self.draft(draft_id)

    def save_claims(self, draft_id, claims, now=None):
        stamp = _now(now)
        with self.conn:
            self.conn.execute("DELETE FROM claim WHERE draft_id=?", (draft_id,))
            for claim in claims:
                self.conn.execute(
                    """INSERT INTO claim (claim_id, draft_id, slide, text, kind,
                           fact_ids, validation_status, reason_codes, checked_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (claim["claim_id"], draft_id, claim["slide"], claim["text"],
                     claim["kind"], json.dumps(claim["fact_ids"]),
                     claim["validation_status"], json.dumps(claim["reason_codes"]),
                     stamp))

    def claims(self, draft_id):
        out = []
        for row in self.conn.execute(
                "SELECT * FROM claim WHERE draft_id=? ORDER BY slide, claim_id",
                (draft_id,)).fetchall():
            claim = dict(row)
            claim["fact_ids"] = json.loads(claim["fact_ids"])
            claim["reason_codes"] = json.loads(claim["reason_codes"])
            out.append(claim)
        return out

    def update_claim(self, claim_id, text=None, status=None, reason_codes=None,
                     fact_ids=None, now=None):
        current = self.conn.execute("SELECT * FROM claim WHERE claim_id=?",
                                    (claim_id,)).fetchone()
        if not current:
            raise KeyError(claim_id)
        with self.conn:
            self.conn.execute(
                """UPDATE claim SET text=?, validation_status=?, reason_codes=?,
                       fact_ids=?, checked_at=? WHERE claim_id=?""",
                (current["text"] if text is None else text,
                 current["validation_status"] if status is None else status,
                 current["reason_codes"] if reason_codes is None
                 else json.dumps(reason_codes),
                 current["fact_ids"] if fact_ids is None else json.dumps(fact_ids),
                 _now(now), claim_id))

    # -------------------------------------------------------- review and delivery

    def record_decision(self, draft_id, reviewer_id, decision, comment=None, now=None):
        stamp = _now(now)
        decision_id = _sha(f"{draft_id}|{reviewer_id}|{decision}|{stamp}")[:12]
        with self.conn:
            self.conn.execute(
                """INSERT INTO review_decision (decision_id, draft_id, reviewer_id,
                       decision, comment, decided_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (decision_id, draft_id, reviewer_id, decision, comment, stamp))
        return decision_id

    def decisions(self, draft_id):
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM review_decision WHERE draft_id=? ORDER BY decided_at",
            (draft_id,)).fetchall()]

    def deliver(self, draft_id, destination, idempotency_key, now=None):
        """ER-FR-12. A repeated key is `AlreadyDelivered`, never a second review item."""
        delivery_id = _sha(f"{destination}|{idempotency_key}")[:12]
        try:
            with self.conn:
                self.conn.execute(
                    """INSERT INTO delivery (delivery_id, draft_id, destination,
                           idempotency_key, status, delivered_at)
                       VALUES (?, ?, ?, ?, 'delivered', ?)""",
                    (delivery_id, draft_id, destination, idempotency_key, _now(now)))
        except sqlite3.IntegrityError:
            existing = self.conn.execute(
                "SELECT delivery_id FROM delivery WHERE idempotency_key=?",
                (idempotency_key,)).fetchone()
            raise AlreadyDelivered(existing["delivery_id"] if existing else None,
                                   idempotency_key)
        return delivery_id

    def deliveries(self, draft_id=None):
        sql = "SELECT * FROM delivery"
        args = ()
        if draft_id:
            sql += " WHERE draft_id=?"
            args = (draft_id,)
        return [dict(r) for r in self.conn.execute(sql + " ORDER BY delivered_at",
                                                   args).fetchall()]

    # -------------------------------------------------------------------- audit trail

    def _audit(self, event_id, from_state, to_state, actor, reason_code, correlation_id,
               detail, stamp):
        """Append one audit row. Called inside the caller's transaction, never alone."""
        self.conn.execute(
            """INSERT INTO audit_event (event_id, from_state, to_state, actor,
                   reason_code, correlation_id, detail, at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, from_state, to_state, actor, reason_code, correlation_id,
             json.dumps(detail, default=str) if detail is not None else None, stamp))

    def note(self, event_id, actor, detail, reason_code=None, correlation_id=None,
             now=None):
        """An audit row that is not a state change — an edit, a decision, a delivery."""
        with self.conn:
            self._audit(event_id, None, None, actor, reason_code, correlation_id,
                        detail, _now(now))

    def audit(self, event_id=None, limit=200):
        sql = "SELECT * FROM audit_event"
        args = ()
        if event_id:
            sql += " WHERE event_id=?"
            args = (event_id,)
        sql += " ORDER BY audit_id LIMIT ?"
        return [dict(r) for r in self.conn.execute(sql, args + (limit,)).fetchall()]


def append_run_ledger(record, path=RUNS):
    """The human-readable run ledger, beside the database. Append-only, git-ignored.

    Opinions and run outcomes, not paid data — the same convention as `runs.jsonl` in
    `src/tunanetra/` and `warnings.jsonl` in `src/pump-and-dump/`.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as handle:
        handle.write(json.dumps(record, default=str) + "\n")
    return path


# ------------------------------------------------------------------------------ gates


def _fixture(store=None):
    store = store or Store(":memory:")
    store.upsert_workspace("ws1", "Content Ops", reviewer_id="compliance@example",
                           comparator_mode="sequential", now="2026-09-10T08:00:00")
    store.set_watchlist("ws1", ["ADRO", "BBCA", "BBRI", "TLKM"])
    return store


def check_duplicate():
    """AT-02: the same report twice is one event and one `duplicate`."""
    failures = []
    store = _fixture()
    event = store.create_event("ws1", "ADRO", "q1-2026", "2026-03-31", "2026-09-06",
                               now="2026-09-10T08:00:00")
    try:
        store.create_event("ws1", "ADRO", "q1-2026", "2026-03-31", "2026-09-06",
                           now="2026-09-10T09:00:00")
    except Duplicate as exc:
        if exc.event_id != event["event_id"]:
            failures.append("the duplicate did not point at the canonical event")
    else:
        failures.append("a second identical event was created — UNIQUE(event_hash) "
                        "is not doing its job")

    if len(store.events("ws1")) != 1:
        failures.append(f"{len(store.events('ws1'))} events exist, expected 1")

    # A new source_as_of for the same period is a restatement candidate, so a NEW event.
    restated = store.create_event("ws1", "ADRO", "q1-2026", "2026-03-31", "2026-09-20",
                                  now="2026-09-20T08:00:00")
    if restated["event_id"] == event["event_id"]:
        failures.append("a new source_as_of did not produce a distinct event")

    # The hash is stable across processes: it is a pure function of its five inputs.
    if event_hash("ws1", "ADRO", "q1-2026", "2026-03-31", "2026-09-06") != \
            event_hash("ws1", "ADRO", "q1-2026", "2026-03-31", "2026-09-06"):
        failures.append("event_hash is not stable")
    store.close()
    return failures, 5


def check_transitions():
    """PRD §12: the happy path runs, and nothing may skip a step."""
    failures = []
    store = _fixture()
    event = store.create_event("ws1", "BBCA", "q2-2026", "2026-06-30", "2026-09-06",
                               now="2026-09-10T08:00:00")
    event_id = event["event_id"]

    path = ["fetching", "validated", "fact_locked", "drafted", "needs_review", "approved"]
    state = "discovered"
    for to_state in path:
        store.transition(event_id, state, to_state, "service:test",
                         correlation_id="run-1", now="2026-09-10T08:00:00")
        state = to_state
    if store.event(event_id)["state"] != "approved":
        failures.append("the happy path did not reach approved")

    illegal = [
        ("approved", "fact_locked", "backwards to fact_locked"),
        ("needs_review", "approved", "off a state the event is not in"),
    ]
    for from_state, to_state, why in illegal:
        try:
            store.transition(event_id, from_state, to_state, "service:test")
        except IllegalTransition:
            continue
        failures.append(f"an illegal transition was allowed: {why}")

    # Skipping a step from the true current state is refused by the transition table.
    second = store.create_event("ws1", "TLKM", "q2-2026", "2026-06-30", "2026-09-06",
                                now="2026-09-10T08:00:00")
    try:
        store.transition(second["event_id"], "discovered", "approved", "service:test")
    except IllegalTransition:
        pass
    else:
        failures.append("discovered -> approved was allowed")
    if store.event(second["event_id"])["state"] != "discovered":
        failures.append("a refused transition still moved the row")

    # A refused transition writes no audit row: the two are one transaction.
    audit_rows = [r for r in store.audit(second["event_id"]) if r["to_state"] == "approved"]
    if audit_rows:
        failures.append("a refused transition still wrote an audit row")

    # Every state in STATES must be reachable in the table, or it is dead vocabulary.
    reachable = {"discovered"} | {t for moves in ALLOWED.values() for t in moves}
    if set(STATES) - reachable:
        failures.append(f"unreachable states: {sorted(set(STATES) - reachable)}")
    store.close()
    return failures, len(path) + len(illegal) + 4


def check_delivery_idempotency():
    """ER-FR-12: a replay with the same key delivers once."""
    failures = []
    store = _fixture()
    event = store.create_event("ws1", "BBRI", "q1-2026", "2026-03-31", "2026-09-06",
                               now="2026-09-10T08:00:00")
    store.transition(event["event_id"], "discovered", "fetching", "service:test")
    store.transition(event["event_id"], "fetching", "validated", "service:test")
    store.transition(event["event_id"], "validated", "fact_locked", "service:test")
    store.save_factset(event["event_id"], {
        "fact_set_id": "fs1", "version": 1, "source_hash": "h", "rule_version": "r",
        "locked_at": "2026-09-10T08:00:00", "facts": []})
    store.save_draft("d1", event["event_id"], "fs1", "er-carousel-1", {"slides": []})

    key = f"{event['event_id']}|1"
    store.deliver("d1", "review_queue", key, now="2026-09-10T08:00:00")
    try:
        store.deliver("d1", "review_queue", key, now="2026-09-10T09:00:00")
    except AlreadyDelivered:
        pass
    else:
        failures.append("a replayed delivery created a second review item")
    if len(store.deliveries("d1")) != 1:
        failures.append(f"{len(store.deliveries('d1'))} deliveries, expected 1")
    store.close()
    return failures, 3


def check_audit_append_only():
    """The audit table has no mutating SQL anywhere in this module. Checked, not asserted."""
    failures = []
    with open(os.path.abspath(__file__)) as handle:
        source = handle.read().lower()
    # The needles are assembled at runtime so that this check does not find itself.
    table = "audit" + "_event"
    for verb in ("update ", "delete from ", "drop table "):
        statement = verb + table
        if statement in source:
            failures.append(f"store.py contains {statement!r} — the audit trail is no "
                            f"longer append-only")

    store = _fixture()
    event = store.create_event("ws1", "ADRO", "q1-2026", "2026-03-31", "2026-09-06",
                               now="2026-09-10T08:00:00")
    store.transition(event["event_id"], "discovered", "fetching", "service:test",
                     correlation_id="run-1", now="2026-09-10T08:00:01")
    store.note(event["event_id"], "user:ops", {"edited": "slide 2"},
               now="2026-09-10T08:00:02")
    rows = store.audit(event["event_id"])
    if len(rows) != 3:
        failures.append(f"{len(rows)} audit rows, expected 3 (create, move, note)")
    if [r["audit_id"] for r in rows] != sorted(r["audit_id"] for r in rows):
        failures.append("audit rows are not in insertion order")
    for row in rows:
        if not row["actor"] or not row["at"]:
            failures.append("an audit row has no actor or no timestamp")
    store.close()
    return failures, len(rows) + 4


def check_foreign_keys():
    """PRAGMA foreign_keys is per connection and off by default. Prove it is on."""
    failures = []
    store = _fixture()
    if not store.conn.execute("PRAGMA foreign_keys").fetchone()[0]:
        failures.append("foreign keys are off — an orphaned draft would be accepted")
    try:
        store.conn.execute(
            """INSERT INTO draft (draft_id, event_id, fact_set_id, template_version,
                   status, content, created_at)
               VALUES ('x', 'no-such-event', 'no-such-factset', 't', 's', '{}', 'now')""")
        store.conn.commit()
    except sqlite3.IntegrityError:
        pass
    else:
        failures.append("a draft was inserted against a non-existent event")
    store.close()
    return failures, 2


def main():
    results = [("duplicate suppression", *check_duplicate()),
               ("state machine", *check_transitions()),
               ("delivery idempotency", *check_delivery_idempotency()),
               ("audit append-only", *check_audit_append_only()),
               ("foreign keys", *check_foreign_keys())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)
    print("\nthe database refuses what the convention only discourages" if not failed
          else f"\n{failed} store failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
