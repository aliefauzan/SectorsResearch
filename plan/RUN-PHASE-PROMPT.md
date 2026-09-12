# RUN-PHASE-PROMPT

Satu blok tempel-salin untuk menjalankan satu fase. **Hanya baris `PHASE:` yang berubah.**
Tempel ke sesi Claude Code yang dibuka di akar repo `Sectors`.

---

```
PHASE: 0

Kerjakan fase di atas, dan hanya fase itu.

## Baca, dalam urutan ini

1. plan/PROGRESS.md — seluruhnya. Ia satu-satunya berkas yang menyatakan keadaan nyata.
2. plan/README.md — semantik kotak centang, batas eksekusi, garis potong.
3. plan/phases/phase-<PHASE>-*.md — berkas fasenya.
4. Hanya bagian plan/01-architecture.md dan plan/02-data-model.md yang berkas fase itu rujuk.
   Jangan membaca keduanya utuh.

Jangan membaca berkas fase lain. Jangan membaca .claude/prds/ kecuali berkas fase menunjuknya.

## Berhenti sebelum mulai, kalau

- plan/PROGRESS.md menyatakan sebuah fase yang lebih awal belum terpenuhi, DAN fase itu ada di
  kolom "Menunggu" pada blok Status fase ini. Laporkan fase mana dan berhenti.
- Ada baris blocker terbuka yang pemiliknya "saya" (manusia) dan fase ini bergantung padanya.
  Laporkan dan berhenti.
- git status --porcelain tidak kosong dan perubahannya bukan milik Anda. Laporkan dan berhenti.

## Kerjakan

Ikuti daftar Tugas di berkas fase, berurut. Jangan mengerjakan tugas dari fase lain, bahkan
kalau tampak sepele dan bahkan kalau Anda sedang membuka berkasnya.

Batas eksekusi di plan/README.md berlaku penuh. Tujuh baris itu adalah batas, bukan preferensi.

## Sebelum menyatakan selesai

1. Jalankan test suite dan laporkan jumlah gate serta kode keluarnya:

       cd src/katalis && ./run.sh test; echo "exit=$?"

   Laporkan jumlah assertion per modul dan totalnya. Bandingkan dengan jumlah yang tertulis di
   plan/PROGRESS.md. Jumlah yang turun harus dijelaskan di baris yang sama.

2. Kalau Anda melakukan merge, rebase, atau pull apa pun selama fase ini, jalankan ulang
   perintah di atas setelahnya. Gate yang hijau sebelum merge tidak mengatakan apa-apa tentang
   gate setelah merge.

3. Telusuri Kriteria Keluar satu per satu, bernomor, dan untuk masing-masing nyatakan
   "terpenuhi" atau "tidak terpenuhi" beserta **bukti**: perintah yang Anda jalankan dan
   keluarannya. Tidak ada kriteria yang dinyatakan terpenuhi tanpa keluaran perintah.
   Kriteria yang tidak dapat Anda verifikasi sendiri ditandai "hanya manusia" dan dimasukkan
   ke daftar di bawah.

## Perbarui plan/PROGRESS.md di commit yang sama dengan kode

Bukan commit berikutnya. Commit yang sama.

- Perbarui blok "Di mana kita sekarang": fase, revisi Cloud Run, jumlah gate, saldo kredit.
- Perbarui baris fase ini di tabel fase, memakai hanya tiga keadaan: [ ], [x], [~].
  [x] menuntut selesai, ter-commit, DAN berjalan pada revisi Cloud Run yang melayani.
  [~] menuntut alasan di baris yang sama.
- Perbarui tabel blocker: tutup yang tertutup dengan tanggalnya, tambahkan yang baru.
- **Tambahkan** satu entri Session Log bertanggal di paling bawah. Jangan pernah menulis ulang
  atau menghapus entri yang sudah ada, termasuk entri Anda sendiri dari sesi sebelumnya.

## Laporkan apa yang hanya bisa dilakukan manusia

Daftar eksplisit di akhir, misalnya: mengklaim kredit di portal, melakukan push, membuat
proyek atau trigger di konsol GCP, menambahkan secret, menyambungkan Vercel, merekam dan
mengunggah video, memublikasikan post media sosial, mewawancarai pengguna, dan menekan submit.
Nyatakan untuk masing-masing apa yang sudah disiapkan supaya manusia tinggal mengeksekusi.
```

---

## Nilai `PHASE:`

| Nilai | Berkas | Kredit |
| --- | --- | --- |
| `0` | `phases/phase-0-foundation.md` | 0 |
| `1` | `phases/phase-1-suspension-modifier.md` | 0 |
| `2` | `phases/phase-2-deploy-pipeline.md` | 0 |
| `3` | `phases/phase-3-deterministic-classifier.md` | 0 |
| `4` | `phases/phase-4-pillar-verdicts.md` | 0 |
| `5` | `phases/phase-5-labeled-corpus.md` | 42 |
| `6` | `phases/phase-6-learning-and-llm.md` | 0 / kuota model |
| `7` | `phases/phase-7-surface-and-submission.md` | 0 |

## Akhiran opsional

Tambahkan di bawah baris `PHASE:`, satu per baris.

| Akhiran | Arti |
| --- | --- |
| `MODE: plan-only` | Jangan mengubah satu berkas pun di `src/`. Baca, telusuri Kriteria Keluar terhadap keadaan sekarang, laporkan apa yang sudah terpenuhi dan apa yang belum, lalu berhenti. Berguna sebelum memulai fase yang mahal |
| `MODE: resume` | Fase ini sudah dimulai di sesi lain. Baca Session Log paling bawah lebih dulu, lanjutkan dari tugas pertama yang belum selesai, dan jangan mengulangi tugas yang sudah dicatat selesai |
| `MODE: verify` | Jangan mengubah apa pun. Telusuri Kriteria Keluar dan nyatakan terpenuhi / tidak terpenuhi dengan bukti perintah. Perbarui `PROGRESS.md` hanya bila sebuah klaim ternyata salah |
| `CUT: <item>` | Terapkan pemotongan bernama dari bagian "Kalau Ini Melar" di berkas fase, atau dari garis potong di `plan/README.md`. Tandai barisnya `[~]` beserta alasannya. Jangan memotong apa pun yang tidak disebutkan di baris ini |

## Blok "Behind Schedule"

Tempel **sebagai ganti** improvisasi, bukan sebagai tambahan untuknya.

```
BEHIND SCHEDULE.

Jangan memutuskan sendiri apa yang dipotong. Terapkan garis potong di plan/README.md, berurut
dari atas, sampai sisa pekerjaan muat:

  1. S7 CLASSIFIER=llm (bagian B Fase 6)
  2. S6 katalis-learn (bagian A Fase 6)
  3. S5 halaman Vercel (bagian Fase 7)
  4. Simbol kelima dan keenam di Fase 5
  5. Tiga percakapan pengguna (bagian Fase 7)

Tidak pernah dipotong: pipeline deploy (Fase 2), empat pilar (Fase 0, 3, 4), dan Fase 7.

Untuk tiap item yang dipotong:
  - tandai barisnya [~] di plan/PROGRESS.md dengan alasannya di baris yang sama;
  - nyatakan metrik §5 mana yang menjadi tidak terpenuhi;
  - dan kalau yang dipotong adalah item 1 ATAU item 2, nyatakan secara eksplisit bahwa
    deklarasi track harus berpindah dari Track 01 ke Track 03 sebelum submit, dan tambahkan
    itu sebagai baris blocker dengan pemilik "saya" (manusia).

Laporkan pemotongannya sebelum mengerjakan apa pun, dan tunggu konfirmasi.
```
