# 15 · Loop penilai — menilai peringatan vs kenyataan

**Kredit: rendah, ~1–2 per tick** · Dependensi: 03, 14

## Tujuan

Langkah pertama tick harian: mengambil peringatan yang masih terbuka dan mengadunya
dengan apa yang benar-benar terjadi.

## Prasyarat baca

- `research/plan/meridian-saham/spec.md` §6
- `research/docs/api/11-data-provenance.md` — kadensi refresh

## Kenapa jam 11:00 WIB

`/v2/suspensions/` di-refresh **harian 10:00 WIB** dan ia sumber label utama.
Job jam 07:00 menilai peringatan kemarin memakai data yang belum diperbarui.
Kadensi lain: `/v2/filings/` tiap 2 jam, `/v2/news/` tiap 4 jam,
`/v2/index-daily/` hari kerja 18:00 WIB.

## Berkas yang dibuat

```
app/agent/__init__.py
app/agent/adjudicate.py
```

## Langkah

1. Muat peringatan berstatus `open` dari `warnings.jsonl`.
2. Untuk tiap peringatan, cek `/v2/suspensions/` sejak tanggal peringatan dan
   `/v2/daily/` untuk perilaku harga sesudahnya.
3. Tandai: `true_positive` kalau suspensi cooling-down terjadi dalam jendela
   prediksi · `false_positive` kalau jendela lewat tanpa peristiwa ·
   `still_open` kalau jendela belum habis · `expired` untuk kasus lain.
4. Tulis ke `outcomes.jsonl` dengan bukti lengkap, termasuk `pdf_url`.
5. **Idempoten.** Tick yang dijalankan dua kali dalam sehari tidak boleh menulis
   outcome ganda. Ini penting karena scheduler bisa retry.
6. Panggilan suspensi diambil sekali per tick untuk seluruh peringatan, bukan
   per peringatan.

## Kriteria selesai

```bash
python3 -m pytest app/tests/test_adjudicate.py -q
python3 app/agent/adjudicate.py --dry-run
```

Tes:
- menjalankan dua kali menghasilkan `outcomes.jsonl` yang identik
- peringatan yang jendelanya belum habis tetap `open`
- tiap `true_positive` membawa bukti dengan tanggal dan sumber

## Jangan

- Jangan menilai peringatan yang jendelanya belum habis sebagai gagal. Itu
  membuat sistem terlihat lebih buruk dari kenyataannya.
