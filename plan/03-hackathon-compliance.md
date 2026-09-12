# 03 · Keterlacakan aturan hackathon

Sumber: `research/docs/hackathon/01-rules.md`, `02-tracks.md`, `03-submission-checklist.md`.
Tiap baris di bawah menyebut aturan, keadaan hari ini, perintah yang menunjukkannya, dan fase
yang menutupnya.

## Kelayakan — lulus/gagal, bukan skor

Pemeriksaan kelayakan menilai empat hal: submission lengkap, produk berjalan, data Sectors
sebagai sumber inti, dan onboarding tiap peserta terverifikasi. Gagal di salah satunya
membuat sisanya tidak dinilai.

| Aturan | Keadaan hari ini | Bukti | Fase |
| --- | --- | --- | --- |
| WNI atau berdomisili di Indonesia | Di luar kendali repo | — | — |
| **Tiap peserta menyelesaikan onboarding sectors.app sebelum baris kode pertama** | **Tidak dapat diverifikasi dari repo.** Commit pertama `2026-09-05`; tidak ada bukti onboarding mendahuluinya | `git log --reverse --format='%ad %h %s' --date=short \| head -1` → `2026-09-05 bb83d3a init` | Blocker, bukan fase |
| Repo dibuat di dalam jendela build (≥19 Agu 2026) | **Lulus.** Commit pertama 5 September, jendela dibuka 19 Agustus | perintah yang sama | — |
| Sectors API sebagai sumber inti, bukan satu panggilan hiasan | **Lulus.** Cabut `research/harness/recorded/` dan tiap kartu berhenti terbit | `cd src/katalis && ./run.sh symbols` | — |
| Prototipe berjalan dari ujung ke ujung | **Lulus secara lokal, belum secara publik.** CLI menerbitkan kartu; tidak ada deployment | `./run.sh pilar LIFE 2026-09-01` | Fase 2 |
| Eksekusi transaksi otomatis dilarang | **Lulus.** Nol jalur order di `src/katalis/`; kartu membawa penyangkalan wajib | `./run.sh pilar LIFE 2026-09-01 \| tail -3` | — |
| Kunci API tidak boleh masuk repo publik | **Lulus.** Hanya `.env.example` terlacak | `git ls-files \| grep -E '\.env\|__pycache__'` | — |

## Code freeze

Repo dan aplikasi membeku pada saat submit, atau pada 30 September 23:59 WIB, mana yang lebih
dulu. Setelah beku: tidak ada commit, push, edit, atau perubahan apa pun — **termasuk
perbaikan bug**. Satu-satunya pengecualian adalah kredensial yang bocor, dan itu pun harus
dicabut lebih dulu lalu di-push sebagai commit yang isinya hanya penghapusan.

Konsekuensi praktis untuk rencana ini: **Fase 7 adalah fase terakhir yang boleh menyentuh
`src/katalis/`**, dan submission ditekan setelah video terunggah dan terbukti dapat diakses,
bukan sebelum. Submit lebih awal tidak membeli waktu poles; ia menghabiskan sisa jendela.

## Kredit

1.000 kredit per tim, diklaim dari portal setelah semua anggota onboarding. Non-transferable,
tanpa top-up, hangus saat event selesai. **Roster terkunci saat kredit diklaim.**

Keadaan hari ini, dari alat rekonsiliasi repo sendiri:

```bash
cd research/harness && python3 src/reconcile_usage.py
```

```
portal rows: 408   portal total: 377
ledger total (capture only): 272
difference (traffic outside capture.py): 105
```

Ekspor portal bertanggal `2026-09-05` (`ls research/evidence/usage-log/`), dan ledger memuat
tujuh baris setelah tanggal itu — pembelian LIFE. Jadi belanja nyata **≈384** dan sisa
**≈616**. Fase 5 membelanjakan 42; tidak ada fase lain yang membelanjakan apa pun.

Angka yang ditulis PRD §0 ("272 dari 1.000") dan §5 ("total ≤332") lebih rendah 105 daripada
yang portal tagih. Itu blocker terbuka, bukan catatan kaki — lihat `PROGRESS.md`.

## Palang track

Deklarasi hari ini: **Track 01 · AI Agents & Assistants**. Palangnya, dikutip dari
`02-tracks.md`:

> Proyek harus memuat **custom-built agent logic or orchestration**. Tim harus membangun
> sesuatu miliknya sendiri di sekitar model — bukan sekadar menyambungkan klien yang sudah
> ada ke Sectors.

dan, lebih tajam:

> "If the product would disappear when the team's prompt is removed from someone else's
> client, it does not meet this track's bar."

**Track 01 mewajibkan komponen AI/LLM.** Jalur default KATALIS deterministik dan memang harus
begitu (§12.3 aturan 3). Yang memenuhi palang ini adalah **Fase 6**: `katalis-learn` sebagai
orkestrasi milik sendiri (replay atas peristiwa berlabel, penghasil lesson, `clamp()` sebagai
satu-satunya jalan masuk, hold-out) ditambah `CLASSIFIER=llm` sebagai komponen model.

Karena itu satu konsekuensi harus dinyatakan sekarang, bukan dinegosiasikan di hari terakhir:
**kalau Fase 6 dipotong seluruhnya, produk tidak memenuhi palang Track 01 dan deklarasi
track harus dipindah ke Track 03 · Market Intelligence sebelum submit.** Aturan menyatakan
juri boleh memindahkan proyek ke track yang cocok alih-alih mendiskualifikasinya, tetapi
memindahkan sendiri lebih baik daripada dipindahkan, dan Track 03 tidak mewajibkan komponen
LLM sama sekali. Baris ini adalah bagian dari garis potong di `README.md`, bukan tambahan
untuknya.

## Tiga bobot penilaian, dan artefak mana yang menjawabnya

| Kriteria | Bobot | Yang dinilai | Artefak yang menjawabnya | Fase |
| --- | --- | --- | --- | --- |
| Kegunaan nyata | 40% | "Bisakah seseorang memakainya hari ini dan mendapat manfaat?" | Kartu di atas ≥3 simbol IDX nyata, dapat dicapai lewat URL publik tanpa terminal; tiga percakapan pengguna | Fase 2, 5, 7 |
| Video & storytelling | 30% | Seberapa menarik, jelas, dan terproduksi videonya | `99-demo-script.md`, video juri ≤3 menit, teaser 1 menit | Fase 7 |
| Kedalaman teknis | 30% | **Diverifikasi terhadap repo GitHub**: seberapa inovatif pemakaian Sectors API, apakah nyata dan tidak dipalsukan untuk demo | `src/katalis/` ter-commit; `./run.sh test` sebagai langkah build Cloud Build; gate yang benar-benar bisa merah; `research/harness/` | Fase 0, 2, 3, 4 |

Dua hal yang membuat 30% terakhir bisa hilang tanpa satu baris kode pun berubah: repo yang
tidak publik, dan gate yang hijau karena tidak menguji apa-apa. Yang pertama ditutup dengan
memublikasikan repo; yang kedua adalah seluruh isi Fase 0.

## Daftar submission

Enam item, semuanya wajib, dan tiga di antaranya bukan kode.

| # | Item | Keadaan | Fase |
| --- | --- | --- | --- |
| 1 | Tautan repo publik, tetap publik ≥90 hari setelah pengumuman, tanpa kunci API | Repo ada (`origin` = `https://github.com/aliefauzan/SectorsResearch`); status publik **belum diverifikasi** | Fase 7 |
| 2 | Video teaser 1 menit, terbit publik | Belum ada | Fase 7 |
| 3 | Video juri ≤3 menit, dapat diakses | Belum ada; naskah ada di `99-demo-script.md` | Fase 7 |
| 4 | Pernyataan masalah satu kalimat | Ada di `00-prd.md`, belum disalin ke form | Fase 7 |
| 5 | Pemilihan track + daftar nama peserta | Lihat bagian palang track di atas | Fase 7 |
| 6 | **Post media sosial yang menandai akun Sectors resmi** | Belum ada. Penyebab gagal yang murah dan sering terlewat | Fase 7 |

Item 6 tidak punya ketergantungan teknis apa pun dan bisa dikerjakan kapan saja; ia tetap di
Fase 7 hanya karena ia harus menunjuk ke repo dan video yang sudah terbit.

## Dua repo, satu submission

Repo pemegang PRD (`SectorsHackathon`) melacak 14 berkas, seluruhnya `.md`. Repo pemegang kode
(`Sectors`, remote `SectorsResearch`) melacak 720 berkas termasuk `src/katalis/`.

```bash
git -C /Users/af/dumpProject/SectorsHackathon ls-files | wc -l   # 14
git -C /Users/af/dumpProject/Sectors ls-files | wc -l            # 720
git -C /Users/af/dumpProject/Sectors remote -v
```

Aturan mengizinkan beberapa repo asalkan semuanya dibuat di dalam jendela build, tetapi form
submission meminta **satu** tautan repo, dan kedalaman teknis diverifikasi terhadap repo itu.
Satu repo harus dipilih dan ia harus yang memuat `src/katalis/`. PRD §12.1 menyebut repo
`aliefauzan/SectorsHackathon`; remote yang sebenarnya adalah `aliefauzan/SectorsResearch`.
Selisih itu juga menyentuh syarat Vercel Hobby ("tidak mendukung repo milik organisasi Git"):
kedua nama berada di akun pribadi, jadi S5 aman hari ini, tetapi nama yang salah di PRD harus
diperbaiki sebelum ia masuk video.
