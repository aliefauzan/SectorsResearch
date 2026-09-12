# 99 · Naskah video juri — tiga menit, shot demi shot

Maksimum tiga menit. Bahasa Indonesia. Tidak ada musik yang menutupi suara, tidak ada animasi
transisi, tidak ada slide yang berisi klaim tanpa layar yang menunjukkannya. Setiap shot di
bawah ini adalah layar nyata dari perintah nyata; kalau sebuah shot tidak bisa direkam karena
fasenya belum selesai, shot itu **dihapus**, bukan diganti mockup.

Anggaran waktu total 180 detik. Kolom terakhir adalah kriteria keluar fase yang menghasilkan
shot itu — kalau kriterianya belum terpenuhi, shotnya belum ada.

| # | Detik | Layar | Yang diucapkan | Dari |
| --- | --- | --- | --- | --- |
| 1 | 0–15 | Satu tangkapan layar grup WhatsApp saham dengan satu ticker disebut | Masalahnya dalam satu kalimat: seseorang menyebut satu saham, dan Anda tidak punya cara menjawab siapa yang mengangkatnya | — |
| 2 | 15–30 | Terminal: `./run.sh symbols` | Produk berjalan di atas payload IDX yang benar-benar dibeli, bukan data contoh. Sembilan simbol, dan yang tidak bisa dinilai mengatakan kenapa | Fase 5 kriteria 3 |
| 3 | 30–75 | Terminal: `./run.sh pilar LIFE 2026-09-01`, kartu penuh, tahan di layar | **Shot inti.** LIFE naik 41,7% dalam tiga hari bursa. 65% net beli dari satu broker. Free float 7,5%. Dan tidak ada satu berita pun yang menjelaskannya — kartunya berbunyi BERGERAK TANPA PENJELASAN | Fase 4 kriteria 2 |
| 4 | 75–90 | `research/harness/recorded/v2_suspensions.json` di layar, baris LIFE disorot | Empat hari bursa kemudian bursa menyuspensinya. Tanggalnya ada di berkas yang sama yang dibaca kartu | Fase 1 kriteria 3 |
| 5 | 90–105 | Terminal split: suntik angka karangan ke `render()`, gate berubah merah | Tiap angka di kartu membawa endpoint dan field asalnya. Angka yang tidak punya asal tidak tercetak — dan ini gatenya, bukan janjinya | Fase 0 kriteria 2 |
| 6 | 105–125 | `./run.sh learn`, lalu satu berkas `lessons/`, lalu satu lesson yang **ditolak** karena hanya dua peristiwa mendukungnya | Agen menyapu ulang peristiwa berlabel yang sudah terjadi, menulis lesson, dan menolak menggeser ambang kalau buktinya tipis. Satu simbol ditahan dan tidak pernah dipakai belajar | Fase 6 kriteria 2 dan 5 |
| 7 | 125–140 | Cloud Build: satu commit yang merusak gate, build merah, revisi lama tetap melayani | Gate produk ini benar-benar bisa merah, dan build yang merah tidak pernah men-deploy | Fase 2 kriteria 2 |
| 8 | 140–160 | Peramban: halaman kartu, URL publik, tanpa terminal | Kartu yang sama, di URL yang bisa dibuka siapa pun | Fase 7 kriteria 1 |
| 9 | 160–175 | Terminal: `env -u SECTORS_API_KEY -u ANTHROPIC_API_KEY CLASSIFIER=rules ./run.sh test` hijau | Cabut semua kunci model dan produk tetap berjalan penuh. Model menerjemahkan; kode yang menghitung | Fase 3 kriteria 2 |
| 10 | 175–180 | Kartu, baris penyangkalan disorot | KATALIS menyatakan struktur transaksi, bukan nasihat investasi | — |

## Shot yang tidak boleh dilewat

**Shot 6 adalah shot yang membuktikan Track 01, dan ia tidak boleh dilewat selama track yang
dideklarasikan adalah Track 01.** Palang track berbunyi: proyek harus memuat orkestrasi atau
logika agen yang dibangun sendiri, dan "if the product would disappear when the team's prompt
is removed from someone else's client, it does not meet this track's bar". Yang menjawab palang
itu bukan kartu dan bukan pipeline — keduanya deterministik dan tidak melibatkan model sama
sekali. Yang menjawabnya adalah loop replay: sapuan simbol × tanggal miliknya sendiri,
penghasil lesson miliknya sendiri, dan pagar yang menolak lesson bertopang bukti tipis. Itu
orkestrasi, dan ia terlihat di layar.

Konsekuensinya harus dipegang: **kalau Fase 6 dipotong, shot 6 hilang, dan begitu shot 6 hilang
deklarasi track harus berpindah ke Track 03 sebelum submit.** Track 03 tidak mewajibkan
komponen LLM dan seluruh video lainnya tetap berlaku apa adanya. Yang tidak boleh terjadi
adalah mendeklarasikan Track 01 dengan video yang tidak memuat satu pun bukti orkestrasi;
aturan mengizinkan juri memindahkan proyek ke track yang cocok, tetapi memindahkan sendiri
lebih baik daripada dipindahkan.

**Shot 3 adalah shot yang membuktikan produknya.** Kalau video harus dipotong ke satu shot, ini
yang bertahan. Ia satu-satunya yang menunjukkan produk melakukan pekerjaan yang ia janjikan,
bukan menunjukkan bahwa produk berjalan.

## Aturan perekaman

- **Tidak ada layar yang tidak nyata.** Tiap terminal adalah perintah yang benar-benar
  dijalankan, tiap peramban adalah URL yang benar-benar hidup.
- **Tanggal terlihat.** Kartu mencetak jendelanya sendiri; jangan menutupinya dengan overlay.
- **Kunci tidak pernah di layar.** Sebelum merekam: `env | grep -i sectors` harus dijalankan di
  jendela lain, bukan di jendela yang direkam.
- **Rekam versi kasar lebih dulu**, di atas apa yang sudah berjalan hari ini, lalu ganti shot
  satu per satu saat fasenya selesai. Kriteria bernilai 30% tidak boleh bergantung pada fase
  yang belum selesai.
- **Unggah, lalu buka dari penyamaran.** Video yang tidak dapat diakses tidak dinilai.

## Versi teaser satu menit

Shot 1 (10 detik), shot 3 (25 detik), shot 4 (10 detik), shot 8 (10 detik), shot 10 (5 detik).
Tidak ada narasi mekanisme; teaser menjual masalahnya, bukan arsitekturnya.
