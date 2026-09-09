# 10 · Kontrol saham kecil — satu-satunya tugas berbiaya kredit

**Kredit: 10** · Dependensi: 04

## Tujuan

Menutup lubang terakhir dari uji kelayakan. Sampai ini ada, angka 61,6% konsentrasi
**deskriptif, bukan diskriminatif**.

## Masalah yang diselesaikan

Uji kelayakan membandingkan gorengan tersuspensi vs blue chip. Itu mencampur
**ukuran** dengan **manipulasi**. Saham kecil punya broker terkonsentrasi terlepas
dari digoreng atau tidak. Dan `XL` mungkin sekadar broker ritel online terbesar yang
muncul di mana-mana.

Kontrol yang benar: **saham kecil yang tidak pernah disuspensi.**

## Prasyarat baca

- `research/plan/meridian-saham/temuan-kelayakan.md` §Q1 dan §"Uji berikutnya"
- `research/harness/plans/plan-feasibility.json` — tiru pola plannya

## Berkas yang dibuat

```
research/harness/plans/plan-control.json
```

## Langkah

1. Ambil 10 nama dari `universe.control_group()`. Kandidat yang sudah terverifikasi
   ada di screener cache: `INDX`, `BMBL`, `WIDI`, `OCAP`, `ARKA`, `HADE`, `DIGI`,
   `PCAR`, `AEGS`, `RICY`.
2. Tulis plan: `/v2/daily/{sym}/` dengan `start` dan `end` **eksplisit** (jendela
   yang sama dengan kelompok tersuspensi), 1 kredit per simbol.
3. **Rehearse ke mock lebih dulu**, lalu hapus apa pun yang mock tulis ke
   `recorded/` sebelum live:

   ```bash
   cd research/harness && python3 src/mock_server.py --port 8787 --credits 1000
   cd research/harness && SECTORS_BASE_URL=http://127.0.0.1:8787 python3 src/capture.py --plan plans/plan-control.json --budget 400
   ```

4. Baru live, dengan cap:

   ```bash
   cd research/harness && python3 src/capture.py --plan plans/plan-control.json --budget 330
   ```

5. Commit rekamannya beserta baris ledgernya. Rekaman ini dibayar kredit —
   menghilangkannya berarti membayar dua kali.

## Kriteria selesai

- 10 berkas `v2_daily_*.json` baru di `recorded/`
- Ledger bertambah 10 baris
- `git status` bersih setelah commit

## Jangan

- **Jangan** ambil broker-summary untuk kelompok kontrol dalam tugas ini (20 kredit
  lagi). Uji momentum dulu; kalau momentum saja sudah memisahkan, konsentrasi belum
  tentu perlu dibeli.
- Jangan panggil simbol yang tidak ada di screener cache. 404 menagih 1 kredit.
