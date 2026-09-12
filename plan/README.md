# plan/ — rencana implementasi KATALIS

Dokumen, bukan kode. Direktori ini menerjemahkan `katalis-v9.prd.md` menjadi delapan fase
yang bisa dijalankan satu per satu, dan menyatakan apa yang harus terlihat sebelum sebuah
fase boleh disebut selesai.

## Aturan masuk

Buka **[`PROGRESS.md`](PROGRESS.md) lebih dulu, selalu.** Ia satu-satunya berkas di sini yang
menyatakan keadaan nyata: fase yang sedang berjalan, revisi Cloud Run yang melayani, jumlah
gate hijau, sisa kredit, dan apa yang terverifikasi hidup versus terverifikasi lokal versus
sekadar diklaim. Berkas lain menyatakan rencana; hanya `PROGRESS.md` yang menyatakan kenyataan.

Kalau yang Anda cari adalah **apa yang harus Anda sendiri kerjakan** — membuat proyek GCP,
mengambil ekspor portal, merekam video, menekan submit — buka [`TODO.md`](TODO.md).
Berkas itu memuat hanya baris yang seorang agen tidak bisa selesaikan sendiri.

Setelah itu baca `README.md` ini, lalu berkas fase yang ditunjuk `PROGRESS.md`, lalu **hanya
bagian** `01-architecture.md` dan `02-data-model.md` yang berkas fase itu rujuk. Jangan membaca
seluruh direktori sebelum bekerja; itu menghabiskan konteks pada bagian yang tidak dipakai.

## Di repo mana rencana ini hidup, dan kenapa

Rencana ini ditulis di `/Users/af/dumpProject/Sectors` — repo yang memuat `src/katalis/`,
`research/harness/recorded/`, `.gitignore`, dan riwayat git. PRD dan berkas penilaian juri
hidup di repo lain, `/Users/af/dumpProject/SectorsHackathon`, yang melacak 14 berkas dan
seluruhnya `.md`:

```bash
git -C /Users/af/dumpProject/SectorsHackathon ls-files | wc -l    # 14
git -C /Users/af/dumpProject/Sectors ls-files src/katalis          # 6 berkas
```

Rencana ditaruh bersama kode karena salah satu aturannya adalah "perbarui rencana di commit
yang sama dengan kode", dan aturan itu mustahil kalau keduanya berada di dua repo. Pemisahan
dua repo itu sendiri adalah blocker terbuka — lihat baris B2 di `PROGRESS.md`.

## Peta direktori

| Berkas | Menjawab |
| --- | --- |
| `PROGRESS.md` | Di mana kita sekarang, apa tugas berikutnya, apa yang memblokir |
| `TODO.md` | **Hanya** pekerjaan manusia: konsol GCP, portal Sectors, akun pihak ketiga, kamera, orang. Pekerjaan kode tidak pernah masuk ke sini |
| `00-prd.md` | Masalah, pengguna, hipotesis, kriteria sukses, non-goal, loop inti dari ujung ke ujung |
| `01-architecture.md` | Bentuk sistem, lapisan, katalog modul, empat pilar, topologi deploy D1–D10, pengurangan lingkup yang disengaja, risiko |
| `02-data-model.md` | Bentuk payload per endpoint dengan nama field terverifikasi, objek `Figure`, kontrak kartu, state machine, tabel ambang |
| `03-hackathon-compliance.md` | Keterlacakan aturan: kelayakan, code freeze, kredit, palang track, tiga bobot penilaian dan artefak mana yang menjawab masing-masing |
| `04-observability.md` | `plans.jsonl`, `_ledger.jsonl`, keluaran gate, jejak per kartu, apa yang diperiksa saat sebuah kartu salah, dan apa yang tidak dibangun |
| `99-demo-script.md` | Video juri tiga menit, shot demi shot |
| `phases/phase-0…7` | Delapan fase, masing-masing dengan Status, Tugas, Kriteria Keluar, Bobot Demo, dan Kalau Ini Melar |
| `inputs/README.md` | Dari mana payload terekam berasal, mana yang hidup dan mana yang replay, dan apa yang tidak boleh diasumsikan pembaca tentangnya |
| `RUN-PHASE-PROMPT.md` | Prompt penjalan satu fase; satu blok tempel-salin, hanya baris `PHASE:` yang berubah |

## Semantik kotak centang — tiga keadaan, hanya tiga

| Tanda | Arti |
| --- | --- |
| `[ ]` | Belum dikerjakan |
| `[x]` | Selesai, **ter-commit**, **dan** berjalan di Cloud Run pada revisi yang benar-benar melayani |
| `[~]` | Sengaja dilewati, dengan alasannya di baris yang sama |

`[x]` menuntut revisi yang ter-deploy karena kartu yang hanya terbit di laptop bukan kartu
yang bisa dicapai juri. Aturan 09 hackathon menilai kedalaman teknis "verified against the
GitHub repository", dan aturan 08 menuntut produk yang berjalan; keduanya tidak bisa dijawab
oleh terminal seseorang. Satu-satunya pengecualian dicatat di `phase-2`: sebelum Fase 2 hijau
tidak ada Cloud Run sama sekali, jadi Fase 0 dan Fase 1 memakai bentuk `[x]` yang lebih lemah
— selesai dan ter-commit — dan `PROGRESS.md` menandainya "terverifikasi lokal", bukan
"terverifikasi hidup". Begitu Fase 2 hijau, keduanya harus dinaikkan ke bentuk penuh.

`[~]` tanpa alasan di baris yang sama adalah `[ ]`. Tidak ada keadaan keempat: tidak ada
"sebagian", tidak ada "hampir", tidak ada "selesai kecuali".

Tiga keadaan yang sama dipakai di **tiga tempat**, dan ketiganya harus sepakat:

1. Tabel fase di `PROGRESS.md` — satu baris per fase.
2. Baris `Keadaan` di blok Status tiap berkas fase.
3. Tiap butir **Tugas** dan tiap butir **Kriteria keluar** di dalam berkas fase.

Sebuah fase hanya boleh ditandai selesai bila **setiap** butir Tugas dan **setiap** butir
Kriteria keluar di dalamnya sudah ditandai. Butir yang dilewati memakai `[~]` dengan
alasannya di baris yang sama, dan fase yang memuat satu `[~]` pun tidak pernah menjadi
`[x]` — ia menjadi `[~]` di tabel fase, dengan butir yang dilewati disebut namanya.

## Perbarui rencana di commit yang sama dengan kode

Setiap commit yang menyentuh `src/katalis/` juga menyentuh `plan/PROGRESS.md`. Bukan commit
berikutnya, bukan di akhir sesi — commit yang sama.

Biaya kalau tidak: `PROGRESS.md` berhenti menjadi satu-satunya berkas yang menyatakan
kenyataan, dan begitu ia berbohong sekali, sesi berikutnya membaca keadaan yang salah,
mengerjakan fase yang salah, dan menemukan kesalahannya hanya setelah `./run.sh test` gagal
karena alasan yang tidak ada di rencana. Ini persis kegagalan yang sudah terjadi sekali di
proyek ini: PRD §0 mengutip `cat src/katalis/state/thresholds.learned.json` untuk angka
"18/18 ambang `shipped`", dan berkas itu tidak pernah ada
(`ls src/katalis/state` → `No such file or directory`). Satu klaim yang tidak diperiksa
terhadap disk menghasilkan satu baris audit merah dan potongan nilai pada dimensi kejujuran.

## Batas eksekusi — batas, bukan preferensi

Diturunkan dari PRD §12.3 dan §13. Melanggar salah satunya bukan trade-off; ia membatalkan
alasan fase yang bersangkutan ada.

1. **Scheduler bukan kanal.** D3 menulis berkas ke bucket. Ia tidak pernah mengirim pesan ke
   pengguna, tidak lewat e-mail, tidak lewat bot, tidak lewat webhook. Mengirim berarti
   menjamin kartu benar setiap hari, dan jaminan itu menuntut refresh live harian yang
   anggaran kreditnya tidak ada.
2. **Deploy tidak menambah fitur.** D1 mengekspos kartu yang sudah ada, dengan keluaran yang
   identik dengan `./run.sh pilar`. Setiap baris logika baru yang muncul karena "sekalian
   sudah di Cloud Run" ditolak di review, apa pun nilainya.
3. **Produk tidak boleh bergantung pada kuota model.** D10 boleh mati, kehabisan kredit, atau
   ditolak kuncinya, dan `./run.sh test` tetap hijau serta kartu tetap terbit. Itulah sebabnya
   M9 (klasifikasi deterministik) adalah MUST dan S7 (`CLASSIFIER=llm`) hanya SHOULD.
4. **Kredit Sectors, bukan kuota GCP, adalah anggaran yang mengikat.** Rekonsiliasi portal
   terakhir membaca **377 kredit tertagih** dari 1.000 (ekspor portal bertanggal 2026-09-05),
   dan ledger memuat tujuh baris setelah tanggal ekspor itu — jadi belanja nyata **≈384** dan
   sisa **≈616**. Perintahnya:
   ```bash
   cd research/harness && python3 src/reconcile_usage.py
   ```
   Setiap berkas fase menyatakan biaya kreditnya sendiri di blok Status. Fase yang tidak
   menyatakannya dianggap belum ditulis.
5. **Gate sitasi fail-closed.** Angka tanpa pasangan `(endpoint, field)` tidak tercetak.
   `Figure.__post_init__` melempar `ValueError` untuk figure tanpa sitasi
   (`src/katalis/pillars.py:52`), dan itu adalah bentuk yang benar; yang belum benar adalah
   gate kartunya — lihat Fase 0.
6. **Uji skema fail-closed.** Field yang tidak hadir di `research/harness/recorded/` membuat
   CI merah. Kartu tidak boleh menyebut field yang tidak pernah dilihat dari payload nyata.
7. **Tidak ada `.env`, tidak ada kunci, tidak ada `__pycache__`** di repo maupun di image
   mana pun. Hari ini bersih:
   ```bash
   git ls-files | grep -E '\.env|__pycache__'      # hanya .env.example
   ```
   `Dockerfile` Fase 2 harus memakai `.dockerignore` yang menegakkan hal yang sama, karena
   `.gitignore` tidak berlaku di dalam konteks build.

## Peta fase

Diturunkan dari PRD §9. Kolom kredit adalah biaya kredit Sectors, bukan biaya GCP.

| Fase | Menutup (baris PRD §9) | Kredit | Bisa dipotong |
| --- | --- | --- | --- |
| 0 | D1 + D3 ditutup, M6 kebersihan repo, `./run.sh test` hijau sebagai garis dasar | 0 | tidak |
| 1 | S1 modifier suspensi sebagai `Figure` | 0 | tidak |
| 2 | M8 pipeline deploy: Cloud Build → langkah test → Artifact Registry → Cloud Run `katalis-api`, Secret Manager | 0 | tidak |
| 3 | M9 klasifikasi deterministik menjelaskan-vs-melaporkan | 0 | tidak |
| 4 | S2 + D2 ditutup — kartu berbunyi `BERGERAK TANPA PENJELASAN`, bukan `tenang` | 0 | tidak |
| 5 | S3 enam simbol berlabel dibeli | 42 | tidak |
| 6 | S6 replay `katalis-learn`, lalu S7 `CLASSIFIER=llm` | 0 / kuota model | ya, potongan pertama |
| 7 | S5 halaman baca, S4 README + halaman metode + tiga percakapan, video, submission | 0 | tidak |

**Satu tempat PRD §9 lebih longgar daripada tabel di atas, dan PRD yang menang:** §9 hanya
menuntut S5 (halaman Vercel) menunggu baris 4 (M8, yaitu Fase 2) dan S7 menunggu baris 5 dan 6
(M9 dan S2/D2, yaitu Fase 3 dan Fase 4) — tabel ini menaruh keduanya lebih belakang daripada
yang dituntut ketergantungan, jadi keduanya boleh dikerjakan lebih awal bila ada waktu luang,
dan tidak boleh dikerjakan lebih akhir daripada fase yang tertulis.

Satu ketidakcocokan di dalam PRD sendiri, dicatat di sini supaya tidak diputuskan dua kali:
§6 menulis S3 sebagai "dua simbol nyata tambahan, 12 kredit", sedangkan §7 dan §9 baris 7
menulis "enam simbol, 42 kredit". Fase 5 memakai **enam simbol / 42 kredit**, karena §7
menjelaskan alasannya (korpus belajar S6 adalah simbol yang sama yang S3 beli) dan §6 tidak.

## Garis potong — daftar berurut, tidak boleh diimprovisasi

Kalau waktu habis, potong dari atas. Urutan ini diturunkan dari pembagian MUST/SHOULD/CUT di
PRD §6 dan kolom ketergantungan §9, dan ia **bukan bahan diskusi saat sedang terburu-buru** —
justru itulah alasannya ditulis sekarang.

1. **S7 `CLASSIFIER=llm`** (bagian kedua Fase 6). SHOULD, dan §12.3 aturan 3 sudah menyatakan
   produk harus berjalan tanpanya. Dipotong pertama karena ia satu-satunya pekerjaan yang
   biayanya bukan waktu saja melainkan juga kuota model dan satu secret tambahan.
2. **S6 `katalis-learn`** (bagian pertama Fase 6). SHOULD. Memotongnya membuat dimensi "loop
   belajar" bernilai nol pada audit internal, dan itu harga yang diketahui — bukan kejutan.
3. **S5 halaman Vercel** (bagian dari Fase 7). SHOULD, dan PRD §10 sudah menyiapkan
   pemotongannya kalau syarat Vercel Hobby berubah. CLI dan Cloud Run tetap permukaan utama.
4. **Simbol kelima dan keenam di Fase 5.** Turun dari enam ke empat menghemat 14 kredit dan
   masih memenuhi metrik §5 "≥3 simbol nyata". Yang hilang adalah korpus S6, yang pada titik
   ini sudah dipotong di baris 2.
5. **Tiga percakapan pengguna** (bagian dari Fase 7). Dipotong terakhir di antara yang boleh
   dipotong, karena ia satu-satunya bukti untuk bagian hipotesis §4 yang masih hipotesis.

**Yang tidak pernah dipotong, apa pun yang terjadi:**

- **Pipeline deploy (Fase 2).** Tanpa revisi yang melayani, `[x]` tidak pernah bisa diberikan
  pada apa pun, dan kriteria "produk berjalan" pada pemeriksaan kelayakan bertumpu pada
  terminal yang tidak dimiliki juri.
- **Empat pilar (Fase 0, 3, 4 — mekanismenya).** Cabut empat pilar dan yang tersisa adalah
  tampilan ulang field API; itu persis yang dinilai rendah pada kriteria 30% "how innovative
  is the use of Sectors API".
- **Fase 7.** Video bernilai 30% dari total dan submission yang tidak lengkap gagal pada
  pemeriksaan kelayakan, bukan pada skor. Memotong Fase 7 berarti memotong nilai, bukan
  memotong lingkup.
