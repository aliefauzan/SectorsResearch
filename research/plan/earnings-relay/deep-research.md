<!-- Mirror of Google Doc `178O5IZHb5bZw-1WZ431E8z_elZ8JeHYk601i3ZBuWR4`, tab 2 (Deep Research), with the Storyboard and User Flow tabs appended.
     Taken 2026-09-10. The doc can change; this copy is what the build answers to. -->

# DEEP RESEARCH — EARNINGS RELAY

## Evidence-locked earnings content untuk tim Content Ops dan Compliance

# Kesimpulan juri

Verdict saat ini: PROVISIONAL FINALIST-WORTHY — 85/100. Potential score: 93/100 bila tiga gate lolos: coverage data, koreksi manusia \<30%, dan unattended demo yang stabil.

Kekuatan utama: masalah berulang, mudah didemokan, Track 2 sangat jelas, dan artifact akhirnya langsung dapat dipakai reviewer. Kelemahan utama: kategori social scheduling, AI writing, approval, dan compliance tooling sudah padat; novelty hanya kuat bila produk benar-benar menunjukkan evidence lock per klaim, bukan sekadar generator konten.

Confidence user pain: MEDIUM. Belum ada wawancara pengguna. Confidence track-fit: HIGH. Confidence data feasibility: MEDIUM karena API key Sectors tidak tersedia saat riset.

# 1\. Metode dan batas riset

Audit dilakukan per 10 September 2026 dengan sumber resmi Sectors, OJK, FCA, FINRA, dokumentasi vendor, public editorial pages, Devpost/GitHub search, Jina Reader, Exa, RSS, dan transkrip YouTube. Exa mencapai batas free-tier pada tahap akhir; kanal sosial yang mewajibkan login/cookie tidak dipaksakan.

Novelty statement yang defensible: Tidak ditemukan solusi publik yang setara secara persona, input, trigger, workflow, claim-level evidence, dan output dalam audit terbatas per tanggal riset. Ini bukan klaim bahwa solusi serupa tidak pernah ada.

# 2\. Mengapa problem ini nyata

POJK 22/2023 menempatkan penyampaian informasi, pemasaran, dan market conduct sebagai bagian pengawasan pelindungan konsumen.\[1\] Pada 1 Januari–29 Agustus 2025, OJK mencatat 11 denda senilai Rp297 juta untuk pelanggaran informasi dalam iklan, disertai 6 peringatan tertulis dan perintah korektif termasuk penghapusan iklan.\[2\] Angka ini tidak membuktikan bahwa kesalahan earnings content adalah penyebabnya, tetapi membuktikan bahwa kualitas komunikasi publik memiliki konsekuensi nyata.

POJK 6/2026 membedakan edukasi, pemasaran, dan pemberian rekomendasi serta menekankan informasi yang jelas, akurat, jujur, mudah diakses, dan tidak berpotensi menyesatkan.\[3\] Karena target produk adalah PUJK atau platform yang dapat memublikasikan konten, hasil sistem tetap harus masuk review manusia; aplikasi tidak boleh mengeluarkan compliance verdict.

Benchmark internasional menguatkan kebutuhan workflow evidence dan approval. FCA melaporkan 19.766 promosi keuangan direview sepanjang 2024 dan 1.633 atau 8% diubah/ditarik; FCA juga melakukan review atas 411 promosi sosial dari 21 perusahaan.\[4\] FINRA Rule 2210 mewajibkan catatan komunikasi, tanggal penggunaan, approver, dan sumber tabel/statistik.\[5\] Angka ini bukan proyeksi Indonesia, melainkan bukti bahwa provenance dan approval adalah kontrol operasional yang lazim.

# 3\. Audit sampel konten publik

Sampel eksploratif: 20 halaman konten earnings/issuer dari empat penerbit publik—Stockbit, Ajaib, IPOT, dan Bareksa; masing-masing lima. Sepuluh klaim angka di-spot-check terhadap periode laporan atau sumber yang dirujuk ketika tersedia. Ini public-web proxy, bukan sampel penuh Instagram/TikTok \[6\]\[19\]\[20\]\[21\].

## Temuan observasional:

  - 20/20 halaman memuat klaim finansial numerik.
  - 20/20 menyebut periode atau konteks tanggal; kualitas pembanding antarperiode bervariasi.
  - Sebagian halaman menyebut sumber umum atau disclaimer. Stockbit, misalnya, mengingatkan pengguna untuk memverifikasi dokumen resmi IDX.\[6\]
  - 0/20 halaman yang diamati menyediakan claim-level machine-readable drawer yang membuka raw field, periode, formula, dan as\_of untuk setiap klaim.
  - Filing-to-publish latency tidak dapat dihitung secara konsisten karena timestamp event filing resmi tidak selalu tampil bersama timestamp konten. Karena itu, riset tidak mengklaim angka efisiensi waktu.

Interpretasi: kebutuhan sumber dan disclaimer sudah dipahami pasar. White space bukan “membuat ringkasan earnings”, melainkan membangun rantai bukti dari source field sampai draft dan approval.

# 4\. Matriks existing solutions

  - Hootsuite Financial Services — social management, approval, archiving, Proofpoint compliance flags. Sangat dekat pada downstream review; tidak berfokus pada transformasi earnings Indonesia atau evidence per klaim.\[7\]
  - Sprout Social — multi-step approval dan notifikasi reviewer; kuat untuk collaboration, tetapi bukan source-to-claim financial fact pipeline.\[8\]
  - Buffer — draft approval, permission, calendar, dan API/MCP draft; tidak mengunci angka ke laporan keuangan.\[9\]
  - Canva dan Adobe Express — desain, template, caption, dan scheduling. Mereka mempercepat produksi visual tetapi bukan audit layer untuk period normalization atau claim provenance.\[10\]\[11\]
  - AlphaSense — earnings research, generative search, citations, dan auditable evidence untuk analyst. Sangat kuat sebagai benchmark citation UX; output utamanya research, bukan lima-slide social pack untuk tim content Indonesia.\[12\]
  - Quartr API — transcripts, filings, slides, dan structured earnings content; dapat menjadi alternate data source, sehingga memperlemah moat bila Sectors tidak memberi keunggulan Indonesia.\[13\]
  - Stockbit AI Reports — ringkasan dokumen emiten dengan source label dan disclaimer; ini pesaing lokal paling relevan pada tahap summarization, namun tidak ditemukan approval queue, claim-status gate, atau evidence drawer per social claim pada halaman publik yang diaudit.\[6\]
  - n8n/Zapier templates — mudah membangun trigger → AI text → social draft. Threat-nya tinggi: tanpa deterministic metric lock dan audit state, Earnings Relay terlihat seperti template automation biasa.\[14\]

Verdict novelty: DIFFERENTIATED INTEGRATION, bukan pure white space. Produk akan gagal novelty bila demo hanya “data masuk, AI menulis caption”.

# 5\. Workflow penggunaan realistis

Persona utama adalah Content Operations Manager yang menjaga kalender konten untuk 5–10 emiten populer. Satu kali setup: watchlist, template lima slide, tone, forbidden claims, dan channel tujuan. Scheduler berjalan harian atau pada polling window earnings.

Ketika report date baru terdeteksi, sistem mengambil financials, menyamakan unit dan periode, lalu menghitung tiga metrik. Fact table dibekukan dengan hash. AI hanya boleh menulis kalimat yang mereferensikan fact IDs. Claim Risk Gate mencocokkan angka, periode, arah perubahan, dan penggunaan kata promosi.

Artifact dikirim ke satu review queue. Content Ops memperbaiki konteks; Compliance melihat status supported / needs review / rejected dan membuka bukti. Publishing dilakukan manual di luar MVP. Setiap run menyimpan as\_of, source endpoint, rule version, prompt version, approver, dan waktu keputusan.

# 6\. Arsitektur Track 2 dan proof of automation

State machine: scheduled → fetch → normalize → compare previous state → new/no-op/duplicate → calculate → lock facts → draft → claim gate → deliver → audit.

  - State minimum: run\_id, started\_at, completed\_at, input\_as\_of, event\_hash, rule\_version, status, retry\_count, destination, dan reviewer outcome.
  - Demo wajib: run A menghasilkan pack; run B pada event sama menjadi duplicate/no-op; run C memperlihatkan data incomplete atau failure lalu recovery tanpa draft ganda.
  - Reliability: retry terbatas, idempotency key dari ticker+period+filing date, dan fail-closed untuk klaim yang tak punya evidence.

# 7\. Pemakaian Sectors

Trigger utama: GET /v2/companies/quarterly-financial-dates/?since=… untuk mendeteksi tanggal laporan baru. Dokumentasi menyebut sekitar 950 emiten, maksimum 30 per halaman, sekitar 32 kredit untuk sweep penuh; incremental polling dan watchlist cache penting.\[15\]

Fact source: GET /v2/financials/quarterly/{symbol}/?approx=true dengan field seperti date, revenue, earnings, gross\_profit, dan field sektoral; nilai null harus menjadi unknown.\[16\]

Sectors harus tetap core: event detection, fact table, periode, dan evidence berasal darinya. Brand rules dan template boleh eksternal, tetapi workflow tidak boleh berfungsi sama ketika Sectors dicabut.

# 8\. Evidence yang mendukung dan yang melemahkan

## Mendukung:

  - Konten earnings berulang dan memiliki artifact yang jelas; reviewer langsung tahu apa yang harus dilakukan.
  - Risk control terlihat visual: satu angka dapat dibuka hingga raw field dan formula.
  - Track 2 proof kuat karena ada schedule, state, no-op, dedupe, delivery, dan audit log.

## Melemahkan / ancaman:

  - Social suites sudah memiliki approvals dan compliance integrations; AlphaSense/Quartr sudah kuat pada cited financial intelligence.
  - Public sample tidak membuktikan durasi kerja manual atau correction rate. Tanpa interview, ROI masih inferensi.
  - Laporan restatement, perubahan unit, bank/insurance fields, dan angka negatif dapat menaikkan correction rate.
  - Jika AI membuat framing promosi yang tak tersirat data, evidence benar pun tidak membuat konten aman.

# 9\. Skor juri

**STRICT 85/100 — finalist-worthy, provisional.**

  - Usability 33/40: severity dan actionability kuat; user-frequency dan time-saving belum diwawancarai.
  - Video & Storytelling 27/30: before/after dan magic moment claim drawer sangat mudah dipahami.
  - Technical Execution 25/30: scheduler, state, deterministic metrics, citations, and reliability jelas; coverage live belum diuji.

POTENTIAL 93/100 — 37/40 usability, 28/30 story, 28/30 technical. Status winner-worthy hanya setelah semua gates benar-benar lolos.

# 10\. MVP 7–10 hari

  - Hari 1–2: Sectors adapter, sample fixtures, schema, freshness polling.
  - Hari 3–4: period normalization, tiga metric functions, null/negative tests, fact-table hash.
  - Hari 5–6: template carousel/caption dan claim-to-fact mapping.
  - Hari 7: review queue, status gate, manual approval.
  - Hari 8: scheduler, retry, idempotency, no-op, audit log.
  - Hari 9–10: demo fixtures, three-run proof, video, and QA.

# 11\. Kill criteria dan eksperimen 48 jam

  - Kill bila correction rate pada 30 draft uji \>30%, satu klaim tidak dapat ditelusuri ke source field, atau workflow tetap sama tanpa Sectors.
  - Kill bila tidak dapat menunjukkan new/no-op/duplicate/failure dalam demo unattended.
  - Wawancarai tiga Content Ops dan dua compliance reviewer: berapa menit per earnings post, titik review tersulit, dan artifact apa yang mereka simpan.
  - Uji 10 laporan lintas bank, consumer, mining: target 100% angka terhubung ke fact ID dan zero unsupported auto-pass.
  - Bandingkan baseline manual vs tool: waktu review, jumlah koreksi angka/periode, dan reviewer confidence.

# Sumber

[\[1\] OJK — POJK 22/2023 Pelindungan Konsumen](https://ojk.go.id/id/regulasi/Pages/Pelindungan-Konsumen-dan-Masyarakat-di-Sektor-Jasa-Keuangan.aspx)

[\[2\] OJK — Penegakan informasi iklan 2025](https://www.ojk.go.id/en/berita-dan-kegiatan/siaran-pers/Pages/Financial-Services-Sector-Stability-Maintained-Amid-Global-and-Domestic-Dynamics.aspx)

[\[3\] OJK — POJK 6/2026 Penyampai Informasi](https://ojk.go.id/id/regulasi/Pages/POJK-6-Tahun-2026-Perilaku-Penyampai-Informasi-Sektor-Jasa-Keuangan.aspx)

[\[4\] FCA — Financial Promotions Data 2024](https://www.fca.org.uk/data/financial-promotions-data-2024)

[\[5\] FINRA — Rule 2210 Communications with the Public](https://www.finra.org/rules-guidance/rulebooks/finra-rules/2210)

[\[6\] Stockbit — AI Reports dan contoh ARTO](https://snips.stockbit.com/ai-reports-stockbit/penyampaian-laporan-keuangan-interim-yang-tidak-diaudit-arto)

[\[7\] Hootsuite — Financial Services](https://www.hootsuite.com/industries/financial-services)

[\[8\] Sprout Social — Message Approval Workflows](https://support.sproutsocial.com/hc/en-us/articles/205974715-Message-Approval-Workflows)

[\[9\] Buffer — Managing and approving draft posts](https://support.buffer.com/en-us/articles/managing-and-approving-draft-posts-57li7M8tDA)

[\[10\] Canva — Social Media](https://www.canva.com/social-media/)

[\[11\] Adobe Express — Content Scheduler](https://www.adobe.com/express/feature/content-scheduler)

[\[12\] AlphaSense — Generative Search](https://www.alpha-sense.com/platform/generative-search/)

[\[13\] Quartr — API](https://quartr.com/products/quartr-api)

[\[14\] Sectors — n8n Integration Guide](https://docs.sectors.app/recipes/non-programmatical-tools/04-n8n/01-n8n-sectors-api-guide)

[\[15\] Sectors — Latest Quarterly Financial Dates](https://docs.sectors.app/api-references/v2/indonesia/helper-list/latest-quarterly-dates)

[\[16\] Sectors — Quarterly Financials](https://docs.sectors.app/api-references/v2/indonesia/report/quarterly-financials)

[\[17\] Sectors Hackathon — Track 2](https://hackathon.sectors.app/tracks/automation-workflows)

[\[18\] Sectors Hackathon — Rules & Rubric](https://hackathon.sectors.app/rules)

[\[19\] Ajaib — Sampel konten saham](https://ajaib.co.id/belajar/saham/indf-icbp-tertekan-rugi-kurs-bagaimana-prospek-sahamnya)

[\[20\] IPOT News — Financial Statements / Research News](https://www.indopremier.com/ipotnews/)

[\[21\] Bareksa — Tag Kinerja Emiten](https://www.bareksa.com/berita/tag/kinerja-emiten)

  

  

|  |  |  |
| :-: | :-: | :-: |
| \*\*Solusi\*\* | \*\*Sudah kuat\*\* | \*\*Gap terhadap use case\*\* |
| Hootsuite / Sprout | Approval, archive, compliance integrations | Bukan earnings-to-claim evidence |
| Canva / Adobe | Template, design, scheduling | Tidak mengunci angka & periode |
| AlphaSense / Quartr | Financial research dan citations | Bukan social pack Indonesia |
| Stockbit AI Reports | Ringkasan filing lokal | Tidak terlihat claim-status workflow |
| n8n / Zapier | Trigger dan routing cepat | Mudah menjadi generic AI automation |
| \*\*Earnings Relay\*\* | \*\*Sectors trigger + fact lock + audit\*\* | \*\*Harus buktikan correction rate \\\<30%\*\* |

  
  

# Storyboard — Earnings Relay  

*Alt text: Storyboard realistis 3×3 Earnings Relay—laporan baru dideteksi otomatis, fakta Sectors dinormalisasi dan dikunci, draft diperiksa per klaim, lalu reviewer manusia menyetujui dan audit trail disimpan.*

  
  

# User Flow — Earnings Relay  

*Alt text: Swimlane Earnings Relay—Content Ops mengatur watchlist; automation mengambil data Sectors, mengunci fakta dan memeriksa klaim; Compliance mereview; hasilnya review pack dan audit log, tanpa auto-publish.*
