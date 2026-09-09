# 18 · Permukaan output — paragraf, bukan dashboard

**Kredit: 0** · Dependensi: 09

## Tujuan

Bentuk final produk. Prototipe yang sudah jalan ada di
`mersamur/tools/profile_demo.py` — tugas ini memindahkannya ke `app/` dan
memperbaikinya.

## Aturan yang menentukan bentuk

Track 03 menyatakan langsung: *"A product that only displays raw Sectors data in a
different visual form, however well presented, does not qualify."* **Dashboard adalah
jebakan.** Outputnya kalimat.

## Prasyarat baca

- `mersamur/tools/profile_demo.py` — prototipe yang bekerja
- `mersamur/riset/red-team.md` §D11

## Berkas yang dibuat

```
app/render/__init__.py
app/render/paragraph.py
```

## Langkah

1. Ubah profil dari tugas 09 menjadi paragraf bahasa Indonesia yang terbaca manusia.
2. **Tiap angka membawa sitasi** endpoint dan field. Verifikator fail-closed: kalau
   ada angka tanpa sumber, tolak menghasilkan output — jangan tebak.
3. Angka diucapkan dengan berguna: "Rp1,2 triliun", bukan "1200000000000".
4. Perbaiki dari prototipe: paragrafnya masih terlalu panjang dan bertele. Pecah
   jadi dua sampai tiga kalimat. Kalimat pertama menyebut yang paling menonjol.
5. Riwayat suspensi disebut sebagai fakta bertanggal dengan sumbernya, bukan sebagai
   tuduhan.
6. **Kosakata terlarang**: beli, jual, aman, bahaya, rekomendasi, target harga,
   dan warna merah/hijau sebagai vonis. Tulis daftar ini sebagai tes.
7. Disclaimer melekat di tiap output, bukan hanya di README.

## Kriteria selesai

```bash
python3 -m pytest app/tests/test_paragraph.py -q
python3 -m app.render.paragraph LIFE ASLI PACK
```

Tes:
- angka tanpa sitasi memicu penolakan, bukan output yang dikarang
- tidak ada kosakata terlarang di output mana pun
- output untuk saham tanpa data mengatakan "data tidak tersedia", bukan nol

## Jangan

- Jangan bangun dashboard. Kalau butuh permukaan visual, itu daftar paragraf.
