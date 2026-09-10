# Shot list — video juri 3 menit

Pasangan [`naskah.md`](naskah.md): naskah menulis yang diucapkan, berkas ini
menulis yang terlihat. Nomor bidikan dirujuk dari naskah.

**Nol kredit.** Tidak satu pun perintah di daftar ini membuka soket ke Sectors
API. Semuanya membaca `../research/harness/recorded/`. Kalau sebuah bidikan
butuh panggilan live, bidikan itu salah — bukan anggarannya.

---

## Persiapan sekali sebelum rekam

### Terminal

| Setelan | Nilai | Kenapa |
| --- | --- | --- |
| Ukuran jendela | 100×32 kolom-baris | Paragraf CLI membungkus di ~72 kolom; 100 memberi napas tanpa mengecilkan huruf |
| Font | monospace, **18 pt minimum** | Terminal tak terbaca adalah cara termurah kehilangan nilai |
| Tema | latar terang, kontras tinggi | Kompresi YouTube memakan teks tipis di latar gelap |
| Rekaman | **1080p**, 30 fps | 720p disebut eksplisit sebagai pemakan nilai |
| Prompt shell | `$ ` polos | Prompt panjang membocorkan path dan username |
| Direktori kerja | `mersamur/` | Semua perintah di naskah relatif ke sini |

```bash
cd mersamur && python3 -m pytest app/tests -q
```

Jalankan sekali sebelum rekam. Kalau ada yang merah, jangan rekam — perbaiki dulu.

### Keamanan layar — periksa tiap bidikan

- [ ] `.env` tidak terbuka, tidak ter-`cat`, tidak muncul di autocomplete
- [ ] `SECTORS_API_KEY` tidak pernah ada di layar, termasuk di `env | grep`
- [ ] `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID` tidak terlihat
- [ ] Riwayat shell bersih — jalankan dengan shell baru, bukan sesi kerja
- [ ] Tidak ada tab browser lain, notifikasi desktop dimatikan
- [ ] Nama dan nomor telepon di tangkapan Telegram tertutup blur
- [ ] Folder `synth/` tidak pernah terbuka

### Aset yang harus disiapkan lebih dulu

| Aset | Berkas | Catatan |
| --- | --- | --- |
| Tangkapan grup Telegram | `video/aset/telegram.png` | **Grup uji milik sendiri**, bukan grup nyata. Kode saham boleh terlihat; nama, foto, nomor, handle — blur. Kalau memakai grup nyata, blur semuanya termasuk nama grup |
| Berita pembekuan MSCI | `video/aset/msci.png` | Tempo — tautan di `riset/deep-research.md` §Rujukan |
| IHSG −7,35% | `video/aset/ihsg.png` | Katadata Databoks, 28 Jan 2026 — tautan di rujukan yang sama |
| Pengumuman suspensi IDX | `video/aset/idx-<KODE>-<TANGGAL>.pdf` | Dari situs IDX, peristiwa yang **sudah selesai**. Bidikan S8 |
| Thumbnail berita | opsional | `thumbnail` di `/v2/news/` adalah URL gambar CDN — poles visual gratis, sudah dibayar |

---

## Bidikan

Kolom **jenis**: `layar` = perekaman layar, `aset` = gambar diam, `sunting` =
dirakit saat penyuntingan.

### 0:00–0:25 — masalahnya

| # | Detik | Jenis | Isi layar | Perintah / berkas |
| --- | --- | --- | --- | --- |
| S1 | 0–8 | aset | Tangkapan Telegram, zoom pelan ke pesan berisi kode saham | `video/aset/telegram.png` |
| S2 | 8–17 | aset | Judul Tempo soal pembekuan MSCI, lalu grafik Katadata | `msci.png` → `ihsg.png` |
| S3 | 17–25 | sunting | Teks di layar: `free float` dan `konsentrasi kepemilikan`, keduanya dilingkari | — |

Bar disclaimer bawah sudah menyala sejak frame pertama S1.

### 0:25–1:15 — produknya

| # | Detik | Jenis | Isi layar | Perintah / berkas |
| --- | --- | --- | --- | --- |
| S4 | 25–75 | layar | **Satu perekaman utuh tanpa cut.** Terminal kosong → ketik perintah → paragraf tercetak → gulir pelan ke blok sitasi, berhenti di baris `/v2/broker-summary/` dan `state/thresholds.json` | `python3 -m app.cli LIFE` |

Yang harus terbaca di S4, karena naskah menyebutkannya:

```
volume: sesi terakhir tercatat 24,5x median 16 sesi bertransaksi sebelumnya
konsentrasi broker 83,8% (menyala)
IDX tercatat menghentikan perdagangan LIFE sebanyak 2 kali sebelum 2026-08-10
```

Gulir sampai baris `… 21 baris sitasi seluruhnya` terlihat. Jangan potong blok
sitasi — itu klaim inti produk. Bar bawah berganti ke teks "kode saham" begitu
`LIFE` muncul.

### 1:15–2:20 — cabang A (`lessons.jsonl` berisi)

| # | Detik | Jenis | Isi layar | Perintah / berkas |
| --- | --- | --- | --- | --- |
| S5A | 75–95 | layar | `warnings.jsonl` lalu `outcomes.jsonl`, satu baris disorot di masing-masing | `python3 -m json.tool < state/warnings.jsonl` per baris, atau buka di editor dengan wrap menyala |
| S6A | 95–120 | layar | Satu baris `lessons.jsonl` diperbesar: tanggal, emiten, sumbu tersangka, margin | `state/lessons.jsonl` |
| S7A | 120–140 | layar | `thresholds.json` dibuka di `history` — versi lama dan alasannya berdampingan; lalu keluaran hold-out | `state/thresholds.json` · `python3 app/agent/evolve.py --dry-run` |

Kalau hold-out tidak membaik, **rekam itu apa adanya**. Jangan ulangi bidikan
sampai angkanya bagus.

### 1:15–2:20 — cabang B (`lessons.jsonl` kosong)

| # | Detik | Jenis | Isi layar | Perintah / berkas |
| --- | --- | --- | --- | --- |
| S5B | 75–95 | layar | Tiga berkas kosong berturut-turut, tanpa dipoles | `wc -l state/warnings.jsonl state/outcomes.jsonl state/lessons.jsonl` |
| S6B | 95–120 | layar | Loop berjalan atas keadaan kosong dan mengatakannya sendiri — tiga perintah, satu demi satu | `python3 app/agent/adjudicate.py --dry-run` → `python3 app/agent/lessons.py --dry-run` → `python3 app/agent/evolve.py --dry-run` |
| S6B-2 | — | layar | Kelewatan yang dinamai: CSMI dan TMPO, dua dari empat sumbu menyala, di bawah bar tiga | `python3 -m app.cli CSMI TMPO` |
| S7B | 120–140 | layar | `thresholds.json` `history` — satu-satunya perubahan nyata, versi 3, sumbu katalis, dengan alasannya; lalu `temuan` di backtest | `state/thresholds.json` · `python3 -c "import json;[print('-',t) for t in json.load(open('state/backtest_report.json'))['temuan'][:3]]"` |

Yang harus terbaca di S6B, verbatim dari keluaran:

```
tidak ada peringatan terbuka — tidak ada yang dinilai.
0 pelajaran akan ditulis.
tidak ada sumbu yang punya pelajaran selesai — tidak ada ambang yang diusulkan bergerak.
```

Yang harus terbaca di S6B-2, karena naskah menyebut angkanya:

```
CSMI  2 dari 4 sumbu tercatat menyala; konsentrasi broker 61,6% (menyala)
TMPO  2 dari 4 sumbu tercatat menyala; konsentrasi broker 61,6% (menyala)
```

Tanggal grid 2026-08-14; CSMI disuspensi 2026-08-28, TMPO 2026-08-27. Verifikasi
ulang keduanya di hari rekam sebelum mengucapkannya:

```bash
cd mersamur && python3 -c "from app import labels; print([(e.date,e.symbol) for e in labels.label_events() if e.symbol in ('CSMI','TMPO') and str(e.date)>='2026-08-01'])"
```

### 2:20–2:45 — bukti

| # | Detik | Jenis | Isi layar | Perintah / berkas |
| --- | --- | --- | --- | --- |
| S8A | 140–165 | sunting | Layar terbelah. Kiri: baris `warnings.jsonl`, tanggalnya disorot. Kanan: PDF IDX, tanggal pengumuman disorot | `state/warnings.jsonl` · `video/aset/idx-*.pdf` |
| S8B | 140–165 | sunting | Layar terbelah. Kiri: baris `/v2/suspensions/` dari rekaman, untuk peristiwa yang sudah selesai. Kanan: PDF IDX untuk peristiwa yang sama | keluaran `labels.label_events()` · `video/aset/idx-*.pdf` |

Kedua sisi harus menunjukkan **tanggal yang sama-sama terbaca**. Itu inti
adegannya: juri bisa mengeceknya sendiri tanpa menjalankan apa pun.

### 2:45–3:00 — tak ditunggui, dan batasnya

| # | Detik | Jenis | Isi layar | Perintah / berkas |
| --- | --- | --- | --- | --- |
| S9 | 165–172 | layar | Blok `on: schedule: cron:` disorot, lalu komentar di atasnya yang menjelaskan 11:00 WIB | `../.github/workflows/tick.yml` |
| S10 | 172–177 | layar | `runs.jsonl` digulir dari baris pertama ke terakhir — tanggal-tanggal berbeda harus terlihat bergerak. Lalu tab Actions GitHub dengan daftar run hijau | `state/runs.jsonl` · halaman Actions |
| S11 | 177–180 | sunting | Kartu disclaimer penuh layar, 3 detik | — |

S10 adalah bukti Track 02. Ia tidak bisa dikarang dan ia butuh waktu berjalan —
karena itu jendela rekam dibuka 25 September, bukan 29.

---

## Rakit dan ekspor

| Setelan | Nilai |
| --- | --- |
| Resolusi | 1920×1080, 30 fps |
| Audio | mono, ternormalisasi ke −16 LUFS; rekam ulang kalau ada dengung |
| Subtitle | `.srt` terpisah, atau terbakar — bahasa Indonesia. Banyak juri menonton tanpa suara |
| Durasi | **≤ 180 detik.** Diperiksa dengan `ffprobe` sebelum unggah |
| Berkas | `video/mersamur-juri-3menit.mp4` (tidak di-commit — lihat di bawah) |

Berkas video **tidak** masuk repo. Repo menyimpan naskah dan shot list; videonya
diunggah dan tautannya masuk formulir pengiriman.

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 video/mersamur-juri-3menit.mp4
```

**Unggah:** YouTube atau Vimeo (publik atau unlisted), Google Drive **dengan
berbagi tautan menyala**, atau Loom. Tautan yang tidak bisa dibuka = tidak
dinilai. Uji tautannya di jendela penyamaran sebelum mengirim.

---

## Daftar periksa hari rekam

- [ ] `python3 -m pytest app/tests -q` hijau
- [ ] Gerbang G1, G2, G3 di `naskah.md` dijawab; cabang dipilih dan ditulis
- [ ] Jumlah baris `runs.jsonl` dicek, dan angkanya yang diucapkan di S10
- [ ] Semua aset ada di `video/aset/`, wajah dan nama sudah diblur
- [ ] Daftar §Keamanan layar dijalani sekali per bidikan
- [ ] Bar disclaimer menyala sejak frame 0
- [ ] Tidak ada saham hidup yang disebut; semua peristiwa sudah selesai dan diumumkan
- [ ] Durasi akhir ≤ 180 detik
- [ ] Tanggal rekam ≤ **2026-09-27**
