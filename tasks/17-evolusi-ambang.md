# 17 · Evolusi ambang dan lima pagarnya

**Kredit: 0** · Dependensi: 12, 16

## Tujuan

Lapisan yang mengubah parameternya sendiri — orkestrasi buatan sendiri yang disebut
bar Track 01 secara eksplisit. Dan lapisan yang paling mudah berubah jadi overfitting
yang dipamerkan sebagai wawasan.

## Prasyarat baca

- `research/plan/meridian-saham/red-team.md` §A3
- `research/plan/pump-and-dump/agen-risiko-belajar-mandiri.md`

## Aturan yang mengikat

**Ambang bergerak HANYA pada set penyetelan historis** (walk-forward, ratusan
peristiwa). Forward test dari run harian **tidak pernah** dipakai menyetel — hanya
memvalidasi. Alasannya di tugas 12: base rate 0,77% berarti 14 hari live hanya
menghasilkan 3–5 peristiwa positif.

`yunus-0x/meridian` menggeser ambang setelah 5 posisi tertutup. Lima terlalu sedikit
untuk domain ini; menyalinnya menghasilkan agen yang belajar derau.

## Berkas yang dibuat

```
app/agent/evolve.py
```

## Lima pagar — semuanya wajib, semuanya harus terlihat di video

1. **N minimum**: tidak ada ambang bergerak sebelum sumbu itu punya ≥20 peristiwa
   selesai **di set penyetelan**.
2. **Batas langkah**: satu iterasi menggeser ambang paling banyak 10% dari nilainya.
3. **Lantai dan langit-langit** yang ditetapkan manusia, di `thresholds.json`.
   Tanpa ini loop hanyut ke memperingatkan segalanya, atau tidak pernah sama sekali.
4. **Hold-out**: satu irisan waktu tidak pernah dipakai menyetel. Angka video dari sana.
5. **Tombol mati**: `--reset` mengembalikan seluruh ambang ke nilai awal.

## Langkah

1. Baca agregasi lesson dari tugas 16.
2. Usulkan pergeseran, lalu jalankan kelima pagar. Kalau salah satu gagal, **jangan
   geser** dan catat alasannya.
3. Tiap perubahan menulis entri ke `thresholds.json.history`: versi, tanggal, sumbu,
   dari, ke, alasan, N, hold-out sebelum dan sesudah.
4. Bump `version`. Peringatan yang dikeluarkan sesudahnya membawa versi itu.

## Kriteria selesai

```bash
python3 -m pytest app/tests/test_evolve.py -q
python3 app/agent/evolve.py --dry-run
python3 app/agent/evolve.py --reset
```

Tes:
- pergeseran >10% ditolak
- sumbu dengan N=3 tidak bergerak
- ambang tidak pernah keluar dari lantai/langit
- `--reset` mengembalikan persis ke versi 1
- data hold-out tidak pernah dibaca oleh jalur penyetelan

## Jangan

- Jangan sembunyikan kalau ambang yang menyetel diri kalah dari ambang tetap.
  Laporkan itu. Yang dinilai adalah loopnya ada, berjalan, dan bisa diaudit.
