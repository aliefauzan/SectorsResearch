# Meridian untuk Saham — Versi Ringkas

> Pendamping bahasa sederhana untuk [`deep-research.md`](deep-research.md). Kalau hanya punya
> lima menit, baca ini.

## Tiga hal yang perlu diketahui tentang lombanya

1. **Sectors harus jadi sumber data inti.** Tesnya sederhana: cabut Sectors, produk harus mati.
   Kalau produk masih jalan, submission gugur di pemeriksaan pertama.
2. **70% nilainya bukan kode.** Usability 40%, video 30%, teknis 30%. Penjurian asinkron —
   Anda tidak hadir untuk menjelaskan apa pun.
3. **Proyek paling obvious di tiap track sudah diterbitkan Supertype sendiri.** Termasuk agen
   multi-spesialis fundamental + teknikal + berita (FinArena, Juni 2026). Membangunnya ulang
   dinilai rendah oleh orang yang menulisnya.

## Ada dua Meridian

- **`yunus-0x/meridian`** (yang Anda tautkan) — agen likuiditas otonom untuk pool DLMM di
  Solana. Ia **membuka dan menutup posisi dengan modal nyata**. Eksekusi trade otomatis dilarang
  di semua track lomba ini.
- **`iliane5/meridian`** — yang berita: scrape RSS, klaster dengan embedding + UMAP/HDBSCAN,
  sintesis brief harian.

Bayangan Anda tentang "Meridian yang heavy scraping berita" adalah yang kedua. Arsitektur
belajarnya yang menarik ada di yang pertama.

## Kenapa "agen saham dengan scraping berita berat" tidak boleh dibangun

- **Gagal eligibility.** Sinyal dari berita hasil scraping menjadikan Sectors dekorasi.
- **Mubazir.** `/v2/news/` seharga 1 kredit sudah mengembalikan `dimension` — tiap artikel
  sudah diklasifikasi di 8 tema berskor. Anda menghabiskan berminggu-minggu membangun ulang
  sesuatu yang gratis.
- **Arah sinyalnya terbalik.** Di kripto, berita *adalah* fundamentalnya. Di saham, berita
  tertinggal di belakang data terstruktur yang sudah merekam pergerakan: broker flow, filing,
  komposisi pemegang saham.

**Pembalikannya:** data Sectors mendeteksi, berita menjelaskan.

## Saham beda dari kripto di enam titik yang mengubah arsitektur

| | Kripto | Saham IDX |
| --- | --- | --- |
| Jam | 24/7 | Sesi tetap, T+2, 22 hari libur bursa 2026 |
| Batas harga | Tidak ada | ARA/ARB — 35%/25%/20% per pita harga (usulan revisi) |
| Siapa yang membeli | Terlihat penuh di chain, gratis | Buram — hanya broker summary agregat, berkredit |
| Fundamental | Tidak ada | Laporan kuartalan wajib, **tanggalnya diketahui sebelumnya** |
| Wasit | Tidak ada | IDX + OJK bisa suspensi, pindah papan, delisting |
| Umpan balik | Jam | Minggu sampai kuartal |

Ditambah satu yang khas Indonesia: **short selling masih dilarang/ditunda.** Tidak ada cara
mengekspresikan pandangan negatif, jadi distorsi harga bertahan lebih lama sebelum runtuh.

Empat lapis yang menggerakkan saham, dari yang paling sering dilewatkan:

1. **Aturan bursa** — ARA/ARB, Papan Pemantauan Khusus (172 saham per Januari 2026), suspensi, UMA.
2. **Arus dana** — broker flow per kohort, aliran asing (~Rp75 T keluar sampai Juni 2026,
   IHSG −31,8% YTD), rebalancing indeks (MSCI membekukan Indonesia; IHSG −7,35% dalam sehari).
3. **Fundamental terjadwal** — earnings, cum/ex dividen, rights issue, stock split. Semuanya
   bertanggal dan mengubah harga secara mekanis.
4. **Komoditas dan makro** — batu bara, nikel, CPO; BI Rate 5,75% setelah naik 100 bps sejak
   Mei 2026; rupiah menyentuh 18.178.

## Bentuk yang lolos

> Agen risiko yang menjalankan screen kerapuhan harian, menilai peringatannya sendiri terhadap
> pengumuman bursa yang benar-benar terjadi, menulis pelajaran dari tiap kesalahannya, dan
> menggeser ambangnya sendiri di dalam pagar yang bisa diaudit.

Diambil dari Meridian: loop ReAct, decision log, lessons, threshold evolution.
Dibuang: eksekusi on-chain, wallet, PnL, scraping sinyal Discord.
Diganti: reward PnL → **peristiwa bertanggal yang diumumkan bursa** (suspensi, PPK, UMA).

Track yang disarankan: **02**, ladang paling kosong, dengan loop belajar sebagai kedalaman
teknisnya.

## Dua temuan baru per 9 September 2026

1. **BEI menargetkan revisi aturan PPK di Q3 2026** — kriteria 6 (free float), 7 (likuiditas),
   dan 10 (suspensi >1 hari) diusulkan **dihapus**. Ketiganya ada di antara tujuh kriteria yang
   bisa dihitung di ide PPK early warning. Kalau ide itu dipakai, buat kriterianya sebagai
   konfigurasi berversi, bukan konstanta.
2. **MSCI membekukan rebalancing Indonesia** atas kualitas free float dan konsentrasi
   kepemilikan. Itu persis dua sumbu yang bisa dihitung dari data Sectors — pengait pembuka
   video yang terverifikasi secara eksternal.

## Kalau saya juri, tiga pertanyaan pertama

1. Saya cabut Sectors — apa yang mati?
2. Mana log run tanpa ditunggui lintas hari, bukan satu run yang dipicu saat merekam?
3. Apa yang dilakukan agen ketika ia salah — dan di berkas mana saya bisa melihatnya?

## Satu hal untuk dikerjakan hari ini

Nyalakan scheduler melawan mock. Gratis, dan tiga minggu log adalah satu-satunya bukti yang
tidak bisa dikarang di minggu terakhir.

```bash
cd ../research/harness && python3 src/mock_server.py --port 8787 --credits 1000
```
