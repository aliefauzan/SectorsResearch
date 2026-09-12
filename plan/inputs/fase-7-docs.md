# Fase 7 · tugas 2 dan 3 — README tingkat repo dan halaman metode

Catatan sesi, bukan pembaruan rencana. `plan/PROGRESS.md` dan `plan/phases/*` tidak disentuh
oleh sesi ini; berkas ini hanya merekam apa yang dikerjakan, perintah apa yang dijalankan, dan
keluaran apa yang keluar.

Sesi: cabang `fase7-docs`, worktree `sectors-14`, 2026-09-12. Nol kredit Sectors. Tidak ada
panggilan ke `api.sectors.app`, tidak ada `gcloud`, tidak ada push, tidak ada PR.

Tugas yang dikerjakan: **tugas 2** (`README.md` tingkat repo) dan **tugas 3** (tabel 18 ambang
masuk README). Kriteria keluar yang dijawab: **2**, **3**, dan **4**. Tugas 1, 4, 5, 6, 7, 8, 9
milik lane lain atau pekerjaan manusia dan tidak disentuh.

## Berkas yang dibuat

| Berkas | Isi |
| --- | --- |
| `README.md` (akar repo) | Paragraf produk, satu perintah menjalankan, kartu contoh byte-identik, hitungan peristiwa loop belajar, hitungan 18 ambang `shipped`/`learned`, tabel `./run.sh method` apa adanya, dan daftar apa yang tidak diperiksa |
| `plan/inputs/fase-7-docs.md` | Berkas ini |

Tidak ada berkas di `src/katalis/` yang disentuh. Tidak ada berkas di `plan/PROGRESS.md` atau
`plan/phases/` yang disentuh.

## Kriteria keluar 2 — kartu contoh byte-identik

Kartu yang dipakai: `LIFE 2026-09-01` pada commit ini.

Perintah yang menghasilkan angkanya:

```bash
cd src/katalis && ./run.sh pilar LIFE 2026-09-01 > /tmp/card-life.txt; echo "exit=$?"
# exit=0
wc -c < /tmp/card-life.txt
# 3650
```

Keluaran lengkapnya, apa adanya — ini yang disalin ke `README.md` di dalam blok berpagar:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BERGERAK TANPA PENJELASAN  ·  FLOAT TIPIS · free float 7.5%
LIFE · PT MSIG Life Insurance Indonesia Tbk 2026-08-28..2026-09-01 · recorded
kabar dilabeli CLASSIFIER=rules
   ambang dipakai: event_window 3 shipped · thin_float 0.15 shipped ·
   float_absorbed 0.01 shipped · foreign_share_in 0.6 shipped ·
   top1_dominant 0.4 shipped · neff_dominant 3 shipped · neff_crowd 8
   shipped · baseline_days 45 shipped · volume_mad_floor 0.05 shipped ·
   volume_z 2 shipped · dead_day_share 0.4 shipped · beta_shrink 0.7 shipped
   · price_mad_floor 0.005 shipped · resid_z 2.5 shipped ·
   news_lookback_days 7 shipped · filing_material_pct 0.5 shipped
────────────────────────────────────────────────────────────────────────────
!! KONSENTRASI  [bahaya]
   Satu broker, XL (Stockbit Sekuritas Digital), mengambil 65% dari net
   beli. Pembeli efektif: 2.2.
   broker_puncak XL · pangsa_puncak 64.7% · hhi 0.46 · pembeli_efektif 2.17
   · pangsa_asing 28.0% · pangsa_kohort retail 65%, institutional 28%, mixed
   7% · net_beli_total Rp553,717,500 · harga_masuk_puncak Rp9,840 ·
   float_terserap 0.03%
     (broker_puncak: Stockbit Sekuritas Digital)

!! VOLUME  [bahaya]
   Volume puncak 4.2 z di atas kebiasaannya sendiri (45 hari bursa).
   volume_puncak 174,100 · volume_z 4.18
     (volume_z: baseline 45 hari bursa)

!! MOMENTUM  [bahaya]
   Naik +41.7% dalam 3 hari bursa; +41.1% setelah gerak IHSG dikeluarkan,
   16.7 z.
   return_kumulatif 41.7% · return_residual 41.1% · beta_efektif 0.35 ·
   residual_z 16.75
     (return_residual: setelah gerak IHSG dikeluarkan)
     (beta_efektif: 0,7*beta_OLS + 0,3)
     (residual_z: baseline 45 hari bursa)

!! KATALIS  [bahaya]
   Tidak ada kabar yang menjelaskan: 1 dari 1 artikel terbaru hanya
   melaporkan harga yang sudah bergerak.
   artikel_menjelaskan 0 · artikel_melaporkan 1 · filing_material 0 ·
   aksi_korporasi 0
     (artikel_menjelaskan: artikel berlabel menjelaskan dalam 7 hari
     terakhir)
     (artikel_melaporkan: artikel berlabel melaporkan dalam 7 hari terakhir)

   YANG BELUM KAMI PERIKSA
     — cuaca dan fase iklim — belum dipasang
     — kanal di luar cakupan kami: Telegram, Stockbit, X

   FIELD
     /v2/broker-summary/{symbol}/ → summary[].broker_code
     /v2/broker-summary/{symbol}/ → summary[].nval
     /v2/brokers/ → code, is_foreign
     /v2/brokers/ → code, cohort
     /v2/broker-summary/{symbol}/ → summary[].bavg_per_share
     /v2/broker-summary/{symbol}/ → summary[].nlot,
     financials.historical_financials[].outstanding_shares, free_float
     /v2/daily/{symbol}/ → volume
     /v2/daily/{symbol}/ → close
     /v2/index-daily/ihsg/ → price
     /v2/news/ → timestamp, symbols, title, tags, dimension
     /v2/filings/ → holder_name, share_percentage_transaction,
     transaction_type
     /v2/company/corporate-actions/{symbol}/ → action_type, date

   KATALIS menyatakan struktur transaksi, bukan nasihat investasi. Tidak ada
   baris di atas yang berarti beli atau jual.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Bukti byte-identik — kartu diekstrak kembali dari `README.md` lalu di-`diff` terhadap
keluaran perintah yang menghasilkan kartu itu:

```bash
cd /Users/af/.ao/data/worktrees/sectors/sectors-14
awk '/^<!-- CARD-BEGIN -->$/{f=1;next} /^<!-- CARD-END -->$/{f=0} f' README.md | sed '1d;$d' > /tmp/readme-card.txt
wc -c < /tmp/readme-card.txt
# 3650
diff /tmp/readme-card.txt <(cd src/katalis && ./run.sh pilar LIFE 2026-09-01); echo "card diff exit=$?"
# card diff exit=0
```

Tidak ada keluaran `diff` di antara baris-baris itu, artinya nol selisih. Kartu di README
adalah 3650 byte, sama persis dengan stdout perintahnya.

## Kriteria keluar 3 — peristiwa loop belajar, dan ambang `shipped` versus `learned`

### Peristiwa loop belajar: 0

Fase 6 (`katalis-learn`) belum dijalankan, jadi angka jujurnya nol dan itu yang ditulis. Tidak
ada berkas hasil belajar. Perintah:

```bash
cd src/katalis && ./run.sh method | grep -c 'learned'
# 0
ls src/katalis/state
# ls: src/katalis/state: No such file or directory
```

`state/thresholds.learned.json` — berkas yang menampung hasil kalibrasi menurut
`src/katalis/thresholds.py` — tidak ada, dan direktori induknya pun tidak ada.

### Ambang: 18 `shipped`, 0 `learned`

```bash
cd src/katalis && ./run.sh method | grep -cE '  \[[0-9.]+, [0-9.]+\]  (shipped|learned)$'
# 18
cd src/katalis && ./run.sh method | grep -cE '  \[[0-9.]+, [0-9.]+\]  shipped$'
# 18
cd src/katalis && ./run.sh method | grep -cE '  \[[0-9.]+, [0-9.]+\]  learned$'
# 0
```

Ketiganya lewat `./run.sh method` sebagai sumber, bukan pembacaan kode sendiri. Baris
`ambang dipakai:` di kartu juga menyebut `shipped` untuk setiap ambang yang dibaca kartu itu.

## Kriteria keluar 4 — tabel 18 ambang identik dengan `./run.sh method`

Perintah dan keluaran lengkapnya:

```bash
cd src/katalis && ./run.sh method > /tmp/method.txt; echo "exit=$?"
# exit=0
wc -c < /tmp/method.txt
# 3694
```

Keluaran apa adanya — ini yang disalin ke `README.md`:

```text
AMBANG YANG BERLAKU
────────────────────────────────────────────────────────────────────────────
top1_dominant         0.4      [0.25, 0.6]  shipped
  One broker taking 40% of net buying is the point where 'the market bought
  it' stops being a fair description of what happened.
neff_dominant         3.0      [2.0, 5.0]  shipped
  Effective buyers = 1/HHI. Below 3 the buying side is a handful of desks
  however many broker codes appear in the file.
neff_crowd            8.0      [5.0, 15.0]  shipped
  Above 8 effective buyers no single hand explains the move.
foreign_share_in      0.6      [0.5, 0.8]  shipped
  Foreign brokers taking 60% of net buying is a one-sided tape, and it has
  to agree with net_foreign_inflow before it is said out loud.
retail_crowd_share    0.6      [0.45, 0.8]  shipped
  Retail plus mixed above 60% is the signature of a crowd, not a desk.
volume_z              2.0      [1.5, 3.5]  shipped
  Robust z on log volume. 2.0 keeps the daily flag count survivable for a
  human reader; the MAD floor below stops a dead stock manufacturing one.
volume_mad_floor      0.05     [0.01, 0.3]  shipped
  One log tick. Without a floor, a stock whose volume never moves has MAD≈0
  and every ordinary day scores z=∞.
resid_z               2.5      [1.5, 4.0]  shipped
  Cumulative 3-day residual return against IHSG, robust z over a 45-day
  baseline. 2.5 is the level where the move stops being the index's.
price_mad_floor       0.005    [0.001, 0.02]  shipped
  Half a percent of daily log return. Same argument as volume.
beta_shrink           0.7      [0.5, 1.0]  shipped
  beta_eff = 0.70*beta_OLS + 0.30. Shrinking towards 1 stops a thin baseline
  from handing a stock a beta of 4 and erasing its own move.
baseline_days         45       [30, 60]  shipped
  Trading days of baseline. 45 plus a 10-day scan plus the 3-day exclusion
  fits one /v2/daily/ call, which caps at 90 CALENDAR days — about 62
  trading days, which is what LIFE actually returned. Budget against 62
  trading days, not 90.
event_window          3        [1, 5]  shipped
  Trading days the move and the flow are both measured over. Broker summary
  is daily; three days is long enough to survive one quiet session.
dead_day_share        0.4      [0.2, 0.7]  shipped
  More than 40% zero-return days in the baseline and no z means anything.
  Such symbols are rejected with a reason, not scored.
news_lookback_days    7        [3, 21]  shipped
  How far before the flagged day an article may sit and still be read as
  preceding the move.
filing_lookback_days  30       [7, 90]  shipped
  Insider and major-holder filings are reported with a lag; 30 days is the
  window where one still explains today's tape.
filing_material_pct   0.5      [0.1, 2.0]  shipped
  Percentage points of the company a registered holder moved before it is
  worth putting on the card.
thin_float            0.15     [0.05, 0.3]  shipped
  Free float under 15% is the population where a small rupiah amount moves
  the price a long way.
float_absorbed        0.01     [0.002, 0.05]  shipped
  1% of free float changing hands inside the event window. This is the
  sentence no other service can print.

ALASAN SEBUAH SIMBOL DITOLAK
  baseline_tipis   fewer baseline days than baseline_days requires
  baseline_mati    more zero-return days than dead_day_share allows
  tanpa_broker     no broker summary on this source for this symbol
  tanpa_indeks     no IHSG series to take the market move out of
  tanpa_float      symbol absent from /v2/free-float/
```

Bukti identik — blok metode diekstrak kembali dari `README.md` lalu di-`diff`:

```bash
cd /Users/af/.ao/data/worktrees/sectors/sectors-14
awk '/^<!-- METHOD-BEGIN -->$/{f=1;next} /^<!-- METHOD-END -->$/{f=0} f' README.md | sed '1d;$d' > /tmp/readme-method.txt
wc -c < /tmp/readme-method.txt
# 3694
diff /tmp/readme-method.txt <(cd src/katalis && ./run.sh method); echo "method diff exit=$?"
# method diff exit=0
```

Nol selisih.

## Apa yang tidak diperiksa — sumbernya

Bagian itu di README menyitir langsung blok `YANG BELUM KAMI PERIKSA` yang kartu cetak
sendiri (terlihat di kartu contoh: cuaca dan fase iklim, serta kanal Telegram/Stockbit/X),
lalu menyebut kelima alasan penolakan bernama yang `./run.sh method` cetak di blok `ALASAN
SEBUAH SIMBOL DITOLAK`. Tidak ada klaim baru yang ditambahkan.

## Verifikasi penutup

```bash
cd src/katalis && ./run.sh test; echo "exit=$?"
# ... (20 + 22 + 92 + 62 + 63 + 25 + 13 = 297 assertion di 44 fungsi check)
# Semua gate hijau.
# exit=0
```

297 assertion, 44 fungsi check bernama, exit 0. Sama persis dengan angka di `plan/PROGRESS.md`
(297 di 44); tidak ada berkas `src/katalis/` yang diubah sesi ini.

```bash
cd /Users/af/.ao/data/worktrees/sectors/sectors-14
git diff --name-only --cached master
# README.md
# plan/inputs/fase-7-docs.md
```

Satu perintah lain yang dijalankan untuk memastikan kartu memang punya empat pilar:

```bash
cd src/katalis && ./run.sh pilar LIFE 2026-09-01 | grep -c '^!! '
# 4
```

## Yang tidak dapat ditulis karena belum ada

1. **Jumlah peristiwa loop belajar selain 0.** Satu-satunya angka yang bisa dihasilkan perintah
   adalah 0, karena Fase 6 belum jalan dan `src/katalis/state/` tidak ada. README menulis 0 dan
   menyebut Fase 6; tidak ada angka lain yang dikarang.
2. **Ambang `learned` selain 0.** Berkas `state/thresholds.learned.json` tidak ada, jadi tidak
   ada satu pun baris `learned` yang bisa dihitung. README menulis 18 `shipped` / 0 `learned`.
3. **Bukti kartu dari Cloud Run.** Kriteria keluar 2 hanya menuntut byte-identik dengan
   `./run.sh pilar` pada revisi yang ter-commit; itu dipenuhi lewat `diff` di atas. URL publik
   tidak dipanggil sesi ini — lane S5 yang mengurusnya.
4. **Tiga percakapan, video, teaser, post media sosial, submit.** Bukan bagian tugas 2 dan 3,
   dan tidak ada bahannya di sesi ini.
