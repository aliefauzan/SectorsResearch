# 21 · Naskah dan rekaman video

**Kredit: 0** · Dependensi: semua · **30% dari nilai akhir**

## Tujuan

Penjurian asinkron, tanpa sesi langsung. Video dan repo memikul seluruh argumen
sendirian.

## Prasyarat baca

- `research/docs/hackathon/03-submission-checklist.md`
- `mersamur/riset/spec.md` §10

## Berkas yang dibuat

```
video/naskah.md
video/shot-list.md
```

## Struktur tiga menit

| Detik | Isi | Kenapa |
| --- | --- | --- |
| 0–25 | Screenshot grup Telegram berisi tip saham. Lalu: MSCI membekukan rebalancing Indonesia atas kualitas free float; IHSG ditutup −7,35% pada hari pengumuman | Masalahnya nyata, baru, terverifikasi di luar |
| 25–75 | Tempel satu ticker. Paragraf keluar. Sekali saja | Ini produknya. Jangan jelaskan arsitektur di sini |
| 75–140 | **Adegan pemenang:** buka `lessons.jsonl`. "Agen ini salah tanggal X. Ini catatan yang dia tulis. Ini ambang yang dia geser di `thresholds.json` versi 5→6. Ini hasil hold-out sesudahnya." | Tidak ada tim lain punya adegan ini |
| 140–165 | Buka `warnings.jsonl` dan PDF suspensi IDX bersebelahan — peringatan H−5, pengumuman resmi H | Bukti yang bisa diverifikasi juri sendiri |
| 165–180 | Konfigurasi cron + `runs.jsonl` beberapa minggu. Disclaimer | Syarat bukti Track 02 |

## Aturan

1. **Jangan habiskan 90 detik pertama menjelaskan arsitektur.** Juri perlu tahu
   masalah siapa yang diselesaikan sebelum mereka peduli bagaimana.
2. **Pakai peristiwa historis yang sudah selesai** untuk demo — saham yang sudah
   disuspensi dan pengumumannya sudah terbit. Menyebut saham yang masih hidup
   sebagai "direkayasa" adalah risiko hukum bagi Anda dan bagi penyelenggara.
3. **Kalau hold-out tidak membaik, katakan di video.** Temuan negatif yang jujur
   dinilai lebih tinggi daripada kurva yang mencurigakan.
4. Angka `thumbnail` dari `/v2/news/` adalah URL gambar CDN — poles visual gratis.
5. Disclaimer di layar, bukan hanya diucapkan.

## Kriteria selesai

- Durasi ≤ 3 menit.
- Adegan `lessons.jsonl` benar-benar ada dan menampilkan kesalahan nyata.
- Seseorang yang tidak tahu apa-apa tentang proyek ini bisa menyebut penggunanya
  setelah menonton.
- Direkam **sebelum 27 September**, bukan malam terakhir.

## Jangan

- Jangan rekam sebelum `runs.jsonl` punya riwayat beberapa minggu. Adegan itu
  yang tidak bisa dikarang, dan ia butuh waktu berjalan.
