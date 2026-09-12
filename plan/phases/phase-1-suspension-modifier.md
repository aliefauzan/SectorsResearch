# Fase 1 · Modifier suspensi sebagai `Figure`

## Status

| | |
| --- | --- |
| Keadaan | `[x]` selesai dan ter-commit — **terverifikasi lokal**, bukan terverifikasi hidup (belum ada Cloud Run; lihat `plan/README.md`) |
| Menutup | PRD §9 baris 3 (S1) |
| Menunggu | Fase 0 |
| Kredit Sectors | **0** — payload sudah di disk |
| Aset | `research/harness/recorded/v2_suspensions.json`, 20 baris, 17 simbol unik |
| Garis dasar masuk | 94 assertion di 18 fungsi check |
| Garis dasar keluar | **98 assertion di 19 fungsi check**, exit 0 |
| Diselesaikan | 2026-09-12 |

## Kenapa ini yang kedua, dan kenapa ia kecil

`/v2/suspensions/` adalah satu-satunya aset Sectors yang absen dari 28 rilis produk **dan** 39
resep dokumentasi mereka (`research/plan/gap-vs-sectors-releases.md`,
`research/evidence/sectors/release-timeline-2026-09-07.md`). The Orderbook dan Foreign Flow
sudah rilis Mei–Agustus 2026, jadi Pilar 1 sendirian berdiri di teritori yang penyelenggara
sudah kuasai. Pembeda yang tersisa harus datang dari suspensi dan dari membedakan menjelaskan
versus melaporkan — dan yang pertama berbiaya nol kredit serta muat dalam satu fase kecil.

Ia menunggu Fase 0 karena satu alasan yang sempit: modifier ini harus lahir sebagai `Figure`,
bukan sebagai tempelan string pada headline. Selama gate sitasi masih memeriksa keanggotaan
token, tempelan string akan lolos, dan kami akan menambahkan satu klaim lagi yang gate-nya
tidak menjaga.

## Tugas

- [x] **1. Pakai `normalize_suspension()` yang sudah ada.**
      `sources.py:324` sudah menormalkan satu baris suspensi menjadi `{symbol, suspension_date,
      reason, pdf_url}`. Yang belum ada adalah pemuat per simbol yang memotong pada `as_of` dan
      mengembalikan daftar suspensi **sebelum** tanggal kartu.

- [x] **2. Tambahkan suspensi ke `bag_from()`, dipotong pada `as_of`.**
      Suspensi setelah tanggal kartu adalah masa depan; memasukkannya adalah look-ahead yang
      persis sama dengan defect aksi korporasi di Fase 0. Untuk LIFE pada `as_of=2026-09-01`,
      dua suspensi yang tercatat (`2026-09-02`, `2026-09-04`) berada **setelah** tanggal itu dan
      karena itu tidak boleh muncul di kartu.

- [x] **3. Lahirkan modifier sebagai `Figure`.**
      Nama `pernah_disuspensi`, nilai jumlah suspensi sebelum `as_of`, endpoint
      `/v2/suspensions/`, fields `(symbol, suspension_date)`. Tanggal terakhirnya masuk sebagai
      catatan figure, bukan sebagai string terpisah.

- [x] **4. Cetak di headline dan di blok FIELD.**
      Headline berbunyi `… · PERNAH DISUSPENSI · <tanggal>` hanya bila nilainya lebih dari nol.
      `/v2/suspensions/ → symbol, suspension_date` muncul di blok FIELD.

- [x] **5. Gate: modifier tidak boleh melihat masa depan.**
      Satu check baru yang membangun kartu untuk sebuah simbol pada tanggal sebelum suspensinya
      dan memastikan modifier **tidak** muncul, lalu pada tanggal sesudahnya dan memastikan ia
      muncul dengan tanggal yang benar.

## Kriteria keluar

- [x] **1.** `cd src/katalis && ./run.sh test; echo $?` mencetak `Semua gate hijau.` dan `0`, dengan
      jumlah assertion lebih besar daripada pada akhir Fase 0 dan nol skip.
- [x] **2.** `./run.sh pilar LIFE 2026-09-01` **tidak** memuat `PERNAH DISUSPENSI` di headline, karena
      kedua suspensi LIFE bertanggal setelah `2026-09-01`.
- [x] **3.** `./run.sh pilar LIFE 2026-09-10` memuat `PERNAH DISUSPENSI · 2026-09-04` di headline, dan
      blok FIELD-nya memuat baris `/v2/suspensions/ → symbol, suspension_date`.
- [x] **4.** Skrip suntikan Fase 0 kriteria 2 tetap mencetak kegagalan untuk ketiga suntikan — yaitu
      modifier baru tidak melonggarkan gate sitasi.
- [x] **5.** `cd research/harness && python3 src/reconcile_usage.py` mencetak total portal yang **sama
      persis** dengan pada akhir Fase 0. Fase ini tidak membelanjakan satu kredit pun.
- [x] **6.** `plan/PROGRESS.md` di-commit bersama perubahan kode, dengan jumlah gate barunya tertulis.

## Bobot demo

Kriteria 2 dan 3 berpasangan, dan pasangan itu adalah shot video: kartu yang sama, dua tanggal,
dan modifier yang muncul hanya setelah peristiwanya benar-benar terjadi. Ia menunjukkan dua hal
sekaligus — bahwa produk memakai aset Sectors yang tidak dipakai siapa pun, dan bahwa ia tidak
curang terhadap waktu.

## Kalau ini melar

1. **Gate tugas 5** disederhanakan menjadi satu arah saja: kartu sebelum suspensi tidak memuat
   modifier. Arah sebaliknya diverifikasi manual dan dicatat di `PROGRESS.md` sebagai
   terverifikasi manual, bukan tergate.
2. **Baris `reason`** dari payload suspensi tidak masuk kartu. Hanya tanggal.

Yang **tidak** dipotong: modifier tetap lahir sebagai `Figure`, dan tetap dipotong pada
`as_of`. Kalau salah satu dari keduanya dipotong, fase ini tidak punya nilai — ia hanya
menambah satu string ke headline, dan satu string ke headline bukan pembeda.

---

## Koreksi terhadap Kriteria keluar 3

Kriteria itu ditulis dengan `2026-09-10`, dan tanggal itu **tidak bisa** dipakai. Tape broker
LIFE berakhir `2026-09-04`, jadi kartu yang lebih baru ditolak `tanpa_broker` sebelum satu
modifier pun dicapai:

```
pillars.Rejected: tanpa_broker: no broker summary on this source for this symbol
```

Penolakan itu benar — ia justru penolakan bernama yang M4 janjikan — dan ia adalah fixture yang
salah untuk pertanyaan ini. Tanggal yang menjawab pertanyaannya adalah `2026-09-04`: kedua
suspensi LIFE (`2026-09-02`, `2026-09-04`) sudah terjadi, dan tape broker masih menjangkaunya.
Gate memakai tanggal itu, dengan alasannya sebagai komentar di sebelah baris yang memilihnya.

Ini kesalahan rencana, bukan kesalahan kode, dan dicatat di sini alih-alih diam-diam diperbaiki:
berkas fase menulis tanggal tanpa memeriksanya terhadap jendela tape.

## Hasil, 2026-09-12

98 assertion hijau di 19 fungsi check, naik dari 94, exit 0. Nol kredit.

- `sources.py` — `suspensions_for(source, symbol, end=None)` di atas `normalize_suspension()`
  yang sudah ada. Ia memotong pada `end`, ascending, satu simbol.
- `pillars.py` — `suspension_history(rows, as_of)` mengembalikan `Figure("pernah_disuspensi",
  n, "/v2/suspensions/", ("symbol", "suspension_date"), note="terakhir <tanggal>")`, atau
  `None` bila simbol itu belum pernah disuspensi, sehingga kartu diam alih-alih mencetak nol.
  `verdict()` menerimanya dan menambahkan modifier hanya bila nilainya bukan nol. `assess()`
  membawanya di `result["modifier_figures"]` — figure tingkat kartu, karena ia menyitir sebuah
  modifier di headline, bukan sebuah pilar.
- `card.py` — blok FIELD mengiterasi figure pilar **dan** figure tingkat kartu, dan
  `check_field_block_is_complete` memeriksa keduanya.
- Dua gate baru menjaga arah: `check_suspension_modifier_respects_as_of` (4 assertion) menguji
  bahwa kartu `2026-09-01` tidak memuat modifier maupun figure-nya, dan bahwa kartu
  `2026-09-04` memuat keduanya dengan nilai 2 dan endpoint yang benar.
  `check_as_of_does_not_leak` diperluas ikut membandingkan `modifier_figures` antara kartu yang
  dipotong dan yang tidak.
