# 00 · PRD, dipadatkan

Ringkasan `katalis-v9.prd.md` ke bentuk yang cukup untuk bekerja tanpa membuka PRD penuh.
Ini bukan PRD kesembilan dan tidak berwenang mengubah lingkup: kalau baris di sini berselisih
dengan `katalis-v9.prd.md`, PRD yang menang dan baris ini yang diperbaiki.

## Masalah

Investor ritel Indonesia melihat satu sahamnya naik tajam dan tidak punya cara menjawab
pertanyaan pertama: **siapa yang mengangkatnya, dan apakah ada yang menjelaskannya.**

Biayanya terukur. 172 saham berada di Papan Pemantauan Khusus per Januari 2026 — sekitar
seperlima pasar — dan daftarnya terbit setelah statusnya berlaku
(`research/evidence/rechecks/ppk-verification-2026-09-07.md`). Tidak ada peringatan dini resmi.

LIFE.JK adalah kasus itu, dan datanya ada di disk repo ini: free float 7,5%, naik 41,7% dalam
tiga hari bursa, 65% net beli dari satu broker, disuspensi 2026-09-02 dan 2026-09-04.

```bash
cd src/katalis && ./run.sh pilar LIFE 2026-09-01
```

## Pengguna

**Primary.** Investor ritel Indonesia yang memegang 3–15 saham dan aktif di grup
WhatsApp/Telegram saham. Pemicunya sempit dan itulah gunanya: ia baru melihat satu simbol
bergerak tajam, atau baru disebutkan satu simbol, dan sedang memutuskan apakah ikut.

Data LIFE mempertajam persona itu alih-alih hanya mengilustrasikannya. Broker puncaknya XL,
Stockbit Sekuritas Digital — aplikasi ritel — dan pangsa kohortnya pada jendela yang sama
adalah ritel 65%, institusi 28%, campuran 7%. Yang mengangkat saham itu adalah orang seperti
penggunanya, lewat aplikasi yang ia pakai.

**Bukan untuk.** Trader institusi, day trader yang butuh tick dan orderbook, dan siapa pun
yang mengharapkan rekomendasi beli/jual.

## Hipotesis

Kami percaya **kartu Empat Pilar ber-sitasi** akan **menghentikan investor ritel membeli ke
dalam pergerakan yang digerakkan satu tangan pada saham berfloat tipis** untuk **investor ritel
Indonesia yang sedang memutuskan apakah ikut sebuah simbol**.

Satu bagiannya sudah berhenti menjadi hipotesis. Pada LIFE.JK verdict tertinggi terbit
2026-08-27 dan bursa menyuspensi 2026-09-02 — empat hari bursa lebih dulu, di atas data IDX
nyata, dan dapat diperiksa siapa pun terhadap `research/harness/recorded/v2_suspensions.json`.
n-nya satu; itu satu kasus, bukan tingkat keberhasilan.

Yang **belum** terbukti dan tetap hipotesis: bahwa pengguna membuka kartu **sebelum** membeli,
bukan sesudah. Itu butuh percakapan nyata, bukan argumen, dan itulah tugas terakhir Fase 7.

## Kriteria sukses

Dibatasi anggaran kredit, bukan kalender. Enam baris, dan tiap baris punya fase yang
memenuhinya.

| Metrik | Target | Dipenuhi di |
| --- | --- | --- |
| Kartu penuh di atas data nyata | ≥3 simbol | Fase 5 (satu sudah ada: LIFE) |
| Peringatan mendahului peristiwa berlabel | ≥2 dari 3 | Fase 5 + Fase 6 |
| Kebisingan pada replay berlabel | ≤40% | Fase 6 |
| Loop belajar hidup | ≥6 lesson dari peristiwa berlabel, ≥1 simbol hold-out | Fase 6 |
| Terbaca tanpa dipandu | 3 dari 3 orang menyebut isi kartu tanpa dipandu | Fase 7 |
| Kredit | belanja tambahan ≤60 | Fase 5 membelanjakan 42; sisanya cadangan |

Baris kredit adalah satu-satunya yang tidak bisa dinegosiasikan di tengah jalan: kredit tidak
bisa ditambah, tidak bisa dipindahkan, dan hangus di akhir event.

## Non-goal — dinyatakan, bukan didiamkan

| Yang tidak dibangun | Kenapa |
| --- | --- |
| Perencana LLM yang memutuskan apa yang menarik | Yang membuat kartu bernilai adalah ambang yang bisa diperiksa, bukan pilihan model yang tidak bisa |
| Loop belajar sebagai forward test harian | Tiap hari bursa yang dinilai menarik kredit baru. Bentuk replay-nya masuk sebagai S6 |
| Katalis cuaca, adapter BMKG/Open-Meteo | Pembeda yang manis tanpa bukti prediktif. Disimpan sebagai riset |
| Bot WhatsApp/Telegram, memori per pengguna, konfigurasi semesta | Tiga permukaan sudah lebih banyak dari yang bisa dirawat satu orang |
| Kanal harian yang mengirim ke pengguna | Mengirim berarti menjamin kartu benar tiap hari, dan itu menuntut refresh live harian |
| Eksekusi transaksi, rekomendasi, target harga, realtime intraday, portofolio | Dilarang aturan hackathon, atau bukan produk ini |

## Loop inti, dari ujung ke ujung

Satu simbol dan satu tanggal masuk; satu kartu keluar, dan tiap angka di kartu itu membawa
endpoint dan field asalnya. Tidak ada langkah di bawah ini yang memanggil API live.

1. **Pemilihan `as_of`.** Pengguna memberi simbol dan tanggal. Tanpa tanggal, dipakai hari
   terakhir yang ada di data.
2. **Pemuatan lokal.** `bag_from()` membaca tujuh dataset dari `research/harness/recorded/`
   dan memotong tiap deret pada `as_of` (`src/katalis/pillars.py:478`). Satu dataset belum
   dipotong dan itu defect terbuka — lihat Fase 0.
3. **Penolakan bernama, sebelum apa pun dihitung.** Simbol tanpa ringkasan broker ditolak
   sebagai `tanpa_broker`; baseline yang terlalu pendek ditolak sebagai `baseline_tipis`.
   Penolakan mencetak alasannya dan keluar dengan status 0, bukan traceback.
4. **Join lintas-endpoint.** `/v2/broker-summary/{symbol}/` dijoin dengan `/v2/brokers/` per
   hari untuk memberi tiap kode broker sebuah nama, bendera asing/domestik, dan kohort
   ritel/institusi/campuran. Ini pekerjaan yang tidak diberikan satu layar pun secara jadi,
   dan ia gratis: kedua payload sudah dibeli.
5. **Turunan bernama.** Di atas join berdiri HHI, pembeli efektif (1/HHI), pangsa asing,
   pangsa kohort, float terserap, harga masuk broker puncak, z robust volume terhadap baseline
   45 hari bursa, dan return residual terhadap IHSG. Tiap turunan lahir sebagai objek `Figure`
   yang menolak dibangun tanpa `(endpoint, fields)`.
6. **Ambang, bukan warna.** 18 ambang bernama memetakan turunan ke status `tenang` / `waspada`
   / `bahaya` per pilar, lalu ke satu headline kartu. Tiap ambang punya lantai, langit-langit,
   dan alasan satu kalimat (`./run.sh method`).
7. **Render dan gate.** Kartu dirender, lalu diuji: tiap angka harus dapat dilacak ke sebuah
   `Figure`, tidak boleh ada kalimat yang berbunyi nasihat, blok FIELD harus lengkap, dan
   simbol yang ditolak harus menyebutkan alasannya.
8. **Keluaran.** Satu kartu di terminal hari ini; kartu yang sama lewat
   `GET /card/{symbol}?date=` setelah Fase 2, dan halaman baca-saja setelah Fase 7.

Yang **tidak** ada di loop ini, dan itu disengaja: tidak ada panggilan jaringan, tidak ada
kunci API, tidak ada model bahasa di jalur default. `env -u SECTORS_API_KEY ./run.sh test`
tetap hijau.

## Kalimat mekanisme

**`/v2/broker-summary/{symbol}/` × `/v2/brokers/`, dijoin per hari, nol kredit tambahan.**
Kedua payload ada; tidak ada satu layar pun yang memberi gabungannya jadi. Kode menghitung,
model bahasa menerjemahkan — dan batas itu ditegakkan gate, bukan niat baik (§13 PRD,
dirangkum di `01-architecture.md`).
