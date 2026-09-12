# Fase 0 · Fondasi — gate yang benar-benar menjaga

## Status

| | |
| --- | --- |
| Keadaan | `[~]` selesai kecuali `README.md` tingkat repo, yang dipindah ke Fase 7 lewat bagian Kalau Ini Melar |
| Menutup | PRD §9 baris 1 (D1 + D3), baris 2 (M6), ditambah tiga defect dari JURI-v9 |
| Menunggu | tidak ada |
| Kredit Sectors | **0** |
| Garis dasar masuk | `./run.sh test` → 73 assertion di 18 fungsi check, exit 0 |
| Garis dasar keluar | `./run.sh test` → **94 assertion** di 18 fungsi check, exit 0 |
| Diselesaikan | 2026-09-12 |

## Kenapa ini lebih dulu daripada apa pun

Selama gate sitasi bocor, tiap fitur baru menumpuk di atas klaim yang belum benar. Klaim itu
bukan klaim kecil: "tiap angka membawa sitasinya" adalah satu-satunya alasan seseorang boleh
mempercayai kartu ini, dan ia adalah satu-satunya gate yang akan menahan keluaran model kalau
Fase 6 masuk. Memperbaikinya setelah Fase 6 berarti memperbaikinya di bawah beban.

Dua defect tambahan dari audit internal masuk ke fase yang sama karena keluarganya sama —
gate yang hijau tanpa menguji apa pun: berkas ambang hasil belajar yang tidak pernah dibaca
gate-nya, dan satu angka kartu yang bisa lahir dari tanggal setelah `as_of`.

M6 (kebersihan repo) ikut di sini karena ia prasyarat keras Fase 2: tanpa kode di repo, tidak
ada trigger build. Sebagian besarnya sudah selesai dan tinggal diverifikasi ulang, bukan
dikerjakan.

## Tugas

- [x] **1. Tutup D1 — gate sitasi menguji asal, bukan keanggotaan token.**
      Bangun kartu dari daftar `Figure` di satu fungsi render, lalu bandingkan token angka pada
      kartu terhadap himpunan token yang **fungsi itu sendiri** hasilkan. Hari ini `card.py:174`
      memeriksa `if token not in allowed`, dan `allowed` adalah gabungan semua note, unit, dan
      headline — itulah sebabnya `0.53` dan `2.32` lolos.

- [x] **2. Tutup D3 — `DEMO_CASES` memuat kasus recorded.**
      `pillars.py:38` hari ini berbunyi `DEMO_CASES = (("synth", "KVDN", "2026-09-04"),)`, dan
      keempat gate di `card.py` memakai `DEMO_CASES[0]`. Tambahkan `("recorded", "LIFE", "2026-09-01")`.
      Datanya sudah di disk; nol kredit. Perhatikan bahwa gate `card.py` memakai `DEMO_CASES[0]`
      secara harfiah — mengubah tuple saja tidak cukup, gate harus mengulangi seluruh tuple.

- [x] **3. Tutup lubang ambang hasil belajar.**
      `check_learned_cannot_escape()` (`thresholds.py:138`) hanya menguji aritmetika `clamp()` dan
      tidak pernah membuka `state/thresholds.learned.json`. Buat ia membaca `_learned()` dan
      **gagal** bila ada nilai yang berbeda dari hasil `clamp()`-nya sendiri. Nilai di luar batas
      harus ditolak dengan nama berkas dan nama ambangnya, bukan diam-diam diperbaiki.

- [x] **4. Tutup look-ahead pada aksi korporasi.**
      `bag_from()` (`pillars.py:498`) memuat `actions` tanpa `upto(..., as_of)`, dan `catalyst()`
      memilih `a["date"] >= start`. Potong `actions` pada `as_of`. Perhatikan bentuk payloadnya:
      `corporate_actions` adalah dict berkunci jenis aksi dengan nama tanggal berbeda per jenis
      (`agm_date`, dan seterusnya), jadi `upto()` untuk deret harian tidak langsung berlaku —
      lihat `02-data-model.md`.

- [x] **5. Perluas `check_as_of_does_not_leak` ke semua figure.**
      Hari ini ia menguji satu figure (`volume_z`) pada satu simbol sintetis dan menghitung 1
      assertion. Ia harus membandingkan **setiap** figure pada kartu antara sumber penuh dan
      sumber yang sudah dipotong, untuk tiap entri `DEMO_CASES`.

- [x] **6. Tutup D4 — satu kata di catatan `baseline_days`.**
      Catatannya menulis "caps at 90 days" tanpa menyebut kalender. Tulis "90 hari kalender ≈ 62
      hari bursa". `/v2/daily/` memotong ke 90 hari kalender, dan itulah sebabnya LIFE memberi 62
      baris, bukan 90.

- [~] **7. Verifikasi ulang M6, jangan mengerjakan ulang.**
      `src/katalis/` sudah terlacak sejak commit `1a439e6`, `.env` sudah diabaikan, dan tidak ada
      `__pycache__` terlacak. Yang perlu dilakukan hanya memastikan itu masih benar pada akhir
      fase, dan menambahkan `README.md` tingkat repo kalau belum ada — hari ini `ls README.md`
      mengembalikan `No such file or directory`.

## Kriteria keluar

- [x] **1.** `cd src/katalis && ./run.sh test; echo $?` mencetak `Semua gate hijau.` dan `0`, dengan
      jumlah assertion **lebih besar** dari 73 dan nol skip.
- [x] **2.** Skrip berikut mencetak kegagalan, bukan `[]`, untuk ketiga suntikan:
      ```bash
      cd src/katalis && python3 - <<'PY'
      import card
      orig = card.render
      for bad in ["rasio utang terhadap ekuitas 0.53, margin 2.32%", "float 15 persen", "target harga 987654321"]:
          card.render = lambda *a, **k: orig(*a, **k) + "\n" + bad
          print(bad, "->", card.check_every_number_is_a_figure()[0])
      PY
      ```
- [x] **3.** `python3 -c "import sys;sys.path.insert(0,'src/katalis');import pillars;print(pillars.DEMO_CASES)"`
      memuat `("recorded", "LIFE", "2026-09-01")`, dan `./run.sh test` menampilkan blok bukti
      `check_verdict_is_never_advice` untuk LIFE serta KVDN.
- [x] **4.** Menulis `{"values":{"top1_dominant":0.99}}` ke `src/katalis/state/thresholds.learned.json`
      membuat `./run.sh test` keluar dengan status **1** dan mencetak nama berkas serta nama
      ambangnya. Menghapus berkas itu mengembalikan suite ke hijau.
- [x] **5.** Menyuntikkan satu aksi korporasi bertanggal `2026-12-31` ke sumber untuk kartu
      `as_of=2026-09-01` **tidak** mengubah `aksi_korporasi`, dan `check_as_of_does_not_leak`
      menghitung lebih dari 1 assertion.
- [x] **6.** `./run.sh method | grep baseline_days` menyebut "hari kalender" dan "hari bursa" dalam satu
      baris.
- [x] **7.** `git ls-files | grep -E '\.env|__pycache__'` hanya mengembalikan `.env.example`, dan
      `git status --porcelain` kosong setelah commit terakhir fase ini.
- [x] **8.** `plan/PROGRESS.md` di-commit dalam commit yang sama dengan perubahan `src/katalis/`, dengan
      jumlah gate barunya tertulis.

## Bobot demo

Kriteria 2 dan 4 adalah shot video. Suntikkan angka karangan ke kartu di depan kamera, lalu
tunjukkan gate berubah merah. Ini satu-satunya cara menunjukkan bahwa "tiap angka membawa
sitasinya" adalah mekanisme, bukan slogan — dan ia langsung menjawab kriteria kedalaman
teknis 30% yang berbunyi "tidak dipalsukan untuk demo".

## Kalau ini melar

Yang dipotong, berurut:

1. **Tugas 5** (perluasan `check_as_of_does_not_leak` ke semua figure) turun menjadi: uji semua
   figure pada **satu** entri `DEMO_CASES`, bukan semua entri.
2. **Tugas 6** (D4, satu kata) dipindah ke Fase 7 dan digabung ke penulisan README.
3. **Tugas 7** bagian `README.md` tingkat repo dipindah ke Fase 7.

Yang **tidak** dipotong di dalam fase ini: tugas 1, 2, 3, dan 4. Keempatnya adalah gate yang
hijau tanpa menguji apa pun, dan membiarkan satu saja berarti seluruh angka "gate hijau" di
fase berikutnya tidak menyatakan apa-apa.

---

## Hasil, 2026-09-12

94 assertion hijau di 18 fungsi check, naik dari 73, exit 0. Empat gate yang sebelumnya hijau
tanpa menguji apa pun kini bisa merah, dan ketiganya dibuktikan merah dengan serangan yang sama
yang menembusnya kemarin.

Yang berubah di kode:

- `card.py` — `render()` dipecah menjadi `_render()` yang mengembalikan `(teks, Counter)`.
  Tiap baris kartu ditulis lewat `put()`, yang menghitung token angka di baris itu saat ia
  ditulis. Gate membandingkan **multiset** token pada kartu terhadap multiset yang fungsi render
  itu sendiri keluarkan, bukan terhadap gabungan semua note, unit, headline dan ambang. Tabrakan
  token tidak lagi menolong penyerang: angka yang bertabrakan menaikkan hitungannya, dan
  hitungan yang berubah adalah gate merah. Keempat gate kartu kini mengulangi seluruh
  `DEMO_CASES`, bukan `DEMO_CASES[0]`.
- `pillars.py` — `DEMO_CASES` memuat `("recorded", "LIFE", "2026-09-01")`. `bag_from()` menerima
  `cut=False` yang membangun bag yang sama tanpa satu pun pemotongan as-of; hanya gate yang
  memakainya. `actions` kini melewati `upto()`, dan `catalyst()` memilih dari jendela alih-alih
  dari masa depan. `check_as_of_does_not_leak` membangun tiap kartu demo dua kali dan menuntut
  **tiap** figure identik, bukan hanya `volume_z` pada satu simbol sintetis.
- `thresholds.py` — `check_learned_cannot_escape()` membuka
  `state/thresholds.learned.json` dan gagal untuk nama yang tidak ada di tabel, nilai bukan
  angka, dan nilai yang berbeda dari hasil `clamp()`-nya sendiri. Nilai yang perlu dijepit
  sekarang ditolak, bukan diam-diam diperbaiki. Catatan `baseline_days` menyebut hari kalender
  dan hari bursa.

Yang **tidak** ditutup, dan dicatat apa adanya: angka di dalam **headline pilar** masih bisa
berupa pembulatan yang berbeda dari figure-nya sendiri — kartu LIFE menulis `65%` di headline
sementara figure-nya `64.7%`, dan `2.2` sementara figure-nya `2.17`. Gate baru menerima keduanya
karena renderer memang mengeluarkan keduanya. Menuntut headline memakai angka figure apa adanya
berarti mengubah format headline di keempat pilar, dan itu pekerjaan Fase 4, bukan Fase 0.
Dicatat sebagai B14 di `plan/PROGRESS.md`.
