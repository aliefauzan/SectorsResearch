# TODO — yang hanya bisa dikerjakan manusia

Berkas ini memuat **hanya** pekerjaan yang seorang agen tidak bisa selesaikan sendiri: konsol
GCP, portal Sectors, akun pihak ketiga, kamera, dan orang. Semua pekerjaan kode ada di
`phases/`, dan keadaan nyata ada di `PROGRESS.md`. Kalau sebuah baris di sini bisa dikerjakan
agen, ia salah tempat — pindahkan ke berkas fase.

Kotak centang sama seperti di seluruh `plan/`: `[ ]` belum · `[x]` selesai · `[~]` sengaja
dilewati, alasan di baris yang sama.

Tiap baris menyebut **kenapa ia memblokir** dan **apa yang saya bisa kerjakan begitu ia
selesai**. Urutan di dalam tiap bagian penting; antar bagian tidak.

---

## Sudah terverifikasi — jangan dikerjakan ulang

Diperiksa 2026-09-12 dengan perintah, bukan ingatan.

- [x] **Repo `aliefauzan/SectorsResearch` sudah publik dan dibuat di dalam jendela build.**
      `gh repo view aliefauzan/SectorsResearch --json visibility,createdAt` → `PUBLIC`,
      `2026-09-05T14:01:37Z`. Jendela dibuka 19 Agustus, jadi ini lolos.
- [x] **Repo `aliefauzan/SectorsHackathon` juga publik**, dibuat `2026-09-10`. Ia memuat PRD,
      bukan kode.
- [x] **Tidak ada kunci API di berkas terlacak.**
      `git ls-files | grep -E '\.env|__pycache__'` → hanya `.env.example`.
- [x] **`gcloud` terpasang dan terautentikasi** (SDK 567.0.0), dan ada **dua akun penagihan
      berstatus OPEN**: `018056-334B67-5DE9C0` ("free trial") dan `01B951-232B54-4E1D9A`
      ("My Billing Account"). `gcloud billing accounts list`.
- [x] **Proyek GCP ada dan tertagih: `ada-sectors-508410` ("ADA sectors").**
      Ditautkan 2026-09-12 ke akun penagihan **`018056-334B67-5DE9C0` ("free trial")**.
      `gcloud billing projects describe ada-sectors-508410` → `billingEnabled: True`.
- [x] **Enam API aktif** di proyek itu: `run`, `cloudbuild`, `artifactregistry`,
      `secretmanager`, `storage`, `cloudscheduler`.
      `gcloud services list --enabled --project=ada-sectors-508410`
- [x] **`SECTORS_API_KEY` ada di Secret Manager**, satu versi aktif, dimuat dari
      `/Users/af/dumpProject/Sectors/.env` lewat pipa — nilainya tidak pernah dicetak.
      Diverifikasi dengan membandingkan SHA-256 nilai lokal dan nilai tersimpan: cocok.
      `gcloud secrets versions list SECTORS_API_KEY --project=ada-sectors-508410` → `1 enabled`

---

## Sekarang — memblokir commit berikutnya

- [ ] **Push tiga commit yang sudah ada.**
      `git log origin/master..HEAD` menunjukkan `6128b4b`, `7121ef2`, `83fe2a1` belum di
      origin. Tanpa push, Cloud Build tidak punya apa pun untuk dipicu, dan juri tidak punya
      apa pun untuk dibaca.
      ```bash
      git push origin master
      ```
      *Begitu selesai:* Fase 2 bisa memasang trigger yang benar-benar menyala.

- [ ] **Putuskan satu repo yang dikirim ke portal, dan perbaiki nama repo di PRD.**
      Form submission meminta **satu** tautan, dan kriteria kedalaman teknis 30% diverifikasi
      terhadap repo itu. Kode ada di `SectorsResearch`; PRD §12.1 menulis
      `aliefauzan/SectorsHackathon`. Pilih `SectorsResearch` kecuali Anda memindahkan kode.
      *Begitu selesai:* B9 tertutup, dan `03-hackathon-compliance.md` bisa menyebut satu nama
      alih-alih dua.

---

## Sebelum Fase 2 · Pipeline deploy

Saya bisa menulis `server.py`, `Dockerfile`, `.dockerignore` dan `cloudbuild.yaml` tanpa satu
klik pun. Yang di bawah ini yang tidak bisa.

- [x] **Proyek GCP dibuat dan ditautkan ke akun penagihan.** `ada-sectors-508410`,
      akun `018056-334B67-5DE9C0` ("free trial"), `billingEnabled: True`.
      **Bukan akun yang dipilih lebih dulu:** `01B951-232B54-4E1D9A` ("My Billing Account")
      ditolak dua kali dengan `FAILED_PRECONDITION: Cloud billing quota exceeded`, dan
      penolakan itu bukan soal jumlah proyek — hanya tiga proyek tertaut di sana. Jalan
      keluarnya adalah mengajukan kenaikan kuota lewat tautan yang Google berikan, lalu
      menautkan ulang.

- [ ] **Putuskan apakah akun penagihan tetap "free trial" atau dipindah ke "My Billing
      Account".** Selama di trial, biaya keluar dari kredit welcome, bukan dari kartu — itu
      posisi yang lebih aman dan itulah yang berlaku sekarang. Memindahkannya nanti adalah
      satu perintah:
      ```bash
      gcloud billing projects link ada-sectors-508410 --billing-account=01B951-232B54-4E1D9A
      ```

- [ ] **Catat tanggal trial mulai dan sisa harinya.** §10 PRD membuka pertanyaan ini dan ia
      masih terbuka; `gcloud` tidak mengekspos tanggalnya, jadi bacalah di konsol Billing →
      Overview. Ia menentukan kapan D10 (panggilan model) berhenti gratis.

- [x] **Enam API diaktifkan** di `ada-sectors-508410`: `run`, `cloudbuild`,
      `artifactregistry`, `secretmanager`, `storage`, `cloudscheduler`.

- [x] **`SECTORS_API_KEY` dimuat ke Secret Manager**, satu secret, satu versi aktif.
      Nilainya dialirkan dari `.env` ke `gcloud secrets versions add --data-file=-` lewat pipa,
      jadi ia tidak pernah tercetak, tidak pernah masuk argumen perintah, dan tidak pernah
      masuk riwayat percakapan. Diverifikasi dengan membandingkan SHA-256 nilai lokal dan
      nilai tersimpan — cocok. Batas Always Free: 6 versi secret aktif per bulan.

- [ ] **Sambungkan repo GitHub ke Cloud Build** (konsol, sekali, butuh OAuth GitHub).
      Cloud Build → Triggers → Connect repository → `aliefauzan/SectorsResearch`.
      **Cabangnya `master`, bukan `main`.**
      *Begitu selesai:* saya bisa membuat trigger dan `cloudbuild.yaml`-nya lewat CLI.

- [ ] **Putuskan region, dan catat keputusannya.**
      Rencana: bucket di **US** (Always Free Cloud Storage hanya region US), Cloud Run di
      **`asia-southeast2`** untuk latensi Jakarta. Balikkan kalau biaya keluar-region muncul
      di tagihan.

- [ ] **Cek free tier Cloud Scheduler sebelum membuat job kedua.**
      Ia **tidak tercantum** di halaman Google Cloud Free Program. Rencana memakai satu job,
      jadi ini tidak memblokir hari ini — tetapi periksa halaman pricing Scheduler sebelum
      job kedua.

---

## Sebelum Fase 5 · Membeli enam simbol — 42 kredit

**Ini satu-satunya fase yang membelanjakan kredit, dan ia tidak bisa dibatalkan.**

- [ ] **Ambil ekspor log penggunaan portal yang baru.** Ekspor yang ada semuanya bertanggal
      `2026-09-05` (`ls research/evidence/usage-log/`), sedangkan pembelian LIFE terjadi
      sesudahnya. Sampai ada ekspor baru, sisa kredit hanya diketahui sampai 5 September.
      Angka hari ini: portal **377** tertagih, ledger **272**, selisih **105**, ditambah tujuh
      baris ledger setelah tanggal ekspor → belanja nyata **≈384**, sisa **≈616**.
      Letakkan CSV baru di `research/evidence/usage-log/`, lalu:
      ```bash
      cd research/harness && python3 src/reconcile_usage.py
      ```
      *Begitu selesai:* B3 tertutup, dan Fase 5 tahu apakah enam simbol muat atau harus turun
      ke empat.

- [ ] **Konfirmasi enam simbol yang dibeli, dan satu yang ditahan sebagai hold-out.**
      Kandidat berlabel di `v2_suspensions.json` (17 simbol unik): AGAR, ASLI, BEEF, COAL,
      CSMI, DOOH, EKAD, INCF, MDIA, NICK, PACK, PPGL, SAFE, TMPO, TRUK, YPAS. LIFE sudah ada.
      Hold-out tidak boleh LIFE — ia sudah dipakai membangun pilar. Kandidat yang belum pernah
      disentuh kode: **NICK, PPGL, SAFE**.
      *Saya usulkan daftarnya kalau Anda mau; keputusannya tetap milik Anda karena ia
      membelanjakan kredit.*

- [ ] **Jalankan `capture.py` live, setelah rehearsal mock hijau.** Saya menulis rencananya
      dan menjalankan rehearsal; **perintah live yang terakhir Anda yang tekan**, supaya tidak
      ada kredit yang keluar tanpa seseorang memutuskannya.

---

## Sebelum Fase 6 · Jalur model — opsional

- [ ] **Pilih penyedia model dan siapkan kuncinya.** Vertex AI tidak punya Always Free dan
      dibayar dari sisa trial; penyedia luar berarti satu secret lagi di Secret Manager.
      PRD menunda keputusan sampai M9 hijau, dan itu masih urutan yang benar.
- [~] **Boleh dilewati seluruhnya.** Fase 6 adalah potongan pertama di garis potong. Kalau
      dilewati, lihat baris track di bagian Submission — deklarasi track harus berpindah.

---

## Fase 7 · Permukaan, video, submission

- [ ] **Sambungkan halaman ke Vercel** (akun Vercel, konsol). Vercel Hobby melarang pemakaian
      komersial dan **tidak menerima repo milik organisasi Git** — repo Anda milik akun
      pribadi, jadi aman hari ini. Kalau repo dipindah ke organisasi, baris ini dipotong.

- [ ] **Wawancarai tiga orang.** Metrik §5: tiga dari tiga menyebut isi kartu **tanpa
      dipandu**. Catat apa yang mereka sebut lebih dulu, apa yang salah dibaca, apa yang
      ditanyakan. Ini satu-satunya bukti untuk bagian hipotesis §4 yang masih hipotesis —
      bahwa orang membuka kartu **sebelum** membeli, bukan sesudah.

- [ ] **Rekam video juri ≤3 menit.** Naskah shot demi shot ada di `99-demo-script.md`.
      Rekam versi kasar **sekarang**, di atas apa yang sudah berjalan, lalu ganti shot satu
      per satu saat fasenya selesai. Kriteria bernilai 30% tidak boleh menunggu enam fase.

- [ ] **Rekam video teaser 1 menit.** Boleh potongan dari video juri.

- [ ] **Unggah kedua video, lalu buka tautannya dari jendela penyamaran.**
      Video yang tidak dapat diakses **tidak dinilai** — itu aturan tertulis, bukan risiko.

- [ ] **Terbitkan post media sosial yang menandai akun Sectors resmi.**
      Syarat submission yang terdaftar, tanpa ketergantungan teknis apa pun, dan penyebab
      gagal yang paling murah. Bisa dikerjakan kapan saja setelah repo dan video terbit.

- [ ] **Isi form submission.** Enam item: tautan repo, video teaser, video juri, pernyataan
      masalah satu kalimat, pilihan track + nama peserta, dan tautan post media sosial.

- [ ] **Putuskan track sebelum menekan submit.**
      **Track 01** kalau Fase 6 selesai — palangnya menuntut orkestrasi milik sendiri dan
      komponen AI/LLM, dan yang menjawabnya adalah `katalis-learn` plus `CLASSIFIER=llm`.
      **Track 03** kalau Fase 6 dipotong. Aturan mengizinkan juri memindahkan proyek ke track
      yang cocok, tetapi memindahkan sendiri lebih baik daripada dipindahkan.

- [ ] **Submit paling akhir.** Repo dan aplikasi **membeku** saat submit: tidak ada commit,
      push, edit, atau perbaikan bug setelahnya. Submit saat selesai, bukan saat gugup.

---

## Tidak dapat diperbaiki mundur — periksa sekarang, bukan nanti

- [ ] **Pastikan tiap peserta menyelesaikan onboarding sectors.app sebelum baris kode
      pertama.** Commit pertama repo ini `2026-09-05`
      (`git log --reverse --format='%ad %h %s' --date=short | head -1`), dan tidak ada bukti
      onboarding mendahuluinya di repo mana pun.
      Satu anggota yang belum onboard dapat membuat **seluruh** submission tidak sah, dan
      tidak ada pekerjaan apa pun setelah ini yang memperbaikinya. Kalau tim Anda satu orang,
      periksa akun Anda sendiri dan tutup baris ini.

- [ ] **Pastikan roster tim sudah final sebelum mengklaim kredit bonus.** Roster **terkunci**
      saat kredit diklaim. Kalau kredit sudah diklaim, baris ini sudah lewat — tandai `[x]`.

---

## Peta ke `PROGRESS.md`

| Baris di sini | Blocker |
| --- | --- |
| Ekspor portal baru | B3 |
| Onboarding peserta | B7 |
| Video, teaser, post media sosial | B8 (bagian "repo publik" sudah tertutup) |
| Satu repo dipilih, nama di PRD diperbaiki | B9 |
| Keputusan track | B10 |
