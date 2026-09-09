# Spec Build — Pemeriksa Kerapuhan Saham

> Spesifikasi kerja untuk ide yang dipilih di [`deep-research.md`](deep-research.md).
> Ditulis 9 September 2026. Tenggat: registrasi **22 Sep**, submission **30 Sep**, 23:59 WIB.
> Semua nama field dan biaya kredit di dokumen ini **diverifikasi terhadap payload asli** di
> `research/harness/recorded/`, bukan terhadap contoh spec.

---

## 0. Temuan yang mengubah spec ini

Sebelum menulis satu baris kode, ini yang ditemukan dari membaca ulang payload yang sudah
terekam pada 6 September:

**`/v2/suspensions/` adalah label yang seolah dibuat khusus untuk produk ini.**

```
pagination: {"total_count": 583, "limit": 20, "has_next": true}
```

583 peristiwa suspensi tersedia. Dan dari 20 baris terbaru (11 Ags – 4 Sep 2026), **18 di
antaranya beralasan sama**:

> *"Terjadinya peningkatan harga kumulatif yang signifikan pada saham ASLI.JK, dalam rangka
> cooling down sebagai bentuk perlindungan bagi investor"*

IDX **mensuspensi saham justru karena perilaku pump**, mengumumkannya dengan tanggal, alasan,
dan `pdf_url` resmi. Itu bukan proksi label — itu label yang sesungguhnya, dari wasit pasar,
bertanggal, dan bisa diverifikasi juri sendiri dengan mengklik PDF-nya.

Konsekuensinya untuk seluruh proyek:

1. **Ground truth-nya ada dan murah.** 583 peristiwa ÷ 20 baris per halaman = ~30 panggilan =
   **~30 kredit** untuk seluruh riwayat. Backtest tidak lagi hipotetis.
2. **Produknya jadi bisa dinilai secara objektif.** "Apakah sinyal kerapuhan hari H−5 memprediksi
   suspensi cooling-down di hari H?" adalah pertanyaan yang punya jawaban angka.
3. **Videonya punya bukti.** Bukan "menurut model kami saham ini rapuh", melainkan "model kami
   menandainya lima hari sebelum IDX mensuspensinya — ini pengumuman resminya."

Ini satu-satunya bagian dari proyek yang harus dikerjakan **hari pertama**. Kalau sinyalnya
tidak memprediksi apa-apa, Anda perlu tahu tanggal 11 September, bukan tanggal 27.

---

## 1. Produk

**Untuk siapa:** investor ritel Indonesia yang menerima tip saham di grup Telegram dan tidak
punya cara membedakan pergerakan nyata dari yang direkayasa.

**Apa yang dilakukan:** menerima satu ticker (atau watchlist), mengembalikan satu paragraf
deskriptif tentang apa yang membuat saham itu rapuh — dan menjalankan screen yang sama setiap
hari kerja, menilai peringatannya sendiri terhadap pengumuman IDX, lalu menyesuaikan ambangnya.

**Output, bentuk final:**

> *ASLI diperdagangkan dengan free float 8%, satu broker berkohort ritel mengambil 61% dari net
> beli selama lima sesi terakhir, volumenya 8× median 30 hari, dan tidak ada berita berdimensi
> `financials` maupun `future` dalam 90 hari. Empat dari empat sumbu menyala. Pola kombinasi ini
> muncul pada 23 dari 41 saham yang disuspensi IDX untuk cooling-down sejak Januari 2026.*

**Yang tidak pernah dilakukan:** memberi vonis beli/jual, skor yang disajikan sebagai
rekomendasi, atau sinyal merah/hijau. Deskriptif sepanjang waktu — itu yang menjaga produk ini
di sisi aman code of conduct.

**Track:** 02 (Automation & Workflows). Intinya jadwal harian + bukti run tanpa ditunggui;
loop belajar adalah kedalaman teknisnya.

---

## 2. Kontrak data — diverifikasi dari payload asli

Jangan tulis parser dari contoh spec. Ini bentuk yang benar-benar dikembalikan.

### `/v2/suspensions/` — 1 kredit per halaman (20 baris)

```json
{"results": [{"symbol": "ASLI.JK", "suspension_date": "2026-09-04",
              "reason": "Terjadinya peningkatan harga kumulatif yang signifikan ...",
              "pdf_url": "https://www.idx.co.id/..."}],
 "pagination": {"total_count": 583, "limit": 20, "offset": 0,
                "has_next": true, "next_offset": 20}}
```

Refresh **harian 10:00 WIB**. Ini menentukan jam tick. Klasifikasikan `reason` dengan regex ke
tiga kelas: `cooling_down` (mengandung "peningkatan harga kumulatif"), `penurunan_harga`,
`lain`. Hanya `cooling_down` yang dipakai sebagai label positif.

### `/v2/broker-summary/{symbol}/top/` — 2 kredit

```json
{"symbol": "BBCA.JK", "start": "...", "end": "...", "origin": "all", "cohort": "all",
 "top_buyers":  [{"rank": 1, "broker_code": "...", "net_idr": 123, "buy_idr": ..., "sell_idr": ...}],
 "top_sellers": [{"rank": 1, "broker_code": "...", "net_idr": -456, ...}]}
```

`net_idr` **sudah negatif** untuk `top_sellers`. Menerima parameter `cohort` dan `origin`
langsung — "broker ritel mendominasi sisi beli" adalah satu panggilan, bukan join.

### `/v2/brokers/` — 1 kredit, cache permanen

```json
[{"code": "...", "name": "...", "is_foreign": false, "cohort": "...", "license_type": "..."}]
```

88 baris. Perhatikan: fieldnya **`is_foreign` (boolean)**, bukan `origin`. Ambil sekali,
simpan ke berkas, jangan panggil lagi.

### `/v2/daily/{symbol}/` — 1 kredit, ≤90 hari

```json
[{"symbol": "...", "date": "...", "close": .., "open": .., "high": .., "low": ..,
  "volume": .., "market_cap": ..}]
```

### `/v2/foreign-flow/{symbol}/` — 1 kredit

```json
{"symbol": "...", "data": [{"date": "2026-06-08", "net_foreign_inflow": -832847864000}]}
```

### `/v2/news/?symbols=` — 1 kredit

```json
{"results": [{"title": .., "body": .., "source": .., "thumbnail": .., "timestamp": ..,
              "sector": .., "sub_sector": .., "tags": [..], "symbols": [..],
              "dimension": {"future": 0, "dividend": 0, "ownership": 0, "technical": 0,
                            "valuation": 0, "financials": 0, "management": 0,
                            "sustainability": 0}}]}
```

`body` ~500 karakter — perlakukan sebagai ekstrak, bukan teks penuh.

### `/v2/filings/?symbol=` — 1 kredit

Lebih kaya dari yang terdokumentasi:

```
title · body · source · timestamp · sector · sub_sector · tags · symbol
transaction_type · holder_type · holder_name
holding_before · holding_after · amount_transaction
price · transaction_value · price_transaction
share_percentage_before · share_percentage_after · share_percentage_transaction
idx_investor_slug · idx_conglomerates_group_slug
```

`share_percentage_transaction` dan `idx_conglomerates_group_slug` tidak muncul di deskripsi
endpoint mana pun. Insider yang mengurangi kepemilikan saat harga melonjak adalah sumbu
tersendiri.

### `/v2/free-float/` — 10 kredit untuk seluruh pasar

```json
[{"symbol": "HKMU.JK", "company_name": "...", "free_float": 1.0}]
```

961 baris dalam satu panggilan. **Tidak ada field tanggal** — ini snapshot hari ini. Jangan
dipakai sebagai fitur untuk memprediksi peristiwa masa lalu (lihat §7, kebocoran label).

---

## 3. Arsitektur modul

```
src/
  sectors_client.py     klien berkredit: cache-first, ledger belanja, retry,
                        User-Agent browser (Cloudflare memblokir Python-urllib),
                        RateWindow 25 permintaan berbayar / ~30 detik
  universe.py           watchlist + resolusi simbol; hanya simbol yang pernah muncul
                        di respons sebelumnya (identifier tebakan = 1 kredit hangus)
  axes/
    thinness.py         free_float + market_cap
    concentration.py    broker-summary top, dibobot kohort
    volume_anomaly.py   residual volume vs baseline sendiri
    catalyst.py         news dimension — ketiadaan katalis fundamental
    insider.py          filings — arah transaksi insider
    history.py          suspensi sebelum jendela fitur
  score.py              konvergensi 4+ sumbu → profil, bukan skor tunggal
  labels.py             /v2/suspensions/ → klasifikasi reason → peristiwa bertanggal
  backtest.py           replay historis; wajib lulus tes anti-kebocoran
  agent/
    plan.py             planner sadar anggaran: endpoint mana untuk pertanyaan ini
    adjudicate.py       nilai peringatan terbuka vs peristiwa yang benar-benar terjadi
    lessons.py          tulis lesson terstruktur tiap peringatan selesai
    evolve.py           geser ambang, dengan lima pagar
  render/
    paragraph.py        profil → satu paragraf bahasa Indonesia
    notify.py           kirim ke Telegram
  ledger.py             tulis keempat berkas state
tests/
  test_no_leakage.py    tiap fitur punya tanggal, dan lebih awal dari tanggal peristiwa
  test_broker_sign.py   net_idr negatif untuk penjual; dominansi menjumlahkan
  test_suspended.py     deret nol = disuspensi, bukan sepi
  test_budget.py        tidak ada jalur kode yang memanggil live tanpa cap
state/
  warnings.jsonl  outcomes.jsonl  lessons.jsonl  thresholds.json
```

`sectors_client.py` adalah satu-satunya modul yang boleh menyentuh jaringan. Semua modul lain
menerima data, tidak mengambilnya. Itu yang membuat seluruh sistem bisa diuji tanpa kredit.

---

## 4. Skema empat berkas state

Ini yang akan dibuka juri. Bentuknya penting.

### `warnings.jsonl` — append-only

```json
{"id": "w-20260911-ASLI", "symbol": "ASLI.JK", "date": "2026-09-11",
 "axes": {"thinness": {"value": 0.08, "threshold": 0.15, "fired": true},
          "concentration": {"value": 0.61, "threshold": 0.45, "fired": true},
          "volume_anomaly": {"value": 8.2, "threshold": 3.0, "fired": true},
          "catalyst_absence": {"value": true, "threshold": null, "fired": true},
          "insider": {"value": -0.4, "threshold": -0.2, "fired": false}},
 "axes_fired": 4, "thresholds_version": 7,
 "prediction": "cooling_down_suspension_within_10_trading_days",
 "credits_spent": 10, "status": "open"}
```

### `outcomes.jsonl` — append-only

```json
{"warning_id": "w-20260911-ASLI", "resolved_on": "2026-09-18",
 "outcome": "true_positive", "days_elapsed": 5,
 "evidence": {"source": "/v2/suspensions/", "suspension_date": "2026-09-16",
              "reason_class": "cooling_down",
              "pdf_url": "https://www.idx.co.id/..."}}
```

`outcome` ∈ `true_positive` · `false_positive` · `still_open` · `expired`.
Bukti selalu membawa `pdf_url` kalau ada — itu yang bisa diklik juri.

### `lessons.jsonl` — append-only

```json
{"warning_id": "w-20260911-XXXX", "written_on": "2026-09-21",
 "conditions": "float 11%, konsentrasi 0.52, volume 4.1x, tanpa katalis",
 "expected": "suspensi cooling-down dalam 10 hari",
 "actual": "tidak ada suspensi; volume kembali normal dalam 3 sesi",
 "hypothesis": "konsentrasi 0.52 di bawah ambang yang berarti untuk subsektor ini",
 "axis_implicated": "concentration", "subsector": "Basic Materials"}
```

### `thresholds.json` — menyimpan riwayatnya sendiri

```json
{"version": 7, "updated_on": "2026-09-21",
 "current": {"thinness": 0.15, "concentration": 0.45, "volume_anomaly": 3.0},
 "bounds":  {"concentration": {"floor": 0.30, "ceiling": 0.75}},
 "history": [
   {"version": 7, "date": "2026-09-21", "axis": "concentration",
    "from": 0.42, "to": 0.45, "reason": "6 false positive berturut di bawah 0.45",
    "n_resolved": 23, "holdout_before": 0.31, "holdout_after": 0.38}]}
```

Riwayat di dalam berkasnya sendiri = rollback selalu mungkin, dan tiap perubahan bisa
ditelusuri ke peristiwa yang memicunya.

---

## 5. Empat sumbu

Skor **bukan** rata-rata tertimbang. Profilnya adalah **berapa sumbu yang menyala dan mana**.
Konvergensi lintas pandangan independen adalah argumennya; agregasi ke satu angka justru
membuangnya.

| Sumbu | Rumus | Sumber |
| --- | --- | --- |
| Ketipisan | `free_float < T₁` **dan** `market_cap` di kuintil terbawah | free-float + screener |
| Konsentrasi | `net_dominance = top_buyers[0].net_idr + top_sellers[0].net_idr`, dinormalisasi ke total nilai transaksi; dibobot kalau `cohort == retail` | broker-summary top |
| Anomali volume | residual `volume` hari ini terhadap baseline musiman mingguannya sendiri — **bukan** level | daily |
| Ketiadaan katalis | tidak ada artikel dengan `dimension.financials > 0` atau `dimension.future > 0` dalam 90 hari | news |

Sumbu pendukung: insider (`filings`), riwayat masalah (`suspensions` **sebelum** jendela fitur).

**Normalisasi wajib terhadap subsektor dan rezim pasar.** Lonjakan volume saham batu bara pada
hari harga batu bara melonjak bukan anomali. Tanpa normalisasi, model menyala untuk seluruh
papan saat IHSG bergejolak — dan pada 2026 itu sering.

---

## 6. Loop harian

Jalan **setelah 10:00 WIB** karena `/v2/suspensions/` — sumber label utama — di-refresh jam itu.
Job jam 07:00 menilai peringatan kemarin memakai data yang belum diperbarui.

```
0 4 * * 1-5   # 04:00 UTC = 11:00 WIB, Senin–Jumat
```

```
1. NILAI    ambil warnings status=open; cek /v2/suspensions/ dan /v2/daily/
            → tulis outcomes.jsonl, tandai selesai atau biarkan terbuka
2. PELAJARI tiap outcome baru → tulis lessons.jsonl
3. SETEL    kalau lima pagar terpenuhi → geser ambang, bump version, catat di history
4. SCREEN   jalankan sumbu dengan ambang saat ini → tulis warnings.jsonl
5. KIRIM    peringatan baru ke Telegram
6. CATAT    tulis ledger belanja kredit hari ini
```

Lewati hari libur bursa — kalendernya sudah ada di `harness/src/synth_extended.py`.

**Lima pagar untuk langkah 3** (semuanya harus terpenuhi, semuanya harus terlihat di video):

1. N ≥ 20 peringatan selesai untuk sumbu itu
2. Satu iterasi menggeser ambang ≤ 10% dari nilainya
3. Lantai dan langit-langit absolut yang ditetapkan manusia
4. Periode hold-out yang tidak pernah dipakai menyetel — angka video berasal dari sana
5. Perintah reset ke nilai awal

---

## 7. Tiga tes yang wajib ada di repo

Ini bukan tes untuk kualitas kode. Ini tes yang menjawab pertanyaan juri.

**`test_no_leakage.py`** — tiap fitur membawa tanggal, dan tanggal itu lebih awal dari tanggal
peristiwa. `free_float` tanpa tanggal **dilarang masuk backtest**; penggantinya float yang
direkonstruksi dari `shareholders-composition` bulanan (1 kredit/simbol/tahun, ada sejak 2021).
Tes ini gagal kalau ada fitur tanpa tanggal.

**`test_broker_sign.py`** — memastikan dominansi **menjumlahkan** `top_buyers[0].net_idr` dan
`top_sellers[0].net_idr`, dan menolak implementasi yang menjumlahkan seluruh sisi (selalu
mendekati nol karena pasar zero-sum).

**`test_suspended.py`** — saham dengan seluruh fitur hitung persis nol adalah saham yang
**disuspensi**, bukan sepi. Cek `/v2/suspensions/` sebelum menyimpulkan apa pun.

Tambahan: suspensi tidak boleh jadi fitur **dan** label untuk peristiwa yang sama. Hanya
suspensi sebelum jendela fitur yang boleh menjadi fitur.

---

## 8. Anggaran kredit

Sisa: **~623 dari 1.000**.

| Pos | Kredit | Kapan |
| --- | --- | --- |
| Riwayat suspensi penuh (583 ÷ 20 ≈ 30 halaman) | ~30 | sekali, hari 1 |
| Free float seluruh pasar | 10 | sekali |
| Daftar broker | 1 | sekali, cache permanen |
| Backtest: 40 saham × (daily 1 + broker 2 + news 1 + filings 1) | ~200 | sekali, hari 1–3 |
| Universe demo 30 saham × 10 | ~300 | sekali, prefetch |
| Cadangan run harian + koreksi | ~80 | selama masa bangun |
| **Total** | **~620** | |

Ketat. Maka: **rehearse setiap rencana melawan mock lebih dulu**, dan hapus apa pun yang
ditulis mock ke `recorded/` sebelum panggilan live.

```bash
cd ../research/harness && python3 src/mock_server.py --port 8787 --credits 1000
cd ../research/harness && SECTORS_BASE_URL=http://127.0.0.1:8787 python3 src/capture.py --plan plans/plan.json --budget 300
```

Aturan yang tidak boleh dilanggar: jangan pernah panggil live ad-hoc dengan `curl`; jangan
pernah panggil identifier yang belum pernah muncul di respons (404 menagih 1 kredit); jangan
pernah biarkan `sections`, `classifications`, `periods`, `n_quarters` default.

---

## 9. Jadwal — 9 sampai 30 September

**Prasyarat, hari ini, sebelum apa pun:** semua anggota selesaikan onboarding Sectors, lalu
daftar tim. Tutup 22 September. Tanpa ini, seluruh dokumen ini tidak berarti.

| Hari | Kerjakan | Selesai berarti |
| --- | --- | --- |
| **9 Sep** | Nyalakan scheduler melawan mock, meski logikanya stub | Cron jalan, log bertimestamp mulai menumpuk |
| 10–11 Sep | Tarik 583 suspensi, klasifikasikan `reason`, bangun set label | `labels.py` + tabel: berapa peristiwa cooling-down per bulan |
| 12–14 Sep | `sectors_client.py` + backtest 40 saham + `test_no_leakage.py` | **Angka pertama: apakah sinyal H−5 memprediksi suspensi H.** Kalau tidak, ganti arah sekarang |
| 15–17 Sep | Empat sumbu + `score.py` + dua tes lainnya | Profil satu ticker keluar dari data cache |
| 18–20 Sep | Loop: NILAI → PELAJARI → SETEL, keempat berkas state | Ledger terisi dari run nyata, bukan seed |
| **22 Sep** | **Batas registrasi** | Terdaftar |
| 21–24 Sep | `paragraph.py` + Telegram + permukaan input ticker | Orang lain bisa memakainya tanpa Anda menjelaskan |
| 25–27 Sep | Rekam video, tulis README, disclaimer | Video jadi, bukan draf |
| 28–29 Sep | Cadangan. Bug yang muncul di sini pasti muncul | — |
| **30 Sep** | Submit pagi hari, bukan malam | Terkirim |

Dua hal yang **tidak bisa dikejar di minggu terakhir**: riwayat run scheduler, dan backtest yang
menyelamatkan Anda dari membangun sesuatu yang tidak jalan. Keduanya di awal, sengaja.

---

## 10. Video — tiga menit

| Detik | Isi | Kenapa |
| --- | --- | --- |
| 0–25 | Screenshot grup Telegram berisi tip saham. Lalu: MSCI membekukan Indonesia atas kualitas free float; IHSG −7,35% dalam sehari | Masalahnya nyata, baru, terverifikasi di luar |
| 25–75 | Tempel satu ticker. Paragraf keluar. Sekali saja | Ini produknya. Jangan jelaskan arsitektur di sini |
| 75–140 | **Adegan pemenang:** buka `lessons.jsonl`. "Agen ini salah tanggal 14 September. Ini catatan yang dia tulis. Ini ambang yang dia geser di `thresholds.json` versi 5→6. Ini hasil hold-out sesudahnya." | Tidak ada tim lain punya adegan ini |
| 140–165 | Buka `warnings.jsonl` dan PDF suspensi IDX bersebelahan — peringatan H−5, pengumuman H | Bukti yang bisa diverifikasi juri sendiri |
| 165–180 | Konfigurasi cron + log tiga minggu. Disclaimer di layar | Syarat bukti Track 02 |

Kalau hold-out tidak membaik, **katakan di video**. Temuan negatif yang jujur dinilai lebih
tinggi daripada kurva yang mencurigakan, dan juri yang paham statistik akan tahu bedanya.

---

## 11. Definition of done

Submission dianggap selesai kalau semua ini benar:

- [ ] Semua anggota onboarding Sectors selesai; tim terdaftar sebelum 22 Sep
- [ ] Cabut Sectors → produk mati. Tidak ada sumber data lain
- [ ] Tidak ada eksekusi trade, tidak ada integrasi broker
- [ ] `warnings.jsonl`, `outcomes.jsonl`, `lessons.jsonl`, `thresholds.json` terisi dari run
      nyata, ter-commit, dan bisa dibaca juri
- [ ] Riwayat run scheduler ≥ 14 hari dengan timestamp nyata
- [ ] Tiga tes wajib lulus di CI
- [ ] Ledger belanja kredit ada di repo
- [ ] Backtest dilaporkan apa adanya, termasuk kalau hasilnya lemah
- [ ] Bahasa deskriptif di seluruh output; disclaimer di layar, README, dan video
- [ ] `.env` git-ignored; tidak ada kunci API di mana pun dalam riwayat commit
- [ ] Video ≤ 3 menit, adegan "agen ini salah" ada di dalamnya
