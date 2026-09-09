# 09 · Profil konvergensi

**Kredit: 0** · Dependensi: 05, 06, 07, 08

## Tujuan

Menggabungkan empat sumbu menjadi **profil**, bukan skor tunggal.

## Kenapa bukan skor tunggal

Argumen produk ini adalah **konfirmasi lintas pandangan independen**. Meratakan empat
sumbu jadi satu angka membuang argumen itu, dan mengubah produk deskriptif menjadi
skor yang terbaca sebagai rekomendasi — yang dilarang code of conduct.

Yang dilaporkan: **berapa sumbu menyala, dan mana.**

## Prasyarat baca

- `research/plan/meridian-saham/spec.md` §5
- `research/plan/meridian-saham/red-team.md` §D11

## Berkas yang dibuat

```
app/profile.py
```

## Langkah

1. Panggil keempat sumbu, kumpulkan nilai + `fired` masing-masing.
2. Ambang dibaca dari `state/thresholds.json`, tidak pernah hardcoded.
3. Kembalikan objek: nilai tiap sumbu, ambang yang berlaku, `fired`, jumlah menyala,
   versi ambang, dan **daftar sitasi** — endpoint dan field asal tiap angka.
4. Sumbu yang datanya tidak ada harus jadi `unknown`, bukan `false`. Data hilang
   bukan bukti ketenangan.
5. Tangani saham tersuspensi secara khusus: profil harus menyatakannya, bukan
   melaporkan nol di semua sumbu.
6. Jangan pernah mengembalikan kata "beli", "jual", "aman", "bahaya", atau warna.

## Kriteria selesai

```bash
python3 -m pytest app/tests/test_profile.py -q
python3 -c "from app.profile import build; print(build('LIFE')['axes_fired'], build('PACK')['axes_fired'])"
```

Harus memberi peringkat yang konsisten dengan uji kelayakan: LIFE lebih tinggi
dari PACK.

Tes:
- sumbu tanpa data = `unknown`, tidak dihitung sebagai tidak menyala
- tiap angka di output punya sitasi
- tidak ada kosakata vonis di output

## Jangan

- Jangan menambahkan bobot dan menjumlahkan. Itu tugas yang berbeda dan lebih lemah.
