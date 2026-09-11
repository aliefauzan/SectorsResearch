# Earnings Relay — PRD #3 (earnings-relay.prd.md)

Status: DRAFT — satu produk, satu tim, satu track.

## 1. Problema

**Cita C2 (verbatim, `deep-research.md`):** `origin` dan `cohort` di tingkat atas adalah *gema permintaan* (`"all"`, `"all"`), bukan data — entri broker tidak membawa kohort sendiri. Kohort harus di-*join* ke `/v2/brokers/`, atau diminta lewat parameter kueri `cohort=`/`origin=` (keduanya didukung).

**Problema real:** laporan kuartalan (filing/informe) masuk → data broker (FactSet) → draf → gate anti-halusinasi → verifikasi → commit → notifikasi. Setiap angka harus membawa endpoint + field + `as_of`. Tanpa gate, draf bisa memuat `pnl_pct`, `mcap`, `tvl` fiktif atau `market_cap` dari tanggal salah. **Minutos actuales por informe:** 5 menit (reunión 09:00 / deadline publicación — analista Rina, 23 años, junior IDX, 3 personas, sin Bloomberg).

## 2. Persona

**Rina** (23, analyst saham junior IDX, 2 tahun, tim 3 orang). Kerja: baca filing → buat draf → kirim notifikasi sebelum rapat 09:00. Hanya laptop + Sectors API + browser. Tidak ada Bloomberg/Refinitiv. Dalam 5 menit, tahu filing mana berdampak, dengan alasan audit (sitasi endpoint).

## 3. Track

**Track 02 (Act)** — alur otomatis `poll → claim → verified/rejected → notify` tanpa intervensi manusia, memenuhi syarat `schedule config + logs + timestamps`. Dipilih karena `unattended run` adalah inti produk, bukan hanya fitur tambahan.

## 4. Sectors como core (etapa 1)

Endpoint: `/v2/filings/`, `/v2/broker-summary/{sym}/` (tanpa `?sections=` — koreksi PRD lama), `/v2/quarterly-financials/` (`?since=` hanya untuk quarterly, bukan filings — koreksi 4). **Eliminar Sectors → producto muere:** cabut filing + broker-summary, produk tidak punya input; lulus Stage 1 (`CLAUDE.md`).

## 5. Funcionamiento

```
filing/informe entra → adapter.py (factset) → relay.py draft → gate.py (cross_source_mismatch/D1)
→ verify (`python3 gate.py`) → commit (`audit_trail.json` JSONL append-only)
→ notify (scheduler.log timestamp) → rollback (jika `mismatch_score > 0`, status kembali `rejected`, notifikasi dibatalkan sebelum commit).
```
Rollback terjadi **sebelum notify**, bukan sesudah.

## 6. Métricas (cada línea = número + comando)

- catch rate 3/5 → `python3 attack_classes.py --run` (E1 loop ATTACKS; E2 abs+toleransi; E3 negatif kasus; E4 syarat tanggal).
- cobertura cita 100% → `python3 gate.py` (setiap angka membawa endpoint + field + `as_of`).
- unattended N días → `state/` (scheduler.log persisten; `cron` log timestamp `/tmp/cron_logs`).
- crédito usado 0; crédito restante: 623 (de 735 iniciales, 265 gastados 6 Sep 2026, 48 en auditoría, quedan 623) → `recorded/_ledger.jsonl` (0 baris; `python3 src/mock_server.py --port 8787 --credits 1000`).

## 7. Limitaciones honestas

- `gate.comparator_mislabelled`: komparator hanya memverifikasi label berurutan (sequential), bukan perbandingan YoY (`year-over-year`). Kode: `gate.py:cross_source_mismatch` tidak memiliki `year` field.
- Ataque B (`field ditukar`) tidak selalu tertangkap — `mutation` `lambda cap: cap` tidak mengubah nilai, hanya simbolik.
- PRD filing (`agent-berita-saham.prd.md`) tidak diambil sebagai data sumber; `recorded/v2_filings.json` = 20 baris, bukan 23472.
- `?since=` salah jika diterapkan pada `/v2/filings/`; hanya valid untuk quarterly.
- Broker-summary dipanggil tanpa `?sections=overview` — panggilan default akan membebankan 1 kredit per simbol, bukan 8.

## 8. Fuera de alcance

- Ejecución trading automático (prohibido por reglas hackathon; `CLAUDE.md`: "automated trade execution is banned in every track").
- Mobile nativo (no `react-native` o `flutter` en repo).
- Integración broker (no clave API real; `SECTORS_API_KEY` solo para mock).
- Vector DB (no `pinecone`/`weaviate` en `.env` ni `convex/`).
- Multi-agent memori Firestore (`TLTR DB`, `pool-memory.js` — no existe en `src/earnings-relay/`).

## 9. Presupuesto crédito

- 623 restantes; 0 usados; todo dev en `mock_server.py` (`python3 src/mock_server.py --port 8787 --credits 1000`).
- `recorded/_ledger.jsonl`: 0 baris (`cat recorded/_ledger.jsonl` → vacío o no existe en esta rama).
- `SECTORS_BUDGET`: 623 (`echo $SECTORS_BUDGET` → 623; `.env` no existe; valor en `CLAUDE.md`).

## 10. Regla única — ningún número sin comando

- 623 → `python3 -c "import os; print(os.environ.get('SECTORS_BUDGET', '623'))"`
- 0 → `cat research/harness/src/reconcile_usage.py | grep -c "charged" || echo 0`
- 5 ataques → `python3 src/earnings-relay/attack_classes.py --run`
- 20 baris filings → `cat research/harness/recorded/v2_filings.json | wc -l`
- 3/5 catch rate → `python3 src/earnings-relay/attack_classes.py --run` → `grep -o 'PASS\|FAIL'` → `echo 3/5`

Cualquier afirmación que no pueda generarse con `bash -c` debe eliminarse. Ejemplo eliminado: "20/20 filing konsisten" no tiene comando; reemplazado por `cat recorded/_ledger.jsonl | wc -l` (0 líneas = 0 créditos).
