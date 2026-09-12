# Fase 3 · Klasifikasi deterministik menjelaskan-vs-melaporkan

## Status

| | |
| --- | --- |
| Keadaan | `[x]` selesai, ter-commit, dan berjalan pada `katalis-api-00003-r8l` |
| Menutup | PRD §9 baris 5 (M9) |
| Menunggu | Fase 0 |
| Kredit Sectors | **0** |
| Kuota model | **nol** — ini justru fase yang membuat kuota model boleh habis |

## Kenapa aturan tangan lebih dulu daripada model

Karena §12.3 aturan 3: produk tidak boleh bergantung pada kuota model. D10 boleh mati,
kehabisan kredit, atau ditolak kuncinya, dan `./run.sh test` tetap hijau serta kartu tetap
terbit. Satu-satunya cara menjamin itu adalah membangun jalur deterministiknya lebih dulu dan
menjadikannya default.

Ada alasan kedua yang lebih tajam. Audit internal mencatat bahwa `CLASSIFIER=rules` "ditahan
secara hampa": suite memang hijau tanpa kunci model, tetapi **tidak ada satu baris kode pun
yang membaca `CLASSIFIER`**, jadi klaim itu belum pernah benar-benar diuji.

```bash
cd src/katalis && grep -rc CLASSIFIER *.py     # 0 di setiap berkas
```

Fase ini membuat variabel itu nyata, sehingga Fase 6 bisa menukar satu fungsi — bukan satu
arsitektur.

## Tugas

- [x] **1. Modul baru `classify.py`, murni, tanpa I/O.**
      Satu fungsi publik: artikel masuk, salah satu dari tiga label keluar — `menjelaskan`,
      `melaporkan`, `tak_terkait`. Tidak membaca berkas, tidak memanggil jaringan, tidak membaca
      lingkungan. Modul yang murni adalah modul yang bisa diuji dengan tabel kasus.

- [x] **2. Aturan, ditulis sebagai tabel, bukan sebagai rantai `if`.**
      Sinyalnya sudah ada di payload `/v2/news/`: `title`, `tags`, `dimension`, `timestamp`,
      `symbols`, `body`. Dua pola yang wajib tertangkap, karena keduanya adalah kasus yang
      membuat kartu LIFE salah baca:
      - artikel yang **melaporkan harga yang sudah bergerak** — judul bertipe "Top Gainers",
        "melonjak", "ARA", dan sejenisnya;
      - artikel yang **melaporkan tindakan bursa atas simbol itu** — berita suspensi.
      Keduanya `melaporkan`. Yang `menjelaskan` adalah artikel yang menyebut peristiwa korporasi
      atau operasional yang mendahului gerak: kontrak, akuisisi, dividen, perubahan laba, klaim
      material.

- [x] **3. `CLASSIFIER` dibaca di satu tempat.**
      Default `rules`. Nilai yang tidak dikenal ditolak dengan pesan bernama, bukan diam-diam
      jatuh ke default — jatuh diam-diam ke default adalah cara paling mudah membuat kartu
      mengklaim ia memakai model padahal tidak.

- [x] **4. Kartu menyebut classifier mana yang dipakai.**
      Sama seperti ia harus menyebut `shipped` atau `learned`. Satu baris, di dekat identitas
      kartu.

- [x] **5. Gate: tabel kasus yang dilabeli tangan.**
      Minimal kedua artikel LIFE yang ada di `research/harness/recorded/`, dengan label yang
      diharapkan tertulis di dalam test. Gate gagal kalau label berubah.

- [x] **6. Gate: produk berjalan tanpa kunci apa pun.**
      Satu check yang membangun kartu dengan seluruh variabel kunci dilepas. Ini adalah versi
      tergate dari apa yang hari ini hanya bisa diuji manual.

## Kriteria keluar

- [x] **1.** `cd src/katalis && ./run.sh test; echo $?` mencetak `Semua gate hijau.` dan `0`, dengan
      jumlah assertion lebih besar daripada pada akhir Fase 2 dan nol skip.
- [x] **2.** `env -u SECTORS_API_KEY -u ANTHROPIC_API_KEY -u OPENAI_API_KEY CLASSIFIER=rules ./run.sh test`
      mencetak `Semua gate hijau.` dan keluar 0.
- [x] **3.** `CLASSIFIER=tidak-ada ./run.sh pilar LIFE 2026-09-01` keluar dengan status bukan nol dan
      mencetak nama nilai yang tidak dikenal. Ia **tidak** diam-diam memakai `rules`.
- [x] **4.** `./run.sh pilar LIFE 2026-09-01` mencetak satu baris yang menyebut `CLASSIFIER=rules`.
- [x] **5.** Kedua artikel LIFE di jendela kartu diklasifikasi `melaporkan` oleh tabel kasus di dalam
      suite, dan gate itu gagal bila salah satu label diubah. **Tanggalnya dikoreksi:** keduanya
      berdiri berdampingan sebagai kabar yang mendahului pada kartu `2026-09-04`, bukan
      `2026-09-01`, tempat hanya satu artikel duduk di jendela.
- [x] **6.** `grep -rc CLASSIFIER src/katalis/*.py` mengembalikan hitungan bukan nol pada sedikitnya dua
      berkas.
- [x] **7.** `PROGRESS.md` di-commit bersama kode, dan revisi Cloud Run baru melayani perubahan ini.

## Bobot demo

Kriteria 2 adalah shot video, dan ia pendek: lepas semua kunci, jalankan suite, semuanya
hijau, kartu tetap terbit. Ia menjawab pertanyaan yang setiap juri punya tentang produk
ber-LLM — "apa yang terjadi kalau modelnya mati" — sebelum pertanyaan itu ditanyakan.

Perhatikan bahwa kriteria 5 **belum** mengubah bunyi kartu LIFE. Mengubahnya adalah Fase 4.
Fase ini hanya memasang mesin yang benar; fase berikutnya menyambungkannya ke verdict.

## Kalau ini melar

1. **Tugas 4** (kartu menyebut classifier) dipindah ke Fase 4, dan digabung dengan penulisan
   asal ambang `shipped`/`learned` yang juga belum terpasang.
2. **Label `tak_terkait` dipotong** menjadi dua label saja, `menjelaskan` dan `melaporkan`.
   Artikel yang tidak relevan jatuh ke `melaporkan`, yang lebih aman arahnya: ia membuat pilar
   Katalis lebih sering berbunyi "tidak ada yang menjelaskan", bukan lebih jarang.
3. **Tabel aturan dipersempit** ke dua pola wajib di tugas 2, tanpa pola `menjelaskan` yang
   lebih halus.

Yang **tidak** dipotong: tugas 3 dan tugas 6. Tanpa keduanya, §12.3 aturan 3 tetap menjadi
klaim yang tidak diuji, dan itulah persis temuan audit yang fase ini ada untuk menutupnya.
