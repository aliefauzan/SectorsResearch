# 01 · Kerangka scheduler yang jalan hari ini

**Kredit: 0** · Dependensi: tidak ada · **Kerjakan pertama, hari ini juga.**

## Kenapa ini nomor satu

Track 02 mensyaratkan bukti run tanpa ditunggui: konfigurasi jadwal **plus log
bertimestamp lintas hari**. Aturannya menyatakan run manual tanpa itu tidak cukup.
Tiga minggu riwayat tidak bisa dikarang tanggal 29 September. Semua tugas lain bisa
dikerjakan di minggu terakhir; yang ini tidak.

Kerangkanya boleh masih bodoh. Yang penting ia mulai berdetak sekarang.

## Prasyarat baca

- `research/docs/hackathon/02-tracks.md` bagian Track 02
- `research/plan/meridian-saham/spec.md` §6

## Berkas yang dibuat

```
app/__init__.py
app/tick.py                  satu siklus harian, saat ini cukup memanggil profil demo
app/config.py                jam tick, watchlist awal, path state
.github/workflows/tick.yml   jadwal + commit log kembali ke repo
state/runs.jsonl             append-only, satu baris per run
```

## Langkah

1. `app/tick.py` menjalankan satu siklus dan menulis satu baris ke `state/runs.jsonl`:
   `{"ts": ..., "run_id": ..., "symbols_screened": N, "warnings_emitted": N, "duration_ms": N, "status": "ok|error", "notes": "..."}`
2. Untuk sekarang, isi siklusnya boleh memanggil logika di
   `research/harness/src/profile_demo.py` atas data cache. Tidak apa-apa bodoh.
3. Jadwal `0 4 * * 1-5` UTC = **11:00 WIB**, hari kerja. Bukan jam 7 pagi —
   `/v2/suspensions/` baru di-refresh 10:00 WIB, dan itu sumber label utama.
4. Lewati hari libur bursa. Kalender IDX 2026 ada di
   `research/harness/src/synth_extended.py` — impor atau salin daftarnya.
5. Workflow harus commit `state/runs.jsonl` kembali ke repo, supaya riwayatnya
   tumbuh dan terlihat di GitHub.
6. Tambahkan `--dry-run` supaya bisa diuji tanpa efek samping.

## Kriteria selesai

```bash
python3 app/tick.py --dry-run          # keluar 0, tidak menulis apa pun
python3 app/tick.py                    # menambah tepat satu baris ke state/runs.jsonl
python3 -c "import json;[json.loads(l) for l in open('state/runs.jsonl')]"
```

- Workflow terlihat di tab Actions GitHub dengan jadwal aktif.
- Jalankan sekali secara manual lewat `workflow_dispatch` untuk membuktikan ia hidup.

## Jangan

- Jangan panggil API live. Siklus ini membaca cache.
- Jangan tunda tugas ini sampai logikanya matang. Kerangka bodoh yang berjalan
  sejak 9 September mengalahkan sistem sempurna yang mulai 25 September.
