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
| Fase berjalan | **Fase 0 dan Fase 1 selesai.** Dua dari delapan |
| Fase berikutnya | Fase 2 · Pipeline deploy |
| Revisi Cloud Run yang melayani | **tidak ada** — Fase 2 belum dimulai |
| Gate | **98 assertion hijau di 19 fungsi check**, exit 0 (naik dari 73) |
| Kredit terpakai | **377 terkonfirmasi portal** (ekspor `2026-09-05`), **≈384** termasuk tujuh baris ledger setelah tanggal ekspor |
| Kredit tersisa | **≈616 dari 1.000** |
| Produk | 6 berkas, terlacak git sejak commit `1a439e6`; 1.916 baris sebelum Fase 0 |
| Repo | 720 berkas terlacak, 15 commit, commit pertama `2026-09-05`, remote `https://github.com/aliefauzan/SectorsResearch` |
| Working tree | bersih; `master` sejajar dengan `origin/master` |

### Perintah yang menghasilkan baris-baris itu

```bash
cd src/katalis && ./run.sh test; echo "exit=$?"     # 20/20 22/22 39/39 17/17 = 98, exit=0
wc -l src/katalis/*.py src/katalis/*.sh             # Σ 1916
git ls-files src/katalis                            # 6 berkas
git ls-files | wc -l                                # 720
git log --oneline | wc -l                           # 15
git log --reverse --format='%ad %h %s' --date=short | head -1   # 2026-09-05 bb83d3a init
git remote -v
git status --porcelain                              # kosong
cd research/harness && python3 src/reconcile_usage.py
ls research/evidence/usage-log/                     # lima CSV, semuanya 2026-09-05
```

### Terverifikasi hidup · terverifikasi lokal · sekadar diklaim

| Terverifikasi **hidup** (publik, dapat dicapai orang lain) | |
| --- | --- |
| — | Nol. Tidak ada deployment. |

| Terverifikasi **lokal** (perintah dijalankan di mesin ini, 2026-09-12) | Perintah |
| --- | --- |
| 73 gate hijau, exit 0 | `cd src/katalis && ./run.sh test` |
| LIFE `siap`, 62 hari bursa, 7 hari aliran broker | `./run.sh symbols` |
| Kartu LIFE terbit: `SATU PEMBELI DOMINAN · FLOAT TIPIS · free float 7.5%` | `./run.sh pilar LIFE 2026-09-01` |
| Modifier suspensi terbit hanya setelah peristiwanya: `2026-09-01` diam, `2026-09-04` berbunyi `PERNAH DISUSPENSI · 2026-09-04` | `./run.sh pilar LIFE 2026-09-01` lalu `2026-09-04` |
| Kartu LIFE `2026-09-10` ditolak `tanpa_broker` — tape broker berakhir `2026-09-04` | `./run.sh pilar LIFE 2026-09-10` |
| Pilar Katalis berbunyi `[tenang]` pada LIFE — **defect D2 masih terbuka** | perintah yang sama |
| Gate sitasi menolak ketiga suntikan (**ditutup Fase 0**) | monkeypatch `card.render` + `check_every_number_is_a_figure()` |
| Berkas ambang hasil belajar yang diracuni membuat suite merah, exit 1 (**ditutup Fase 0**) | tulis `state/thresholds.learned.json`, lalu `./run.sh test` |
| `actions` dipotong `as_of`; aksi bertanggal `2026-12-31` tidak lagi masuk kartu (**ditutup Fase 0**) | suntikan `sources.corporate_actions` + `check_as_of_does_not_leak` → `([], 3)` |
| `DEMO_CASES` memuat kasus `recorded/LIFE` (**ditutup Fase 0**) | `python3 -c "import pillars;print(pillars.DEMO_CASES)"` |
| Nol referensi `CLASSIFIER`, `llm`, `lesson`, hold-out di `src/katalis/` | pencarian atas enam berkas |
| `state/` tidak ada di `src/katalis/` | `ls src/katalis/state` |
| 18 ambang di `thresholds.TABLE` | `python3 -c "import thresholds as T; print(len(T.TABLE))"` |
| Headline pilar masih memakai pembulatan sendiri (`65%` vs figure `64.7%`) | `./run.sh pilar LIFE 2026-09-01` — blocker B14 |
| 20 baris suspensi atas 17 simbol unik | `python3` atas `research/harness/recorded/v2_suspensions.json` |
| 136 berkas payload terekam | `ls research/harness/recorded/*.json \| wc -l` |
| Tidak ada `.env` atau `__pycache__` terlacak | `git ls-files \| grep -E '\.env\|__pycache__'` → `.env.example` |

| **Sekadar diklaim** (tidak dapat diverifikasi dari repo) | |
| --- | --- |
| Onboarding sectors.app tiap peserta sebelum baris kode pertama | Blocker B7 |
| Tanggal mulai trial GCP dan pemilik akun penagihan | `gcloud billing accounts list` menunjukkan dua akun OPEN; mana yang dipakai belum diputuskan |
| Tiga commit lokal (`6128b4b`, `7121ef2`, `83fe2a1`) belum di-push ke origin | `git log origin/master..HEAD --oneline`; lihat `TODO.md` |
| Kredit tersisa **tepat** ≈616 | Ekspor portal terakhir bertanggal `2026-09-05`; belanja sesudahnya hanya diketahui dari ledger. Blocker B3 |

---

## Tugas berikutnya

Buka `plan/phases/phase-2-deploy-pipeline.md`. Fase ini adalah yang pertama yang tidak bisa
diselesaikan sendirian oleh agen: proyek GCP, akun penagihan, secret, dan trigger Cloud Build
menuntut konsol dan kredensial. Yang bisa disiapkan lebih dulu tanpa satu klik konsol pun
adalah `server.py` (pembungkus HTTP di atas `cli.py`, keluarannya identik dengan
`./run.sh pilar`), `Dockerfile` berbasis `python:3.12-slim`, `.dockerignore` yang menolak
`.env`, `.env.*`, `__pycache__/`, `.git/` dan `research/` kecuali `research/harness/recorded/`,
dan `cloudbuild.yaml` yang menjalankan `./run.sh test` **di dalam image** sebagai langkah build.
Perhatikan cabang repo ini `master`, bukan `main`. Setelah itu berhenti dan laporkan apa yang
hanya bisa dikerjakan manusia.

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
| B6 | Pilar Katalis berbunyi `tenang` pada LIFE, menyitir "Top Gainers" dan berita suspensi sebagai kabar yang mendahului | Anda (agen) | 3 lalu 4 | terbuka |
| B7 | Onboarding sectors.app tiap peserta sebelum baris kode pertama tidak dapat diverifikasi dari repo. Commit pertama `2026-09-05`. **Tidak dapat diperbaiki mundur** | Saya (manusia) | kelayakan | terbuka |
| B8 | Video juri, video teaser, dan post media sosial: nol bukti hari ini. Ketiganya syarat submission | Saya (manusia) | 7 | terbuka — **bagian "repo publik" tertutup 2026-09-12**: `gh repo view aliefauzan/SectorsResearch` → `PUBLIC`, dibuat `2026-09-05` |
| B9 | Dua repo. PRD di `SectorsHackathon` (14 berkas, semuanya `.md`); kode di repo ini, remote `SectorsResearch`. Form submission meminta satu tautan, dan kedalaman teknis diverifikasi terhadap repo itu. PRD §12.1 menyebut nama repo yang berbeda dari remote yang sebenarnya | Saya (manusia) | 7 | terbuka |
| B10 | Track 01 mewajibkan komponen AI/LLM dan orkestrasi milik sendiri. Jalur default KATALIS deterministik; yang memenuhi palang adalah Fase 6. Kalau Fase 6 dipotong, deklarasi track harus berpindah ke Track 03 **sebelum** submit | Saya (manusia) — keputusan | 6 / 7 | terbuka |
| B11 | Kartu tidak menyebut asal ambang (`shipped` / `learned`) maupun classifier yang dipakai, padahal PRD §7 dan §13 menyatakan ia menyebut keduanya | Anda (agen) | 3 dan 4 | terbuka |
| B12 | PRD §0 mengutip `cat src/katalis/state/thresholds.learned.json` untuk angka "18/18 ambang `shipped`". Berkas itu tidak pernah ada | Anda (agen) | 6, atau koreksi PRD lebih awal | terbuka |
| B16 | Kartu LIFE tidak dapat dinilai setelah `2026-09-04`: tape `/v2/broker-summary/` berakhir di sana, jadi tanggal yang lebih baru ditolak `tanpa_broker`. Ini benar, dan ia membatasi tanggal mana yang bisa dipakai demo maupun gate | — | 5 | terbuka — hilang sendiri kalau jendela broker LIFE dibeli lebih panjang; tidak dianggarkan |
| B14 | Headline pilar memakai pembulatannya sendiri: kartu LIFE menulis `65%` sementara figure-nya `64.7%`, dan `2.2` sementara figure-nya `2.17`. Gate baru menerima keduanya karena renderer memang mengeluarkan keduanya; menuntut headline memakai angka figure apa adanya berarti mengubah format keempat pilar | Anda (agen) | 4 | terbuka |
| B15 | `README.md` tingkat repo belum ada | Anda (agen) | 7 | terbuka — dipindah dari Fase 0 lewat bagian Kalau Ini Melar |
| B13 | PRD §6 menulis S3 sebagai "dua simbol, 12 kredit"; §7 dan §9 menulis "enam simbol, 42 kredit" | — | 5 | **tertutup 2026-09-12** — rencana memakai enam simbol / 42 kredit, alasannya di `plan/README.md` |

---

## Fase

| Fase | Berkas | Keadaan | Kredit | Catatan |
| --- | --- | --- | --- | --- |
| 0 · Fondasi | `phases/phase-0-foundation.md` | `[~]` | 0 | Tujuh dari tujuh tugas dikerjakan, satu sebagian: D1, D3, D4, lubang ambang learned dan look-ahead ditutup; `README.md` tingkat repo dipindah ke Fase 7 (B15). 73 → 94 gate. Belum `[x]` karena belum ada revisi Cloud Run |
| 1 · Modifier suspensi | `phases/phase-1-suspension-modifier.md` | `[x]` | 0 | Lima tugas, enam kriteria, semuanya terpenuhi — **terverifikasi lokal**. 94 → 98 gate. Kriteria 3 dikoreksi dari `2026-09-10` ke `2026-09-04`, alasannya di berkas fase |
| 2 · Pipeline deploy | `phases/phase-2-deploy-pipeline.md` | `[ ]` | 0 | Nol komponen ada. Tidak ada `Dockerfile`, `cloudbuild.yaml`, atau proyek GCP |
| 3 · Klasifikasi deterministik | `phases/phase-3-deterministic-classifier.md` | `[ ]` | 0 | Nol referensi `CLASSIFIER` di `src/katalis/` |
| 4 · Verdict pilar | `phases/phase-4-pillar-verdicts.md` | `[ ]` | 0 | Kartu LIFE harus berhenti berbunyi `tenang` |
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
| Kredit | belanja tambahan ≤60 | **0 dibelanjakan sejak rencana ini ditulis**; 42 dianggarkan untuk Fase 5 |

---

## Pertanyaan terbuka yang membuat sebuah fase belum dapat dispesifikasi penuh

Tiap baris menyebut fase yang terpengaruh dan satu pertanyaan yang membukanya.

| Fase | Yang PRD diamkan | Pertanyaan yang membuka |
| --- | --- | --- |
| 2 | Proyek GCP, akun penagihan, dan kapan 90 hari trial dimulai | Proyek mana yang dipakai, siapa pemilik akun penagihannya, dan sudah berapa hari trial berjalan |
| 2 | Nama layanan, region, dan apakah bucket US benar-benar dipilih di atas latensi Jakarta | Apakah biaya keluar-region sudah muncul di tagihan, dan kalau belum, apakah keputusan US tetap |
| 3 | Berapa artikel per simbol yang perlu diklasifikasi sebelum pilar Katalis berubah bunyinya. Pada LIFE jumlahnya dua, dan dua terlalu kecil untuk menyatakan aturan tangan kalah | Berapa artikel dalam korpus Fase 5, dan berapa di antaranya yang label tangannya berbeda dari keluaran aturan |
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
