# Firewall Tip Saham — dalam bahasa sederhana

Tanggal: 2026-09-09. Pendamping bahasa awam untuk
[`deep-research-firewall-pump-and-dump.md`](deep-research-firewall-pump-and-dump.md).

Topik ini **berdiri sendiri**. Riset kedua pada sesi yang sama, tentang akses non-visual, ada di
[`deep-research-akses-non-visual-simple.md`](deep-research-akses-non-visual-simple.md) — topik
berbeda, tidak saling bergantung.

---

## 1. Apa yang dibangun, satu paragraf

Alat yang menerima **satu kode saham** — yang baru saja seseorang lihat di grup Telegram, X, atau
video YouTube — lalu menjelaskan apa yang membuat saham itu rapuh: lonjakan harga dan volume di
luar kebiasaannya sendiri, dominasi segelintir broker, ritel masuk sementara institusi keluar, dan
tidak adanya berita fundamental yang menjelaskan kenaikan itu.

Satu kalimat: **ia memeriksa tip saham sebelum uang bergerak.**

---

## 2. Masalahnya, dan datanya

**Masalah.** Ritel menerima kode saham dari grup chat dan tidak punya cara memisahkan pergerakan
nyata dari yang direkayasa **sebelum** bertindak. Penegakan hukum datang tiga sampai empat tahun
kemudian.

| Klaim | Angka | Sumber | §|
| --- | --- | --- | --- |
| Pom-pom saham nyata dan dihukum | denda **Rp5,35 miliar** ke pegiat medsos; AYLS, FILM, BSML; 2021–2022 | OJK SP 38/GKPB/OJK/II/2026, 20 Feb 2026 | B1 |
| Penegakan terlambat | pelanggaran 2021–2022 → sanksi **Februari 2026** | idem | B1 |
| Modusnya persis pola yang kita cari | *"memanfaatkan reaksi followers atas informasi yang disampaikan"* | idem, verbatim | B1 |
| Ikut influencer merugikan | **56% "antiskill"**, imbal hasil abnormal **−2,3%/bulan**; 28% skilled +2,6% | Finfluencers, 29.000 akun StockTwits | B2 |
| Sinyal sosial menyesatkan | probabilitas "skilled" **memprediksi popularitas negatif**, β = −0,80 (p<1%) | idem | B2 |
| Celah regulasi diakui global | finfluencer *"operate outside"* kerangka regulasi | IOSCO FR/08/2025 | B2 |
| Paparannya masif | **30,27 juta SID**; ritel **51,1%** nilai transaksi; **54,12%** investor saham < 30 tahun | BEI/KSEI, Agustus 2026 | B5 |
| Kanalnya teridentifikasi | Telegram, Stockbit, Facebook; aktivitas B=0,284 dan sentimen B=0,329 → volume (p=0,001) | E-Jurnal Akuntansi 35(7), 2025 | B4 |
| Jawabannya bisa diuji | **583** suspensi berlabel IDX; 18/20 terbaru = *cooling down* lonjakan harga | `/v2/suspensions/` | B7 |
| Alat yang ada mengajak ikut, bukan memperingatkan | *"TP 1 (5%), TP 2 (10%), TP 3 (20%)"*, tagline "Semua Pasti Cuan!" | bandarmology.net | B9 |

---

## 3. Input → proses → output

![Alur input, proses, output — firewall tip saham](diagrams/firewall-pump-and-dump-alur.png)

> Diagram: [`diagrams/firewall-pump-and-dump-alur.drawio`](diagrams/firewall-pump-and-dump-alur.drawio),
> dibangun oleh [`diagrams/firewall-pump-and-dump-alur.py`](diagrams/firewall-pump-and-dump-alur.py).


```
INPUT
  1 kode saham              contoh: BNBR
  (opsional) teks tip       tempel pesan Telegram/X apa adanya (konteks saja)

        ↓  planner sadar-anggaran, target ~10 kredit per emiten

PROSES — 5 langkah, tiap langkah menghasilkan angka bersitasi

  P1  Baseline & anomali                              [Nam & Skillicorn 2023]
      /v2/daily/{symbol}/          → OHLCV ≤90 hari
      baseline = mean & SD atas 5 hari sebelum tanggal-uji
      pump_flag = harga > mean+2SD  DAN  volume > mean+2SD
      jendela pengamatan lanjutan: t+4

  P2  Siapa yang menggerakkan
      /v2/broker-summary/{symbol}/top/  → rank, broker_code, net_idr
      /v2/brokers/                      → origin, cohort   (cache selamanya)
      metrik = pangsa 5 broker teratas, dibobot kohort

  P3  Siapa yang keluar
      /v2/foreign-flow/{symbol}/                  → net_foreign_inflow harian
      /v2/company/shareholders-composition/{sym}/ → 9 kategori lokal + 9 asing
      pola dicari: individual_l naik, institusi/asing turun

  P4  Apakah ada alasannya                          [Columbia/Fidelity tahap 2]
      /v2/news/?symbols={symbol}
      ada berita fundamental di jendela sama → turunkan skor
      nol hasil                              → pertahankan

  P5  Konteks struktural (bobot RENDAH — lihat §4)
      /v2/suspensions/?symbol=  · /v2/free-float/ · /v2/companies/

        ↓  verifikator fail-closed: tiap angka wajib bawa (endpoint, field)

OUTPUT
  • vonis satu kalimat      "Rapuh pada 3 dari 4 sumbu."
  • 4 paragraf, satu per sumbu: angka → pembanding → sumber
  • tabel angka mentah + daftar sitasi
  • TIDAK PERNAH: target harga, sinyal beli/jual, sizing, eksekusi
```

Ambang "2 standar deviasi pada harga **dan** volume, jendela 5 hari, dump dalam 4 hari" bukan
tebakan — itu skema pelabelan dari makalah deteksi pump-and-dump 2023 yang mencapai akurasi 85%.
*(§B3)*

---

## 4. Tiga asumsi yang riset ini batalkan

**"Saham kecil paling rentan."** Studi atas BEI menemukan **arah sebaliknya** — kapitalisasi kecil
justru berprobabilitas manipulasi lebih rendah. Studi 2026 atas IDX80 juga tidak menemukan
konsentrasi pada saham kecil. Kapitalisasi jadi **fitur, bukan gerbang**. *(§B4, K2)*

**"Float tipis adalah sumbu utama."** BEI berencana **menghapus** free float rendah sebagai
kriteria Papan Pemantauan Khusus (Juli 2026), karena itu ciri teknis perdagangan, bukan kondisi
fundamental. Skor tidak boleh runtuh kalau float dicabut — siapkan uji ablasi. *(§B6, K1)*

**"`/v2/suspensions/` cuma riwayat masalah."** Ia sumber **label**. *(§B7, K3)*

---

## 5. Bagaimana kita tahu ini benar-benar bekerja

IDX sudah melabeli jawabannya. `/v2/suspensions/` berisi **583 baris**, dan 18 dari 20 terbaru
berbunyi sama:

> "Terjadinya peningkatan harga kumulatif yang signifikan pada saham X, dalam rangka cooling down
> sebagai bentuk perlindungan bagi investor"

Bertanggal, plus `pdf_url` ke pengumuman resmi. Ditulis bursa sendiri.

```
positif   : suspensi ber-reason "peningkatan harga kumulatif yang signifikan"
negatif   : lonjakan volume ≥2 SD yang TIDAK berujung suspensi dalam 10 hari bursa
titik uji : T−1  — sehari SEBELUM bursa mengumumkan
metrik    : presisi & recall, dipecah per bucket kapitalisasi,
            dilaporkan dengan dan tanpa sumbu free_float
```

Biaya menarik seluruh label: **~30 kredit** (583 baris ÷ 20 per halaman).

**Jebakan yang dihindari:** `/v2/free-float/` dan `/v2/companies/` mengembalikan snapshot hari ini
tanpa tanggal. Memakainya untuk menilai event Agustus adalah kebocoran label. Pakai
`shareholders-composition` yang bertanggal bulanan.

---

## 6. Contoh keluaran

> **BNBR — Bakrie & Brothers. Rapuh pada 3 dari 4 sumbu.**
>
> **Volume.** 7.994.414.100 lembar pada 6 Agustus 2026 — tervolume di seluruh bursa hari itu, pada
> harga Rp105. Terhadap baseline lima harinya sendiri, ini melewati ambang dua standar deviasi.
> *(`/v2/daily/BNBR/` field `volume`; `/v2/most-traded/`)*
>
> **Broker.** [pangsa 5 broker teratas, dibobot kohort] *(`/v2/broker-summary/BNBR/top/`)*
>
> **Kepemilikan.** [individu lokal vs institusi asing, per tanggal bulanan]
> *(`/v2/company/shareholders-composition/BNBR/`)*
>
> **Katalis.** [ada / tidak ada berita fundamental pada jendela sama] *(`/v2/news/?symbols=BNBR`)*
>
> Bukan rekomendasi beli atau jual. Tiap angka bisa ditelusuri ke satu endpoint dan satu field.

Volume dan harga di atas nyata, dari rekaman `most-traded` 2026-08-06. Tiga sumbu lain dikosongkan
karena belum ditarik — itu perilaku fail-closed yang sama yang akan dipakai produk: **tidak
menyebut angka yang belum diambil.**

Frame pembuka video yang menjelaskan dirinya sendiri: pada 2026-09-04, tiga gainer teratas —
UANG +24,92%, RONY +24,90%, SMMT +24,88% — semuanya menempel di batas ARA. *(§B8)*

---

## 7. Yang produk ini TIDAK katakan

- ❌ "BNBR akan naik besok." · ❌ "Target profit 20%." · ❌ Beli / jual / tahan / sizing.
- ❌ Eksekusi transaksi otomatis — dilarang aturan hackathon di semua track.
- ✅ "Volume hari ini 4,3 standar deviasi di atas kebiasaannya sendiri."
- ✅ "Lima broker menguasai 61% sisi beli; empat berkohort ritel."
- ✅ "Tidak ada berita perusahaan pada jendela yang sama."
- ✅ "Pada 583 suspensi historis, profil ini menyala pada T−1 sebanyak X%."

Garisnya bukan selera. Kompetitor terdekat menjual sinyal TP otomatis — itu rekomendasi investasi
dalam pengertian POJK 5/2019. Kami memakai data yang sama untuk mengatakan kebalikannya: bukan
"ayo ikut bandar", tapi **"ini kenapa saham ini rapuh"**. *(§B9)*

---

## 8. Yang belum diverifikasi

1. **Kosakata `reason` pada 563 suspensi sisanya** — baru 20 yang terbaca. Ini memblokir seluruh
   protokol evaluasi. ~30 kredit.
2. **Venue terbit makalah "Finfluencers"** — saat ini baru working paper + CEPR DP20204.
3. **Penulis dan tahun studi pump-dump BEI** (ProQuest 2088916427).
4. **Statistik KSEI resmi** — PDF gagal diekstrak; angka dari pemberitaan rilis BEI.
5. **Keandalan `cohort` pada `/v2/brokers/`** — nilainya mencakup `unknown`, proporsinya belum
   dihitung.
6. **Crawl X dan Telegram** — belum jalan: ekstensi OpenCLI tidak tersambung, Firecrawl menolak IP
   ini tanpa kunci API.

---

## 9. Dari mana tiap klaim berasal

| Bagian di sini | Bagian di dokumen besar |
| --- | --- |
| Data masalah (§2) | B1, B2, B4, B5, B7, B9 |
| Input/proses/output (§3) | B11 — kontrak lengkap |
| Ambang 2 SD, jendela t+4 (§3) | B3 — Nam & Skillicorn arXiv 2301.11403 |
| Asumsi yang dibatalkan (§4) | B4, B6, Koreksi K1–K3 |
| Protokol evaluasi (§5) | B7 — 583 suspensi |
| Field API (§3, §6) | B8 — dibaca dari `research/harness/recorded/` |
| Garis kepatuhan (§7) | B9, S2 — POJK 5/2019 |
| Belum diverifikasi (§8) | S3 |
