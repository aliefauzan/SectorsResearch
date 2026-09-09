# 03 · Set label dari riwayat suspensi

**Kredit: 0** — 585 baris sudah dibayar dan ada di disk · Dependensi: 02

## Tujuan

Mengubah `/v2/suspensions/` menjadi set peristiwa bertanggal yang bisa dipakai
backtest — dengan kelas alasan yang benar dan pemisahan yang mencegah kebocoran.

## Prasyarat baca

- `mersamur/riset/temuan-kelayakan.md` §Q4
- `mersamur/tools/feasibility.py` — klasifikator alasan sudah benar di sana

## Berkas yang dibuat

```
app/labels.py
```

## Langkah

1. Muat `research/harness/recorded/v2_suspensions__limit-30.json` (585 baris).
2. Klasifikasikan `reason` ke sembilan kelas. Salin daftar pola dari
   `feasibility.py` — regex naif kehilangan 17 peristiwa karena
   `"Dalam rangka cooling down"` muncul tanpa awalan `"peningkatan harga kumulatif"`.
3. **Hanya `cooling_down` yang jadi label positif** (452 peristiwa). Kelas lain
   disimpan tapi tidak dipakai sebagai target.
4. **Buang semua peristiwa sebelum 2025.** Nol cooling-down ada sebelum itu;
   memasukkannya berarti melatih di rezim aturan yang berbeda.
5. Fungsi `events(symbol, before=None, after=None)` yang mengembalikan peristiwa
   bertanggal, supaya pemanggil bisa memaksa batas waktu.
6. **Pemisahan fitur/label.** Suspensi hanya boleh jadi fitur kalau tanggalnya
   **lebih awal** dari awal jendela fitur peristiwa yang sedang diprediksi.
   Sediakan `history_before(symbol, cutoff_date)` dan buat itu satu-satunya jalan
   modul lain melihat riwayat.
7. Hitung dan ekspos base rate per rezim tahun.

## Kriteria selesai

```bash
python3 -m pytest app/tests/test_labels.py -q
python3 -c "from app.labels import summary; print(summary())"
```

Harus mencetak: 452 cooling-down, 236 emiten unik, base rate 2026 ≈ 0,77%
per saham per 10 hari bursa.

Tes yang harus ada:
- `history_before` tidak pernah mengembalikan peristiwa pada atau sesudah cutoff
- peristiwa pra-2025 tidak masuk set label
- kelas alasan cocok dengan hitungan di `temuan-kelayakan.md`

## Jangan

- Jangan pakai `going_concern` sebagai label positif. Itu masalah yang berbeda.
