# Naskah video juri — 3 menit

Penjurian asinkron. Tidak ada sesi tanya jawab. Video ini dan repo memikul
seluruh argumen sendirian: **30% dari nilai akhir** langsung, dan ia yang
membentuk penilaian kegunaan nyata (40%) karena juri tidak pernah melihat produk
ini dipakai selain di sini.

Naskah ini menulis apa yang **diucapkan**. Apa yang **terlihat** ada di
[`shot-list.md`](shot-list.md), nomor bidikannya dirujuk di kolom kanan.

- **Durasi target:** 175 detik. Batas keras 180.
- **Bahasa:** Indonesia. Tidak ada preferensi nilai antara ID dan EN.
- **Kredit API yang dihabiskan untuk merekam video ini: 0.** Semua yang muncul
  di layar berjalan atas payload di `../research/harness/recorded/`.

## Anggaran durasi

Kecepatan acuan **2,5 kata per detik** — narasi bahasa Indonesia yang terbaca
santai, bukan dikejar. Kolom *bicara* adalah waktu narasi; selisihnya terhadap
slot adalah jeda yang disengaja saat paragraf tercetak atau berkas digulir.
Jeda itu bagian dari bidikannya, bukan sisa yang boleh diisi kalimat baru.

| Segmen | Slot | Kata | Bicara | Sisa untuk jeda |
| --- | ---: | ---: | ---: | ---: |
| 0:00–0:25 masalah | 25 d | 65 | 26 d | 0 d |
| 0:25–1:15 produk | 50 d | 96 | 38 d | 12 d |
| 1:15–2:20 koreksi diri — cabang A | 65 d | 102 | 41 d | 24 d |
| 1:15–2:20 koreksi diri — cabang B | 65 d | 150 | 60 d | 5 d |
| 2:20–2:45 bukti — cabang A | 25 d | 28 | 11 d | 14 d |
| 2:20–2:45 bukti — cabang B | 25 d | 56 | 22 d | 3 d |
| 2:45–3:00 tak ditunggui | 15 d | 37 | 15 d | 0 d |
| **Total (jalur B, yang terpadat)** | **180 d** | **404** | **162 d** | **18 d** |

Cabang B yang menentukan batas. Kalau latihan dengan stopwatch tembus 180,
yang dipotong adalah kalimat backtest di cabang B — bukan kalimat CSMI/TMPO,
yang memikul kejujuran seluruh video.

Periksa hasil akhirnya, jangan percaya tabel ini:

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 video/mersamur-juri-3menit.mp4
```

---

## Gerbang rekam — dijawab sebelum kamera menyala

Dua adegan di naskah ini bergantung pada isi berkas yang **hari ini masih
kosong**. Jawab tiga pertanyaan ini pada hari rekam, lalu pilih cabangnya.
Jangan memilih cabang berdasarkan mana yang terdengar lebih bagus.

| # | Pertanyaan | Perintah | Kalau ya | Kalau tidak |
| --- | --- | --- | --- | --- |
| G1 | `state/lessons.jsonl` punya ≥1 baris dari kesalahan nyata? | `wc -l state/lessons.jsonl` | **Cabang A** (75–140) | **Cabang B** (75–140) |
| G2 | `state/warnings.jsonl` punya baris yang mendahului satu suspensi IDX? | `wc -l state/warnings.jsonl` | **Cabang A** (140–165) | **Cabang B** (140–165) |
| G3 | `state/runs.jsonl` punya ≥10 baris dari hari kerja berbeda? | `wc -l state/runs.jsonl` | rekam | **tunda** — lihat §Jadwal |

Keadaan pada 2026-09-10: G1 **tidak** (0 baris), G2 **tidak** (0 baris),
G3 **belum** (1 baris). Naskah cabang B bukan rencana cadangan yang lebih lemah
— ia adalah temuan negatif yang jujur, dan aturan 3 tugas ini menyatakan temuan
seperti itu dinilai lebih tinggi daripada kurva yang mencurigakan.

**Dilarang menggeser ambang di `state/thresholds.json` agar cabang A terbuka.**
Itu menyetel model untuk memenangkan demo, dan `app/agent/evolve.py` memang
dibangun untuk mencegahnya. Kalau tergoda, baca §Batasan di `README.md`.

---

## Jadwal

| Tanggal | Yang terjadi |
| --- | --- |
| 2026-09-09 | Baris pertama `runs.jsonl`. Cron `0 4 * * 1-5` mulai berjalan |
| 2026-09-25 (Jumat) | 13 hari kerja terkumpul di `runs.jsonl`. **Jendela rekam dibuka** |
| 2026-09-25 s.d. 2026-09-26 | Rekam, sunting, unggah |
| **2026-09-27** | **Batas rekam.** Bukan malam terakhir — kriteria selesai tugas 21 |
| 2026-09-30, 23:59 WIB | Batas kirim. Server penyelenggara yang memutuskan ketepatan waktu |

---

## 0:00–0:25 · Masalahnya, dan siapa yang punya

*Bidikan: S1, S2, S3. Tanpa wajah bicara. Suara mulai di detik 0.*

> Ini grup Telegram. Satu kode saham masuk, tanpa alasan, tanpa angka.
>
> Kalau Anda investor ritel di Indonesia, pilihannya cuma dua: percaya, atau
> abaikan. Tidak ada cara memeriksanya dalam dua menit.
>
> Januari 2026, MSCI membekukan rebalancing indeks Indonesia atas kualitas free
> float dan konsentrasi kepemilikan. IHSG ditutup minus tujuh koma tiga lima
> persen hari itu.
>
> Dua hal yang dipersoalkan MSCI itu bisa dihitung dari data Sectors.

*(65 kata · ±26 detik pada 2,5 kata/detik)*

**Klaim yang diucapkan dan sumbernya** — kalau juri memeriksa, harus ketemu:

| Klaim | Sumber |
| --- | --- |
| MSCI membekukan rebalancing Indonesia atas kualitas free float | Tempo, `riset/deep-research.md` §6.2 |
| IHSG −7,35% pada hari pengumuman (28 Jan 2026) | Katadata Databoks, `riset/deep-research.md` §6.2 |

---

## 0:25–1:15 · Produknya. Sekali, tanpa potongan

*Bidikan: S4. Satu perekaman utuh, tanpa cut. Terminal saja.*

> Tempel satu kode saham. Satu paragraf keluar.

*Ketik `python3 -m app.cli LIFE`, tekan Enter, diam sampai paragraf selesai
tercetak. Jangan bicara di atas teks yang sedang muncul.*

> Yang dibaca: sesi terakhir LIFE tercatat dua puluh empat setengah kali median
> enam belas sesi sebelumnya. Satu broker memegang delapan puluh tiga koma
> delapan persen sisi beli. Dan IDX pernah menghentikan perdagangan saham ini
> dua kali sebelum jendela ini.
>
> Tidak ada kata "beli". Tidak ada skor. Tidak ada lampu merah atau hijau.
> Daftar kata terlarang itu ditegakkan oleh tes, bukan oleh niat.
>
> Di bawahnya, dua puluh satu baris sitasi. Tiap angka membawa endpoint dan nama
> field asalnya — jadi paragraf ini bisa dibantah baris per baris, bukan
> dipercaya begitu saja.

*(96 kata · ±38 detik bicara; sisa 12 detik adalah jeda saat paragraf tercetak.
Jangan isi jeda itu dengan kalimat)*

Aturan segmen ini: **jangan sebut arsitektur.** Tidak ada kata "sumbu",
"pipeline", "modul". Juri perlu tahu masalah siapa yang diselesaikan sebelum
mereka peduli bagaimana.

---

## 1:15–2:20 · Adegan pemenang: agen yang mengoreksi dirinya

Pilih **satu** cabang lewat gerbang G1. Rekam hanya yang terpilih.

### Cabang A — kalau `lessons.jsonl` sudah berisi kesalahan nyata

*Bidikan: S5A, S6A, S7A.*

> Alat yang menampilkan angka sudah banyak. Yang ini menulis apa yang dia
> katakan, lalu menghadapkannya ke apa yang benar-benar terjadi.
>
> Ini `warnings.jsonl` — apa yang sistem katakan, kapan, terhadap ambang berapa.
> Ini `outcomes.jsonl` — putusannya, diadili terhadap `/v2/suspensions/`, sumber
> label resmi IDX.
>
> Dan ini `lessons.jsonl`. Baris ini adalah satu kesalahan. Tanggalnya, emitennya,
> sumbu yang paling mungkin salah, dan berapa jauh ia meleset dari ambangnya.
>
> Agen ini lalu mengusulkan menggeser ambang itu. Usulannya harus lewat lima
> penjaga di `evolve.py` — dan alasan geserannya disimpan di dalam
> `thresholds.json` sendiri, versi lama tetap ada.
>
> Ini hasil hold-out sesudahnya. \[**Ucapkan angkanya apa adanya. Kalau tidak
> membaik, katakan tidak membaik.**\]

*(102 kata · ±41 detik bicara; sisanya jeda saat berkas dibuka dan digulir)*

### Cabang B — kalau `lessons.jsonl` masih kosong (keadaan 2026-09-10)

*Bidikan: S5B, S6B, S7B.*

> Alat yang menampilkan angka sudah banyak. Yang ini menulis apa yang dia
> katakan, lalu menghadapkannya ke apa yang benar-benar terjadi. Loop itu ada,
> jalan tiap hari kerja, dan hari ini ia tidak punya apa-apa untuk dipelajari.
> Saya tunjukkan kenapa, karena itu temuan yang sebenarnya.
>
> Empat sumbu, ambang tiga dari empat. Pada ambang yang produk ini dokumentasikan,
> belum ada satu simbol pun yang lewat — jadi `warnings.jsonl`, `outcomes.jsonl`
> dan `lessons.jsonl` kosong, dan log yang sepi itu saya laporkan apa adanya.
>
> Ini mahalnya. Empat belas Agustus, CSMI dan TMPO. Keduanya dihentikan IDX dua
> minggu kemudian. Sistem membaca dua dari empat sumbu menyala di keduanya —
> di bawah bar. Ia tidak memperingatkan. Itu kelewatan yang bisa dihitung, bukan
> kelewatan yang disembunyikan.
>
> Backtest-nya mencatat konsekuensinya sendiri: nol peringatan, jadi lift tidak
> terdefinisi. Bukan kalah — belum terukur.
>
> Yang bergerak justru satu-satunya hal yang boleh bergerak: ambang katalis, versi
> dua ke tiga, alasannya tertulis di dalam berkasnya sendiri.

*(150 kata · ±60 detik pada 2,5 kata/detik. Latih dengan stopwatch; kalau lewat,
buang kalimat backtest — bukan kalimat CSMI/TMPO.)*

---

## 2:20–2:45 · Bukti yang bisa diverifikasi juri sendiri

Pilih lewat gerbang G2.

### Cabang A

*Bidikan: S8A.*

> Ini bukan klaim yang harus dipercaya. Kiri: baris `warnings.jsonl`, tertanggal
> lima hari bursa sebelumnya. Kanan: pengumuman penghentian sementara dari IDX,
> tanggal H. Dua berkas, dua tanggal, keduanya publik.

*(28 kata · ±11 detik; sisanya diam di layar terbelah)*

### Cabang B

*Bidikan: S8B.*

> Sumber kebenarannya satu, dan bukan buatan kami: `/v2/suspensions/` —
> lima ratus delapan puluh lima peristiwa, empat ratus lima puluh dua
> cooling-down. Kiri, baris yang dikembalikan Sectors. Kanan, pengumuman IDX
> untuk peristiwa yang sama. Tiap tanggal bisa dicek juri sendiri.
>
> Semua yang saya tunjukkan sudah selesai dan sudah diumumkan. Tidak ada saham
> hidup yang disebut di video ini.

*(56 kata · ±22 detik)*

---

## 2:45–3:00 · Tak ditunggui, dan batasnya

*Bidikan: S9, S10, S11. Disclaimer muncul di layar dan bertahan sampai video habis.*

> Berjalan sendiri tiap hari kerja, log-nya di-commit balik ke repo —
> \[**sebutkan jumlah baris pada hari rekam**\] baris sejauh ini.
>
> Untuk investor ritel yang menerima tip di grup chat: satu paragraf, tiap angka
> tersitasi. Deskriptif, bukan saran investasi.

*(37 kata · ±15 detik. Jangan tambah kalimat di sini — ini segmen paling ketat
di seluruh naskah, dan kartu disclaimer memakan tiga detik terakhirnya.)*

---

## Disclaimer di layar

Bukan hanya diucapkan — syarat aturan 5 tugas ini dan Fase 2 checklist.

- **Bar bawah permanen**, muncul sejak detik 0 sampai frame terakhir:
  `Deskriptif · bukan saran investasi · tanpa eksekusi transaksi · mersamur/DISCLAIMER.md`
- **Kartu penuh 3 detik** di 2:57–3:00, teks yang sama diperbesar.
- Saat kode saham mana pun terlihat di layar, bar bawah berganti:
  `Kode saham muncul karena ada di respons API pada jendela yang disebut — bukan tuduhan terhadap emiten mana pun.`

---

## Yang tidak boleh masuk video

1. **Sembilan puluh detik pertama untuk arsitektur.** Diagram arsitektur tidak
   muncul sama sekali di naskah ini; itu disengaja.
2. **Saham yang masih hidup disebut "direkayasa".** Risiko hukum untuk tim dan
   penyelenggara. Hanya peristiwa yang sudah disuspensi dan sudah diumumkan.
3. **Data sintetis.** `synth/` tidak boleh muncul satu frame pun. Kalau terpaksa
   muncul, harus berlabel di layar — lebih mudah: jangan buka foldernya.
4. **Klaim yang tidak didukung repo.** Kedalaman teknis diverifikasi terhadap
   repositori; satu klaim yang tidak ketemu berkasnya merusak seluruh 30%.
5. **Rekaman senyap, terminal 720p yang tidak terbaca, lima menit diagram.**
   Empat cara termurah kehilangan nilai, menurut checklist penyelenggara.
6. **Isi `.env`, `SECTORS_API_KEY`, token bot Telegram, ID chat pribadi.**
   Lihat §Keamanan layar di `shot-list.md`.

---

## Di luar cakupan tugas ini

Checklist Fase 3 juga meminta **video teaser 1 menit** (publik, YouTube atau
media sosial, murni produk bekerja), **satu kalimat pernyataan masalah**, dan
**satu unggahan media sosial yang menandai akun Sectors**. Tugas 21 hanya
mencakup video juri tiga menit. Ketiganya belum punya berkas dan belum
dikerjakan — dicatat di sini supaya tidak hilang.
