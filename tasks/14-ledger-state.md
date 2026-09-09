# 14 · Empat berkas state

**Kredit: 0** · Dependensi: 09

## Tujuan

Ini yang akan dibuka juri. Kriteria technical depth 30% menyatakan penilaian
"diverifikasi terhadap repositori GitHub" — klaim tanpa berkas bernilai nol.

## Prasyarat baca

- `research/plan/meridian-saham/spec.md` §4

## Berkas yang dibuat

```
app/ledger.py
state/warnings.jsonl
state/outcomes.jsonl
state/lessons.jsonl
state/thresholds.json
```

## Langkah

1. Tiga yang pertama **append-only**. Jangan pernah menulis ulang baris lama.
2. `warnings.jsonl` — tiap peringatan membawa: id, simbol, tanggal, nilai tiap sumbu,
   ambang yang berlaku saat itu, versi ambang, prediksi, kredit terpakai, status.
3. `outcomes.jsonl` — resolusi: outcome (`true_positive`/`false_positive`/
   `still_open`/`expired`), hari berlalu, dan **bukti**. Bukti wajib membawa
   `pdf_url` kalau ada — itu yang bisa diklik juri.
4. `lessons.jsonl` — kondisi, harapan, kenyataan, dugaan sebab, sumbu yang terlibat,
   subsektor.
5. `thresholds.json` — nilai saat ini, batas lantai/langit, **dan riwayat tiap
   perubahan di dalam berkasnya sendiri**, lengkap dengan bukti pendukung dan angka
   hold-out sebelum/sesudah. Riwayat di dalam berkas berarti rollback selalu mungkin.
6. Skema divalidasi saat tulis. Baris rusak lebih buruk daripada tidak ada baris.

## Kriteria selesai

```bash
python3 -m pytest app/tests/test_ledger.py -q
python3 -c "import json;[json.loads(l) for l in open('state/warnings.jsonl')]"
```

Tes:
- menulis dua kali tidak pernah menimpa baris lama
- baris yang tidak sesuai skema ditolak saat tulis
- `thresholds.json` selalu bisa di-rollback ke versi mana pun dari riwayatnya

## Jangan

- Jangan taruh berkas ini di `.gitignore`. Justru berkas inilah buktinya.
