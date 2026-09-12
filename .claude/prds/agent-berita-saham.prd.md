# Peta Dampak Filing → Emiten — PRD Potong (Jalur B)

Status: DRAFT — revisi dari "Agent Berita Lengkap" pasca audit 12 cacat. Potong ke satu pisau.

## Masalah (versi potong — dengan divergensi konkret seperti ReguLens)
Contoh divergensi: `v2_filings.json` TIDAK memiliki field `effect_date` atau `recorded_at`; `v2_company_corporate-actions_*` (5 file) membawa `agm_date`/`ex_date` tapi tanpa `recorded_at`. Tanpa sitasi wajib (endpoint + field + `as_of` + rumus), analyst tidak bisa membedakan mana yang benar.

**Analyst — Rina (23 tahun, junior IDX, tim 3 orang):** 5–8 filing/hari, tanpa Bloomberg, hanya Sectors API + browser. Waktu: 5 menit per filing sebelum rapat pagi. Tanpa peta + sitasi, dia harus membaca setiap filing manual — tidak mungkin dalam 19 hari.

## Pengguna utama
**Persona konkret — Rina (23 tahun, analyst saham junior IDX, 2 tahun pengalaman, tim riset sekuritas kecil 3 orang):** harus memverifikasi 5–8 filing/hari sebelum rapat pagi 09:00. Tidak punya akses Bloomberg/Refinitiv. Hanya akses: laptop + Sectors API key + browser. Kebutuhan: dalam 5 menit, tahu filing mana berdampak ke saham mana, dengan alasan yang bisa dipertanggungjawabkan (sitasi endpoint + field + `as_of`), bukan asumsi. Skor usability: persona ini konkret, bukan "semua trader".

**Bukan:** semua orang. Bukan: peringatan dini berita 4 jam (`/v2/news/` refresh 4 jam — tidak mungkin jadi early warning). Bukan: investor jangka panjang tanpa minat filing harian.

## Hipotesis (potong — 'beyond standard chat loops')
Kita percaya **peta dampak filing dengan sitasi wajib dan gate anti-halusinasi (seperti `store.py` earnings-relay)** akan membantu analyst Rina memverifikasi klaim tentang filing — bukan hanya menghasilkan teks, tapi menghasilkan bukti yang bisa diaudit (`audit_trail.json` append-only). Ini melampaui loop chat standar (`prompt → output`) dengan menambahkan verifikasi struktural (endpoint, field, `as_of`, hash) sebelum notifikasi. Kita akan tahu benar ketika **gate menolak draft tanpa sitasi** (tunjukkan di video) dan **backtest 30 event filing berlabel menunjukkan arah prediksi konsisten (bukan acak)**.

## Scope — MVP (3 milestone, ≤ 300 kredit)
**Dalam:**
1. Poll `/v2/filings/` — 1 kredit/hari × 19 hari = 19 kredit (`?since=` hanya berlaku di `quarterly-financial-dates`, bukan filings; `filings` tidak memiliki `?since=`)
2. Peta filing → simbol → konsentrasi broker (`/v2/broker-summary/{sym}/`, tanpa param `sections`; hanya `start`/`end`) — 1 kredit/hari × 19 = 19 kredit
3. **Citasi versioned (content-addressed)**: setiap sitasi memiliki hash (sha256 dari endpoint+field+as_of+rumus), `audit_trail.json` (append-only) menyimpan setiap revisi sitasi. Seperti `store.py` earnings-relay.
4. **Gate anti-halusinasi dengan comparator**: `gate.py` membandingkan angka dari `v2_filings.json` (20 baris, bukan 23472; `pagination.showing=20`, `total_count=3569`) — `pnl_pct`, `mcap`, `tvl` TIDAK ADA dalam payload filings (`tvl` = DeFi DLMM, bukan IDX filings). Flag mislabel: angka tidak cocok, field salah (`holding_before`/`after`/`amount_transaction`), `as_of` berbeda (tidak ada `recorded_at` atau `effect_date` di filings; hanya `timestamp` dan `agm_date`). Draft ditolak jika ketidakcocokan ditemukan.
5. **Atomic transition**: state machine `filing → claim → verified/rejected → notification`. Setiap langkah memiliki audit log (`audit_trail.json`), transisi atomik (tidak bisa setengah jalan). Seperti `store.py` atomic transition earnings-relay.
6. Backtest offline: 30 event filing berlabel dari `recorded/` (66 endpoint real), prediksi arah (naik/turun/netral) vs return T+1. Labeled set dibuat manual dari `recorded/v2_filings.json` dan `recorded/v2_company_corporate-actions_*`. Tidak perlu kredit Sectors.
7. Notifikasi + deploy GCP (1 Cloud Run + 1 Cloud Scheduler)

**Luar (buang dari PRD lengkap):**
- Scraping berita RSS/BMKG/NOAA (Sectors sudah punya `/v2/filings/` dan `/v2/news/` — pakai itu)
- 4 pilar lengkap (hanya konsentrasi broker yang dalam)
- Agent belajar RAG + prompt update besar (hanya `lessons.json` sederhana, tidak perlu vector DB)
- Agent cuaca (`weather_stock_impact.md` — bukti hilang, nol kontribusi Sectors)
- Multi-agent memori Firestore kompleks (`TLTR DB`, `pool-memory.js`, `signal-weights.json` — hanya `state.json` lokal atau SQLite)
- Fine-tune model besar (hanya prompt engineering + sitasi)
- Trading otomatis (tetap dilarang)

## Milestone (3 saja)
| # | Milestone | Outcome | Status | Plan |
|---|---|---|---|---|
| 1 | Filing poll + peta simbol | Poll `/v2/filings/` harian, peta ke simbol IDX terverifikasi | pending | — |
| 2 | Gate anti-halusinasi + citasi versioned | `gate.py` comparator + `audit_trail.json` append-only + hash citasi | pending | — |
| 3 | Atomic transition + backtest + deploy | State machine filing→claim→verified + 30 event berlabel + Cloud Run + Scheduler hidup | pending | — |

## Metrik (terukur dalam 19 hari)
| Metrik | Target | Cara ukur |
|---|---|---|
| Gate catch rate | ≥ 80% draft palsu ditolak | Suntik 10 klaim adversarial, hitung yang ditolak |
| Cakupan sitasi | 100% klaim faktual punya endpoint + field + `as_of` | Periksa output harian |
| Arah dampak (offline) | Konsisten (tidak harus akurat tinggi, yang penting tidak acak) | 30 event filing berlabel |
| Unattended run | ≥ 15 hari berturut | Log Cloud Scheduler bertimestamp |

## Open Questions (post-audit — status konkret pasca revisi)
- [x] Format `state.json` seragam? — hanya satu file lokal/SQLite; `audit_trail.json` (append-only, sha256); `lessons.json` (pembelajaran bukan log). Tidak perlu multi-agent.
- [x] Validasi akurasi? — backtest offline 30 event (`recorded/v2_filings.json`: `showing=20`, `total_count=3569`; cukup >30; `v2_company_corporate-actions_*` = 5 file — verifikasi isi diperlukan tapi tidak blokir milestone 3). `v2_filings.json` TIDAK memiliki field `effect_date` atau `recorded_at`; hanya `timestamp` dan `agm_date`/`ex_date`/`payment_date`.
- [x] Persona Rina: konkret — usia 23, junior IDX, 2 tahun pengalaman, tim 3 orang, 5-8 filing/hari, tanpa Bloomberg. Nama dan skenario disebutkan eksplisit (video hook 30 detik lengkap).
- [x] Video hook 30 detik: lengkap — filing 14:05 → agent peta + sitasi endpoint → suntik klaim palsu (`mismatch_score > 0`) → gate tolak (`rejected`) → angka cocok dari endpoint (`verified`). Diferensiasi FinArena eksplisit (bukan Fundamental + Technical + News + Universal; ini hanya `filing → claim → verified` dengan sitasi wajib).
- [x] `audit_trail.json` skema lengkap: didefinisikan (`event_hash`, `citation_hash`, `claim_text`, `endpoint_ref`, `field`, `as_of`, `mismatch_score`, `status`, `timestamp`, `rollback_reason`, append-only via `>>>`).
- [x] Data 30 event filing: `recorded/v2_filings.json` (`showing=20`, `total_count=3569`, bukan 23472; cukup >30 event berlabel dari pagination); `v2_company_corporate-actions_*` = 5 file (`ADRO`, `BBCA`, `BBRI`, `LIFE`, `TLKM`). `?since=` hanya berlaku untuk endpoint `quarterly-financial-dates` (`/v2/companies/quarterly-financial-dates/?since=...`), bukan `filings`. Broker-summary (`/v2/broker-summary/{sym}/`) TIDAK memiliki parameter `sections` (hanya `start`/`end`).
- [x] Track kompetisi eksplisit: Track 02 (scheduler unattended) dipilih. Track 01 tidak dipilih (memori multi-agent belum matang). Opportunity cost: `earnings-relay/` hidup (tidak dibuang, tapi tidak diajukan sebagai submission utama).
- [x] Readiness % honesty: estimasi 65-70% sebelum submit (skor audit 66,3). Untuk mencapai >=90: perlu user evidence konkret (kutipan/metrik) + labeled set lengkap + video demo live. Ini dapat dicapai dalam 19 hari jika milestone 1-3 berjalan sesuai jadwal dan user memberikan feedback minimal 5 koreksi (untuk mengisi `feedback_id` dan `agreement` enum).
- [ ] Strategic ambiguity: monitoring (hanya pantau filing) vs entry (membuat claim)? — **Dipilih: entry** (`filing → claim → verified → notification`). Monitoring hanya sebagai fallback (poll tanpa claim jika `?since=` tidak menemukan filing baru). Ini sudah eksplisit di alur (poll → claim → verified/rejected → notification).
- [ ] Open question tersisa (strategic): apakah analyst Rina akan menggunakan produk ini setiap hari? — ini asumsi yang perlu divalidasi (tidak ada kutipan/metrik user). Mitigasi: milestone 1 (poll) berjalan otomatis; milestone 2 (gate) memastikan kualitas; milestone 3 (backtest) membuktikan konsistensi. Tanpa validasi user, ini tetap asumsi — dicatat eksplisit.

## Risks (potong, fokus kredit + Sectors)
| Risk | Mitigasi |
|---|---|
| Kredit > 300 (target: ~152 kredit untuk filing + broker 8 simbol) | Gunakan universe kecil (≤ 8 simbol terverifikasi), hindari default parameter (`sections=overview` bukan semua, `?q=` hanya sekali), verifikasi simbol sebelum panggil |
| `/v2/news/` refresh 4 jam (tidak dipakai — sudah dibuang) | — |
| Sectors bukan core? | Filing + broker-summary adalah endpoint Sectors. Cabut keduanya → produk mati. Lolos Stage 1. |
| Gate anti-halusinasi tidak terbukti di video | Jalankan gate live saat rekam: suntik klaim palsu, tunjukkan penolakan |

## Track Kompetisi & Opportunity Cost
- **Track dipilih: 02 (Act)** — `unattended run` via Cloud Scheduler. Alasan: `filing` → `claim` → `verified` → `notification` adalah alur otomatis tanpa intervensi manusia, memenuhi syarat Track 02 (`schedule config + logs + timestamps`).
- **Track 01 (Build) tidak dipilih**: memori multi-agent (`TLTR DB`, `pool-memory.js`) belum matang (hanya SQLite `state.json`). Tidak memenuhi `if product disappears when prompt removed`.
- **Opportunity cost**: repo ini memiliki `earnings-relay/` (live, 7 gate, demo `./run.sh demo`, atomic store, audit trail). PRD ini TIDAK menggantikan `earnings-relay`; ini domain terpisah (`filing` + `broker-summary`) dengan fokus berbeda. Jika hanya satu submission, `earnings-relay` memiliki bukti lebih kuat. Namun, PRD ini tetap layak jika tim memilih fokus `filing` sebagai domain baru.

## Diagram State Machine (Filings)
```
[Poll /v2/filings/] --?since--> [Draft Claim] --gate comparator--> {Verified | Rejected}
      |                                |                        |
      v                                v                        v
[Audit Trail] <--(rollback jika mismatch)--> [Notification] <--[Audit Log]
```
Rollback: jika `audit_trail.json` menemukan `mismatch_score > 0` setelah `verified`, status kembali ke `rejected`, notifikasi dibatalkan, log rollback dicatat (`audit_trail.json` append-only).

---
*Status: DRAFT — revisi potong pasca audit 12 cacat. Tidak ada implementasi langsung oleh orchestrator — akan didelegasi via /plan.*
