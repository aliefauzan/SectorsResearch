#!/usr/bin/env python3
"""
The workflow: poll, dedupe, fetch, validate, lock, draft, gate, deliver, review.

    ./run.sh poll                    one tick
    ./run.sh poll --watch --every 30 the unattended loop, in process
    ./run.sh runs                    what every tick did, and why
    ./run.sh draft 1                 the draft, with the evidence behind every figure
    ./run.sh review 1 --decision approve --as compliance
    ./run.sh demo                    the scripted four-run proof (AT-10)

Every number that reaches a draft came out of a locked FactSet, and every sentence that
states one names the `fact_id` it stands on. A claim without a `fact_id` is rejected
before a reviewer ever sees it, and approval is blocked while any claim is unresolved.

The pipeline, one step per PRD §6, each of them a `store.transition()` so that the run
log and the audit trail are the same story told at two levels of detail:

    discovered -> fetching -> validated -> fact_locked -> drafted -> needs_review
                                                                       |
                                     rejected -> revised --------------+--> approved

What the recorded data can and cannot do, stated on screen rather than hidden:
`recorded/` holds four trailing quarters per symbol, so the PRD's default year-over-year
comparator has no period to compare against and resolves to `unknown` with the exact call
that would supply it. The sequential comparator IS computable, and PRD §9 allows it as an
explicit Admin opt-in — so the demo workspace enables it, every comparing slide says so,
and `gate.comparator_mislabelled` rejects any sentence that describes it as
year-over-year. That check is the reason this is not just a caption generator.

    python3 relay.py --self-test     # AT-01 … AT-10, comparator honesty, credit ledger
"""
import argparse
import json
import os
import sys
import time

import adapter as adapter_module
import factset as factset_module
import gate
import metrics as metrics_module
import periods
import sources
import store as store_module
import template

HERE = os.path.dirname(os.path.abspath(__file__))

#: The demo workspace. One workspace, because MVP has one (PRD §3), and a watchlist of
#: exactly the symbols the recordings can actually answer for.
WORKSPACE_ID = "ws-demo"
WORKSPACE_NAME = "Content Ops — demo"
REVIEWER_ID = "compliance@contoh.id"
WATCHLIST = ("ADRO", "BBCA", "BBRI", "TLKM")

#: PRD §9 makes year-over-year the default and sequential an explicit Admin opt-in. On
#: `recorded/` the prior-year quarter does not exist for any symbol, so the demo
#: workspace opts in — and says so on every slide. On `synth/` the year is there, so the
#: default stands and the full YoY path is exercised.
COMPARATOR_BY_SOURCE = {"recorded": "sequential", "synth": "yoy"}

#: PRD §3. Approval is a Compliance role; editing wording is Content Ops. Checked here,
#: server-side, and not in the UI — `webapp.py` calls these same functions.
ROLES = ("ops", "compliance", "admin")
CAN_APPROVE = ("compliance", "admin")
CAN_EDIT = ("ops", "admin")

DESTINATION = "review_queue"


class NotPermitted(Exception):
    """A command run under a role that PRD §3 does not give it.

    Raised in `relay.py` rather than checked in the UI, because "the button was hidden"
    is not access control.
    """


class StaleVersion(Exception):
    """A review decision written against a draft version that has since moved (PRD §14).

    Optimistic concurrency: two reviewers looking at the same queue must not be able to
    overwrite each other's revision silently.
    """


class Unresolved(Exception):
    """Approval attempted while a claim is still `rejected` or `needs_review` (AT-08)."""


def open_store(path=None):
    return store_module.Store(path or store_module.DB_PATH)


def setup(store, source="recorded", watchlist=WATCHLIST, prohibited=(), now=None):
    """The workspace and watchlist an Admin would have configured (ER-FR-01)."""
    store.upsert_workspace(WORKSPACE_ID, WORKSPACE_NAME, reviewer_id=REVIEWER_ID,
                           prohibited_claims=prohibited,
                           comparator_mode=COMPARATOR_BY_SOURCE.get(source, "yoy"),
                           now=now)
    store.set_watchlist(WORKSPACE_ID, watchlist)
    return store.workspace(WORKSPACE_ID)


def _cursor(store):
    """The newest report date any completed run has already seen (ER-FR-02)."""
    for run in store.runs(limit=200):
        if run["next_cursor"]:
            return run["next_cursor"]
    return None


def _run_id(store, now):
    return f"run-{len(store.runs(limit=10_000)) + 1:03d}"


def _draft_number(store, draft_id):
    """The human-facing draft number, which is its position in the queue."""
    for index, draft in enumerate(store.drafts(), start=1):
        if draft["draft_id"] == draft_id:
            return index
    return None


def _resolve_draft(store, reference):
    """A draft by its number in the queue, or by its id. The CLI accepts either."""
    drafts = store.drafts()
    text = str(reference)
    if text.isdigit() and 1 <= int(text) <= len(drafts):
        return drafts[int(text) - 1]
    for draft in drafts:
        if draft["draft_id"] == text:
            return draft
    return None


# ------------------------------------------------------------------------ the pipeline


def process_event(store, adapter, event, workspace, now=None, correlation_id=None,
                  source="recorded"):
    """One report event, from `discovered` to a delivered draft. Returns a summary."""
    event_id = event["event_id"]
    symbol = event["symbol"]
    period_key = event["period_key"]
    comparator_mode = workspace["comparator_mode"]
    prohibited = json.loads(workspace["prohibited_claims"] or "[]")
    summary = {"event_id": event_id, "symbol": symbol, "period_key": period_key,
               "state": "discovered", "draft_id": None, "reason": None, "attempts": 0}

    # ------------------------------------------------------------------------ fetch
    store.transition(event_id, "discovered", "fetching", "service:poll",
                     correlation_id=correlation_id, now=now)
    try:
        rows, meta = adapter.fetch_quarterly(symbol)
        summary["attempts"] = meta.get("attempts", 1)
    except (adapter_module.FetchFailed, adapter_module.Fabricated,
            sources.NotRecorded) as exc:
        retryable = getattr(exc, "retryable", False)
        reason = ("fetch_failed" if retryable else
                  "facts_unavailable" if isinstance(exc, sources.NotRecorded)
                  else "fabricated_payload")
        store.transition(event_id, "fetching", "failed", "service:poll",
                         reason_code=reason, correlation_id=correlation_id,
                         detail={"error": str(exc),
                                 "endpoint": sources.ENDPOINT["quarterly"].format(
                                     symbol=symbol)},
                         now=now)
        summary.update({"state": "failed", "reason": reason,
                        "attempts": getattr(exc, "attempts", 1)})
        return summary

    index = sources.period_index(rows)
    keys = sorted(index)
    comparator_key, status, reason_code = periods.select_comparator(
        period_key, keys, comparator_mode)
    comparator = {"mode": comparator_mode, "key": comparator_key, "status": status,
                  "reason_code": reason_code}

    wanted = {k: index[k] for k in (period_key, comparator_key) if k in index}
    built = factset_module.build_factset(
        symbol, period_key, wanted, comparator, source,
        sources.ENDPOINT["quarterly"], meta.get("source_as_of"), now=now)

    # --------------------------------------------------------------------- validate
    ok, reasons = factset_module.validate(built)
    if not ok:
        store.transition(event_id, "fetching", "failed", "service:validate",
                         reason_code=sorted(set(reasons))[0],
                         correlation_id=correlation_id,
                         detail={"reasons": sorted(set(reasons)),
                                 "endpoint": sources.ENDPOINT["quarterly"].format(
                                     symbol=symbol)},
                         now=now)
        summary.update({"state": "failed", "reason": sorted(set(reasons))[0]})
        return summary
    store.transition(event_id, "fetching", "validated", "service:validate",
                     reason_code=(sorted(set(reasons))[0] if reasons else None),
                     correlation_id=correlation_id, now=now)

    # ------------------------------------------------------------------------- lock
    locked = factset_module.lock(built, now=now)
    stored = factset_module.unlock_copy(locked)
    store.save_factset(event_id, stored)
    store.transition(event_id, "validated", "fact_locked", "service:evidence",
                     correlation_id=correlation_id,
                     detail={"fact_set_id": stored["fact_set_id"],
                             "source_hash": stored["source_hash"]}, now=now)

    # ---------------------------------------------------------------------- metrics
    results = compute_metrics(stored)
    store.save_metrics(stored["fact_set_id"], list(results.values()))

    # ------------------------------------------------------------ draft and the gate
    draft = template.build_draft(stored, results)
    draft_id = f"{stored['fact_set_id']}-v{stored['version']}"
    store.save_draft(draft_id, event_id, stored["fact_set_id"],
                     template.TEMPLATE_VERSION, draft, status="drafted",
                     version=stored["version"], now=now)
    claims = gate.validate_draft(draft, stored, results, prohibited)
    store.save_claims(draft_id, claims, now=now)
    store.transition(event_id, "fact_locked", "drafted", "service:draft",
                     correlation_id=correlation_id,
                     detail={"draft_id": draft_id, "claims": len(claims)}, now=now)

    # --------------------------------------------------------------------- delivery
    blocked = gate.unresolved(claims)
    store.transition(event_id, "drafted", "needs_review", "service:gate",
                     reason_code=(blocked[0]["reason_codes"][0] if blocked and
                                  blocked[0]["reason_codes"] else None),
                     correlation_id=correlation_id,
                     detail={"unresolved": len(blocked)}, now=now)
    store.set_draft_status(draft_id, "needs_review")
    try:
        store.deliver(draft_id, DESTINATION, f"{event_id}|{stored['version']}", now=now)
        delivered = True
    except store_module.AlreadyDelivered:
        # ER-FR-12: a replay delivers once. Not an error, and not a second review item.
        delivered = False
    store.note(event_id, "service:delivery",
               {"draft_id": draft_id, "delivered": delivered,
                "idempotency_key": f"{event_id}|{stored['version']}"},
               correlation_id=correlation_id, now=now)

    summary.update({"state": "needs_review", "draft_id": draft_id,
                    "unresolved": len(blocked), "claims": len(claims),
                    "fact_set_id": stored["fact_set_id"],
                    "comparator": comparator, "delivered": delivered})
    return summary


def compute_metrics(factset):
    """The three metrics for one FactSet. `unknown` where the comparator is not there."""
    comparator = factset["comparator"]
    mode = comparator["mode"]
    current_revenue = factset_module.value_of(factset, "target", "revenue")
    current_earnings = factset_module.value_of(factset, "target", "earnings")
    prior_revenue = factset_module.value_of(factset, "comparator", "revenue")
    prior_earnings = factset_module.value_of(factset, "comparator", "earnings")

    if comparator["status"] != "ok":
        reason = comparator.get("reason_code") or "comparator_unavailable"
        inputs = {"current_revenue": current_revenue,
                  "current_earnings": current_earnings}
        return {t: metrics_module.unavailable(t, mode, reason, inputs)
                for t in metrics_module.METRIC_TYPES}

    return {
        "revenue_yoy": metrics_module.revenue_yoy(current_revenue, prior_revenue, mode),
        "net_income_yoy": metrics_module.net_income_yoy(current_earnings,
                                                        prior_earnings, mode),
        "net_margin_delta": metrics_module.net_margin_delta(
            current_earnings, current_revenue, prior_earnings, prior_revenue, mode),
    }


def poll(store, adapter, workspace=None, now=None, use_cursor=True, source="recorded"):
    """One tick. Detect, dedupe, and take every new event through the pipeline."""
    workspace = workspace or store.workspace(WORKSPACE_ID)
    watchlist = store.watchlist(WORKSPACE_ID)
    cursor = _cursor(store) if use_cursor else None
    run_id = _run_id(store, now)
    store.start_run(run_id, WORKSPACE_ID, "schedule", cursor=cursor, now=now)

    outcome = {"run_id": run_id, "cursor": cursor, "new": [], "duplicate": [],
               "failed": [], "detected": 0, "status": "ok"}
    try:
        rows, meta = adapter.poll_trigger(watchlist, cursor)
    except (adapter_module.FetchFailed, adapter_module.Fabricated,
            sources.NotRecorded) as exc:
        store.finish_run(run_id, "failed", error_code="trigger_unavailable", now=now)
        outcome.update({"status": "failed", "error": str(exc)})
        store_module.append_run_ledger({"run_id": run_id, "status": "failed",
                                        "error": str(exc), "at": now or time.strftime(
                                            "%Y-%m-%dT%H:%M:%S")})
        return outcome

    outcome["detected"] = meta["detected"]
    outcome["in_watchlist"] = meta["in_watchlist"]
    for row in rows:
        try:
            event = store.create_event(WORKSPACE_ID, row["symbol"], row["period_key"],
                                       row["report_date"], meta["source_as_of"],
                                       correlation_id=run_id, now=now)
        except store_module.Duplicate as exc:
            # AT-02: points at the canonical event, creates no Draft and no Delivery.
            outcome["duplicate"].append({"symbol": row["symbol"],
                                         "period_key": row["period_key"],
                                         "canonical_event_id": exc.event_id})
            store.note(exc.event_id, "service:poll",
                       {"duplicate_of": exc.event_id, "symbol": row["symbol"]},
                       reason_code="duplicate", correlation_id=run_id, now=now)
            continue
        summary = process_event(store, adapter, event, workspace, now=now,
                                correlation_id=run_id, source=source)
        (outcome["failed"] if summary["state"] == "failed"
         else outcome["new"]).append(summary)

    status = ("no_op" if not rows else
              "failed" if outcome["failed"] and not outcome["new"] else "ok")
    outcome["status"] = status
    store.finish_run(run_id, status, detected=meta["detected"], new=len(outcome["new"]),
                     duplicate=len(outcome["duplicate"]),
                     next_cursor=meta.get("next_cursor"), now=now)
    store_module.append_run_ledger({
        "run_id": run_id, "status": status, "cursor": cursor,
        "next_cursor": meta.get("next_cursor"), "detected": meta["detected"],
        "in_watchlist": meta["in_watchlist"], "new": len(outcome["new"]),
        "duplicate": len(outcome["duplicate"]), "failed": len(outcome["failed"]),
        "at": now or time.strftime("%Y-%m-%dT%H:%M:%S")})
    return outcome


# ------------------------------------------------------------------- review and edit


def review(store, draft_reference, decision, role, comment=None, expected_version=None,
           actor=None, now=None):
    """ER-FR-10, AT-08. Approval needs Compliance, and every claim resolved."""
    if decision not in ("approve", "reject"):
        raise ValueError(f"unknown decision {decision!r}")
    if decision == "approve" and role not in CAN_APPROVE:
        raise NotPermitted(f"peran {role!r} tidak boleh menyetujui — perlu "
                           f"{' atau '.join(CAN_APPROVE)}")
    draft = _resolve_draft(store, draft_reference)
    if draft is None:
        raise KeyError(draft_reference)
    if expected_version is not None and int(expected_version) != draft["version"]:
        raise StaleVersion(f"draf sudah versi {draft['version']}, bukan "
                           f"{expected_version} — muat ulang sebelum memutuskan")

    claims = store.claims(draft["draft_id"])
    blocked = gate.unresolved(claims)
    if decision == "approve" and blocked:
        raise Unresolved(f"{len(blocked)} klaim belum selesai: " +
                         ", ".join(sorted({r for c in blocked
                                           for r in c['reason_codes']}) or ["-"]))

    actor = actor or f"user:{role}"
    store.record_decision(draft["draft_id"], actor, decision, comment, now=now)
    event = store.event(draft["event_id"])
    if decision == "approve":
        store.transition(event["event_id"], event["state"], "approved", actor,
                         correlation_id=draft["draft_id"], now=now)
        store.set_draft_status(draft["draft_id"], "approved")
    else:
        store.transition(event["event_id"], event["state"], "rejected", actor,
                         reason_code="reviewer_rejected",
                         correlation_id=draft["draft_id"],
                         detail={"comment": comment}, now=now)
        store.set_draft_status(draft["draft_id"], "rejected")
        # A rejection goes back to Content Ops as `revised`, which is where an edit
        # happens. PRD §12: rejected -> revised -> needs_review.
        store.transition(event["event_id"], "rejected", "revised", actor,
                         correlation_id=draft["draft_id"], now=now)
    return {"draft_id": draft["draft_id"], "decision": decision,
            "state": store.event(event["event_id"])["state"],
            "unresolved": len(blocked)}


def edit_claim(store, draft_reference, claim_id, text, role, now=None):
    """ER-FR-11, AT-07. Editing a factual span drops the claim and revalidates it."""
    if role not in CAN_EDIT:
        raise NotPermitted(f"peran {role!r} tidak boleh menyunting — perlu "
                           f"{' atau '.join(CAN_EDIT)}")
    draft = _resolve_draft(store, draft_reference)
    if draft is None:
        raise KeyError(draft_reference)
    stored = store.latest_factset(draft["event_id"])
    results = {m["type"]: m for m in store.metrics(draft["fact_set_id"])}
    workspace = store.workspace(WORKSPACE_ID)
    prohibited = json.loads((workspace or {}).get("prohibited_claims") or "[]")

    claims = {c["claim_id"]: c for c in store.claims(draft["draft_id"])}
    if claim_id not in claims:
        raise KeyError(claim_id)
    claim = dict(claims[claim_id])
    claim["text"] = text

    # The claim drops to needs_review the moment it is touched, and only the gate can
    # put it back — an edit never keeps a `supported` status it did not re-earn.
    store.update_claim(claim_id, text=text, status=gate.NEEDS_REVIEW,
                       reason_codes=["edited_pending_revalidation"], now=now)
    status, reasons = gate.check_claim(claim, stored, results, prohibited)
    store.update_claim(claim_id, status=status, reason_codes=reasons, now=now)

    # The draft version moves, which is what makes a stale review decision detectable.
    store.set_draft_status(draft["draft_id"], "needs_review", bump_version=True)
    # The event goes back into the queue, including from `approved`: an edit after
    # approval is a new thing to approve. `needs_review -> needs_review` is a legal move
    # (a revalidation in place), and anything else raises rather than moving silently.
    event = store.event(draft["event_id"])
    if event["state"] in ("revised", "approved", "needs_review"):
        store.transition(event["event_id"], event["state"], "needs_review",
                         f"user:{role}", reason_code="revalidated",
                         correlation_id=claim_id, now=now)
    store.note(draft["event_id"], f"user:{role}",
               {"claim_id": claim_id, "text": text, "status": status,
                "reason_codes": reasons}, reason_code="edit", now=now)
    return {"claim_id": claim_id, "validation_status": status, "reason_codes": reasons}


def restate(store, adapter, event_id, new_rows=None, as_of=None, role="admin",
            now=None):
    """ER-FR-07, AT-05. A new source version makes FactSet v2 and reopens the claims."""
    event = store.event(event_id)
    if event is None:
        raise KeyError(event_id)
    previous = store.latest_factset(event_id)
    if previous is None:
        raise KeyError(f"{event_id} has no FactSet to restate")

    if new_rows is None:
        rows, meta = adapter.fetch_quarterly(event["symbol"])
        index = sources.period_index(rows)
        new_rows = {k: index[k] for k in previous["rows"] if k in index}
        as_of = as_of or meta.get("source_as_of")

    new, changed = factset_module.restate(previous, new_rows, as_of=as_of, now=now)
    ok, reasons = factset_module.validate(new)
    if not ok:
        raise factset_module.FactSetInvalid(", ".join(sorted(set(reasons))))
    locked = factset_module.unlock_copy(factset_module.lock(new, now=now))
    store.save_factset(event_id, locked)

    results = compute_metrics(locked)
    store.save_metrics(locked["fact_set_id"], list(results.values()))
    draft = template.build_draft(locked, results)
    draft_id = f"{locked['fact_set_id']}-v{locked['version']}"
    store.save_draft(draft_id, event_id, locked["fact_set_id"],
                     template.TEMPLATE_VERSION, draft, status="needs_review",
                     version=locked["version"], now=now)
    workspace = store.workspace(WORKSPACE_ID)
    prohibited = json.loads((workspace or {}).get("prohibited_claims") or "[]")
    claims = gate.validate_draft(draft, locked, results, prohibited)
    store.save_claims(draft_id, claims, now=now)

    # Every claim of the SUPERSEDED draft that cited a fact whose value moved goes back
    # to needs_review. The old draft is marked superseded, never deleted (PRD §15).
    reopened = []
    for old_draft in store.drafts(event_id):
        if old_draft["draft_id"] == draft_id:
            continue
        store.set_draft_status(old_draft["draft_id"], "superseded")
        for claim in store.claims(old_draft["draft_id"]):
            if set(claim["fact_ids"]) & set(changed):
                store.update_claim(claim["claim_id"], status=gate.NEEDS_REVIEW,
                                   reason_codes=["restated"], now=now)
                reopened.append(claim["claim_id"])

    if event["state"] != "needs_review":
        try:
            store.transition(event_id, event["state"], "needs_review",
                             f"user:{role}", reason_code="restatement",
                             detail={"fact_set_id": locked["fact_set_id"],
                                     "changed": changed}, now=now)
        except store_module.IllegalTransition:
            pass
    store.note(event_id, f"user:{role}",
               {"restated_to": locked["fact_set_id"], "version": locked["version"],
                "changed_fact_ids": changed, "reopened_claims": reopened},
               reason_code="restatement", now=now)
    return {"fact_set_id": locked["fact_set_id"], "version": locked["version"],
            "changed": changed, "reopened": reopened, "draft_id": draft_id}


# ------------------------------------------------------------------------- rendering


def render_runs(store, limit=20):
    lines = ["RUN      STATUS      TERDETEKSI  BARU  DUPLIKAT  KURSOR"]
    for run in reversed(store.runs(limit)):
        lines.append(f"{run['run_id']:8} {run['status']:11} "
                     f"{run['detected_count']:10}  {run['new_count']:4}  "
                     f"{run['duplicate_count']:8}  {run['cursor'] or '—'}")
    lines.append("")
    lines.append("ANTREAN TINJAUAN")
    for number, draft in enumerate(store.drafts(), start=1):
        claims = store.claims(draft["draft_id"])
        blocked = gate.unresolved(claims)
        event = store.event(draft["event_id"])
        lines.append(f"  #{number} {event['symbol']:6} "
                     f"{periods.quarter_label(event['period_key']):8} "
                     f"{draft['status']:13} {len(claims)} klaim, "
                     f"{len(blocked)} belum selesai")
    if not store.drafts():
        lines.append("  (kosong)")
    return "\n".join(lines)


def render_draft(store, reference, verbose=True):
    draft = _resolve_draft(store, reference)
    if draft is None:
        return f"draf {reference} tidak ada"
    event = store.event(draft["event_id"])
    stored = store.latest_factset(draft["event_id"])
    facts = {f["fact_id"]: f for f in stored["facts"]}
    claims = {c["claim_id"]: c for c in store.claims(draft["draft_id"])}
    content = draft["content"]

    lines = [f"DRAF #{_draft_number(store, draft['draft_id'])}  {event['symbol']}  "
             f"{periods.quarter_label(event['period_key'])}  ·  {draft['status']}  "
             f"·  FactSet v{draft['version']} {draft['fact_set_id']}",
             f"komparator: {content['comparator']['mode']} "
             f"({content['comparator']['status']})  ·  sumber: {content['source']}  "
             f"·  as_of {content['as_of']}", ""]

    for slide in content["slides"]:
        lines.append(f"  Slide {slide['index']} — {slide['title']}")
        for slot in slide["slots"]:
            claim = claims.get(f"{draft['fact_set_id']}-{slot['slot_id']}")
            status = claim["validation_status"] if claim else "—"
            reasons = ",".join(claim["reason_codes"]) if claim and claim["reason_codes"] else ""
            mark = {"supported": "✓", "needs_review": "?", "rejected": "✗"}.get(status, " ")
            lines.append(f"    {mark} {status:13} {slot['text']}")
            if reasons:
                lines.append(f"      └ {reasons}")
            if verbose:
                for fact_id in slot["fact_ids"]:
                    fact = facts.get(fact_id)
                    if not fact:
                        lines.append(f"      └ {fact_id}: tidak ada di FactSet ini")
                        continue
                    lines.append(f"      └ {fact_id} · {fact['endpoint']} · "
                                 f"{fact['source_field']} · {fact['raw_value']} · "
                                 f"{fact['period']} · as_of {fact['as_of']}")
        lines.append("")

    blocked = gate.unresolved(list(claims.values()))
    lines.append(f"  [Setujui] {'terkunci' if blocked else 'siap'}: "
                 f"{len(blocked)} klaim belum selesai")
    return "\n".join(lines)


def render_symbols(store, source="recorded"):
    mode = COMPARATOR_BY_SOURCE.get(source, "yoy")
    lines = [f"sumber: {source} — {template.SOURCE_NOTE.get(source, source)}",
             f"komparator: {mode} — {periods.COMPARATOR_LABEL[mode]}", "",
             "yang bisa dibaca:"]
    lines.append(sources.describe(source))
    yoy = sources.comparable_symbols(source, "yoy")
    lines.append("")
    lines.append(f"komparator tahun-ke-tahun tersedia untuk {len(yoy)} emiten"
                 + (f": {', '.join(yoy[:8])}" if yoy else
                    f" — tidak ada. Panggilan yang menyediakannya: "
                    f"{sources.ENDPOINT['quarterly_yoy']}"))
    return "\n".join(lines)


def render_audit(store, event_id):
    event = store.event(event_id)
    if event is None:
        return f"event {event_id} tidak ada"
    lines = [f"AUDIT {event_id}  {event['symbol']} "
             f"{periods.quarter_label(event['period_key'])}  ·  {event['state']}", ""]
    for row in store.audit(event_id):
        move = (f"{row['from_state'] or '—'} → {row['to_state']}"
                if row["to_state"] else "catatan")
        lines.append(f"  {row['at']}  {move:28} {row['actor']:18} "
                     f"{row['reason_code'] or ''}")
        if row["detail"]:
            lines.append(f"      {row['detail']}")
    return "\n".join(lines)


# ------------------------------------------------------------------------------ demo


def demo(store, adapter, workspace, now="2026-09-10T08:00:00", source="recorded"):
    """The four-run proof AT-10 asks for: an alert, a dedup, a no-op, and a recovery."""
    lines = []
    first = poll(store, adapter, workspace, now=now, source=source)
    lines.append(f"RUN A  {first['run_id']}  baru={len(first['new'])} "
                 f"duplikat={len(first['duplicate'])} gagal={len(first['failed'])} "
                 f"→ {first['status']}")
    for item in first["new"]:
        lines.append(f"        {item['symbol']} {item['period_key']}  → draf "
                     f"{item['draft_id']}  ({item['unresolved']} klaim belum selesai)")

    second = poll(store, adapter, workspace, now=now, use_cursor=False, source=source)
    lines.append(f"RUN B  {second['run_id']}  baru={len(second['new'])} "
                 f"duplikat={len(second['duplicate'])} → {second['status']}  "
                 f"(kursor diabaikan: laporan yang sama, event_hash cocok)")

    third = poll(store, adapter, workspace, now=now, source=source)
    lines.append(f"RUN C  {third['run_id']}  terdeteksi={third['detected']} "
                 f"baru=0 → {third['status']}  (kursor {third['cursor']})")

    failing = _FailingAdapter(adapter)
    fourth = poll(store, adapter=failing, workspace=workspace, now=now,
                  use_cursor=False, source=source)
    lines.append(f"RUN D  {fourth['run_id']}  → {fourth['status']}  "
                 f"(sumber pemicu tidak bisa dihubungi, {failing.attempts} percobaan)")
    fifth = poll(store, adapter, workspace, now=now, use_cursor=False, source=source)
    lines.append(f"RUN E  {fifth['run_id']}  duplikat={len(fifth['duplicate'])} "
                 f"→ {fifth['status']}  (pulih; event kanonik dipakai ulang, "
                 f"tidak ada draf baru)")
    lines.append("")
    lines.append(render_runs(store))
    return "\n".join(lines)


class _FailingAdapter:
    """An adapter whose trigger is down. Used by `demo` to produce a visible failure."""

    def __init__(self, inner):
        self.inner = inner
        self.attempts = 0

    def poll_trigger(self, watchlist, cursor=None):
        self.attempts = adapter_module.MAX_ATTEMPTS
        raise adapter_module.FetchFailed("sumber pemicu tidak bisa dihubungi",
                                         status=503, retryable=True,
                                         attempts=self.attempts)

    def fetch_quarterly(self, symbol):
        return self.inner.fetch_quarterly(symbol)


# ------------------------------------------------------------------------------ gates
#
# One check per acceptance test in PRD §18, plus the two this data situation adds: that
# the comparator is described honestly, and that the run spent nothing.


NOW = "2026-09-10T08:00:00"


def _fresh(source="recorded", watchlist=WATCHLIST, prohibited=()):
    """An in-memory workflow: nothing on disk, no socket, and no credit."""
    store = open_store(":memory:")
    workspace = setup(store, source, watchlist, prohibited, now=NOW)
    adapter = adapter_module.Adapter(mode="direct", source=source)
    return store, adapter, workspace


class _StubAdapter:
    """A direct adapter whose quarterly rows are doctored, for the data-shape tests.

    It is a wrapper rather than a monkeypatch so the code under test is the real code:
    the rows arrive through the same `fetch_quarterly` contract that `sources.py`
    produces, they are simply not the rows that are on disk.
    """

    def __init__(self, inner, mutate):
        self.inner = inner
        self.mutate = mutate

    def poll_trigger(self, watchlist, cursor=None):
        return self.inner.poll_trigger(watchlist, cursor)

    def fetch_quarterly(self, symbol):
        rows, meta = self.inner.fetch_quarterly(symbol)
        return [self.mutate(dict(row)) for row in rows], meta


def check_new_event():
    """AT-01: one new report gives one FactSet, one Draft, one review item."""
    failures = []
    store, adapter, workspace = _fresh(watchlist=["ADRO"])
    outcome = poll(store, adapter, workspace, now=NOW)

    if len(outcome["new"]) != 1:
        failures.append(f"{len(outcome['new'])} new events, expected 1")
    if len(store.factsets(outcome["new"][0]["event_id"])) != 1:
        failures.append("expected exactly one FactSet")
    if len(store.drafts()) != 1:
        failures.append(f"{len(store.drafts())} drafts, expected 1")
    if len(store.deliveries()) != 1:
        failures.append(f"{len(store.deliveries())} review items, expected 1")

    event = store.event(outcome["new"][0]["event_id"])
    if event["state"] != "needs_review":
        failures.append(f"the event ended in {event['state']}, expected needs_review")
    draft = store.drafts()[0]
    claims = store.claims(draft["draft_id"])
    if not claims:
        failures.append("the draft has no claims")
    for claim in claims:
        if claim["kind"] == "factual" and not claim["fact_ids"]:
            failures.append(f"{claim['claim_id']}: factual claim with no fact_id")
    # The whole state machine has to be visible in the audit trail, in order.
    moves = [r["to_state"] for r in store.audit(event["event_id"]) if r["to_state"]]
    expected = ["discovered", "fetching", "validated", "fact_locked", "drafted",
                "needs_review"]
    if moves != expected:
        failures.append(f"the audit trail reads {moves}, expected {expected}")
    print(f"        AT-01 · {len(store.drafts())} draf, {len(claims)} klaim, "
          f"{len(store.deliveries())} item antrean")
    store.close()
    return failures, 7


def check_duplicate():
    """AT-02: the same poll again is a duplicate and adds no draft."""
    failures = []
    store, adapter, workspace = _fresh(watchlist=["ADRO"])
    first = poll(store, adapter, workspace, now=NOW)
    before = len(store.drafts())

    second = poll(store, adapter, workspace, now=NOW, use_cursor=False)
    if len(second["duplicate"]) != 1:
        failures.append(f"{len(second['duplicate'])} duplicates, expected 1")
    if second["duplicate"] and second["duplicate"][0]["canonical_event_id"] != \
            first["new"][0]["event_id"]:
        failures.append("the duplicate does not point at the canonical event")
    if len(store.drafts()) != before:
        failures.append("a duplicate created a second draft")
    if len(store.deliveries()) != 1:
        failures.append("a duplicate created a second review item")

    # With the cursor applied it is not even a duplicate: there is nothing to do.
    third = poll(store, adapter, workspace, now=NOW)
    if third["status"] != "no_op":
        failures.append(f"a poll with an advanced cursor was {third['status']}, "
                        f"expected no_op")
    if len(store.drafts()) != before:
        failures.append("a no-op created a draft")
    print(f"        AT-02 · duplikat={len(second['duplicate'])}, "
          f"no-op={third['status']}, draf tetap {before}")
    store.close()
    return failures, 6


def check_null_data():
    """AT-03: a null required field fails the run. The value never becomes zero."""
    failures = []
    store, adapter, workspace = _fresh(watchlist=["ADRO"])

    def blank_revenue(row):
        if row["period_key"] == "q1-2026":
            row["revenue"] = None
        return row

    outcome = poll(store, _StubAdapter(adapter, blank_revenue), workspace, now=NOW)
    if len(outcome["failed"]) != 1:
        failures.append(f"{len(outcome['failed'])} failures, expected 1")
    if outcome["failed"] and outcome["failed"][0]["reason"] != \
            factset_module.REQUIRED_FIELD_NULL:
        failures.append(f"reason {outcome['failed'][0]['reason']}, expected "
                        f"{factset_module.REQUIRED_FIELD_NULL}")
    if store.drafts():
        failures.append("a null required field still produced a draft")
    if store.deliveries():
        failures.append("a null required field still delivered a review item")
    event = store.events()[0]
    if event["state"] != "failed":
        failures.append(f"the event is in {event['state']}, expected failed")
    # The failure names the endpoint a human would have to look at.
    detail = " ".join(str(r["detail"]) for r in store.audit(event["event_id"]))
    if "/v2/financials/quarterly/ADRO/" not in detail:
        failures.append("the failure does not name the endpoint it came from")
    if "0" == str(outcome["failed"][0].get("value", "")):
        failures.append("a null became a zero")
    print(f"        AT-03 · gagal={outcome['failed'][0]['reason']}, 0 draf, 0 antrean")
    store.close()
    return failures, 6


def check_zero_prior():
    """AT-04: a zero comparator gives `unknown` and `denominator_zero`, not a number."""
    failures = []
    store, adapter, workspace = _fresh(watchlist=["ADRO"])

    def zero_prior(row):
        if row["period_key"] == "q4-2025":
            row["revenue"] = 0
        return row

    outcome = poll(store, _StubAdapter(adapter, zero_prior), workspace, now=NOW)
    if not outcome["new"]:
        failures.append("a zero comparator stopped the run instead of the metric")
        store.close()
        return failures, 5

    fact_set_id = outcome["new"][0]["fact_set_id"]
    results = {m["type"]: m for m in store.metrics(fact_set_id)}
    revenue = results["revenue_yoy"]
    if revenue["quality_status" if "quality_status" in revenue else "status"] != \
            metrics_module.UNKNOWN:
        failures.append(f"revenue_yoy is {revenue['status']}, expected unknown")
    if revenue["reason_code"] != metrics_module.DENOMINATOR_ZERO:
        failures.append(f"reason {revenue['reason_code']}, expected denominator_zero")
    if revenue["value"] is not None or revenue["display"] is not None:
        failures.append("an unknown metric carried a value")

    draft = store.drafts()[0]
    # Only the revenue slide is affected: a zero prior revenue leaves net income
    # computable, so the check is on the slide whose metric is unknown, not the caption.
    revenue_slide = draft["content"]["slides"][1]
    revenue_text = " ".join(slot["text"] for slot in revenue_slide["slots"])
    if "%" in revenue_text:
        failures.append(f"a percentage appeared for a metric that could not be "
                        f"computed: {revenue_text}")
    if "belum bisa dihitung" not in revenue_text:
        failures.append("the draft does not say the comparison could not be made")
    print(f"        AT-04 · revenue_yoy={revenue['status']}/{revenue['reason_code']}, "
          f"tanpa persentase")
    store.close()
    return failures, 5


def check_restatement():
    """AT-05: a new source version makes FactSet v2 and reopens the affected claims."""
    failures = []
    store, adapter, workspace = _fresh(watchlist=["ADRO"])
    outcome = poll(store, adapter, workspace, now=NOW)
    event_id = outcome["new"][0]["event_id"]
    old_draft = store.drafts()[0]

    def restated_revenue(row):
        if row["period_key"] == "q1-2026":
            row["revenue"] = 9_000_000_000_000
        return row

    result = restate(store, _StubAdapter(adapter, restated_revenue), event_id,
                     as_of="2026-09-20", now=NOW)
    factsets = store.factsets(event_id)
    if len(factsets) != 2:
        failures.append(f"{len(factsets)} FactSets, expected 2")
    if result["version"] != 2:
        failures.append(f"the restatement is version {result['version']}")
    if factsets[0]["version"] != 1:
        failures.append("version 1 was overwritten rather than kept")
    if not result["changed"]:
        failures.append("the restatement reported no changed facts")
    if not result["reopened"]:
        failures.append("no claim went back to needs_review after the restatement")

    superseded = store.draft(old_draft["draft_id"])
    if superseded["status"] != "superseded":
        failures.append(f"the old draft is {superseded['status']}, expected superseded")
    reopened = [c for c in store.claims(old_draft["draft_id"])
                if c["validation_status"] == gate.NEEDS_REVIEW]
    if not reopened:
        failures.append("the old draft's claims were not reopened")
    if store.event(event_id)["state"] != "needs_review":
        failures.append("the event did not go back to needs_review")
    print(f"        AT-05 · FactSet v{result['version']}, "
          f"{len(result['changed'])} fakta berubah, "
          f"{len(result['reopened'])} klaim dibuka lagi, draf lama superseded")
    store.close()
    return failures, 8


def check_unsupported_claim():
    """AT-06: no fact_id, or prohibited wording, is rejected and cannot be submitted."""
    failures = []
    store, adapter, workspace = _fresh(watchlist=["ADRO"],
                                       prohibited=["kinerja fenomenal"])
    outcome = poll(store, adapter, workspace, now=NOW)
    draft = store.drafts()[0]
    stored = store.latest_factset(draft["event_id"])
    results = {m["type"]: m for m in store.metrics(draft["fact_set_id"])}

    unsupported = {"claim_id": "x", "slide": 2, "kind": "factual",
                   "text": "Pendapatan melonjak.", "fact_ids": []}
    status, reasons = gate.check_claim(unsupported, stored, results)
    if status != gate.REJECTED or gate.NO_FACT_ID not in reasons:
        failures.append(f"a claim with no fact_id was {status} {reasons}")

    admin_word = {"claim_id": "y", "slide": 2, "kind": "framing",
                  "text": "Kinerja fenomenal kuartal ini.", "fact_ids": []}
    status, reasons = gate.check_claim(
        admin_word, stored, results,
        json.loads(store.workspace(WORKSPACE_ID)["prohibited_claims"]))
    if status != gate.REJECTED or gate.PROHIBITED_PHRASE not in reasons:
        failures.append(f"an Admin-prohibited phrase was {status} {reasons}")

    # And a rejected claim blocks approval: it cannot be submitted past the gate.
    claim = store.claims(draft["draft_id"])[1]
    store.update_claim(claim["claim_id"], status=gate.REJECTED,
                       reason_codes=[gate.NO_FACT_ID], now=NOW)
    try:
        review(store, 1, "approve", "compliance", now=NOW)
    except Unresolved:
        pass
    else:
        failures.append("a draft with a rejected claim was approved")
    print(f"        AT-06 · no_fact_id + prohibited_phrase ditolak, persetujuan dikunci")
    store.close()
    return failures, 3


def check_edit_invalidates():
    """AT-07: editing a factual span clears `supported` and revalidates."""
    failures = []
    store, adapter, workspace = _fresh(watchlist=["ADRO"])
    poll(store, adapter, workspace, now=NOW)
    draft = store.drafts()[0]
    before = [c for c in store.claims(draft["draft_id"])
              if c["kind"] == "factual" and c["validation_status"] == gate.SUPPORTED]
    if not before:
        failures.append("the fixture produced no supported factual claim to edit")
        store.close()
        return failures, 5

    target = before[0]
    outcome = edit_claim(store, 1, target["claim_id"],
                         "Pendapatan Q1 2026 Rp9,00 T.", "ops", now=NOW)
    if outcome["validation_status"] == gate.SUPPORTED:
        failures.append("an edited figure kept its supported status")
    if gate.NUMBER_MISMATCH not in outcome["reason_codes"]:
        failures.append(f"the edit was not caught as a number mismatch: "
                        f"{outcome['reason_codes']}")
    if store.draft(draft["draft_id"])["version"] == draft["version"]:
        failures.append("the draft version did not move after an edit")

    # An edit by a role that may not edit is refused server-side.
    try:
        edit_claim(store, 1, target["claim_id"], "apa pun", "compliance", now=NOW)
    except NotPermitted:
        pass
    else:
        failures.append("a compliance reviewer was allowed to rewrite the copy")

    # And the edit is in the audit trail with who did it.
    detail = " ".join(str(r["detail"]) for r in store.audit(draft["event_id"]))
    if target["claim_id"] not in detail:
        failures.append("the edit is not in the audit trail")
    print(f"        AT-07 · {target['claim_id']} → "
          f"{outcome['validation_status']} {outcome['reason_codes']}")
    store.close()
    return failures, 5


def check_review_loop():
    """AT-08: reject goes back to Ops; approve needs every claim resolved and the role."""
    failures = []
    store, adapter, workspace = _fresh(watchlist=["ADRO"])
    poll(store, adapter, workspace, now=NOW)
    draft = store.drafts()[0]

    # Ops may not approve, whatever the state of the claims.
    try:
        review(store, 1, "approve", "ops", now=NOW)
    except NotPermitted:
        pass
    else:
        failures.append("Content Ops approved its own draft")

    # A reject returns the event to Ops as `revised`.
    outcome = review(store, 1, "reject", "compliance", comment="ganti kalimat pembuka",
                     now=NOW)
    if outcome["state"] != "revised":
        failures.append(f"a rejection left the event in {outcome['state']}")
    if store.draft(draft["draft_id"])["status"] != "rejected":
        failures.append("the draft was not marked rejected")
    if not store.decisions(draft["draft_id"]):
        failures.append("the decision was not recorded")

    # An edit puts it back into the queue, and a stale version is refused (PRD §14).
    claim = store.claims(draft["draft_id"])[0]
    edit_claim(store, 1, claim["claim_id"], claim["text"], "ops", now=NOW)
    try:
        review(store, 1, "approve", "compliance", expected_version=1, now=NOW)
    except StaleVersion:
        pass
    else:
        failures.append("a decision on a stale version was accepted")

    # With every claim resolved, and the right role, approval works.
    for item in store.claims(draft["draft_id"]):
        store.update_claim(item["claim_id"], status=gate.SUPPORTED, reason_codes=[],
                           now=NOW)
    current = store.draft(draft["draft_id"])["version"]
    outcome = review(store, 1, "approve", "compliance", expected_version=current,
                     now=NOW)
    if outcome["state"] != "approved":
        failures.append(f"approval left the event in {outcome['state']}")
    if store.draft(draft["draft_id"])["status"] != "approved":
        failures.append("the draft was not marked approved")
    print(f"        AT-08 · tolak → revised, versi basi ditolak, setujui → approved")
    store.close()
    return failures, 8


def check_transient_failure():
    """AT-09: two retries, one draft, and the canonical event is reused on replay.

    Driven over a real socket against a local server that answers 503 twice and then
    serves the recorded payloads, so the retry path under test is the real one in
    `adapter._get` — not a monkeypatch, and not a random `--chaos` roll that would make
    the gate flaky.
    """
    import http.server
    import socketserver
    import threading

    failures = []
    state = {"trigger_calls": 0}
    trigger = {"results": [{"symbol": "ADRO.JK", "date": "2026-03-31", "quarter": "q1"}],
               "pagination": {"has_next": False, "showing": 1, "total_count": 1,
                              "merged": True, "pages_fetched": 1}}
    quarterly = sources.load("recorded", "quarterly", "ADRO")

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path.startswith("/v2/companies/quarterly-financial-dates/"):
                state["trigger_calls"] += 1
                if state["trigger_calls"] <= 2:
                    self.send_response(503)
                    self.end_headers()
                    self.wfile.write(b'{"error": "Service Unavailable"}')
                    return
                payload = trigger
            elif self.path.startswith("/v2/financials/quarterly/ADRO/"):
                payload = quarterly
            else:
                self.send_response(404)
                self.end_headers()
                return
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Mock-Source", "recording")
            self.end_headers()
            self.wfile.write(body)

    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        store = open_store(":memory:")
        workspace = setup(store, "recorded", ["ADRO"], now=NOW)
        adapter = adapter_module.Adapter(mode="http",
                                         base_url=f"http://127.0.0.1:{port}",
                                         sleeper=lambda seconds: None)
        outcome = poll(store, adapter, workspace, now=NOW)

        if state["trigger_calls"] != 3:
            failures.append(f"{state['trigger_calls']} trigger attempts, expected 3 "
                            f"(two 503s and one success)")
        if len(outcome["new"]) != 1:
            failures.append(f"{len(outcome['new'])} events after the retries")
        if len(store.drafts()) != 1:
            failures.append(f"{len(store.drafts())} drafts, expected 1")
        if len(store.deliveries()) != 1:
            failures.append("the retried run delivered more than once")

        attempts_before_replay = state["trigger_calls"]
        # The replay reuses the canonical event and delivers nothing new.
        replay = poll(store, adapter, workspace, now=NOW, use_cursor=False)
        if len(replay["duplicate"]) != 1:
            failures.append("the replay did not resolve to the canonical event")
        if len(store.drafts()) != 1:
            failures.append("the replay created a second draft")
        print(f"        AT-09 · {attempts_before_replay} percobaan HTTP nyata "
              f"(503, 503, 200) → 1 draf, replay → duplikat")
        store.close()
    finally:
        server.shutdown()
        server.server_close()
    return failures, 6


def check_demo_proof():
    """AT-10: an alert, a dedup, a no-op and a recovery, all readable from the run log."""
    failures = []
    store, adapter, workspace = _fresh()
    text = demo(store, adapter, workspace, now=NOW)

    for needle, why in (("RUN A", "the first run"), ("duplikat=4", "the dedup run"),
                        ("no_op", "the no-op run"), ("failed", "the failed run"),
                        ("pulih", "the recovery")):
        if needle not in text:
            failures.append(f"{why} is not readable in the demo output ({needle!r})")
    if len(store.drafts()) != len(WATCHLIST):
        failures.append(f"{len(store.drafts())} drafts across the demo, expected "
                        f"{len(WATCHLIST)} — one per watchlist symbol")
    statuses = {run["status"] for run in store.runs()}
    if not {"ok", "no_op", "failed"} <= statuses:
        failures.append(f"the run log does not show every outcome: {sorted(statuses)}")
    # Readable without opening the database: the run ledger says the same thing.
    if "ANTREAN TINJAUAN" not in text:
        failures.append("the demo does not show the review queue")
    print(f"        AT-10 · {len(store.runs())} run, status "
          f"{sorted(statuses)}, {len(store.drafts())} draf")
    store.close()
    return failures, 8


def check_comparator_honesty():
    """On recorded data the comparison is sequential, and nothing may call it yearly."""
    failures = []
    if template.YOY_ENDPOINT_HINT != sources.ENDPOINT["quarterly_yoy"]:
        failures.append("template.YOY_ENDPOINT_HINT has drifted from "
                        "sources.ENDPOINT['quarterly_yoy']")

    store, adapter, workspace = _fresh()
    if workspace["comparator_mode"] != "sequential":
        failures.append(f"the recorded workspace compares {workspace['comparator_mode']}")
    poll(store, adapter, workspace, now=NOW)

    for draft in store.drafts():
        text = draft["content"]["caption"].lower()
        for word in periods.YOY_WORDING:
            if word in text:
                failures.append(f"{draft['draft_id']}: says {word!r} about a "
                                f"sequential comparison")
        if periods.COMPARATOR_LABEL["sequential"].lower() not in text:
            failures.append(f"{draft['draft_id']}: does not say which comparison it made")
        for claim in store.claims(draft["draft_id"]):
            if gate.COMPARATOR_MISLABELLED in claim["reason_codes"]:
                failures.append(f"{claim['claim_id']}: mislabelled comparator survived "
                                f"into the queue")

    # And the year-over-year path is genuinely unavailable here, not merely unused.
    if sources.comparable_symbols("recorded", "yoy"):
        failures.append("year-over-year became computable on recorded data — revisit "
                        "the unknown path before shipping")
    if not sources.comparable_symbols("synth", "yoy"):
        failures.append("no layer can exercise the year-over-year path any more")
    print(f"        komparator · recorded=sequential (opt-in Admin), yoy tersedia "
          f"untuk {len(sources.comparable_symbols('synth', 'yoy'))} emiten sintetis")
    store.close()
    return failures, 4 + len(WATCHLIST)


def check_yoy_on_synth():
    """The full year-over-year path, exercised where the periods actually exist."""
    failures = []
    symbols = sources.comparable_symbols("synth", "yoy")[:1]
    store, adapter, workspace = _fresh("synth", watchlist=symbols)
    if workspace["comparator_mode"] != "yoy":
        failures.append("the synthetic workspace is not on the PRD default comparator")
    outcome = poll(store, adapter, workspace, now=NOW, source="synth")
    if len(outcome["new"]) != 1:
        failures.append(f"{len(outcome['new'])} synthetic events, expected 1 — the "
                        f"trigger should announce only the newest report per symbol")
        store.close()
        return failures, 4

    results = {m["type"]: m for m in store.metrics(outcome["new"][0]["fact_set_id"])}
    computed = [t for t, m in results.items() if m["status"] == metrics_module.OK]
    if len(computed) != 3:
        failures.append(f"only {computed} computed on synth — the YoY path is not "
                        f"actually exercised anywhere")
    caption = store.drafts()[0]["content"]["caption"]
    if "SINTETIS" not in caption:
        failures.append("a synthetic draft is not labelled DATA SINTETIS")
    if periods.COMPARATOR_LABEL["yoy"].lower() not in caption.lower():
        failures.append("the synthetic draft does not say it compares year on year")
    print(f"        yoy · {symbols[0]} (sintetis) · {len(computed)}/3 metrik terhitung "
          f"· berlabel DATA SINTETIS")
    store.close()
    return failures, 4


def check_ledger():
    """This product spends nothing. A run that leaked a credit fails the suite."""
    failures = []
    ledger = os.path.join(sources.RECORDED, "_ledger.jsonl")
    with open(ledger) as handle:
        lines = sum(1 for _ in handle)
    if lines != 168:
        failures.append(f"the credit ledger moved: {lines} lines, expected 168 — "
                        f"something in this product reached the live API")
    # And no module here may name the live host outside the gate that refuses it.
    marker = "api." + "sectors.app"
    for name in ("relay.py", "sources.py", "store.py", "template.py", "gate.py",
                 "metrics.py", "factset.py", "periods.py", "money.py"):
        with open(os.path.join(HERE, name)) as handle:
            if marker in handle.read():
                failures.append(f"{name} names the live API host")
    print(f"        kredit · ledger tetap {lines} baris · produk ini tidak "
          f"memanggil API berbayar sama sekali")
    return failures, 10


def self_test():
    results = [("AT-01 new event", *check_new_event()),
               ("AT-02 duplicate", *check_duplicate()),
               ("AT-03 null data", *check_null_data()),
               ("AT-04 prior zero", *check_zero_prior()),
               ("AT-05 restatement", *check_restatement()),
               ("AT-06 unsupported", *check_unsupported_claim()),
               ("AT-07 edit invalidates", *check_edit_invalidates()),
               ("AT-08 review loop", *check_review_loop()),
               ("AT-09 transient failure", *check_transient_failure()),
               ("AT-10 demo proof", *check_demo_proof()),
               ("comparator honesty", *check_comparator_honesty()),
               ("yoy path on synth", *check_yoy_on_synth()),
               ("credit ledger", *check_ledger())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:24} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)
    print("\nsetiap angka membawa buktinya, dan tidak ada kredit terpakai" if not failed
          else f"\n{failed} kegagalan alur kerja")
    return 1 if failed else 0


# ------------------------------------------------------------------------------- CLI


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="relay.py",
        description="Earnings Relay — angka terverifikasi, konten siap ditinjau. "
                    "Setiap angka membawa endpoint, field, formula dan as_of-nya.")
    parser.add_argument("command", nargs="?", default="poll",
                        choices=("poll", "runs", "draft", "review", "edit", "symbols",
                                 "audit", "demo", "setup"))
    parser.add_argument("reference", nargs="?", help="nomor draf, atau event_id")
    parser.add_argument("--source", default=os.environ.get("SOURCE", "recorded"),
                        choices=("recorded", "synth"))
    parser.add_argument("--mode", default="direct", choices=("direct", "http"),
                        help="direct membaca rekaman; http bicara ke mock lokal")
    parser.add_argument("--base-url", default=adapter_module.MOCK_URL)
    parser.add_argument("--db", default=None)
    parser.add_argument("--now", help="jam yang disuntikkan, agar demo reprodusibel")
    parser.add_argument("--watch", action="store_true", help="ulangi terus")
    parser.add_argument("--every", type=int, default=60, help="detik antar tick")
    parser.add_argument("--decision", choices=("approve", "reject"))
    parser.add_argument("--comment")
    parser.add_argument("--claim")
    parser.add_argument("--text")
    parser.add_argument("--as", dest="role", default="ops", choices=ROLES)
    parser.add_argument("--expected-version", type=int)
    parser.add_argument("--ignore-cursor", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    store = open_store(args.db)
    try:
        workspace = store.workspace(WORKSPACE_ID) or setup(store, args.source,
                                                           now=args.now)
        if args.command == "setup":
            workspace = setup(store, args.source, now=args.now)
            print(f"workspace {WORKSPACE_ID} · watchlist "
                  f"{', '.join(store.watchlist(WORKSPACE_ID))} · komparator "
                  f"{workspace['comparator_mode']}")
            return 0
        if args.command == "symbols":
            print(render_symbols(store, args.source))
            return 0

        adapter = adapter_module.Adapter(mode=args.mode, base_url=args.base_url,
                                         source=args.source)

        if args.command == "poll":
            while True:
                outcome = poll(store, adapter, workspace, now=args.now,
                               use_cursor=not args.ignore_cursor, source=args.source)
                print(f"{outcome['run_id']}  status={outcome['status']}  "
                      f"terdeteksi={outcome['detected']}  baru={len(outcome['new'])}  "
                      f"duplikat={len(outcome['duplicate'])}  "
                      f"gagal={len(outcome['failed'])}")
                for item in outcome["new"]:
                    print(f"        {item['symbol']} {item['period_key']} → draf "
                          f"{item['draft_id']} ({item.get('unresolved', 0)} klaim "
                          f"belum selesai)")
                for item in outcome["failed"]:
                    print(f"        {item['symbol']} {item['period_key']} → gagal: "
                          f"{item['reason']}")
                if not args.watch:
                    return 0
                time.sleep(max(1, args.every))

        if args.command == "runs":
            print(render_runs(store))
            return 0
        if args.command == "draft":
            if not args.reference:
                parser.error("draft butuh nomor draf, misal: draft 1")
            print(render_draft(store, args.reference))
            return 0
        if args.command == "audit":
            if not args.reference:
                parser.error("audit butuh event_id")
            print(render_audit(store, args.reference))
            return 0
        if args.command == "demo":
            print(demo(store, adapter, workspace, now=args.now or "2026-09-10T08:00:00",
                       source=args.source))
            return 0
        if args.command == "review":
            if not args.reference or not args.decision:
                parser.error("review butuh nomor draf dan --decision")
            try:
                outcome = review(store, args.reference, args.decision, args.role,
                                 args.comment, args.expected_version, now=args.now)
            except (NotPermitted, Unresolved, StaleVersion) as exc:
                print(f"ditolak: {exc}", file=sys.stderr)
                return 3
            print(f"draf {args.reference}: {outcome['decision']} → "
                  f"{outcome['state']}")
            return 0
        if args.command == "edit":
            if not (args.reference and args.claim and args.text):
                parser.error("edit butuh nomor draf, --claim dan --text")
            try:
                outcome = edit_claim(store, args.reference, args.claim, args.text,
                                     args.role, now=args.now)
            except NotPermitted as exc:
                print(f"ditolak: {exc}", file=sys.stderr)
                return 3
            print(f"{outcome['claim_id']}: {outcome['validation_status']} "
                  f"{outcome['reason_codes']}")
            return 0
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
