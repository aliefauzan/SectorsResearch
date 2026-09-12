# PROGRESS

Berkas ini adalah titik masuk sesi dan satu-satunya berkas di `plan/` yang menyatakan
**keadaan nyata**. Berkas lain menyatakan rencana. Kalau keduanya berselisih, berkas ini yang
benar dan yang lain yang diperbaiki.

Disemai 2026-09-12 dari perintah yang benar-benar dijalankan di repo ini. Tiap angka di bawah
punya perintahnya sendiri.

---

## Di mana kita sekarang

| | |
| --- | --- |
| Fase berjalan | **Fase 0 sampai 4 dikerjakan**; `[x]` penuh baru Fase 1 dan 3. Fase 0 `[~]` karena B15, Fase 2 `[~]` karena B17 (trigger push), **Fase 4 `[~]` karena B18 (revisi Cloud Run baru)** |
| Fase berikutnya | Fase 5 · Korpus berlabel — **menunggu B3 ditutup** |
| Revisi Cloud Run yang melayani | **`katalis-api-00003-r8l`**, 100% lalu lintas, di `https://katalis-api-ibyebnreqa-et.a.run.app` — `GET /card/{simbol}?date=…` dan `GET /health`. **Ia belum memuat Fase 4**; yang dibutuhkan `katalis-api-00004-…` |
| Proyek GCP | `ada-sectors-508410`, penagihan `01B951-232B54-4E1D9A` ("My Billing Account"), `SECTORS_API_KEY` di Secret Manager v1 sebagai referensi |
| Yang berjalan di GCP | D1 `katalis-api` · D2 job `katalis-refresh` · D3 scheduler `katalis-refresh-daily` (satu job, `30 18 * * 1-5` Asia/Jakarta) · D4 secret · D6 repo `katalis` (simpan 5 tag) · D7 bucket `katalis-recorded` (`us-east1`). **D5 trigger belum** — B17 |
| Gate | **297 assertion hijau di 44 fungsi check**, exit 0 (naik dari 243 di 40 fungsi — empat fungsi bertambah: dua di `pillars.py`, satu di `card.py`, satu di `server.py`; `thresholds.py` tetap tidak mencetak dua check-nya per nama) |
| Kredit terpakai | **377 terkonfirmasi portal** (ekspor `2026-09-05`), **≈384** termasuk tujuh baris ledger setelah tanggal ekspor. **Nol dibelanjakan di Fase 2, 3 maupun 4** |
| Kredit tersisa | **≈616 dari 1.000** |
| Produk | 9 berkas di `src/katalis/` — tidak ada modul baru di Fase 4; `pillars.py`, `card.py`, `server.py` yang berubah |
| Repo | remote `https://github.com/aliefauzan/SectorsResearch`, cabang `master`. **`origin/master` sudah di `29660a1`**, jadi sampai akhir Fase 3 semuanya sudah di-push — klaim "lima commit lokal belum di-push" di edisi sebelumnya sudah tidak benar |
| Working tree | bersih saat Fase 4 dimulai; satu commit Fase 4 di cabang `fase4-verdicts`, belum di-push |

### Perintah yang menghasilkan baris-baris itu

```bash
cd src/katalis && ./run.sh test; echo "exit=$?"     # 20 22 92 62 63 25 13 = 297, exit=0
wc -l src/katalis/*.py src/katalis/*.sh             # Σ 3282
git ls-files src/katalis                            # 9 berkas
git ls-files | wc -l                                # 720
git log --oneline | wc -l                           # 23
git log --reverse --format='%ad %h %s' --date=short | head -1   # 2026-09-05 bb83d3a init
git remote -v
git status --porcelain                              # bersih sebelum commit Fase 4
gcloud run services describe katalis-api --region=asia-southeast2 \
  --format='value(status.url,status.traffic[0].revisionName)'
gcloud scheduler jobs list --location=asia-southeast2
gcloud artifacts repositories describe katalis --location=asia-southeast2
cd research/harness && python3 src/reconcile_usage.py
ls research/evidence/usage-log/                     # lima CSV, semuanya 2026-09-05
```

### Terverifikasi hidup · terverifikasi lokal · sekadar diklaim

| Terverifikasi **hidup** (publik, dapat dicapai orang lain) | Perintah |
| --- | --- |
| Kartu LIFE terbit dari sebuah URL, byte-identik dengan terminal pengembang | `diff <(curl -s "https://katalis-api-ibyebnreqa-et.a.run.app/card/LIFE?date=2026-09-01") <(cd src/katalis && ./run.sh pilar LIFE 2026-09-01)` → tidak ada selisih, 2.971 byte |
| `GET /health` mengembalikan `ok` pada revisi yang melayani | `curl -s .../health` |
| Kunci hadir sebagai referensi, bukan nilai | `gcloud run services describe katalis-api` → `valueFrom.secretKeyRef` |
| Gate merah menghentikan deploy: build `60e1a5c0` `FAILURE` di langkah `test`, `push` dan `deploy` tidak pernah berjalan, revisi yang melayani tidak berubah | `gcloud builds describe 60e1a5c0…` → `['SUCCESS','FAILURE','QUEUED','QUEUED','QUEUED']` |
| Image yang dipush tidak membawa `.env`, `__pycache__`, atau `*.pyc` | `docker run --rm --entrypoint sh …:manual2 -c 'find /app -name ".env*" -o -name "__pycache__" -o -name "*.pyc"'` → nol baris |
| Kartu yang melayani menyebut mesin pelabelnya: `kabar dilabeli CLASSIFIER=rules`, dan `/card/LIFE?date=2026-09-04` byte-identik dengan terminal | `diff <(curl -s ".../card/LIFE?date=2026-09-04") <(cd src/katalis && ./run.sh pilar LIFE 2026-09-04)` → tidak ada selisih |
| Build `3bb39bae` `SUCCESS` di kelima langkah; revisi `katalis-api-00003-r8l` melayani 100% | `gcloud builds describe 3bb39bae…` · `gcloud run services describe katalis-api` |
| Scheduler memicu job, dan job menulis kartu ke bucket | `gcloud scheduler jobs run katalis-refresh-daily` → eksekusi `katalis-refresh-xs7ps` `Completed` dalam 4,31 s; `gcloud storage cat gs://katalis-recorded/cards/recorded/LIFE/2026-09-01.txt` byte-identik dengan CLI |

| Terverifikasi **lokal** (perintah dijalankan di mesin ini, 2026-09-12) | Perintah |
| --- | --- |
| 297 gate hijau di 44 fungsi check, exit 0 | `cd src/katalis && ./run.sh test` |
| LIFE `siap`, 62 hari bursa, 7 hari aliran broker | `./run.sh symbols` |
| Kartu LIFE terbit: `BERGERAK TANPA PENJELASAN · FLOAT TIPIS · free float 7.5%` | `./run.sh pilar LIFE 2026-09-01` |
| Kartu LIFE mencetak `artikel_menjelaskan 0 · artikel_melaporkan 1`, dan `/v2/news/ → timestamp, symbols, title, tags, dimension` ada di blok FIELD | `./run.sh pilar LIFE 2026-09-01` |
| Kartu LIFE mencetak asal 16 ambang yang dipakainya, semuanya `shipped` | `./run.sh pilar LIFE 2026-09-01` → baris `ambang dipakai:` |
| Header `Access-Control-Allow-Origin: *` hadir pada `/card/…`, `/health`, `/healthz` dan pada penolakan `/nope` | `python3 -c` atas `server._probe`; gate `check_cors_header_is_on_every_reply` |
| Modifier suspensi terbit hanya setelah peristiwanya: `2026-09-01` diam, `2026-09-04` berbunyi `PERNAH DISUSPENSI · 2026-09-04` | `./run.sh pilar LIFE 2026-09-01` lalu `2026-09-04` |
| Kartu LIFE `2026-09-10` ditolak `tanpa_broker` — tape broker berakhir `2026-09-04` | `./run.sh pilar LIFE 2026-09-10` |
| Pilar Katalis LIFE `2026-09-01` kini `[bahaya]` dan verdictnya `BERGERAK TANPA PENJELASAN` — **D2 tertutup 2026-09-12**, dan gate `check_life_2026_09_01_is_an_unexplained_move` mengulanginya tiap build | `./run.sh pilar LIFE 2026-09-01` |
| Membalik satu label LIFE di `classify.CASES` membuat gate tugas 6 merah, `4/5`, exit 1 | monkeypatch `classify.CASES` + `pillars.check_life_2026_09_01_is_an_unexplained_move()` |
| Gate sitasi menolak ketiga suntikan (**ditutup Fase 0**) | monkeypatch `card.render` + `check_every_number_is_a_figure()` |
| Berkas ambang hasil belajar yang diracuni membuat suite merah, exit 1 (**ditutup Fase 0**) | tulis `state/thresholds.learned.json`, lalu `./run.sh test` |
| `actions` dipotong `as_of`; aksi bertanggal `2026-12-31` tidak lagi masuk kartu (**ditutup Fase 0**) | suntikan `sources.corporate_actions` + `check_as_of_does_not_leak` → `([], 3)` |
| `DEMO_CASES` memuat kasus `recorded/LIFE` (**ditutup Fase 0**) | `python3 -c "import pillars;print(pillars.DEMO_CASES)"` |
| `CLASSIFIER` hidup di lima berkas (`card.py` 12, `classify.py` 7, `server.py` 6, `cli.py` 1, `pillars.py` 1); nol referensi `llm`, `lesson`, hold-out | `grep -rc CLASSIFIER src/katalis/*.py` |
| `state/` tidak ada di `src/katalis/` | `ls src/katalis/state` |
| 18 ambang di `thresholds.TABLE` | `python3 -c "import thresholds as T; print(len(T.TABLE))"` |
| Headline pilar masih memakai pembulatan sendiri (`65%` vs figure `64.7%`, `2.2` vs `2.17`) | `./run.sh pilar LIFE 2026-09-01` — blocker B14, **tidak disentuh Fase 4**: ia tidak termasuk enam tugas berkas fase |
| 20 baris suspensi atas 17 simbol unik | `python3` atas `research/harness/recorded/v2_suspensions.json` |
| 136 berkas payload terekam | `ls research/harness/recorded/*.json \| wc -l` |
| Tidak ada `.env` atau `__pycache__` terlacak | `git ls-files \| grep -E '\.env\|__pycache__'` → `.env.example` |

| **Sekadar diklaim** (tidak dapat diverifikasi dari repo) | |
| --- | --- |
| Onboarding sectors.app tiap peserta sebelum baris kode pertama | Blocker B7 |
| Apakah ada anggaran dan peringatan biaya di akun penagihan | Proyek tertaut ke akun berbayar, bukan trial; pemakaian di atas Always Free ditagih. Lihat `TODO.md` |
| ~~Tiga commit lokal (`6128b4b`, `7121ef2`, `83fe2a1`) belum di-push~~ **sudah tidak benar** — `origin/master` di `29660a1`, sama dengan ujung Fase 3 | `git ls-remote origin refs/heads/master` → `29660a1…` |
| Kredit tersisa **tepat** ≈616 | Ekspor portal terakhir bertanggal `2026-09-05`; belanja sesudahnya hanya diketahui dari ledger. Blocker B3 |

---

## Tugas berikutnya

Fase 4 menutup D2 dan B6. Kartu LIFE `2026-09-01` berbunyi **BERGERAK TANPA PENJELASAN**,
pilar Katalisnya `[bahaya]`, dan gate `check_life_2026_09_01_is_an_unexplained_move`
mengulanginya tiap build — kartu itu berhenti menjadi ilustrasi dan menjadi kasus uji. Dua
angka lama yang menghitung setiap artikel sampai awal tape (`artikel_mendahului`,
`artikel_mengikuti`) diganti oleh `artikel_menjelaskan` dan `artikel_melaporkan`, yang
dipotong `news_lookback_days` — ambang yang sampai fase ini dideklarasikan dan tidak pernah
dibaca. Kartu juga mencetak asal tiap ambang yang dipakainya (B11 ditutup).

Yang belum: **revisi Cloud Run baru** (B18). `katalis-api-00003-r8l` melayani Fase 3, jadi
kriteria keluar 8 dan `[x]` untuk Fase 4 menunggu satu `gcloud builds submit`. Trigger push
(B17) juga masih menunggu handshake OAuth GitHub di konsol, dan perintah setelahnya sudah
tertulis di `infra/trigger.sh`.

---

## Blocker

Baris bertanda pemilik **Saya (manusia)** punya langkah konkretnya di
[`TODO.md`](TODO.md); tabel ini hanya menyatakan keadaannya.

| # | Blocker | Pemilik | Fase | Keadaan |
| --- | --- | --- | --- | --- |
| B1 | Gate sitasi menguji keanggotaan token, bukan asal angka | Anda (agen) | 0 | **tertutup 2026-09-12** — gate membandingkan multiset token kartu terhadap yang `_render()` sendiri keluarkan; ketiga suntikan ditolak |
| B2 | `check_learned_cannot_escape()` tidak pernah membuka berkas ambang hasil belajar | Anda (agen) | 0 | **tertutup 2026-09-12** — gate membaca berkas; `top1_dominant: 0.99` membuat `./run.sh test` exit 1 |
| B3 | Angka kredit di PRD §0 (272) dan §5 (plafon 332) lebih rendah 105 daripada tagihan portal (377). Ekspor portal terakhir `2026-09-05`, jadi sisa nyata hanya diketahui sampai tanggal itu | Saya (manusia) — ambil ekspor portal baru | 5 | terbuka |
| B4 | `actions` tidak dipotong `as_of` | Anda (agen) | 0 | **tertutup 2026-09-12** — `bag_from()` memotong `actions`; `check_as_of_does_not_leak` membandingkan tiap figure pada tiap kartu demo |
| B5 | `DEMO_CASES` hanya memuat kasus sintetis | Anda (agen) | 0 | **tertutup 2026-09-12** — `("recorded", "LIFE", "2026-09-01")` masuk, dan keempat gate kartu mengulangi seluruh tuple |
| B6 | Pilar Katalis berbunyi `tenang` pada LIFE, menyitir "Top Gainers" dan berita suspensi sebagai kabar yang mendahului | Anda (agen) | 3 lalu 4 | **tertutup 2026-09-12** — kartu `2026-09-01` berbunyi `BERGERAK TANPA PENJELASAN`, pilar Katalis `[bahaya]`, dan Top Gainers tidak lagi disitir sebagai kabar yang mendahului; digate oleh `check_life_2026_09_01_is_an_unexplained_move` |
| B7 | Onboarding sectors.app tiap peserta sebelum baris kode pertama tidak dapat diverifikasi dari repo. Commit pertama `2026-09-05`. **Tidak dapat diperbaiki mundur** | Saya (manusia) | kelayakan | terbuka |
| B8 | Video juri, video teaser, dan post media sosial: nol bukti hari ini. Ketiganya syarat submission | Saya (manusia) | 7 | terbuka — **bagian "repo publik" tertutup 2026-09-12**: `gh repo view aliefauzan/SectorsResearch` → `PUBLIC`, dibuat `2026-09-05` |
| B9 | Dua repo. PRD di `SectorsHackathon` (14 berkas, semuanya `.md`); kode di repo ini, remote `SectorsResearch`. Form submission meminta satu tautan, dan kedalaman teknis diverifikasi terhadap repo itu. PRD §12.1 menyebut nama repo yang berbeda dari remote yang sebenarnya | Saya (manusia) | 7 | terbuka |
| B10 | Track 01 mewajibkan komponen AI/LLM dan orkestrasi milik sendiri. Jalur default KATALIS deterministik; yang memenuhi palang adalah Fase 6. Kalau Fase 6 dipotong, deklarasi track harus berpindah ke Track 03 **sebelum** submit | Saya (manusia) — keputusan | 6 / 7 | terbuka |
| B11 | Kartu tidak menyebut asal ambang (`shipped` / `learned`) maupun classifier yang dipakai, padahal PRD §7 dan §13 menyatakan ia menyebut keduanya | Anda (agen) | 3 dan 4 | **tertutup 2026-09-12** — kartu mencetak `kabar dilabeli CLASSIFIER=rules` (Fase 3) dan satu baris `ambang dipakai:` dengan `shipped`/`learned` untuk tiap ambang yang benar-benar dibaca (Fase 4); dua gate terpisah |
| B12 | PRD §0 mengutip `cat src/katalis/state/thresholds.learned.json` untuk angka "18/18 ambang `shipped`". Berkas itu tidak pernah ada | Anda (agen) | 6, atau koreksi PRD lebih awal | terbuka |
| B16 | Kartu LIFE tidak dapat dinilai setelah `2026-09-04`: tape `/v2/broker-summary/` berakhir di sana, jadi tanggal yang lebih baru ditolak `tanpa_broker`. Ini benar, dan ia membatasi tanggal mana yang bisa dipakai demo maupun gate | — | 5 | terbuka — hilang sendiri kalau jendela broker LIFE dibeli lebih panjang; tidak dianggarkan |
| B14 | Headline pilar memakai pembulatannya sendiri: kartu LIFE menulis `65%` sementara figure-nya `64.7%`, dan `2.2` sementara figure-nya `2.17`. Gate baru menerima keduanya karena renderer memang mengeluarkan keduanya; menuntut headline memakai angka figure apa adanya berarti mengubah format keempat pilar | Anda (agen) | 4 | **tetap terbuka** — Fase 4 menjalankannya dan tidak menyentuhnya: keenam tugas berkas fase tidak memuatnya, dan menutupnya berarti satu formatter bersama untuk headline dan figure di keempat pilar. Dinaikkan ke orkestrator, bukan dikerjakan diam-diam |
| B18 | Kartu Fase 4 belum dilayani Cloud Run: `katalis-api-00003-r8l` adalah image Fase 3, jadi `GET /card/LIFE?date=2026-09-01` dari URL publik masih menjawab `SATU PEMBELI DOMINAN` dan tanpa header CORS | Saya (manusia) — satu `gcloud builds submit` | 4 | terbuka — perintahnya ada di `TODO.md`; sesi Fase 7 menunggu revisi ini untuk membuktikan kriteria 1-nya |
| B15 | `README.md` tingkat repo belum ada | Anda (agen) | 7 | terbuka — dipindah dari Fase 0 lewat bagian Kalau Ini Melar |
| B17 | Trigger Cloud Build dari push belum ada: `gcloud builds connections list` → nol. Menyambungkan `aliefauzan/SectorsResearch` menuntut handshake OAuth GitHub yang tidak punya bentuk CLI. Commitnya sendiri sudah di origin sampai `29660a1` (diperiksa 2026-09-12), jadi yang tersisa hanya handshake-nya. Sampai itu selesai, kriteria keluar 1 Fase 2 terbuka dan kriteria 2 hanya terbukti lewat `builds submit` | Saya (manusia) — sambungkan repo di konsol, lalu `infra/trigger.sh` | 2 | terbuka |
| B13 | PRD §6 menulis S3 sebagai "dua simbol, 12 kredit"; §7 dan §9 menulis "enam simbol, 42 kredit" | — | 5 | **tertutup 2026-09-12** — rencana memakai enam simbol / 42 kredit, alasannya di `plan/README.md` |

---

## Fase

| Fase | Berkas | Keadaan | Kredit | Catatan |
| --- | --- | --- | --- | --- |
| 0 · Fondasi | `phases/phase-0-foundation.md` | `[~]` | 0 | Tujuh dari tujuh tugas dikerjakan; `README.md` tingkat repo dipindah ke Fase 7 (B15) — satu butir `[~]`, jadi fasenya `[~]`, bukan `[x]`. 73 → 94 gate. Sejak Fase 2 ia **terverifikasi hidup**, bukan lagi hanya lokal |
| 1 · Modifier suspensi | `phases/phase-1-suspension-modifier.md` | `[x]` | 0 | Lima tugas, enam kriteria, semuanya terpenuhi, dan sejak `katalis-api-00002-c5r` **terverifikasi hidup** — modifier suspensi terbit dari URL, bukan hanya dari terminal. 94 → 98 gate |
| 2 · Pipeline deploy | `phases/phase-2-deploy-pipeline.md` | `[~]` | 0 | Tujuh dari delapan tugas selesai dan berjalan; **tugas 8 (trigger push) menunggu OAuth GitHub — B17**, dan karena itu kriteria keluar 1 terbuka dan kriteria 2 hanya terbukti lewat `builds submit`. 98 → 128 gate |
| 3 · Klasifikasi deterministik | `phases/phase-3-deterministic-classifier.md` | `[x]` | 0 | Enam tugas, tujuh kriteria, semuanya terpenuhi dan berjalan pada `katalis-api-00003-r8l`. `classify.py` lahir murni dan bertabel; `CLASSIFIER` dibaca di satu tempat dan menolak nilai asing dengan exit 2. 128 → 243 gate |
| 4 · Verdict pilar | `phases/phase-4-pillar-verdicts.md` | `[~]` | 0 | Keenam tugas dan tujuh kriteria yang dapat diperiksa sendiri terpenuhi — kartu LIFE kini `BERGERAK TANPA PENJELASAN` dengan pilar Katalis `[bahaya]`, digate tiap build. **`[~]` karena kriteria 8 menuntut revisi Cloud Run baru, dan `katalis-api-00003-r8l` masih image Fase 3 — B18.** 243 → 297 gate |
| 5 · Korpus berlabel | `phases/phase-5-labeled-corpus.md` | `[ ]` | **42** | Menunggu B3 ditutup sebelum satu panggilan dibuat |
| 6 · Loop belajar dan model | `phases/phase-6-learning-and-llm.md` | `[ ]` | 0 / kuota model | Potongan pertama di garis potong. Memotongnya memindahkan track |
| 7 · Permukaan dan submission | `phases/phase-7-surface-and-submission.md` | `[ ]` | 0 | Tidak pernah dipotong |

Keadaan yang dipakai hanya tiga: `[ ]` belum · `[x]` selesai, ter-commit, **dan** berjalan
pada revisi Cloud Run yang melayani · `[~]` sengaja dilewati dengan alasan di baris yang sama.

---

## Metrik §5, keadaan hari ini

| Metrik | Target | Hari ini |
| --- | --- | --- |
| Kartu penuh di atas data nyata | ≥3 simbol | **1** (LIFE) |
| Peringatan mendahului peristiwa berlabel | ≥2 dari 3 | **1 dari 1** — verdict tertinggi `2026-08-27`, suspensi `2026-09-02` |
| Kebisingan pada replay berlabel | ≤40% | **belum diukur** — Fase 6 |
| Loop belajar hidup | ≥6 lesson, ≥1 hold-out | **0 lesson** |
| Terbaca tanpa dipandu | 3 dari 3 | **0 percakapan** |
| Kredit | belanja tambahan ≤60 | **0 dibelanjakan sejak rencana ini ditulis**, Fase 2 termasuk; 42 dianggarkan untuk Fase 5 |

---

## Pertanyaan terbuka yang membuat sebuah fase belum dapat dispesifikasi penuh

Tiap baris menyebut fase yang terpengaruh dan satu pertanyaan yang membukanya.

| Fase | Yang PRD diamkan | Pertanyaan yang membuka |
| --- | --- | --- |
| 2 | ~~Proyek GCP, akun penagihan, dan kapan 90 hari trial dimulai~~ | **terjawab** — `ada-sectors-508410`, akun `01B951-232B54-4E1D9A`, bukan akun trial, jadi pemakaian di atas Always Free ditagih |
| 2 | Apakah biaya keluar-region benar-benar muncul | Layanan di `asia-southeast2`, bucket di `us-east1` — satu region US karena Always Free tidak berlaku untuk multi-region `US`. Satu objek 2.971 byte per hari bursa; periksa tagihan sebelum volumenya naik |
| 3 / 4 | Berapa artikel per simbol yang perlu diklasifikasi sebelum pilar Katalis berubah bunyinya. Pada LIFE `2026-09-04` ada tiga yang mendahului: dua `menjelaskan`, satu `melaporkan` — dan tiga terlalu kecil untuk menyatakan aturan tangan kalah | Berapa artikel dalam korpus Fase 5, dan berapa di antaranya yang label tangannya berbeda dari keluaran aturan |
| 5 | Enam simbol mana yang dibeli | Berapa sisa kredit sebenarnya setelah ekspor portal baru (B3), dan simbol berlabel mana yang punya deret harian cukup panjang |
| 5 / 6 | Simbol mana yang menjadi hold-out | Sama seperti di atas; kandidat yang belum pernah disentuh kode adalah NICK.JK, PPGL.JK, SAFE.JK |
| 6 | Penyedia model untuk S7 dan berapa biayanya | Vertex AI dari sisa trial, atau penyedia luar dengan satu secret tambahan. PRD menunda keputusan sampai M9 hijau, dan itu masih pilihan yang benar |
| 6 | Jendela "mendahului" untuk menghitung hit versus false alarm | Berapa hari bursa sebelum suspensi sebuah verdict tinggi masih dihitung mendahului |
| 7 | Siapa tiga orang yang diwawancarai dan lewat apa | Apakah mereka pengguna nyata dari persona §3, atau orang terdekat — jawabannya mengubah nilai buktinya |

---

## Session Log

Append-only. Satu entri per sesi, bertanggal. **Jangan pernah menulis ulang atau menghapus
entri yang sudah ada, termasuk entri Anda sendiri.**

### 2026-09-12 — `plan/` dibangkitkan

Menulis seluruh direktori `plan/` dari `katalis-v9.prd.md`, `JURI-v9-penilaian.md`,
`JURI-v8-penilaian.md`, `MARKET-RESEARCH-v1.md`, dan repo ini. Tidak ada kode produk yang
disentuh; tidak ada PRD baru yang dibuat.

Dijalankan untuk menyemai berkas ini: `./run.sh test` (73 hijau, exit 0), `./run.sh symbols`,
`./run.sh pilar LIFE 2026-09-01`, `reconcile_usage.py`, `capture.py --report`, plus tiga
reproduksi serangan dari JURI-v9 — suntikan angka karangan, peracunan
`state/thresholds.learned.json`, dan suntikan aksi korporasi bertanggal masa depan. Ketiganya
masih tembus hari ini, dan menjadi B1, B2, dan B4.

Dua koreksi terhadap PRD yang dibuat di sini dan harus dibawa ke PRD sendiri: angka kredit
(B3) dan nama repo di §12.1 (B9). Satu perselisihan internal PRD ditutup: S3 adalah enam
simbol / 42 kredit, bukan dua / 12 (B13).

Berkas `state/thresholds.learned.json` yang dibuat untuk reproduksi serangan sudah dihapus;
`ls src/katalis/state` kembali mengembalikan `No such file or directory`.

### 2026-09-12 — Fase 0 dijalankan

Tujuh tugas, enam selesai penuh, satu dilewati sebagian. Gate 73 → **94**, exit 0.

Ditutup: B1 (gate sitasi kini membandingkan multiset token kartu terhadap token yang
`_render()` sendiri keluarkan — ketiga suntikan yang kemarin hijau sekarang merah), B2
(`check_learned_cannot_escape()` membuka `state/thresholds.learned.json` dan menolak nilai yang
harus dijepit; berkas beracun membuat suite exit 1), B4 (`actions` melewati `upto()`, dan
`check_as_of_does_not_leak` membandingkan **tiap** figure pada tiap kartu demo alih-alih satu
figure pada satu simbol sintetis), B5 (`DEMO_CASES` memuat `recorded/LIFE`, dan keempat gate
kartu mengulangi seluruh tuple). D4 ditutup di catatan `baseline_days`.

Dibuka: B14 (headline pilar memakai pembulatan sendiri — gate baru sah menerimanya, tetapi
klaim "tiap angka membawa sitasinya" baru benar penuh setelah Fase 4 menyeragamkan format
headline) dan B15 (`README.md` tingkat repo, dipindah ke Fase 7 lewat bagian Kalau Ini Melar
milik Fase 0).

Nol kredit dibelanjakan. `state/thresholds.learned.json` yang dipakai menguji gate sudah
dihapus; `ls src/katalis/state` kembali `No such file or directory`.

### 2026-09-12 — Fase 1 dijalankan

Lima tugas, semuanya selesai. Gate 94 → **98**, 19 fungsi check, exit 0, nol kredit.

`/v2/suspensions/` — satu-satunya aset Sectors yang absen dari 28 rilis dan 39 resep — kini
menjadi modifier kartu, lahir sebagai `Figure` bernama `pernah_disuspensi` dengan endpoint dan
field-nya sendiri, bukan sebagai tempelan string. Figure tingkat kartu adalah bentuk baru di
`assess()` (`result["modifier_figures"]`), dan blok FIELD mengiterasi keduanya.

Satu koreksi terhadap rencana, dicatat alih-alih diam-diam diperbaiki: Kriteria keluar 3
menulis `2026-09-10`, dan tanggal itu tidak bisa dipakai karena tape broker LIFE berakhir
`2026-09-04` dan kartu yang lebih baru ditolak `tanpa_broker`. Gate memakai `2026-09-04`.
Batas tanggal itu dicatat sebagai B16.

Fase 0 dan Fase 1 keduanya `[x]` dalam bentuk yang lebih lemah yang `plan/README.md` izinkan
sebelum Fase 2: selesai dan ter-commit, terverifikasi lokal. Keduanya harus dinaikkan ke bentuk
penuh begitu ada revisi Cloud Run yang melayani.

### 2026-09-12 — infrastruktur Fase 2 disiapkan

Bukan Fase 2 itu sendiri; hanya langkah-langkah konsol yang mendahuluinya, dijalankan atas
permintaan langsung.

`ada-sectors-508410` ("ADA sectors") ditautkan ke penagihan dan enam API diaktifkan: `run`,
`cloudbuild`, `artifactregistry`, `secretmanager`, `storage`, `cloudscheduler`.
`SECTORS_API_KEY` dimuat ke Secret Manager sebagai satu versi aktif, dialirkan dari `.env`
lewat pipa sehingga nilainya tidak pernah tercetak; kecocokannya diperiksa dengan SHA-256, dan
`.env` tetap tidak terlacak git.

Satu penyimpangan dari pilihan yang diminta: akun penagihan yang dipilih,
`01B951-232B54-4E1D9A` ("My Billing Account"), menolak dua kali dengan
`FAILED_PRECONDITION: Cloud billing quota exceeded` — bukan karena jumlah proyek, karena hanya
tiga yang tertaut di sana. Proyek ditautkan ke `018056-334B67-5DE9C0` ("free trial") sebagai
gantinya, yang berarti biaya keluar dari kredit welcome alih-alih dari kartu. Memindahkannya
kembali adalah satu perintah, dan barisnya ada di `TODO.md`.

`cloudbuild.yaml`, `Dockerfile`, `.dockerignore` dan `server.py` belum ditulis — Fase 2 belum
dimulai. Nol kredit Sectors dibelanjakan.

### 2026-09-12 — penagihan dipindah ke akun yang semula dipilih

`tubesabp-459213` dilepas dari `01B951-232B54-4E1D9A`, kuota terbuka, dan `ada-sectors-508410`
ditautkan ulang ke akun itu: `billingEnabled: True`. Singgahnya di akun "free trial" berakhir.

Diperiksa setelah pemindahan, karena mengganti akun penagihan bisa menjatuhkan layanan:
keenam API tetap aktif, dan `SECTORS_API_KEY` versi 1 tetap `enabled` dengan SHA-256 yang
masih cocok dengan `.env`.

Konsekuensi yang perlu dipegang: ini bukan akun trial, jadi pemakaian di atas Always Free
ditagih alih-alih dipotong dari kredit welcome. Baris anggaran dan peringatan biaya
ditambahkan ke `TODO.md`.

### 2026-09-12 — Fase 2 dijalankan

Tujuh dari delapan tugas selesai **dan berjalan**. Gate 98 → **128** di 26 fungsi check,
exit 0. Nol kredit Sectors.

Ada revisi Cloud Run yang melayani untuk pertama kalinya: `katalis-api-00002-c5r` di
`https://katalis-api-ibyebnreqa-et.a.run.app`, dan `diff` atas
`/card/LIFE?date=2026-09-01` terhadap `./run.sh pilar LIFE 2026-09-01` tidak menemukan
selisih. Itu memindahkan Fase 1 dari "terverifikasi lokal" ke `[x]`, dan memindahkan Fase 0
dari "terverifikasi lokal" ke terverifikasi hidup — tetapi **bukan** ke `[x]`, karena ia masih
memuat satu butir `[~]` (B15) dan `plan/README.md` melarangnya.

Dua modul baru, keduanya dengan gate sendiri yang masuk `./run.sh test`:
`server.py` (17) dan `publish.py` (13). Keduanya sengaja tidak menghitung apa pun —
`check_this_module_computes_nothing` dan `check_bodies_are_the_card_verbatim` menuntut badan
tiap balasan dan tiap objek bucket adalah stdout `card.show()` apa adanya, dan
`check_card_route_matches_the_cli` membuktikannya dengan menjalankan `cli.py` sebagai proses
terpisah lalu membandingkan byte. Batas eksekusi 2 ("deploy tidak menambah fitur") jadi
sesuatu yang gate-nya periksa, bukan sesuatu yang review-nya ingat.

Kriteria 2 dibuktikan dengan benar-benar merusak sesuatu: satu baris ditambahkan ke
`check_table()`, `SHORT_SHA=broken1` dikirim, dan build `60e1a5c0` berakhir `FAILURE` pada
langkah `test` — `hygiene`, `push` dan `deploy` tidak pernah berjalan, revisi yang melayani
tidak bergerak, dan tag `broken1` tidak ada di registry. Kerusakannya dibalik dan suite kembali
exit 0.

Empat penyimpangan dari teks fase, dicatat alih-alih diam-diam dibetulkan:

1. **`/healthz` tidak pernah sampai di belakang Cloud Run.** Front end Google menjawabnya
   sendiri dengan HTML 404 miliknya dan permintaannya tidak muncul di log revisi, padahal di
   dalam container ia benar. `/health` adalah handler yang sama dengan nama yang lolos.
   Keduanya ada dan keduanya digate.
2. **Image membawa `research/harness/synth/`**, bukan hanya `recorded/`. `DEMO_CASES` memuat
   satu kasus sintetis, jadi tanpa `synth/` langkah `test` di dalam image merah — dan tugas 3
   adalah tugas yang tidak boleh dipotong. 7,2 MB dari batas 0,5 GB.
3. **Bucket di `us-east1`, bukan multi-region `US`.** Always Free Cloud Storage berlaku untuk
   satu region US dan tidak untuk multi-region, jadi `-l US` menagih dari byte pertama.
4. **Satu langkah build yang tidak diminta: `hygiene`.** Batas eksekusi 7 berbicara tentang
   image, dan `.dockerignore` yang benar bukan bukti bahwa image-nya bersih.

Satu berkas yang tidak diminta dan ternyata perlu: `.gcloudignore`. Tanpanya
`gcloud builds submit` memakai `.gitignore`, yang memang mengecualikan `.env` — tetapi tarball
sumber adalah tempat kedua sebuah kunci bisa meninggalkan laptop ini, dan "kebetulan aman"
bukan jaminan.

Dibuka: B17 — trigger push. `gcloud builds connections list` mengembalikan nol, dan koneksi
GitHub menuntut OAuth di konsol. `infra/trigger.sh` memuat perintah setelahnya utuh, jadi yang
tersisa adalah satu klik lalu satu perintah. Sampai itu, kriteria keluar 1 terbuka dan
kriteria 2 hanya terbukti lewat `builds submit`.

### 2026-09-12 — Fase 3 dijalankan

Enam tugas, semuanya selesai. Gate 128 → **243** di 40 fungsi check, exit 0, nol kredit
Sectors dan nol kuota model. Revisi `katalis-api-00003-r8l` melayani perubahannya, dan
`/card/LIFE?date=2026-09-04` masih byte-identik dengan terminal.

`classify.py` lahir sebagai modul murni: `RULES` adalah tabel berbaris
`(label, aturan, sinyal, jarum)` dan `label()` tidak tumbuh ketika sebuah pola ditambahkan.
Kemurniannya bukan klaim — `check_this_module_reads_nothing` memindai sumbernya sendiri di
atas blok gate dan merah kalau `open(`, `os.environ`, `urllib`, `socket.`, `subprocess.`
atau `sources.` muncul di sana.

Tiga label, dan yang ketiga bukan hiasan: `tak_terkait` adalah jawaban untuk artikel yang
tidak menyebut simbolnya — satu-satunya jalan ia keluar, dan ia digate terpisah.

Baris yang melaporkan didahulukan atas baris yang menjelaskan, karena artikel "Top Gainers"
LIFE bertag `Rights Issue` dan `Business Expansion` — rights issue milik **perusahaan lain**
di dalam rangkuman yang sama. Tabel yang menaruh "aksi korporasi" lebih dulu akan
melabelinya `menjelaskan` dan mengulang persis kesalahan yang fase ini ada untuk menutupnya.

`CLASSIFIER` dibaca di **satu** tempat, `card.selected_classifier()`, dan itu digate:
`check_classifier_is_read_in_one_place` memindai tiap `.py` di folder ini di atas blok
gate-nya dan menuntut daftar pembacanya persis `['card.py']`. Gate itu langsung berguna —
ia merah ketika gate `server.py` menulis `os.environ["CLASSIFIER"]` untuk membuktikan
penolakan, dan yang dibetulkan adalah pemindainya (kode produk saja), bukan gatenya.

Nilai yang tidak dikenal ditolak di tiga permukaan sekaligus: `classify.resolve()` melempar
`UnknownClassifier` yang menyebut nilainya, `cli.py` mencetaknya ke stderr dan keluar `2`,
dan `server.route()` menjawab `500` bernama alih-alih menyajikan kartu yang mengklaim mesin
yang tidak pernah jalan.

Satu penyimpangan dari teks fase, dicatat alih-alih diam-diam dibetulkan: kriteria keluar 5
menulis "kedua artikel LIFE di jendela kartu". Di kartu `2026-09-01` hanya **satu** artikel
duduk di dalam jendela; kedua artikel yang dimaksud arsitektur — "Top Gainers" `2026-08-31`
dan berita suspensi — baru berdiri berdampingan sebagai kabar yang mendahului di kartu
`2026-09-04`. Gate memakai tanggal itu, dan melabeli ketiganya: Top Gainers `melaporkan`,
suspensi `melaporkan`, laba H1 `menjelaskan`.

Yang **tidak** berubah, dan itu disengaja: bunyi kartu. Pilar Katalis LIFE masih `[tenang]`
dan headline-nya masih menyitir Top Gainers. Fase ini memasang mesinnya; Fase 4 yang
menyambungkannya ke verdict. B6 tetap terbuka, separuh pertamanya tertutup. B11 juga
separuh: kartu kini menyebut classifier-nya, belum asal ambangnya.

### 2026-09-12 — Fase 4 dijalankan

Enam tugas, semuanya selesai. Gate 243 → **297** di 44 fungsi check, exit 0, nol kredit
Sectors dan nol kuota model. Kartu LIFE `2026-09-01` berhenti berbunyi `tenang`:
headline-nya `BERGERAK TANPA PENJELASAN`, pilar Katalisnya `[bahaya]`, dan
`check_life_2026_09_01_is_an_unexplained_move` mengulanginya tiap build. B6 tertutup.
B11 tertutup: kartu mencetak satu baris `ambang dipakai:` dengan `shipped`/`learned` untuk
tiap ambang yang benar-benar dibaca, dan `check_card_names_threshold_origins` menuntut tiap
baris itu ada di kartu.

**Penyimpangan pertama, dicatat alih-alih diam-diam dibetulkan.** Tugas 1 menulis
`artikel_mendahului` "berhenti menghitung artikel di dalam jendela lookback dan mulai
menghitung yang berlabel `menjelaskan`", dan tugas 4 mengizinkan angka lama "tetap ada atau
diganti". Saya menggantinya. Kalau keduanya dipertahankan, satu kartu akan mencetak
`menjelaskan_mendahului 2` tepat di bawah headline yang berkata tidak ada yang menjelaskan —
dua angka yang benar dengan dua arti berbeda, di satu blok, pada shot terpenting video.
Empat angka lama (`artikel_mendahului`, `artikel_mengikuti`, `menjelaskan_mendahului`,
`melaporkan_mendahului`) hilang, digantikan `artikel_menjelaskan` dan `artikel_melaporkan`
yang dipotong `news_lookback_days`. Ambang itu sampai fase ini dideklarasikan dan **tidak
pernah dibaca**: setiap artikel sampai awal tape dihitung "mendahului". Gate Fase 3
`check_catalyst_counts_what_it_labelled` karena itu ditulis ulang atas nama baru dengan
assertion yang sama banyaknya — bukan dihapus, bukan dilonggarkan.

**Penyimpangan kedua: satu header CORS ditambahkan ke `server.py`.**
`Access-Control-Allow-Origin: *` dikirim pada setiap balasan `GET`, termasuk penolakan 400
dan 404. Alasannya permintaan lintas sesi yang disetujui manusia: halaman baca-saja Fase 7
hidup di asal lain, dan tanpa header itu peramban di sana tidak bisa membaca kartu yang ia
memang boleh baca. Batasnya dipegang: **satu header**, dan badan balasan tidak disentuh sama
sekali — `check_bodies_are_the_card_verbatim` dan `check_card_route_matches_the_cli` masih
hijau, artinya byte kartu dari URL masih sama dengan `card.show()` dan `cli.py`. Gate baru
`check_cors_header_is_on_every_reply` (5 assertion) menahannya supaya deploy berikutnya tidak
diam-diam menjatuhkannya.

Apakah ini pelanggaran batas eksekusi 2 ("deploy tidak menambah fitur")? **Menurut saya
tidak, dan inilah alasannya.** Batas itu melarang lapisan permukaan mengubah apa yang
dihitung — katanya sendiri, "setiap baris logika baru yang muncul karena sekalian sudah di
Cloud Run ditolak di review". Header ini tidak menghitung apa pun, tidak menyentuh satu
`Figure`, dan tidak mengubah satu byte kartu. Ia juga tidak memperluas apa yang dapat
dibaca: kartu ini publik, tanpa kunci, tanpa autentikasi, dan `curl` sudah bisa mengambilnya
dari mana saja hari ini — `*` hanya memberi peramban izin yang sama yang sudah dimiliki
setiap klien HTTP lain. Yang berubah adalah satu baris protokol transport pada permukaan yang
sudah publik. Batas itu tetap utuh: `./run.sh pilar` tidak tahu header ini ada.

**Yang tidak dikerjakan, dan disebut terang-terangan: B14 tetap terbuka.** Berkas fase ini
punya enam tugas dan B14 tidak salah satunya. Menutupnya berarti satu formatter bersama untuk
headline dan figure di keempat pilar — perubahan yang menyentuh keempat modul dan tidak
diminta satu kriteria keluar pun. Saya menaikkannya ke orkestrator alih-alih mengerjakannya
diam-diam di bawah nama "Fase 4".

**Blocker baru: B18.** `katalis-api-00003-r8l` masih image Fase 3, jadi kriteria keluar 8
belum dapat dipenuhi dari sini dan Fase 4 berhenti di `[~]`. Perintah deploynya ada di
`TODO.md`. Satu koreksi pada baris lama sekaligus: `origin/master` sudah di `29660a1`, jadi
klaim "commit lokal belum di-push" di edisi-edisi sebelumnya sudah tidak benar — yang tersisa
dari B17 hanya handshake OAuth-nya, bukan push-nya.

Diperiksa dan dicatat: tiga suntikan kriteria 6 masih ditolak (`invented`, `duplicated`,
`hidden` → ketiganya `exit would be 1`), membalik satu label LIFE di `classify.CASES`
membuat gate tugas 6 merah (`4/5`), dan `reconcile_usage.py` masih mencetak portal **377**
dengan `exit=1` seperti sebelumnya — nomornya tidak bergerak karena Fase 4 tidak memanggil
API sama sekali.
