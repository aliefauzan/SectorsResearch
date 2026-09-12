# Naskah Video — Earnings Relay (3 menit)

Bobot penilaian: video & storytelling 30%. Satu cerita, satu orang, satu masalah.

## 0:00–0:20 · Orang dan masalahnya

**BELUM DIISI.** Butuh satu orang nyata yang menerbitkan ringkasan kuartalan — tim IR emiten,
analis sekuritas kecil, atau compliance — dengan kutipan verbatim dari wawancara dan angka
berapa menit proses manual mereka sekarang per laporan.

Jangan pakai persona karangan dan jangan pakai anggota tim sendiri sebagai pengguna. Juri
menilai apakah orang nyata bisa memakainya hari ini; persona rekaan justru membuktikan
sebaliknya.

## 0:20–0:50 · Laporan masuk, pack keluar

Layar: kuartal baru terdeteksi → 5 slide Indonesia tersusun. Tidak ada tangan menyentuh
keyboard. Tunjukkan waktunya di pojok layar.

## 0:50–1:35 · Tiap angka punya asal

Klik satu angka di slide. Muncul `endpoint`, `field`, rumus, `as_of`. Ulangi untuk satu angka
lain di slide berbeda. Inilah jawaban atas halusinasi LLM pada data keuangan — bukan klaim,
tapi mekanisme.

## 1:35–2:10 · Produk menolak dirinya sendiri

Jalankan di layar:

```bash
cd src/earnings-relay && python3 attack_classes.py --run
```

Tunjukkan keluarannya apa adanya, termasuk catch rate hari itu dan serangan yang masih
MISSED. Sebut dengan suara: angka ini turun setelah diukur, dan itu justru buktinya nyata.

## 2:10–2:40 · Jalan sendiri tanpa diawasi

```bash
tail -3 state/scheduler.jsonl
```

Tunjukkan `state/schedule_config.md` (baris cron) berdampingan dengan lognya. Sebutkan sejak
tanggal berapa riwayat dimulai — jangan membulatkan ke atas.

## 2:40–3:00 · Batas yang diakui

Sebut dua batasan dengan lugas: komparator sekuensial dilabeli, bukan year-over-year; dan
serangan yang belum tertangkap. Juri memverifikasi repo — menemukan sendiri apa yang
disembunyikan jauh lebih mahal daripada menyebutnya duluan.

Tutup: satu kalimat tentang siapa yang bisa memakainya besok pagi.

## Aturan produksi

- Semua angka yang muncul di layar harus berasal dari perintah yang dijalankan saat rekaman,
  bukan slide teks.
- Kalau satu perintah gagal saat rekam, tampilkan kegagalannya dan run recovery-nya.
- Bahasa Indonesia sepanjang video.
