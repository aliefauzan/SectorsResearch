# Fase 2 · Pipeline deploy

## Status

| | |
| --- | --- |
| Keadaan | `[~]` — tujuh dari delapan tugas selesai dan berjalan; tugas 8 (trigger) menunggu OAuth GitHub yang hanya manusia bisa tekan (B17) |
| Menutup | PRD §9 baris 4 (M8), komponen D1–D7 dari §12.2 |
| Menunggu | Fase 0 (M6 — kode di repo dengan riwayat) |
| Kredit Sectors | **0** — D3 berjalan `SOURCE=recorded` |
| Biaya GCP | Ditargetkan nol; seluruh komponen dipilih agar muat Always Free |

## Kenapa deploy sedini ini, padahal produk belum selesai

Karena `[x]` di seluruh rencana ini menuntut revisi yang melayani, dan sampai Fase 2 hijau
tidak ada fase yang bisa mencapai bentuk `[x]` penuh. Menundanya berarti menunda definisi
"selesai" itu sendiri sampai minggu terakhir, dan minggu terakhir sudah dipesan untuk video.

Alasan kedua ada di aturan: kedalaman teknis 30% diverifikasi terhadap repo GitHub, dan
kegunaan nyata 40% bertanya "bisakah seseorang memakainya hari ini". Kartu yang hanya terbit
di terminal seseorang tidak menjawab keduanya.

**Deploy tidak menambah fitur.** D1 mengekspos kartu yang sudah ada. Setiap baris logika baru
yang muncul karena "sekalian sudah di Cloud Run" ditolak, apa pun nilainya.

## Tugas

- [x] **1. `server.py` — pembungkus HTTP tipis di atas `cli.py`.**
      `GET /card/{symbol}?date=YYYY-MM-DD`. Keluarannya harus identik dengan `./run.sh pilar`.
      Pustaka standar (`http.server`) sudah cukup; menambah kerangka kerja di sini adalah menambah
      permukaan tanpa menambah kebenaran. Endpoint kedua `GET /healthz` mengembalikan 200.

      Selesai, 17 gate sendiri. Badan balasan adalah stdout `card.show()` yang ditangkap apa
      adanya, bukan `card.render()` yang dipanggil ulang dengan argumen pilihan sendiri — dan
      `check_card_route_matches_the_cli` membuktikannya dengan menjalankan `cli.py` sebagai
      proses terpisah dan membandingkan byte, bukan dengan memanggil fungsi yang sama dua kali.

      **Satu penyimpangan, dicatat alih-alih diam-diam diperbaiki:** `/healthz` benar di dalam
      container (`docker run -p` → `ok`) tetapi **tidak pernah sampai** di belakang Cloud Run —
      front end Google menjawabnya sendiri dengan HTML 404 miliknya, dan permintaannya tidak
      muncul di log permintaan revisi. `/health` adalah handler yang sama dengan nama yang
      lolos, dan itulah nama yang dipakai probe. Keduanya ada, keduanya digate.

- [x] **2. `Dockerfile` dan `.dockerignore`.**
      Base `python:3.12-slim` — batas Always Free Artifact Registry 0,5 GB adalah batas yang
      nyata. `.dockerignore` harus menolak `.env`, `.env.*`, `__pycache__/`, `.git/`, dan
      `research/` kecuali `research/harness/recorded/`. `.gitignore` **tidak** berlaku di dalam
      konteks build; ini titik tempat kunci paling mungkin ikut masuk image.

      Selesai. Image 224 MB, `python:3.12-slim`, pengguna non-root, nol dependensi terpasang.
      `.dockerignore` menolak semuanya lebih dulu (`*`) lalu menamai yang boleh masuk, karena
      daftar-tolak melewatkan apa yang belum terpikirkan dan daftar-izin tidak.

      **Satu penyimpangan:** tugas ini menulis "`research/` kecuali
      `research/harness/recorded/`". Image juga membawa `research/harness/synth/`, karena
      `DEMO_CASES` memuat satu kasus sintetis dan karena itu empat dari enam suite gate
      membutuhkannya — dan tugas 3 menuntut `./run.sh test` hijau **di dalam** image. Memilih
      teks tugas di atas tugas 3 berarti pipeline yang tidak membuktikan apa pun. Tambahannya
      7,2 MB dari batas 0,5 GB.

      Berkas ketiga yang tidak diminta tetapi diperlukan: `.gcloudignore`. Tanpanya
      `gcloud builds submit` memakai `.gitignore` sebagai gantinya — yang memang mengecualikan
      `.env`, tetapi "kebetulan mengecualikan" bukan jaminan, dan tarball sumber adalah tempat
      kedua sebuah kunci bisa meninggalkan laptop ini.

- [x] **3. `cloudbuild.yaml` dengan `./run.sh test` sebagai langkah build.**
      Urutan: build image → jalankan `./run.sh test` di dalam image → push ke Artifact Registry →
      deploy D1. Gate merah berarti tidak ada deploy. Langkah test harus berjalan **di dalam
      image**, bukan di host, supaya yang diuji adalah yang dikirim.

      Selesai, lima langkah: `build` → `test` → `hygiene` → `push` → `deploy`. Langkah
      `hygiene` tidak diminta dan ditambahkan karena batas eksekusi 7 berbicara tentang
      **image**, bukan tentang `.dockerignore`: berkasnya benar dan image-nya bersih adalah dua
      klaim berbeda, jadi langkah itu memeriksa lapisan yang sudah dibangun, bukan berkas yang
      mengatur pembangunannya.

      Dua hal yang membuat build pertama merah dan pantas dicatat: nilai *default* sebuah
      substitusi tidak boleh merujuk substitusi lain — `${PROJECT_ID}` yang ditulis di sana
      tetap literal dan `docker build` menolak tagnya — dan blok `images:` mem-push **setelah**
      langkah terakhir, yaitu setelah `deploy` yang justru membutuhkan image itu sudah ada.
      Keduanya dijelaskan di komentar berkasnya, bukan hanya di sini.

- [x] **4. Secret Manager (D4).**
      Satu secret `SECTORS_API_KEY`, satu versi aktif. Cloud Run membacanya sebagai **referensi
      secret**, bukan variabel lingkungan literal. Produk tidak membutuhkannya untuk menerbitkan
      kartu; ia hanya dibutuhkan D2 saat seseorang memicu refresh live secara manual.

      Selesai, dan diverifikasi dari bentuk yang tersimpan: `valueFrom.secretKeyRef`, bukan
      `value`. `server.py` juga digate untuk itu dari sisi lain —
      `check_no_secret_can_reach_a_response` menaruh sentinel di `SECTORS_API_KEY` dan menuntut
      ia tidak muncul di badan balasan mana pun.

- [x] **5. Artifact Registry (D6) dengan kebijakan simpan 5 tag terakhir.**
      Repo `katalis` di `asia-southeast2`, dua kebijakan: `keep-last-5-tags`
      (`mostRecentVersions.keepCount: 5`) dan `delete-the-rest`, dry-run mati. Kondisi kosong
      ditolak API (`INVALID_ARGUMENT: empty condition`), jadi aturan hapus memakai
      `tagState: ANY` + `olderThan: 86400s` dan aturan simpan yang menang atasnya.
      Definisinya ada di `infra/artifact-cleanup.json`, bukan hanya di konsol.

- [x] **6. Bucket `katalis-recorded` (D7), region US.**
      Always Free Cloud Storage hanya berlaku di region US. Cloud Run tetap di
      `asia-southeast2` untuk latensi. Kalau biaya keluar-region muncul di tagihan, keputusan ini
      dibalik dan alasannya dicatat di `PROGRESS.md`.

      Selesai — **`us-east1`, satu region, bukan multi-region `US`.** Ini penajaman dari teks
      tugas, bukan pengabaiannya: Always Free Cloud Storage berlaku untuk satu region US
      (`us-east1`/`us-west1`/`us-central1`) dan **tidak** untuk multi-region `US`, jadi `-l US`
      akan menagih dari byte pertama. Akses publik dicegah, akses seragam dinyalakan.

- [x] **7.** **`katalis-refresh` (D2) sebagai Cloud Run job, dan `katalis-refresh-daily` (D3) sebagai
      satu Cloud Scheduler job.**
      D3 berjalan dengan `SOURCE=recorded`. Ia menulis berkas ke bucket. **Ia tidak mengirim apa
      pun ke pengguna** — tidak e-mail, tidak webhook, tidak bot. Free tier Cloud Scheduler tidak
      tercantum di halaman Google Cloud Free Program; rencana ini memakai **satu** job, jadi
      pertanyaan itu tidak memblokir, tetapi periksa sebelum membuat job kedua.

      Selesai, dan berjalan: satu eksekusi manual dan satu yang dipicu scheduler, keduanya
      `Completed`, dan objek di bucket **byte-identik** dengan `./run.sh pilar LIFE 2026-09-01`.

      Muatan job adalah `publish.py`, dan bentuknya ditentukan oleh batas eksekusi 1 sebanyak
      oleh apa yang harus ditulis. Ia menulis objek ke Cloud Storage dan tidak punya pintu
      keluar lain, dan `check_this_job_is_not_a_channel()` menegakkan itu dengan membaca sumber
      berkas itu sendiri lewat `ast` — melewati docstring (yang menyebut kata-kata terlarang
      justru karena itu maksudnya) dan melewati gate-nya (yang memuat daftarnya), sehingga yang
      dipindai adalah kode yang benar-benar berjalan. Kredensial datang dari metadata server,
      jadi tidak ada berkas kunci dan tidak ada kunci yang dibaca dari lingkungan; `--dry-run`
      digate untuk **tidak** meminta token sama sekali.

      Definisi scheduler memuat `SOURCE=recorded` di badan permintaannya sendiri
      (`overrides.containerOverrides.env`), bukan hanya di deskripsinya — kriteria keluar 6
      bertanya pada definisinya, dan jawaban yang hanya ada di komentar bukan jawaban.

- [ ] **8. Trigger Cloud Build dari push ke `master`.**
      Cabang di repo ini adalah `master`, bukan `main` — `git rev-parse --abbrev-ref HEAD`.

      **Belum, dan bukan karena kode.** `gcloud builds connections list` mengembalikan nol, dan
      menyambungkan `aliefauzan/SectorsResearch` menuntut handshake OAuth GitHub yang tidak
      punya bentuk CLI. Perintah pembuatan trigger sudah ditulis penuh di `infra/trigger.sh`
      dan langkah konsolnya di `infra/README.md`, jadi yang tersisa untuk manusia adalah satu
      koneksi lalu satu perintah. Dicatat sebagai B17.

## Kriteria keluar

Bukti tiap baris adalah perintah yang dijalankan 2026-09-12 dan keluarannya, bukan ingatan.

- [ ] **1.** `gcloud builds list --limit=1` menunjukkan build `SUCCESS` yang dipicu oleh push, bukan oleh
      perintah manual.
      **Tidak terpenuhi, dan hanya manusia yang bisa menutupnya.** Tiga build `SUCCESS` ada —
      `manual1`, `manual2` — tetapi ketiganya `gcloud builds submit`, dan `source` mereka adalah
      tarball di GCS, bukan sebuah commit. Tanpa koneksi GitHub (B17) tidak ada trigger, dan
      tanpa push (baris pertama `TODO.md`) tidak ada yang memicunya.

- [~] **2.** Satu commit yang sengaja membuat sebuah assertion merah menghasilkan build `FAILURE`, dan
      revisi yang melayani **tidak berubah** — dibuktikan lewat `builds submit`, bukan lewat push, karena tugas 8 belum ada.
      Mekanismenya terbukti dan setengahnya tidak: `check_table()` dirusak dengan satu baris
      `return [...], 1`, `SHORT_SHA=broken1` dikirim, dan build `60e1a5c0` berakhir
      **`FAILURE` pada langkah `test`** dengan `hygiene`, `push` dan `deploy` **tidak pernah
      berjalan** (`['SUCCESS','FAILURE','QUEUED','QUEUED','QUEUED']`). Revisi yang melayani
      tetap `katalis-api-00002-c5r`, tidak ada revisi ketiga yang lahir, dan tag `broken1` tidak
      ada di registry karena push memang tidak tercapai. Kerusakannya sudah dibalik:
      `git diff --stat src/katalis/thresholds.py` kosong dan suite kembali exit 0. Yang belum
      terbukti adalah bahwa **sebuah push** memicu rangkaian yang sama.

- [x] **3.** `curl` ke revisi yang melayani mengembalikan kartu yang byte-identik dengan
      `./run.sh pilar LIFE 2026-09-01`.
      `diff` atas `https://katalis-api-ibyebnreqa-et.a.run.app/card/LIFE?date=2026-09-01`
      terhadap keluaran CLI: tidak ada selisih, 2.971 byte. Dibandingkan dengan `diff`, bukan
      dengan mata, di dua revisi berbeda (`00001`, lalu `00002`).

- [x] **4.** `gcloud run services describe katalis-api` tidak memuat nilai kunci apa pun.
      `{'name': 'SOURCE', 'value': 'recorded'}` dan
      `{'name': 'SECTORS_API_KEY', 'valueFrom': {'secretKeyRef': {'key': 'latest', 'name': 'SECTORS_API_KEY'}}}`
      — sebuah referensi, dan tidak ada bentuk `value` di sebelahnya.

- [x] **5.** `docker run --rm --entrypoint sh <image> -c 'ls -a /app | grep -E "^\.env|__pycache__"'`
      tidak mengembalikan apa pun.
      Diuji pada image yang **benar-benar dipush** (`:manual2`, ditarik ulang dari Artifact
      Registry, bukan build lokal): `grep` exit 1, dan `find /app` atas `.env*`, `__pycache__`
      dan `*.pyc` juga nol baris. Langkah `hygiene` di `cloudbuild.yaml` mengulang pemeriksaan
      yang sama di setiap build, sehingga ia tidak bergantung pada seseorang mengingatnya.

- [x] **6.** `gcloud scheduler jobs list` menunjukkan **satu** job, dan definisinya memuat
      `SOURCE=recorded`.
      Satu baris: `katalis-refresh-daily`, `30 18 * * 1-5`, `ENABLED`, `Asia/Jakarta`. Badan
      permintaannya, didekode dari base64:
      `{"overrides":{"containerOverrides":[{"env":[{"name":"SOURCE","value":"recorded"},{"name":"BUCKET","value":"katalis-recorded"}]}],"taskCount":1}}`

- [x] **7.** `reconcile_usage.py` mencetak total portal yang sama persis dengan pada akhir Fase 1,
      dan tetap sama setelah D3 berjalan sekali.
      `portal rows: 408   portal total: 377`, `ledger total (capture only): 272` — identik
      dengan Fase 1. D3 sudah berjalan **dua** kali sejak itu, dan `_ledger.jsonl` tetap 175
      baris dengan `git status --porcelain research/harness/recorded/` kosong. Nol kredit
      Sectors dibelanjakan sepanjang fase ini.

- [x] **8.** `PROGRESS.md` memuat URL revisi Cloud Run yang melayani, dan status Fase 0 dan Fase 1
      dinaikkan.
      URL dan nama revisi masuk ke blok "Di mana kita sekarang". **Fase 1 naik ke `[x]`.**
      **Fase 0 tetap `[~]`, dan itu bukan kelalaian:** ia memuat satu butir `[~]` (`README.md`
      tingkat repo, dipindah ke Fase 7 lewat B15), dan `plan/README.md` menyatakan fase yang
      memuat satu `[~]` pun tidak pernah menjadi `[x]`. Yang berubah untuk Fase 0 adalah
      labelnya di tabel bukti: dari "terverifikasi lokal" menjadi terverifikasi hidup.

## Bobot demo

Kriteria 2 adalah shot video: commit yang merusak sebuah gate, build yang berubah merah, dan
revisi lama yang tetap melayani. Ini bukti paling langsung bahwa gate produk ini benar-benar
bisa merah — dan gate yang tidak pernah merah adalah gate yang tidak menguji apa pun.

Kriteria 3 adalah shot pendamping dan ia menjawab kegunaan nyata: URL yang bisa dibuka siapa
pun, mengembalikan kartu yang sama dengan yang dijalankan pengembang.

## Kalau ini melar

PRD §11 sudah menyatakan bentuk pemotongannya, dan ia dipakai apa adanya:

1. **D3 Cloud Scheduler dipotong.** Satu job yang menulis berkas ke bucket adalah yang paling
   mudah dilepas dan yang paling sedikit dilihat juri.
2. **D2 Cloud Run job dipotong.** Refresh menjadi satu perintah manual, yang memang sudah jadi
   jalur default-nya.
3. **D7 bucket dipotong.** Image membawa `recorded/` di dalamnya. Ini menaikkan ukuran image
   terhadap batas 0,5 GB dan harus diperiksa, tetapi menghapus satu layanan.
4. **Turun ke "image + build hijau" tanpa Cloud Run publik.** Ini lantai yang PRD sebut, dan
   pada titik ini CLI kembali menjadi satu-satunya permukaan.

Yang **tidak** dipotong: `./run.sh test` sebagai langkah build (tugas 3) dan Secret Manager
(tugas 4). Tanpa yang pertama, pipeline tidak membuktikan apa pun. Tanpa yang kedua, satu-satunya
tempat kunci bisa hidup adalah tempat yang salah.
