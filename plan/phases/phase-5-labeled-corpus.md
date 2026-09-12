# Fase 5 · Enam simbol berlabel dibeli

## Status

| | |
| --- | --- |
| Keadaan | `[ ]` belum dikerjakan |
| Menutup | PRD §9 baris 7 (S3) |
| Menunggu | Fase 0 |
| Kredit Sectors | **42** — satu-satunya fase yang membelanjakan kredit |
| Sisa sebelum fase ini | ≈616 dari 1.000 (`cd research/harness && python3 src/reconcile_usage.py`) |
| Sisa sesudah fase ini | ≈574 |

## Kenapa enam, dan kenapa berlabel

Satu simbol perlu ±7 kredit: deret harian, ringkasan broker, laporan perusahaan, free float,
berita, filing, aksi korporasi. Enam simbol = 42.

Enam adalah angka yang membuat satu belanja memenuhi dua kebutuhan sekaligus. Metrik §5
menuntut "≥3 simbol nyata menghasilkan kartu penuh", dan Fase 6 menuntut korpus peristiwa
berlabel untuk belajar. Simbol yang sama melayani keduanya — asalkan simbolnya **berlabel**.

Itulah sebabnya kandidat float tipis yang menarik ditolak. POLU.JK (float 0,115, +62,4% dalam
14 hari), SMMT.JK (0,116), JARR.JK (0,134) semuanya akan memberi kartu yang bagus, dan tidak
satu pun ada di `v2_suspensions.json` — jadi mereka tidak memberi peristiwa yang bisa dipakai
menilai kartu. **Label lebih berharga daripada float tipis**, karena label adalah yang membuat
loop belajar mungkin.

Kandidat berlabel yang ada di disk hari ini:

```bash
cd research/harness/recorded && python3 -c "
import json; d=json.load(open('v2_suspensions.json'))
print(sorted({r['symbol'] for r in d['results']}))"
```

```
['AGAR.JK','ASLI.JK','BEEF.JK','COAL.JK','CSMI.JK','DOOH.JK','EKAD.JK','INCF.JK',
 'LIFE.JK','MDIA.JK','NICK.JK','PACK.JK','PPGL.JK','SAFE.JK','TMPO.JK','TRUK.JK','YPAS.JK']
```

17 simbol unik atas 20 baris suspensi. LIFE sudah dibeli, jadi enam dipilih dari enam belas
sisanya. **Satu dari enam ditahan sebagai hold-out** dan tidak pernah dipakai menghasilkan
lesson di Fase 6; ia tidak boleh yang paling menarik, dan tidak boleh LIFE — LIFE sudah dipakai
membangun pilar, jadi memakainya sebagai hold-out adalah menipu diri sendiri. Kandidat
hold-out yang belum pernah disentuh kode: NICK.JK, PPGL.JK, SAFE.JK.

## Tugas

- [ ] **1. Rekonsiliasi ledger terhadap portal, sebelum membelanjakan apa pun.**
      Ekspor portal yang ada bertanggal `2026-09-05`
      (`ls research/evidence/usage-log/`), dan ledger memuat tujuh baris setelah tanggal itu.
      Ambil ekspor portal baru, letakkan di `research/evidence/usage-log/`, jalankan
      `python3 src/reconcile_usage.py` dan catat angkanya di `PROGRESS.md`. **Kalau sisa nyata
      kurang dari 42 + cadangan yang wajar, korpus mengecil sebelum satu panggilan dibuat**, dan
      itu keputusan yang diambil di sini, bukan di tengah pembelian.

- [ ] **2. Pilih enam simbol, tulis pilihannya beserta alasannya.**
      Kriteria: ada di `v2_suspensions.json`, punya deret harian cukup panjang untuk baseline 45
      hari bursa, dan tidak semuanya dari satu sektor. Tulis daftarnya di `PROGRESS.md` sebelum
      membeli, supaya pilihan bisa diperiksa setelahnya.

- [ ] **3. Tulis rencana tangkapan, dan rehearse terhadap mock.**
      ```bash
      cd research/harness && python3 src/capture.py --plan plans/plan-katalis-corpus.json --dry-run
      cd research/harness && python3 src/mock_server.py --port 8787 --credits 1000 &
      cd research/harness && SECTORS_BASE_URL=http://127.0.0.1:8787 python3 src/capture.py --plan plans/plan-katalis-corpus.json --budget 60
      ```
      Aturan yang menjaga anggaran: jangan biarkan `sections`, `classifications`, `periods`,
      atau `n_quarters` default; jangan panggil identifier yang tidak datang dari respons
      sebelumnya (404 tetap ditagih 1 kredit); jalankan screener bahasa alami paling banyak sekali.

- [ ] **4. Hapus apa pun yang rehearsal mock tulis ke `recorded/` sebelum menjalankannya live.**
      Payload sintetis yang tertinggal di `recorded/` adalah cara paling mudah membuat kartu
      "nyata" yang tidak nyata.

- [ ] **5. Jalankan live dengan batas anggaran keras.**
      `--budget` di bawah sisa nyata, bukan sama dengan. Satu perintah, satu kali.

- [ ] **6. Commit payload baru bersama baris ledgernya.**
      `recorded/` memang dilacak git — payload itu sudah dibayar dengan kredit dan tidak memuat
      kunci, jadi mengomitnya adalah yang menghentikan orang kedua membayar panggilan yang sama.

- [ ] **7. Verifikasi tiap simbol baru menghasilkan kartu, atau ditolak dengan nama.**
      Simbol yang ditolak `baseline_tipis` setelah dibeli adalah kredit yang terbuang, dan
      alasannya harus masuk `PROGRESS.md` supaya pembelian berikutnya tidak mengulanginya.

## Kriteria keluar

- [ ] **1.** `cd research/harness && python3 src/reconcile_usage.py` keluar dengan status 0, dan
      angkanya tertulis di `PROGRESS.md` dengan tanggal ekspor portal yang dipakai.
- [ ] **2.** Belanja fase ini, dihitung sebagai selisih total portal sebelum dan sesudah, adalah
      **≤42 kredit**.
- [ ] **3.** `cd src/katalis && ./run.sh symbols` menampilkan sedikitnya **enam** simbol berstatus
      `siap` pada lapisan `recorded` — LIFE ditambah lima baru — atau, bila ada yang ditolak,
      `PROGRESS.md` menyebut simbol dan alasannya.
- [ ] **4.** `./run.sh pilar <simbol> <tanggal>` menerbitkan kartu penuh untuk sedikitnya **tiga** simbol
      nyata, memenuhi metrik §5 baris pertama.
- [ ] **5.** `git status --porcelain` kosong: payload baru dan `_ledger.jsonl` ter-commit bersama.
- [ ] **6.** `PROGRESS.md` menyebut simbol mana yang ditahan sebagai hold-out Fase 6, dan simbol itu
      bukan LIFE.
- [ ] **7.** `./run.sh test` tetap hijau dengan jumlah assertion tidak berkurang.

## Bobot demo

Kriteria 4 adalah shot video, dan bentuknya **bukan** satu kartu: ia tiga kartu berturut-turut
untuk tiga simbol berbeda, masing-masing menyebutkan tanggal suspensinya sendiri. Satu kartu
adalah demo; tiga kartu yang mendahului tiga peristiwa adalah pola, dan pola adalah yang
dinilai kriteria "nyata, berfungsi, tidak dipalsukan untuk demo".

## Kalau ini melar

Yang dipotong di sini adalah kredit, bukan waktu, dan urutannya searah:

1. **Enam turun ke empat.** Menghemat 14 kredit. Metrik §5 "≥3 simbol nyata" tetap terpenuhi;
   korpus Fase 6 mengecil dari enam ke empat, dan pagar "≥3 peristiwa mendukung" menjadi
   praktis mustahil dipenuhi — yang berarti Fase 6 akan menulis lesson tanpa menggeser ambang,
   dan itu hasil yang sah asalkan dikatakan.
2. **Empat turun ke tiga.** Menghemat 7 kredit lagi, dan ini adalah lantai: di bawah tiga,
   metrik §5 baris pertama gagal dan kriteria keluar 4 tidak terpenuhi.

Yang **tidak** dipotong: tugas 1 (rekonsiliasi sebelum membeli) dan tugas 4 (bersihkan jejak
rehearsal). Keduanya berbiaya nol dan masing-masing mencegah kegagalan yang tidak bisa
dibatalkan — membelanjakan kredit yang tidak ada, dan menyebut payload sintetis sebagai nyata.
