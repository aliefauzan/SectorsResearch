# Earnings Relay — PRD Submission

Sectors Hackathon 2026 · Track 02 (Automation & Workflows) · satu tim, satu proyek.

**Aturan dokumen:** tidak ada angka tanpa perintah yang memproduksinya. Yang belum diukur
ditulis `BELUM DIUKUR`, bukan ditebak.

## Masalah

Tiap laporan kuartalan terbit, seseorang harus menerbitkan ringkasan yang dibaca publik.
Angkanya datang dari beberapa endpoint yang tidak selalu sepakat: `market_cap` dari harga
harian berbeda dari `market_cap` di company report bila tanggalnya tidak dikunci; komparator
kuartal gampang tertukar antara sekuensial dan year-over-year. Satu angka meleset, yang
terbit adalah pernyataan keuangan yang salah, dan tidak ada yang tahu angka itu asalnya dari
mana.

Produk ini menolak menerbitkan kalimat yang tidak bisa ditelusuri ke `endpoint + field +
as_of`, dan membuktikan penolakannya lewat uji serangan yang dijalankan tiap siklus.

**BELUM DIUKUR:** kutipan verbatim dari 3–5 wawancara dengan orang yang benar-benar
menerbitkan ringkasan kuartalan (tim IR emiten, analis sekuritas kecil, compliance), plus
berapa menit proses manual mereka sekarang per laporan. Sampai ada, persona bernama adalah
asumsi dan tidak ditulis di sini.

## Sectors sebagai core data source

| Endpoint | Dipakai untuk |
|---|---|
| `/v2/companies/quarterly-financial-dates/` | pemicu kuartal baru (`?since=` valid hanya di sini) |
| `/v2/financials/quarterly/{symbol}/` | angka kuartalan yang dinarasikan |
| `/v2/daily/{symbol}/` | `market_cap`, `close` — sumber pembanding |
| `/v2/company/report/{symbol}/?sections=overview` | `market_cap` sumber kedua |

Cabut Sectors: tidak ada laporan yang masuk, tidak ada fakta yang bisa disitir, tidak ada
draft yang bisa dibuat. Produk mati, bukan berkurang.

## Cara kerja

```
kuartal baru terbit
  → sources.py    muat payload (recorded/ atau mock, nol kredit)
  → factset.py    fakta imutabel, id content-addressed, restatement = versi 2
  → template.py   5 slide Indonesia, tiap slot faktual menyebut fact_id
  → gate.py       5 blok check, termasuk cross_source_mismatch
  → verify → commit (audit trail append-only) → notify
```

Rollback hanya sah **sebelum** notify. Notifikasi terkirim tidak bisa ditarik, jadi urutannya
invarian.

`cross_source_mismatch` memeriksa tiga hal:

1. `market_cap` antar endpoint, **hanya bila tanggal kedua sumber sama**.
2. Invarian aritmetika payload: `abs(holding_after − holding_before) == amount_transaction`,
   dan `price × amount ≈ transaction_value` dengan toleransi eksplisit karena sumber
   membulatkan rupiah.
3. Aksi korporasi: `not_implemented` — ditulis apa adanya, tidak diklaim `verified`.

## Metrik

Semua dari root repo, nol kredit.

| Metrik | Angka | Perintah |
|---|---|---|
| Blok gate lolos | 5 | `cd src/earnings-relay && python3 gate.py \| grep -cE '^PASS'` |
| Catch rate serangan | 1/5 | `cd src/earnings-relay && python3 attack_classes.py --run \| tail -2` |
| False positive data asli | 0 dari 20 | blok python di bawah, harus cetak `False` lalu `True` |
| Run unattended tercatat | `wc -l state/scheduler.jsonl` | riwayat dimulai 12 Sep 2026 |
| Kredit dipakai proyek ini | 0 | tidak ada entri baru di `research/harness/recorded/_ledger.jsonl` (175 baris, semua capture 6 Sep 2026) |
| Sisa kredit hibah | 623 dari 1000 | `grep -c "623 remain" CLAUDE.md` |

```bash
python3 - <<'EOF'
import json, sys; sys.path.insert(0, 'src/earnings-relay'); import gate
rows = json.load(open('research/harness/recorded/v2_filings.json'))['results']
print(gate.cross_source_mismatch({"as_of": "x"}, {"v2_filings": rows})[0])          # False
f = dict(rows[0]); f["holding_after"] = f["holding_before"] + 2_000_000
print(gate.cross_source_mismatch({"as_of": "x"}, {"v2_filings": [f]})[0])           # True
EOF
```

Catch rate 1/5 adalah hasil ukur, turun dari angka 2/5 yang sebelumnya diketik tangan. Target
sebelum submit: 3/5 lewat dua perbaikan di daftar berikutnya.

## Batasan yang diakui

- Komparator: `gate.comparator_mislabelled` menolak kalimat yang menyebut perbandingan
  sekuensial sebagai year-over-year. Pada `recorded/` tidak ada pasangan kuartal tahun
  sebelumnya, jadi demo berjalan pada komparator sekuensial dan dilabeli begitu.
- Serangan B (field ditukar, nilai sama) belum tertangkap: butuh tabel satuan per field.
- Serangan C (`as_of` basi) belum tertangkap: tanggal berbeda saat ini dilewati dan dilaporkan
  `consistent`; seharusnya `needs_review`.
- Serangan E (sitasi hilang) ditangani gate sitasi lain, bukan `cross_source_mismatch`.
- Aksi korporasi belum dibandingkan.
- Riwayat unattended baru dimulai 12 Sep 2026. Riwayat lama yang dibuat serentak dengan
  tanggal mundur sudah dihapus.
- Bukti pengguna belum ada.

## Sisa pekerjaan

| # | Item | Efek |
|---|---|---|
| 1 | Bandingkan `symbol` antar sumber; tolak bila himpunan > 1 | 1/5 → 2/5 |
| 2 | Tanggal sumber berbeda → `needs_review`, bukan `consistent` | 2/5 → 3/5 |
| 3 | Fixture positif `check_cross_source` pakai 20 baris asli | mengunci regresi tanda + float |
| 4 | Scheduler jalan tiap hari sampai submit | riwayat unattended bertambah sendiri |
| 5 | Wawancara pengguna | satu-satunya lever untuk bobot 40% |

## Di luar ruang lingkup

Eksekusi trading otomatis (dilarang semua track) · aplikasi mobile native · integrasi broker
untuk order · vector DB / fine-tune · memori multi-agent terdistribusi.

## Anggaran kredit

Hibah 1000, terpakai 377 pada capture 6 Sep 2026, sisa 623. Proyek ini menambah 0 — seluruh
pengembangan berjalan pada `research/harness/recorded/` dan `mock_server.py`.

```bash
cd research/harness && python3 src/mock_server.py --port 8787 --credits 1000
```

Bila satu live capture diperlukan untuk video, jalankan lewat `capture.py --budget`, bukan
`curl`, supaya tercatat di `_ledger.jsonl` beserta biayanya.
