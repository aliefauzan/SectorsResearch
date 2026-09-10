# Disclaimer

**mersamur bersifat deskriptif. Ia bukan saran investasi dan bukan ajakan
bertransaksi.**

## Apa yang keluarannya klaim

Satu paragraf mersamur adalah **catatan atas respons Sectors API pada jendela
tanggal yang disebut di dalam paragraf itu**. Tiap angka di dalamnya dicetak
bersama endpoint dan nama field asalnya, sehingga siapa pun bisa menelusuri
ulang tiap angka ke panggilan yang sama.

Itu saja isinya. Paragraf itu:

- **tidak** menilai emitennya, manajemennya, atau prospek usahanya;
- **tidak** menyatakan bahwa suatu pergerakan harga direkayasa, dimanipulasi,
  atau sah — mersamur tidak punya akses ke identitas pihak di balik order;
- **tidak** meramalkan harga, arah harga, atau apakah suatu saham akan
  dihentikan perdagangannya;
- **tidak** memberi peringkat "aman" atau "berisiko", tidak memakai sinyal warna,
  dan tidak mengeluarkan skor yang bisa dibaca sebagai rekomendasi.

`app/render/paragraph.py` menegakkan ini di kode, bukan di niat: konstanta
`BANNED` di sana memuat daftar kata yang tidak boleh muncul di keluaran mana pun
— antara lain *beli*, *jual*, *aman*, *bahaya*, *rekomendasi*, *target harga*,
*merah*, *hijau*, *manipulasi* — dan `app/tests/test_paragraph.py` gagal kalau
salah satunya lolos.

## Bukan nasihat keuangan

Tidak ada satu pun bagian dari repositori ini, keluarannya, atau pesan yang
dikirimnya ke Telegram yang merupakan nasihat keuangan, nasihat investasi,
nasihat hukum, atau nasihat perpajakan. Pembuatnya bukan penasihat investasi
berizin dan tidak terdaftar di OJK dalam kapasitas apa pun.

Keputusan membeli, menahan, atau menjual efek adalah keputusan pembaca sendiri,
dengan risiko pembaca sendiri, dan sebaiknya diambil setelah berkonsultasi
dengan pihak berizin.

## Tidak ada eksekusi transaksi

mersamur tidak terhubung ke broker mana pun, tidak menempatkan order, dan tidak
punya jalur kode untuk melakukannya. Eksekusi transaksi otomatis dilarang di
seluruh track Sectors Hackathon 2026, dan larangan itu di sini bukan sekadar
kebijakan: satu-satunya panggilan jaringan yang dibuat produk adalah ke Sectors
API (baca) dan ke Telegram Bot API (kirim pesan).

## Data bisa salah, terlambat, atau tidak lengkap

- Sumber tunggalnya adalah Sectors API. Kalau data di sana keliru, keluaran
  mersamur ikut keliru.
- `/v2/suspensions/` — satu-satunya sumber label produk ini — hanya disegarkan
  sekali sehari pada 10:00 WIB. Peristiwa yang diumumkan setelah itu belum
  terlihat sampai siklus berikutnya.
- Sebagian besar analisis di repositori ini berjalan atas payload yang **direkam
  pada 6–9 September 2026** dan disimpan di `research/harness/recorded/`. Angka
  yang dicetak dari sana adalah keadaan pada jendela itu, bukan keadaan hari ini.
- Riwayat label suspensi cooling-down IDX baru ada sejak 2025. Semua klaim
  statistik di repositori ini berdiri di atas rentang 20 bulan, bukan dekade.

Batasan selengkapnya, termasuk yang membuat gerbang go/no-go produk ini belum
bisa diputuskan, ada di [`README.md` §Batasan](README.md#batasan-yang-dinyatakan-sendiri)
dan di `state/backtest_report.json` field `batas`.

## Nama emiten

Kode saham yang muncul di repositori ini muncul karena ia ada di respons Sectors
API pada jendela yang disebut — misalnya karena IDX pernah menghentikan
perdagangannya untuk *cooling down*, yang merupakan peristiwa publik. Kemunculan
sebuah kode saham di sini **bukan** tuduhan terhadap emiten, pemegang saham,
manajemen, atau broker mana pun.

## Lisensi data dan penggunaan

Data Sectors tunduk pada Terms of Service Sectors, termasuk batasan penggunaan
komersialnya. Repositori ini adalah karya untuk Sectors Hackathon 2026 dan bukan
produk komersial.

---

Disclaimer ini ikut tercetak — dalam bentuk ringkas — di setiap keluaran produk:
di blok CLI (`python3 -m app.cli LIFE`), di field `disclaimer` pada keluaran
`--json`, dan di setiap pesan Telegram yang dikirim `app/render/notify.py`.
