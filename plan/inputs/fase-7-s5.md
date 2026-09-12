# Fase 7 · tugas 1 — halaman baca-saja (S5, D8)

Catatan sesi, bukan pembaruan rencana. `plan/PROGRESS.md` dan `plan/phases/*` tidak disentuh
oleh sesi ini; berkas ini hanya merekam apa yang dikerjakan, apa yang terbukti, dan apa yang
masih menunggu.

Sesi: cabang `vercel-page`, worktree `sectors-8`, 2026-09-12. Nol kredit Sectors. Tidak ada
deploy, tidak ada `gcloud builds submit`, tidak ada penyambungan Vercel.

## Keadaan kriteria keluar

| Kriteria keluar 1 | Keadaan |
| --- | --- |
| Halaman dapat dibuka dari peramban dan menampilkan kartu | **ya**, lewat halaman yang memanggil Cloud Run langsung — tapi hanya setelah Cloud Run mengirim `Access-Control-Allow-Origin` |
| `python3 -m http.server` polos menampilkan kartu untuk LIFE 2026-09-01 dan 2026-09-04 | **belum**, dan **tidak** boleh ditandai terpenuhi sebelum revisi Cloud Run yang melayani membawa header itu |
| `curl -s <halaman>` tidak memuat nilai kunci | **ya**, hari ini, tanpa syarat |

## Apa yang dibuat

`web/index.html` — satu berkas, nol build, nol dependensi, nol kunci, nol analytics pihak
ketiga. Halaman memanggil satu alamat, langsung:

```
https://katalis-api-ibyebnreqa-et.a.run.app/card/{simbol}?date=YYYY-MM-DD
```

Balasannya dicetak apa adanya di `<pre>` monospace. Tidak ada angka yang dihitung di peramban;
setiap angka di kartu keluar dari `card.show()` di sisi server. CLI tetap permukaan utama.

`web/README.md` — cara membuka lokal, prasyarat CORS, dan langkah Vercel yang dilakukan manusia.

Tidak ada `web/vercel.json` dan tidak ada proxy dev. Halaman berbicara ke Cloud Run langsung,
tanpa rewrite dan tanpa perantara, supaya tidak ada yang menyembunyikan ke mana permintaan pergi.

## Mengapa `python3 -m http.server` polos belum bisa

Cloud Run tidak mengirim `access-control-allow-origin`. Halaman statis di asal lain karena itu
tidak boleh membaca balasannya — batasan peramban, bukan batasan server. Bukti:

```bash
curl -s -i -H "Origin: http://localhost:8000" \
  "https://katalis-api-ibyebnreqa-et.a.run.app/card/LIFE?date=2026-09-01" | grep -i access-control
# (nol baris)

grep -rn "Access-Control" src/ plan/ infra/     # (nol kecocokan)
```

Di Chromium, halaman yang sama gagal dengan `Failed to fetch` ketika `?api=` tidak diberikan,
dan halaman menampilkan pesan itu apa adanya — bukan halaman kosong.

Keputusan manusia: **opsi 1** — sesi Fase 4 menambahkan `Access-Control-Allow-Origin: *` di
`src/katalis/server.py`, dan header itu ikut di revisi Cloud Run berikutnya. Sesi ini dilarang
menyentuh `src/katalis/`, jadi perubahan itu bukan miliknya.

## Apa yang sudah terbukti hari ini, dan dengan apa

Semua bukti di bawah memakai `python3 -m http.server` polos untuk menyajikan `web/`, ditambah
satu **test double sekali pakai** di `/tmp/corsh/cors_proxy.py` yang menambahkan header CORS dan
memeruskan ke Cloud Run. Test double itu **bukan bagian repo** dan **bukan bukti kriteria
keluar 1**; ia hanya melatih jalur fetch/render/penolakan halaman sebelum revisi CORS mendarat.
Kalau nanti dianggap mengaburkan, hapus saja — ia tidak dirujuk kode mana pun.

```bash
python3 -m http.server 8000 --directory web       # halaman
python3 /tmp/corsh/cors_proxy.py 8899             # tiruan header CORS, sekali pakai
```

Yang terbukti, lewat Chromium:

| Yang diperiksa | Hasil |
| --- | --- |
| `?api=http://127.0.0.1:8899&symbol=LIFE&date=2026-09-01` | `HTTP 200 · LIFE 2026-09-01`, kartu 2.687 karakter, `font-family` monospace, byte badan sama dengan `curl` (3.199 byte) |
| `…&date=2026-09-04` | `HTTP 200 · LIFE 2026-09-04`, 2.794 karakter, byte sama dengan `curl` (3.308 byte) |
| preset `LIFE 2026-09-10 (ditolak)` | badan ditampilkan apa adanya: `LIFE 2026-09-10: TIDAK DINILAI — tanpa_broker: no broker summary on this source for this symbol` — alasan bernama dari API, bukan halaman kosong |
| `http://127.0.0.1:8000/` tanpa `?api=` (lintas asal langsung ke Cloud Run) | `tidak dapat menjangkau katalis-api` + `Failed to fetch` + alamat yang dipanggil — jalur gagal yang jujur, dan bukti kenapa CORS dibutuhkan |

```bash
curl -s http://127.0.0.1:8000/ -o /tmp/served.html -w 'HTTP %{http_code}  %{size_download} bytes\n'
# HTTP 200  7429 bytes

grep -nEi "SECTORS_API_KEY|api[_-]?key|authorization|bearer|secret|password|token|passwd" /tmp/served.html
# (nol kecocokan)

grep -nEi "google-analytics|googletagmanager|gtag\(|plausible|posthog|segment\.|mixpanel|hotjar|sentry|_vercel/insights|clarity" /tmp/served.html
# (nol kecocokan)

grep -rnoE "https?://[^\"' )]+" web/ | sort -u
# hanya https://katalis-api-ibyebnreqa-et.a.run.app (+ 127.0.0.1 di README)
```

`cd src/katalis && ./run.sh test` dijalankan, tidak ada berkas `src/katalis/` yang disentuh:
**243 assertion hijau di 40 fungsi check, exit 0**.

## Yang tetap hanya bisa dilakukan manusia

1. **Menyambungkan Vercel** (akun + konsol) dan menekan `vercel deploy`. Kesiapan yang
   ditinggalkan: `web/` sudah siap sebagai Root Directory, Framework Preset **Other**, Build
   Command kosong, Output Directory kosong, dan **nol environment variable** — halaman tidak
   memegang kunci, jadi tidak ada yang perlu diisi di dashboard.
2. **Revisi Cloud Run yang membawa `Access-Control-Allow-Origin`** — dikerjakan sesi Fase 4,
   di-deploy oleh manusia. Setelah itu bukti kriteria keluar 1 diulang tanpa `?api=` dan tanpa
   test double, lalu tabel ini diperbarui.

Urutannya mengikat: menyambungkan Vercel sebelum revisi CORS melayani hanya menghasilkan halaman
yang menjawab dengan pesan gagal yang jujur, bukan kartu.
