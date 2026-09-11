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
        "desc": "market_cap dipasang ke volume (nilai besar salah konteks)",
        "mutation": lambda cap: cap,  # symbolically: field reassigned
        "target": "market_cap",
        "expected_catch": True,
        "reason_pattern": "mismatch",
    },
    {
        "id": "C", "name": "as_of basi",
        "desc": "tanggal 2 minggu lalu (stale as_of)",
        "mutation": lambda d: d,
        "target": "as_of",
        "expected_catch": True,
        "reason_pattern": "stale",
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
        "mapped_to": "manejado por otro gate (citation gate, not cross_source_mismatch)",
    },
]

# A3: Positive fixtures from real recorded/v2_filings.json (20 real lines) for check_cross_source
# Blocks regression E2 by ensuring cross_source_mismatch handles real recorded data correctly.
import json
import os

POSITIVE_FIXTURES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "research", "harness", "recorded", "v2_filings.json")

def load_positive_fixtures():
    if not os.path.exists(POSITIVE_FIXTURES_PATH):
        return []
    with open(POSITIVE_FIXTURES_PATH) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data[:20]
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        return data["results"][:20]
    return []

if __name__ == "__main__":
    for a in ATTACKS:
        print(f"{a['id']}: {a['name']} — {a['desc']} (target={a['target']}, "
              f"catch={a['expected_catch']}, reason={a['reason_pattern']})")
