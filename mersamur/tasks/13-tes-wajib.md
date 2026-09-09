# 13 · Tiga tes yang dicari juri

**Kredit: 0** · Dependensi: 12

## Tujuan

Ini bukan tes untuk kualitas kode. Ini tes yang menjawab tiga pertanyaan yang akan
diajukan juri ke repo — dan yang membuktikan jawabannya tanpa Anda hadir.

## Prasyarat baca

- `mersamur/riset/spec.md` §7
- `research/docs/api/10-domain-pitfalls.md`

## Berkas yang dibuat

```
app/tests/test_no_leakage.py
app/tests/test_broker_sign.py
app/tests/test_suspended.py
.github/workflows/tests.yml
```

## Langkah

### `test_no_leakage.py`

Setiap fitur wajib membawa tanggal, dan tanggal itu wajib lebih awal dari tanggal
peristiwa. **Fitur tanpa tanggal dilarang masuk backtest.**

`/v2/free-float/` tidak punya field tanggal — ia snapshot hari ini. Memakainya
memprediksi suspensi masa lalu adalah kebocoran murni. Tes harus menolaknya.
Penggantinya: float direkonstruksi dari `shareholders-composition` bulanan.

### `test_broker_sign.py`

Memastikan dominansi **menjumlahkan** `top_buyers[0].net_idr` dan
`top_sellers[0].net_idr`. Tulis tes yang GAGAL kalau seseorang menjumlahkan seluruh
kedua sisi — hasilnya selalu mendekati nol karena pasar zero-sum, dan tanda yang
terbalik membalik seluruh produk.

### `test_suspended.py`

Saham dengan seluruh fitur hitung persis nol adalah saham **tersuspensi**, bukan sepi.
Tes memastikan pipeline mengeceknya sebelum menyimpulkan apa pun tentang deret datar.

## Kriteria selesai

```bash
python3 -m pytest app/tests/ -q
```

Semua lulus, dan CI hijau di GitHub Actions. CI yang merah pada hari penjurian lebih
buruk daripada tidak ada CI sama sekali.

## Jangan

- Jangan tulis tes yang lulus dengan sendirinya. Tiap tes harus Anda buktikan gagal
  pada implementasi yang salah — lakukan sekali, secara sengaja, lalu perbaiki.
