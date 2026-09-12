# Fase 5 · Persiapan tanpa kredit

Catatan kerja untuk tugas 1–4 `plan/phases/phase-5-labeled-corpus.md`, dikerjakan di worktree
`/Users/af/.ao/data/worktrees/sectors/sectors-7` pada cabang `fase5-prep`, 2026-09-12.

Tugas 5 fase itu — panggilan live 42 kredit — **tidak dijalankan**. Ia menunggu B3, yang
pemiliknya manusia. Berkas fase, `plan/PROGRESS.md`, dan seluruh `src/katalis/` tidak disentuh.
Tidak ada deploy Cloud Run dan tidak ada `gcloud builds submit`. `SECTORS_BASE_URL` menunjuk
mock di kedua kali rehearsal berjalan.

---

## Tugas 1 · Rekonsiliasi ledger terhadap portal

Perintah yang dijalankan apa adanya terhadap CSV yang sudah ada:

```bash
cd research/harness && python3 src/reconcile_usage.py
```

Keluaran, apa adanya:

```
portal rows: 408   portal total: 377
ledger total (capture only): 272
difference (traffic outside capture.py): 105
...
7 endpoint(s) where the model and the bill disagree:
| endpoint | ledger says | portal charged |
| --- | --- | --- |
| `/v2/broker-summary/LIFE/` | 1 | 0 |
| `/v2/company/corporate-actions/LIFE/` | 1 | 0 |
| `/v2/company/report/LIFE/` | 1 | 0 |
| `/v2/daily/LIFE/` | 1 | 0 |
| `/v2/filings/` | 2 | 1 |
| `/v2/index-daily/ihsg/` | 2 | 1 |
| `/v2/news/` | 2 | 1 |
| status | requests | credits |
| 200 | 303 | 368 |
| 400 | 95 | 0 |
| 404 | 9 | 9 |
| 405 | 1 | 0 |
```

**`exit=1`, bukan 0.** Tujuh selisih itu bukan regresi model biaya: ketujuhnya adalah tujuh
panggilan LIFE tanggal 2026-09-11, sesudah tanggal ekspor portal. Dibuktikan dari ledger:

```bash
# 7 baris ledger dengan ts > 2026-09-05, semuanya 2026-09-11T13:52, semuanya status 200
daily/LIFE · index-daily/ihsg · broker-summary/LIFE · company/report/LIFE · news · filings
· company/corporate-actions/LIFE
```

Ledger punya barisnya; ekspor tidak, karena ekspor berhenti di 2026-09-05. Karena itu
`reconcile_usage.py` keluar 1 sampai ekspor baru diambil.

Angka yang berlaku hari ini, apa adanya:

| | |
| --- | --- |
| Portal, tertagih sampai ekspor 2026-09-05 | **377** |
| Belanja di ledger sesudah tanggal ekspor | **+7** (tujuh panggilan LIFE, 2026-09-11) |
| Belanja nyata yang paling mungkin | **≈384 dari 1.000** |
| Sisa | **≈616** |

### Keputusan yang diambil di sini

Tidak ada angka kredit yang dikarang. Sisa ≈616 jauh di atas 42 + cadangan yang wajar, jadi
**korpus tetap enam simbol dan anggaran tetap 42**. Tidak ada pengecilan lingkup.

### Yang tetap hanya bisa dilakukan manusia

**Mengambil ekspor portal baru.** Ekspor terakhir bertanggal 2026-09-05 dan tidak ada alat
yang bisa menariknya dari repo ini — itu langkah konsol. Ekspor itu yang akan menutup B3 dan
membuat kriteria keluar 1 Fase 5 (reconcile exit 0) benar-benar terpenuhi. Sampai itu diambil,
temuan di atas adalah keadaan yang jujur, bukan kegagalan.

---

## Tugas 2 · Enam simbol, dan satu hold-out

Sumber kandidat: `research/harness/recorded/v2_suspensions.json` — 20 baris, 17 simbol unik.
LIFE tidak diulang (sudah dibeli 2026-09-11). Enam dipilih dari enam belas sisanya.

### Panjang deret harian — apa adanya

**Tidak ada deret harian di disk untuk satu pun kandidat.** Yang ada hanya LIFE
(`v2_daily_LIFE__end-2026-09-10_start-2026-05-01.json`, 62 baris). `v2_close__limit-30.json`
bukan deret — ia satu baris per simbol. `synth/market/daily/` memuat 120 simbol dan tidak satu
pun kandidat ada di sana. Jadi kolom "deret harian di disk" di bawah **0 baris untuk semuanya**,
dan itu fakta, bukan angka yang hilang.

Panjang yang **diharapkan** sesudah dibeli berasal dari preseden LIFE: jendela
`2026-05-01..2026-09-10` (permintaan 133 hari kalender) kembali 62 baris bursa karena endpoint
memotongnya ke 90 hari kalender. 62 > 45, jadi baseline terpenuhi — dengan catatan penting:
62 adalah sifat *endpoint*, bukan jaminan per simbol. Simbol yang dihentikan lebih awal bisa
kembali lebih pendek, dan itu tugas 7 fase (verifikasi tiap simbol menerbitkan kartu).

### Tabel pilihan

Baris = nomor baris `"symbol"` di `research/harness/recorded/v2_suspensions.json`.

| # | Simbol | Baris | Tanggal suspensi | Alasan suspensi | Free float | Nama perusahaan (di disk) | Sektor (dari nama) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **PACK.JK** | 46, dan 64 | 2026-09-01 (dan 2026-08-27) | peningkatan harga kumulatif, cooling down | 0,3819 | PT Abadi Nusantara Hijau Investama Tbk | kemasan / industri |
| 2 | **TRUK.JK** | 22, dan 118 | 2026-09-04 (dan 2026-08-11) | peningkatan harga kumulatif, cooling down | 0,2983 | PT Guna Timur Raya Tbk | logistik / transportasi |
| 3 | **EKAD.JK** | 58 | 2026-08-27 | peningkatan harga kumulatif, cooling down | 0,1774 | Ekadharma International Tbk | kesehatan / alat medis |
| 4 | **TMPO.JK** | 70 | 2026-08-27 | peningkatan harga kumulatif, cooling down | 0,2503 | Tempo Inti Media Tbk | media / penerbitan |
| 5 | **AGAR.JK** | 76 | 2026-08-19 | peningkatan harga kumulatif, cooling down | 0,2501 | PT Asia Sejahtera Mina Tbk | perikanan / akuakultur |
| 6 | **NICK.JK** | 16 | 2026-09-04 | peningkatan harga kumulatif, cooling down | 0,2162 | PT Charnic Capital Tbk | investasi / keuangan |

Free float dari `recorded/v2_free-float.json`; nama perusahaan dari berkas yang sama. Keenamnya
ada di tabel itu, jadi tidak ada satu pun yang perlu dibeli hanya untuk tahu namanya.

### Kenapa enam ini

- **PACK dan TRUK punya dua peristiwa berlabel masing-masing**, bukan satu. Korpus Fase 6 lebih
  kaya dari simbol yang sama, dan pagar "≥3 peristiwa mendukung" lebih mungkin dipenuhi.
- **Sektornya terpisah**: kemasan, logistik, kesehatan, media, perikanan, keuangan. Ini penting
  karena kriteria Fase 5 menolak enam simbol dari satu sektor.
  *Catatan kejujuran:* tidak ada field sektor di disk untuk keenamnya — `/v2/companies/` hanya
  mengembalikan `symbol` dan `company_name`. Penggolongan di atas karena itu bertumpu pada nama
  perusahaan yang memang tercatat, bukan pada field yang tidak ada. Kalau label sektor yang
  dapat diverifikasi mesin dibutuhkan, itu satu panggilan `/v2/company/report/<sym>/` tambahan
  per simbol, atau satu `/v2/subsectors/` pasar-lebar — keduanya **tidak** dimasukkan ke rencana
  ini.
- **Tidak satu pun sudah disentuh kode.** `CLASSIFIER` hidup di lima berkas `src/katalis/` dan
  nol di antaranya menyebut keenam ticker ini.

### Yang ditolak, dan kenapa

- **Polu/SMMT/JARR dan float tipis lain**: tidak ada di `v2_suspensions.json`, jadi tidak
  berlabel. Label lebih berharga daripada float tipis — itu alasan yang sudah tertulis di berkas
  fase, dan dipegang di sini.
- **COAL.JK dan INCF.JK**: alasannya bukan peningkatan harga melainkan ketidakpastian
  kelangsungan usaha. Labelnya jenis lain; dua dari enam cukup untuk keragaman label, enam
  terlalu banyak, dan simbol berhenti usaha lebih mungkin ditolak `baseline_tipis` setelah
  dibeli.
- **MDIA.JK, BEEF.JK, DOOH.JK, YPAS.JK, CSMI.JK, ASLI.JK, PPGL.JK, SAFE.JK**: kalah bersaing
  dalam sektor, atau tidak memberi apa pun yang PACK/TRUK/EKAD/TMPO/AGAR/NICK belum berikan.
  PPGL dan SAFE satu sektor dengan TRUK; MDIA satu sektor dengan TMPO; YPAS satu sektor dengan
  PACK.

### Hold-out Fase 6

**NICK.JK.** Alasan:

- Ia satu-satunya kandidat hold-out yang **belum pernah disentuh kode** dan tidak satu sektor
  dengan simbol lain di korpus.
- Ia punya **satu** peristiwa, bukan dua, jadi ia yang paling sedikit "menarik" di korpus —
  syarat yang berkas fase minta untuk hold-out.
- Bukan LIFE: LIFE sudah dipakai membangun pilar, jadi memakainya sebagai hold-out adalah
  menipu diri sendiri.
- Ia tetap **dibeli** (kartunya harus bisa terbit dan diukur), tetapi tidak boleh dipakai
  menghasilkan lesson di Fase 6.

Ia dinyatakan sebagai field `hold_out` di dalam berkas rencana, supaya pilihan itu bisa
diperiksa mesin, bukan hanya dibaca manusia.

---

## Tugas 3 · Rencana tangkapan

Ditulis ke `research/harness/plans/plan-katalis-corpus.json` — **36 entri, 36 kredit**.

```bash
cd research/harness && python3 src/capture.py --plan plans/plan-katalis-corpus.json --dry-run
# to fetch: 36 calls, estimated 36 credits
```

Enam panggilan per simbol, semuanya dibaca `pillars.bag_from()` lewat `sources.py`:

| Path | Parameter yang dibatasi | Kredit |
| --- | --- | --- |
| `/v2/daily/<SYM>/` | `start=2026-05-01`, `end=2026-09-10` | 1 |
| `/v2/broker-summary/<SYM>/` | `start`/`end` per simbol, rentang 14 hari kalender | 1 |
| `/v2/company/report/<SYM>/` | `sections=financials` | 1 |
| `/v2/news/` | `symbols=<SYM>.JK`, `start`/`end` per simbol | 1 |
| `/v2/filings/` | `symbol=<SYM>.JK`, `start`/`end` per simbol | 1 |
| `/v2/company/corporate-actions/<SYM>/` | tanpa parameter — endpoint tidak menerimanya | 1 |

Jendela broker per simbol (14 hari kalender, batas sisi-klien yang LIFE pakai):

| Simbol | broker `start`..`end` | news/filings `start`..`end` |
| --- | --- | --- |
| PACK | 2026-08-19 .. 2026-09-02 | 2026-08-02 .. 2026-09-07 |
| TRUK | 2026-08-22 .. 2026-09-05 | 2026-08-05 .. 2026-09-10 |
| EKAD | 2026-08-14 .. 2026-08-28 | 2026-07-28 .. 2026-09-02 |
| TMPO | 2026-08-14 .. 2026-08-28 | 2026-07-28 .. 2026-09-02 |
| AGAR | 2026-08-06 .. 2026-08-20 | 2026-07-20 .. 2026-08-25 |
| NICK | 2026-08-22 .. 2026-09-05 | 2026-08-05 .. 2026-09-10 |

### Aturan anggaran yang dijaga

- **`sections`, `classifications`, `periods`, `n_quarters` tidak pernah default.**
  `classifications`, `periods`, dan `n_quarters` tidak muncul sama sekali karena tidak ada
  endpoint di rencana ini yang menerimanya. `sections` selalu eksplisit
  (`sections=financials`, 1 kredit; tanpa itu 8).
- **Satu simbol per entri.** Tidak ada entri multi-simbol, termasuk `/v2/news/`: tiap entri
  membawa tepat satu `symbols=` / `symbol=`.
- **Tidak ada identifier yang tidak datang dari respons yang sudah ada di disk.** Keenam ticker
  datang dari `recorded/v2_suspensions.json`. Tidak ada broker code, slug, atau simbol SGX/KLSE
  yang ditebak di rencana ini.
- **Screener bahasa alami tidak dijalankan sama sekali** — nol kredit.
- **Yang sengaja tidak dibeli karena sudah di disk:**
  - `/v2/index-daily/ihsg/` — jendela yang sama sudah ada sebagai
    `v2_index-daily_ihsg__end-2026-09-10_start-2026-05-01.json`. Karena itu tidak ada entri
    tanpa simbol di rencana ini.
  - `/v2/free-float/` (961 baris, memuat keenam simbol), `/v2/brokers/` (registry, join nol
    kredit untuk origin/cohort), `/v2/suspensions/` (20 baris, keenam simbol ada).
  - `/v2/broker-summary/<sym>/top/` — `sources.broker_top` ada tapi tidak dibaca
    `pillars.bag_from()`, jadi 2 kredit per simbol akan terbuang.
  - `/v2/foreign-flow/` — split asing diturunkan dari join `brokers.is_foreign` × broker flow,
    nol kredit tambahan.
- **36 < 42.** Selisih 6 sengaja ditinggalkan: `--budget` harus di bawah sisa nyata, bukan sama
  dengan.

### Satu temuan yang harus dibaca sebelum belanja live

Perintah persis yang tertulis di berkas fase,

```bash
SECTORS_BASE_URL=http://127.0.0.1:8787 python3 src/capture.py --plan plans/plan-katalis-corpus.json --budget 42
```

**tidak bisa jalan.** `capture.py` menghitung `--budget` sebagai **plafon seumur hidup**
terhadap ledger, bukan plafon untuk rencana ini: ia memulai `running = already` (=272, total
ledger yang sudah dibelanjakan) lalu menolak panggilan yang akan melewati `--budget`. Dengan 272
sudah terpakai dan `--budget 42`, panggilan pertama langsung berhenti:

```
STOP: next call would exceed budget (272 + 1 > 42). Raise --budget to continue.
done. estimated spend this session: 0. cumulative: 272.
```

Untuk belanja live, `--budget` harus sekurangnya `272 + 36 = 308`. Angka yang disarankan:
**`--budget 310`** — cukup untuk seluruh 36 panggilan, memotong rencana ini di ≤38 kredit
(4 kredit di bawah alokasi 42), dan tetap jauh di bawah plafon 1.000. Catatan: ledger
mengunder-estimasi belanja nyata sekitar 105 kredit (trafik di luar `capture.py`), jadi total
nyata sesudah belanja live adalah ≈384 + 36 = **≈420 dari 1.000**.

---

## Tugas 4 · Rehearsal terhadap mock, dan biayanya

Mock dijalankan dengan label sesi di log, dan kedua kali rehearsal menunjuk ke sana lewat
`SECTORS_BASE_URL`. Worktree ini tidak punya `.env` (git-ignored, hanya ada di repo utama), jadi
`SECTORS_API_KEY` diisi nilai sekali-pakai `dev-key` — nilainya tidak pernah meninggalkan
loopback, dan tidak pernah dicetak.

```bash
cd research/harness && python3 src/mock_server.py --port 8787 --credits 1000
```

### Rehearsal A — perintah apa adanya dari berkas fase

```bash
SECTORS_API_KEY=dev-key SECTORS_BASE_URL=http://127.0.0.1:8787 \
  python3 src/capture.py --plan plans/plan-katalis-corpus.json --budget 42
```

Hasil: **0 panggilan, 0 kredit**, `STOP` pada panggilan pertama (lihat temuan di atas),
`exit=0`. Mock mencatat `calls: 0, credits_spent: 0`.

### Rehearsal B — `--budget` yang benar-benar mengizinkan rencananya

```bash
SECTORS_API_KEY=dev-key SECTORS_BASE_URL=http://127.0.0.1:8787 \
  python3 src/capture.py --plan plans/plan-katalis-corpus.json --budget 308
```

Hasil:

```
done. estimated spend this session: 36. cumulative: 308.
exit=0
```

- **36 panggilan, semuanya `200`.** Nol `402`, nol `400`, nol `404`.
- **Mock menagih 36 kredit** (meterannya sendiri), sisa mock 964 dari 1.000:

  ```json
  {"calls": 36, "credits_spent": 36, "credits_remaining": 964,
   "by_endpoint": {"/v2/daily/{symbol}/": 6, "/v2/broker-summary/{symbol}/": 6,
                   "/v2/company/report/{symbol}/": 6, "/v2/news/": 6,
                   "/v2/filings/": 6, "/v2/company/corporate-actions/{symbol}/": 6}}
  ```

- **Ledger tumbuh persis 36 baris, semuanya `billed_cost: 1`, semuanya status 200** (272 → 308).
  Di endpoint-endpoint rencana ini model biaya `capture.py` dan meteran mock **sepakat** — beda
  176-vs-167 yang diketahui pada rehearsal plan penuh berasal dari `/v2/free-float/`, yang tidak
  ada di rencana ini.

### Biaya rehearsal versus anggaran 42

| | Kredit |
| --- | --- |
| Dianggarkan berkas fase | **42** |
| Perkiraan rencana (36 entri) | **36** |
| Ditagih mock pada rehearsal | **36** |
| Selisih terhadap 42 | **−6** |

Selisih 6 bukan penghematan yang diklaim: enam kredit itu memang tidak pernah direncanakan
belanja — `/v2/index-daily/ihsg/` dan tiga tabel pasar-lebar tidak dibeli karena sudah di disk.
**Rehearsal ini tidak membelanjakan kredit Sectors sepeser pun.** Mock hanya memakai kreditnya
sendiri; nol panggilan menyentuh `api.sectors.app`.

### Apa yang rehearsal ini **tidak** buktikan

Mock melayani simbol yang belum terekam dari `fixtures/` — contoh milik spec, bukan data AGAR
yang nyata. Karena itu `v2_daily_AGAR...` hasil rehearsal hanya 153 byte, bukan 62 baris. Yang
dibuktikan rehearsal adalah **plumbing-nya**: slug berkas, bentuk parameter, idempotensi,
pencocokan path di `sources.py`, dan biayanya. **Bukan** panjang deret harian, dan bukan bahwa
tiap simbol akan menghasilkan kartu. Keduanya baru diketahui sesudah belanja live, dan
diperiksa tugas 7 fase.

### Jejak rehearsal dibersihkan, dan dibuktikan

```bash
git clean -f research/harness/recorded/          # 36 berkas mock dihapus
git checkout -- research/harness/recorded/_ledger.jsonl research/harness/recorded/_manifest.json
git status --porcelain research/harness/recorded/
# (kosong)
ls research/harness/recorded/*.json | wc -l      # 136, kembali ke angka asal
```

Hash kedua berkas status kembali persis ke nilai sebelum rehearsal:

```
b042746a5f31f1d85160ea2c1b4524cb962272698c3cce0d23ad79b016dda01f  _ledger.jsonl
2f61b18f5605e2d25522175500ffa3edad03fc843b8e891bbfb4694f6023e99f  _manifest.json
```

Tidak ada payload sintetis yang tertinggal di `recorded/`. Mock dihentikan sesudahnya.

---

## Tugas 5 (dari daftar keluaran) · Gate produk tetap hijau

Dijalankan, tidak ada berkas yang diubah:

```bash
cd src/katalis && ./run.sh test
```

**243/243 assertion hijau di 40 fungsi check, `exit=0`.** Sama dengan angka di
`plan/PROGRESS.md`, jadi tidak ada yang mundur. `git status --porcelain src/katalis/` kosong.

---

## Yang tetap hanya bisa dilakukan manusia

1. **Ambil ekspor portal baru, letakkan di `research/evidence/usage-log/`, jalankan
   `reconcile_usage.py`.** Ini menutup B3 dan membuat kriteria keluar 1 Fase 5 terpenuhi.
   Tanpa itu reconcile tetap `exit=1` dengan tujuh selisih yang sudah dijelaskan di atas.
2. **Belanja live 36 kredit, satu perintah, satu kali**, sesudah B3 ditutup:

   ```bash
   cd research/harness && SECTORS_API_KEY=<kunci tim dari .env> SECTORS_BASE_URL=https://api.sectors.app \
     python3 src/capture.py --plan plans/plan-katalis-corpus.json --budget 310
   ```

   Lalu commit payload baru bersama baris ledgernya (tugas 6 fase), dan verifikasi tiap simbol
   menerbitkan kartu atau ditolak dengan nama (tugas 7 fase).

## Kesiapan yang ditinggalkan

- `research/harness/plans/plan-katalis-corpus.json` — 36 entri, 36 kredit, tiap parameter
  dibatasi, satu simbol per entri, nol identifier tebakan, `hold_out: "NICK.JK"` sebagai field
  yang bisa diperiksa mesin.
- Enam simbol + hold-out terpilih dan beralasan, dengan baris `v2_suspensions.json` dan free
  float yang bisa dicek ulang.
- Rencana sudah dilatih terhadap mock: 36/36 `200`, biaya dan bentuk slug terbukti benar, dan
  `recorded/` sudah kembali bersih persis seperti semula.
- Satu temuan konkret yang mencegah belanja gagal: `--budget 42` seperti tertulis di berkas fase
  akan berhenti tanpa satu pun panggilan; angka yang benar adalah 310.
