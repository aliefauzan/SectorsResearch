# Agent Berita Saham Lengkap — Sectors Hackathon 2026

## Problem
Trader saham (pemula hingga profesional) tidak tahu berita mana berdampak ke saham mana, dan terlalu banyak info berita membuat keputusan sulit. Tanpa peringatan dini, sitasi sumber, dan pembelajaran dari koreksi user, trader rentan membeli saham gorengan dan kehilangan konteks kondisi pasar (volume, momentum, katalis, konsentrasi) serta kondisi eksternal (cuaca).

## Evidence
- **Asumsi — needs validation via user research**: belum ada kutipan pengguna konkret atau metrik observasi. Riset teknis sudah dilakukan sebagai dasar: meridian berita (iliane5/meridian) + trading self-learning (umarmuhdhor/meridian), 66 endpoint Sectors API terverifikasi, budget kredit ~735 (CLAUDE.md), GCP free tier tersedia (`docs/gcp-free-tier.md`), cuaca mempengaruhi saham (`weather_stock_impact.md`).

## Users
- **Primary**: trader saham IDX (pemula → profesional) yang membutuhkan peringatan berita + dampak saham + alasan + sitasi, serta pembelajaran dari koreksi.
- **Not for**: eksekusi trading otomatis (dilarang semua track hackathon), investor jangka panjang tanpa minat berita harian.

## Hypothesis
Kita percaya **agent berita saham lengkap (multi-agent: berita, 4 pilar, belajar, cuaca) dengan memori bersama dan 4 pilar screening** akan membantu trader saham membuat keputusan lebih baik. Kita akan tahu benar ketika **jumlah koreksi user yang diterima sebagai pembelajaran (feedback) bertambah** dan **akurasi dampak berita terhadap saham meningkat** (divalidasi melalui review manual / metrik internal agent).

## Success Metrics
| Metric | Target | How measured |
|---|---|---|
| Koreksi user diterima sebagai pembelajaran | ≥ 10 koreksi dalam 30 hari | Feedback table (`feedback_id`, `agreement` enum) |
| Akurasi dampak berita (manual review) | ≥ 70% | Perbandingan rekomendasi agent vs hasil pasar aktual |
| Endpoint Sectors API dipanggil tanpa 404 yang tidak perlu | 0 404 dibayar (hindari simbol belum diverifikasi) | Ledger `recorded/` + `capture.py` budget |

## Scope
**MVP** — agent lengkap:
1. Agent berita (scraping live + klaster + briefing) — RSS/BMKG/NOAA + LLM (Gemini/3rd party)
2. Agent 4 pilar (konsentrasi, volume, momentum, katalis) — endpoint Sectors (`broker-summary`, `daily`, `top-changes`, `corporate-actions`, dll)
3. Agent belajar (feedback user → RAG + prompt update → `lessons.json`, `signal-weights.json`) — memori bersama (`TLTR DB`, `state.json`)
4. Agent cuaca (polling BMKG/NOAA/GCP Weather → modul korelasi dampak saham) — `weather_stock_impact.md`
5. Notifikasi + sitasi sumber + deploy GCP (Cloud Run, Scheduler, Secret Manager, Cloud Build) + Vercel
6. Multi-agent memori bersama (Firestore/Cloud SQL schema seragam: semua agent membaca `state.json` sebelum bertindak)

**Out of scope**
- Eksekusi trading otomatis (dilarang hackathon)
- Aplikasi mobile native (hanya web/Vercel)
- Integrasi broker langsung untuk order (hanya analisis, bukan eksekusi)
- Trading agent Solana DLMM (hanya referensi arsitektur, bukan implementasi)
- Fine-tune model besar (hanya RAG + prompt engineering sebagai MVP)

## Delivery Milestones
| # | Milestone | Outcome | Status | Plan |
|---|---|---|---|---|
| 1 | Agent berita + scraping | Scraping berita live + klaster + briefing dasar | pending | — |
| 2 | 4 pilar endpoint | Endpoint Sectors lengkap + biaya kredit terkontrol | pending | — |
| 3 | Loop belajar | Feedback user disimpan + RAG + prompt update | pending | — |
| 4 | Integrasi cuaca | Modul korelasi cuaca → dampak saham | pending | — |
| 5 | Multi-agent memori | `state.json` + `TLTR DB` + `lessons.json` bersama di GCP | pending | — |
| 6 | Deploy GCP + Vercel | Cloud Run + Scheduler + Secret Manager + Vercel live | pending | — |

## Open Questions
- [x] Bagaimana memori bersama antar agent bekerja? — `state.json` (status saat ini), `lessons.json` (feedback), `TLTR DB` (ringkasan berita), `signal-weights.json` (bobot 4 pilar), `pool-memory.js` (konteks saham), semua di Firestore/Cloud SQL schema seragam.
- [ ] Bagaimana format `state.json` yang seragam untuk semua agent (berita, 4 pilar, belajar, cuaca) agar tidak konflik saat membaca/menulis?
- [ ] Bagaimana cara validasi akurasi dampak berita (manual review vs metrik internal) sebelum PRD diubah menjadi implementasi?

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| 404 dibayar (1 kredit) karena simbol belum diverifikasi | Tinggi | Kredit habis cepat | Verifikasi simbol dari tier sebelumnya sebelum panggil (`plan-katalis-life.json` referensi) |
| Multi-agent memori tidak konsisten (race condition saat menulis `state.json`) | Sedang | Konteks hilang, agent salah keputusan | Gunakan Firestore transactions atau Cloud SQL row-level lock saat update `state.json` |
| User tidak memberikan feedback (loop belajar tidak terisi) | Sedang | Model tidak belajar, akurasi stagnan | Notifikasi aktif (Cloud Scheduler) + reminder user untuk memberikan koreksi |
| GCP biaya melebihi free tier (Cloud Run + Vertex AI) | Rendah | Biaya operasional naik | Monitor budget harian (`SECTORS_BUDGET` = 250 default, tapi deploy bukan konsumsi kredit Sectors); gunakan polling (bukan streaming) untuk hemat |
| Cuaca ekstrem tidak terprediksi (BMKG/NOAA lag) | Rendah | Peringatan terlambat | Kombinasi prediksi 3-6 bulan (NOAA) + prakiraan lokal (BMKG) + alert ekstrem real-time |

---
*Status: DRAFT — requirements only. Implementation planning pending via /plan.*
