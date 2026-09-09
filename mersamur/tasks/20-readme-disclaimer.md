# 20 · README, disclaimer, dan pembeda

**Kredit: 0** · Dependensi: 12, 14

## Tujuan

Repo adalah setengah dari penilaian. Kriteria technical depth 30% dinilai
"diverifikasi terhadap repositori GitHub". Juri membaca ini sebelum mereka membaca
kode.

## Prasyarat baca

- `mersamur/riset/red-team.md` §C8 dan §C9
- `research/plan/already-published.md`

## Berkas yang dibuat

```
README.md
DISCLAIMER.md
```

## Langkah

1. **Kalimat pertama menyebut orang**, bukan teknologi:
   > Investor ritel Indonesia yang menerima tip saham di grup chat dan tidak punya
   > cara membedakan pergerakan nyata dari yang direkayasa.
2. **Pembeda eksplisit dari resep Sectors sendiri.** Satu paragraf. Resep
   [GNN Anomaly Detection bagian 1–3](https://docs.sectors.app/recipes/gnn-anomaly-detection/01-gnn-part-1)
   mendeteksi anomali dikonfirmasi broker activity dan foreign flow — dan halaman
   track resmi menyebutnya sebagai kalibrasi kedalaman Track 03. Perbedaan yang sah:
   resep itu mendeteksi anomali statistik, produk ini menjawab pertanyaan pengguna
   pada momen keputusan; resep itu tidak punya label, produk ini divalidasi terhadap
   suspensi resmi IDX; resep itu berjalan sekali, produk ini mengoreksi diri dan
   menyimpan jejaknya. **Kalau Anda tidak menyatakannya, juri yang menulis resep itu
   akan menyatakannya sendiri, di kepalanya.**
3. **Peta bukti** — tautan langsung ke berkas yang menjawab tiap pertanyaan juri:
   `state/warnings.jsonl`, `outcomes.jsonl`, `lessons.jsonl`, `thresholds.json`,
   `runs.jsonl`, `backtest_report.json`, ledger kredit.
4. **Batasan dinyatakan sendiri sebelum juri menemukannya**: label hanya ada sejak
   2025; backtest terbatas anggaran kredit; hold-out kecil; kelompok kontrol 10 nama.
5. **Ketergantungan Sectors dinyatakan**: cabut Sectors dan produk berhenti bekerja.
   Sebutkan endpoint yang dipakai dan untuk apa.
6. `DISCLAIMER.md`: deskriptif, bukan saran investasi, bukan ajakan bertransaksi.
   Tautkan dari README, dari CLI, dan dari tiap output.

## Kriteria selesai

- README bisa dibaca orang yang belum pernah dengar produk ini, dalam dua menit,
  dan mereka tahu masalah siapa yang diselesaikan.
- Tiap klaim di README punya tautan ke berkas yang membuktikannya.
- Tidak ada klaim yang tidak bisa diverifikasi dari repo.

## Jangan

- Jangan tulis "menggunakan AI canggih". Tulis apa yang dilakukan sistem dan di
  berkas mana buktinya.
