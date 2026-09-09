# 07 · Sumbu kualitas katalis

**Kredit: 0** · Dependensi: 02, 04

## Tujuan

Menjawab: apakah ada alasan fundamental di balik pergerakan ini?

## Rumusan sumbu ini SUDAH DIREVISI

Rumusan awal — "tidak ada berita" — **terbukti salah** pada 9 September. Sepuluh dari
sepuluh saham tersuspensi punya berita: 112 artikel untuk 10 nama.

Rumusan yang benar:

> Berita **ada**, tetapi 21 dari 30 artikel hanya berdimensi `technical`, dan hanya
> 3 yang `financials`. Liputannya membahas pergerakan harga, bukan alasan di baliknya.

## Prasyarat baca

- `mersamur/riset/temuan-kelayakan.md` §Q2

## Berkas yang dibuat

```
app/axes/catalyst.py
```

## Langkah

1. Baca `/v2/news/?symbols=` dari cache. `symbols` menerima daftar dipisah koma dan
   satu panggilan mencakup banyak simbol — 1 kredit, bukan 1 per simbol.
2. Tiap artikel membawa `dimension`: objek berskor delapan tema
   (`future`, `dividend`, `ownership`, `technical`, `valuation`, `financials`,
   `management`, `sustainability`). Sudah dihitung Sectors; jangan bangun klasifikator.
3. Sumbunya: **rasio artikel berdimensi fundamental** =
   `(financials > 0 atau future > 0) / total artikel`. Rendah = pergerakan tanpa
   alasan yang dilaporkan.
4. Bedakan tiga keadaan dan jangan campur: tidak ada artikel · ada artikel tapi nol
   fundamental · ada artikel fundamental. Ketiganya berarti hal berbeda.
5. `body` panjangnya ~500 karakter. Perlakukan sebagai ekstrak, jangan bangun
   summarizer di atasnya.
6. Batasi jendela waktu lewat `start`/`end`, dan pastikan tidak ada artikel setelah
   tanggal peristiwa yang bocor ke fitur.

## Kriteria selesai

```bash
python3 -m pytest app/tests/test_catalyst.py -q
python3 -c "from app.axes.catalyst import score; print(score('LIFE'))"
```

`LIFE` harus menunjukkan 8 artikel, 2 berdimensi fundamental.

Tes: artikel bertanggal setelah cutoff tidak pernah masuk hitungan.

## Jangan

- Jangan scrape berita dari mana pun. `/v2/news/` sudah lengkap dan terklasifikasi,
  dan scraping merusak tes eligibility.
