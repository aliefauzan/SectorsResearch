# Meridian untuk Saham IDX — Riset Mendalam

> Dibuat 9 September 2026. Menjawab tiga pertanyaan: (1) apa sebenarnya yang dinilai lomba ini,
> (2) bagaimana arsitektur bergaya Meridian dipindahkan dari kripto ke saham IDX — dan faktor apa
> saja yang sebenarnya menggerakkan saham, (3) pandangan dari kursi juri.
>
> Pendamping: [`ringkas.md`](ringkas.md). Prasyarat baca:
> [`../../research/plan/idea-shortlist-2026-09-08.md`](../../research/plan/idea-shortlist-2026-09-08.md) dan
> [`../../research/plan/pump-and-dump/agen-risiko-belajar-mandiri.md`](../../research/plan/pump-and-dump/agen-risiko-belajar-mandiri.md),
> yang sudah memuat rancangan loop belajarnya. Dokumen ini tidak mengulangnya — ia mengisi
> lapisan domain yang belum ada: **fisika pasar saham**, dan konsekuensinya bagi desain agen.

---

## Vonis di depan

1. **Meridian tidak bisa diport apa adanya.** Bukan karena kodenya sulit, tapi karena mesin
   belajarnya bergantung pada dua hal yang tidak ada di saham: eksekusi trade (dilarang di semua
   track) dan umpan balik PnL dalam hitungan jam (di saham, jamnya diganti minggu).
2. **Sinyal berbasis scraping berita gagal tes eligibility**, dan sekaligus membangun ulang
   sesuatu yang sudah gratis di `/v2/news/` (`dimension`, 8 tema berskor per artikel).
3. **Yang layak diambil dari Meridian justru bagian yang bukan trading**: loop ReAct dengan
   peran terpisah, decision log terstruktur, lessons pasca-peristiwa, dan threshold evolution.
   Empat hal itu persis yang disebut bar Track 01 sebagai "orkestrasi buatan sendiri".
4. **Yang harus diganti adalah sinyal reward-nya.** Di DLMM: fee terkumpul dan PnL posisi. Di
   saham IDX: **peristiwa bertanggal yang diumumkan bursa** — suspensi, masuk Papan Pemantauan
   Khusus, UMA, notasi khusus, delisting. Itu ground truth yang jujur dan bisa di-backtest.
5. **Dua temuan baru per hari ini yang mengubah dua ide di dosir** — lihat Bagian 6. Revisi
   aturan PPK yang ditarget Q3 2026 mengusulkan menghapus kriteria 6, 7, dan 10; tiga dari tujuh
   kriteria yang bisa dihitung di [`../../research/plan/idea-ppk-early-warning.md`](../../research/plan/idea-ppk-early-warning.md).

---

## Bagian 1 · Apa yang sebenarnya dinilai lomba ini

Detail lengkap ada di [`../../research/docs/hackathon/`](../../research/docs/hackathon/). Yang penting untuk
keputusan desain hanya lima kalimat.

**Satu kalimat brief-nya:** *"Solve an interesting problem thoughtfully with Sectors API."*
Aturannya menyatakan secara eksplisit bahwa kecanggihan kode bukan yang dinilai.

**Satu batasan keras:** Sectors MCP atau REST harus menjadi sumber data **inti** — tesnya,
cabut Sectors dan produk harus kehilangan fungsi intinya. Eksekusi trade otomatis dilarang di
seluruh track.

**Bobot penilaian:**

| Kriteria | Bobot | Yang sebenarnya diukur |
| --- | --- | --- |
| Real-world usability | 40% | Bisakah penggunanya disebut dalam satu kalimat |
| Video & storytelling | 30% | Apakah masalahnya terbaca dalam tiga menit tanpa Anda hadir |
| Technical depth | 30% | Diverifikasi dari repo — inovasi pemakaian API, bukan tumpukan framework |

**70% adalah perumusan masalah dan komunikasi.** Penjurian asinkron 1–8 Oktober, tanpa sesi
langsung. Video dan repo memikul seluruh argumen sendirian.

**Tiga track, dibedakan oleh apa yang memutuskan langkah berikutnya:**

| Yang memutuskan | Track | Bar-nya |
| --- | --- | --- |
| Model | 01 · Reason | Orkestrasi buatan sendiri. *"Kalau produknya hilang begitu prompt tim dicabut dari klien orang lain, ia tidak lolos."* |
| Jam / trigger | 02 · Act | Berjalan tanpa ditunggui, **dibuktikan dengan log bertimestamp di video** |
| Rumus / model | 03 · Reveal | Insight turunan, bukan render ulang data |

Konteks lapangan: dari 48 tim publik (hitung ulang 5 Sep), 15 Track 01, 12 Track 03, 7 Track 02,
14 belum memilih. Slack melaporkan 105 anggota, jadi papan itu batas bawah. **Track 01 paling
ramai sekaligus punya tes diskualifikasi paling ketat** — juri akan sudah terkalibrasi pada
belasan proyek "klien AI + MCP" sebelum sampai ke milik Anda.

Dan yang paling sering dilewatkan: **proyek paling obvious di tiap track sudah diterbitkan
sebagai tutorial resmi oleh Supertype**, organisasi yang menjurinya. Termasuk **FinArena**
(Juni 2026) — agen Fundamental + Teknikal + Berita + sintesis, berjalan paralel, dengan
personalisasi profil risiko. Kalau pitch Track 01 Anda adalah "beberapa agen spesialis
mensintesis sinyal fundamental, teknikal, dan berita" — itu resep mereka.
Lihat [`../../research/plan/already-published.md`](../../research/plan/already-published.md).

---

## Bagian 2 · Dua Meridian, dan kenapa perbedaannya menentukan

Nama yang sama dipakai dua proyek berbeda. Keduanya relevan, dengan cara berlawanan.

### `yunus-0x/meridian` — agen likuiditas otonom (yang Anda tautkan)

Bukan proyek berita. Ia pengelola likuiditas otonom untuk pool **Meteora DLMM di Solana**.

| Komponen | Detail |
| --- | --- |
| Screening agent | tiap 30 menit — memindai pool terhadap ambang: fee/TVL ≥ 0,05; TVL $10k–150k; organic score ≥ 60; holder ≥ 500; bin step 80–125 |
| Management agent | tiap 10 menit — stop loss −15%, take profit 5% dari modal, trailing TP 1,5%, alert out-of-range 30 menit |
| Loop | ReAct: muat state → suntik memori → ekspos tool sesuai peran → eksekusi → laporan keputusan |
| Memori | `decision-log.json`, `pool-memory.js`, `strategy-library.js` |
| Belajar | `lessons.js` — `studyTopLPers` menganalisis perilaku LP teratas; `/evolve` menggeser ambang setelah 5+ posisi tertutup |
| HiveMind | `hivemind.js` — sinkronisasi pelajaran antar-instance lewat API pusat |
| Stack | Node 18+, OpenRouter, Solana RPC, PM2, Telegram |

**Ia membuka dan menutup posisi on-chain dengan modal nyata.** Itu eksekusi trade otomatis —
dilarang di ketiga track. Mengutipnya di video tanpa catatan ini mengundang pertanyaan yang
salah dari juri.

### `iliane5/meridian` — "personal intelligence agency" (yang berita)

Ini yang sesuai dengan bayangan "Meridian yang heavy scraping berita".

Pipeline: Cloudflare Workers memanen RSS harian → ekstraksi teks dengan fallback render browser
untuk paywall → Gemini menilai relevansi dan struktur tiap artikel → embedding
`multilingual-e5-small` + **UMAP + HDBSCAN** untuk klasterisasi → LLM menelaah tiap klaster →
sintesis brief markdown yang membawa kontinuitas dari brief hari sebelumnya → Nuxt 3 di
Cloudflare Pages. Stack: Turborepo, Hono, PostgreSQL, Drizzle.

Yang layak dicuri dari sini: **klasterisasi sebelum sintesis** (bukan ringkas per artikel), dan
**kontinuitas antar-hari** (brief hari ini tahu apa yang dikatakan brief kemarin). Keduanya bisa
dipakai tanpa scraping sama sekali — `/v2/news/` mengembalikan `title`, `body`, `source`,
`timestamp`, `sector`, `sub_sector`, `tags`, `symbols`, dan `dimension` seharga **1 kredit**.

### Kenapa "agen saham dengan scraping berita berat" gagal sebelum dinilai

Tiga alasan, berurutan dari yang paling fatal:

1. **Eligibility.** Kalau sinyalnya lahir dari berita hasil scraping, Sectors turun menjadi
   penampil harga di sebelah headline. Cabut Sectors — produk masih jalan. Itu kegagalan tes,
   tanpa banding.
2. **Mubazir.** `dimension` sudah mengklasifikasi tiap artikel di delapan tema berskor
   (`future`, `dividend`, `ownership`, `technical`, `valuation`, `financials`, `management`,
   `sustainability`). Membangun klasifikator sendiri menghabiskan minggu untuk sesuatu yang
   sudah ada seharga 1 kredit.
3. **Ekonomi sinyalnya terbalik.** Di kripto, berita **adalah** fundamentalnya — tidak ada
   laporan keuangan, tidak ada regulator, tidak ada kalender. Di saham, berita adalah *lagging
   indicator* dari sesuatu yang sudah terekam di data terstruktur: broker flow, filing insider,
   komposisi pemegang saham, aksi korporasi. Berita berguna untuk **menjelaskan**, bukan untuk
   **mendeteksi**.

**Pembalikannya:** data Sectors menghasilkan sinyal, berita menjelaskannya. Scraping menjadi
lapisan pengaya opsional yang bisa dimatikan tanpa mematikan produk. Itu satu-satunya bentuk
yang lolos eligibility sekaligus tetap terasa seperti Meridian.

---

## Bagian 3 · Apa yang menggerakkan saham — dan kenapa berbeda dari kripto

Ini inti pertanyaannya. Perbedaannya bukan sekadar "asetnya lain". Perbedaannya **struktural**,
dan tiap perbedaan mengubah satu keputusan arsitektur.

### 3.0 Perbedaan pokok, dalam satu tabel

| Sumbu | Kripto / DLMM | Saham IDX |
| --- | --- | --- |
| Jam pasar | 24/7, tanpa jeda | Sesi tetap, T+2, **22 hari libur bursa 2026** yang tidak diekspos endpoint mana pun |
| Batas gerak harga | Tidak ada | **ARA/ARB** — auto rejection asimetris per pita harga |
| Transparansi kepemilikan | Total — tiap wallet terlihat, gratis, real-time | Buram — hanya lewat pelaporan wajib: broker summary, filing, komposisi bulanan |
| Fundamental | Praktis tidak ada | Laporan kuartalan wajib, diaudit, **bertanggal, bisa diketahui sebelumnya** |
| Regulator | Tidak ada | IDX + OJK — bisa menyuspensi, memindahkan papan, memberi notasi, mendelisting |
| Peristiwa terjadwal | Nyaris tidak ada | Earnings, RUPS, cum/ex dividen, rights issue, rebalancing indeks — **kalender penuh** |
| Kemampuan short | Bebas | **Masih dilarang/ditunda di Indonesia** → ekspresi arah bersifat asimetris |
| Umpan balik posisi | Jam | Minggu sampai kuartal |
| Ground truth untuk belajar | PnL terealisasi | **Pengumuman bursa bertanggal** (suspensi, PPK, UMA, delisting) |
| Sifat gerak | Refleksif, naratif, likuiditas tipis | Arus dana + fundamental + rezim makro, dengan *pocket* refleksif di saham gorengan |
| Biaya data | Gratis dari chain | Berkredit, dan itu yang membentuk seluruh arsitektur Anda |

Satu baris yang paling sering diabaikan pembangun yang datang dari kripto: **di saham, data
mahal dan kepemilikan buram.** Di DLMM, `holder count` adalah panggilan gratis. Di IDX, padanan
terdekatnya — siapa yang mengakumulasi — hanya bisa disimpulkan dari broker summary agregat,
dan tiap panggilan menagih kredit. Arsitektur yang mengasumsikan data murah akan kehabisan 623
kredit tersisa dalam dua hari iterasi.

### 3.1 Lapis 0 — Mikrostruktur dan aturan bursa (tidak ada padanan di kripto)

Ini lapisan yang paling sering dilewatkan pembangun dari dunia kripto, dan justru yang paling
sering menjelaskan pergerakan harga saham kecil di IDX.

- **ARA/ARB (Auto Rejection Atas/Bawah).** Harga tidak bisa bergerak melampaui pita harian.
  Dalam revisi yang sedang dibahas: **35%** untuk saham Rp10–200, **25%** untuk Rp200–5.000,
  **20%** di atas Rp5.000; rentang Rp1–10 tetap Rp1 dari harga acuan. Konsekuensinya bagi model:
  serangkaian hari yang **mentok di ARA** bukan "return besar", itu **antrian yang tidak
  terpenuhi** — informasinya ada di volume dan di jumlah hari beruntun, bukan di besar returnnya.
- **Papan Pemantauan Khusus + Full Call Auction.** Saham yang memenuhi salah satu kriteria
  dipindah ke lelang berkala, bukan matching kontinu. Likuiditas runtuh. **172 saham** ada di
  sana per Januari 2026, sekitar seperlima pasar. Ini peristiwa bertanggal, diumumkan, dan
  memukul pemegang saham secara nyata — kandidat label terbaik yang ada.
- **Suspensi dan UMA.** Suspensi punya tanggal dan alasan resmi, tersedia di `/v2/suspensions/`
  yang di-refresh **harian 10:00 WIB**. Ini menentukan jam tick agen Anda: job jam 07:00 menilai
  peringatan kemarin memakai data suspensi yang belum diperbarui.
- **Short selling masih ditunda.** IDX memperpanjang penundaan melewati tenggat 17 Maret 2026
  dengan alasan kondisi pasar rapuh; IDSS untuk institusi domestik dan asing masih menunggu
  evaluasi. Artinya: **tidak ada mekanisme untuk mengekspresikan pandangan negatif**. Semua
  tekanan jual berasal dari pemegang yang keluar. Ini yang membuat pola pump-and-dump di IDX
  berbeda bentuknya dari di kripto — tidak ada pihak yang secara ekonomis diuntungkan dengan
  menekan lebih awal, jadi distorsi bisa bertahan lebih lama sebelum runtuh.
- **Program Liquidity Provider** dan aturan free float — mengubah kedalaman order book pada
  saham tertentu tanpa perubahan fundamental apa pun.
- **Kalender libur bursa.** 22 hari pada 2026, tidak ada endpoint. Scheduler yang mengabaikannya
  menghasilkan hari-hari kosong yang terlihat seperti anomali. Kalendernya sudah ada di
  `synth_extended.py`.

### 3.2 Lapis 1 — Arus dana dan kepemilikan (spesialisasi Indonesia)

Inilah "bandarmology", dan inilah tempat Sectors punya data yang tidak dimiliki orang lain.

| Sumbu | Endpoint | Kredit | Isi |
| --- | --- | --- | --- |
| Aliran broker | `/v2/broker-summary/{symbol}/top/` | 2 | `rank`, `broker_code`, `net_idr`, dan filter `cohort` (retail/institutional) serta `origin` (foreign/domestic) **langsung di parameter** |
| Identitas broker | `/v2/brokers/` | 1, cache selamanya | `origin`, `cohort` |
| Aliran asing | `/v2/foreign-flow/{symbol}/` | 1 | `net_foreign_inflow` harian, ≤90 hari |
| Panel kepemilikan | `/v2/company/shareholders-composition/{symbol}/` | 1/tahun | Bulanan sejak 2021, 9 kategori investor × lokal/asing |
| Insider | `/v2/filings/?symbol=` | 1 | `holder_name`, `holding_before`, `transaction_type` |
| Jaringan | `?sections=ownership` | 1 | `major_shareholders`, `top_transactions` **bernama institusi**, `whale_investors`, `conglomerates_group` |

Tiga catatan yang mengubah kode:

**Jebakan zero-sum.** Menjumlahkan net pembeli dengan net penjual selalu mendekati nol — untuk
tiap pembeli ada penjual. `net_idr` **sudah negatif** untuk sisi jual, jadi skor dominansi
**menjumlahkan**, bukan mengurangi. Salah tanda membalik seluruh produk.

**Rezim arus asing adalah faktor tingkat pasar, bukan tingkat saham.** Pada 2026 ini bukan
detail akademis: outflow asing menembus **~Rp75 triliun** per akhir Juni, IHSG terkoreksi
**~31,8% YTD** dan sampai 35,8% dari puncaknya di 9.134,7 (Januari). Model risiko per-saham yang
tidak mengendalikan rezim pasar akan menyalakan peringatan untuk seluruh papan sekaligus.

**Inklusi/eksklusi indeks adalah arus dana yang bisa diketahui jadwalnya.** Ini padanan
terdekat dengan "listing di exchange besar" di kripto, tapi terjadwal dan terpublikasi. Dan
2026 memberi contoh ekstremnya: **MSCI membekukan rebalancing Indonesia** — IHSG ditutup
**−7,35%** pada hari pengumuman (28 Januari 2026), 18 saham dikeluarkan dari benchmark efektif
1 Juni 2026, BREN dan DSSA menghadapi risiko outflow ~$270 juta. Alasan yang dinyatakan MSCI:
**kualitas free float dan transparansi kepemilikan**. Per review Agustus 2026, status emerging
market dipertahankan tetapi pembekuannya tetap berlaku.

Perhatikan apa artinya itu untuk dosir ini: **free float dan konsentrasi kepemilikan sedang
menjadi berita halaman depan**, dan itu persis dua sumbu yang sudah bisa dihitung dari data
Sectors. Video yang membuka dengan "ini alasan MSCI membekukan Indonesia, dan ini cara mengukur
saham mana yang paling terpapar" punya pengait yang tidak bisa dikarang tim lain.

### 3.3 Lapis 2 — Fundamental dan aksi korporasi (terjadwal, wajib, nol padanan kripto)

Ini yang paling asing bagi orang kripto: **peristiwa yang tanggalnya diketahui sebelum
terjadi**.

- **Earnings.** `/v2/companies/quarterly-financial-dates/?since=<terakhir>` hanya mengembalikan
  emiten yang melapor sejak polling terakhir — endpoint yang memang ada untuk polling kesegaran
  murah. Pelaporan bersifat *bursty*: menumpuk di minggu-minggu setelah tiap tutup kuartal.
- **Siklus dividen.** RUPS → cum date → ex date → pembayaran. Di Indonesia ini menggerakkan
  perilaku ritel secara masif, dan **harga turun secara mekanis** pada ex-date. Model anomali
  yang tidak menyadari ex-date akan melaporkan penurunan terjadwal sebagai kejadian luar biasa.
- **Aksi korporasi.** `/v2/company/corporate-actions/{symbol}/` — `right_issue`, `warrant`,
  `bonus`, `stock_split`, plus `agm_result`. Semuanya **mengubah jumlah saham dan free float
  pada tanggal yang sudah diketahui**. Rights issue adalah satu-satunya bagian dari cerita free
  float yang menatap ke depan.
- **Jebakan nama field bergantung sektor.** `/v2/financials/quarterly/{symbol}/` mengembalikan
  `realized_capital_goods_investment` untuk bank dan `capital_expenditure` di slot yang sama
  untuk non-bank. Parser yang ditulis dari contoh spec **diam-diam membuang capex seluruh pasar
  non-bank**. Baca kedua kunci.
- **Sinyal tekanan struktural**: ekuitas negatif, opini audit disclaimer, PKPU/kepailitan, tidak
  ada pendapatan. Ini kriteria PPK, dan sebagian besar bisa dihitung.

### 3.4 Lapis 3 — Sektor, komoditas, dan makro

IHSG bukan indeks teknologi. Ia indeks **komoditas dan bank**, dan dua sumbu itu digerakkan oleh
hal yang sepenuhnya di luar emitennya.

- **Komoditas.** `mining.sectors.app` menyimpan 594 perusahaan batu bara termasuk yang tidak
  tercatat, benchmark HBA, ekspor, izin, dan cadangan. Harga batu bara, nikel, CPO, emas
  menggerakkan seluruh subsektor serempak. Catatan operasional: **hanya 9 dari 366 perusahaan
  tambang punya detail record** — filter dengan `?has_financials=true`.
- **Bank.** LAR, NIM, pertumbuhan kredit; definisi lengkap tiap field perbankan ada di FLARE
  dengan sitasi OJK/Basel III.
- **Makro.** BI menaikkan BI Rate **100 bps sejak Mei 2026** (4,75% → 5,75%) untuk menahan
  rupiah yang menyentuh rekor terlemah **18.178** pada 8 Juni, lalu menahannya di 5,75%. Selisih
  yield SUN vs UST menentukan daya tarik aset Indonesia bagi asing. Ditambah faktor yang
  disebut analis secara eksplisit pada 2026: **inkonsistensi kebijakan pemerintah** dan
  geopolitik.

Konsekuensi desain: **anomali harus dinormalisasi terhadap subsektor dan terhadap rezim pasar.**
Lonjakan volume di saham batu bara pada hari HBA melonjak bukan anomali. Lonjakan volume di
saham yang sama ketika seluruh subsektornya diam — itu anomali.

### 3.5 Lapis 4 — Naratif dan sosial

Di sini kripto dan saham paling mirip, dan justru di sini saham lebih sulit.

Grup Telegram, cuitan, video YouTube menggerakkan saham gorengan Indonesia sama seperti mereka
menggerakkan memecoin. Bedanya: di kripto Anda bisa memverifikasi klaim naratif terhadap chain —
wallet deployer, konsentrasi holder, kunci likuiditas — secara gratis dan real-time. Di saham,
**tidak ada chain**. Proksi terdekatnya adalah broker summary, filing insider, dan komposisi
pemegang saham bulanan, semuanya agregat, tertunda, dan berkredit.

Itu bukan kelemahan produk — itu **problem statement-nya**. Investor ritel yang menerima tip di
grup chat tidak punya cara membedakan pergerakan nyata dari yang direkayasa, justru karena
transparansi yang dianggap biasa di kripto tidak ada di sini.

Satu pagar yang tidak bisa dinegosiasikan: **jangan scrape grup sinyalnya.** Pengguna yang
menempelkan tickernya. Itu menjaga Sectors sebagai satu-satunya sumber data, menjaga eligibility
bersih, dan menghindari mengumpulkan pesan orang lain.

---

## Bagian 4 · Konsekuensi bagi desain agen

Empat perbedaan di atas mengubah empat keputusan konkret.

### 4.1 Sinyal reward harus diganti, bukan diskalakan

Meridian belajar cepat karena posisinya tertutup dalam hitungan jam dan hasilnya berupa angka
tunggal. Agen saham tidak punya itu — dan **tidak boleh** punya, karena mengejar PnL berarti
mengeksekusi trade.

Penggantinya: **peristiwa bertanggal yang diumumkan bursa.**

| Meridian | Padanan saham | Kenapa sah |
| --- | --- | --- |
| Posisi tertutup dengan PnL | Suspensi IDX | Bertanggal, beralasan, ada `pdf_url` |
| Take profit tercapai | Masuk PPK | Diumumkan per periode, memukul pemegang saham secara nyata |
| Stop loss kena | Runtuh setelah lonjakan | `/v2/daily/` OHLC + volume, ≤90 hari per panggilan |
| Out of range | Notasi khusus / UMA | Diumumkan bursa |

Label ini **tidak berkorelasi dengan return**, dan itu justru keunggulannya: memprediksi
peristiwa administratif adalah deskripsi, bukan saran investasi. Aman di bawah code of conduct,
dan bisa di-backtest karena tanggalnya publik.

### 4.2 Belajar harus dari masa lalu **dan** masa depan

22 hari tidak cukup untuk mengumpulkan peristiwa. Jadi dua sumber label sekaligus: replay
historis untuk menginisialisasi ambang, forward test harian untuk membuktikan loopnya hidup.
Rancangan lengkapnya — termasuk lima pagar anti-overfitting dan masalah kebocoran label — sudah
ada di [`../../research/plan/pump-and-dump/agen-risiko-belajar-mandiri.md`](../../research/plan/pump-and-dump/agen-risiko-belajar-mandiri.md).

Satu tambahan dari riset hari ini: **`/v2/free-float/` tidak punya field tanggal.** Memakainya
sebagai fitur untuk memprediksi peristiwa masa lalu adalah kebocoran murni. Penggantinya adalah
float yang direkonstruksi dari panel `shareholders-composition` bulanan. Aturan yang perlu
ditulis sebagai tes di repo: **tiap fitur harus punya tanggal, dan tanggal itu harus lebih awal
dari tanggal peristiwanya.**

### 4.3 Kadensi tick ditentukan input paling lambat

Bukan penutupan pasar. `/v2/suspensions/` di-refresh harian 10:00 WIB dan ia adalah sumber label
utama, jadi tick harian berjalan **setelah 10:00 WIB**. `/v2/filings/` tiap 2 jam, `/v2/news/`
tiap 4 jam, `/v2/index-daily/` hari kerja 18:00 WIB.

Bandingkan dengan Meridian yang tick tiap 10 dan 30 menit. Agen saham yang tick tiap 10 menit
membakar kredit untuk membaca angka yang sama berulang kali.

### 4.4 Anggaran kredit adalah batasan arsitektur, bukan detail operasional

623 kredit tersisa dari 1.000. Profil kerapuhan lengkap satu ticker ≈ **10 kredit**. Universe
demo 30 nama ≈ 300 kredit, di-prefetch sekali, di-cache, diputar ulang di video.

Meridian memanggil API-nya sesering yang ia mau. Agen ini tidak bisa. Maka **planner yang sadar
anggaran** — yang memutuskan endpoint mana yang layak dipanggil untuk pertanyaan ini — bukan
hiasan arsitektur; itu keharusan, dan kebetulan ia juga persis jenis orkestrasi yang dicari bar
Track 01.

---

## Bagian 5 · Bentuk yang lolos: "Meridian-IDX"

Gabungan dari yang di atas, dinyatakan sebagai satu produk.

> **Agen risiko yang menjalankan screen kerapuhan harian atas watchlist IDX, menilai
> peringatannya sendiri terhadap pengumuman bursa yang benar-benar terjadi, menulis pelajaran
> terstruktur dari tiap kesalahannya, dan menggeser ambangnya sendiri di dalam pagar yang bisa
> diaudit.**

### Yang dipinjam dan yang dibuang

| Komponen `yunus-0x/meridian` | Nasib | Alasan |
| --- | --- | --- |
| Loop ReAct dengan prompt sadar peran | **Dipinjam** | Persis yang disebut bar Track 01 |
| `decision-log.json` | **Dipinjam** | Agen bisa mempertanggungjawabkan keputusan lampau |
| Lessons pasca-peristiwa | **Dipinjam** | Label diganti dari PnL ke pengumuman bursa |
| Threshold evolution | **Dipinjam, diperketat** | 5 posisi terlalu sedikit; butuh N≥20/sumbu, batas langkah 10%, lantai-langit, hold-out, tombol mati |
| Dua agen jadwal terpisah | **Dipinjam, dilambatkan** | 30 mnt/10 mnt → satu tick harian setelah 10:00 WIB |
| HiveMind | **Dipinjam sebagian** | Menjadi generalisasi lintas subsektor, bukan jaringan antar-instance |
| Buka/tutup posisi on-chain | **Dibuang** | Dilarang di semua track |
| Wallet, modal, PnL | **Diganti** | Skor peringatan, bukan PnL |
| Discord signal ingestion | **Dibuang** | Scraping grup sinyal merusak eligibility dan mengumpulkan pesan orang lain |
| `studyTopLPers` | **Diganti** | Padanannya: mempelajari perilaku broker teratas per kohort |

### Dari `iliane5/meridian`

Klasterisasi sebelum sintesis, dan kontinuitas antar-hari. Diterapkan pada `/v2/news/` — bukan
pada RSS hasil scraping. Berita menjawab satu pertanyaan saja: *apakah ada alasan fundamental di
balik pergerakan ini?* Kalau `dimension` hanya mengembalikan liputan `technical` dengan
`financials` dan `future` bernilai nol, itu bagian dari sinyal.

### Penempatan track

**Track 03** kalau intinya skornya. **Track 02** kalau intinya jadwalnya dan Anda punya riwayat
run tanpa ditunggui. **Track 01** kalau loop belajarnya benar-benar ada dan terlihat di ledger —
tapi ingat Track 01 punya 15 tim dan bar diskualifikasi terketat.

Rekomendasi: **Track 02 dengan loop belajar sebagai kedalaman teknisnya.** Ladang paling kosong,
bukti paling murah (nyalakan scheduler hari ini melawan mock, gratis), dan loop belajarnya
memberi skor 30% technical depth tanpa harus bersaing di kolam Track 01.

---

## Bagian 6 · Dua temuan baru per 9 September 2026

### 6.1 Revisi aturan PPK mengancam tiga dari tujuh kriteria yang bisa dihitung

BEI menargetkan rilis revisi aturan Papan Pemantauan Khusus/FCA pada **Q3 2026** — yaitu
sekarang, di tengah masa lomba. Yang diusulkan dihapus: **kriteria 6 (free float), kriteria 7
(likuiditas rendah), dan kriteria 10 (suspensi lebih dari satu hari bursa)**. Tujuh kriteria
lain dipertahankan, termasuk kriteria 1 (harga rata-rata di bawah Rp51) dan kriteria 5 (ekuitas
negatif).

[`../../research/plan/idea-ppk-early-warning.md`](../../research/plan/idea-ppk-early-warning.md) menghitung **tujuh dari sebelas**
kriteria. Tiga yang diusulkan hilang — 6, 7, dan 10 — semuanya ada di daftar tujuh itu. Kalau
aturan barunya terbit sebelum 30 September, prediktor yang dibangun terhadap rulebook lama
memprediksi rezim yang sudah tidak berlaku, dan juri yang mengikuti pasar akan tahu.

**Tindakan:** verifikasi status aturan terhadap dokumen primer IDX sebelum berkomitmen, dan
kalau ide PPK dipakai, arsitekturkan kriterianya sebagai **konfigurasi berversi**, bukan
konstanta — lalu tunjukkan di video bahwa produknya bertahan terhadap perubahan aturan. Itu
justru mengubah risiko menjadi bukti kedalaman.

Efek sampingnya: usul menghapus kriteria free float juga melemahkan ide #3 daftar pendek
(free-float stress test) lebih jauh dari yang sudah dinyatakan di sana.

### 6.2 Pembekuan MSCI menjadikan free float dan konsentrasi kepemilikan cerita halaman depan

MSCI membekukan rebalancing indeks Indonesia atas **kualitas free float dan kekhawatiran
konsentrasi kepemilikan**; IHSG ditutup **−7,35%** pada hari pengumuman, 18 saham keluar dari
benchmark efektif 1 Juni 2026, dan pembekuan Foreign Inclusion Factor berlaku untuk semua saham
Indonesia. Per review Agustus 2026 pembekuan itu masih berlaku.

Ini pengait pembuka video yang kuat, dan ia bekerja untuk **ide 4 (pemeriksa kerapuhan)**
maupun modul float: masalahnya nyata, baru, terverifikasi secara eksternal, dan sumbu yang
dipersoalkan MSCI persis sumbu yang sudah bisa dihitung dari data Sectors.

---

## Bagian 7 · Kalau saya juri

Asumsi: saya membaca repo dan menonton video tiga menit, asinkron, tanpa Anda hadir, setelah
melihat belasan submission lain. Berikut penilaian saya atas "Meridian untuk saham" **sebagaimana
dirumuskan awal** — agen dengan scraping berita berat — lalu atas bentuk yang direkomendasikan.

### 7.1 Kartu skor: "agen saham bergaya Meridian dengan scraping berita"

| Tahap | Vonis |
| --- | --- |
| **Stage 1 · Eligibility** | **Berisiko gagal.** Kalau sinyal lahir dari berita hasil scraping, Sectors bukan sumber inti. Saya mencabutnya secara mental; kalau produk masih jalan, selesai di sini. |
| **Usability (40%)** | **Rendah–sedang.** "Agen intelijen saham" bukan pengguna. Saya butuh satu kalimat berisi orang. |
| **Video (30%)** | Sedang. Agen berpikir itu menarik ditonton, tapi tanpa masalah yang terumus, ia jadi demo teknologi. |
| **Technical depth (30%)** | **Rendah**, dan ini yang menyakitkan: saya tahu `/v2/news/` sudah mengembalikan `dimension`. Membangun klasifikator berita sendiri terbaca sebagai tidak membaca dokumentasi, bukan sebagai kedalaman. Dan agen multi-spesialis fundamental/teknikal/berita adalah **resep FinArena kami sendiri**, terbit Juni 2026. |

Total: tidak masuk daftar pendek.

### 7.2 Kartu skor: "Meridian-IDX" — agen risiko yang belajar mandiri

| Tahap | Vonis |
| --- | --- |
| **Stage 1** | **Lolos bersih.** Enam sumbu sinyalnya semuanya endpoint Sectors. Cabut Sectors dan tidak ada yang tersisa. |
| **Usability (40%)** | **Tinggi** — kalau kalimat pembukanya benar. "Investor ritel Indonesia yang menerima tip saham di grup chat dan tidak punya cara membedakan pergerakan nyata dari yang direkayasa" bernilai bagus. "Platform intelijen risiko" tidak. |
| **Video (30%)** | **Tinggi**, dan ini bagian yang paling sering disia-siakan tim. Ceritanya sudah jadi: agen ini **salah** pada tanggal X, inilah pelajaran yang ia tulis, inilah ambang yang ia geser, inilah hasil sesudahnya. Agen yang mengaku salah di depan kamera lebih meyakinkan daripada kurva yang naik. |
| **Technical depth (30%)** | **Tinggi kalau ledger-nya ada di repo.** Yang saya cari: `warnings.jsonl`, `outcomes.jsonl`, `lessons.jsonl`, `thresholds.json` dengan riwayat perubahan di dalamnya. Itu bukti orkestrasi yang tidak bisa dipalsukan oleh prompt. |

### 7.3 Tujuh pertanyaan yang akan saya ajukan ke repo

Setiap tim harus bisa menjawab semuanya dari kode, bukan dari README.

1. **Cabut Sectors — apa yang mati?** Kalau jawabannya "tampilan harga", Anda gagal Stage 1.
2. **Mana bukti run tanpa ditunggui?** Konfigurasi cron plus log bertimestamp lintas hari.
   Satu run manual yang dipicu saat merekam tidak cukup, dan aturannya menyatakan itu.
3. **Fitur mana yang punya tanggal?** Kalau backtest memakai `free_float` hari ini untuk
   memprediksi suspensi 2024, seluruh angka evaluasinya tidak berarti. Saya akan mencarinya.
4. **Apakah broker flow dijumlahkan dengan benar?** `net_idr` sudah negatif untuk sisi jual.
   Kalau saya lihat `sum(buyers) + sum(sellers)` sebagai total, produknya datar dan tim tidak
   menyadarinya.
5. **Apa yang dilakukan agen ketika ia salah?** Kalau tidak ada jawabannya, "belajar mandiri"
   adalah klaim slide.
6. **Berapa kredit yang dihabiskan demo ini, dan bagaimana Anda tahu?** Ledger spend adalah
   sinyal kematangan rekayasa yang tidak dimiliki hampir semua tim.
7. **Apakah produk ini memberi saran investasi?** Skor yang disajikan sebagai rekomendasi
   melanggar code of conduct. Bahasa deskriptif melindungi seluruh submission.

### 7.4 Yang membuat saya mencoret tim, terlepas dari kualitas kode

- Membangun ulang resep yang sudah kami terbitkan — brief top-movers jam 7 pagi ke Discord,
  chatbot screener bahasa alami, agen spesialis FinArena.
- Dashboard bidang Sectors yang disebut "market intelligence". Itu render ulang.
- Video yang menghabiskan 90 detik pertama menjelaskan arsitektur. Saya perlu tahu masalah
  siapa yang diselesaikan sebelum saya peduli bagaimana.
- Klaim yang tidak bisa saya verifikasi di repo. Kriteria technical depth menyatakan
  "diverifikasi terhadap repositori GitHub" — kalau tidak ada di sana, ia tidak dihitung.
- Angka yang dihalusinasikan. Satu angka keuangan yang salah di layar merusak seluruh premis.
  Verifikator fail-closed — asisten menolak menyebut angka yang tidak ia ambil — justru
  mengesankan.

### 7.5 Kalau saya harus memilih satu hal untuk Anda kerjakan hari ini

Nyalakan scheduler. Sekarang, melawan mock, gratis:

```bash
cd ../research/harness && python3 src/mock_server.py --port 8787 --credits 1000
```

Tanggal 30 September, tiga minggu log run tanpa ditunggui adalah satu-satunya bukti dalam
submission Anda yang **tidak bisa dikarang belakangan**. Semua hal lain di dokumen ini bisa
dikerjakan di minggu terakhir. Yang ini tidak.

---

## Sumber

Riset internal: [`../../research/docs/hackathon/`](../../research/docs/hackathon/),
[`../../research/docs/api/`](../../research/docs/api/), [`../../research/plan/already-published.md`](../../research/plan/already-published.md),
[`../../research/plan/competitive-landscape.md`](../../research/plan/competitive-landscape.md),
[`../../research/plan/idea-shortlist-2026-09-08.md`](../../research/plan/idea-shortlist-2026-09-08.md),
[`../../research/plan/idea-ppk-early-warning.md`](../../research/plan/idea-ppk-early-warning.md),
[`../../research/plan/pump-and-dump/`](../../research/plan/pump-and-dump/), [`../../research/audit/VERIFICATION-LIVE.md`](../../research/audit/VERIFICATION-LIVE.md).

Repositori rujukan: [`yunus-0x/meridian`](https://github.com/yunus-0x/meridian) ·
[`iliane5/meridian`](https://github.com/iliane5/meridian)

Eksternal, diakses 9 September 2026:

- [Revisi Aturan Papan Pemantauan Khusus FCA Ditarget Rilis Q3-2026 — Fortune Indonesia](https://www.fortuneidn.com/market/revisi-aturan-papan-pemantauan-khusus-fca-ditarget-rilis-q3-2026-00-3dhnm-tb3jd7)
- [BEI Bakal Ubah Aturan Papan Pemantauan Khusus, 3 Kriteria Dihapus — Kompas](https://money.kompas.com/read/2026/07/05/082323126/bei-bakal-ubah-aturan-papan-pemantauan-khusus-3-kriteria-dihapus)
- [FCA Dievaluasi, Bursa Revisi 3 Kriteria Saham Papan Pemantauan Khusus — CNBC Indonesia](https://www.cnbcindonesia.com/market/20260706153805-17-748427/fca-dievaluasi-bursa-revisi-3-kriteria-saham-papan-pemantauan-khusus)
- [IDX Extends Short-Selling Ban — Jakarta Globe](https://jakartaglobe.id/business/idx-extends-shortselling-ban)
- [BEI: short selling bagi institusi dan asing tunggu evaluasi di 2026 — Antara](https://www.antaranews.com/berita/4643557/bei-short-selling-bagi-institusi-dan-asing-tunggu-evaluasi-di-2026)
- [MSCI Freezes Indonesia Index Rebalancing — Tempo](https://en.tempo.co/read/2083426/msci-freezes-indonesia-stock-index-rebalancing-amid-market-concerns)
- [MSCI keeps Indonesia as emerging market, freeze remains — Indonesia Business Post](https://indonesiabusinesspost.com/7152/markets-and-finance/msci-keeps-indonesia-as-emerging-market-freeze-remains)
- [IHSG ditutup −7,35% setelah pengumuman MSCI — Katadata Databoks](https://databoks.katadata.co.id/en/market/statistics/6979df85991ed/the-jakarta-composite-index-closed-down-735-following-the-msci-announcement-wednesday-january-28-2026)
- [Market Recap Semester I-2026 — Bibit](https://blog.bibit.id/blog-1/bibit-update-market-recap-semester-i-2026)
- [Indonesia Macro Update — BI Rate 19 Aug 2026 — KB Valbury](https://www.kbvalbury.com/indonesia-macro-update-bi-rate-update-19-aug-2026)
