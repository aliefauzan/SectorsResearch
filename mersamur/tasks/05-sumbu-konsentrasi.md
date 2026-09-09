# 05 · Sumbu konsentrasi broker

**Kredit: 0** · Dependensi: 02, 04

## Tujuan

Sumbu terkuat dari uji kelayakan. Median broker teratas menguasai **61,6%** sisi beli
di saham tersuspensi, vs 11–34% di blue chip.

## Prasyarat baca

- `mersamur/riset/temuan-kelayakan.md` §Q1
- `research/docs/api/10-domain-pitfalls.md` — jebakan zero-sum

## Berkas yang dibuat

```
app/axes/__init__.py
app/axes/concentration.py
```

## Langkah

1. Baca `/v2/broker-summary/{symbol}/top/` dari cache. Bentuknya:
   `{symbol, start, end, origin, cohort, top_buyers[], top_sellers[]}`,
   tiap baris `{rank, broker_code, net_idr, buy_idr, sell_idr}`.
2. **Rasio konsentrasi**: `top_buyers[0].buy_idr / sum(buy_idr)`. Sediakan juga top-3.
3. **Dominansi neto** — jebakan yang mematahkan setiap proyek bandarmology:

   ```python
   # SALAH: selalu mendekati nol, pasar itu zero-sum
   total = sum(b["net_idr"] for b in buyers) + sum(s["net_idr"] for s in sellers)

   # BENAR: net_idr SUDAH negatif untuk penjual, jadi ini MENJUMLAHKAN
   dominance = buyers[0]["net_idr"] + sellers[0]["net_idr"]
   ```

4. **Bobot kohort.** Muat `/v2/brokers/` dari cache — fieldnya `code`, `name`,
   `is_foreign` (boolean), `cohort`, `license_type`. Perhatikan: **`is_foreign`,
   bukan `origin`** — spec menyesatkan di sini. Konsentrasi berat di sisi ritel
   pada saham tipis adalah pola yang dicari.
5. Tangani `top_buyers` pendek: NICK hanya punya 5 pembeli. Kelangkaan itu sendiri
   informasi, bukan error.
6. Kembalikan objek bernilai + `fired` boolean terhadap ambang dari `thresholds.json`,
   bukan konstanta hardcoded.

## Kriteria selesai

```bash
python3 -m pytest app/tests/test_concentration.py -q
python3 -c "from app.axes.concentration import score; print(score('LIFE'))"
```

`LIFE` harus memberi rasio ≈ 0,84 dengan broker teratas `XL`, kohort `retail`.

Tes wajib: implementasi yang menjumlahkan **seluruh** kedua sisi harus GAGAL tes.
Tulis tesnya supaya menangkap tanda yang terbalik.

## Jangan

- Jangan simpulkan apa pun dari deret yang seluruhnya nol tanpa cek suspensi —
  saham yang semua fiturnya nol itu **disuspensi**, bukan sepi.
