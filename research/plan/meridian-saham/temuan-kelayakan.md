# Temuan Uji Kelayakan — Data Live, 9 September 2026

> Menjawab empat pertanyaan dari [`red-team.md`](red-team.md). Semua angka berasal dari
> panggilan live ke `api.sectors.app`, terekam di `research/harness/recorded/` dengan entri
> ledger-nya. **52 kredit terpakai** (21 + 20 + 11). Jalankan ulang analisisnya gratis:
>
> ```bash
> cd research/harness && python3 src/feasibility.py
> ```

## Vonis

**Produknya layak dibangun.** Tiga dari empat gerbang lolos, satu lolos sebagian dan menunjuk
uji lanjutan yang berbiaya 10 kredit. Tetapi **empat asumsi di [`spec.md`](spec.md) terbukti
salah** dan spec harus direvisi sebelum kode ditulis.

---

## Q4 · Base rate dan set label — LOLOS

585 baris, 2018-12-28 sampai 2026-09-09.

```
TAHUN   cooling   lain   TOTAL
2018-2024     0     53      53
2025        332     70     402
2026        120     10     130
```

### Temuan 1 — label ini baru ada sejak 2025

**Nol suspensi cooling-down sebelum 2025.** Riwayat label yang bisa dipakai adalah **20 bulan**,
bukan 7,7 tahun. Semua peristiwa sebelumnya kelas lain: `long_suspend` 56, `rule_I_A` 25,
`late_report` 16, `ppk_over_1y` 7, `delisting` 3.

Ini kabar baik untuk anggaran: backtest hanya perlu 2025–2026, jadi kekhawatiran biaya di
red-team §B7 hilang.

### Temuan 2 — base rate lebih rendah dari perkiraan

```
REZIM 2026: 120 cooling-down / ~174 hari bursa = 0,69 per hari
BASE RATE per saham per jendela 10 hari : 0,77%
```

Taksiran red-team dari 20 baris: 1,22%. Angka sebenarnya **0,77%**. Presisi telanjang akan
terlihat buruk apa pun modelnya — **laporkan lift, bukan akurasi**.

### Temuan 3 — residivisme mendominasi

```
452 peristiwa cooling-down / 236 emiten unik = 1,92 per emiten
353/452 (78%) berasal dari emiten yang pernah disuspensi sebelumnya
teratas: MGLV x7 · UDNG x7 · PACK x5 · MDIA x5 · LUCY x5 · MLPT x5 · INET x5 · MINA x5
```

Tiga konsekuensi:

- **Baseline kedua yang wajib dikalahkan.** Red-team hanya menyebut baseline momentum. "Pernah
  disuspensi" sendirian mungkin sudah kuat. Sekarang ada dua lawan tanding, bukan satu.
- **Risiko kebocoran parah.** Model bisa menang dengan menghafal daftar residivis, bukan dengan
  memahami apa pun. Pemisahan waktu harus ketat.
- **Tapi juga fitur produk gratis.** "Saham ini sudah disuspensi 5 kali, terakhir 3 minggu lalu"
  berguna, benar, dan nol pemodelan.

### Temuan 4 — klasifikasi alasan perlu diperbaiki

Regex awal kehilangan 17 peristiwa: `"Dalam rangka cooling down"` muncul **tanpa** awalan
`"peningkatan harga kumulatif"`. Setelah diperbaiki: 435 → **452**. Sembilan kelas alasan
terpetakan di `src/feasibility.py`.

---

## Q1 · Ketersediaan broker-summary untuk gorengan — LOLOS

10 dari 10 saham tersuspensi mengembalikan baris penuh. `n_brokers=10` bekerja.

```
SYM     top1_buy%  top3_buy%  top1 broker         cohort
LIFE        83,8%      90,0%           XL         retail
NICK        80,5%      98,7%           PD          mixed
TRUK        66,6%      86,3%           XL         retail
AGAR        62,6%      69,8%           XL         retail
CSMI        61,6%      78,3%           XL         retail
TMPO        61,6%      76,8%           XL         retail
ASLI        54,0%      70,4%           XL         retail
SAFE        51,8%      64,1%           XL         retail
PPGL        26,7%      44,6%           CP  institutional
PACK        13,5%      33,3%           YU  institutional

median top1 gorengan : 61,6%
PEMBANDING BLUE CHIP : BBCA 11,3% · BBRI 14,3% · ADRO 30,0% · TLKM 33,9%
```

Satu broker ritel (`XL`) adalah pembeli teratas di **7 dari 10** saham tersuspensi.

### Peringatan: perbandingan ini masih tercampur

Ini membandingkan **gorengan tersuspensi vs blue chip** — mencampur ukuran dengan manipulasi.
Saham kecil punya broker terkonsentrasi terlepas dari digoreng atau tidak. Dan `XL` mungkin
sekadar broker ritel online terbesar, muncul di mana-mana.

**Kontrol yang benar** — saham kecil yang tidak pernah disuspensi — belum diambil. Sampai itu
ada, 61,6% menarik tapi belum membuktikan apa pun.

---

## Q2 · Cakupan berita — LOLOS, tetapi sumbunya harus dirumuskan ulang

```
emiten diminta dengan berita : 10/10   (112 artikel untuk 10 nama)
PACK 11 · LIFE 8 · PPGL 8 · NICK 5 · ASLI 4 · SAFE 4 · TRUK 3 · CSMI 2 · TMPO 2 · AGAR 2

dimension bukan-nol di 30 artikel:
  technical 21 · valuation 7 · future 4 · financials 3 · ownership 3
```

Kekhawatiran red-team §B6 — bahwa saham lapis tiga tidak punya berita sama sekali — **tidak
terbukti**. Cakupannya justru baik.

Tetapi rumusan sumbunya salah. Bukan *"tidak ada berita"*, melainkan:

> **"Berita ada, 21 dari 30 berdimensi `technical`, hanya 3 yang `financials`."**

Liputan yang membahas pergerakan harga tanpa alasan fundamental di baliknya. Rumusan ini lebih
kuat dan lebih mudah dipertahankan daripada ketiadaan.

> Catatan proses: vonis pertama analyzer ini **salah** — memakai penyebut 329 emiten padahal
> panggilannya hanya meminta 10. Sudah diperbaiki di `src/feasibility.py`.

---

## Q3 · Lift vs baseline momentum — LOLOS SEBAGIAN

Uji di dalam saham yang sama: jendela 5 hari sebelum suspensi vs semua jendela lain pada
saham itu juga.

```
SYM     gain5 sblm suspensi   median gain5   persentil
TMPO                  46,5%          -3,8%          94
TRUK                  31,9%          21,4%          88
CSMI                  47,6%          13,4%          88
ASLI                  51,6%          26,5%          81
AGAR                  49,6%           0,0%          81
NICK                  30,1%          26,5%          81
LIFE                  60,2%          23,8%          75
PACK                  38,9%          28,7%          75
PPGL                  44,8%          26,0%          69
SAFE                  42,3%          25,0%          62

persentil median : 81
peristiwa di persentil >=90 : 2/12 (17%)
```

**Momentum saja tidak cukup.** Kalau cukup, persentilnya akan mendekati 99 dan mayoritas
peristiwa berada di atas persentil 90. Yang terjadi: median 81, hanya 17% di atas 90.

Tautologi §A1 **nyata tetapi tidak fatal** — ada ruang untuk sumbu lain. Perhatikan juga bahwa
saham-saham ini rutin bergerak 13–29% dalam lima hari **pada hari biasa**. Baseline apa pun di
universe ini harus dinormalisasi terhadap volatilitasnya sendiri.

**Batas keyakinan:** hanya 12 peristiwa, jendela 21 hari. Ini indikasi arah, bukan bukti.

---

## Empat koreksi untuk `spec.md`

1. **`/v2/daily/` mengembalikan 21 hari secara default, bukan 90.** Jendela penuh butuh `start`
   dan `end` eksplisit. Seluruh perhitungan baseline volume dan momentum di spec mengasumsikan
   90 hari.
2. **`/v2/suspensions/` limit maksimum 30**, jadi riwayat penuh = 20 halaman = 20 kredit.
3. **Sumbu "tanpa katalis" diganti** menjadi "tidak ada berita berdimensi fundamental",
   bukan ketiadaan berita.
4. **Tambahkan baseline "pernah disuspensi"** sebagai lawan tanding kedua, dan tangani
   kebocorannya.

## Satu temuan yang mengubah penentuan universe

```
200 saham berkapitalisasi terkecil di screener
  pernah disuspensi : 98 (49%)
  kandidat kontrol bersih : 102
```

Base rate pasar 0,77% per 10 hari. Tetapi di **universe 200 saham terkecil, separuhnya punya
riwayat suspensi**. Itu universe tempat tip grup Telegram berasal.

Batasi produk ke lapis itu dan ekonomi statistiknya berubah total — dari mencari jarum di
tumpukan jerami menjadi memilah kelompok yang memang berisiko tinggi. **Ini yang membuat produk
punya peluang bekerja.**

## Uji berikutnya — 10 kredit

Ambil `/v2/daily/` untuk 10 saham dari daftar kontrol bersih (`INDX`, `BMBL`, `WIDI`, `OCAP`,
`ARKA`, `HADE`, `DIGI`, `PCAR`, `AEGS`, `RICY`) dengan `start`/`end` eksplisit. Itu menutup
lubang terakhir: apakah 61,6% konsentrasi dan lonjakan momentum benar-benar membedakan saham
yang digoreng dari saham kecil biasa.

Tanpa itu, semua angka di atas deskriptif — bukan diskriminatif.
