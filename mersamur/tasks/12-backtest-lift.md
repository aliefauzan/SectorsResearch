# 12 · Backtest walk-forward — GERBANG GO/NO-GO

**Kredit: 0** · Dependensi: 11

## Tujuan

Menjalankan sistem terhadap 20 bulan riwayat berlabel, dengan pemisahan waktu yang
jujur, dan menghasilkan angka yang akan muncul di video.

## Prasyarat baca

- `mersamur/riset/red-team.md` §A3 — pemisahan dua rezim
- `mersamur/riset/temuan-kelayakan.md` §Q4

## Kontradiksi yang tugas ini selesaikan

Spec awal mensyaratkan N≥20 peringatan selesai per sumbu sebelum ambang bergerak.
Dengan base rate 0,77%, forward test 14 hari hanya menghasilkan 3–5 true positive.
**Ambang tidak akan pernah menyala pada data live.**

Pemisahannya:

| Rezim | Data | Fungsi | N |
| --- | --- | --- | --- |
| **Penyetelan** | replay historis 2025–2026, walk-forward | di sini ambang bergerak | ratusan |
| **Forward test** | run harian sejak sekarang | **validasi saja, tidak pernah menyetel** | 3–5 |

## Berkas yang dibuat

```
app/backtest.py
state/backtest_report.json
```

## Langkah

1. Walk-forward: untuk tiap tanggal T, hitung fitur **hanya dari data sebelum T**,
   lalu cek peristiwa dalam 10 hari bursa sesudahnya.
2. Data label hanya 2025-01 sampai 2026-09. Jangan sentuh yang lebih tua.
3. **Sisihkan periode hold-out** yang tidak pernah dipakai menyetel apa pun.
   Angka di video berasal dari sana.
4. Laporkan per rezim tahun — base rate 2025 dan 2026 berbeda.
5. Simpan laporan lengkap ke `state/backtest_report.json`: parameter, jendela,
   confusion matrix, lift, jumlah peristiwa, dan angka hold-out terpisah.
6. **Kalau hold-out tidak lebih baik dari baseline, tulis itu di laporan.** Temuan
   negatif yang jujur dinilai lebih tinggi daripada kurva yang mencurigakan.

## Kriteria selesai

```bash
python3 app/backtest.py --walk-forward --holdout 2026-07-01
python3 -m pytest app/tests/test_backtest.py -q
```

Laporan harus memuat: lift pada set penyetelan, lift pada hold-out, dan keduanya
berdampingan dengan kedua baseline dari tugas 11.

Tes: fitur pada tanggal T tidak berubah kalau data setelah T dihapus.

## Jangan

- Jangan pakai hold-out untuk memilih apa pun. Sekali dilihat untuk menyetel,
  ia bukan hold-out lagi.
