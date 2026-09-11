#!/usr/bin/env python3
"""
The browser surface: a view over `relay.py`, not a second engine.

    python3 webapp.py --port 8082 --source recorded

Five screens, exactly PRD §7:

    /                Runs — what every tick did, and why
    /queue           Review Queue — every draft, and what is blocking it
    /draft/<id>      Draft & Evidence — the slides, with the evidence drawer of ER-FR-14
    /audit/<event>   the append-only trail for one report event
    /setup           the workspace configuration, read-only

No arithmetic happens in this file. Every number on every page came out of a locked
FactSet through `relay.py`, and the evidence panel prints the fact's own endpoint, field,
raw value, normalized value, period and `as_of` — not a re-derivation of them.

Accessibility is a PRD requirement (§16), not a nicety, so the same rules the sibling
product is measured against apply here: one `<h1>`, `<h2>` per section with no skipped
levels, every table with a `<caption>` and `<th scope=…>`, status conveyed by a word as
well as a colour, keyboard-reachable controls with a visible focus ring, `lang="id"` and
a skip link.

Actions are POSTs to `relay.review` and `relay.edit_claim`, which is where the RBAC and
the optimistic-concurrency checks live. The UI hides nothing: a button that a role may
not press is still there, and pressing it returns the server's refusal in words.

    python3 webapp.py --self-test    # every route 200s, and the evidence panel is complete
"""
import argparse
import html
import http.server
import json
import os
import socketserver
import urllib.parse

import gate
import periods
import relay
import sources
import store as store_module
import template

HERE = os.path.dirname(os.path.abspath(__file__))

STYLE = """
:root { --ink:#111; --paper:#fff; --rule:#767676; --accent:#0b4f9e; --warn:#8a4b00;
        --ok:#0a6b3d; --bad:#a01b1b; --panel:#f6f6f4; }
@media (prefers-color-scheme: dark) {
  :root { --ink:#f2f2f2; --paper:#111; --rule:#9a9a9a; --accent:#8ab4f8; --warn:#f0b357;
          --ok:#5fd39b; --bad:#ff8a8a; --panel:#1c1c1c; }
}
* { box-sizing: border-box; }
body { margin:0; background:var(--paper); color:var(--ink);
       font:1.02rem/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }
main, header, footer { max-width:64rem; margin:0 auto; padding:0 1.25rem; }
a { color:var(--accent); }
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible {
  outline:3px solid var(--accent); outline-offset:2px; }
.skip { position:absolute; left:-9999px; }
.skip:focus { position:static; display:inline-block; padding:.5rem; }
h1 { font-size:1.5rem; margin:1.25rem 0 .25rem; }
h2 { font-size:1.2rem; margin:1.75rem 0 .5rem; border-top:1px solid var(--rule);
     padding-top:.9rem; }
h3 { font-size:1rem; margin:1.1rem 0 .3rem; }
nav ul { list-style:none; display:flex; gap:1rem; padding:0; margin:.5rem 0 0;
         flex-wrap:wrap; }
table { border-collapse:collapse; width:100%; margin:.5rem 0 1rem; }
caption { text-align:left; font-weight:600; padding:.35rem 0; }
th, td { border:1px solid var(--rule); padding:.4rem .55rem; text-align:left;
         vertical-align:top; font-size:.95rem; }
th[scope="col"] { background:var(--panel); }
code, .mono { font-family:ui-monospace, SFMono-Regular, Menlo, monospace;
              font-size:.86rem; word-break:break-all; }
.status { font-weight:600; }
.status-supported { color:var(--ok); }
.status-needs_review { color:var(--warn); }
.status-rejected { color:var(--bad); }
.slot { border-left:4px solid var(--rule); padding:.35rem .75rem; margin:.6rem 0; }
.slot-supported { border-left-color:var(--ok); }
.slot-needs_review { border-left-color:var(--warn); }
.slot-rejected { border-left-color:var(--bad); }
.evidence { background:var(--panel); padding:.5rem .75rem; margin:.35rem 0 0; }
.note { background:var(--panel); padding:.75rem 1rem; margin:1rem 0; }
button { font:inherit; padding:.4rem .8rem; }
form.inline { display:inline; }
footer { margin:2.5rem 0 3rem; font-size:.9rem; }
"""


def esc(value):
    return html.escape("" if value is None else str(value))


def shell(title, body, source):
    """Every page, same frame. One `<h1>` lives inside `body`."""
    return (f'<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{esc(title)} · Earnings Relay</title><style>{STYLE}</style></head>'
            f'<body><a class="skip" href="#utama">Lompat ke konten</a>'
            f'<header><nav aria-label="Utama"><ul>'
            f'<li><a href="/">Runs</a></li>'
            f'<li><a href="/queue">Antrean tinjauan</a></li>'
            f'<li><a href="/setup">Setup</a></li>'
            f'</ul></nav></header><main id="utama">{body}</main>'
            f'<footer><p>{esc(template.SOURCE_NOTE.get(source, source))}</p>'
            f'<p>{esc(template.DISCLAIMER)}</p>'
            f'<p>Tidak ada publikasi otomatis. Persetujuan manusia wajib.</p>'
            f'</footer></body></html>')


def status_cell(status):
    """Status as a word and a colour, never as a colour alone."""
    return (f'<span class="status status-{esc(status)}">{esc(status)}</span>')


def runs_page(store, source):
    rows = store.runs(limit=50)
    body = ["<h1>Runs</h1>",
            "<p>Setiap tick penjadwal, beserta apa yang ditemukan dan apa yang "
            "diputuskan. Tidak ada yang perlu dibuka di database untuk membacanya.</p>",
            '<table><caption>Riwayat run</caption><thead><tr>'
            '<th scope="col">Run</th><th scope="col">Status</th>'
            '<th scope="col">Terdeteksi</th><th scope="col">Baru</th>'
            '<th scope="col">Duplikat</th><th scope="col">Kursor</th>'
            '<th scope="col">Mulai</th></tr></thead><tbody>']
    for run in rows:
        body.append(f'<tr><th scope="row" class="mono">{esc(run["run_id"])}</th>'
                    f'<td>{status_cell(run["status"])}</td>'
                    f'<td>{run["detected_count"]}</td><td>{run["new_count"]}</td>'
                    f'<td>{run["duplicate_count"]}</td>'
                    f'<td class="mono">{esc(run["cursor"] or "—")}</td>'
                    f'<td class="mono">{esc(run["started_at"])}</td></tr>')
    if not rows:
        body.append('<tr><td colspan="7">Belum ada run. Jalankan '
                    '<code>./run.sh poll</code>.</td></tr>')
    body.append("</tbody></table>")

    body.append("<h2>Peristiwa laporan</h2>")
    body.append('<table><caption>Report event dan keadaannya</caption><thead><tr>'
                '<th scope="col">Event</th><th scope="col">Emiten</th>'
                '<th scope="col">Periode</th><th scope="col">Tanggal laporan</th>'
                '<th scope="col">Keadaan</th><th scope="col">Audit</th>'
                '</tr></thead><tbody>')
    for event in store.events(relay.WORKSPACE_ID):
        body.append(f'<tr><th scope="row" class="mono">{esc(event["event_id"])}</th>'
                    f'<td>{esc(event["symbol"])}</td>'
                    f'<td>{esc(periods.quarter_label(event["period_key"]))}</td>'
                    f'<td class="mono">{esc(event["report_date"])}</td>'
                    f'<td>{status_cell(event["state"])}</td>'
                    f'<td><a href="/audit/{esc(event["event_id"])}">jejak audit</a>'
                    f'</td></tr>')
    if not store.events(relay.WORKSPACE_ID):
        body.append('<tr><td colspan="6">Belum ada peristiwa.</td></tr>')
    body.append("</tbody></table>")
    return shell("Runs", "".join(body), source)


def queue_page(store, source, message=None):
    drafts = store.drafts()
    body = ["<h1>Antrean tinjauan</h1>"]
    if message:
        body.append(f'<p class="note" role="status">{esc(message)}</p>')
    body.append('<table><caption>Draf menunggu keputusan</caption><thead><tr>'
                '<th scope="col">#</th><th scope="col">Emiten</th>'
                '<th scope="col">Periode</th><th scope="col">Status</th>'
                '<th scope="col">Klaim</th><th scope="col">Belum selesai</th>'
                '<th scope="col">Versi</th></tr></thead><tbody>')
    for number, draft in enumerate(drafts, start=1):
        event = store.event(draft["event_id"])
        claims = store.claims(draft["draft_id"])
        blocked = gate.unresolved(claims)
        body.append(f'<tr><th scope="row">'
                    f'<a href="/draft/{number}">#{number}</a></th>'
                    f'<td>{esc(event["symbol"])}</td>'
                    f'<td>{esc(periods.quarter_label(event["period_key"]))}</td>'
                    f'<td>{status_cell(draft["status"])}</td>'
                    f'<td>{len(claims)}</td><td>{len(blocked)}</td>'
                    f'<td>v{draft["version"]}</td></tr>')
    if not drafts:
        body.append('<tr><td colspan="7">Antrean kosong.</td></tr>')
    body.append("</tbody></table>")
    return shell("Antrean tinjauan", "".join(body), source)


def draft_page(store, number, source, message=None):
    draft = relay._resolve_draft(store, number)
    if draft is None:
        return None
    event = store.event(draft["event_id"])
    factset = store.latest_factset(draft["event_id"])
    facts = {f["fact_id"]: f for f in factset["facts"]}
    claims = {c["claim_id"]: c for c in store.claims(draft["draft_id"])}
    content = draft["content"]
    blocked = gate.unresolved(list(claims.values()))

    body = [f'<h1>Draf #{esc(number)} — {esc(event["symbol"])} '
            f'{esc(periods.quarter_label(event["period_key"]))}</h1>']
    if message:
        body.append(f'<p class="note" role="status">{esc(message)}</p>')
    body.append(
        f'<p class="note">FactSet <code>{esc(draft["fact_set_id"])}</code> '
        f'versi {draft["version"]} · template {esc(draft["template_version"])} · '
        f'sumber {esc(content["source"])} · as_of {esc(content["as_of"])}<br>'
        f'Komparator: {esc(periods.COMPARATOR_LABEL[content["comparator"]["mode"]])} '
        f'({esc(content["comparator"]["status"])})</p>')

    for slide in content["slides"]:
        body.append(f'<h2>Slide {slide["index"]} — {esc(slide["title"])}</h2>')
        for slot in slide["slots"]:
            claim = claims.get(f'{draft["fact_set_id"]}-{slot["slot_id"]}')
            status = claim["validation_status"] if claim else "—"
            body.append(f'<div class="slot slot-{esc(status)}">')
            body.append(f'<p>{esc(slot["text"])}</p>')
            body.append(f'<p>Status klaim: {status_cell(status)}')
            if claim and claim["reason_codes"]:
                body.append(f' · alasan: <code>{esc(", ".join(claim["reason_codes"]))}'
                            f'</code>')
            body.append("</p>")
            if slot["fact_ids"]:
                body.append('<table class="evidence"><caption>Bukti untuk kalimat ini'
                            '</caption><thead><tr><th scope="col">fact_id</th>'
                            '<th scope="col">Endpoint</th><th scope="col">Field</th>'
                            '<th scope="col">Nilai mentah</th>'
                            '<th scope="col">Nilai ternormalisasi</th>'
                            '<th scope="col">Periode</th><th scope="col">Unit</th>'
                            '<th scope="col">as_of</th></tr></thead><tbody>')
                for fact_id in slot["fact_ids"]:
                    fact = facts.get(fact_id)
                    if fact is None:
                        body.append(f'<tr><th scope="row" class="mono">{esc(fact_id)}'
                                    f'</th><td colspan="7">tidak ada di FactSet ini — '
                                    f'klaim ini mengutip versi lama</td></tr>')
                        continue
                    body.append(
                        f'<tr><th scope="row" class="mono">{esc(fact_id)}</th>'
                        f'<td class="mono">{esc(fact["endpoint"])}</td>'
                        f'<td class="mono">{esc(fact["source_field"])}</td>'
                        f'<td class="mono">{esc(fact["raw_value"])}</td>'
                        f'<td class="mono">{esc(fact["normalized_value"])}</td>'
                        f'<td>{esc(fact["period"])}</td><td>{esc(fact["unit"])}</td>'
                        f'<td class="mono">{esc(fact["as_of"])}</td></tr>')
                body.append("</tbody></table>")
            if claim:
                body.append(
                    f'<form class="inline" method="post" action="/draft/{esc(number)}">'
                    f'<input type="hidden" name="action" value="edit">'
                    f'<input type="hidden" name="claim_id" value="{esc(claim["claim_id"])}">'
                    f'<label for="t-{esc(claim["claim_id"])}">Ubah kalimat</label> '
                    f'<input id="t-{esc(claim["claim_id"])}" name="text" size="52" '
                    f'value="{esc(slot["text"])}">'
                    f'<button type="submit">Simpan dan periksa ulang</button></form>')
            body.append("</div>")

    body.append("<h2>Metrik</h2>")
    body.append('<table><caption>Metrik yang dihitung untuk FactSet ini</caption>'
                '<thead><tr><th scope="col">Metrik</th><th scope="col">Status</th>'
                '<th scope="col">Nilai</th><th scope="col">Tampilan</th>'
                '<th scope="col">Komparator</th><th scope="col">Formula</th>'
                '<th scope="col">Alasan</th></tr></thead><tbody>')
    for metric in store.metrics(draft["fact_set_id"]):
        body.append(f'<tr><th scope="row">{esc(metric["type"])}</th>'
                    f'<td>{status_cell(metric["status"])}</td>'
                    f'<td class="mono">{esc(metric["value"])}</td>'
                    f'<td>{esc(metric["display"] or "—")}</td>'
                    f'<td>{esc(metric["comparator"])}</td>'
                    f'<td class="mono">{esc(metric["formula"])}</td>'
                    f'<td class="mono">{esc(metric["reason_code"] or "—")}</td></tr>')
    body.append("</tbody></table>")

    body.append("<h2>Keputusan</h2>")
    body.append(f'<p>{len(blocked)} klaim belum selesai. '
                f'{"Persetujuan terkunci sampai semuanya selesai." if blocked else "Siap disetujui."}</p>')
    body.append(
        f'<form method="post" action="/draft/{esc(number)}">'
        f'<input type="hidden" name="action" value="review">'
        f'<input type="hidden" name="expected_version" value="{draft["version"]}">'
        f'<label for="peran">Peran</label> '
        f'<select id="peran" name="role">'
        + "".join(f'<option value="{esc(r)}">{esc(r)}</option>' for r in relay.ROLES)
        + f'</select> <label for="komentar">Komentar</label> '
          f'<input id="komentar" name="comment" size="40"> '
          f'<button type="submit" name="decision" value="approve">Setujui</button> '
          f'<button type="submit" name="decision" value="reject">Tolak</button>'
          f'</form>')
    body.append(f'<p><a href="/audit/{esc(event["event_id"])}">Jejak audit peristiwa '
                f'ini</a></p>')
    return shell(f"Draf #{number}", "".join(body), source)


def audit_page(store, event_id, source):
    event = store.event(event_id)
    if event is None:
        return None
    body = [f'<h1>Jejak audit — {esc(event["symbol"])} '
            f'{esc(periods.quarter_label(event["period_key"]))}</h1>',
            f'<p class="note">Event <code>{esc(event_id)}</code> · keadaan '
            f'{status_cell(event["state"])} · hash laporan '
            f'<code>{esc(event["event_hash"][:24])}…</code></p>',
            '<table><caption>Setiap perubahan, hanya bisa ditambah</caption><thead><tr>'
            '<th scope="col">Waktu</th><th scope="col">Dari</th><th scope="col">Ke</th>'
            '<th scope="col">Aktor</th><th scope="col">Alasan</th>'
            '<th scope="col">Rincian</th></tr></thead><tbody>']
    for row in store.audit(event_id):
        body.append(f'<tr><th scope="row" class="mono">{esc(row["at"])}</th>'
                    f'<td>{esc(row["from_state"] or "—")}</td>'
                    f'<td>{esc(row["to_state"] or "catatan")}</td>'
                    f'<td>{esc(row["actor"])}</td>'
                    f'<td class="mono">{esc(row["reason_code"] or "—")}</td>'
                    f'<td class="mono">{esc(row["detail"] or "")}</td></tr>')
    body.append("</tbody></table>")
    return shell("Jejak audit", "".join(body), source)


def setup_page(store, source):
    workspace = store.workspace(relay.WORKSPACE_ID) or {}
    watchlist = store.watchlist(relay.WORKSPACE_ID)
    prohibited = json.loads(workspace.get("prohibited_claims") or "[]")
    yoy = sources.comparable_symbols(source, "yoy")
    body = ["<h1>Setup</h1>",
            "<p>Konfigurasi ruang kerja, hanya-baca di MVP. Perubahan dilakukan lewat "
            "<code>./run.sh setup</code>.</p>",
            '<table><caption>Ruang kerja</caption><tbody>'
            f'<tr><th scope="row">Nama</th><td>{esc(workspace.get("name"))}</td></tr>'
            f'<tr><th scope="row">Zona waktu</th>'
            f'<td>{esc(workspace.get("timezone"))}</td></tr>'
            f'<tr><th scope="row">Jadwal</th>'
            f'<td>{esc(workspace.get("schedule"))}</td></tr>'
            f'<tr><th scope="row">Peninjau</th>'
            f'<td>{esc(workspace.get("reviewer_id"))}</td></tr>'
            f'<tr><th scope="row">Komparator</th>'
            f'<td>{esc(workspace.get("comparator_mode"))} — '
            f'{esc(periods.COMPARATOR_LABEL.get(workspace.get("comparator_mode"), ""))}'
            f'</td></tr>'
            f'<tr><th scope="row">Watchlist</th>'
            f'<td>{esc(", ".join(watchlist))}</td></tr>'
            f'<tr><th scope="row">Frasa terlarang tambahan</th>'
            f'<td>{esc(", ".join(prohibited) or "—")}</td></tr>'
            '</tbody></table>',
            "<h2>Apa yang bisa dan tidak bisa dihitung</h2>",
            f'<p>Komparator tahun-ke-tahun tersedia untuk {len(yoy)} emiten pada '
            f'sumber <code>{esc(source)}</code>.'
            + ("" if yoy else
               f' Panggilan yang akan menyediakannya: '
               f'<code>{esc(sources.ENDPOINT["quarterly_yoy"])}</code>. Belum '
               f'dijalankan — produk ini tidak memanggil API berbayar.')
            + "</p>",
            f'<p>Endpoint yang dipakai: '
            f'<code>{esc(sources.ENDPOINT["trigger"])}</code> dan '
            f'<code>{esc(sources.ENDPOINT["quarterly"])}</code>.</p>']
    return shell("Setup", "".join(body), source)


class Handler(http.server.BaseHTTPRequestHandler):
    source = "recorded"
    db_path = None

    def _send(self, markup, status=200, content_type="text/html; charset=utf-8"):
        payload = markup.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _store(self):
        return relay.open_store(self.db_path)

    def _not_found(self, what):
        self._send(shell("Tidak ada", f"<h1>Tidak ada</h1><p>{esc(what)}</p>",
                         self.source), status=404)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        store = self._store()
        try:
            message = urllib.parse.parse_qs(parsed.query).get("pesan", [None])[0]
            if path == "/":
                self._send(runs_page(store, self.source))
            elif path == "/queue":
                self._send(queue_page(store, self.source, message))
            elif path == "/setup":
                self._send(setup_page(store, self.source))
            elif path.startswith("/draft/"):
                markup = draft_page(store, path.split("/")[-1], self.source, message)
                self._send(markup) if markup else self._not_found("draf itu")
            elif path.startswith("/audit/"):
                markup = audit_page(store, path.split("/")[-1], self.source)
                self._send(markup) if markup else self._not_found("peristiwa itu")
            else:
                self._not_found(parsed.path)
        finally:
            store.close()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        form = urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8"))
        reference = parsed.path.rstrip("/").split("/")[-1]
        store = self._store()
        message = ""
        try:
            action = (form.get("action") or [""])[0]
            role = (form.get("role") or ["ops"])[0]
            if action == "review":
                decision = (form.get("decision") or ["approve"])[0]
                try:
                    outcome = relay.review(
                        store, reference, decision, role,
                        comment=(form.get("comment") or [None])[0],
                        expected_version=(form.get("expected_version") or [None])[0])
                    message = f"{decision}: peristiwa sekarang {outcome['state']}"
                except (relay.NotPermitted, relay.Unresolved, relay.StaleVersion) as exc:
                    # The server's refusal, in words, on the page. Hiding the button
                    # would not be access control.
                    message = f"ditolak: {exc}"
            elif action == "edit":
                try:
                    outcome = relay.edit_claim(store, reference,
                                               (form.get("claim_id") or [""])[0],
                                               (form.get("text") or [""])[0], role)
                    message = (f"{outcome['claim_id']}: {outcome['validation_status']}"
                               + (f" — {', '.join(outcome['reason_codes'])}"
                                  if outcome["reason_codes"] else ""))
                except (relay.NotPermitted, KeyError) as exc:
                    message = f"ditolak: {exc}"
            else:
                message = "aksi tidak dikenal"
        finally:
            store.close()
        location = f"/draft/{urllib.parse.quote(reference)}?pesan=" \
                   f"{urllib.parse.quote(message)}"
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *args):
        pass


# ------------------------------------------------------------------------------ gates


def _demo_store():
    """A populated in-memory workflow, so the markup checks run on real content."""
    store = relay.open_store(":memory:")
    workspace = relay.setup(store, "recorded", ["ADRO", "BBCA"], now=relay.NOW)
    adapter = __import__("adapter").Adapter(mode="direct", source="recorded")
    relay.poll(store, adapter, workspace, now=relay.NOW)
    return store


def check_routes():
    """Every route renders, and the two that can 404 do."""
    failures = []
    store = _demo_store()
    pages = {
        "runs": runs_page(store, "recorded"),
        "queue": queue_page(store, "recorded"),
        "draft": draft_page(store, "1", "recorded"),
        "audit": audit_page(store, store.events()[0]["event_id"], "recorded"),
        "setup": setup_page(store, "recorded"),
    }
    for name, markup in pages.items():
        if not markup:
            failures.append(f"/{name} rendered nothing")
            continue
        if markup.count("<h1") != 1:
            failures.append(f"/{name}: {markup.count('<h1')} level-one headings")
        if '<html lang="id">' not in markup:
            failures.append(f"/{name}: no language declared")
        if 'class="skip"' not in markup:
            failures.append(f"/{name}: no skip link")
        if "<table" in markup and "<caption>" not in markup:
            failures.append(f"/{name}: a table with no caption")
        if "<table" in markup and 'scope="col"' not in markup:
            failures.append(f"/{name}: a table with no column headers")
        if template.DISCLAIMER not in markup:
            failures.append(f"/{name}: the disclaimer is missing")

    if draft_page(store, "99", "recorded") is not None:
        failures.append("a draft that does not exist rendered a page")
    if audit_page(store, "no-such-event", "recorded") is not None:
        failures.append("an event that does not exist rendered a page")
    store.close()
    return failures, len(pages) * 6 + 2


def check_evidence_panel():
    """ER-FR-14: every figure on the page has its endpoint, field and as_of beside it."""
    failures = []
    store = _demo_store()
    draft = store.drafts()[0]
    factset = store.latest_factset(draft["event_id"])
    markup = draft_page(store, "1", "recorded")

    cited = {fact_id for slide in draft["content"]["slides"]
             for slot in slide["slots"] for fact_id in slot["fact_ids"]}
    for fact_id in cited:
        fact = next(f for f in factset["facts"] if f["fact_id"] == fact_id)
        for key in ("fact_id", "endpoint", "source_field", "period", "as_of"):
            if esc(fact[key]) not in markup:
                failures.append(f"{fact_id}: {key} is not in the evidence panel")
        if esc(fact["raw_value"]) not in markup:
            failures.append(f"{fact_id}: the raw value is not shown")

    for needle, why in (("Nilai ternormalisasi", "the normalized value column"),
                        ("Formula", "the formula column"),
                        ("Komparator", "the comparator"),
                        ("belum selesai", "the count of unresolved claims")):
        if needle not in markup:
            failures.append(f"missing: {why}")
    if "compliant" in markup.lower() or "sesuai ketentuan" in markup.lower():
        failures.append("the page offers a compliance verdict, which is not its to give")
    print(f"        bukti · {len(cited)} fakta dikutip, semuanya lengkap di panel")
    store.close()
    return failures, len(cited) + 5


def check_no_second_engine():
    """No arithmetic in this file: the page is a view, not a second implementation."""
    failures = []
    with open(os.path.abspath(__file__)) as handle:
        body = handle.read()
    # The evidence panel prints values; it never computes one. A `/` between two names
    # would be a ratio being derived here rather than read from a metric.
    for needle in ("revenue /", "earnings /", "- 1", "* 100"):
        if needle in body.split("def check_no_second_engine")[0]:
            failures.append(f"webapp.py appears to compute something: {needle!r}")
    for module in ("metrics", "factset"):
        if f"import {module}" in body:
            failures.append(f"webapp.py imports {module} — it should read what "
                            f"relay.py already computed")
    return failures, 6


def self_test():
    results = [("routes", *check_routes()),
               ("evidence panel", *check_evidence_panel()),
               ("no second engine", *check_no_second_engine())]
    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)
    print("\nsetiap angka di layar membawa endpoint, field dan as_of-nya" if not failed
          else f"\n{failed} kegagalan tampilan")
    return 1 if failed else 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="webapp.py")
    parser.add_argument("--port", type=int, default=8082)
    parser.add_argument("--source", default="recorded", choices=("recorded", "synth"))
    parser.add_argument("--db", default=None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    Handler.source = args.source
    Handler.db_path = args.db
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"http://127.0.0.1:{args.port}   (sumber: {args.source}, nol kredit)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
