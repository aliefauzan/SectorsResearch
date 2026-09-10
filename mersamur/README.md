# mersamur

**Untuk investor ritel Indonesia yang menerima tip saham di grup chat dan tidak
punya cara membedakan pergerakan nyata dari yang direkayasa.**

Tempel satu kode saham. Dapat satu paragraf yang menyebutkan apa yang tercatat di
data — dan di bawahnya, endpoint serta field asal tiap angka, supaya paragraf itu
bisa dibantah baris per baris.

```
$ python3 -m app.cli LIFE

LIFE

Pada jendela 2026-08-10 .. 2026-09-09, LIFE paling menonjol pada sumbu
volume: sesi terakhir tercatat 24,5x median 16 sesi bertransaksi sebelumnya
— 147.000 lembar terhadap 6.000 lembar, dengan ambang 5,0x. 2 dari 4 sumbu
tercatat menyala; sumbu lain terbaca konsentrasi broker 83,8% (menyala),
momentum persentil 44, katalis rasio 0,125. IDX tercatat menghentikan
perdagangan LIFE sebanyak 2 kali sebelum 2026-08-10, terakhir pada
2025-08-22 dengan klasifikasi cooling_down.

Deskriptif, bukan anjuran investasi: angka di atas adalah catatan atas
respons Sectors API pada jendela yang disebut, bukan penilaian atas
emitennya. Teks lengkapnya: mersamur/DISCLAIMER.md.

sumber tiap angka:
  - 24,5x — rasio volume terhadap median · /v2/daily/{symbol}/ (date, volume)
  - 16 — sesi bertransaksi di jendela · /v2/daily/{symbol}/ (date, volume)
  - 83,8% — pangsa broker teratas · /v2/broker-summary/{symbol}/top/ (…)
  - 40,5% — ambang konsentrasi · state/thresholds.json (current.concentration, …)
  - 2 — suspensi tercatat sebelum batas · /v2/suspensions/ (symbol, …)
  … 21 baris sitasi seluruhnya
```

Tidak ada vonis beli atau jual, tidak ada skor rekomendasi, tidak ada sinyal
merah-hijau. `app/render/paragraph.py` menolak mencetak paragraf yang memuat satu
pun angka tanpa sitasi, dan daftar kata terlarangnya ditegakkan oleh
[`app/tests/test_paragraph.py`](app/tests/test_paragraph.py). Baca
[`DISCLAIMER.md`](DISCLAIMER.md).

## Jalankan sendiri — nol kredit

Semua perintah dijalankan dari folder ini.

```bash
cd mersamur
python3 -m pytest app/tests -q               # 427 tes
python3 -m app.cli LIFE                      # paragraf + sitasi
python3 app/evaluate.py --compare-baselines  # gerbang go/no-go vs dua baseline
python3 app/backtest.py --walk-forward       # replay 2025-01-01..2026-08-26
python3 app/tick.py --dry-run                # satu siklus harian
python3 tools/feasibility.py                 # empat uji kelayakan
python3 tools/dashboard.py                   # papan pengguna -> state/dashboard.html
python3 tools/dashboard.py --mode pipeline   # catatan pembangunan
python3 tools/serve.py --open                # keduanya di localhost
```

`tools/serve.py` menyajikan papan di `127.0.0.1:8080` dan merakitnya ulang tiap
permintaan, jadi menjalankan `app/tick.py` atau menggeser satu ambang langsung
terlihat tanpa dibangun ulang. Ada dua halaman, dan pembedaannya disengaja:

* **`/`** — yang dipakai orang yang memakai produknya: catatan per kode saham,
  sitasi tiap angka, dan cara membacanya. Tidak ada tahap pipeline, tidak ada
  gerbang, tidak ada hitungan kredit.
* **`/pipeline`** — catatan pembangunan untuk yang menilai repo: tahap mana yang
  jalan dan di titik mana alirannya berhenti, gerbang go/no-go, hasil backtest,
  kredit, asal tiap payload.

Keduanya menampilkan keadaan sistem, bukan render ulang respons API — pembedaan
yang dituntut Track 03 — dan keduanya dijaga pemeriksa kosakata yang sama dengan
paragraf produk: satu kata vonis menghentikan halaman, bukan lolos begitu saja.

Tidak satu pun dari perintah di atas membuka soket ke Sectors API. Semuanya
membaca payload yang sudah dibayar di `../research/harness/recorded/`.

## Kenapa ini bukan resep GNN Anomaly Detection

Sectors sendiri sudah menerbitkan
[GNN Anomaly Detection bagian 1–3](https://docs.sectors.app/recipes/gnn-anomaly-detection/01-gnn-part-1)
— graf korelasi harga, skor anomali dari graph autoencoder, lalu **dikonfirmasi
dengan broker activity dan foreign flow** — dan halaman track resmi menyebutnya
sebagai kalibrasi kedalaman yang diharapkan. Dua dari empat sumbu produk ini
memang ada di resep itu, jadi perbedaannya dinyatakan di sini alih-alih dibiarkan
disimpulkan sendiri oleh juri yang menulisnya. **Resep itu mendeteksi anomali
statistik; produk ini menjawab pertanyaan pengguna pada momen keputusan** — satu
kode saham yang baru saja masuk ke grup chat, satu paragraf, tiap angka
tersitasi. **Resep itu tidak punya label; produk ini divalidasi terhadap suspensi
resmi IDX** — 452 peristiwa cooling-down dari `/v2/suspensions/`
([`app/labels.py`](app/labels.py)), yang membuat "salah" punya arti yang bisa
dihitung. **Dan resep itu berjalan sekali; produk ini mengoreksi dirinya sendiri
dan menyimpan jejaknya** — tiap peringatan diadili terhadap apa yang benar-benar
terjadi ([`app/agent/adjudicate.py`](app/agent/adjudicate.py)), tiap hasil jadi
satu baris pelajaran ([`app/agent/lessons.py`](app/agent/lessons.py)), dan ambang
hanya bergerak lewat lima penjaga yang ditulis di
[`app/agent/evolve.py`](app/agent/evolve.py), dengan alasan dan bukti tersimpan di
dalam `state/thresholds.json` itu sendiri.

Pembedanya juga bukan datanya. Broker summary sudah lazim di alat ritel Indonesia
dan bandarmology bukan istilah baru. Yang baru di sini adalah **konvergensi empat
saksi yang datanya independen + validasi terhadap peristiwa resmi + loop koreksi
diri yang jejaknya ada di repo**. Alat yang ada menampilkan; ini menyimpulkan dan
mempertanggungjawabkan.

## Peta bukti

Tiap klaim di atas punya berkas yang membuktikannya, dan tiap berkas bisa dibaca
tanpa menjalankan apa pun.

| Pertanyaan | Berkas | Isinya sekarang |
| --- | --- | --- |
| Apa yang sistem katakan, kapan, terhadap ambang berapa? | [`state/warnings.jsonl`](state/warnings.jsonl) | **kosong** — belum ada simbol yang melewati ambang 3 dari 4 sumbu |
| Apa yang benar-benar terjadi setelahnya? | [`state/outcomes.jsonl`](state/outcomes.jsonl) | **kosong** — tidak ada peringatan untuk diadili |
| Apa yang dipelajari dari selisihnya? | [`state/lessons.jsonl`](state/lessons.jsonl) | **kosong** — tidak ada hasil untuk dipelajari |
| Ambangnya berapa, dan kenapa pernah berubah? | [`state/thresholds.json`](state/thresholds.json) | versi 3, satu entri `history` dengan alasan dan angkanya |
| Apakah siklus harian benar-benar jalan tanpa ditunggui? | [`state/runs.jsonl`](state/runs.jsonl) · [`../.github/workflows/tick.yml`](../.github/workflows/tick.yml) | satu baris sejauh ini; cron `0 4 * * 1-5`, log di-commit balik ke repo |
| Apakah empat sumbu mengalahkan baseline naif? | [`state/backtest_report.json`](state/backtest_report.json) · `python3 app/evaluate.py --compare-baselines` | **belum bisa diputuskan** — lihat §Batasan |
| Berapa kredit yang dibelanjakan, untuk apa? | [`../research/harness/recorded/_ledger.jsonl`](../research/harness/recorded/_ledger.jsonl) | 33 panggilan / **62 kredit** pada 2026-09-09 milik produk ini (52 kelayakan + 10 lengan kontrol) |
| Berapa kredit yang dibelanjakan **produk saat berjalan**? | `state/credits.jsonl` | **belum ada** — belum satu pun panggilan berbayar dibuat oleh produk |

Tiga berkas pertama kosong dan itu dilaporkan apa adanya. `app/tick.py` menyaring
watchlist tiap hari kerja; pada ambang yang didokumentasikan produk ini, belum ada
satu simbol pun yang lewat. Log yang sepi tapi berasal dari ambang yang benar
lebih berguna daripada log yang ramai dari ambang placeholder — alasannya ada di
docstring [`app/tick.py`](app/tick.py).

## Ketergantungan pada Sectors

**Cabut Sectors API dan produk ini berhenti bekerja.** Tidak ada sumber kedua,
tidak ada scraping, tidak ada data sintetis yang dipakai sebagai sumber produk.
Enam endpoint, masing-masing menjawab satu hal:

| Endpoint | Dipakai untuk | Di berkas |
| --- | --- | --- |
| `/v2/suspensions/` | **satu-satunya ground truth** — 585 baris, 452 di antaranya cooling-down; jadi label, sumbu riwayat, dan bahan adjudikasi | [`app/labels.py`](app/labels.py) · [`app/axes/history.py`](app/axes/history.py) |
| `/v2/companies/` | universe kerja: 200 emiten berkapitalisasi terkecil, plus 102 kandidat kontrol yang belum pernah disuspensi | [`app/universe.py`](app/universe.py) |
| `/v2/broker-summary/{symbol}/top/` | sumbu konsentrasi — pangsa broker pembeli teratas | [`app/axes/concentration.py`](app/axes/concentration.py) |
| `/v2/brokers/` | kohort tiap kode broker (ritel / campuran / institusi), yang menggeser ambang konsentrasi | [`app/axes/concentration.py`](app/axes/concentration.py) |
| `/v2/daily/{symbol}/` | sumbu volume (rasio terhadap median) dan sumbu momentum (persentil kenaikan lima sesi) | [`app/axes/volume_anomaly.py`](app/axes/volume_anomaly.py) · [`app/axes/momentum.py`](app/axes/momentum.py) |
| `/v2/news/` | sumbu katalis — pangsa artikel berdimensi fundamental di jendela yang sama | [`app/axes/catalyst.py`](app/axes/catalyst.py) |

Satu-satunya panggilan jaringan lain adalah ke Telegram Bot API, untuk mengirim
pesan saat sebuah simbol *memasuki* keadaan itu — bukan digest harian
([`app/render/notify.py`](app/render/notify.py)).

## Batasan yang dinyatakan sendiri

Ini bagian yang biasanya ditemukan juri sendiri, jadi lebih baik ditulis di sini.

**Gerbang go/no-go belum bisa diputuskan.** `python3 app/evaluate.py
--compare-baselines` berakhir dengan `HASIL: BERHENTI` — bukan karena model kalah,
melainkan karena perbandingannya belum sah. Tiga penghalangnya dicetak di akhir
perintah itu: ketersediaan data tidak simetris antara lengan kasus (sampai 4 sumbu
terukur) dan lengan kontrol (rata-rata 1,2), sistem empat sumbu tidak mengeluarkan
satu pun peringatan sehingga liftnya tidak terdefinisi, dan lengan kontrol dipilih
dengan kriteria "tidak pernah disuspensi" — variabel yang persis dibaca baseline
`pernah_disuspensi`, sehingga di universe ini baseline itu mustahil salah.
Menyetel ambang untuk memenangkan gerbang ini dilarang, dan tidak dilakukan.

**Label hanya ada sejak 2025.** Nol suspensi cooling-down sebelum 2025 di 585
baris `/v2/suspensions/`. Riwayat yang bisa dipakai 20 bulan, bukan 7,7 tahun.

**Backtest terbatas anggaran kredit.** `state/backtest_report.json` merekam
sendiri tiga batasnya di field `batas`: baris screener dan daftar broker adalah
snapshot September 2026 tanpa tanggal, jadi keanggotaan universe pada tanggal
lebih awal memakai informasi yang belum ada saat itu — kebocoran seleksi yang
diketahui dan tidak bisa diperbaiki tanpa membeli screener historis; kalender
libur hanya milik 2026; panel broker adalah agregat satu jendela tanpa rincian
harian, sehingga sumbu konsentrasi tidak terukur sepanjang periode uji. Set
penyetelan bahkan tidak punya satu pun sesi harga yang terlihat — `/v2/daily/`
hanya terekam untuk 2026-08-10..2026-09-09.

**Hold-out kecil.** 6 pasangan (tanggal, emiten) berlabel di sisi hold-out. Angka
apa pun dari sana punya selang kepercayaan lebar dan tidak boleh dikutip sebagai
presisi produk. Hold-out tidak dipakai menyetel apa pun pada jalankan ini
(`holdout_dipakai_menyetel: false`).

**Kelompok kontrol 10 nama.** Lengan kontrol yang dibeli live hanya sepuluh emiten
(`plans/plan-control.json`, 10 kredit), dari 102 kandidat bersih. Sepuluh nama
tidak cukup untuk memisahkan "kecil" dari "direkayasa" secara meyakinkan.

**Base rate 0,77%** per saham per 10 hari bursa. Presisi telanjang akan terlihat
buruk apa pun modelnya; itu sebabnya metrik yang dilaporkan adalah lift, bukan
akurasi. Model yang tidak pernah memperingatkan apa pun tetap 99,2% akurat.

## Angka yang membentuk produk ini

Dari data live 9 September 2026, bisa dijalankan ulang gratis dengan
`python3 tools/feasibility.py`. Rinciannya di
[`riset/temuan-kelayakan.md`](riset/temuan-kelayakan.md).

- **452** suspensi cooling-down IDX di 585 baris, **tidak satu pun sebelum 2025**
- **0,77%** base rate per saham per 10 hari bursa → laporkan lift, bukan akurasi
- **78%** peristiwa berasal dari emiten yang pernah disuspensi → baseline kedua,
  sekaligus risiko kebocoran
- **61,6%** median konsentrasi broker teratas di saham tersuspensi, vs 11–34% blue chip
- **49%** dari 200 saham terkecil punya riwayat suspensi → universe inilah yang
  membuat statistiknya bisa bekerja
- **berita ada, tapi didominasi `technical`** (21 dari 30 artikel); `financials`
  dan `future` jarang → sumbu katalis dirumuskan sebagai *tidak ada artikel
  berdimensi fundamental*, bukan *tidak ada berita*

## Isi folder

```
mersamur/
  README.md          berkas ini
  DISCLAIMER.md      deskriptif, bukan saran investasi
  app/               kode produk
    cli.py           tempel satu ticker, dapat satu paragraf
    tick.py          satu siklus harian → state/runs.jsonl + Telegram
    axes/            empat sumbu: konsentrasi, volume, momentum, katalis
    agent/           adjudicate → lessons → evolve, loop koreksi diri
    render/          paragraf bersitasi + pengiriman transisi
    baselines/       dua lawan tanding wajib
    evaluate.py      gerbang go/no-go
    backtest.py      replay walk-forward + hold-out
    tests/           427 tes
  state/             enam berkas bukti — lihat §Peta bukti
  riset/             kenapa produk ini berbentuk begini
  tools/             skrip analisis, nol kredit
  plans/             rencana capture khusus produk ini
  tasks/             21 tugas + PROMPT.md — satu berkas satu tugas
```

### `riset/` — kenapa begini

| Berkas | Isi |
| --- | --- |
| [`ringkas.md`](riset/ringkas.md) | Lima menit. Mulai dari sini |
| [`deep-research.md`](riset/deep-research.md) | Apa yang menggerakkan saham vs kripto |
| [`spec.md`](riset/spec.md) | Arsitektur, skema berkas state, anggaran kredit |
| [`red-team.md`](riset/red-team.md) | Dua belas cara ide ini kalah |
| [`temuan-kelayakan.md`](riset/temuan-kelayakan.md) | **Data live.** Empat gerbang kelayakan, 52 kredit |

### Yang dipakai dari luar folder ini

Dosir riset dan harness offline berlaku untuk seluruh repo, jadi tetap di tempatnya:

| Path | Isi |
| --- | --- |
| `../research/harness/recorded/` | payload live + `_ledger.jsonl` — **sudah dibayar**, pakai ini, jangan beli ulang |
| `../research/harness/src/mock_server.py` | rehearse rencana capture gratis |
| `../research/harness/src/capture.py` | satu-satunya yang boleh memanggil API live |
| `../research/docs/api/` | 16 dokumen referensi Sectors API |
| `../research/docs/hackathon/` | aturan, track, checklist |
| `../.env` | `SECTORS_API_KEY` — git-ignored sejak commit pertama |

---

Track 02 (Automation & Workflows), Sectors Hackathon 2026. Tidak ada eksekusi
transaksi otomatis — dilarang di semua track, dan produk ini tidak punya jalur
kode untuk melakukannya. [`DISCLAIMER.md`](DISCLAIMER.md).
