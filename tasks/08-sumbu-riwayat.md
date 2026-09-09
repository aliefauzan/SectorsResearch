# 08 · Sumbu riwayat — sekaligus baseline kedua

**Kredit: 0** · Dependensi: 03

## Tujuan

Riwayat suspensi adalah fitur termurah dan mungkin terkuat yang ada. Ia juga
**lawan tanding** yang harus dikalahkan sistem Anda.

## Fakta yang membentuk tugas ini

```
452 peristiwa cooling-down / 236 emiten unik = 1,92 per emiten
353/452 (78%) berasal dari emiten yang pernah disuspensi sebelumnya
MGLV x7 · UDNG x7 · PACK x5 · MDIA x5 · LUCY x5 · MLPT x5 · INET x5 · MINA x5
```

Tujuh puluh delapan persen. Model bisa terlihat pintar hanya dengan menghafal daftar
residivis. Tugas ini harus membuat itu **mustahil terjadi diam-diam**.

## Prasyarat baca

- `research/plan/meridian-saham/temuan-kelayakan.md` §Q4 temuan 3
- `research/plan/meridian-saham/red-team.md` §A2

## Berkas yang dibuat

```
app/axes/history.py
app/baselines/previously_suspended.py
```

## Langkah

1. `history.py` hanya boleh mengakses riwayat lewat `labels.history_before(sym, cutoff)`.
   Tidak ada jalan lain. Ini satu-satunya pertahanan terhadap kebocoran.
2. Fitur: jumlah suspensi sebelum cutoff, hari sejak yang terakhir, kelas alasannya.
3. `previously_suspended.py` adalah **baseline murni**: memberi peringatan kepada
   setiap saham yang pernah disuspensi, tanpa sumbu lain. Ini yang harus dikalahkan
   di tugas 11.
4. Baseline ini wajib dievaluasi dengan pemisahan waktu yang sama persis dengan
   sistem utama — kalau tidak, perbandingannya curang ke arah yang menguntungkan Anda.

## Kriteria selesai

```bash
python3 -m pytest app/tests/test_history.py -q
```

Tes wajib:
- `history.py` tidak punya akses langsung ke berkas suspensi — hanya lewat `labels`
- fitur yang dihitung dengan cutoff T tidak berubah kalau peristiwa setelah T ditambahkan
- baseline menghasilkan prediksi untuk universe yang sama dengan sistem utama

## Jangan

- Jangan perlakukan baseline ini sebagai jerami. Ia mungkin menang. Kalau menang,
  itu temuan yang harus dilaporkan, bukan disembunyikan.
