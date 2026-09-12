# LANES — empat sesi berjalan bersamaan, satu penulis per berkas

Ditulis 2026-09-12, saat Fase 3 baru mendarat di `master` (`29660a1`) dan tiga lane dibuka
paralel. Berkas ini **bukan** rencana; ia aturan lalu lintas. Kalau ia berselisih dengan
`PROGRESS.md`, `PROGRESS.md` yang benar soal keadaan dan berkas ini yang benar soal siapa
boleh menulis apa.

## Lane yang hidup

| Cabang | Worktree | Memiliki (boleh tulis) | Dilarang menyentuh | Kredit |
| --- | --- | --- | --- | --- |
| `master` | `/Users/af/dumpProject/Sectors` | `plan/PROGRESS.md`, `plan/LANES.md`, deploy Cloud Run | — | 0 |
| `fase4-verdicts` | `sectors-6` | `src/katalis/pillars.py`, `card.py`, `plan/phases/phase-4-*.md`, **dan `plan/PROGRESS.md`** | `classify.py` selain memanggilnya, `web/`, `research/harness/plans/` | 0 |
| `fase5-prep` | `sectors-7` | `research/harness/plans/`, `plan/inputs/fase-5-prep.md` | seluruh `src/katalis/`, `plan/PROGRESS.md`, panggilan API live | 0 |
| `vercel-page` | `sectors-8` | `web/`, `plan/inputs/fase-7-s5.md` | seluruh `src/katalis/`, `plan/PROGRESS.md` | 0 |

`fase4-verdicts` adalah **satu-satunya** lane selain `master` yang boleh menulis
`PROGRESS.md`, karena ia dijalankan dengan prompt fase penuh yang menuntutnya. Konsekuensinya
ada di urutan merge di bawah, dan bukan sesuatu yang boleh diimprovisasi.

## Urutan merge — berurut, tidak paralel

1. **`fase4-verdicts` lebih dulu.** Ia menulis ulang blok "Di mana kita sekarang", tabel fase,
   dan menambah entri Session Log. Apa pun yang menulis `PROGRESS.md` sebelum ia mendarat
   menghasilkan konflik yang harus diselesaikan tangan di berkas yang justru paling mahal
   kalau salah.
2. **`fase5-prep`.** Hanya `research/harness/plans/` dan satu berkas `plan/inputs/`. Tidak
   bersinggungan dengan apa pun di atas.
3. **`vercel-page`.** Hanya `web/`. Tidak bersinggungan.

Setelah **tiap** merge, bukan sekali di akhir:

```bash
cd src/katalis && ./run.sh test; echo "exit=$?"
```

Gate yang hijau sebelum merge tidak mengatakan apa-apa tentang gate setelah merge. Jumlah
assertion dilaporkan tiap kali, dan jumlah yang turun dijelaskan di baris yang sama.

## Deploy: satu penulis, selalu `master`

Hanya sesi `master` yang menjalankan `gcloud builds submit`. Dua build bersamaan berlomba
pada revisi yang melayani, dan yang kalah tetap meninggalkan tag di registry yang menyimpan
hanya lima. Lane lain menyiapkan kode; `master` yang menerbitkannya.

## Fakta yang sudah basi di `PROGRESS.md`, diperbaiki setelah merge 1

| Baris | Keadaan nyata per 2026-09-12 20:30 WITA | Perintah |
| --- | --- | --- |
| "empat/lima commit lokal belum di-push" | **nol** belum di-push; `origin/master` = `29660a1` | `git rev-list --count origin/master..HEAD` → `0` |
| Blok Status tidak menyebut lane paralel | tiga lane hidup, tabel di atas | `git worktree list` |
| Versioning bucket tidak disebut | `gs://katalis-recorded` versioning **mati** | `gcloud storage buckets describe gs://katalis-recorded --format='value(versioning)'` → kosong |

## Kalau sebuah lane menyimpang dari lingkupnya

Lane yang menyentuh berkas milik lane lain tidak di-merge. Ia diminta membatalkan berkas itu
(`git checkout master -- <path>`) dan commit ulang. Alasannya bukan kerapian: dua sesi yang
mengedit `pillars.py` bersamaan menghasilkan gate hijau di dua cabang dan merah setelah
digabung, dan yang hilang adalah kepercayaan pada angka gate itu sendiri.
