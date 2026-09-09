# Prompt Eksekusi — ganti satu baris saja

Salin seluruh blok di bawah ke sesi Claude Code baru. **Yang perlu diubah hanya baris `TUGAS:`.**

---

```
TUGAS: tasks/01-scheduler-kerangka.md

Kerjakan HANYA berkas tugas di atas. Jangan mengerjakan tugas lain, jangan
mendahului tugas berikutnya, jangan memperluas cakupan.

Langkah:
1. Baca berkas tugas itu sampai habis.
2. Baca konteks yang disebut di bagian "Prasyarat baca" di dalamnya. Jangan baca
   dokumen lain kecuali tugas itu menyebutnya.
3. Kerjakan hanya yang ada di bagian "Langkah".
4. Jalankan semua perintah di "Kriteria selesai". Semuanya harus lulus.
5. Laporkan: berkas apa yang dibuat/diubah, hasil tiap kriteria, dan apa yang
   TIDAK dikerjakan karena di luar cakupan.

Aturan yang mengikat setiap tugas:
- NOL panggilan API live kecuali berkas tugas menyebut biaya kreditnya secara
  eksplisit. Kalau butuh data, pakai research/harness/recorded/ yang sudah dibayar.
- Kalau tugas memang butuh kredit: rehearse ke mock dulu
  (research/harness/src/mock_server.py), baru live lewat capture.py dengan --budget.
  Jangan pernah curl atau skrip sekali pakai.
- Kode produk masuk ke app/. Jangan sentuh research/harness/src/ kecuali diminta.
  Harness itu standard-library-only dan sengaja bersih.
- Jangan pernah menulis kunci API ke berkas mana pun. .env sudah di-gitignore.
- Bahasa output produk: Indonesia. Komentar kode dan commit: Inggris.
- Output produk selalu DESKRIPTIF. Tidak pernah ada vonis beli/jual, skor sebagai
  rekomendasi, atau sinyal merah/hijau.
- Selesai satu tugas: commit dengan pesan yang menyebut nomor tugasnya. Jangan push.

Kalau menemukan sesuatu yang membuat tugas ini tidak bisa dikerjakan seperti
tertulis, berhenti dan katakan — jangan diam-diam mengganti pendekatan.
```

---

## Urutan

Jalankan berurutan. Nomor kecil dulu — dependensinya nyata, bukan kosmetik.

| # | Tugas | Kredit | Kenapa di posisi ini |
| --- | --- | --- | --- |
| 01 | `01-scheduler-kerangka.md` | 0 | **Paling tidak bisa dikejar.** Log 3 minggu harus mulai hari ini |
| 02 | `02-klien-sectors.md` | 0 | Semua tugas lain lewat sini |
| 03 | `03-label-suspensi.md` | 0 | Ground truth; data sudah di disk |
| 04 | `04-universe-lapis-tiga.md` | 0 | Menentukan siapa yang di-screen |
| 05 | `05-sumbu-konsentrasi.md` | 0 | Sumbu terkuat dari uji kelayakan |
| 06 | `06-sumbu-volume-momentum.md` | 0 | Butuh normalisasi per saham |
| 07 | `07-sumbu-katalis.md` | 0 | Dirumuskan ulang setelah uji kelayakan |
| 08 | `08-sumbu-riwayat.md` | 0 | Sekaligus baseline kedua |
| 09 | `09-profil-konvergensi.md` | 0 | Menggabungkan 4 sumbu jadi profil |
| 10 | `10-kontrol-live.md` | **10** | Satu-satunya tugas berbiaya kredit |
| 11 | `11-baseline-pembanding.md` | 0 | **Gerbang go/no-go** |
| 12 | `12-backtest-lift.md` | 0 | **Gerbang go/no-go** |
| 13 | `13-tes-wajib.md` | 0 | Tiga tes yang dicari juri |
| 14 | `14-ledger-state.md` | 0 | Empat berkas yang dibuka juri |
| 15 | `15-loop-penilai.md` | 0 | Menilai peringatan vs kenyataan |
| 16 | `16-loop-pelajaran.md` | 0 | Lessons terstruktur |
| 17 | `17-evolusi-ambang.md` | 0 | Lima pagar |
| 18 | `18-paragraf-output.md` | 0 | Permukaan produk |
| 19 | `19-pengiriman-telegram.md` | 0 | Saluran + riwayat run nyata |
| 20 | `20-readme-disclaimer.md` | 0 | Yang diperiksa juri di repo |
| 21 | `21-naskah-video.md` | 0 | 30% nilai |

**Tugas 11 dan 12 adalah gerbang.** Kalau empat sumbu tidak mengalahkan kedua baseline,
berhenti dan pikirkan ulang — jangan lanjut ke 13.

## Di luar semua tugas ini

Dua hal yang tidak bisa dikerjakan Claude dan menggugurkan submission kalau terlewat:

1. **Onboarding Sectors semua anggota**, lalu **daftar tim sebelum 22 September 23:59 WIB.**
2. **Submit sebelum 30 September 23:59 WIB.**
