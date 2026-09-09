# mersamur

Pemeriksa kerapuhan saham IDX — dan agen yang mengoreksi dirinya sendiri tiap hari.

> **Untuk siapa.** Investor ritel Indonesia yang menerima tip saham di grup Telegram
> dan tidak punya cara membedakan pergerakan nyata dari yang direkayasa.

Tempel satu ticker, dapat satu paragraf. Tiap angka membawa endpoint dan field asalnya.

```
LIFE   —   3 dari 4 sumbu menyala

LIFE diperdagangkan dengan satu broker berkohort ritel (XL) mengambil 84% dari
nilai beli sepuluh broker teratas, volume sesi terakhir 24,5x median 15 sesi
sebelumnya, dan IDX sudah menghentikan perdagangannya 4 kali untuk cooling down,
terakhir 2026-09-04.
```

Bukan vonis. Bukan rekomendasi. Deskripsi.

---

## Semua dijalankan dari folder ini

```bash
cd mersamur
```

Setiap perintah di seluruh dokumen ini dan di `tasks/` mengasumsikan itu.

```bash
python3 tools/feasibility.py          # empat uji kelayakan, nol kredit
python3 tools/profile_demo.py LIFE    # prototipe output produk
```

## Isi

```
mersamur/
  README.md          berkas ini
  tasks/             21 tugas + PROMPT.md — satu berkas satu tugas
  riset/             kenapa produk ini berbentuk begini
  tools/             skrip analisis, nol kredit
  plans/             rencana capture khusus produk ini
  app/               kode produk        (dibangun tugas 01-19)
  state/             empat berkas bukti (dibangun tugas 14)
```

### `tasks/` — cara membangun

Buka sesi Claude Code baru, tempel isi [`tasks/PROMPT.md`](tasks/PROMPT.md).
**Ganti satu baris untuk pindah tugas:**

```
TUGAS: tasks/01-scheduler-kerangka.md
```

Urutannya dependensi, bukan kosmetik. Tugas **01 dikerjakan hari ini** — tiga minggu
riwayat run tanpa ditunggui tidak bisa dikarang tanggal 29 September. Tugas **11 dan
12 adalah gerbang go/no-go**: empat sumbu harus mengalahkan dua baseline, atau
produknya perlu dipikir ulang.

### `riset/` — kenapa begini

| Berkas | Isi |
| --- | --- |
| [`ringkas.md`](riset/ringkas.md) | Lima menit. Mulai dari sini |
| [`deep-research.md`](riset/deep-research.md) | Apa yang menggerakkan saham vs kripto; bagian mana dari Meridian yang bisa diport |
| [`spec.md`](riset/spec.md) | Arsitektur, skema empat berkas state, anggaran kredit |
| [`red-team.md`](riset/red-team.md) | Dua belas cara ide ini kalah |
| [`temuan-kelayakan.md`](riset/temuan-kelayakan.md) | **Data live.** Empat gerbang kelayakan, 52 kredit |

## Yang dipakai dari luar folder ini

Dosir riset dan harness offline berlaku untuk seluruh repo, jadi tetap di tempatnya:

| Path | Isi |
| --- | --- |
| `../research/harness/recorded/` | 23 rekaman live, **sudah dibayar 52 kredit** — pakai ini, jangan beli ulang |
| `../research/harness/src/mock_server.py` | Rehearse rencana capture gratis |
| `../research/harness/src/capture.py` | Satu-satunya yang boleh memanggil API live |
| `../research/docs/api/` | 16 dokumen referensi Sectors API |
| `../research/docs/hackathon/` | Aturan, track, checklist |
| `../.env` | `SECTORS_API_KEY` — git-ignored sejak commit pertama |

## Angka yang membentuk produk ini

Semuanya dari data live 9 September 2026, bisa dijalankan ulang gratis dengan
`python3 tools/feasibility.py`.

- **452** suspensi cooling-down IDX, **tidak satu pun sebelum 2025** — riwayat label
  20 bulan, bukan 7,7 tahun
- **0,77%** base rate per saham per 10 hari bursa → laporkan lift, jangan akurasi
- **78%** peristiwa berasal dari emiten yang pernah disuspensi → baseline kedua,
  dan risiko kebocoran
- **61,6%** median konsentrasi broker teratas di saham tersuspensi, vs 11–34% blue chip
- **49%** dari 200 saham terkecil punya riwayat suspensi → universe inilah yang
  membuat statistiknya bisa bekerja

## Batasan

Deskriptif, bukan saran investasi. Tidak ada eksekusi trade — dilarang di semua track
hackathon ini. Sectors API adalah satu-satunya sumber data; cabut, dan produk berhenti
bekerja.
