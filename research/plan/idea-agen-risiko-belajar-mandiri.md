# Ide · Agen Risiko yang Belajar Mandiri

> Meminjam mekanisme belajar dari `yunus-0x/meridian` — *lessons* terstruktur dan
> *threshold evolution* — dan membuang lapisan eksekusinya, yang dilarang di semua track.
> Lapisan orkestrasi untuk [`idea-shortlist-2026-09-08.md`](idea-shortlist-2026-09-08.md) #4
> (pemeriksa risiko pump-and-dump). Track 01.

## Yang dipinjam dan yang dibuang

| Komponen `yunus-0x/meridian` | Padanan di sini | Status |
| --- | --- | --- |
| Screening agent tiap 30 menit | Screen risiko harian setelah data settle | Dipinjam |
| Management agent tiap 10 menit | Penilai hasil — mengadu peringatan terbuka dengan apa yang benar-benar terjadi | Dipinjam |
| *Lessons* ditulis tiap posisi ditutup | *Lessons* ditulis tiap peringatan selesai | Dipinjam |
| Threshold evolution setelah 5+ posisi | Evolusi ambang setelah N peringatan selesai, dengan pagar | Dipinjam, diperketat |
| HiveMind — jaringan belajar bersama | Generalisasi lintas subsektor | Dipinjam sebagian |
| Buka/tutup posisi on-chain | — | **Dibuang** |
| Wallet, modal, PnL | Skor peringatan, bukan PnL | **Diganti** |

Yang tersisa setelah eksekusi dicabut tetap merupakan orkestrasi buatan sendiri: planner,
eksekutor sadar anggaran, penilai hasil, memori lintas waktu, dan lapisan yang mengubah
parameternya sendiri. Aturan Track 01 menyebut manajemen memori dan state secara eksplisit
sebagai hal yang memenuhi syarat.

---

## Masalah yang membuat ini sulit: dari mana labelnya

Agen `yunus-0x/meridian` bisa belajar cepat karena posisinya tertutup dalam hitungan jam.
Peringatan risiko saham tidak begitu. Kalau agen hanya belajar dari masa depan, dalam 22 hari
ia mengumpulkan terlalu sedikit peristiwa untuk menyetel apa pun, dan lapisan belajarnya
menjadi klaim di slide, bukan sesuatu yang bekerja.

Jawabannya: **dua sumber label sekaligus.**

### Label A — replay historis (langsung tersedia, gratis atau murah)

Peristiwa yang sudah bertanggal dan bisa diverifikasi:

| Peristiwa | Sumber | Bertanggal? |
| --- | --- | --- |
| Suspensi IDX | `/v2/suspensions/` → `suspension_date`, `reason`, `pdf_url` | Ya |
| Masuk Papan Pemantauan Khusus | Pengumuman IDX per periode | Ya, di luar API |
| Runtuhnya harga setelah lonjakan | `/v2/daily/{symbol}/` → OHLC + `volume`, ≤90 hari per panggilan | Ya |

Agen tidak perlu menunggu masa depan. Ia memutar ulang masa lalu: ambil peristiwa, rekonstruksi
seperti apa sinyal kerapuhan **N hari sebelum** peristiwa itu, lalu setel ambangnya. Ini yang
memberi agen cukup peristiwa untuk mulai belajar pada hari pertama.

### Label B — forward test selama masa bangun (bukti yang tak bisa dikarang)

Mulai hari ini, tiap hari kerja, agen mengeluarkan peringatan dan menyimpannya. Setiap
peringatan lama dinilai terhadap apa yang benar-benar terjadi. Dalam 22 hari itu menghasilkan
riwayat run tanpa ditunggui — persis bukti yang diminta Track 02, dan cerita yang jauh lebih
kuat daripada backtest saja: *agen ini salah pada 3 September, inilah lesson yang ia tulis,
inilah ambang yang ia geser, dan inilah hasilnya sesudah itu.*

Label A menginisialisasi. Label B membuktikan loopnya hidup. Keduanya perlu.

---

## "Belajar dari banyak sumber" — enam guru independen

Kekuatan Sectors untuk ini adalah bahwa beberapa endpoint memberi **pandangan yang benar-benar
independen** atas pertanyaan yang sama. Agen tidak belajar satu ambang; ia belajar bagaimana
menimbang enam saksi yang tidak saling menyalin.

| # | Guru | Endpoint | Kredit | Apa yang ia beri tahu |
| --- | --- | --- | --- | --- |
| 1 | Aliran broker | `/v2/broker-summary/{symbol}/top/` | 2 | Siapa yang mengakumulasi, kohort apa (`retail`/`institutional`), asal mana |
| 2 | Aliran asing | `/v2/foreign-flow/{symbol}/` | 1 | `net_foreign_inflow` harian, ≤90 hari |
| 3 | Struktur kepemilikan | `/v2/company/shareholders-composition/{symbol}/` | 1/tahun | Panel bulanan, 9 kategori × lokal/asing, sejak 2021 |
| 4 | Perilaku insider | `/v2/filings/?symbol=` | 1 | `holder_name`, `holding_before`, `transaction_type` |
| 5 | Katalis atau ketiadaannya | `/v2/news/?symbols=` | 1 | `dimension` — 8 tema berskor, sudah dihitung |
| 6 | Riwayat masalah | `/v2/suspensions/?symbol=` | 1 | Tanggal dan alasan resmi |

Yang dipelajari agen bukan "apakah saham ini berbahaya", melainkan tiga hal yang lebih spesifik
dan lebih bisa dipertahankan:

1. **Bobot per guru.** Guru mana yang benar-benar memprediksi hasil, per subsektor. Ambang
   kerapuhan saham tambang berbeda dari saham bank; agen menemukan itu dari data, bukan dari
   asumsi kita.
2. **Pola konvergensi.** Kombinasi mana yang berarti. Dosir ini sudah menyatakan prinsipnya:
   konfirmasi lintas sinyal independen jauh lebih kuat daripada sinyal tunggal. Agen belajar
   *kombinasi mana* yang layak dipercaya, bukan sekadar bahwa konfirmasi itu baik.
3. **Kegagalannya sendiri.** Setiap false positive ditulis sebagai lesson terstruktur — kondisi
   apa yang ada, apa yang agen kira akan terjadi, apa yang terjadi. Itu yang dibaca agen pada
   iterasi berikutnya. Ini bagian yang langsung dipinjam dari `yunus-0x/meridian`.

---

## Loop

Irama tick ditentukan oleh input paling lambat, bukan oleh penutupan pasar. Kadensi refresh
Sectors berbeda per dataset — lihat [`../docs/api/11-data-provenance.md`](../docs/api/11-data-provenance.md):

| Dataset | Kadensi |
| --- | --- |
| `/v2/filings/` | tiap 2 jam |
| `/v2/news/` | tiap 4 jam |
| `/v2/daily/` | harian |
| `/v2/suspensions/` | **harian 10:00 WIB** (`0 3 * * *`) |
| `/v2/index-daily/` | hari kerja 18:00 WIB |

Suspensi adalah input paling lambat sekaligus sumber label utama. Maka tick harian dijalankan
**setelah 10:00 WIB**, bukan setelah penutupan pasar. Job yang berjalan jam 07:00 menilai
peringatan kemarin terhadap data suspensi yang belum diperbarui.

```
tick harian (setelah 10:00 WIB)
  1. NILAI    — ambil peringatan yang masih terbuka, cek terhadap
                /v2/suspensions/ dan /v2/daily/. Tandai selesai atau biarkan terbuka.
  2. PELAJARI — untuk tiap peringatan yang selesai, tulis lesson terstruktur.
  3. SETEL    — kalau syarat evolusi terpenuhi, geser ambang. Catat alasannya.
  4. SCREEN   — jalankan screen dengan ambang saat ini. Keluarkan peringatan baru.
  5. CATAT    — tulis semuanya ke ledger append-only.
```

Langkah 5 bukan pelengkap. Ledger itulah demonstrasinya: ia menunjukkan agen berubah dari
waktu ke waktu, dan itu yang tidak bisa ditiru oleh sebuah prompt di atas klien orang lain.

---

## State yang disimpan

Empat tabel, semuanya berkas datar, semuanya append-only kecuali yang terakhir.

| Tabel | Isi |
| --- | --- |
| `warnings.jsonl` | tiap peringatan: simbol, tanggal, nilai tiap sumbu, ambang yang berlaku saat itu, prediksi |
| `outcomes.jsonl` | resolusi tiap peringatan: apa yang terjadi, berapa hari kemudian, sumber buktinya |
| `lessons.jsonl` | lesson terstruktur per peringatan yang selesai — kondisi, harapan, kenyataan, dugaan sebab |
| `thresholds.json` | ambang saat ini, plus riwayat tiap perubahan dengan bukti pendukungnya |

`thresholds.json` menyimpan riwayat di dalam dirinya sendiri, sehingga rollback selalu mungkin
dan tiap perubahan bisa ditelusuri ke peristiwa yang memicunya.

---

## Evolusi ambang — dan pagar yang membuatnya jujur

Loop penyetelan diri di atas N kecil bukan pembelajaran; itu overfitting dengan langkah
tambahan. `yunus-0x/meridian` menggeser ambangnya setelah 5 posisi tertutup. Lima terlalu
sedikit untuk domain ini, dan menyalinnya apa adanya akan menghasilkan agen yang belajar
derau lalu memamerkannya sebagai wawasan.

Lima pagar. Semuanya harus ada, dan semuanya harus terlihat di video — kedisiplinannya justru
yang bernilai, bukan besarnya perbaikan.

1. **N minimum per sumbu.** Tidak ada ambang yang bergerak sebelum sumbu itu punya minimal 20
   peringatan yang sudah selesai. Sumbu dengan 3 peristiwa tidak belajar apa-apa.
2. **Batas langkah.** Satu iterasi menggeser ambang paling banyak 10% dari nilainya. Loncatan
   besar adalah tanda derau, bukan sinyal.
3. **Lantai dan langit-langit absolut.** Ambang tidak boleh keluar dari rentang yang ditetapkan
   manusia. Tanpa ini, loop akan hanyut ke salah satu dari dua kondisi tak berguna: memperingatkan
   segalanya, atau tidak pernah memperingatkan apa pun.
4. **Periode hold-out.** Satu irisan waktu tidak pernah dipakai untuk menyetel apa pun, hanya
   untuk melapor. Angka yang dilaporkan di video berasal dari sana. Kalau performa hold-out tidak
   membaik, katakan itu di video — juri lebih menghargai temuan negatif yang jujur daripada
   kurva yang mencurigakan.
5. **Tombol mati.** Perintah yang mengembalikan seluruh ambang ke nilai awal. Loop yang tidak
   bisa dibatalkan tidak layak dijalankan tanpa pengawasan.

Kejujuran yang perlu dinyatakan di depan: belum tentu ambang yang menyetel diri mengalahkan
ambang tetap yang dipilih dengan baik pada horizon 22 hari. Yang dinilai adalah **loopnya ada,
berjalan tanpa ditunggui, dan bisa diaudit**. Kalau ternyata kalah dari ambang tetap, laporkan
itu — dan tunjukkan bagaimana Anda tahu.

---

## Jebakan yang bisa mematikan seluruh proyek

### 1. Kebocoran label — ini yang paling mungkin terjadi

`/v2/free-float/` mengembalikan array telanjang `symbol`, `company_name`, `free_float`.
**Tidak ada field tanggal.** Nilainya adalah keadaan hari ini.

Memakai `free_float` hari ini sebagai fitur untuk memprediksi suspensi tahun 2024 adalah
kebocoran murni: agen memakai informasi yang belum ada saat peristiwanya terjadi. Backtest-nya
akan terlihat hebat dan tidak berarti apa-apa.

Berlaku sama untuk `major_shareholders` di
`/v2/company/report/{symbol}/?sections=ownership` — juga snapshot saat ini.

**Penggantinya sudah ada:** float yang direkonstruksi dari
`/v2/company/shareholders-composition/{symbol}/` — bulanan, bertanggal, tersedia sejak 2021,
1 kredit per simbol per tahun. Inilah alasan modul float dari ide #3 di daftar pendek penting;
ia bukan produk terpisah, ia adalah prasyarat agar backtest ini sah.

Aturan praktisnya, tulis sebagai tes di repo: **tiap fitur harus punya tanggal, dan tanggal itu
harus lebih awal dari tanggal peristiwa.** Fitur tanpa tanggal tidak boleh masuk backtest.

### 2. Suspensi sebagai fitur sekaligus label

`/v2/suspensions/` dipakai di dua tempat: sebagai guru #6 (riwayat masalah) dan sebagai sumber
label. Untuk satu peristiwa yang sama, itu berarti agen memprediksi X memakai X. Pisahkan: hanya
suspensi **sebelum** jendela fitur yang boleh menjadi fitur.

### 3. Biaya kredit dari loop yang belajar

Tiap iterasi belajar berpotensi memanggil API. Kalau backtest diputar ulang tiap kali ambang
berubah, kreditnya habis dalam beberapa hari.

Aturannya: **ambil sekali, putar ulang berkali-kali.** Semua data historis diunduh satu kali ke
`recorded/` lewat `capture.py`, lalu penyetelan berjalan di atas berkas lokal berapa kali pun,
tanpa biaya. Hanya tick harian yang menyentuh API live.

### 4. Saham dengan seluruh fitur nol adalah saham yang disuspensi

Bukan saham yang sepi. Cek `/v2/suspensions/` sebelum menyimpulkan apa pun tentang deret datar.
Lihat [`../docs/api/10-domain-pitfalls.md`](../docs/api/10-domain-pitfalls.md).

### 5. Perangkap zero-sum pada data broker

Menjumlahkan net pembeli dan net penjual selalu menghasilkan sekitar nol. Pakai skor dominansi,
dan ingat `net_idr` **sudah negatif** untuk penjual sehingga skornya menjumlahkan, bukan
mengurangi. Salah tanda membalik seluruh produk.

---

## Yang belum diverifikasi

**Seberapa jauh ke belakang arsip broker menjangkau.** `/v2/broker-summary/{symbol}/` menerima
`start` dan `end` dengan jendela maksimum 14 hari, dan `/top/` dengan default 30 hari, tetapi
dokumentasi tidak menyatakan tanggal paling awal yang tersedia. Kalau arsipnya hanya beberapa
bulan, guru #1 tidak bisa dipakai untuk peristiwa 2024 dan backtest harus bersandar pada guru
2–6.

Ini menentukan bentuk backtest, jadi selesaikan lebih dulu dengan satu probe 1 kredit:

```
GET /v2/broker-summary/BBCA/?start=2024-01-02&end=2024-01-10
```

Probe parameter yang salah bentuk gratis — 400 tidak ditagih — tetapi rentang yang valid namun
kosong tetap ditagih 1 kredit. Satu panggilan, jawabannya pasti.

Sebagai perbandingan, batas yang **sudah** terdokumentasi: `/v2/idx-total/` sejak 1 Januari 2021,
`/v2/index-daily/` sejak 2 Januari 2019, `shareholders-composition` sejak 2021,
`/v2/daily/` maksimum 90 hari per panggilan.

---

## Anggaran kredit

Sisa ~623 (log portal: 377 sudah ditagih). Rancang backtest bertahap supaya tidak habis di depan.

### Tahap 1 — mesinnya, nol kredit

Bangun seluruh loop terhadap `recorded/` (66 endpoint sudah tertangkap dan terbayar) dan
`synth/` (volume tak terbatas, deterministik per `--seed`). Semua logika penilaian, penulisan
lesson, evolusi ambang, dan ledger bisa selesai dan teruji tanpa satu kredit pun.

```bash
cd research/harness && python3 src/mock_server.py --port 8787 --credits 1000
cd research/harness && python3 src/synth_universe.py --companies 300 --days 180
```

Jangan pernah mengirimkan data sintetis sebagai sumber data produk, dan beri label di layar
kalau ia muncul di video.

### Tahap 2 — backtest nyata yang ramping, ~80 kredit

20 peristiwa, hanya sumbu yang murah dan bertanggal lebih dulu:

| Item | Kredit |
| --- | --- |
| `/v2/suspensions/` berpaginasi, dipakai bersama semua peristiwa | ~5 |
| `/v2/daily/{symbol}/` × 20 | 20 |
| `/v2/news/?symbols=` × 20 | 20 |
| `/v2/filings/?symbol=` × 20 | 20 |
| `shareholders-composition` × 20 (satu tahun) | 20 |
| **Subtotal** | **~85** |

Tambahkan guru broker (2 kredit per simbol) hanya untuk sebagian kecil, dan hanya setelah probe
arsip di atas terjawab.

### Tahap 3 — forward test, ~5 kredit per hari kerja

22 hari kerja × ~5 = ~110 kredit. Ini yang membeli riwayat run tanpa ditunggui.

### Total

~85 + ~110 + 50 (pengambilan segar hari demo) + 150 (cadangan) ≈ **395 dari 623**. Longgar,
asalkan Tahap 1 benar-benar dikerjakan di mock dan bukan di API live.

Semua rehearsal lewat mock lebih dulu:

```bash
cd research/harness && SECTORS_BASE_URL=http://127.0.0.1:8787 python3 src/capture.py --plan plans/plan.json --budget 300
```

---

## Kenapa ini melewati bar Track 01

Bar-nya menolak "klien siap pakai plus prompt yang bagus". Yang di sini bukan itu:

- **Planner** yang memutuskan guru mana yang perlu dipanggil untuk simbol ini, dan mana yang
  bisa dilewati karena tidak informatif.
- **Eksekutor sadar anggaran** yang menolak melampaui batas kredit, dengan `capture.py` sebagai
  satu-satunya jalur ke API live.
- **Penilai hasil** yang mengadu output agen sendiri dengan pengumuman IDX.
- **Memori lintas waktu** — empat tabel state, disebut eksplisit dalam aturan sebagai kualifikasi.
- **Lapisan yang mengubah parameternya sendiri**, berpagar, teraudit, bisa di-rollback.

Semuanya terlihat di repo dan bisa didemokan.

---

## Video

Tiga menit, dan lapisan belajar tidak terlihat kecuali ditunjukkan. Urutan yang bekerja:

1. **Satu peringatan yang salah.** Tanggal, simbol, apa yang agen kira, apa yang terjadi.
2. **Lesson yang ia tulis.** Teks aslinya, di layar.
3. **Ambang yang bergeser**, beserta bukti yang memicunya, dari `thresholds.json`.
4. **Peringatan berikutnya yang benar** pada pola yang sama.
5. **Ledger**, digulir cepat — timestamp run tanpa ditunggui selama tiga minggu.

Orkestrasi yang tidak terlihat bernilai sama dengan tidak ada. Tunjukkan ledgernya.

Dan disclaimer, di layar: alat informasi dan analisis, bukan saran investasi. Tanpa eksekusi
otomatis, tanpa rekomendasi beli atau jual.
