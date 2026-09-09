#!/usr/bin/env python3
"""Answer the four feasibility questions from red-team.md against whatever is on disk.

    python3 src/feasibility.py

Standard library only, zero credits. Reads `recorded/` via `_manifest.json` and reports
per question: ANSWERED (with the number), or BLOCKED (naming the call that would answer it).

The four questions:
  Q1  Does /v2/broker-summary/{sym}/top/ return usable rows for third-liner stocks?
  Q2  What fraction of suspended stocks have ANY news at all?
  Q3  Does a 4-axis screen beat "sort by 5-day cumulative gain"?
  Q4  What is the real base rate of cooling-down suspensions?
"""
import json
import os
import re
import statistics
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(os.path.dirname(HERE), "recorded")

# Reason patterns, ordered — first match wins. Derived from all 585 live rows:
# "cooling down" appears BOTH with and without the "peningkatan harga kumulatif" preamble,
# so matching only the preamble undercounts the label class by 17 events.
REASON_PATTERNS = [
    ("cooling_down",  r"peningkatan harga kumulatif|cooling down"),
    ("ppk_over_1y",   r"papan pemantauan khusus selama lebih dari"),
    ("price_decline", r"penurunan harga"),
    ("going_concern", r"kelangsungan usaha"),
    ("late_report",   r"belum menyampaikan laporan|belum melakukan pembayaran"),
    ("delisting",     r"delisting|buyback"),
    ("rule_I_A",      r"peraturan bursa nomor i-a|ketentuan v\.1\.1"),
    ("long_suspend",  r"suspend more than"),
]

LISTED_UNIVERSE = 900  # IDX listed companies, order of magnitude


def load(slug):
    p = os.path.join(REC, slug + ".json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)


def rows(payload):
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    return payload.get("results") or payload.get("data") or []


def classify(reason):
    text = (reason or "").lower()
    for name, pattern in REASON_PATTERNS:
        if re.search(pattern, text):
            return name
    return "other"


def header(n, title):
    print()
    print("=" * 72)
    print(f"Q{n}. {title}")
    print("=" * 72)


def q4_base_rate():
    header(4, "Base rate suspensi cooling-down")
    pay = load("v2_suspensions__limit-30") or load("v2_suspensions")
    if pay is None:
        print("BLOCKED — butuh /v2/suspensions/ (limit=30, pages=20) = 20 kredit")
        return None
    r = rows(pay)
    pag = pay.get("pagination") or {}
    total = pag.get("total_count")
    have = len(r)
    kinds = Counter(classify(x.get("reason")) for x in r)
    dates = sorted(x["suspension_date"] for x in r if x.get("suspension_date"))
    span_days = None
    if len(dates) >= 2:
        y0, m0, d0 = (int(v) for v in dates[0].split("-"))
        y1, m1, d1 = (int(v) for v in dates[-1].split("-"))
        span_days = (y1 - y0) * 365 + (m1 - m0) * 30 + (d1 - d0)

    print(f"baris di disk       : {have}" + (f" dari total_count {total}" if total else ""))
    print(f"rentang tanggal     : {dates[0]} .. {dates[-1]}" if dates else "")
    print(f"klasifikasi alasan  : {dict(kinds)}")

    sym_counts = Counter(x["symbol"] for x in r)
    repeats = {s: c for s, c in sym_counts.items() if c > 1}
    top = ", ".join(f"{k} x{v}" for k, v in Counter(repeats).most_common(8))
    print(f"emiten unik         : {len(sym_counts)}  |  berulang: {len(repeats)}"
          f"  (teratas: {top or 'tidak ada'})")

    # Per-year, because the label class is NOT stationary: cooling-down suspensions
    # do not exist before 2025. Averaging over the whole span understates the live rate.
    by_year = defaultdict(Counter)
    for x in r:
        by_year[x["suspension_date"][:4]][classify(x.get("reason"))] += 1
    print()
    print(f"{'TAHUN':6} {'cooling':>8} {'lain':>6} {'TOTAL':>7}")
    for y in sorted(by_year):
        b = by_year[y]
        other = sum(b.values()) - b["cooling_down"]
        print(f"{y:6} {b['cooling_down']:>8} {other:>6} {sum(b.values()):>7}")

    latest = max(by_year)
    cool = [x for x in r if classify(x.get("reason")) == "cooling_down"
            and x["suspension_date"].startswith(latest)]
    rate10 = None
    if len(cool) >= 2:
        ds = sorted(x["suspension_date"] for x in cool)
        y0, m0, d0 = (int(v) for v in ds[0].split("-"))
        y1, m1, d1 = (int(v) for v in ds[-1].split("-"))
        td = ((y1 - y0) * 365 + (m1 - m0) * 30 + (d1 - d0)) * 5 / 7
        per_day = len(cool) / max(td, 1)
        rate10 = per_day * 10 / LISTED_UNIVERSE
        print()
        print(f"REZIM {latest}: {len(cool)} cooling-down / ~{td:.0f} hari bursa "
              f"= {per_day:.2f} per hari")
        print(f"BASE RATE per saham per jendela 10 hari : {rate10*100:.2f}%")
        print("  -> presisi telanjang akan terlihat buruk apa pun modelnya. Laporkan LIFT.")

    all_cool = [x for x in r if classify(x.get("reason")) == "cooling_down"]
    cc = Counter(x["symbol"] for x in all_cool)
    from_repeat = sum(n for n in cc.values() if n > 1)
    print()
    print(f"RESIDIVISME: {len(all_cool)} peristiwa cooling-down / {len(cc)} emiten unik "
          f"= {len(all_cool)/max(len(cc),1):.2f} per emiten")
    print(f"  {from_repeat}/{len(all_cool)} ({from_repeat/max(len(all_cool),1)*100:.0f}%) "
          f"peristiwa berasal dari emiten yang pernah disuspensi sebelumnya")
    print("  -> BASELINE KEDUA yang wajib dikalahkan: 'pernah disuspensi'.")
    print("  -> dan risiko kebocoran: riwayat suspensi sebagai fitur memprediksi suspensi.")
    return rate10


def q2_news_coverage():
    header(2, "Cakupan berita untuk saham tersuspensi (daya beda sumbu 'tanpa katalis')")
    susp = load("v2_suspensions__limit-30") or load("v2_suspensions")
    if susp is None:
        print("BLOCKED — butuh daftar suspensi")
        return
    suspended = {x["symbol"].replace(".JK", "") for x in rows(susp)}

    targeted, requested_slug = None, None
    for fn in sorted(os.listdir(REC)):
        if fn.startswith("v2_news__") and "symbols-" in fn:
            targeted = load(fn[:-5])
            requested_slug = fn[fn.index("symbols-"):-5]
            break

    if targeted is not None:
        arts = rows(targeted)
        # The denominator is the symbols the call ASKED for, parsed out of the cache slug —
        # not every suspended stock ever. Using the full set understates coverage ~33x.
        # The cache slug truncates the symbol list, so take the basket from the plan itself.
        asked = []
        planp = os.path.join(os.path.dirname(HERE), "plans", "plan-feasibility.json")
        if os.path.exists(planp):
            with open(planp) as fh:
                asked = json.load(fh).get("suspended_basket") or []
        if not asked:
            asked = re.findall(r"[A-Z]{4}", requested_slug or "")
        covered = Counter()
        for a in arts:
            for s in a.get("symbols") or []:
                covered[s.replace(".JK", "")] += 1
        hit = [s for s in asked if covered.get(s)]
        total_articles = (targeted.get("pagination") or {}).get("total_count")
        print(f"panggilan bertarget: {len(arts)} artikel dikembalikan"
              f"{f' dari {total_articles} total' if total_articles else ''}")
        print(f"emiten diminta dengan berita : {len(hit)}/{len(asked)}")
        for s in asked:
            print(f"  {s:6} {covered.get(s, 0)} artikel")

        # The axis is not "no news" — it is "news exists but carries no fundamental weight".
        dims = Counter()
        for a in arts:
            for k, v in (a.get("dimension") or {}).items():
                if v:
                    dims[k] += 1
        print()
        print(f"dimension bukan-nol di {len(arts)} artikel: {dict(dims.most_common())}")
        fundamental = dims["financials"] + dims["future"]
        if len(hit) / max(len(asked), 1) < 0.3:
            print("  VONIS: cakupan berita nyaris nol -> sumbu konstan, BUANG")
        elif fundamental < len(arts) * 0.25:
            print("  VONIS: berita ADA tapi didominasi `technical`; `financials`/`future` jarang.")
            print("     -> rumuskan ulang sumbu: bukan 'tanpa berita', melainkan")
            print("        'berita ada tapi tidak ada yang berdimensi fundamental'.")
        else:
            print("  VONIS: sumbu punya variasi, layak diuji lebih lanjut")
        return

    broad = load("v2_news__extension-idx")
    if broad is None:
        print("BLOCKED — butuh /v2/news/?symbols=<10 nama> = 1 kredit")
        return
    covered = set()
    for a in rows(broad):
        for s in a.get("symbols") or []:
            covered.add(s.replace(".JK", ""))
    pag = broad.get("pagination") or {}
    print(f"[BUKTI LEMAH] hanya 1 halaman berita umum di disk "
          f"({len(rows(broad))} dari {pag.get('total_count')} artikel)")
    print(f"emiten pada halaman itu : {len(covered)}")
    print(f"irisan dengan tersuspensi: {sorted(suspended & covered) or 'NOL'}")
    print("BLOCKED untuk vonis — butuh /v2/news/?symbols=<nama tersuspensi> = 1 kredit")


def q1_broker_availability():
    header(1, "Ketersediaan broker-summary untuk saham lapis tiga")
    susp = load("v2_suspensions__limit-30") or load("v2_suspensions")
    targets = sorted({x["symbol"].replace(".JK", "") for x in rows(susp)}) if susp else []

    found, missing = [], []
    for sym in targets:
        pay = None
        for cand in (f"v2_broker-summary_{sym}_top__n_brokers-10",
                     f"v2_broker-summary_{sym}_top"):
            pay = pay or load(cand)
        (found if pay else missing).append((sym, pay))

    print(f"emiten tersuspensi   : {len(targets)}")
    print(f"punya broker-summary : {len(found)}")
    if not found:
        print("BLOCKED — butuh /v2/broker-summary/{sym}/top/ x10 = 20 kredit")
        print("  INI GERBANG PALING AWAL: kalau top_buyers kosong untuk saham ini,")
        print("  sumbu konsentrasi mati dan produk perlu dipikir ulang.")
        return

    print()
    print(f"{'SYM':8} {'buyers':>7} {'sellers':>8} {'dominance':>12}  usable")
    for sym, pay in found:
        b = pay.get("top_buyers") or []
        s = pay.get("top_sellers") or []
        dom = None
        if b and s:
            # net_idr is ALREADY negative for sellers -> dominance ADDS
            dom = (b[0].get("net_idr") or 0) + (s[0].get("net_idr") or 0)
        ok = "YA" if (len(b) >= 3 and len(s) >= 3) else "TIDAK"
        print(f"{sym:8} {len(b):>7} {len(s):>8} {str(dom):>12}  {ok}")


def q3_lift_vs_momentum():
    header(3, "Lift screen 4 sumbu vs baseline naif (kenaikan kumulatif 5 hari)")
    susp = load("v2_suspensions__limit-30") or load("v2_suspensions")
    targets = sorted({x["symbol"].replace(".JK", "") for x in rows(susp)}) if susp else []

    have = [s for s in targets if load(f"v2_daily_{s}")]
    control = [f[len("v2_daily_"):-5] for f in os.listdir(REC)
               if f.startswith("v2_daily_") and f[len("v2_daily_"):-5] not in targets]

    print(f"tersuspensi dengan daily : {len(have)}/{len(targets)}")
    print(f"kontrol dengan daily     : {len(control)}  {control}")

    if not have:
        print()
        print("BLOCKED — butuh /v2/daily/{sym}/ untuk 10 nama tersuspensi = 10 kredit,")
        print("  plus universe kontrol dari /v2/companies/ = 1 kredit.")
        print("  Ini uji yang menentukan apakah produk punya alasan untuk ada:")
        print("  kalau 4 sumbu tidak mengalahkan 'urutkan kenaikan 5 hari', tidak ada produk.")
        return

    def gain5(sym):
        d = rows(load(f"v2_daily_{sym}"))
        d = [x for x in d if x.get("close")]
        if len(d) < 6:
            return None
        d.sort(key=lambda x: x["date"])
        return d[-1]["close"] / d[-6]["close"] - 1

    g_susp = [g for g in (gain5(s) for s in have) if g is not None]
    g_ctrl = [g for g in (gain5(s) for s in control) if g is not None]
    if g_susp and g_ctrl:
        print()
        print(f"median kenaikan 5 hari, tersuspensi : {statistics.median(g_susp)*100:6.1f}%")
        print(f"median kenaikan 5 hari, kontrol     : {statistics.median(g_ctrl)*100:6.1f}%")
        print("  -> selisih inilah yang harus dikalahkan sumbu-sumbu lain untuk punya nilai")


def main():
    print("UJI KELAYAKAN — empat pertanyaan sebelum menulis kode produk")
    print(f"membaca: {REC}")
    q4_base_rate()
    q1_broker_availability()
    q2_news_coverage()
    q3_lift_vs_momentum()
    print()
    print("=" * 72)
    print("Setiap BLOCKED di atas menamai panggilan yang membukanya.")
    print("Rencananya: plans/plan-feasibility.json — 52 kredit, sudah lolos rehearsal mock.")


if __name__ == "__main__":
    main()
