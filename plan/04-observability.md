# 04 · Observabilitas

Satu pertanyaan yang harus bisa dijawab kapan saja: **kenapa kartu ini berbunyi begini.**
Semua yang ada di bawah dibangun untuk menjawab itu, dan tidak ada yang dibangun untuk
menjawab pertanyaan lain.

## Satu catatan tentang nama

Rencana ini mewarisi kosakata dari rencana rujukan, yang menyebut `plans.jsonl`. Berkas dengan
nama itu **tidak ada di repo ini** dan tidak akan dibuat:

```bash
find . -name "plans.jsonl" -not -path "./.git/*"     # tidak ada keluaran
```

Padanannya di sini terbelah dua, dan pembelahannya berguna: **rencana** adalah berkas JSON
statis di `research/harness/plans/`, dan **apa yang benar-benar terjadi** adalah baris di
`research/harness/recorded/_ledger.jsonl`. Rencana adalah niat, ledger adalah belanja, dan
menyatukan keduanya dalam satu berkas persis yang membuat angka 272-vs-377 tidak ketahuan
selama beberapa hari.

## `research/harness/plans/*.json` — niat, sebelum satu kredit keluar

Tiap rencana tangkapan adalah daftar panggilan dengan parameter yang sudah dibatasi, dikelompokkan
per tier. Rencana dijalankan lebih dulu terhadap mock, gratis, lalu terhadap API live dengan
batas anggaran keras.

```bash
cd research/harness && python3 src/capture.py --plan plans/plan.json --dry-run
```

Yang harus diperiksa sebelum sebuah rencana dijalankan live: tidak ada `sections`,
`classifications`, `periods` atau `n_quarters` yang dibiarkan default (sebuah company report
yang di-default berbiaya 8, bukan 1), dan tidak ada identifier yang tidak berasal dari respons
sebelumnya (404 tetap ditagih 1 kredit, karena lookup-nya berjalan).

## `research/harness/recorded/_ledger.jsonl` — belanja, satu baris per panggilan

175 baris hari ini. Satu baris adalah satu panggilan, dan ia menyimpan cukup untuk menjawab
"kenapa saldo bergerak":

```json
{"ts": 1788626877.18, "path": "/v2/subsectors/", "params": {}, "status": 403,
 "est_cost": 1, "billed": false, "billed_cost": 0, "pages_fetched": 0, "cost_headers": {}}
```

`cost_headers` selalu kosong, dan itu bukan bug: **API tidak mengirim header biaya sama
sekali.** `est_cost` adalah model harness, `billed_cost` adalah tebakannya tentang apa yang
benar-benar ditagih, dan satu-satunya catatan independen adalah ekspor CSV portal di
`research/evidence/usage-log/`. Alat yang mempertemukan keduanya:

```bash
cd research/harness && python3 src/reconcile_usage.py
```

Ia keluar dengan status 1 kalau keduanya tidak sepakat pada endpoint yang seharusnya sepakat.
Jalankan sebelum membelanjakan 42 kredit Fase 5, bukan sesudah.

`_manifest.json` di sebelahnya (167 entri) memetakan slug panggilan ke berkas payload-nya —
itulah yang membuat `recorded/` datar alih-alih berupa pohon yang bisa dijelajahi. Jangan
menebak nama berkas; baca manifest.

## Keluaran gate

`./run.sh test` mencetak satu blok per modul, satu baris per fungsi check, dan jumlah assertion
per fungsi. Hari ini 73 assertion hijau di 18 fungsi check, dan kode keluar 0.

```bash
cd src/katalis && ./run.sh test; echo "exit=$?"
```

Format keluarannya sengaja bukan TAP dan bukan JUnit: beberapa check mencetak **bukti** di
bawah barisnya sendiri — misalnya `registry 88 codes · flow 85 codes · unmapped ['JB'] at
0.0815% of gross`, dan blok verdict lengkap dari `check_verdict_is_never_advice`. Baris bukti
itulah yang membuat suite berguna saat sebuah kartu salah, karena ia menunjukkan nilai
antara, bukan hanya lulus/gagal.

Yang harus tetap benar tentang keluaran ini saat fase berjalan:

- Jumlah gate **naik**, tidak pernah turun diam-diam. Kalau sebuah fase mengurangi jumlahnya,
  `PROGRESS.md` menyebut alasannya di baris yang sama.
- Kode keluar 1 kalau ada satu assertion merah. Cloud Build (D5) bersandar pada ini.
- Suite tidak pernah menyentuh jaringan. `env -u SECTORS_API_KEY ./run.sh test` harus tetap
  hijau, dan itu adalah cara termurah memverifikasi §12.3 aturan 3.

## Jejak per kartu

Kartu itu sendiri adalah jejaknya. Tiap angka mencetak nama, nilai, satuan, dan — di blok
FIELD — pasangan `(endpoint → field)` yang melahirkannya. Tidak ada log terpisah yang harus
dibuka untuk mengetahui dari mana `pangsa_puncak 64.7%` berasal.

```bash
cd src/katalis && ./run.sh pilar LIFE 2026-09-01
```

Tiga hal yang dicetak kartu dan **tidak** akan dipindahkan ke log: blok FIELD, blok
YANG BELUM KAMI PERIKSA, dan catatan sitasi per figure. Memindahkannya ke log berarti membuat
pembaca kartu mempercayai sesuatu yang tidak ia lihat, dan itu membatalkan alasan produk ini
ada.

Dua hal yang **belum** dicetak kartu dan seharusnya:

- **Asal ambang.** PRD §7 dan §13 menyatakan kartu menyebut `shipped` atau `learned`; hari ini
  ia tidak menyebut keduanya. `thresholds.provenance()` sudah mengembalikan pasangan itu; yang
  hilang hanya penulisannya ke kartu.
- **Mana classifier yang dipakai.** `CLASSIFIER=rules` versus `llm`. Nol referensi `CLASSIFIER`
  di `src/katalis/` hari ini; Fase 3 memasangnya.

## Apa yang diperiksa saat sebuah kartu salah

Urutan ini dari yang paling sering benar ke yang paling jarang. Ikuti dari atas; berhenti saat
ketemu.

1. **Simbolnya memang dinilai?** `./run.sh symbols`. `tanpa_broker` dan `baseline_tipis`
   adalah jawaban, bukan bug.
2. **Tanggalnya ada di deret?** Kartu memakai hari terakhir yang ada bila tanggal tidak
   diberikan, dan jendela peristiwa mundur `event_window` hari bursa dari sana.
3. **Payload-nya yang mana?** Baca `_manifest.json`, bukan nama berkas. Satu simbol bisa punya
   beberapa tangkapan dengan jendela tanggal berbeda.
4. **Angkanya salah atau ambangnya?** Kartu mencetak keduanya. `./run.sh method` mencetak
   ambang, lantai, langit-langit, dan alasannya. Kalau nilai turunan benar tetapi statusnya
   terasa salah, yang diperdebatkan adalah ambang — dan itu percakapan yang berbeda.
5. **Ambangnya `shipped` atau `learned`?** `python3 -c "import thresholds as T; print(T.provenance('<nama>'))"`
   dari `src/katalis/`. Sampai Fase 0 selesai, berkas `state/thresholds.learned.json` bisa
   menggeser ambang tanpa satu gate pun merah — jadi periksa keberadaan berkas itu lebih dulu.
6. **Ada data setelah `as_of` yang bocor?** Sampai Fase 0 selesai, `actions` tidak dipotong
   `upto()` (`src/katalis/pillars.py:498`), jadi `aksi_korporasi` bisa menghitung aksi yang
   bertanggal setelah tanggal kartu.

## Apa yang tidak dibangun

Dinyatakan supaya tidak muncul diam-diam di tengah fase.

| Tidak dibangun | Kenapa |
| --- | --- |
| Log terstruktur, level log, korelasi request | Satu proses, satu kartu, keluar. Yang perlu dibaca sudah tercetak di kartu |
| Metrik, dashboard, alerting | Cloud Run `min-instances=0` dengan `SOURCE=recorded` tidak punya kondisi darurat yang bisa dibangunkan seseorang |
| Tracing terdistribusi | Satu-satunya panggilan lintas layanan adalah Vercel → Cloud Run, dan ia sinkron dan tunggal |
| Riwayat kartu / audit trail per pengguna | Tidak ada pengguna, tidak ada sesi, tidak ada state. Kartu adalah fungsi murni dari payload dan `as_of` |
| Penilaian kartu terhadap hari bursa berikutnya | Itu forward test, dan ia dipotong di PRD §6. Bentuk replay-nya adalah Fase 6 |
