# Jadwal Unattended — earnings-relay (Track 02)

## Cron

```cron
0 2 * * *  cd /path/ke/repo && SECTORS_BASE_URL=http://127.0.0.1:8787 python3 state/scheduler.py >> state/cron.out 2>&1
```

Padanan Cloud Scheduler: frekuensi `every 24 hours`, target Cloud Run job yang menjalankan
perintah yang sama.

## Apa yang dijalankan tiap siklus

1. `src/earnings-relay/gate.py` — 5 blok check, termasuk `cross_source_mismatch`.
2. `src/earnings-relay/attack_classes.py --run` — 5 kelas serangan, catch rate diukur ulang.

Tidak ada intervensi manusia per siklus. Nol kredit Sectors: sumber data `research/harness/recorded/`,
`SECTORS_BASE_URL` menunjuk `mock_server.py`.

## Bukti yang dihasilkan

| Berkas | Isi |
|---|---|
| `state/scheduler.jsonl` | satu baris JSON per run, append-only |
| `state/runs/<run_id>.json` | satu berkas per run, `run_id` = timestamp beserta zona waktu |

Tiap entri membawa `started_at`, `finished_at`, `duration_s`, `gate_pass`, `gate_fail`,
`catch_rate`, `credits_spent`.

## Verifikasi

```bash
python3 state/scheduler.py          # satu siklus manual
wc -l state/scheduler.jsonl         # berapa run tercatat
tail -1 state/scheduler.jsonl       # run terakhir
```

## Catatan jujur

Riwayat dimulai **12 September 2026**. Jumlah run yang tercatat adalah apa adanya dari
`wc -l state/scheduler.jsonl` — tidak ada entri yang ditulis mundur. Riwayat bertanggal lebih
awal dari tanggal itu sengaja dihapus karena dibuat serentak dan tidak mewakili run nyata.
