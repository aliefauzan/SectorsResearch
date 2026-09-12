# Fase 2 · Pipeline deploy

## Status

| | |
| --- | --- |
| Keadaan | `[ ]` belum dikerjakan |
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

- [ ] **1. `server.py` — pembungkus HTTP tipis di atas `cli.py`.**
      `GET /card/{symbol}?date=YYYY-MM-DD`. Keluarannya harus identik dengan `./run.sh pilar`.
      Pustaka standar (`http.server`) sudah cukup; menambah kerangka kerja di sini adalah menambah
      permukaan tanpa menambah kebenaran. Endpoint kedua `GET /healthz` mengembalikan 200.

- [ ] **2. `Dockerfile` dan `.dockerignore`.**
      Base `python:3.12-slim` — batas Always Free Artifact Registry 0,5 GB adalah batas yang
      nyata. `.dockerignore` harus menolak `.env`, `.env.*`, `__pycache__/`, `.git/`, dan
      `research/` kecuali `research/harness/recorded/`. `.gitignore` **tidak** berlaku di dalam
      konteks build; ini titik tempat kunci paling mungkin ikut masuk image.

- [ ] **3. `cloudbuild.yaml` dengan `./run.sh test` sebagai langkah build.**
      Urutan: build image → jalankan `./run.sh test` di dalam image → push ke Artifact Registry →
      deploy D1. Gate merah berarti tidak ada deploy. Langkah test harus berjalan **di dalam
      image**, bukan di host, supaya yang diuji adalah yang dikirim.

- [ ] **4. Secret Manager (D4).**
      Satu secret `SECTORS_API_KEY`, satu versi aktif. Cloud Run membacanya sebagai **referensi
      secret**, bukan variabel lingkungan literal. Produk tidak membutuhkannya untuk menerbitkan
      kartu; ia hanya dibutuhkan D2 saat seseorang memicu refresh live secara manual.

- [ ] **5. Artifact Registry (D6) dengan kebijakan simpan 5 tag terakhir.**

- [ ] **6. Bucket `katalis-recorded` (D7), region US.**
      Always Free Cloud Storage hanya berlaku di region US. Cloud Run tetap di
      `asia-southeast2` untuk latensi. Kalau biaya keluar-region muncul di tagihan, keputusan ini
      dibalik dan alasannya dicatat di `PROGRESS.md`.

- [ ] **7.** **`katalis-refresh` (D2) sebagai Cloud Run job, dan `katalis-refresh-daily` (D3) sebagai
      satu Cloud Scheduler job.**
      D3 berjalan dengan `SOURCE=recorded`. Ia menulis berkas ke bucket. **Ia tidak mengirim apa
      pun ke pengguna** — tidak e-mail, tidak webhook, tidak bot. Free tier Cloud Scheduler tidak
      tercantum di halaman Google Cloud Free Program; rencana ini memakai **satu** job, jadi
      pertanyaan itu tidak memblokir, tetapi periksa sebelum membuat job kedua.

- [ ] **8. Trigger Cloud Build dari push ke `master`.**
      Cabang di repo ini adalah `master`, bukan `main` — `git rev-parse --abbrev-ref HEAD`.

## Kriteria keluar

- [ ] **1.** `gcloud builds list --limit=1` menunjukkan build `SUCCESS` yang dipicu oleh push, bukan oleh
      perintah manual.
- [ ] **2.** Satu commit yang sengaja membuat sebuah assertion merah menghasilkan build `FAILURE`, dan
      `gcloud run revisions list --service katalis-api` menunjukkan revisi yang melayani **tidak
      berubah**. Commit itu di-revert setelahnya.
- [ ] **3.** `curl -s "https://<katalis-api-url>/card/LIFE?date=2026-09-01"` mengembalikan kartu yang
      byte-identik dengan keluaran `cd src/katalis && ./run.sh pilar LIFE 2026-09-01`. Bandingkan
      dengan `diff`, bukan dengan mata.
- [ ] **4.** `gcloud run services describe katalis-api --format='value(spec.template.spec.containers[0].env)'`
      tidak memuat nilai kunci apa pun; secret hadir sebagai referensi.
- [ ] **5.** `docker run --rm --entrypoint sh <image> -c 'ls -a /app | grep -E "^\.env|__pycache__"'`
      tidak mengembalikan apa pun.
- [ ] **6.** `gcloud scheduler jobs list` menunjukkan **satu** job, dan definisinya memuat
      `SOURCE=recorded`.
- [ ] **7.** `cd research/harness && python3 src/reconcile_usage.py` mencetak total portal yang sama
      persis dengan pada akhir Fase 1, dan tetap sama setelah D3 berjalan sekali.
- [ ] **8.** `PROGRESS.md` memuat URL revisi Cloud Run yang melayani, dan status Fase 0 dan Fase 1
      dinaikkan dari "terverifikasi lokal" menjadi `[x]`.

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
