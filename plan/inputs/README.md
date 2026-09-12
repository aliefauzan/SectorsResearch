# inputs · Dari mana payload berasal

Produk ini tidak pernah memanggil API live. Ia membaca berkas. Direktori ini menjelaskan
berkas mana, dari mana, dan apa yang tidak boleh diasumsikan tentangnya.

## Tiga lapisan, menurun menurut kesetiaan

Bangun terhadap lapisan tertinggi yang punya apa yang Anda butuhkan; turun hanya untuk volume.

| Lapisan | Lokasi | Isi | Nyata? |
| --- | --- | --- | --- |
| 1 | `research/harness/recorded/` | Payload asli yang ditangkap dari API live pada 6 September 2026. 136 berkas JSON, plus `_ledger.jsonl` dan `_manifest.json` | **Ya** |
| 2 | `research/harness/fixtures/` | Contoh respons milik spec OpenAPI sendiri, satu per operasi terdokumentasi | Bentuknya nyata, angkanya contoh |
| 3 | `research/harness/synth/` | Semesta yang dibangkitkan, deterministik per `--seed` | **Tidak** |

```bash
ls research/harness/recorded/*.json | wc -l     # 136
```

## Live versus replay

**Semua yang ada di `recorded/` adalah replay dari panggilan live yang benar-benar terjadi.**
Ia bukan mock dan bukan fixture. Kesetiaannya diperiksa, bukan diasumsikan:

```bash
cd research/harness && python3 src/verify_mock.py
```

```
PASS replay parity 134 checked, 0 failed
PASS error parity 19 · PASS method parity 3 · PASS rate-limit parity 2 · PASS header parity 1
mock matches the captured API
```

**Tidak ada satu pun jalur di `src/katalis/` yang membuka soket.** Satu-satunya berkas yang
pernah memanggil API live adalah `research/harness/src/capture.py`, dan ia menulis ke
`recorded/` beserta baris ledgernya.

`recorded/` dilacak git **dengan sengaja**. Payload itu dibayar dengan kredit dan tidak memuat
kunci, jadi mengomitnya adalah yang menghentikan orang kedua membayar panggilan yang sama.

## Apa yang tidak boleh diasumsikan pembaca

1. **`recorded/` bukan pohon yang bisa dijelajahi; ia cache datar.** Nama berkas adalah slug
   panggilan. Jangan menebak nama; baca `_manifest.json` (167 entri), yang memetakan slug ke
   path, parameter, status, dan waktu tangkap.

2. **Satu simbol bisa punya beberapa tangkapan dengan jendela tanggal berbeda.** LIFE punya
   deret harian `2026-05-01..2026-09-10` dan ringkasan broker `2026-08-22..2026-09-04`. Kartu
   yang meminta tanggal di luar irisan keduanya ditolak dengan nama, bukan diisi nol.

3. **Panjang deret tidak seragam, dan itu bukan bug.** `/v2/daily/` memotong ke **90 hari
   kalender**, bukan 90 hari bursa — untuk LIFE itu 62 baris. Delapan simbol lain hanya
   memiliki 20 hari karena hanya itu yang dibeli. `./run.sh symbols` menyebutkan keduanya.

4. **Tujuh dari sembilan simbol tidak punya ringkasan broker.** Itu keputusan belanja, bukan
   keterbatasan API. Mereka muncul sebagai `tanpa_broker`, dan itu penolakan bernama, bukan
   kegagalan.

5. **Komparator tahun-ke-tahun tidak ada di `recorded/`.** Tiap payload kuartalan hanya memuat
   empat kuartal terakhir. Ini tidak menyentuh KATALIS — pilar-pilarnya harian — tetapi ia
   penting bagi siapa pun yang meminjam lapisan data ini.

6. **`cost_headers` selalu kosong.** API tidak mengirim header biaya sama sekali. Angka kredit
   di `_ledger.jsonl` adalah model harness, dan satu-satunya catatan independen adalah ekspor
   CSV portal di `research/evidence/usage-log/` — yang bertanggal `2026-09-05` dan karena itu
   tidak memuat pembelian setelahnya.

7. **`synth/` tidak boleh dikirim sebagai sumber data produk.** Aturan hackathon melarang
   data sintetis sebagai sumber produk dan menuntut labelnya di layar bila ia muncul di video.
   `synth/` hidup di sini untuk satu alasan sempit: `check_as_of_does_not_leak` butuh deret 90
   hari yang `recorded/` tidak punya untuk kebanyakan simbol.

## Sebelum menambah payload baru

Baca `plan/phases/phase-5-labeled-corpus.md`. Ringkasnya: rekonsiliasi ledger terhadap portal
lebih dulu, rehearse rencana terhadap mock, hapus apa pun yang rehearsal tulis ke `recorded/`,
lalu jalankan live sekali dengan `--budget` di bawah sisa nyata.
