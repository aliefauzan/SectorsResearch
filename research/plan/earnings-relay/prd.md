<!-- Mirror of Google Doc `178O5IZHb5bZw-1WZ431E8z_elZ8JeHYk601i3ZBuWR4`, tab 1 (PRD — Engineering Handoff).
     Taken 2026-09-10. The doc can change; this copy is what the build answers to. -->

# EARNINGS RELAY

## Angka terverifikasi, konten siap ditinjau.

# Product Requirements Document — Engineering Handoff

Track 2 — Automation & Workflows  |  MVP 7–10 hari  |  Status: provisional finalist-worthy

Skor riset: 85/100 strict; potensi 93/100 jika validasi pengguna, coverage data, dan reliability demo lolos.

## 1\. Product definition

Earnings Relay adalah workflow otomatis untuk mengubah laporan keuangan baru menjadi satu paket konten yang siap ditinjau. Sistem mengunci fakta dan formula sebelum narasi dibuat, memeriksa setiap klaim terhadap evidence, lalu mengirim draft ke satu review queue. Produk tidak memublikasikan konten dan tidak memberi rekomendasi investasi.

  - Primary outcome: satu report event menghasilkan satu review pack yang traceable, atau satu status no-op/duplicate/failed yang dapat dijelaskan.
  - Target organisasi: sekuritas atau platform investasi Indonesia dengan watchlist konten earnings berulang.
  - Primary user: Content Operations Manager. Reviewer: Compliance Reviewer atau Content Lead. Admin: pemilik workspace dan aturan.
  - Core dependency: trigger dan fact set berasal dari Sectors; tanpa Sectors, detection, provenance, dan claim verification kehilangan fungsi inti.

## 2\. Problem dan why now

Tim content perlu bergerak cepat saat laporan baru tersedia, tetapi angka, periode pembanding, satuan, arah perubahan, dan wording klaim masih diperiksa manual. Generator konten generik mempercepat copywriting, namun dapat membuat angka tidak konsisten, membandingkan periode yang salah, atau menghasilkan klaim yang tidak memiliki bukti. Bottleneck yang diselesaikan bukan “menulis caption”, melainkan membuat draft finansial yang dapat diaudit sebelum masuk ke reviewer.

Current workaround biasanya berupa monitoring manual, spreadsheet per emiten, copy-paste angka, calculator, template desain, chat internal, dan review terpisah. Earnings Relay menyatukan urutan tersebut menjadi scheduled workflow dengan state, deduplication, evidence lock, dan human approval.

## 3\. Users, roles, dan permission

  - Admin — membuat workspace, mengelola schedule, watchlist, template, prohibited claims, reviewer, dan retention. Tidak dapat menandai klaim supported tanpa rule engine.
  - Content Ops Editor — melihat run, membuka draft, mengubah wording non-faktual, mengirim ke review, dan menanggapi rejection. Perubahan angka memicu validasi ulang.
  - Compliance Approver — membuka evidence per klaim, memberi komentar, approve, atau reject. Tidak mengubah source fact.
  - Read-only Stakeholder — melihat approved pack dan audit trail tanpa hak edit.
  - Service Account — membaca Sectors dan menjalankan job. Secret hanya tersimpan server-side.

## 4\. Jobs to be done dan user stories

JTBD: ketika laporan earnings baru tersedia untuk emiten dalam watchlist, tim ingin menerima satu draft yang seluruh angkanya sudah dinormalisasi dan dapat ditelusuri, sehingga waktu review dipakai untuk judgement dan konteks—bukan mencari ulang sumber.

  - Sebagai Admin, saya dapat mengatur 5–10 emiten, cadence, template lima slide, tone, prohibited claims, dan reviewer sebelum automation diaktifkan.
  - Sebagai Content Ops, saya menerima satu draft per report event dan tidak menerima draft ganda ketika scheduler mengulang fetch.
  - Sebagai Content Ops, saya dapat melihat tiga metrik, comparator, raw value, formula, endpoint, dan as\_of sebelum mengirim draft ke reviewer.
  - Sebagai Content Ops, saya dapat mengubah wording; bila angka atau periode diubah, claim kembali ke needs\_review.
  - Sebagai Compliance Reviewer, saya dapat membuka setiap klaim dan melihat fact\_id yang mendukung, lalu approve atau reject dengan alasan.
  - Sebagai Admin, saya dapat menjelaskan setiap run—termasuk no-op dan failure—tanpa membuka database.

## 5\. Goals dan non-goals

### Goals MVP

  - Mendeteksi laporan baru secara unattended untuk watchlist kecil.
  - Menghasilkan tepat tiga metrik deterministik dan satu immutable FactSet.
  - Membuat carousel lima slide dan caption Bahasa Indonesia yang hanya memakai fakta terkunci.
  - Memblokir klaim unsupported, menandai ambiguity sebagai needs\_review, dan menjaga exactly-once delivery ke review queue.
  - Menyediakan audit trail yang mudah dibaca dalam demo.

### Non-goals MVP

  - Auto-publish ke media sosial, rekomendasi buy/sell, target harga, atau personalized advice.
  - Menentukan bahwa konten telah memenuhi seluruh kewajiban compliance.
  - Menggantikan judgement editor atau approver.
  - Mendukung semua jenis filing, semua bahasa, atau seluruh emiten sekaligus.
  - Menjadikan LLM sebagai sumber angka, formula, trigger, atau status claim.

## 6\. Happy path end-to-end

  - 1\) Admin membuat workspace, watchlist, template, rules, reviewer, dan schedule.
  - 2\) Scheduler menjalankan poll incremental pada latest quarterly financial dates.
  - 3\) Event untuk symbol dalam watchlist dinormalisasi menjadi period\_key lalu di-hash.
  - 4\) Event baru mengambil quarterly financials; event lama menjadi duplicate/no-op.
  - 5\) Validation layer memeriksa required fields, freshness, unit, currency, dan comparator.
  - 6\) Metric engine menghitung tiga metrik; FactSet disimpan immutable bersama provenance.
  - 7\) Template engine membuat outline. Narrative engine opsional hanya mengisi slot yang merujuk fact\_id.
  - 8\) Claim Risk Gate memeriksa angka, periode, arah, prohibited phrase, dan citation.
  - 9\) Draft supported/needs\_review masuk ke Content Ops; klaim rejected diblokir.
  - 10\) Reviewer membuka evidence, approve atau reject. Approved pack disimpan; publishing dilakukan manual di luar MVP.

## 7\. Information architecture dan layar

  - Setup — workspace, watchlist, schedule, template, brand tone, prohibited claims, reviewer, dan test connection.
  - Runs — daftar run dengan started\_at, completed\_at, input\_as\_of, status, detected event, retry count, dan reason.
  - Review Queue — filter needs\_review/approved/rejected; satu card per report event, bukan per scheduler run.
  - Draft & Evidence — preview lima slide dan caption; panel kanan berisi claim status, fact\_id, raw value, formula, comparator, source, dan as\_of.
  - Audit — timeline state change, rule\_version, template\_version, prompt\_version, actor, comment, delivery status, dan event\_hash.
  - Empty/Error State — no event, incomplete data, source unavailable, retry scheduled, atau duplicate suppressed.

## 8\. Functional requirements

### P0 — wajib untuk demo dan MVP

  - ER-FR-01: Admin dapat menyimpan watchlist 5–10 symbol dan schedule harian.
  - ER-FR-02: Poller memakai cursor/since dan mencatat source\_as\_of; hasil di luar watchlist diabaikan.
  - ER-FR-03: Sistem membentuk event\_hash dari workspace, symbol, period\_key, report\_date, dan source version untuk deduplication.
  - ER-FR-04: Financial adapter memetakan source data ke canonical fields dan menyimpan raw payload reference.
  - ER-FR-05: Validator menolak required field null, comparator tidak sejenis, unit tidak dikenal, atau denominator nol.
  - ER-FR-06: Metric engine hanya menghitung Revenue YoY, Net Income YoY, dan Net Margin Delta.
  - ER-FR-07: FactSet immutable setelah fact\_locked; restatement membuat version baru, bukan overwrite diam-diam.
  - ER-FR-08: Draft selalu memiliki template\_version dan setiap factual slot memiliki fact\_id.
  - ER-FR-09: Claim Risk Gate menghasilkan supported, needs\_review, atau rejected dengan reason\_code.
  - ER-FR-10: Review queue mendukung edit wording, comment, submit, approve, dan reject.
  - ER-FR-11: Perubahan angka, periode, atau direction menginvalidasi claim dan menjalankan revalidation.
  - ER-FR-12: Delivery ke review queue idempotent; publishing tidak tersedia.
  - ER-FR-13: Run log memperlihatkan new, sent, duplicate, no-op, failed, retried, needs\_review, dan approved.
  - ER-FR-14: Evidence drawer memperlihatkan source field, raw value, normalized value, formula, period, comparator, endpoint, dan as\_of.

### P1 — setelah alur P0 stabil

  - ER-FR-15: Preview variasi tone tanpa membuat FactSet baru.
  - ER-FR-16: Template berbeda per sector dengan metric availability guard.
  - ER-FR-17: Export pack ke PNG/PDF atau webhook internal setelah approval.
  - ER-FR-18: Rule analytics untuk melihat reason\_code dan correction pattern paling sering.

## 9\. Business rules dan formula deterministik

  - Revenue YoY = (revenue\_t / revenue\_same\_period\_prior) − 1. Jika prior null atau nol, metric\_status = unknown dan tidak boleh dinarasikan sebagai persentase.
  - Net Income YoY memakai period yang sama. Jika nilai berubah tanda, tampilkan nilai absolut dan status sign\_change; jangan memaksakan growth percentage yang menyesatkan.
  - Net Margin Delta = (net\_income\_t / revenue\_t) − (net\_income\_prior / revenue\_prior), ditampilkan dalam percentage points. Denominator nol/null menghasilkan unknown.
  - Comparator default: quarter terhadap quarter fiskal yang sama tahun sebelumnya; FY terhadap FY. Sequential comparison hanya berjalan jika Admin mengaktifkannya secara eksplisit.
  - Rounding diterapkan pada display layer; evidence menyimpan precision sumber. Direction claim dihitung dari unrounded value.
  - Narasi hanya dapat memakai token yang disediakan template dan fact\_id. Claim tanpa fact\_id = rejected.
  - Prohibited claims mencakup ajakan transaksi, target harga, superlative tanpa basis, dan wording yang diset Admin.
  - Restatement atau perubahan source\_as\_of membuat FactSet version baru dan seluruh claim terdampak kembali needs\_review.

## 10\. Sectors data contract

  - Trigger: GET /v2/companies/quarterly-financial-dates/?since={cursor}. Simpan symbol, report date/period identifier, fetch time, source\_as\_of, page cursor, dan endpoint version.
  - Facts: GET /v2/financials/quarterly/{symbol}/?approx=true. Canonical minimum: date/period, revenue, earnings/net income, currency/unit jika tersedia, dan source metadata.
  - Field name final harus dikunci setelah schema/API sample audit. Adapter tidak boleh menyebarkan nama vendor langsung ke UI/domain logic.
  - Missing/null = unknown, bukan nol. Approximate atau inferred value harus membawa quality flag dan dapat diblokir oleh workspace policy.
  - Rate/credit control: poll incremental, filter watchlist setelah fetch, cache response per run, dan jangan refetch source yang sama selama TTL.
  - Freshness: tampilkan as\_of di evidence. Laporan dengan period sama tetapi source version baru diperlakukan sebagai restatement candidate.

## 11\. System architecture

  - Web App — Setup, Runs, Review Queue, Draft & Evidence, Audit.
  - API Service — authentication, RBAC, workspace config, draft/review commands, export.
  - Scheduler/Worker — recurring poll, retry, timeout, concurrency limit, dan dead-letter status.
  - Sectors Adapter — pagination, rate/credit guard, schema mapping, raw response reference, freshness.
  - Event Resolver — watchlist match, period\_key, event\_hash, new/duplicate/no-op decision.
  - Validation + Metric Engine — deterministic rules, comparator selection, metrics, FactSet lock.
  - Template/Narrative Engine — deterministic outline; optional LLM receives fact tokens only.
  - Claim Risk Gate — claim parsing, fact linkage, prohibited phrase, direction/period/number checks.
  - Persistence — relational store for workflow state; object storage optional untuk export/raw payload; append-only audit event.
  - Delivery Adapter — internal review queue only untuk MVP.

## 12\. State machine

ReportEvent happy path: discovered → fetching → validated → fact\_locked → drafted → needs\_review → approved. Rejection menghasilkan rejected lalu revised → needs\_review. Terminal operational states: no\_op, duplicate, failed. Retry hanya berlaku pada transient fetch/delivery failure; validation failure membutuhkan data baru atau tindakan manusia.

  - Transition harus atomic dan menyimpan from\_state, to\_state, actor/service, timestamp, reason\_code, dan correlation\_id.
  - approved tidak boleh dicapai bila ada claim rejected atau needs\_review.
  - Duplicate run menunjuk canonical event\_id; tidak membuat Draft atau Delivery baru.
  - Failed setelah retry maksimum tetap terlihat di Runs dan dapat di-replay Admin dengan idempotency key yang sama.

## 13\. Core data model

  - Workspace: id, name, timezone, schedule, reviewer\_id, prohibited\_claims, status.
  - WatchlistItem: workspace\_id, symbol, active, content\_template\_id.
  - ReportEvent: symbol, period\_key, report\_date, source\_as\_of, event\_hash, state.
  - Run: run\_id, trigger\_type, started\_at, completed\_at, cursor, status, attempt, error\_code.
  - FactSet: fact\_set\_id, event\_id, version, source\_hash, rule\_version, locked\_at.
  - Metric: metric\_id, fact\_set\_id, type, raw inputs, normalized value, display value, comparator, quality\_status.
  - Draft: draft\_id, event\_id, template\_version, prompt\_version, content, status.
  - Claim: claim\_id, draft\_id, text span, fact\_ids, validation\_status, reason\_codes.
  - ReviewDecision: draft\_id, reviewer\_id, decision, comment, decided\_at.
  - Delivery: destination, idempotency\_key, status, delivered\_at.

## 14\. Internal job dan API contracts

  - PollReportsJob input: workspace\_id, cursor, scheduled\_at, rule\_version. Output: run\_id, detected\_count, new\_count, duplicate\_count, next\_cursor.
  - BuildEvidenceJob input: event\_id dan source\_as\_of. Output: fact\_set\_id, metric statuses, validation warnings, source\_hash.
  - BuildDraftJob input: fact\_set\_id, template\_version, prompt\_version optional. Output: draft\_id dan claim\_count; tidak menerima arbitrary angka dari client.
  - ValidateClaimsJob input: draft\_id. Output per claim: status, fact\_ids, reason\_codes, checked\_at.
  - Review command: draft\_id, expected\_version, decision, comment, actor\_id. Optimistic concurrency mencegah reviewer menimpa revisi baru.
  - Run response selalu membawa run\_id, current\_state, retryable, user\_message, dan audit\_url.

## 15\. Reliability, error handling, security, dan audit

  - Retry transient 429/5xx/network maksimal tiga kali dengan exponential backoff + jitter. 4xx schema/auth tidak diulang tanpa perubahan.
  - Idempotency key wajib untuk event creation dan review delivery. Database unique constraint menjadi lapisan terakhir deduplication.
  - Partial failure tidak boleh mengirim draft. FactSet hanya dikunci setelah seluruh required validation selesai.
  - Secret API disimpan server-side; log tidak boleh memuat credential atau raw prompt sensitif.
  - RBAC divalidasi di server. Approval memerlukan role Compliance Approver; semua change memakai actor identity.
  - Audit append-only menyimpan source\_as\_of, rule/template/prompt version, evidence hash, edit history, reviewer, dan timestamps.
  - UI selalu menampilkan human-readable reason dan opsi berikutnya: retry, wait for data, edit wording, atau contact Admin.

## 16\. Non-functional requirements dan SLO

  - Run harian untuk 10 emiten selesai ≤5 menit pada kondisi source normal.
  - P95 Review Queue dan Draft & Evidence \<2 detik dengan cached records.
  - Exactly-once delivery secara efektif: event yang sama tidak menghasilkan lebih dari satu active draft.
  - Semua perhitungan reproducible: input, rule\_version, dan source snapshot yang sama menghasilkan FactSet yang sama.
  - Accessibility: keyboard navigation, label status tidak hanya bergantung pada warna, dan evidence dapat dibaca screen reader.
  - Observability: structured log, metrics per job, trace\_id/correlation\_id, failure alert untuk Admin.
  - Retention audit dapat dikonfigurasi; default MVP ditentukan bersama tim compliance sebelum pilot.

## 17\. Telemetry dan success metrics

  - Funnel: report\_detected → fact\_locked → draft\_created → submitted → approved.
  - Reliability: no-op rate, duplicate suppression rate, fetch error rate, retry recovery, median run duration.
  - Quality: blocked claim rate, needs\_review rate, factual correction rate, restatement rate, claim-without-fact count.
  - Workflow: median time report-to-draft, draft-to-decision, revision count, approval rate.
  - Pilot success: ≥90% angka pada accepted sample traceable tanpa manual source search; factual correction setelah gate \<30%; tidak ada duplicate draft pada demo.

## 18\. Acceptance tests

  - AT-01 New event: report baru dalam watchlist menghasilkan satu FactSet, satu Draft, dan satu review item.
  - AT-02 Duplicate: poll yang sama menghasilkan duplicate/no-op dan tidak menambah Draft.
  - AT-03 Null data: required financial field null menghasilkan failed/needs\_review; nilai tidak menjadi nol.
  - AT-04 Prior zero: growth percentage menjadi unknown dengan reason denominator\_zero.
  - AT-05 Restatement: source version baru membuat FactSet v2 dan claim lama kembali needs\_review.
  - AT-06 Unsupported claim: klaim tanpa fact\_id atau wording terlarang menjadi rejected dan tidak dapat di-submit.
  - AT-07 Edit angka: perubahan factual span menginvalidasi status supported.
  - AT-08 Reject/approve: reject kembali ke Content Ops; approve hanya berhasil jika semua claim resolved.
  - AT-09 Transient failure: dua retry tidak membuat draft ganda; recovery memakai canonical event.
  - AT-10 Demo proof: satu unattended alert, satu no-op, dan satu dedup/recovery dapat dipahami dari UI dan audit log.

## 19\. Implementation plan 7–10 hari

  - Hari 1 — freeze API sample, canonical schema, rules, state machine, event hash, dan demo tickers.
  - Hari 2 — workspace/watchlist config, database entities, Sectors adapter, pagination/cursor.
  - Hari 3 — scheduler, ReportEvent resolver, run log, idempotency, retry.
  - Hari 4 — validation, comparator, tiga metric functions, unit tests, FactSet lock.
  - Hari 5 — five-slide template, optional narrative slot, Claim Risk Gate.
  - Hari 6 — Review Queue, Draft & Evidence, approve/reject, edit revalidation.
  - Hari 7 — audit UI, demo fixtures untuk alert/no-op/dedup, end-to-end tests.
  - Hari 8 — accessibility, performance, failure states, credit/rate guard.
  - Hari 9 — video rehearsal, seed data, reliability hardening.
  - Hari 10 — buffer untuk API mismatch, QA, dan submission packaging.

## 20\. Future extensions

  - Webhook/Canva/social scheduler setelah approval; tetap tidak auto-publish secara default.
  - Additional deterministic metrics per sector dan multilingual templates.
  - Policy packs berbeda per organization, reviewer SLA, dan redline comparison.
  - Restatement monitoring dan batch content calendar.
  - Learning dari reviewer hanya untuk ranking/template; tidak mengubah facts atau approval rule otomatis.

## 21\. Open decisions dan dependencies

  - API key dan sample 10 filing untuk mengunci field mapping, credit budget, pagination, dan approx behavior.
  - Pilihan scheduler/runtime, review destination, authentication provider, dan export format.
  - Daftar prohibited claims yang disetujui reviewer pilot.
  - Apakah draft dibuat sepenuhnya template-based atau memakai LLM untuk narrative slots.
  - Interview minimal dua Content Ops dan dua reviewer; confidence user pain tetap medium sebelum ini selesai.
  - Kill criterion: jika workflow memberi manfaat sama tanpa Sectors, fact-to-claim linkage tidak dapat dibuktikan, atau correction rate diperkirakan \>30%, ide harus diturunkan.

## 22\. Engineering definition of done

  - Setup → unattended poll → FactSet → draft → claim validation → review → approval berjalan end-to-end.
  - Seluruh P0 dan AT-01 sampai AT-10 lulus; core metric logic memiliki unit tests untuk null, zero, sign change, rounding, dan period mismatch.
  - Setiap factual claim memiliki fact\_id, source, period, formula, as\_of, serta validation status.
  - Scheduler, state, retry, idempotency, deduplication, and audit dapat dibuktikan tanpa database access.
  - UI tidak menyediakan buy/sell advice atau auto-publish; reviewer manusia wajib.
  - README menjelaskan local setup, environment variables, architecture, data contract, demo script, dan limitations.
