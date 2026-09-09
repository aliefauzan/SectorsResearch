# Red Team — Kenapa Ide Ini Bisa Kalah

> Dikuliti 9 September 2026. Ini bukan daftar risiko sopan. Ini dua belas cara ide di
> [`spec.md`](spec.md) bisa gagal, diurutkan dari yang paling dalam, plus apa yang harus ada di
> ide itu supaya masing-masing tidak terjadi.
>
> Tiga di antaranya adalah cacat konseptual yang tidak bisa diperbaiki dengan kerja lebih keras.
> Satu di antaranya adalah kontradiksi di dalam spec saya sendiri.

---

## Bagian A · Cacat konseptual — ini yang benar-benar membunuh

### A1. Tautologi momentum — **cacat paling dalam**

Suspensi cooling-down IDX dipicu oleh **aturan mekanis**: peningkatan harga kumulatif melewati
ambang tertentu dalam N hari. Aturannya publik dan deterministik.

Artinya: memprediksi "saham ini akan disuspensi cooling-down" bisa direduksi menjadi
**memprediksi saham yang sudah naik banyak akan naik lagi.** Itu detektor momentum dengan
langkah tambahan.

Juri yang tajam akan bertanya satu pertanyaan yang menghancurkan:

> *"Apa bedanya model empat sumbu kalian dengan mengurutkan saham berdasarkan kenaikan lima hari
> terakhir?"*

Kalau tidak ada jawaban berangka, seluruh klaim kedalaman teknis runtuh. Anda memprediksi
fungsi dari harga memakai harga.

**Yang harus ada:** baseline naif sebagai lawan tanding wajib. Bandingkan screen 4 sumbu vs
"lima besar kenaikan kumulatif 5 hari". **Kalau tidak mengalahkannya, Anda tidak punya produk.**
Kalau mengalahkannya, angka itu adalah judul kedalaman teknis Anda dan harus muncul di video.

Pertanyaan sesungguhnya bukan *"apakah saham ini akan disuspensi"* — itu bisa ditebak dari
harga. Pertanyaannya: **"di antara saham yang sama-sama naik tajam, mana yang naiknya
direkayasa?"** Itu yang butuh broker flow, float, dan ketiadaan katalis. Ubah pertanyaannya,
dan seluruh proyek jadi masuk akal lagi.

### A2. Base rate — presisi akan terlihat buruk, dan itu wajar

Hitungan dari data terekam: 20 suspensi terbaru mencakup 11 Ags – 4 Sep 2026 (~17 hari bursa)
→ ~1,2 suspensi/hari. Dengan `total_count` 583, riwayatnya membentang ~486 hari bursa,
**sekitar dua tahun**.

Base rate per saham per jendela 10 hari bursa, atas ~900 emiten tercatat:

```
~1,1 cooling-down/hari × 10 hari = ~11 peristiwa
11 / 900 emiten ≈ 1,2% per saham per 10 hari
```

Konsekuensinya keras: kalau screen menyalakan 30 saham dan 1 disuspensi, **presisinya 3%**.
Juri membaca itu sebagai "29 dari 30 peringatan kalian salah".

**Yang harus ada:** jangan pernah melaporkan akurasi atau presisi telanjang. Laporkan **lift**.

> *Base rate suspensi cooling-down: 1,2% per 10 hari. Di antara saham dengan 4 dari 4 sumbu
> menyala: 14%. Lift 11×.*

Lift adalah metrik yang jujur untuk peristiwa langka, dan angkanya justru mengesankan sementara
presisi terlihat memalukan. Sertakan confusion matrix penuh di repo. Juri yang paham statistik
akan lebih menghargai tim yang tahu perbedaannya daripada tim yang melaporkan "akurasi 97%"
(yang dicapai dengan tidak pernah memperingatkan apa pun).

### A3. Loop belajar tidak bisa menyala — **kontradiksi di dalam spec saya sendiri**

`spec.md` §6 mensyaratkan **N ≥ 20 peringatan selesai per sumbu** sebelum ambang bergeser.
Gabungkan dengan base rate A2:

Screen 30 saham/hari × 14 hari = 420 peringatan. Dari itu, true positive yang diharapkan:
**3 sampai 5.** Sumbu mana pun tidak akan pernah mencapai 20 peristiwa positif yang selesai
dalam masa lomba.

**Artinya threshold evolution tidak akan pernah menyala pada data forward.** Adegan video yang
saya sebut "adegan pemenang" — *ini ambang yang dia geser* — tidak akan terjadi kalau pagarnya
dipatuhi. Kalau pagarnya dilanggar demi video, Anda menunjukkan overfitting di depan juri.

**Yang harus ada:** pisahkan dua rezim secara eksplisit.

| Rezim | Sumber data | Fungsi | N tersedia |
| --- | --- | --- | --- |
| **Penyetelan** | Replay historis, walk-forward atas ~2 tahun suspensi | Di sinilah ambang bergerak | ratusan peristiwa |
| **Forward test** | 14+ hari run tanpa ditunggui | **Validasi saja, tidak pernah menyetel** | 3–5 peristiwa |

Ambang berevolusi pada set historis dengan walk-forward — itu jujur, punya N cukup, dan bisa
diaudit. Forward test membuktikan loopnya hidup dan tidak curang. Katakan pembagian ini dengan
lantang di video; kedisiplinannya justru yang bernilai.

### A4. Peringatannya datang setelah kerusakan

Retail dapat tip → beli → saham lanjut naik → IDX suspensi. Peringatan H−5 berarti saham
**sudah** naik 200%. Kalau produk dijual sebagai "peringatan dini", juri berhak bertanya dini
untuk siapa.

**Yang harus ada:** ubah janjinya dari **prediksi** menjadi **karakterisasi pada saat
keputusan**. Produk ini tidak meramal. Ia menjawab pertanyaan yang diajukan pada momen yang
tepat: *saya baru saja diberi ticker ini, apa yang datanya katakan tentang strukturnya?*

Suspensi dipakai untuk **memvalidasi** bahwa karakterisasinya benar — bukan sebagai janji
produk. Perbedaan ini kecil di kalimat, besar di penilaian.

---

## Bagian B · Asumsi data yang belum diverifikasi

### B5. Semua verifikasi dilakukan di blue chip; produknya untuk gorengan

Simbol yang benar-benar terekam di `harness/recorded/`:

```
ADRO · ANTM · ASII · BBCA · BBRI · BMRI · BREN · TLKM
```

**Delapan-delapanya saham besar.** Tidak satu pun saham lapis tiga. Sementara target produk
adalah ASLI, LIFE, NICK — jenis saham yang muncul di daftar suspensi.

Belum ada yang membuktikan `/v2/broker-summary/{symbol}/top/` mengembalikan baris berguna untuk
saham dengan nilai transaksi harian kecil. Kalau `top_buyers` kosong atau hanya berisi satu
broker untuk seluruh universe target, **sumbu konsentrasi mati** dan produk kehilangan
sumbu terpentingnya.

**Yang harus ada — kerjakan hari pertama, sebelum apa pun:** ambil 10 saham yang benar-benar
ada di daftar suspensi, panggil keempat endpoint untuk masing-masing, dan periksa apakah
datanya berguna. Biaya ~50 kredit. Kalau gagal, Anda tahu tanggal 10 September, bukan 27.

Ini uji kelayakan, bukan uji model. Ia mendahului segalanya.

### B6. Ketiadaan berita mungkin nol daya beda

Sumbu "tanpa katalis" mengasumsikan bahwa tidak adanya berita berdimensi `financials`/`future`
itu bermakna. Tapi bisa juga artinya **tidak ada yang pernah menulis tentang saham Rp50**.

Kabar baiknya, dari data terekam: satu halaman berita memuat 27 simbol berbeda termasuk nama
kecil dan menengah (SUNI, TRIN, WINR, DCII, CUAN), dan `total_count` 11.736 artikel. Jadi
cakupannya tidak murni blue chip.

Tapi itu belum membuktikan apa-apa untuk universe target.

**Yang harus ada:** ukur daya bedanya sebelum memakainya. Berapa persen saham di daftar
suspensi punya berita sama sekali? Kalau 95% tidak punya, sumbu ini konstan dan **buang**.
Sumbu yang selalu menyala bukan sinyal, ia derau yang menyamar sebagai konfirmasi.

### B7. Kedalaman backtest dibatasi kredit dan jendela 90 hari

`/v2/daily/{symbol}/` mengembalikan maksimal 90 hari per panggilan. Backtest atas peristiwa dua
tahun ke belakang butuh beberapa panggilan per simbol per peristiwa. Dengan sisa ~623 kredit,
backtest realistis hanya mencakup **peristiwa 2026**, bukan seluruh 583.

**Yang harus ada:** nyatakan batas ini di README dan di video sebelum juri menemukannya sendiri.
"Kami mem-backtest 90 peristiwa dari Januari–September 2026, dibatasi anggaran kredit" jauh
lebih kuat daripada klaim menyeluruh yang runtuh saat diperiksa.

---

## Bagian C · Posisi kompetitif

### C8. Sectors sudah menerbitkan resep yang mirip berbahaya

[GNN Anomaly Detection, bagian 1–3](https://docs.sectors.app/recipes/gnn-anomaly-detection/01-gnn-part-1) —
graf korelasi dari harga harian, skor anomali dengan graph autoencoder, lalu **dikonfirmasi
dengan broker activity dan foreign flow**.

Itu deteksi anomali yang dikonfirmasi arus broker. Sumbu 2 dan sumbu 3 Anda ada di sana. Dan
halaman track resmi menyebut resep ini sebagai **kalibrasi kedalaman yang diharapkan untuk
Track 03**.

**Yang harus ada:** satu paragraf di README dan satu kalimat di video yang menyatakan
perbedaannya secara eksplisit. Perbedaan yang sah:

- Resep itu mendeteksi anomali **statistik**; produk ini menjawab pertanyaan **pengguna** pada
  momen keputusan.
- Resep itu tidak punya **label**; produk ini divalidasi terhadap suspensi resmi IDX.
- Resep itu berjalan sekali; produk ini **mengoreksi dirinya sendiri** dan menyimpan jejaknya.

Kalau Anda tidak menyatakannya, juri yang menulis resep itu akan menyatakannya sendiri, di
kepalanya, dan tidak menguntungkan Anda.

### C9. Bandarmology bukan konsep baru di Indonesia

Stockbit dan sejumlah alat ritel sudah menampilkan broker summary. Investor Indonesia sudah
akrab dengan istilahnya. Kalau video membuka dengan "lihat, aliran broker!", itu bukan wawasan
baru bagi juri mana pun di Jakarta.

**Yang harus ada:** posisikan pembedanya bukan pada datanya, melainkan pada **konvergensi empat
saksi independen + validasi terhadap peristiwa resmi + loop koreksi diri**. Alat yang ada
menampilkan; ini menyimpulkan dan mempertanggungjawabkan.

### C10. Track-nya bisa salah, dan juri akan memindahkannya

Kalau intinya "pengguna menempel ticker", itu **on-demand**, bukan terjadwal. Track 02
mensyaratkan operasi otonom per siklus. Menempelkan watchlist terjadwal di atas produk
on-demand terbaca sebagai tambahan supaya muat, dan juri memindahkan proyek yang salah track.

Dipindah ke Track 03 berarti bersaing dengan 12 tim — dan melawan kalibrasi resep GNN.

**Yang harus ada:** putuskan sekarang, jangan di akhir.

- **Track 02** kalau inti produknya **pengawas watchlist yang memberi peringatan pada
  transisi** — saat saham *memasuki* keadaan rapuh, bukan sekadar sedang berada di dalamnya.
  Trigger transisi jauh lebih bisa dipertahankan daripada query ulang harian. Kotak paste
  ticker jadi pelengkap.
- **Track 03** kalau inti produknya profil kerapuhan itu sendiri.

Video harus memperjuangkan satu di antaranya, bukan keduanya.

---

## Bagian D · Kepatuhan dan eksekusi

### D11. Menyebut saham yang masih hidup sebagai "direkayasa"

Video publik yang menampilkan ticker nyata di sebelah kata manipulasi adalah risiko reputasi dan
hukum bagi Anda, dan risiko bagi penyelenggara yang menayangkannya. Ditambah Terms of Service
Sectors punya batasan penggunaan komersial.

**Yang harus ada:**

- Untuk demo, pakai **peristiwa historis yang sudah selesai** — saham yang sudah disuspensi, dan
  pengumuman IDX-nya sudah terbit. Faktual, bukan tuduhan.
- Bahasa **deskriptif** tanpa kecuali: "float 8%, satu broker 61% net beli, volume 8× median" —
  bukan "saham ini digoreng".
- Tidak pernah ada vonis, skor sebagai rekomendasi, atau warna merah/hijau.
- Disclaimer di layar, di README, di video.

### D12. Skop 21 hari, dan spec-nya punya 15 modul

`spec.md` mendaftar ~15 modul plus 3 tes plus loop plus permukaan output plus video. Itu banyak
untuk 21 hari, apalagi kalau tim masih satu orang.

**Yang harus ada — daftar potong yang diputuskan sekarang, bukan tanggal 28:**

| Boleh dipotong | Tidak boleh dipotong |
| --- | --- |
| Sumbu insider (`filings`) | Empat sumbu inti |
| Sonifikasi / aksesibilitas | Keempat berkas state |
| Antarmuka web (cukup Telegram + CLI) | Riwayat run scheduler |
| Normalisasi subsektor penuh | Perbandingan lawan baseline naif |
| HiveMind / generalisasi lintas subsektor | Uji kelayakan gorengan (B5) |
| Threshold evolution otomatis penuh | Backtest berlabel + angka lift |

Kalau harus memilih satu hal untuk dikorbankan lebih dulu: **antarmuka**. Juri menonton video,
bukan memakai aplikasi Anda.

---

## Ringkasan: enam hal yang harus ada, atau ide ini tidak menang

1. **Perbandingan lawan baseline naif** (momentum 5 hari). Tanpa ini, A1 membunuh Anda.
2. **Metrik lift dengan base rate dinyatakan**, bukan akurasi atau presisi telanjang.
3. **Pemisahan rezim penyetelan (historis, walk-forward) dan forward test (validasi saja)**.
4. **Uji kelayakan data di saham gorengan, hari pertama.** ~50 kredit. Ini gerbang paling awal.
5. **Pembeda eksplisit dari resep GNN Sectors sendiri**, di README dan di video.
6. **Keputusan track sekarang**, dan video yang memperjuangkan satu track saja.

Empat pertama adalah kerja teknis yang bisa gagal dan memberi tahu Anda lebih awal. Dua terakhir
adalah kalimat yang butuh sepuluh menit dan menyelamatkan tiga puluh persen nilai.

## Pertanyaan yang harus bisa dijawab sebelum menulis kode

- Apakah `/v2/broker-summary/{symbol}/top/` mengembalikan data berguna untuk saham lapis tiga?
- Berapa persen saham dalam daftar suspensi punya berita sama sekali?
- Berapa lift screen 4 sumbu dibanding sekadar mengurutkan kenaikan 5 hari?
- Berapa base rate suspensi cooling-down yang sebenarnya, dihitung dari 583 baris, bukan
  diperkirakan dari 20?

Empat pertanyaan, ~60 kredit, dua hari. Jawabannya menentukan apakah tiga minggu berikutnya
layak dijalankan.
