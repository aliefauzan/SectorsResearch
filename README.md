# KATALIS

KATALIS membaca payload Sectors API yang sudah dibeli dan disimpan di repo ini, lalu
menerbitkan satu kartu per pasangan (simbol, tanggal). Kartu itu menjawab satu pertanyaan:
apakah gerak harga hari itu punya penjelasan di luar transaksinya sendiri. Empat pilar
diperiksa — konsentrasi broker, volume, momentum, dan katalis — dan setiap angka di kartu
membawa endpoint dan field asalnya, bukan angka yang dihitung ulang oleh pembaca. Mesin
pelabelnya deterministik (`CLASSIFIER=rules`), jadi produk berjalan tanpa kunci API, tanpa
kuota model, dan tanpa satu pun panggilan API baru saat dipakai. Kartu menyatakan struktur
transaksi; ia bukan nasihat investasi, dan tidak ada baris di dalamnya yang berarti beli atau
jual.

## Menjalankan

```bash
cd src/katalis && ./run.sh pilar LIFE 2026-09-01
```

Perintah lain di folder yang sama, semuanya gratis dan membaca lapisan `recorded/`:

```bash
./run.sh symbols   # apa yang bisa dinilai, dan kenapa sisanya tidak
./run.sh method    # tiap ambang, batasnya, dan asalnya
./run.sh test      # seluruh gate produk ini
```

## Kartu contoh

Byte-identik dengan keluaran `cd src/katalis && ./run.sh pilar LIFE 2026-09-01` pada commit
ini:

<!-- CARD-BEGIN -->
```
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
<!-- CARD-END -->

## Loop belajar

Hari ini **0 peristiwa**. Fase 6 (`katalis-learn`: replay sinyal terhadap korpus berlabel,
lalu satu hold-out) belum dijalankan, jadi tidak ada satu pun ambang yang berasal dari
pembelajaran, dan berkas hasil belajarnya belum ada. Ini bukan angka yang dikarang; perintah
di bawah mengembalikannya apa adanya:

```bash
cd src/katalis && ./run.sh method | grep -c 'learned'
# 0
ls src/katalis/state
# ls: src/katalis/state: No such file or directory
```

## Ambang

Dari 18 ambang, **18 `shipped` dan 0 `learned`**. Dihitung dengan perintah ini:

```bash
cd src/katalis && ./run.sh method | grep -cE '  \[[0-9.]+, [0-9.]+\]  (shipped|learned)$'   # 18
cd src/katalis && ./run.sh method | grep -cE '  \[[0-9.]+, [0-9.]+\]  shipped$'              # 18
cd src/katalis && ./run.sh method | grep -cE '  \[[0-9.]+, [0-9.]+\]  learned$'              # 0
```

Seluruh keluaran `./run.sh method`, disalin apa adanya:

<!-- METHOD-BEGIN -->
```
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
<!-- METHOD-END -->

## Apa yang tidak diperiksa

Kartu mencetak daftar ini sendiri, di blok `YANG BELUM KAMI PERIKSA`:

```text
   YANG BELUM KAMI PERIKSA
     — cuaca dan fase iklim — belum dipasang
     — kanal di luar cakupan kami: Telegram, Stockbit, X
```

Selain itu, yang di luar jangkauan produk ini:

* **Ia tidak memanggil API live.** Yang dinilai adalah payload yang sudah terekam; simbol
  atau tanggal yang di luar irisan tangkapan ditolak dengan alasan bernama (`./run.sh method`
  mencetak kelima alasan itu), bukan diisi angka nol.
* **Ia tidak memeriksa kanal di luar `recorded/`** — percakapan Telegram, Stockbit, dan X
  tidak dibaca, jadi konsentrasi yang dibicarakan di sana tidak masuk kartu.
* **Ia tidak memperkirakan hari esok.** Tidak ada skor, target harga, atau rekomendasi; kartu
  hanya menyatakan apa yang sudah terjadi dan apa yang tidak menjelaskannya.
* **Ia bukan penasihat.** Kalimat penutup kartu berdiri sebagai batas produk: KATALIS
  menyatakan struktur transaksi, bukan nasihat investasi.

Rencana kerja, keadaan nyata, dan blocker hidup di [`plan/`](plan/README.md) —
mulai dari [`plan/PROGRESS.md`](plan/PROGRESS.md), yang menyatakan keadaan sebenarnya.
