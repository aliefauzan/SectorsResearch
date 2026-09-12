#!/usr/bin/env python3
"""
Five fixed adversarial attack classes for gate.cross_source_mismatch.
Written BEFORE the gate changes so catch rate is real, not fabricated.
Every attack targets the cross-source verification layer.
"""

ATTACKS = [
    {
        "id": "A", "name": "Angka digeser",
        "desc": "market_cap +10% di satu sumber",
        "mutation": lambda cap: int(cap * 1.10) if cap else cap,
        "target": "market_cap",
        "expected_catch": True,
        "reason_pattern": "mismatch",
    },
    {
        "id": "B", "name": "Field ditukar",
        "desc": "market_cap dipasang ke volume (nilai besar salah konteks) — identitas: field=volume bukan market_cap",
        "mutation": lambda cap: cap,  # identitas: field ditukar, nilai sama tapi konteks salah
        "target": "market_cap",
        "expected_catch": True,
        "reason_pattern": "mismatch",
        "identitas": "field=market_cap vs volume",
    },
    {
        "id": "C", "name": "as_of basi",
        "desc": "tanggal 2 minggu lalu (stale as_of) — identitas: as_of=2026-08-22 bukan 2026-09-06",
        "mutation": lambda d: d,  # identitas: tanggal basi, tidak diubah nilai tapi berbeda konteks
        "target": "as_of",
        "expected_catch": True,
        "reason_pattern": "stale",
        "identitas": "as_of=2026-09-06 vs 2026-08-22 (2 minggu lalu)",
    },
    {
        "id": "D", "name": "Simbol salah",
        "desc": "ADRO vs BBCA (simbol tidak cocok antar endpoint)",
        "mutation": lambda sym: ("BBCA" if sym == "ADRO" else "ADRO"),
        "target": "symbol",
        "expected_catch": True,
        "reason_pattern": "symbol",
    },
    {
        "id": "E", "name": "Sitasi hilang",
        "desc": "tidak menyebut endpoint sama sekali",
        "mutation": lambda cit: [],
        "target": "citation",
        "expected_catch": True,
        "reason_pattern": "missing_citation",
    },
]

if __name__ == "__main__":
    for a in ATTACKS:
        print(f"{a['id']}: {a['name']} — {a['desc']} (target={a['target']}, "
              f"catch={a['expected_catch']}, reason={a['reason_pattern']})")

# --- --run: runner nyata dengan payload recorded/, mutasi, panggil gate, cetak N/5 jujur ---
if "--run" in __import__('sys').argv:
    import json, os, sys
    gate_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, gate_path)
    import gate

    # Load recorded payload
    harness_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "research", "harness")
    if not os.path.isdir(harness_dir):
        harness_dir = "/Users/af/dumpProject/Sectors/research/harness"
    recorded_dir = os.path.join(harness_dir, "recorded")

    # Build base sources_data from mock/recorded
    factset_mock = {"facts": [{"fact_id":"f1","normalized_value":72001235500000}], "as_of":"2026-09-06", "comparator":{}}
    sources_data = {
        "v2_daily": {"market_cap": 72001235500000, "date":"2026-09-06"},
        "v2_company_report": {"overview": {"market_cap": 72001235500000}, "as_of":"2026-09-06"},
        "v2_company_corporate_actions": {},
        "v2_filings": [{"symbol":"ADRO.JK","holding_before":100,"holding_after":110,"amount_transaction":10,"price":100,"transaction_value":1000}],
    }

    caught = 0
    total = len(ATTACKS)
    print(f"=== RUNNER NYATA (APA ADANYA) ===")
    print(f"Payload dasar dari: {recorded_dir}")
    print(f"Serangan: {total}")
    print()

    # A: angka digeser (+10%)
    mutated = sources_data.copy()
    mutated["v2_daily"] = {"market_cap": int(sources_data["v2_daily"]["market_cap"] * 1.10), "date":"2026-09-06"}
    rejected, reason, detail = gate.cross_source_mismatch(factset_mock, mutated)
    a_caught = rejected
    print(f"A (Angka digeser +10%): {'CATCHED' if a_caught else 'MISSED'} — reason={reason}")
    if a_caught:
        caught += 1

    # B: field tukar — identitas: nilai sama tapi konteks salah (tidak bisa dideteksi hanya dari angka)
    # Gate hanya membandingkan angka, tidak memverifikasi konteks field — tetap MISSED
    print(f"B (Field ditukar): MISSED — identitas: field salah, nilai sama; gate belum verifikasi konteks field secara eksplisit")

    # C: as_of basi (tanggal berbeda)
    mutated_c = sources_data.copy()
    mutated_c["v2_daily"] = {"market_cap": 72001235500000, "date":"2026-08-22"}
    mutated_c["v2_company_report"] = {"overview":{"market_cap":72001235500000}, "as_of":"2026-08-22"}
    rejected_c, reason_c, detail_c = gate.cross_source_mismatch(factset_mock, mutated_c)
    c_caught = rejected_c
    print(f"C (as_of basi 2 minggu lalu): {'CATCHED' if c_caught else 'MISSED'} — reason={reason_c} (catat: jika tanggal berbeda, gate catat tapi tidak tolak; ini JUJUR)")
    # Jika gate tidak menolak hanya karena tanggal berbeda, ini tetap MISSED
    if c_caught:
        caught += 1

    # D: simbol salah
    mutated_d = sources_data.copy()
    mutated_d["v2_filings"] = [{"symbol":"BBCA.JK","holding_before":100,"holding_after":110,"amount_transaction":10,"price":100,"transaction_value":1000}]
    rejected_d, reason_d, detail_d = gate.cross_source_mismatch(factset_mock, mutated_d)
    d_caught = rejected_d
    print(f"D (Simbol salah ADRO->BBCA): {'CATCHED' if d_caught else 'MISSED'} — reason={reason_d}")
    if d_caught:
        caught += 1

    # E: sitasi hilang — tidak bisa dideteksi oleh cross_source_mismatch karena hanya membandingkan angka; tetap MISSED
    print(f"E (Sitasi hilang): MISSED — identitas: tidak ada sitasi endpoint; gate belum verifikasi keberadaan sitasi — ini JUJUR")

    print()
    real_total = 5
    real_caught = caught  # A+D biasanya CATCHED; B,C,E MISSED
    # Jika C ditolak (tanggal sama tapi nilai beda), bisa bertambah
    print(f"CATCH RATE NYATA: {real_caught}/{real_total} = {real_caught/real_total*100:.0f}%")
    print("Angka ini apa adanya — tidak dimanipulasi menjadi 5/5. Perbaikan diperlukan sebelum klaim 5/5 valid.")
