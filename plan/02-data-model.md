# 02 · Model data

Nama field di bawah ini dibaca dari payload yang benar-benar ada di
`research/harness/recorded/`, bukan dari spec. Perintah yang menghasilkannya ada di tiap
bagian. Field yang tidak muncul di sini tidak boleh disebut kartu — itulah arti "uji skema
fail-closed" di `README.md`.

## Bentuk payload per endpoint

```bash
cd research/harness/recorded && python3 -c "import json,glob;print(sorted(json.load(open(sorted(glob.glob('v2_brokers*'))[0]))[0].keys()))"
```

| Endpoint | Bentuk teratas | Field yang dipakai kartu |
| --- | --- | --- |
| `/v2/broker-summary/{symbol}/` | `{symbol, start, end, data: [{date, summary: [...]}]}` | `summary[].broker_code`, `summary[].nval`, `summary[].nlot`, `summary[].bavg_per_share` |
| `/v2/brokers/` | list of `{code, name, cohort, is_foreign, license_type}` | `code`, `name`, `cohort`, `is_foreign` |
| `/v2/daily/{symbol}/` | list of `{symbol, date, open, high, low, close, volume, market_cap}` | `date`, `close`, `volume` |
| `/v2/index-daily/ihsg/` | list of `{index_code, date, price}` | `date`, `price` |
| `/v2/news/` | list of `{title, body, source, timestamp, symbols, tags, sector, sub_sector, dimension, thumbnail}` | `timestamp`, `symbols`, `title`, `tags`, `dimension`, `body` |
| `/v2/filings/` | list of `{holder_name, holder_type, share_percentage_before, share_percentage_after, share_percentage_transaction, amount_transaction, price_transaction, ...}` | `holder_name`, `share_percentage_transaction`, `transaction_type` |
| `/v2/company/corporate-actions/{symbol}/` | `{symbol, corporate_actions: {agm, dividend, bonus, right_issue, stock_split, warrant, upcoming_dividend}}` | jenis aksi dan tanggalnya |
| `/v2/free-float/` | list of `{symbol, company_name, free_float}` | `free_float` |
| `/v2/suspensions/` | `{results: [{symbol, suspension_date, reason, pdf_url}]}` | `symbol`, `suspension_date`, `reason` — **belum dipakai kartu; itu Fase 1** |

Dua hal yang harus diperhatikan penulis kode:

- **`summary` adalah list, bukan dict.** Satu baris `data[]` adalah satu hari bursa, dan
  `summary` di dalamnya adalah daftar per kode broker. Struktur ini yang membuat join per hari
  mungkin dan yang membuat "per broker per hari per simbol" tidak punya substitusi gratis.
- **`corporate_actions` adalah dict berkunci jenis aksi**, bukan list rata. Tujuh kunci:
  `agm`, `bonus`, `dividend`, `right_issue`, `stock_split`, `warrant`, `upcoming_dividend`.
  Tiap kunci punya nama tanggalnya sendiri (`agm_date`, dan seterusnya) — itulah sebabnya
  pemotongan `as_of` untuk dataset ini tidak segampang `upto()` pada deret harian, dan itu
  sebagian alasan kenapa defect look-ahead di Fase 0 masih terbuka.

## Objek `Figure`

Satu angka dan asalnya, dan yang kedua wajib.

```python
@dataclass
class Figure:
    name: str
    value: object
    endpoint: str
    fields: tuple
    unit: str = ""
    note: str = ""

    def __post_init__(self):
        if not self.endpoint or not self.fields:
            raise ValueError(f"figure {self.name!r} has no citation")
```

`src/katalis/pillars.py:40`. Konstruktor menolak figure tanpa sitasi, dan itu adalah bentuk
yang benar untuk **kelahiran** angka. Yang belum benar adalah **verifikasi** kartu: gate
memeriksa keanggotaan himpunan token, bukan asal angka, jadi angka karangan yang kebetulan
bertabrakan dengan token figure lain lolos. Direproduksi hari ini:

```bash
cd src/katalis && python3 - <<'PY'
import card, pillars as P
orig = card.render
card.render = lambda *a, **k: orig(*a, **k) + "\nrasio utang terhadap ekuitas 0.53, margin 2.32%"
print(card.check_every_number_is_a_figure())    # ([], 1)  -- hijau, dan seharusnya merah
PY
```

Perbaikannya ada di Fase 0: render dari daftar `Figure` di satu fungsi, lalu bandingkan token
kartu terhadap himpunan token yang **fungsi itu sendiri** hasilkan — bukan terhadap gabungan
semua note, unit, dan headline.

## Kontrak kartu

Satu kartu punya enam blok, dan urutannya tetap.

| Blok | Isi | Gate yang menjaganya |
| --- | --- | --- |
| Headline | Verdict, plus modifier float tipis, plus modifier suspensi (Fase 1) | `check_verdict_is_never_advice` |
| Identitas | Simbol, nama perusahaan, jendela tanggal, lapisan sumber | `check_field_block_is_complete` |
| Empat pilar | Nama pilar, status, kalimat headline, daftar `Figure`, catatan sitasi | `check_every_number_is_a_figure` |
| YANG BELUM KAMI PERIKSA | Daftar apa yang tidak dilihat produk ini | `check_field_block_is_complete` |
| FIELD | Tiap `(endpoint → field)` yang menyumbang angka ke kartu ini | `check_field_block_is_complete` |
| Penyangkalan | "KATALIS menyatakan struktur transaksi, bukan nasihat investasi." | `check_no_advice_in_render` |

Blok FIELD pada kartu LIFE hari ini menyebut tujuh endpoint:

```bash
cd src/katalis && ./run.sh pilar LIFE 2026-09-01 | sed -n '/FIELD/,$p'
```

Kartu untuk simbol yang **ditolak** punya kontrak berbeda dan lebih pendek: satu baris
`<SIMBOL> <TANGGAL>: TIDAK DINILAI — <kode>: <alasan>`, ditambah daftar alasan yang mungkin.
Keluar dengan status 0, tanpa traceback. Dijaga `check_rejects_are_named` dan
`check_rejected_symbol_says_why`.

## State machine

**Status pilar.** Tiga keadaan, ditentukan ambang, tidak pernah ditentukan model.

```
tenang  →  waspada  →  bahaya
```

Tidak ada transisi mundur di dalam satu kartu: status adalah fungsi dari nilai turunan dan
ambangnya pada satu `as_of`, bukan hasil akumulasi.

**Status simbol.** Ditentukan `sources.py` sebelum apa pun dihitung.

```
tanpa_broker     tidak ada /v2/broker-summary/ untuk simbol ini di lapisan ini
baseline_tipis   deret harian lebih pendek daripada baseline_days + event_window
siap             boleh dinilai
```

```bash
cd src/katalis && ./run.sh symbols
```

Hari ini pada `recorded`: LIFE `siap` (62 hari, 7 hari aliran broker), BBCA `baseline_tipis`,
tujuh simbol lain `tanpa_broker`.

**Asal ambang.** Dua keadaan, dan kartu harus menyebutkannya (PRD §7 dan §13 — belum
terpasang, dicatat sebagai defect di `PROGRESS.md`).

```
shipped   nilai di TABLE
learned   nilai dari state/thresholds.learned.json, sudah lewat clamp()
```

## Tabel ambang

18 ambang, masing-masing `(shipped, floor, ceiling, alasan)`.

```bash
cd src/katalis && ./run.sh method
python3 -c "import sys;sys.path.insert(0,'src/katalis');import thresholds as T;print(len(T.TABLE))"   # 18
```

| Nama | Shipped | Lantai | Langit | Untuk apa |
| --- | --- | --- | --- | --- |
| `top1_dominant` | 0,4 | 0,25 | 0,6 | Pangsa net beli satu broker sebelum "pasar membelinya" berhenti jadi deskripsi yang jujur |
| `neff_dominant` | 3,0 | 2,0 | 5,0 | Pembeli efektif = 1/HHI; di bawah 3 sisi beli adalah segelintir desk |
| `neff_crowd` | 8,0 | 5,0 | 15,0 | Di atas 8 tidak ada satu tangan yang menjelaskan gerak |
| `foreign_share_in` | 0,6 | 0,5 | 0,8 | Pangsa asing di sisi beli; harus sejalan dengan arus asing bersih sebelum diucapkan |
| `retail_crowd_share` | 0,6 | 0,45 | 0,8 | Ritel + campuran di atas 60% adalah tanda kerumunan, bukan desk |
| `volume_z` | 2,0 | 1,5 | 3,5 | z robust atas log volume |
| `volume_mad_floor` | 0,05 | 0,01 | 0,3 | Tanpa lantai, saham mati ber-MAD≈0 mencetak z tak hingga |
| `resid_z` | 2,5 | 1,5 | 4,0 | z robust atas return residual 3 hari terhadap IHSG |
| `price_mad_floor` | 0,005 | 0,001 | 0,02 | Alasan yang sama dengan lantai volume |
| `beta_shrink` | 0,7 | 0,5 | 1,0 | `beta_eff = 0,7·beta_OLS + 0,3`; menahan baseline tipis memberi beta 4 |
| `baseline_days` | 45 | 30 | 60 | Hari bursa baseline. **Catatannya menulis "caps at 90 days" tanpa menyebut kalender — itu D4, ditutup di Fase 0** |
| `event_window` | 3 | 1 | 5 | Hari bursa tempat gerak dan aliran diukur bersama |
| `dead_day_share` | 0,4 | 0,2 | 0,7 | Di atas 40% hari nol-return, tidak ada z yang berarti; simbolnya ditolak |
| `news_lookback_days` | 7 | 3 | 21 | Sejauh apa artikel boleh duduk sebelum hari bertanda dan masih dibaca mendahului |
| `filing_lookback_days` | 30 | 7 | 90 | Filing insider dilaporkan dengan jeda |
| `filing_material_pct` | 0,5 | 0,1 | 2,0 | Poin persen kepemilikan sebelum layak masuk kartu |
| `thin_float` | 0,15 | 0,05 | 0,3 | Free float di bawah 15% adalah populasi tempat rupiah kecil memindahkan harga jauh |
| `float_absorbed` | 0,01 | 0,002 | 0,05 | 1% free float berpindah tangan dalam jendela peristiwa. Ini kalimat yang tidak bisa dicetak layanan lain |

`clamp()` adalah satu-satunya jalan masuk nilai hasil belajar, dan ia nyata: menulis
`top1_dominant: 0.99` menghasilkan `0.6`, bukan `0.99`. Yang belum nyata adalah gate-nya —
`check_learned_cannot_escape()` tidak pernah membuka berkasnya, jadi peracunan menggeser tiap
ambang diam-diam ke ekstrem batasnya sambil seluruh suite tetap hijau. Direproduksi hari ini:

```bash
cd src/katalis && mkdir -p state && echo '{"values":{"top1_dominant":0.99}}' > state/thresholds.learned.json
python3 -c "import sys;sys.path.insert(0,'.');import thresholds as T;print(T.provenance('top1_dominant'))"   # ('learned', 0.6)
./run.sh test | tail -2        # Semua gate hijau.
rm -rf state
```

Perbaikannya ada di Fase 0: `check_learned_cannot_escape` membaca `_learned()` dan **gagal**
bila ada nilai yang berbeda dari hasil `clamp()`-nya sendiri. Nilai yang perlu dijepit adalah
nilai yang seharusnya ditolak, bukan diam-diam diperbaiki.
