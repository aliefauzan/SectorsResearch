# 19 · Pengiriman dan riwayat run nyata

**Kredit: 0** · Dependensi: 01, 18

## Tujuan

Menyambungkan tick harian ke saluran nyata, sehingga yang tumbuh bukan hanya berkas
log tapi **riwayat yang terlihat** — beberapa hari pesan bertimestamp di kanal
sungguhan jauh lebih meyakinkan daripada satu run yang dipicu saat merekam.

## Prasyarat baca

- `research/docs/hackathon/02-tracks.md` §Track 02, syarat bukti

## Berkas yang dibuat

```
app/render/notify.py
app/cli.py
```

## Langkah

1. Bot Telegram mengirim peringatan baru dari tick harian. Token lewat `.env`,
   jangan pernah masuk repo.
2. `app/cli.py` menerima satu ticker dan mencetak paragrafnya — ini permukaan
   "pengguna menempel ticker". Cukup CLI; antarmuka web adalah hal pertama yang
   dipotong kalau waktu habis.
3. Tick harian mengirim **hanya transisi** — saham yang *memasuki* keadaan sumbu
   menyala, bukan yang sudah berada di dalamnya berhari-hari. Trigger transisi jauh
   lebih bisa dipertahankan daripada query ulang harian, dan ini yang membuat
   penempatan Track 02 sah.
4. Gagal kirim tidak boleh menggagalkan tick. Catat dan lanjut.
5. Sertakan versi ambang di tiap pesan, supaya riwayat kanal menunjukkan sistem
   yang berubah seiring waktu.

## Kriteria selesai

```bash
python3 -m app.cli LIFE
python3 app/tick.py --dry-run    # menunjukkan apa yang akan dikirim, tidak mengirim
```

- Kanal Telegram memuat pesan dari beberapa hari berbeda dengan timestamp nyata.
- `state/runs.jsonl` tumbuh satu baris per hari kerja.

## Jangan

- Jangan posting otomatis ke akun sosial publik. Itu aksi keluar; sisakan di balik
  konfirmasi eksplisit.
- Jangan kirim ulang peringatan yang sama tiap hari. Itu yang membuat orang
  mematikan notifikasi, dan membuat trigger terlihat seperti query ulang.
