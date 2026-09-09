# 16 · Loop pelajaran — apa yang agen lakukan ketika salah

**Kredit: 0** · Dependensi: 15

## Tujuan

Ini bagian yang paling langsung dipinjam dari `yunus-0x/meridian`, dan bagian yang
membuat adegan pemenang di video mungkin terjadi.

Pertanyaan juri: *"Apa yang dilakukan agen ketika ia salah?"* Kalau tidak ada
jawabannya di berkas, "belajar mandiri" hanyalah klaim di slide.

## Prasyarat baca

- `research/plan/pump-and-dump/agen-risiko-belajar-mandiri.md` — rancangan lengkapnya
- `research/plan/meridian-saham/spec.md` §4

## Berkas yang dibuat

```
app/agent/lessons.py
```

## Langkah

1. Untuk tiap outcome baru dari tugas 15, tulis satu lesson terstruktur ke
   `lessons.jsonl`:
   - `conditions` — nilai tiap sumbu saat peringatan dikeluarkan
   - `expected` — apa yang agen kira akan terjadi
   - `actual` — apa yang benar-benar terjadi
   - `hypothesis` — dugaan sebab, satu kalimat
   - `axis_implicated` — sumbu mana yang paling mungkin keliru
   - `subsector` — karena ambang saham tambang berbeda dari saham bank
2. Lesson ditulis untuk **false positive maupun true positive**. Yang benar juga
   mengajarkan sesuatu.
3. Lesson dari 30 hari terakhir disuntikkan ke konteks screen berikutnya. Itu yang
   membuat loopnya benar-benar tertutup, bukan sekadar arsip.
4. Agregasi per sumbu dan per subsektor — inilah masukan tugas 17.

## Kriteria selesai

```bash
python3 -m pytest app/tests/test_lessons.py -q
python3 -c "from app.agent.lessons import recent; print(len(recent(days=30)))"
```

Tes:
- tiap outcome menghasilkan tepat satu lesson
- lesson membawa keenam field, tidak ada yang kosong
- `recent()` menghormati batas waktu

## Jangan

- Jangan menulis lesson berupa teks bebas dari LLM tanpa struktur. Field
  terstruktur itulah yang bisa diagregasi dan ditunjukkan di video.
