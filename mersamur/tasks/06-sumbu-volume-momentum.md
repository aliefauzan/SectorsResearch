# 06 · Sumbu volume dan momentum

**Kredit: 0** · Dependensi: 02, 04

## Tujuan

Mengukur perilaku harga dan volume sebagai **residual terhadap saham itu sendiri**,
bukan sebagai level absolut.

## Prasyarat baca

- `mersamur/riset/temuan-kelayakan.md` §Q3 dan §"Empat koreksi"

## Fakta yang membentuk tugas ini

Saham di universe target **rutin bergerak 13–29% dalam lima sesi pada hari biasa.**
Ambang absolut seperti "naik 20%" tidak berarti apa-apa di sini. Semua harus relatif
terhadap distribusi saham itu sendiri.

Dan: **`/v2/daily/` mengembalikan 21 hari secara default, bukan 90.** Terbukti live
9 Sep. Jendela penuh butuh `start` dan `end` eksplisit.

## Berkas yang dibuat

```
app/axes/volume_anomaly.py
app/axes/momentum.py
```

## Langkah

1. Selalu minta `/v2/daily/` dengan `start` dan `end` eksplisit. Baseline apa pun
   yang mengasumsikan 90 hari akan diam-diam memakai 21.
2. **Volume**: rasio volume sesi terakhir terhadap median sesi sebelumnya.
   Jangan pakai rata-rata — satu hari ARA merusaknya.
3. **Momentum**: kenaikan kumulatif 5 sesi, lalu **ubah jadi persentil** terhadap
   semua jendela 5 sesi pada saham itu sendiri. Nilai persentil inilah sumbunya,
   bukan persentase mentahnya.
4. Musiman mingguan: kalau data cukup, kurangi efek hari-dalam-minggu sebelum
   menghitung residual.
5. Lewati hari libur bursa saat menghitung jendela.
6. Tandai deret yang seluruh nilainya nol sebagai `suspended`, bukan `quiet`.

## Kriteria selesai

```bash
python3 -m pytest app/tests/test_volume_momentum.py -q
python3 -c "from app.axes.volume_anomaly import score; print(score('LIFE'))"
```

`LIFE` harus memberi rasio volume ≈ 24,5x.

Tes:
- deret nol dikenali sebagai suspensi, bukan anomali
- persentil momentum konsisten: jendela tertinggi = persentil ~100
- jendela yang menyeberangi hari libur tidak menghasilkan hari kosong

## Jangan

- Jangan memakai ambang persentase absolut. Universe ini bergerak terlalu liar.
