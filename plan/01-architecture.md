# 01 · Arsitektur

## Bentuk

Satu CLI Python pustaka standar yang membaca payload IDX terekam dari disk dan menerbitkan
satu kartu empat pilar. Tidak ada kerangka kerja, tidak ada venv, tidak ada langkah build.
Hari ini 1.916 baris di enam berkas:

```bash
wc -l src/katalis/*.py src/katalis/*.sh    # Σ 1916
```

Bentuk itu dipilih karena dua batas yang tidak bisa dinegosiasikan. Pertama, kredit: tiap
panggilan live berbiaya, jadi jalur pengembangan harus membaca disk. Kedua, kuota model:
produk harus berjalan penuh tanpa satu kunci model pun, jadi tidak ada model di jalur default.
Keduanya mendorong ke arsitektur yang sama — mesin deterministik dengan satu titik I/O.

## Lapisan

Empat lapisan, dan ketergantungannya hanya menunjuk ke bawah. Lapisan atas tidak pernah
diimpor lapisan bawah.

| Lapisan | Berkas | Tanggung jawab | Boleh menyentuh disk |
| --- | --- | --- | --- |
| Permukaan | `cli.py`, nanti `server.py` (Fase 2), halaman (Fase 7) | Parsing argumen, pemilihan perintah, kode keluar | tidak |
| Presentasi | `card.py` | Merender `Pillar` jadi teks, dan gate yang menguji hasil render | tidak |
| Domain | `pillars.py`, `thresholds.py` | `Figure`, `Pillar`, empat pilar, ambang, verdict | tidak |
| Data | `sources.py` | Pembacaan dan normalisasi payload, penolakan bernama | **ya, satu-satunya** |

Aturan yang membuat lapisan ini berguna: **`sources.py` adalah satu-satunya berkas yang tahu
di mana payload berada.** `pillars.py` dan `card.py` menerima list dict yang sudah
dinormalisasi. Itulah yang membuat lapisan `recorded` dan `synth` dapat ditukar dengan satu
flag, dan itu pula yang akan membuat bucket GCS (D7) dapat masuk di Fase 2 tanpa satu baris
pun berubah di atas lapisan data.

## Katalog modul

| Modul | Baris | Isi | Apa yang akan berubah |
| --- | --- | --- | --- |
| `sources.py` | 704 | Peta endpoint, pemuat per dataset, join registri broker, tiga tingkat asal `outstanding_shares`, `normalize_suspension()` (ada, belum dipakai kartu), penolakan bernama | Fase 1 memakai `normalize_suspension`; Fase 2 menambah pembacaan dari bucket; Fase 5 menambah simbol baru tanpa kode baru |
| `pillars.py` | 680 | `Figure`, `Pillar`, `bag_from()`, `concentration()`, `volume()`, `momentum()`, `catalyst()`, `verdict()`, `DEMO_CASES`, 8 gate | Fase 0 memperluas `DEMO_CASES` dan menutup look-ahead; Fase 3 memindahkan aturan menjelaskan-vs-melaporkan ke modul sendiri; Fase 4 mengubah `catalyst()` |
| `card.py` | 234 | `render()` dan 4 gate presentasi | Fase 0 membangun ulang render dari daftar `Figure`; Fase 1 menambah modifier suspensi ke headline |
| `thresholds.py` | 167 | `TABLE` 18 ambang `(shipped, floor, ceiling, alasan)`, `clamp()`, `provenance()`, `check_learned_cannot_escape()` | Fase 0 membuat gate benar-benar membaca berkas learned; Fase 6 menulis berkas itu dari lesson |
| `cli.py` | 98 | Empat subcommand: `pilar`, `symbols`, `method`, `test` | Fase 3 menambah pembacaan `CLASSIFIER`; Fase 6 menambah `learn` |
| `run.sh` | 33 | Pembungkus, `SOURCE` default `recorded` | Fase 2 memakai `run.sh test` sebagai langkah build |

Berkas yang **belum ada** dan disebut fase: `classify.py` (Fase 3), `server.py` + `Dockerfile`
+ `cloudbuild.yaml` + `.dockerignore` (Fase 2), `learn.py` + `state/` (Fase 6).

## Empat pilar

Empat pertanyaan, bukan empat panel. Tiga dari empat berdiri di atas data yang tidak punya
substitusi publik, dan itulah yang membuat produk ini lolos uji "cabut Sectors, produk mati".

| Pilar | Pertanyaan | Endpoint | Turunan |
| --- | --- | --- | --- |
| **Konsentrasi** | Siapa yang membeli, dan seberapa sedikit tangan | `/v2/broker-summary/{symbol}/` × `/v2/brokers/` | `pangsa_puncak`, `hhi`, `pembeli_efektif`, `pangsa_asing`, `pangsa_kohort`, `float_terserap`, `harga_masuk_puncak` |
| **Volume** | Apakah ramainya di luar kebiasaan saham itu sendiri | `/v2/daily/{symbol}/` | `volume_puncak`, `volume_z` (z robust, baseline 45 hari bursa, lantai MAD) |
| **Momentum** | Berapa banyak geraknya miliknya sendiri, bukan milik pasar | `/v2/daily/{symbol}/` + `/v2/index-daily/ihsg/` | `return_kumulatif`, `return_residual`, `beta_efektif`, `residual_z` |
| **Katalis** | Apakah ada yang **menjelaskan** geraknya, bukan sekadar **melaporkan** | `/v2/news/`, `/v2/filings/`, `/v2/company/corporate-actions/{symbol}/` | `artikel_mendahului`, `artikel_mengikuti`, `filing_material`, `aksi_korporasi` |

Pilar Katalis adalah yang paling lemah hari ini dan itu yang dibetulkan Fase 3 dan Fase 4. Ia
membaca dua artikel LIFE — sebuah "Top Gainers" dan berita suspensinya sendiri — sebagai
"kabar yang mendahului", padahal keduanya melaporkan harga yang sudah bergerak. Membedakan
sebab dari laporan adalah pekerjaan bahasa; Fase 3 melakukannya dengan aturan deterministik
supaya Fase 6 boleh gagal tanpa menjatuhkan produk.

## Topologi deploy D1–D10

Semua yang berjalan ada di GCP; satu halaman baca-saja ada di Vercel. Nol komponen di bawah
ini ada hari ini — `find . -name "Dockerfile*" -o -name "cloudbuild*"` tidak mengembalikan apa
pun di luar `.claude/worktrees/`.

| # | Komponen | Tempat | Isi | Fase |
| --- | --- | --- | --- | --- |
| D1 | `katalis-api` | Cloud Run service | `GET /card/{symbol}?date=YYYY-MM-DD` mengembalikan kartu yang identik dengan `./run.sh pilar`. `min-instances=0` | 2 |
| D2 | `katalis-refresh` | Cloud Run job | Batch: ambil data, tulis `recorded/*.json` ke GCS, render kartu. Tidak pernah dipanggil pengguna | 2 |
| D3 | `katalis-refresh-daily` | Cloud Scheduler | Satu job, satu jadwal, memicu D2. Berjalan `SOURCE=recorded` sampai ledger direkonsiliasi | 2 |
| D4 | `SECTORS_API_KEY` | Secret Manager | Satu secret, satu versi aktif, dibaca Cloud Run sebagai referensi secret — bukan variabel lingkungan literal | 2 |
| D5 | Trigger `master` | Cloud Build | Push → build image → **`./run.sh test` sebagai langkah build** → push ke Artifact Registry → deploy D1. Gate merah berarti tidak ada deploy | 2 |
| D6 | Repo Docker `katalis` | Artifact Registry | Batas Always Free 0,5 GB memaksa base `python:3.12-slim` dan kebijakan simpan 5 tag terakhir | 2 |
| D7 | Bucket `katalis-recorded` | Cloud Storage | `recorded/*.json` dan kartu terrender. Region US, karena Always Free Cloud Storage hanya US | 2 |
| D8 | Halaman kartu | Vercel | Statis, memanggil D1, tanpa kunci, tidak menghitung apa pun sendiri | 7 |
| D9 | `katalis-learn` | Cloud Run job | Sapuan replay atas simbol berlabel, menulis `lessons/*.json` dan usulan ambang ke bucket. Nol kredit | 6 |
| D10 | Panggilan model | Vertex AI atau penyedia luar | Hanya klasifikasi dan penjelasan teks. **Tidak ada Always Free**; boleh mati tanpa menjatuhkan produk | 6 |

Yang menyeberang batas kepercayaan hanya tiga aliran: Cloud Run → API Sectors (memakai secret),
Vercel → Cloud Run (tanpa secret), dan Cloud Build → Artifact Registry (tanpa secret). Kunci
tidak pernah meninggalkan GCP, dan halaman Vercel tidak pernah memegangnya.

## Pengurangan lingkup yang disengaja

Empat, dan masing-masing menukar sesuatu yang nyata.

1. **Tidak ada database.** Kartu adalah fungsi murni dari payload di disk dan `as_of`; tidak
   ada yang perlu disimpan di antara dua panggilan. Yang ditukar: tidak ada riwayat kartu, dan
   Fase 6 harus menulis `lessons/` sebagai berkas, bukan baris tabel.
2. **Tidak ada autentikasi di D1.** Endpoint kartu publik dan baca-saja. Yang ditukar: siapa
   pun bisa membakar `min-instances=0` milik kita, dan `SOURCE=recorded` membuat itu tidak
   menyentuh kredit Sectors sama sekali — yang persis mengapa D3 default `recorded`.
3. **Tidak ada penjadwalan live.** D3 berjalan `SOURCE=recorded`. Yang ditukar: kartu tidak
   pernah lebih baru dari tangkapan terakhir, dan kami menyebutkan tanggalnya di kartu
   alih-alih menyembunyikannya.
4. **Satu lapisan sintetis dipertahankan.** `synth/` tetap ada karena `check_as_of_does_not_leak`
   butuh deret 90 hari yang `recorded/` tidak punya untuk kebanyakan simbol. Yang ditukar:
   satu gate diuji di atas data yang tidak nyata, dan Fase 0 harus memastikan gate yang
   **menguji kartu** melihat kasus `recorded`, bukan hanya `synth`.

## Risiko

| Risiko | Peluang | Dampak | Mitigasi, dan fase yang memasangnya |
| --- | --- | --- | --- |
| Kerja deploy menarik perhatian dari D1/D2 | Tinggi | Tinggi | Fase 0 mendahului Fase 2. Kalau deploy melar, ia turun ke "image + build hijau" tanpa Cloud Run publik |
| Menulis dokumen lagi alih-alih kode | Tinggi | Tinggi | Direktori ini adalah dokumen terakhir. Commit berikutnya menyentuh `src/katalis/` |
| Enam peristiwa dipakai seolah populasi | Tinggi | Tinggi | Fase 6: lesson butuh ≥3 peristiwa pendukung; satu simbol hold-out; README menyebut n apa adanya |
| LLM menyentuh angka dan gate sitasi jebol | Menengah | Fatal terhadap klaim inti | Fase 0 memperbaiki gate lebih dulu; Fase 6 menjalankan keluaran LLM lewat gate yang sama |
| Produk berhenti berjalan kalau kuota model habis | Menengah | Fatal | Fase 3 (M9) mendahului Fase 6 (S7), dan `CLASSIFIER=rules` adalah default |
| Scheduler membakar kredit Sectors | Menengah | Fatal terhadap §5 | D3 berjalan `SOURCE=recorded`; pemanggilan live hanya manual |
| Kunci API bocor lewat repo atau klien Vercel | Rendah | Fatal | Secret Manager saja; `.dockerignore` di Fase 2; halaman Vercel tidak pernah memegang kunci |
| Mekanisme inti bertabrakan dengan produk Sectors sendiri | Sudah terjadi | Menengah | The Orderbook dan Foreign Flow sudah rilis Mei–Agustus 2026. Pembedanya harus S1 (suspensi) dan S2 (menjelaskan-vs-melaporkan), bukan Pilar 1 sendirian |
| Produk gagal palang Track 01 | Menengah | Tinggi | Lihat `03-hackathon-compliance.md`: kalau Fase 6 dipotong, track deklarasi berpindah ke 03 sebelum submit, bukan sesudah |
