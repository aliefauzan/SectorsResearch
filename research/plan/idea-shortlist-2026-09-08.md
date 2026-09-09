# Daftar Pendek Ide · 8 September 2026

> Lima ide yang muncul dalam sesi, dielaborasi terhadap inventaris endpoint dan aturan
> hackathon, ditambah penilaian TimesFM sebagai lapisan pemodelan. Pendamping
> [`what-we-can-build.md`](what-we-can-build.md), yang merupakan katalog lengkap; berkas ini
> adalah daftar pendek yang benar-benar sedang dipertimbangkan.
>
> Tenggat: **registrasi tutup 22 Sep**, **submission 30 Sep**, keduanya 23:59 WIB. Sisa kredit: **~623 dari 1.000** (log portal: 377 sudah ditagih).

## Cara membaca vonis

Setiap ide dinilai terhadap empat gerbang, dalam urutan yang dilalui juri.

| Gerbang | Pertanyaan | Mode kegagalan |
| --- | --- | --- |
| **Eligibility** | Cabut Sectors — apakah produk berhenti bekerja? | Diskualifikasi, tanpa banding |
| **Bar track** | Apakah lolos bar spesifik track-nya? | Dinilai sebagai re-render atau sekadar prompt |
| **Usability (40%)** | Bisakah pengguna disebut dalam satu kalimat? | Kriteria berbobot tertinggi, hilang |
| **Kedalaman (30%)** | Adakah derivasi yang bisa diverifikasi juri di repo? | Dinilai sebagai dashboard |

Sisanya 30% adalah video dan storytelling, yang merupakan fungsi dari seberapa terbaca output
dalam sembilan puluh detik. Semua vonis di bawah mengasumsikan video tiga menit dan tanpa sesi
langsung.

---

## 0. Koreksi atas rujukan Meridian

Repositori yang ditautkan dalam sesi — `yunus-0x/meridian` — **bukan** proyek intelijen berita.
Itu adalah pengelola likuiditas otonom untuk pool Meteora DLMM di Solana: agen screening tiap
30 menit, agen manajemen tiap 10 menit, loop ReAct di atas OpenRouter, membuka dan menutup
posisi on-chain dengan modal nyata.

Dua konsekuensi.

**Repo itu mengeksekusi trade.** Eksekusi trade otomatis dilarang di semua track hackathon ini.
Arsitekturnya tidak bisa diport apa adanya, dan mengutipnya di video tanpa catatan tersebut
mengundang pertanyaan yang salah dari juri.

**Meridian yang menggarap berita adalah proyek berbeda.** `iliane5/meridian` adalah yang
"personal intelligence agency" — scrape berita, klaster, bikin briefing. Kalau ide 1 terinspirasi
dari produk berita, itu repositori yang perlu dibaca.

Yang **layak** diambil dari `yunus-0x/meridian` justru bagian yang bukan trading: loop ReAct,
*lessons* terstruktur yang ditulis setelah tiap posisi ditutup, dan **threshold evolution** —
agen menyesuaikan parameter screening-nya sendiri berdasarkan win rate yang terealisasi. Yang
terakhir itu orkestrasi buatan sendiri yang sungguhan, dan sudah cukup melewati bar Track 01
kalau diterapkan ke domain tanpa eksekusi (misalnya: screen risiko yang mengetatkan ambangnya
sendiri seiring peringatan masa lalunya diadu dengan pengumuman IDX).

> Rancangan lengkap lapisan itu — sumber label, pagar anti-overfitting, kebocoran label, dan
> anggaran kreditnya — ada di
> [`idea-agen-risiko-belajar-mandiri.md`](idea-agen-risiko-belajar-mandiri.md).

---

## 1. Agen intelijen saham dengan scraping berita berat

**Bentuk.** Agen bergaya Meridian untuk saham IDX yang input utamanya adalah berita hasil
scraping dan faktor eksternal lain.

### Eligibility — di sinilah masalahnya

Aturannya: Sectors MCP atau REST harus menjadi sumber data **inti** — cabut, dan produk harus
berhenti bekerja. Agen yang sinyalnya berasal dari berita hasil scraping gagal tes itu secara
telanjang. Sectors berubah menjadi benda yang menampilkan harga di sebelah headline, yang
artinya dekorasi.

### Scraping-nya juga mubazir

`/v2/news/` berharga **1 kredit** dan sudah mengembalikan, per baris:

`title` · `body` · `source` · `thumbnail` · `timestamp` · `sector` · `sub_sector` · `tags` ·
`symbols` · `dimension`

`dimension` adalah bagian yang penting dan tidak terdokumentasi di mana pun: objek berskor di
delapan tema analitis.

```json
{"future": 0, "dividend": 0, "ownership": 0, "technical": 0,
 "valuation": 0, "financials": 0, "management": 0, "sustainability": 0}
```

Setiap artikel sudah diklasifikasi berdasarkan *jenis beritanya*. Filter yang tersedia:
`symbols`, `sector`, `sub_sector`, `tags`, `keyword`, `start`, `end`, `extension=idx|mining`,
`limit` maksimum 30. Jadi "pipeline berita" yang dibangun di atas scraping menghabiskan
berminggu-minggu membangun ulang klasifikator yang sudah gratis, sekaligus merusak tes
eligibility untuk melakukannya.

Catatan yang perlu dicek di data live: `body` pada contoh resmi panjangnya sekitar 500 karakter.
Perlakukan sebagai ekstrak sepanjang ringkasan, bukan teks penuh yang dijamin, sebelum
membangun summarizer di atasnya.

### Posisi kompetitif

Supertype sudah menerbitkan chatbot saham berbahasa alami dan analis tiga-agen-spesialis.
Sectors sendiri mengirimkan **Sectors Workflow**, builder if-this-then-that dengan ~60 template
dan pengiriman WhatsApp / Email / Slack / Telegram / Sheets. Agen berbasis berita mendarat di
tengah keduanya. Lihat [`already-published.md`](already-published.md) dan
[`competitive-landscape.md`](competitive-landscape.md).

### Kalau tetap mau hidup, bentuknya begini

Balik ketergantungannya. Data Sectors menghasilkan sinyal; berita menjelaskannya.

> Mesin peringkat di atas broker flow, perubahan kepemilikan, dan financials, di mana skor
> `dimension` dari `/v2/news/` dipakai untuk menjawab *apakah ada alasan fundamental di balik
> pergerakan ini, atau tidak?* Scraping menjadi lapisan pengaya opsional yang bisa dimatikan
> tanpa mematikan produk.

Pembalikan itu persisnya adalah ide 4, dan karena itulah ide 4 diperingkat di atas ide ini.

**Vonis: jangan dibangun sebagaimana dirumuskan.** Risiko eligibility tidak sepadan untuk
dipikul, dan pekerjaannya menduplikasi field yang sudah gratis. Lipat separuh yang berguna ke
ide 4.

---

## 2. Automated Earnings-to-Social Evidence Pack

**Bentuk.** Ketika sebuah emiten merilis laporan, sistem otomatis merakit paket bukti yang siap
dibagikan — angka yang bergerak, segmen di baliknya, konteksnya — diformat untuk distribusi
sosial.

### Kenapa lolos Track 02

Bar-nya adalah operasi otonom pada jadwal atau trigger, ditambah **bukti di video**: konfigurasi
scheduler dan log bertimestamp dari run yang berjalan tanpa ditunggui.

Endpoint trigger-nya adalah argumen terkuat untuk ide ini:

```
GET /v2/companies/quarterly-financial-dates/?since=<last-seen>
```

Endpoint ini hanya mengembalikan emiten yang melapor sejak polling terakhir. Sweep seluruh
universe ~32 kredit; polling inkremental hanya sebagian kecilnya. Endpoint ini ada
*khusus* untuk polling kesegaran yang murah, dan memakainya dengan benar adalah jenis detail
yang ditanyakan kriteria kedalaman teknis.

### Pipeline dan biaya

| Langkah | Panggilan | Kredit |
| --- | --- | --- |
| Deteksi laporan baru | `/v2/companies/quarterly-financial-dates/?since=` | ~1 per polling |
| Tarik angkanya | `/v2/financials/quarterly/{symbol}/?n_quarters=4` | 4 (1 per kuartal) |
| Konteks peer | `/v2/company/report/{symbol}/?sections=peers` | 1 |
| Cerita segmen | `/v2/company/get-segments/{symbol}/` | 1 |
| Headline + gambar | `/v2/news/?symbols={symbol}&limit=5` | 1 |

Kira-kira **8 kredit per emiten yang melapor**, dan pelaporan itu bursty — menumpuk pada
minggu-minggu setelah tiap tutup kuartal, sehingga scheduler murah di sebagian besar hari dan
mahal selama dua pekan. Anggarkan dari puncaknya, bukan dari rata-ratanya.

`thumbnail` pada baris berita adalah URL gambar CDN: poles visual gratis untuk kartu sosial,
yang menolong skor video 30% tanpa usaha.

### Dua jebakan

**Nama field bergantung sektor.** `/v2/financials/quarterly/{symbol}/` mengembalikan
`realized_capital_goods_investment` untuk bank — nama yang ditampilkan contoh spec — dan
`capital_expenditure` di slot yang sama untuk selain bank. `financials_sector_metrics` terisi
untuk bank dan berupa objek kosong untuk lainnya. Parser yang ditulis berdasarkan contoh
dokumentasi akan menangani bank dan **diam-diam membuang capex seluruh pasar non-bank**. Baca
kedua kunci. Ini dikonfirmasi live pada 6 Sep; lihat
[`../audit/VERIFICATION-LIVE.md`](../audit/VERIFICATION-LIVE.md).

**Parameter yang dibiarkan default.** Jangan pernah biarkan `n_quarters` atau `sections`
default. Company report yang default berharga 8 kredit, bukan 1; quarterly financials menagih
1 per kuartal yang dikembalikan.

### Risiko posisi

Ini akan terbaca sebagai alat content marketing kecuali penggunanya disebut dengan tepat.
"Generator konten media sosial" bernilai buruk terhadap kriteria usability dunia nyata yang
berbobot 40%. "Tim IR di emiten mid-cap yang saat ini membangun ulang grafik earnings yang sama
dengan tangan tiap kuartal" bernilai bagus. Produk sama, kalimat pembuka berbeda.

Catat juga bahwa mempublikasikan ke akun sosial adalah aksi keluar. Bangun paketnya; sisakan
tindakan posting di balik konfirmasi eksplisit, bukan tembak otomatis.

**Vonis: layak, murah, aman.** Melewati bar Track 02 dengan bersih dan syarat buktinya gratis
kalau scheduler dinyalakan sekarang. Diferensiasinya sedang — endpoint trigger adalah bagian
yang khas, jadi tampilkan ia dengan jelas.

---

## 3. Free-Float Transition Stress Test

**Bentuk.** Emiten mana yang terpapar bila ambang minimum free float dinaikkan — kabarnya
menuju 15% — dan apa yang terjadi pada mereka ketika itu berlaku.

### Pertama, verifikasi premisnya

Angka 15% **belum diverifikasi terhadap regulasi IDX** di repositori ini. Sebelum ini muncul di
pitch, temukan aturannya, tanggal berlakunya, dan masa transisinya di dokumen IDX atau OJK, lalu
kutip di layar. Produk regulatorik yang regulasinya salah gugur di tiga puluh detik pertama
penjurian.

### Batasan data yang membentuk seluruh ide ini

`/v2/free-float/` mengembalikan **array telanjang** berisi `symbol`, `company_name`,
`free_float`. Tidak ada field tanggal. Ini snapshot, bukan deret — jadi "transisi sepanjang
waktu" tidak bisa datang dari endpoint ini. Biayanya 1 kredit per 100 perusahaan yang
dikembalikan, jadi ~10 kredit untuk seluruh pasar, dan parameter filternya (`sector`,
`sub_sector`, `industry`, `sub_industry`) **saling eksklusif** — paling banyak satu per request.

`free_float` juga merupakan turunan: nilainya adalah `share_percentage` dari entri **Public** di
daftar pemegang saham utama perusahaan, dinyatakan sebagai desimal (0,45 = 45%).

### Di mana historinya sebenarnya berada

`/v2/company/shareholders-composition/{symbol}/` — **1 kredit per simbol per tahun**, baris
bulanan, **data tersedia sejak 2021**. Tiap baris membawa setiap kategori investor dua kali,
lokal (`_l`) dan asing (`_f`):

`insurance` · `corporate` · `pension_fund` · `financial_institutions` · `individual` ·
`mutual_fund` · `securities_companies` · `foundation` · `other` · `total`

…ditambah `date`, `shares_number`, `numbers_of_shareholders`, `change_in_shareholders`.

Itulah dimensi waktu yang tidak dimiliki endpoint free float. Tambahkan
`/v2/company/report/{symbol}/?sections=ownership` (1 kredit) untuk `major_shareholders` beserta
`share_percentage`, dan `/v2/company/corporate-actions/{symbol}/` (1 kredit) untuk enam jenis
aksi korporasi yang benar-benar menggeser float — `right_issue`, `warrant`, `bonus`,
`stock_split`, plus `agm_result` berupa teks bebas hasil keputusan rapat.

Biaya untuk daftar pendek 40 nama yang terpapar: ~10 (sweep float pasar) + 40 (komposisi, tahun
berjalan) + 40 (ownership) + 40 (corporate actions) ≈ **130 kredit**. Terjangkau, tapi tidak
sepele terhadap sisa 623.

### Masalah tumpang tindih

Kriteria 6 dari rulebook Papan Pemantauan Khusus adalah *free float di bawah lantai I-A / I-V*.
Kriteria itu sudah menjadi salah satu dari tujuh kriteria yang bisa dihitung di
[`idea-ppk-early-warning.md`](idea-ppk-early-warning.md) — yang di atasnya masih punya: sebelas
kriteria terpublikasi, ground truth yang falsifiable (IDX mengumumkan entri dan keluar, jadi
peringatan bisa di-backtest), 172 saham terdampak per Januari 2026, dan nol prior art di GitHub.

Produk free float yang berdiri sendiri adalah satu kriteria dari semua itu, tanpa ground
truth-nya.

**Vonis: lipat ke ide PPK early warning sebagai modul float-nya.** Sebagai produk mandiri ia
tipis; sebagai sumbu float dari prediktor papan pemantauan — dengan corporate actions sebagai
bagian yang menatap ke depan, karena rights issue mengubah float pada tanggal yang sudah
diketahui — ia kuat. Verifikasi aturan 15% bagaimanapun juga.

---

## 4. Pemeriksa risiko pump-and-dump untuk tip saham dari media sosial

**Bentuk.** Seorang investor ritel diberi satu ticker oleh grup Telegram, unggahan X, atau video
YouTube. Sebelum bertindak, ia memeriksanya di sini dan mendapat deskripsi terstruktur tentang
apa yang membuat saham itu rapuh — float tipis, aktivitas broker terkonsentrasi, volume anomali,
tanpa katalis fundamental.

### Penggunanya, dalam satu kalimat

> Investor ritel Indonesia yang menerima tip saham di grup chat dan tidak punya cara untuk
> membedakan pergerakan yang nyata dari yang direkayasa.

Itu kalimat pembuka terkuat dari kelimanya, terhadap kriteria yang berbobot 40%.

### Semua inputnya ada, dan murah

| Sumbu kerapuhan | Endpoint | Kredit | Field |
| --- | --- | --- | --- |
| Float tipis | `/v2/free-float/` | 1 / 100 perusahaan | `free_float` (desimal) |
| Kecil dan tidak likuid | `/v2/companies/` terstruktur | 1 | `market_cap`, plus 219 field yang bisa difilter |
| Konsentrasi broker | `/v2/broker-summary/{symbol}/top/` | **2** | `rank`, `broker_code`, `net_idr`, `buy_idr`, `sell_idr` |
| Siapa broker itu | `/v2/brokers/` | 1, cache selamanya | `origin` (foreign/domestic), `cohort` (retail/mixed/institutional/unknown) |
| Anomali volume | `/v2/daily/{symbol}/` | 1 | OHLC penuh + `volume` + `market_cap`, ≤90 hari |
| Asing vs domestik | `/v2/foreign-flow/{symbol}/` | 1 | `net_foreign_inflow`, ≤90 hari |
| Riwayat masalah | `/v2/suspensions/?symbol=` | 1 | `suspension_date`, `reason`, `pdf_url` |
| Ada katalisnya? | `/v2/news/?symbols=` | 1 | `dimension` — 8 tema berskor |
| Perilaku insider | `/v2/filings/?symbol=` | 1 | `holder_name`, `holding_before`, `transaction_type` |

**~10 kredit untuk profil lengkap satu ticker.** Universe demo 30 nama ~300 kredit, bisa
di-prefetch sekali, di-cache, dan diputar ulang di video.

`/v2/broker-summary/{symbol}/top/` menerima parameter `cohort` dan `origin` secara langsung,
sehingga "broker ritel mendominasi sisi beli sementara institusi mendistribusi" adalah satu
panggilan, bukan sebuah join.

### Derivasinya

Empat sumbu independen, lalu konvergensi. Panduan dosir ini sendiri menyatakan bahwa konfirmasi
lintas pandangan independen adalah yang membuat sebuah sinyal bisa dipertahankan di bawah
kriteria 30% — dan broker flow, foreign flow, komposisi pemegang saham, serta filing insider
adalah empat pandangan yang sungguh-sungguh independen atas pertanyaan yang sama.

1. **Ketipisan** — `free_float` rendah, `market_cap` kecil. Mudah digerakkan.
2. **Konsentrasi** — dominansi di antara broker teratas, dibobot menurut kohort. Konsentrasi
   yang berat di sisi ritel pada nama yang tipis adalah pola yang dicari.
3. **Anomali volume** — `volume` hari ini terhadap baseline-nya sendiri. Residualnya, bukan
   levelnya.
4. **Ketiadaan katalis** — `/v2/news/` tidak mengembalikan apa pun, atau hanya mengembalikan
   liputan berdimensi `technical` dengan `financials` dan `future` bernilai nol. Pergerakan
   harga tanpa berita fundamental di belakangnya adalah kasus definisionalnya.

Outputnya sebuah kalimat, bukan dashboard:

> *ABCD diperdagangkan dengan float 12%, satu broker ritel mengambil 61% dari net beli selama
> lima sesi, volumenya 8× median 30 harinya, dan tidak ada berita berdimensi financials maupun
> future dalam 90 hari.*

### Jebakan yang mematahkan setiap proyek bandarmology

Jangan menjumlahkan net pembeli dengan net penjual. Pasar saham itu zero-sum — untuk tiap
pembeli ada penjual — sehingga sepuluh teratas dari masing-masing sisi saling meniadakan dan
sinyalnya terbaca datar apa pun yang sedang terjadi.

```python
# SALAH: selalu mendekati nol
total = sum(b["net_idr"] for b in buyers) + sum(s["net_idr"] for s in sellers)

# BENAR: skor dominansi
top_buy_net  = buyers[0].get("net_idr", 0)    # positif: net beli
top_sell_net = sellers[0].get("net_idr", 0)   # negatif: API sudah mengembalikannya negatif
net_dominance = top_buy_net + top_sell_net    # positif = akumulasi dominan
```

`net_idr` **sudah negatif** untuk penjual, jadi skor dominansi menjumlahkan, bukan mengurangi.
Salah tanda membalik seluruh produk. Uraian lengkapnya di
[`../docs/api/10-domain-pitfalls.md`](../docs/api/10-domain-pitfalls.md).

Jebakan kedua dari halaman yang sama: saham yang seluruh fitur hitungnya persis nol adalah saham
yang **disuspensi**, bukan saham yang sedang sepi. Cek `/v2/suspensions/` sebelum menyimpulkan
apa pun tentang deret yang datar.

### Framing — bagian yang menentukan apakah ini bisa dikirim

"Pre-trade firewall" adalah nama yang bagus untuk video dan buruk untuk tinjauan kepatuhan.
Code of conduct melarang saran investasi yang dipersonalisasi, dan alat yang berkata *jangan
beli ini* persis merupakan hal itu.

Seluruh produk harus **deskriptif**: inilah yang ditunjukkan datanya, inilah mengapa kombinasi
itu secara historis rapuh, Anda yang memutuskan. Jangan pernah mengeluarkan vonis, skor yang
disajikan sebagai rekomendasi, atau sinyal beli merah/hijau. Disclaimer di layar, di README, dan
di video. Biayanya satu baris dan ia melindungi seluruh submission.

Juga: jangan scrape grup sinyalnya. Pengguna yang menempelkan ticker-nya. Itu menjaga Sectors
sebagai satu-satunya sumber data, menjaga tes eligibility tetap bersih, dan menghindari
mengumpulkan pesan orang lain.

### Penempatan track

Track 03 sebagai screen berskor. Atau Track 02 kalau dijalankan terjadwal di atas sebuah
watchlist dan memberi peringatan pada transisi — saat *memasuki* keadaan rapuh, bukan sekadar
sedang berada di dalamnya — yang merupakan trigger jauh lebih bisa dipertahankan daripada
sekadar query ulang. Track 02 juga lapangan yang paling kosong: dari 48 tim publik pada hitung
ulang 5 September, 15 memilih Track 01, 12 memilih Track 03, dan 7 memilih Track 02. Bacaan 4
September (44 tim; 16-11-4) sudah tidak berlaku — Track 02 masih paling kosong, tetapi
selisihnya separuh dari yang tampak semula. Lihat `competitive-landscape.md`.

**Vonis: terkuat dari kelimanya.** Pengguna bisa disebut, data unik, derivasi bisa
dipertahankan, murah, dan outputnya menjelaskan dirinya sendiri dalam satu kalimat.

---

## 5. Berinvestasi tanpa penglihatan — riset saham yang mengutamakan screen reader

**Bentuk.** Investor tunanetra atau low-vision tidak bisa membaca grafik candlestick, diagram
Sankey segmen, atau laporan keuangan yang disusun sebagai gambar tabel. Semua yang dikembalikan
Sectors berupa JSON, yang berarti bisa dirender sebagai bahasa terucap yang terstruktur dan bisa
dinavigasi.

### Kenapa ini bernilai tinggi

Kriteria 40% adalah usability dunia nyata, dan ini jawaban paling jernih atas pertanyaan *ini
masalah siapa*. Dari 48 tim publik (hitung ulang 5 September), kemungkinan ada tim kedua yang membangun untuk pengguna ini
sangat kecil. Ini juga kategori di mana demonya berjalan sendiri: rekam video **dengan screen
reader menyala**, dan buktinya adalah produk yang bekerja, bukan klaim tentangnya.

### Yang harus benar-benar nyata

Di sinilah risikonya. Produk yang aksesibel bukanlah produk biasa yang ditempeli alt text, dan
juri yang memakai teknologi bantu akan tahu dalam hitungan detik.

- **WCAG 2.2 AA**, diperiksa, bukan diklaim.
- HTML semantik dengan hierarki heading yang nyata — pengguna screen reader bernavigasi lewat
  heading, bukan dengan menggulir.
- Region `aria-live` untuk apa pun yang berubah tanpa memuat ulang halaman.
- Urutan fokus yang dikelola; setiap interaksi bisa dicapai hanya dengan keyboard.
- Tabel data dengan `<th>`, `scope`, dan caption yang benar — bukan grid `<div>`.
- Angka yang diucapkan dengan berguna: "satu koma dua triliun rupiah", bukan "1200000000000".
- **Sonifikasi** deret harga dan aliran dana — pitch dipetakan ke nilai sepanjang waktu —
  sehingga tren bisa dicerap tanpa grafik. Inilah bagian yang mengubah proyek ini dari sekadar
  pembungkus yang aksesibel menjadi sesuatu yang punya gagasan teknis sendiri.

### Datanya memetakan dengan sangat cocok

| Biasanya visual | Endpoint | Bentuk terucap |
| --- | --- | --- |
| Diagram Sankey pendapatan | `/v2/company/get-segments/{symbol}/` (1) | "Tiga perempat pendapatan berasal dari satu segmen, dan porsinya naik tiga tahun berturut-turut" |
| Scatter plot peer | `?sections=peers` (1) | Seluruh peer set beserta financials dalam satu kredit, diperingkat dan dibacakan |
| Pie kepemilikan | `?sections=ownership` (1) | `major_shareholders`, `whale_investors`, `conglomerates_group` sebagai kalimat |
| Grafik candlestick | `/v2/daily/{symbol}/` (1) | OHLC penuh — ringkas, lalu sonifikasi |
| Area bertumpuk komposisi | `shareholders-composition` (1/tahun) | "Dana pensiun asing membeli empat bulan berturut-turut sementara individu domestik menjual" |

`?sections=peers` adalah yang paling menonjol: **satu kredit membeli seluruh peer set beserta
financials**, termasuk `point_summaries` (penilaian berskor milik Sectors sendiri) dan baris
`revenue_breakdown` / `operating_expense_breakdown`. Mengambil laporan tiap peer secara terpisah
berbiaya N kredit untuk data yang lebih sedikit.

### Dari mana kedalaman teknisnya datang

Alat yang sekadar membacakan teks akan dibaca tipis terhadap kriteria 30%. Dua tambahan
memperbaikinya, dan keduanya sudah terkatalog:

- **Verifikasi angka yang fail-closed** — asisten tidak boleh menyebut angka yang tidak ia
  ambil; tiap figur membawa sitasi ke endpoint dan field, dan pemeriksa pasca-generasi menolak
  angka tanpa sumber lalu memaksa pengambilan ulang. Angka keuangan yang dihalusinasikan adalah
  *keberatan utama* terhadap LLM di bidang keuangan, dan demo di mana asisten menolak menjawab
  sampai ia punya angkanya itu berkesan dan jujur.
- **Sonifikasi**, seperti di atas.

### Penempatan track

Track 01 kalau orkestrasinya nyata — planner yang memutuskan section dan kuartal mana yang perlu
diambil, eksekutor yang sadar anggaran, dan verifikator. Bersebelahan dengan ide 1.4 di
[`what-we-can-build.md`](what-we-can-build.md) (penjelas ritel bilingual), tetapi dengan
pengguna yang berbeda dan jauh lebih tajam. Bahasa Indonesia diterima secara eksplisit tanpa
penalti penilaian.

**Vonis: plafon storytelling tertinggi; lapisan kedalamannya harus dibangun, bukan dijanjikan.**

---

## Lintas ide: 4 + 5 bisa digabung

Ide 4 dan 5 adalah pipeline yang sama dengan permukaan output berbeda. Profil kerapuhan dihitung
sekali; satu produk merendernya sebagai kartu, satunya mengucapkannya. Kalau tim menginginkan
satu submission yang membawa sekaligus cerita usability dan data yang terdiferensiasi, inilah
penggabungannya:

> Pemeriksa risiko tip saham yang bisa didengar dan mengutamakan screen reader — untuk investor
> yang tidak bisa membaca grafik yang ditunjukkan ke semua orang lain.

Satu kalimat itu membawa pengguna yang bernama, kebutuhan yang belum terpenuhi, sumber data yang
tidak dipakai orang lain, dan demo yang jelas dalam sembilan puluh detik.

---

## Lampiran · TimesFM sebagai lapisan pemodelan

Sumber: [`google-research/timesfm`](https://github.com/google-research/timesfm).

### Apa itu

Model fondasi deret waktu decoder-only dari Google Research, dipublikasikan di ICML 2024.

| Versi | Parameter | Catatan |
| --- | --- | --- |
| 3.0 | 200M | Multivariat native; kovariat dinamis masa lalu **dan** masa depan |
| 2.5 | 200M | Quantile head 30M opsional; konteks hingga 16k, horizon hingga 1k; kovariat lewat XReg |
| 2.0 | 500M | Diarsipkan di bawah `v1/` |

Instalasi: `pip install timesfm[torch]`.

### Lisensi — baca ini sebelum memilih versi

Kode sumbernya Apache-2.0. **Bobot TimesFM 3.0 tidak**: bobot itu memakai
`timesfm-non-commercial-license-v1.0`, membatasi penggunaan ke aplikasi non-komersial dan
**non-produksi**. Bobot versi 2.5 ke bawah tetap Apache-2.0.

Submission hackathon dengan video publik dan repositori publik, paling baik pun, ambigu di bawah
kata "non-produksi". **Pakai 2.5.** Selisih kemampuannya tidak sepadan dengan pertanyaan lisensi
itu, dan juri yang memeriksa sedang memeriksa sesuatu yang tak bisa diperbaiki setelah
submission.

### Jangan memakainya untuk meramal harga

Return saham harian mendekati random walk. Model fondasi zero-shot tidak akan mengalahkan
baseline naif dalam arah, dan tiga hal salah sekaligus:

1. Angkanya jelek.
2. Ramalan harga yang disajikan ke pengguna secara fungsional adalah saran investasi — dilarang.
3. Juri membaca model besar yang dibautkan ke target random-walk sebagai gimmick, yang merusak
   skor kedalaman teknis alih-alih menolongnya.

### Pakai untuk deteksi anomali

Ramalkan deretnya, lalu perlakukan **residualnya** sebagai sinyal. Residual besar berarti deret
itu tidak berperilaku seperti dirinya sendiri — yang merupakan deskripsi, bukan prediksi, dan
karenanya lebih bisa dipertahankan secara statistik sekaligus lebih aman di bawah code of
conduct.

Deret yang punya struktur nyata untuk dimodelkan:

| Deret | Endpoint | Kenapa berstruktur |
| --- | --- | --- |
| Volume harian | `/v2/daily/{symbol}/` | Musiman mingguan dan event yang kuat — baseline yang menggerakkan ide 4 |
| Net foreign inflow | `/v2/foreign-flow/{symbol}/` | Rezim aliran dana yang persisten |
| Kepemilikan bulanan | `shareholders-composition` | Panel yang bergerak lambat, bulanan sejak 2021 |
| Harga komoditas | `/v2/mining/commodities/{name}/price/` | Tren dan siklus yang sungguhan |
| Total kapitalisasi pasar | `/v2/idx-total/` | Level indeks, ≤90 hari per panggilan, sejak 2021 |

### Dua batasan operasional

**Jangan taruh di harness.** `research/harness/` sengaja hanya memakai standard library — tanpa
venv, tanpa pip, tanpa build step. TimesFM masuk ke kode produk. Jaga harness tetap bersih.

**Ia harus membuktikan diri terhadap baseline.** Sebelum berkomitmen pada dependensi
200 juta parameter, benchmark TimesFM 2.5 melawan rolling z-score, EWMA, dan dekomposisi STL di
universe sintetis — yang berbiaya **nol kredit**:

```bash
cd research/harness && python3 src/synth_universe.py --companies 300 --days 180
```

Kalau TimesFM tidak menang dengan jelas, ia adalah beban tanpa manfaat dan baseline adalah
keputusan rekayasa yang lebih baik. Kalau ia menang, **taruh tabel perbandingannya di video** —
hasil yang terukur adalah kedalaman teknis yang bisa diverifikasi juri, sedangkan nama model di
sebuah slide tidak.

---

## Peringkat

| Peringkat | Ide | Track | Alasan |
| --- | --- | --- | --- |
| 1 | **Pemeriksa risiko pump-and-dump** | 03, atau 02 terjadwal | Pengguna bisa disebut, data unik, derivasi bisa dipertahankan, ~10 kredit per ticker |
| 2 | **Riset yang mengutamakan screen reader** | 01 | Plafon storytelling tertinggi; menyatu dengan #1 |
| 3 | **Earnings evidence pack** | 02 | Termurah dan teraman; diferensiasi sedang |
| 4 | **Free-float stress test** | — | Lipat ke `idea-ppk-early-warning.md`; verifikasi aturan 15% |
| 5 | **Agen scraping berita** | — | Risiko eligibility; menduplikasi `dimension`, yang sudah gratis |

TimesFM: versi 2.5, untuk residual anomali, hanya setelah ia mengalahkan baseline murah pada
data sintetis.

## Langkah berikutnya

1. **Verifikasi aturan free float 15%** terhadap dokumen primer IDX atau OJK, atau buang.
2. **Nyalakan scheduler Track 02 sekarang**, melawan mock, ide mana pun yang menang — tiga
   minggu log run tanpa ditunggui adalah bukti yang tidak bisa dikarang belakangan, dan biayanya
   nol:

   ```bash
   cd research/harness && python3 src/mock_server.py --port 8787 --credits 1000
   ```

3. **Latih rencana pengambilan data melawan mock** sebelum panggilan live apa pun:

   ```bash
   cd research/harness && SECTORS_BASE_URL=http://127.0.0.1:8787 python3 src/capture.py --plan plans/plan.json --budget 300
   ```

4. **Benchmark TimesFM 2.5 melawan z-score/EWMA/STL** di `synth/` — nol kredit, dan itu
   menyelesaikan pertanyaan pemodelan sebelum ada kode yang bergantung pada jawabannya.
5. **Daftar sebelum 22 September.** Tanpa itu, semua di atas tidak berarti.
