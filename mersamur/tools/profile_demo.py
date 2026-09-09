#!/usr/bin/env python3
"""Render the product's actual output — a fragility paragraph — from cached payloads.

    python3 src/profile_demo.py            # every symbol we have data for
    python3 src/profile_demo.py ASLI       # one symbol

Zero credits: reads only `recorded/`. This is the product surface, not a dashboard —
the deliverable is a sentence a person can act on, with every number traceable to the
endpoint and field it came from.
"""
import json
import os
import re
import statistics
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # repo root
REC = os.path.join(ROOT, "research", "harness", "recorded")
COOL = re.compile(r"peningkatan harga kumulatif|cooling down", re.I)


def load(slug):
    p = os.path.join(REC, slug + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def rupiah(n):
    for div, unit in ((1e12, "triliun"), (1e9, "miliar"), (1e6, "juta")):
        if abs(n) >= div:
            return f"Rp{n/div:,.1f} {unit}".replace(",", ".")
    return f"Rp{n:,.0f}".replace(",", ".")


def profile(sym, brokers, susp_rows):
    """Return (paragraph, citations, axes_fired) or None if we lack data."""
    bs = load(f"v2_broker-summary_{sym}_top__n_brokers-10")
    daily = load(f"v2_daily_{sym}")
    if not bs or not daily:
        return None

    cites, axes = [], {}
    lines = []

    # --- axis: concentration -------------------------------------------------
    buyers = bs.get("top_buyers") or []
    sellers = bs.get("top_sellers") or []
    total_buy = sum(x.get("buy_idr") or 0 for x in buyers)
    if buyers and total_buy:
        top = buyers[0]
        share = (top.get("buy_idr") or 0) / total_buy
        info = brokers.get(top["broker_code"], {})
        cohort = {"retail": "ritel", "institutional": "institusi",
                  "mixed": "campuran"}.get(info.get("cohort"), info.get("cohort"))
        axes["konsentrasi"] = share
        lines.append(f"satu broker berkohort {cohort} ({top['broker_code']}) mengambil "
                     f"{share*100:.0f}% dari nilai beli sepuluh broker teratas")
        cites.append(f"konsentrasi {share*100:.0f}% -> /v2/broker-summary/{sym}/top/ "
                     f".top_buyers[0].buy_idr")
        # net dominance: net_idr is ALREADY negative on the sell side, so this ADDS
        if sellers:
            dom = (buyers[0].get("net_idr") or 0) + (sellers[0].get("net_idr") or 0)
            arah = "akumulasi" if dom > 0 else "distribusi"
            lines.append(f"dominansi neto berada di sisi {arah} sebesar {rupiah(abs(dom))}")
            cites.append(f"dominansi -> top_buyers[0].net_idr + top_sellers[0].net_idr")

    # --- axis: price / volume behaviour --------------------------------------
    d = sorted(daily, key=lambda x: x["date"])
    closes = [x["close"] for x in d if x.get("close")]
    vols = [x["volume"] for x in d if x.get("volume")]
    if len(closes) >= 6:
        gain5 = closes[-1] / closes[-6] - 1
        axes["momentum"] = gain5
        lines.append(f"harganya bergerak {gain5*100:+.0f}% dalam lima sesi terakhir")
        cites.append(f"kenaikan 5 sesi -> /v2/daily/{sym}/ .close")
    if len(vols) >= 10:
        med = statistics.median(vols[:-1])
        if med:
            ratio = vols[-1] / med
            axes["volume"] = ratio
            lines.append(f"volume sesi terakhir {ratio:.1f}x median {len(vols)-1} sesi sebelumnya")
            cites.append(f"rasio volume -> /v2/daily/{sym}/ .volume")

    # --- axis: catalyst quality ---------------------------------------------
    news = None
    for fn in sorted(os.listdir(REC)):
        if fn.startswith("v2_news__") and "symbols-" in fn:
            news = load(fn[:-5])
            break
    if news:
        mine = [a for a in (news.get("results") or [])
                if any(s.replace(".JK", "") == sym for s in (a.get("symbols") or []))]
        if mine:
            dims = Counter()
            for a in mine:
                for k, v in (a.get("dimension") or {}).items():
                    if v:
                        dims[k] += 1
            fundamental = dims["financials"] + dims["future"]
            axes["katalis"] = fundamental
            if fundamental == 0:
                lines.append(f"ada {len(mine)} artikel berita, tetapi tidak satu pun "
                             f"berdimensi financials atau future — liputannya membahas "
                             f"pergerakan harga, bukan alasan di baliknya")
            else:
                lines.append(f"{len(mine)} artikel berita, {fundamental} di antaranya "
                             f"berdimensi fundamental")
            cites.append(f"dimensi berita -> /v2/news/?symbols={sym} .dimension")

    # --- history (free, and the strongest single feature we found) -----------
    hist = [x for x in susp_rows if x["symbol"].replace(".JK", "") == sym]
    cool = [x for x in hist if COOL.search(x.get("reason") or "")]
    if cool:
        dates = sorted(x["suspension_date"] for x in cool)
        axes["riwayat"] = len(cool)
        lines.append(f"IDX sudah menghentikan perdagangannya {len(cool)} kali untuk "
                     f"cooling down, terakhir {dates[-1]}")
        cites.append(f"riwayat suspensi -> /v2/suspensions/ .reason, .suspension_date")

    fired = sum([axes.get("konsentrasi", 0) > 0.45,
                 axes.get("volume", 0) > 3.0,
                 axes.get("katalis", 1) == 0,
                 axes.get("riwayat", 0) >= 1])
    return lines, cites, fired, axes


def render(sym, brokers, susp_rows):
    out = profile(sym, brokers, susp_rows)
    if not out:
        print(f"{sym}: data belum ada di recorded/")
        return
    lines, cites, fired, axes = out
    print("=" * 74)
    print(f"  {sym}   —   {fired} dari 4 sumbu menyala")
    print("=" * 74)
    body = f"{sym} diperdagangkan dengan " + ", ".join(lines[:-1])
    body += f", dan {lines[-1]}." if len(lines) > 1 else "."
    # wrap at 74
    words, line = body.split(), ""
    for w in words:
        if len(line) + len(w) + 1 > 72:
            print("  " + line)
            line = w
        else:
            line = f"{line} {w}".strip()
    print("  " + line)
    print()
    print("  sumber tiap angka:")
    for c in cites:
        print(f"    - {c}")
    print()
    print("  Deskriptif, bukan saran investasi. Data Sectors API, "
          f"{max((x['date'] for x in sorted(load(f'v2_daily_{sym}'), key=lambda y: y['date'])), default='-')}.")
    print()


def main():
    brokers = {b["code"]: b for b in (load("v2_brokers") or [])}
    susp = (load("v2_suspensions__limit-30") or {}).get("results") or []
    targets = sys.argv[1:] or ["LIFE", "ASLI", "NICK", "TRUK", "PPGL",
                               "SAFE", "PACK", "CSMI", "TMPO", "AGAR"]
    for s in targets:
        render(s.upper(), brokers, susp)


if __name__ == "__main__":
    main()
