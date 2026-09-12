# Fase 7 · Permukaan baca dan submission

## Status

| | |
| --- | --- |
| Keadaan | `[ ]` belum dikerjakan |
| Menutup | PRD §9 baris 10 (S5) dan baris 11 (S4), ditambah seluruh daftar submission |
| Menunggu | Fase 4 dan Fase 6; S5 secara teknis hanya menunggu Fase 2 |
| Kredit Sectors | **0** |
| Bisa dipotong | **tidak** — video bernilai 30% dan submission tidak lengkap gagal di kelayakan |

## Kenapa dokumen ditulis paling akhir

Supaya dokumen tidak mendahului produk. Ini proyek yang sudah menulis sembilan PRD dan satu di
antaranya mengutip `cat` atas berkas yang tidak pernah ada. README yang ditulis sebelum kartu
berbunyi benar akan menjelaskan kartu yang tidak ada, dan itu adalah kegagalan yang paling
mahal di tabel kejujuran batas.

Satu pengecualian: video kasar. Rekam versi tiga menit **sekarang**, di atas apa yang sudah
berjalan, lalu perbaiki. Kriteria bernilai 30% tidak boleh bergantung pada fase-fase yang
belum selesai.

## Tugas

- [ ] **1. Halaman baca-saja (S5, D8).**
      Statis, memanggil `katalis-api`, tanpa kunci, tidak menghitung apa pun sendiri. CLI tetap
      permukaan utama; halaman menambah, bukan menggantikan. Vercel Hobby melarang pemakaian
      komersial dan tidak menerima repo milik organisasi Git — repo ini milik akun pribadi, jadi
      aman hari ini; kalau salah satunya berubah, tugas ini dipotong.

- [ ] **2. README tingkat repo.**
      Hari ini tidak ada: `ls README.md` mengembalikan `No such file or directory`. Ia harus
      memuat, apa adanya: apa produknya, satu kartu contoh lengkap, cara menjalankannya dalam
      satu perintah, **n peristiwa yang dipakai loop belajar**, berapa ambang `shipped` versus
      `learned`, dan apa yang produk ini tidak periksa.

- [ ] **3. Halaman metode masuk README apa adanya.**
      `./run.sh method` sudah mencetak 18 ambang dengan lantai, langit-langit, dan alasan, plus
      blok `ALASAN SEBUAH SIMBOL DITOLAK`. Salin keluarannya, jangan tulis ulang — keluaran yang
      disalin tidak bisa menyimpang dari kode.

- [ ] **4. Tiga percakapan pengguna.**
      Metrik §5: tiga dari tiga orang menyebut isi kartu tanpa dipandu. Ini satu-satunya bukti
      untuk bagian hipotesis §4 yang masih hipotesis — bahwa pengguna membuka kartu sebelum
      membeli, bukan sesudah. Catat apa yang mereka sebut lebih dulu, apa yang mereka salah baca,
      dan apa yang mereka tanyakan.

- [ ] **5. Video juri ≤3 menit.**
      Naskah shot demi shot ada di `99-demo-script.md`. Unggah, lalu **buka tautannya dari
      penyamaran** untuk memastikan ia dapat diakses. Video yang tidak dapat diakses tidak
      dinilai — itu aturan tertulis, bukan risiko.

- [ ] **6. Video teaser 1 menit.**
      Rekaman layar produk yang berjalan, terbit publik di YouTube atau media sosial.

- [ ] **7. Post media sosial yang menandai akun Sectors resmi.**
      Syarat submission yang terdaftar. Ia tidak punya ketergantungan teknis dan ia adalah
      penyebab gagal yang paling murah.

- [ ] **8. Repo publik, dan tetap publik ≥90 hari setelah pengumuman.**
      Pindai riwayat, bukan hanya working tree, untuk kunci. Putuskan satu repo yang dikirim;
      lihat `03-hackathon-compliance.md` bagian "Dua repo, satu submission".

- [ ] **9. Submit terakhir.**
      Repo dan aplikasi membeku saat submit. Tidak ada commit, push, atau perbaikan bug setelah
      itu. Submit saat selesai, bukan saat gugup.

## Kriteria keluar

- [ ] **1.** Halaman baca-saja dapat dibuka dari peramban, menampilkan kartu untuk sedikitnya tiga
      simbol, dan `curl -s <halaman>` tidak memuat nilai kunci apa pun.
- [ ] **2.** `README.md` ada di akar repo dan memuat satu kartu contoh yang **byte-identik** dengan
      keluaran `./run.sh pilar <simbol> <tanggal>` pada revisi yang ter-commit.
- [ ] **3.** `README.md` menyebut n peristiwa loop belajar apa adanya, dan menyebut berapa dari 18
      ambang `shipped` dan berapa `learned`.
- [ ] **4.** Tabel 18 ambang di README identik dengan keluaran `./run.sh method`.
- [ ] **5.** Tiga catatan percakapan ada di repo, masing-masing menyebut apa yang disebut pengguna lebih
      dulu tanpa dipandu.
- [ ] **6.** Tautan video juri terbuka dari penyamaran, durasinya ≤3 menit, dan memuat shot yang
      `99-demo-script.md` tandai tidak boleh dilewat.
- [ ] **7.** Tautan video teaser terbuka dari penyamaran dan durasinya ≤1 menit.
- [ ] **8.** Post media sosial terbit dan menandai akun Sectors resmi.
- [ ] **9.** Repo publik; `git log -p | grep -c "<nilai kunci>"` mengembalikan 0 di seluruh riwayat.
- [ ] **10.** Keenam item daftar submission terisi di portal, dan track yang dideklarasikan cocok dengan
       apa yang benar-benar ada di repo — Track 01 bila Fase 6 selesai, Track 03 bila tidak.
- [ ] **11.** `./run.sh test` hijau pada commit terakhir sebelum submit, dan `PROGRESS.md` menyatakan
       jumlah gate akhirnya.

## Bobot demo

Seluruh fase ini adalah bobot demo. 30% dari nilai ada pada video, dan 40% pada kegunaan nyata
— yang dibaca dari halaman, README, dan tiga percakapan itu, bukan dari kode.

## Kalau ini melar

1. **Halaman Vercel (tugas 1).** SHOULD, dan PRD §10 sudah menyiapkan pemotongannya. Cloud Run
   tetap permukaan yang bisa dicapai juri.
2. **Video teaser (tugas 6)** direkam sebagai potongan 60 detik dari video juri, bukan sebagai
   rekaman terpisah.
3. **Tiga percakapan (tugas 4)** turun menjadi satu, dan `PROGRESS.md` menyebut n-nya satu
   alih-alih tiga. Metrik §5 baris "terbaca tanpa dipandu" ditandai tidak terpenuhi, bukan
   ditandai terpenuhi dengan n yang berbeda.

Yang **tidak** dipotong: tugas 5, 7, 8, dan 9. Keempatnya adalah syarat kelayakan, bukan nilai.
Melewatkan salah satunya membuat seluruh pekerjaan enam fase sebelumnya tidak dinilai.
