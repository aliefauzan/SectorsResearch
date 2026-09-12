# web/ — halaman baca-saja (D8)

Satu berkas: `index.html`. Tidak ada build, tidak ada dependensi, tidak ada kunci, tidak ada
analytics pihak ketiga. Halaman memanggil satu alamat —
`https://katalis-api-ibyebnreqa-et.a.run.app/card/{simbol}?date=YYYY-MM-DD` — dan mencetak
badan balasannya apa adanya di `<pre>` monospace. Tidak ada angka yang dihitung di peramban;
setiap angka di kartu keluar dari `card.show()` di sisi server.

CLI tetap permukaan utama. Halaman ini menambah satu jalan masuk, ia tidak menggantikan apa pun.

## Membuka lokal

```bash
python3 -m http.server 8000 --directory web
# buka http://127.0.0.1:8000/
```

Halaman lalu mengambil kartu **langsung dari Cloud Run**, lintas asal. Itu bekerja karena
layanan mengirim `Access-Control-Allow-Origin: *` — kartunya publik dan baca-saja, jadi tidak
ada yang perlu dijaga dengan daftar asal dan tidak ada kunci yang dikirim. Verifikasi headernya:

```bash
curl -s -i -H "Origin: http://127.0.0.1:8000" \
  "https://katalis-api-ibyebnreqa-et.a.run.app/card/LIFE?date=2026-09-01" | grep -i access-control
```

Selama header itu belum ada di revisi yang melayani, peramban menolak membaca balasannya dan
halaman menampilkan pesannya apa adanya, bukan halaman kosong.

## Tautan langsung

Halaman menerima `?symbol=` dan `?date=`:

```
http://127.0.0.1:8000/?symbol=LIFE&date=2026-09-04
```

## Yang dilakukan manusia di Vercel (belum dikerjakan)

1. Impor `aliefauzan/SectorsResearch` sebagai proyek Vercel. **Root Directory: `web`.**
   Framework Preset: **Other**. Build Command: kosong. Output Directory: kosong.
   Environment Variables: **tidak ada satu pun** — halaman tidak memegang kunci.
2. Deploy. Kalau CLI dipakai dari akar repo: `vercel deploy web` (atau `cd web && vercel deploy`).
3. Buka URL yang keluar dan pastikan kartu LIFE `2026-09-01` tampil, lalu tekan
   `LIFE 2026-09-10 (ditolak)` dan pastikan alasan `tanpa_broker` tampil.

Prasyarat yang harus benar lebih dulu: revisi Cloud Run yang melayani sudah mengirim
`Access-Control-Allow-Origin`, karena halaman memanggil Cloud Run langsung tanpa proxy dan
tanpa rewrite di antaranya.
