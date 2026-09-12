# Fase 6 · Loop belajar replay, lalu jalur model

## Status

| | |
| --- | --- |
| Keadaan | `[ ]` belum dikerjakan |
| Menutup | PRD §9 baris 8 (S6) lalu baris 9 (S7) |
| Menunggu | Fase 5 (korpus) dan Fase 4 (pilar Katalis yang benar) |
| Kredit Sectors | **0** — label dan payload sudah di disk |
| Kuota model | dibayar dari sisa trial GCP; **tidak ada Always Free untuk Vertex AI** |
| Bisa dipotong | **ya — ini potongan pertama di garis potong** |

## Kenapa ia menunggu Fase 4, bukan hanya Fase 5

Lesson yang dihasilkan di atas pilar Katalis yang salah baca adalah lesson yang salah. Selama
kartu LIFE berbunyi `tenang` pada hari sebelum suspensi, loop yang menilai kartu terhadap
label akan menyimpulkan bahwa ambangnya terlalu ketat — kesimpulan yang benar secara
aritmetika dan salah secara sebab. Urutan ini bukan kerapian; ia satu-satunya urutan yang
menghasilkan lesson yang berarti.

## Kenapa replay, bukan forward test

Forward test menunggu hari bursa lewat, dan tiap hari yang dinilai menarik kredit baru untuk
data harinya. Label tidak harus datang dari masa depan: `v2_suspensions.json` memuat 20 baris
suspensi atas 17 simbol unik, sudah di disk, nol kredit. Peristiwa yang harus diprediksi kartu
**sudah terjadi dan sudah berlabel**.

Mesinnya sudah setengah terpasang: `clamp()` dengan lantai dan langit per ambang,
`state/thresholds.learned.json` sebagai sumber nilai hasil belajar, `provenance()` yang
membuat kartu bisa menyebut `shipped` atau `learned`, dan — setelah Fase 0 — gate yang
benar-benar membaca berkas itu. Yang hilang satu bagian: penghasil lesson.

## Tugas — bagian A, `katalis-learn` (S6)

- [ ] **1. `learn.py`: sapuan replay simbol × tanggal.**
      Untuk tiap simbol berlabel di korpus, untuk tiap tanggal dalam jendela sebelum
      peristiwanya, bangun kartu dan catat verdictnya. Nol kredit: semuanya dari disk.

- [ ] **2. Hit versus false alarm, dihitung, bukan diperkirakan.**
      Hit adalah verdict tinggi yang mendahului peristiwa berlabel di dalam jendela yang
      ditentukan. False alarm adalah verdict tinggi yang tidak mendahului apa pun. Kebisingan
      adalah rasio kedua terhadap jumlah verdict tinggi, dan §5 menargetkan ≤40%.

- [ ] **3. Penghasil lesson, menulis ke `lessons/*.json`.**
      Satu lesson memuat: peristiwa yang mendasarinya, ambang yang disarankan bergerak, arah, dan
      berapa peristiwa yang mendukung arah itu.

- [ ] **4. Pagar, karena enam peristiwa bukan populasi.** Keempatnya wajib, dan masing-masing
      tergate:
      - satu lesson hanya boleh menggeser ambang bila **≥3 peristiwa** mendukung arah yang sama;
      - **satu simbol ditahan sebagai hold-out** dan tidak pernah dipakai menghasilkan lesson;
      - lesson tetap ditulis walau ambang **tidak** bergerak — nol perubahan yang dijelaskan
        adalah hasil, bukan kegagalan;
      - `clamp()` tetap satu-satunya jalan masuk, dan gate Fase 0 yang membaca berkas learned
        tetap gate build.

- [ ] **5. `katalis-learn` sebagai Cloud Run job (D9).**
      Menulis `lessons/*.json` dan usulan ambang ke bucket. Nol kredit — ia hanya membaca yang
      sudah di disk.

## Tugas — bagian B, `CLASSIFIER=llm` (S7)

- [ ] **6. Tukar satu fungsi, bukan satu arsitektur.**
      `classify.py` dari Fase 3 sudah punya satu titik masuk. `CLASSIFIER=llm` menukar
      implementasinya; segala hal lain tidak berubah.

- [ ] **7. Batas §13 ditegakkan gate, bukan niat baik.**

      | Model boleh | Model tidak boleh, dan gate-nya |
      | --- | --- |
      | Mengklasifikasi satu artikel: `menjelaskan` / `melaporkan` / `tak_terkait` | Menghitung angka apa pun. Tiap angka lahir sebagai `Figure`; gate sitasi menolak angka tanpa asal |
      | Menulis ulang kartu jadi paragraf yang terbaca orang | Menyebut angka yang tidak ada di objek `Figure` kartu itu. Keluaran model melewati gate sitasi yang sama |
      | Menulis lesson jadi kalimat manusia | Memilih ambang, menggeser ambang, atau memanggil `clamp()` |
      | Mengusulkan simbol untuk dilihat orang | Memutuskan verdict. Verdict keluar dari kode deterministik, selalu |

- [ ] **8. Kunci model di Secret Manager, bukan di mana pun yang lain.**
      Satu secret tambahan, satu versi aktif. Batas Always Free Secret Manager adalah 6 versi
      secret aktif per bulan; dua secret aktif masih jauh di bawahnya.

## Kriteria keluar

- [ ] **1.** `cd src/katalis && ./run.sh test; echo $?` mencetak `Semua gate hijau.` dan `0`, dengan
      jumlah assertion lebih besar daripada pada akhir Fase 5 dan nol skip.
- [ ] **2.** `./run.sh learn` menghasilkan **≥6 berkas** di `lessons/`, masing-masing menyebutkan
      peristiwa yang mendasarinya.
- [ ] **3.** Kebisingan yang dihitung sapuan — false alarm dibagi jumlah verdict tinggi — tercetak
      sebagai satu angka, dan angka itu **≤40%** atau `PROGRESS.md` menyebutkan angkanya apa
      adanya beserta alasannya.
- [ ] **4.** Simbol hold-out tidak muncul di satu pun berkas `lessons/`. Satu gate memastikannya, dan
      gate itu berubah merah bila hold-out dimasukkan.
- [ ] **5.** Sebuah lesson yang hanya didukung dua peristiwa **tidak** menggeser ambang, dan gate
      membuktikan itu dengan kasus uji yang sengaja dibuat.
- [ ] **6.** `cat src/katalis/state/thresholds.learned.json` ada dan dapat dibaca; `./run.sh method`
      menyebut tiap ambang sebagai `shipped` atau `learned`, dan jumlah masing-masing tertulis di
      `PROGRESS.md`. **Kalau semuanya tetap `shipped`, itu ditulis apa adanya beserta lessons
      yang menjelaskan kenapa.**
- [ ] **7.** `env -u ANTHROPIC_API_KEY -u OPENAI_API_KEY -u GOOGLE_API_KEY CLASSIFIER=rules ./run.sh test`
      tetap hijau dan kartu tetap terbit — §12.3 aturan 3 masih benar setelah bagian B masuk.
- [ ] **8.** `CLASSIFIER=llm ./run.sh pilar LIFE 2026-09-01` menerbitkan kartu yang verdict dan seluruh
      angkanya **identik** dengan `CLASSIFIER=rules`, kecuali baris yang menyebut classifier mana
      yang dipakai. Perbandingannya dengan `diff`.
- [ ] **9.** `cd research/harness && python3 src/reconcile_usage.py` mencetak total portal yang sama
      persis dengan pada akhir Fase 5.
- [ ] **10.** `PROGRESS.md` di-commit bersama kode, dan revisi Cloud Run baru melayani perubahan ini.

Kriteria 8 layak dibaca dua kali. Ia menuntut model **tidak mengubah apa pun yang berupa
angka**. Kalau `CLASSIFIER=llm` mengubah sebuah verdict pada LIFE, itu bukan perbaikan — itu
bukti bahwa model menyentuh sesuatu yang seharusnya deterministik, dan fase ini tidak selesai.
(Bila model mengubah **label artikel**, verdict boleh ikut berubah — tetapi perubahan itu harus
tampak sebagai perubahan label di kartu, bukan sebagai angka yang bergeser tanpa penjelasan.)

## Bobot demo

Kriteria 2, 5, dan 6 adalah satu shot: lessons yang lahir dari peristiwa nyata, satu lesson
yang **ditolak** karena hanya dua peristiwa mendukungnya, dan tabel ambang yang menyebut mana
yang `shipped` dan mana yang `learned`. Loop yang jujur tentang nol perubahan lebih berguna
daripada loop yang mengarang lima, dan menunjukkan penolakan di depan kamera adalah cara
tercepat membuktikan bahwa pagar itu ada.

Fase ini juga yang memenuhi palang Track 01 — orkestrasi milik sendiri ditambah komponen
model. Lihat `03-hackathon-compliance.md`.

## Kalau ini melar

Fase ini **adalah** potongan pertama di garis potong repo, dan pemotongannya berurut:

1. **Bagian B seluruhnya (S7).** `CLASSIFIER=llm` dipotong; `rules` tetap satu-satunya jalur.
   Konsekuensinya bukan teknis melainkan administratif: tanpa komponen model, deklarasi track
   berpindah dari Track 01 ke Track 03 sebelum submit.
2. **D9 sebagai Cloud Run job.** `katalis-learn` tetap ada sebagai perintah CLI; hanya
   penjadwalannya di GCP yang dipotong.
3. **Bagian A seluruhnya (S6).** Metrik §5 baris "loop hidup" menjadi nol, dan `PROGRESS.md`
   menandainya `[~]` dengan alasan di baris yang sama. Track berpindah ke 03.

Yang **tidak** dipotong bila bagian A dikerjakan sama sekali: keempat pagar di tugas 4.
Loop tanpa pagar di atas enam peristiwa adalah pencocokan yang menyebut dirinya belajar, dan
itu lebih buruk daripada tidak punya loop — ia adalah klaim yang audit mana pun akan robek.
