# Fase 7 · tugas 1 — halaman baca-saja (S5, D8)

Catatan sesi, bukan pembaruan rencana. `plan/PROGRESS.md` dan `plan/phases/*` tidak disentuh
oleh sesi ini; berkas ini hanya merekam apa yang dikerjakan, apa yang terbukti, dan apa yang
masih menunggu.

Sesi: cabang `vercel-page`, worktree `sectors-8`, 2026-09-12. Nol kredit Sectors. Tidak ada
deploy, tidak ada `gcloud builds submit`, tidak ada penyambungan Vercel.

## Keadaan kriteria keluar 1

| Butir | Keadaan |
| --- | --- |
| Halaman dapat dibuka dari peramban dan menampilkan kartu | **terpenuhi** — LIFE `2026-09-01` dan `2026-09-04`, fetch langsung ke Cloud Run |
| `python3 -m http.server` polos, tanpa proxy dan tanpa rewrite | **terpenuhi** — bukti di bawah |
| `curl -s <halaman>` tidak memuat nilai kunci | **terpenuhi** |

## Apa yang dibuat

`web/index.html` — satu berkas, nol build, nol dependensi, nol kunci, nol analytics pihak
ketiga. Halaman memanggil satu alamat tetap, langsung:

```
https://katalis-api-ibyebnreqa-et.a.run.app/card/{simbol}?date=YYYY-MM-DD
```

Balasannya dicetak apa adanya di `<pre>` monospace. Tidak ada angka yang dihitung di peramban;
setiap angka di kartu keluar dari `card.show()` di sisi server. CLI tetap permukaan utama.

Alamat itu **tetap**: tidak ada `?api=` yang bisa mengarahkannya ke host lain. Override seperti
itu pernah ada untuk menunjuk tiruan lokal, dan review keamanan menandainya open-fetch /
content-spoofing — tautan jahatan bisa membuat halaman mencetak teks host penyerang sebagai
kartu KATALIS. Karena itu ia dihapus di commit `69af6c4`.

`web/README.md` — cara membuka lokal, prasyarat CORS, dan langkah Vercel yang dilakukan manusia.

Tidak ada `web/vercel.json` dan tidak ada proxy dev. Halaman berbicara ke Cloud Run langsung,
tanpa perantara, supaya tidak ada yang menyembunyikan ke mana permintaan pergi.

## Bukti kriteria keluar 1 (2026-09-12, revisi `katalis-api-00004-p7w`)

```bash
curl -s -i -H "Origin: http://127.0.0.1:8000" \
  "https://katalis-api-ibyebnreqa-et.a.run.app/card/LIFE?date=2026-09-01" | grep -iE "^(HTTP|access-control)"
# HTTP/2 200
# access-control-allow-origin: *

gcloud run services describe katalis-api --region=asia-southeast2 \
  --format='value(status.traffic[0].revisionName,status.traffic[0].percent)'
# katalis-api-00004-p7w	100
```

```bash
cd web && python3 -m http.server 8000      # polos, tanpa --cgi, tanpa proxy
# buka http://127.0.0.1:8000/
```

Di Chromium, langsung ke Cloud Run:

| Yang diperiksa | Hasil |
| --- | --- |
| `http://127.0.0.1:8000/` (muat pertama, `?symbol=LIFE&date=2026-09-01`) | `HTTP 200 · LIFE 2026-09-01` · `BERGERAK TANPA PENJELASAN · FLOAT TIPIS · free float 7.5%` — 3.650 byte, sama dengan `curl` |
| preset `LIFE 2026-09-04` | `HTTP 200 · LIFE 2026-09-04` · `… · PERNAH DISUSPENSI · 2026-09-04` — 3.735 byte, sama dengan `curl` |
| preset `LIFE 2026-09-10 (ditolak)` | `LIFE 2026-09-10: TIDAK DINILAI — tanpa_broker: no broker summary on this source for this symbol` — alasan bernama dari API, bukan halaman kosong |
| `font-family` di `<pre>` | `ui-monospace, SFMono-Regular, Menlo, Consolas, …` |

```bash
B=https://katalis-api-ibyebnreqa-et.a.run.app
for d in 2026-09-01 2026-09-04 2026-09-10; do printf "%s  " "$d"; curl -s "$B/card/LIFE?date=$d" | wc -c; done
# 2026-09-01  3650
# 2026-09-04  3735
# 2026-09-10   167
```

Tidak ada kunci di halaman yang dilayani, dan tidak ada pihak ketiga:

```bash
curl -s http://127.0.0.1:8000/ -o /tmp/served-cors.html -w 'HTTP %{http_code}  %{size_download} bytes\n'
# HTTP 200  7470 bytes

grep -nEi "SECTORS_API_KEY|api[_-]?key|authorization|bearer|secret|password|token|passwd" /tmp/served-cors.html
# (nol kecocokan)

grep -nEi "google-analytics|googletagmanager|gtag\(|plausible|posthog|segment\.|mixpanel|hotjar|sentry|_vercel/insights|clarity" /tmp/served-cors.html
# (nol kecocokan)

grep -rnoE "https?://[^\"' )]+" web/ | sort -u
# hanya https://katalis-api-ibyebnreqa-et.a.run.app (+ 127.0.0.1 di README)
```

`cd src/katalis && ./run.sh test` dijalankan, tidak ada berkas `src/katalis/` yang disentuh:
**243 assertion hijau di 40 fungsi check, exit 0**.

## Riwayat: kenapa sempat terhalang

Sampai revisi `katalis-api-00004-p7w`, Cloud Run tidak mengirim `access-control-allow-origin`,
jadi peramban menolak membaca balasan lintas asal dan `python3 -m http.server` polos tidak bisa
membuktikan apa pun. Keputusan manusia: header ditambahkan di `src/katalis/server.py` oleh sesi
Fase 4 — sesi ini dilarang menyentuh `src/katalis/`. Sebelum revisi itu melayani, jalur
render/penolakan sempat dilatih memakai tiruan sekali pakai di `/tmp` dan build sementara yang
masih menerima `?api=`; keduanya tidak dipakai lagi dan tidak menjadi bagian dari bukti di atas.

## Yang tetap hanya bisa dilakukan manusia

1. **Menyambungkan Vercel** (akun + konsol) lalu `vercel deploy`. Kesiapan yang ditinggalkan:
   `web/` siap sebagai Root Directory, Framework Preset **Other**, Build Command kosong, Output
   Directory kosong, dan **nol environment variable** — halaman tidak memegang kunci, jadi tidak
   ada yang perlu diisi di dashboard.
2. Membuka URL Vercel yang keluar dan memastikan kartu LIFE `2026-09-01` tampil serta preset
   `LIFE 2026-09-10 (ditolak)` menampilkan `tanpa_broker`.

Prasyarat CORS sudah terpenuhi oleh revisi yang melayani, jadi tidak ada langkah tersisa sebelum
`vercel deploy` selain akun dan konsol.
