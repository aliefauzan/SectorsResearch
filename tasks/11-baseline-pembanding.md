# 11 · Baseline pembanding — GERBANG GO/NO-GO

**Kredit: 0** · Dependensi: 09, 10

## Tujuan

Membuktikan empat sumbu punya alasan untuk ada. Ini pertanyaan yang menghancurkan
kalau tidak terjawab:

> *"Apa bedanya model empat sumbu kalian dengan mengurutkan saham berdasarkan
> kenaikan lima hari?"*

## Prasyarat baca

- `research/plan/meridian-saham/red-team.md` §A1 dan §A2

## Dua lawan tanding

| Baseline | Aturannya | Kenapa berbahaya |
| --- | --- | --- |
| **Momentum** | urutkan kenaikan kumulatif 5 sesi, ambil N teratas | Suspensi cooling-down dipicu aturan mekanis atas kenaikan harga. Memprediksinya bisa tereduksi jadi memprediksi harga dari harga |
| **Pernah disuspensi** | peringatkan tiap saham dengan riwayat suspensi | 78% peristiwa berasal dari residivis |

## Berkas yang dibuat

```
app/baselines/momentum.py
app/baselines/__init__.py
app/evaluate.py
```

## Langkah

1. Ketiganya — sistem 4 sumbu, momentum, pernah-disuspensi — dievaluasi lewat
   **jalur kode yang sama**, universe yang sama, jendela waktu yang sama. Perbedaan
   apa pun di jalur evaluasi membuat perbandingannya tidak sah.
2. Metrik utamanya **lift**, bukan akurasi, bukan presisi telanjang:

   ```
   lift = P(suspensi | sumbu menyala) / P(suspensi)
   ```

   Base rate 0,77% per 10 hari. Akurasi 97% dicapai dengan tidak pernah
   memperingatkan apa pun — angka itu tidak berarti.
3. Laporkan confusion matrix penuh untuk ketiganya, plus jumlah peringatan yang
   dikeluarkan masing-masing. Sistem yang memperingatkan 3x lebih banyak untuk lift
   yang sama bukan sistem yang lebih baik.
4. Ukur juga **kombinasi**: apakah 4 sumbu menambah sesuatu **di atas** momentum,
   bukan hanya mengalahkannya sendirian.

## Kriteria selesai

```bash
python3 app/evaluate.py --compare-baselines
```

Harus mencetak tabel: sistem, peringatan dikeluarkan, true positive, base rate, lift.

**Gerbangnya:** kalau sistem 4 sumbu tidak mengalahkan **kedua** baseline, berhenti.
Jangan lanjut ke tugas 12. Laporkan hasilnya dan pikirkan ulang bentuk produknya.

## Jangan

- Jangan menyetel ambang untuk memenangkan perbandingan ini. Itu overfitting yang
  akan terlihat di hold-out tugas 12.
