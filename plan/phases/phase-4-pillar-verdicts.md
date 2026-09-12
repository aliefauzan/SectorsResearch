# Fase 4 · Pilar Katalis berhenti salah baca

## Status

| | |
| --- | --- |
| Keadaan | `[~]` dikerjakan 2026-09-12; hanya kriteria keluar 8 yang tersisa dan ia pekerjaan manusia |
| Menutup | PRD §9 baris 6 (S2 + D2) |
| Menunggu | Fase 3 — sudah `[x]` |
| Kredit Sectors | **0** — nol dibelanjakan |
| Keadaan hari ini | `./run.sh pilar LIFE 2026-09-01` → `BERGERAK TANPA PENJELASAN`, pilar Katalis `[bahaya]`. Revisi Cloud Run yang melayani masih image Fase 3 — B18 |

## Kenapa ini defect yang paling mahal untuk dibiarkan

Pilar Katalis under-warn pada persis kasus yang produk ini ada untuknya. Hari ini ia berbunyi:

```
 · KATALIS  [tenang]
   Ada kabar yang mendahului: "MSIG Life's claims total Rp545 billion, with
   a majority of death claims involving young adults" (2026-08-21).
   artikel_mendahului 2 · artikel_mengikuti 1 · filing_material 0 · aksi_korporasi 0
```

Dua artikel di dalam jendela itu adalah sebuah "Top Gainers" dan berita suspensinya sendiri.
Keduanya **melaporkan** harga yang sudah bergerak; tidak satu pun **menjelaskan** kenapa ia
bergerak. Kartu yang menyebut keduanya sebagai "kabar yang mendahului" mengatakan kepada
pembacanya bahwa geraknya punya sebab — kebalikan dari kebenarannya.

Setelah fase ini, kartu yang sama harus berbunyi **BERGERAK TANPA PENJELASAN**.

## Tugas

- [x] **1. Sambungkan `classify.py` ke `catalyst()`.**
      `artikel_mendahului` berhenti menghitung "artikel di dalam jendela lookback" dan mulai
      menghitung "artikel di dalam jendela lookback yang berlabel `menjelaskan`". Artikel
      berlabel `melaporkan` dihitung terpisah dan tetap tercetak — menyembunyikannya akan membuat
      kartu tampak seperti tidak ada berita sama sekali, dan itu juga salah.

- [x] **2. Status pilar Katalis mengikuti label, bukan jumlah.**
      Gerak yang besar tanpa satu artikel `menjelaskan` pun adalah `bahaya`, bukan `tenang`.
      Gerak yang besar dengan artikel `menjelaskan` yang mendahuluinya adalah `tenang` atau
      `waspada`, tergantung materialitasnya.

- [x] **3. Verdict kartu memuat `BERGERAK TANPA PENJELASAN`.**
      Ini verdict, bukan modifier: ia menggantikan atau mendampingi `SATU PEMBELI DOMINAN`
      menurut aturan verdict yang sudah ada, dan ia lahir dari ambang, bukan dari kalimat.

- [x] **4. `Figure` baru untuk jumlah per label.**
      `artikel_menjelaskan`, `artikel_melaporkan`. Endpoint `/v2/news/`, fields
      `(timestamp, symbols, title, tags, dimension)`. Angka lama `artikel_mendahului` dan
      `artikel_mengikuti` tetap ada atau diganti — yang tidak boleh adalah angka yang berubah
      artinya tanpa berubah nama.

- [x] **5. Kartu menyebut asal ambang.**
      PRD §7 dan §13 menyatakan kartu menyebut `shipped` atau `learned`; hari ini ia tidak
      menyebut keduanya, dan audit internal memotong nilai untuk itu.
      `thresholds.provenance()` sudah mengembalikan pasangannya; yang hilang hanya penulisannya.

- [x] **6. Gate: kartu LIFE adalah kasus uji, bukan ilustrasi.**
      Satu check yang membangun kartu `("recorded", "LIFE", "2026-09-01")` dan gagal bila verdict
      bukan `BERGERAK TANPA PENJELASAN` atau bila pilar Katalis bukan `bahaya`. Ini adalah gate
      yang mengubah kartu LIFE dari bukti naratif menjadi bukti yang diuji tiap build.

## Kriteria keluar

- [x] **1.** `cd src/katalis && ./run.sh test; echo $?` mencetak `Semua gate hijau.` dan `0`, dengan
      jumlah assertion lebih besar daripada pada akhir Fase 3 dan nol skip.
- [x] **2.** `./run.sh pilar LIFE 2026-09-01` mencetak `BERGERAK TANPA PENJELASAN` di headline dan pilar
      Katalis berstatus `bahaya`.
- [x] **3.** Kartu yang sama mencetak `artikel_menjelaskan 0` dan `artikel_melaporkan` bukan nol, dengan
      pasangan `(endpoint, field)`-nya di blok FIELD.
- [x] **4.** Kartu yang sama mencetak asal setiap ambang yang dipakainya sebagai `shipped` atau
      `learned`.
- [x] **5.** Mengubah label salah satu artikel LIFE di tabel kasus Fase 3 membuat gate baru pada tugas 6
      berubah merah.
- [x] **6.** Skrip suntikan Fase 0 kriteria 2 tetap mencetak kegagalan untuk ketiga suntikan.
- [x] **7.** `cd research/harness && python3 src/reconcile_usage.py` mencetak total portal yang sama
      persis dengan pada akhir Fase 3.
- [~] **8.** `PROGRESS.md` di-commit bersama kode, dan revisi Cloud Run baru melayani perubahan ini.
      **Terpenuhi separuh: commit ada; revisinya belum — B18, pekerjaan manusia.** `katalis-api-00003-r8l` masih image Fase 3, jadi URL publik belum menjawab
      `BERGERAK TANPA PENJELASAN` dan belum membawa header CORS.

## Bobot demo

Kriteria 2 adalah **shot terpenting di seluruh video**. Satu simbol nyata, satu tanggal nyata,
dan kartu yang mengatakan hal yang tepat: saham ini bergerak 41,7% dalam tiga hari, 65% net
belinya dari satu broker, free float 7,5%, dan tidak ada satu pun berita yang menjelaskannya.
Empat hari bursa kemudian bursa menyuspensinya.

Kalau hanya satu shot yang muat di video, shot ini yang dipakai, karena ia satu-satunya yang
menunjukkan produk melakukan pekerjaan yang ia janjikan — bukan menunjukkan bahwa produk
berjalan.

## Kalau ini melar

1. **Tugas 5** (asal ambang di kartu) dipindah ke Fase 7 dan digabung ke penulisan README.
2. **Tugas 4** menyusut menjadi satu `Figure` (`artikel_menjelaskan`) alih-alih dua, dengan
   `artikel_melaporkan` tetap tercetak sebagai catatan tanpa figure sendiri.
3. **Tugas 2** menyusut menjadi dua status, bukan tiga: `bahaya` bila nol artikel
   `menjelaskan`, `tenang` bila ada. Materialitas ditunda.

Yang **tidak** dipotong: tugas 1, 3, dan 6. Ketiganya adalah defect D2 itu sendiri. Memotong
salah satunya berarti fase ini tidak terjadi, apa pun yang tertulis di `PROGRESS.md`.
