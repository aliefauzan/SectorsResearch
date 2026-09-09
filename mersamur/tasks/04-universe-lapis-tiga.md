# 04 · Universe — siapa yang di-screen

**Kredit: 0** · Dependensi: 02, 03

## Tujuan

Membatasi produk ke lapis saham tempat masalahnya benar-benar ada. Ini keputusan
statistik, bukan kosmetik.

## Prasyarat baca

- `mersamur/riset/temuan-kelayakan.md` §"Satu temuan yang mengubah
  penentuan universe"
- `research/docs/api/03-screener-query-language.md`

## Kenapa lapis tiga

Base rate pasar 0,77% per 10 hari. Tapi di **200 saham berkapitalisasi terkecil,
98 (49%) punya riwayat suspensi.** Itu universe tempat tip grup Telegram berasal.
Membatasi ke sana mengubah masalah dari mencari jarum di jerami menjadi memilah
kelompok yang memang berisiko tinggi.

## Berkas yang dibuat

```
app/universe.py
```

## Langkah

1. Muat screener yang sudah terekam:
   `v2_companies__include_query_values-true_limit-200_order_by-market_cap_where-market_cap-1000000000000.json`
2. `watchlist()` mengembalikan universe kerja. Default: 200 saham terkecil.
3. `control_group()` mengembalikan 102 saham kecil yang **tidak pernah** disuspensi —
   dipakai tugas 10 dan 11.
4. **Resolusi simbol yang aman.** Simbol hanya sah kalau pernah muncul di respons
   sebelumnya. Identifier tebakan menagih 1 kredit untuk 404. Tolak simbol yang
   tidak ada di cache atau di screener.
5. Tangani sufiks `.JK` konsisten di satu tempat — normalkan sekali, di sini.
6. Ekspos `market_cap` dari `query_values`; screener tidak mengembalikan field lain.

## Kriteria selesai

```bash
python3 -c "from app.universe import watchlist, control_group; print(len(watchlist()), len(control_group()))"
python3 -m pytest app/tests/test_universe.py -q
```

Harus mencetak `200 102`.

Tes: simbol karangan (`ZZZZ`) ditolak, bukan diteruskan ke klien.

## Jangan

- Jangan panggil screener live. Hasilnya sudah dibayar dan ada di disk.
