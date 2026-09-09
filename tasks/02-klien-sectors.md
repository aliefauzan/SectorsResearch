# 02 · Klien Sectors — cache-first, berledger, sadar anggaran

**Kredit: 0** · Dependensi: 01

## Tujuan

Satu-satunya modul di `app/` yang boleh menyentuh jaringan. Semua modul lain menerima
data, tidak mengambilnya. Itu yang membuat seluruh sistem bisa diuji tanpa kredit.

## Prasyarat baca

- `research/docs/api/01-api-guide.md` (auth, billing, error)
- `research/docs/api/05-credit-budget.md`
- `research/harness/src/capture.py` — tiru properti keamanannya
- `research/plan/meridian-saham/temuan-kelayakan.md` §"Empat koreksi"

## Berkas yang dibuat

```
app/sectors_client.py
app/cache.py
```

## Langkah

1. **Cache lebih dulu, selalu.** Cek `research/harness/recorded/` lewat
   `_manifest.json` sebelum mempertimbangkan jaringan. Sebagian besar panggilan
   pengembangan harus selesai tanpa kredit.
2. `User-Agent` browser. Cloudflare memblokir `Python-urllib` dengan
   `403 {"error": "error code: 1010"}` yang tidak menyebut user agent sama sekali.
3. `Authorization` = nilai mentah `SECTORS_API_KEY`, **tanpa** prefiks `Bearer `.
   Baca lewat `research/harness/src/sectors_env.py`, jangan sentuh `os.environ`.
4. `RateWindow`: 25 permintaan **berbayar** per ~30 detik bergulir. Respons gratis
   (400) tidak dihitung. Tidak ada `Retry-After`; menabrak 429 memperpanjang
   penguncian — tunggu jendelanya habis.
5. Ledger append-only tiap panggilan berbayar: path, params, status, est_cost,
   billed_cost dari header, timestamp.
6. **Hard budget cap.** Lewat batas = angkat exception, bukan peringatan.
7. Larangan parameter default: `sections`, `classifications`, `periods`,
   `n_quarters` wajib eksplisit. Tolak panggilan yang membiarkannya kosong.
8. `/v2/daily/` **wajib** `start` dan `end` eksplisit — defaultnya 21 hari,
   bukan 90. Ini terbukti live 9 Sep.

## Kriteria selesai

```bash
python3 -m pytest app/tests/test_client.py -q
```

Tes yang harus ada, semuanya offline:
- panggilan yang ada di cache tidak menyentuh jaringan
- budget terlampaui mengangkat exception sebelum request dikirim
- `sections`/`n_quarters` kosong ditolak
- `/v2/daily/` tanpa `start`/`end` ditolak
- kunci API tidak pernah muncul di ledger atau log

## Jangan

- Jangan panggil live satu pun dalam tugas ini. Semua tes pakai cache dan stub.
