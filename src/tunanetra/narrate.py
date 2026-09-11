#!/usr/bin/env python3
"""
The derivations, and the sentences they license. No I/O, no HTTP, no file paths.

This is the part that is not a re-rendering of Sectors data. Each function takes a
normalized payload and returns a `Finding` — a claim, the raw numbers behind it, and the
`(endpoint, field, as_of)` that has to travel with it. `reader.py` refuses to print a
figure that arrives without one.

Six pictures are replaced, one function each:

    segment_concentration   Sankey of revenue      -> ranked share of the revenue root
    price_trend             candlestick            -> direction, extremes, window
    flow_runs               foreign-flow area      -> longest consecutive-sign run
    ownership_runs          stacked ownership area -> per-class direction runs
    quarterly_change        statement image        -> QoQ and YoY, sector-correct capex
    peer_rank               peer scatter           -> rank within the peer set

**Semantic level.** Lundgard & Satyanarayan (DOI 10.1109/TVCG.2021.3114770; 30 blind and
90 sighted readers, 2,147 sentences) found that blind and sighted readers rank the four
levels of description differently, and that level 1 — the marks, axes and encodings — is
the least useful content for a blind reader. Nothing here may emit level 1. `LEVEL1_VOCAB`
is the enforced blacklist and `check_no_level_one` is the gate.

**Sonification.** Only two behaviours are licensed to become audio, both inside the
parity zone Fu 2026 measured: series direction, and discrete events. Volatility and
multi-indicator comparison fell outside it, so `Finding.audible` is False for those and
`check_audio_zone` asserts it. That thesis is a single unrefereed source (see the plan's
W3), but the failure direction is the safe one either way: a spoken number is never worse
than a tone, it is only slower.

**Windows.** Every recorded series is a fixed, stale capture from 2026-09-06. Every
`Finding` carries the window it actually read, and no sentence here says "the last 90
days" about a 20-row recording.

    python3 narrate.py      # hand-computed fixtures for all four offline symbols
"""
import sources
from money import (say_change, say_count, say_date, say_percent, say_price,
                   say_rupiah)

#: Level-1 vocabulary: the marks, axes and encodings of a chart that does not exist here.
#: A template that reaches for one of these words is describing a picture instead of the
#: data, which is the single most useless thing to say to a blind reader.
LEVEL1_VOCAB = ("sumbu-x", "sumbu-y", "sumbu x", "sumbu y", "grafik batang",
                "diagram batang", "diagram garis", "candlestick", "sankey",
                "legenda", "warna biru", "warna merah", "batang berwarna",
                "x-axis", "y-axis", "bar chart", "line chart", "pie chart")

#: Language that would turn an information tool into advice. The hackathon rules ban
#: automated execution; the research records a blind investor warning specifically about
#: dependence on instant recommendations. Refused, not merely avoided.
ADVICE_VOCAB = ("beli sekarang", "jual sekarang", "sebaiknya beli", "sebaiknya jual",
                "target harga", "rekomendasi beli", "rekomendasi jual", "cut loss",
                "take profit", "should buy", "should sell", "price target")


class Finding:
    """One claim, its raw numbers, and the citation that has to travel with it.

    `audible` marks the two behaviours licensed for sonification. Everything else is
    spoken as a number, which is the whole point of the parity/failure split.
    """

    __slots__ = ("key", "level", "sentence", "numbers", "endpoint", "fields",
                 "as_of", "audible", "series")

    def __init__(self, key, level, sentence, numbers, endpoint, fields, as_of,
                 audible=False, series=None):
        if level not in (2, 3, 4):
            raise ValueError(f"{key}: semantic level {level} is not speakable here")
        lowered = sentence.lower()
        for word in LEVEL1_VOCAB:
            if word in lowered:
                raise ValueError(f"{key}: level-1 vocabulary {word!r} in a sentence")
        for word in ADVICE_VOCAB:
            if word in lowered:
                raise ValueError(f"{key}: advice vocabulary {word!r} in a sentence")
        self.key = key
        self.level = level
        self.sentence = sentence
        self.numbers = numbers
        self.endpoint = endpoint
        self.fields = tuple(fields)
        self.as_of = as_of
        self.audible = audible
        self.series = series

    def citation(self):
        """`(endpoint, fields, as_of)` — what `reader.py` demands before it will print."""
        return {"endpoint": self.endpoint, "fields": list(self.fields),
                "as_of": self.as_of}

    def __repr__(self):
        return f"<Finding {self.key} L{self.level} {self.sentence[:48]!r}>"


class NotDerivable(Exception):
    """The data is present but does not support this claim.

    Distinct from `sources.NotRecorded`, which means the payload was never fetched. The
    sentences differ: *belum diambil* versus *tidak cukup data*.
    """


# ---------------------------------------------------------------- 1. revenue segments

#: The node every revenue inflow ultimately feeds, by sector. Verified against the four
#: recordings: banks route `... -> Interest Income -> Net Interest Income -> Total
#: Revenue`, non-banks route `... -> Total Revenue -> Gross Profit -> ...`. Summing the
#: flat edge list instead of walking to a root double-counts every intermediate node,
#: which is how a "share of revenue" sentence quietly becomes a share of something else.
REVENUE_ROOT = {True: "Interest Income", False: "Total Revenue"}


def segment_concentration(segments, bank, top_n=3):
    """How concentrated revenue is, and in what.

    Walks the Sankey edge list to the sector's revenue root, keeps only the leaf inflows
    — nodes that are a source but never a target — and returns their shares. A leaf is
    a real business line; an intermediate node is an accounting subtotal, and counting
    one as the other is the difference between "three quarters of revenue comes from
    lending" and a number that means nothing.
    """
    edges = segments.get("edges") or []
    if not edges:
        raise NotDerivable("no revenue breakdown edges")

    root = REVENUE_ROOT[bool(bank)]
    targets = {edge["target"] for edge in edges}
    inflows = [edge for edge in edges
               if edge["target"] == root and edge["source"] not in targets]
    if not inflows:
        # Some issuers route everything through an intermediate; fall back to the other
        # root rather than inventing a number, and say so if that fails too.
        root = REVENUE_ROOT[not bank]
        inflows = [edge for edge in edges
                   if edge["target"] == root and edge["source"] not in targets]
    if not inflows:
        raise NotDerivable(f"no leaf inflows reach a revenue root in {len(edges)} edges")

    total = sum(edge["value"] for edge in inflows)
    if not total:
        raise NotDerivable("revenue inflows sum to zero")

    ranked = sorted(({"name": edge["source"], "value": edge["value"],
                      "share": edge["value"] / total} for edge in inflows),
                    key=lambda item: item["share"], reverse=True)
    year = segments.get("financial_year")
    top = ranked[0]
    head = ranked[:top_n]
    covered = sum(item["share"] for item in head)

    sentence = (
        f"Pada tahun buku {year}, {say_percent(top['share'])} pendapatan berasal dari "
        f"{top['name']}, yaitu {say_rupiah(top['value'])} dari total "
        f"{say_rupiah(total)}.")
    if len(ranked) > 1:
        sentence += (f" {say_count(len(head), 'sumber').capitalize()} teratas "
                     f"menyumbang {say_percent(covered)}.")

    return Finding(
        key="segment_concentration",
        level=3,
        sentence=sentence,
        numbers={"root": root, "total": total, "ranked": ranked,
                 "financial_year": year},
        endpoint=sources.ENDPOINT["segments"],
        fields=("revenue_breakdown", "financial_year"),
        # A single financial year, never a trend. `sources.refuse_multiyear_segments`
        # explains why the trend sentence cannot be built at all.
        as_of=f"tahun buku {year}",
    )


# --------------------------------------------------------------------- 2. price trend


def price_trend(rows, symbol):
    """Direction, size and extremes of the recorded price window.

    Deliberately says "20 hari bursa" and names both dates, because the recordings hold
    20 rows and not the 90 days the research document assumed. Sonifiable: this is a
    series direction, which is inside the measured parity zone.
    """
    rows = [row for row in rows if row.get("close") is not None]
    if len(rows) < 2:
        raise NotDerivable("fewer than two price rows")
    rows = sorted(rows, key=lambda row: row["date"])
    first, last = rows[0], rows[-1]
    change = (last["close"] - first["close"]) / first["close"]
    high = max(rows, key=lambda row: row["close"])
    low = min(rows, key=lambda row: row["close"])

    sentence = (
        f"Selama {say_count(len(rows), 'hari bursa')} terakhir yang terekam, "
        f"{say_date(first['date'])} sampai {say_date(last['date'])}, harga "
        f"{symbol} {say_change(change)}, dari {say_price(first['close'])} ke "
        f"{say_price(last['close'])}. Tertinggi {say_price(high['close'])} pada "
        f"{say_date(high['date'])}, terendah {say_price(low['close'])} pada "
        f"{say_date(low['date'])}.")

    return Finding(
        key="price_trend",
        level=3,
        sentence=sentence,
        numbers={"first": first, "last": last, "change": change,
                 "high": high, "low": low, "n": len(rows)},
        endpoint=sources.ENDPOINT["daily"],
        fields=("close", "date"),
        as_of=f"{first['date']} sampai {last['date']}",
        audible=True,
        series=[row["close"] for row in rows],
    )


# -------------------------------------------------------------------- 3. foreign flow


def _longest_run(values):
    """(sign, length, start_index) of the longest consecutive same-sign run."""
    best = (0, 0, 0)
    sign = 0
    length = 0
    start = 0
    for index, value in enumerate(values):
        current = (value > 0) - (value < 0)
        if current and current == sign:
            length += 1
        else:
            sign, length, start = current, 1, index
        if current and length > best[1]:
            best = (sign, length, start)
    return best


def flow_runs(rows, window, symbol):
    """Cumulative foreign flow, and the longest unbroken buying or selling streak.

    This is the one series where the research document's "90 hari" survives contact with
    the recordings: `/v2/foreign-flow/` was captured across 62 trading days from
    2026-06-07 to 2026-09-05. Sonifiable — series direction.
    """
    rows = sorted((row for row in rows if row.get("net_foreign_inflow") is not None),
                  key=lambda row: row["date"])
    if len(rows) < 2:
        raise NotDerivable("fewer than two foreign-flow rows")
    values = [row["net_foreign_inflow"] for row in rows]
    cumulative = sum(values)
    sign, length, start = _longest_run(values)

    direction = "masuk" if cumulative > 0 else "keluar"
    sentence = (
        f"Sepanjang {say_count(len(rows), 'hari bursa')} dari {say_date(window[0])} "
        f"sampai {say_date(window[1])}, dana asing bersih {direction} "
        f"{say_rupiah(abs(cumulative))}.")
    if length >= 3:
        streak = "membeli" if sign > 0 else "menjual"
        sentence += (f" Rentetan terpanjang: asing {streak} "
                     f"{say_count(length, 'hari')} berturut-turut mulai "
                     f"{say_date(rows[start]['date'])}.")

    return Finding(
        key="flow_runs",
        level=3,
        sentence=sentence,
        numbers={"cumulative": cumulative, "run_sign": sign, "run_length": length,
                 "run_start": rows[start]["date"], "n": len(rows),
                 "first_date": rows[0]["date"], "last_date": rows[-1]["date"]},
        endpoint=sources.ENDPOINT["foreign_flow"],
        fields=("net_foreign_inflow", "date"),
        as_of=f"{window[0]} sampai {window[1]}",
        audible=True,
        series=values,
    )


# ------------------------------------------------------------------------ 4. ownership

#: Investor classes rendered in Indonesian, so the sentence is speakable rather than a
#: field name read aloud.
CLASS_NAMES = {
    "individual": "individu", "corporate": "korporasi",
    "mutual_fund": "reksa dana", "pension_fund": "dana pensiun",
    "insurance": "asuransi", "financial_institutions": "lembaga keuangan",
    "securities_companies": "perusahaan sekuritas", "foundation": "yayasan",
    "other": "lainnya",
}


#: A class holding less than this at the end of the window is noise, not a finding.
#: `lembaga keuangan domestik` drifting from 0.01% to 0.01% for seven months is a
#: perfectly real run and tells a listener nothing, and it crowds out the class that
#: actually moved. Kept in `numbers` for the table, kept out of the ranking.
MATERIAL_SHARE = 0.005
MATERIAL_MOVE = 0.001


def ownership_runs(panel, min_run=3):
    """Which investor classes moved in one direction for consecutive months.

    The eight-month recorded panel is what makes this derivable at all, and it is the
    sentence the research document promised — *"dana pensiun asing membeli empat bulan
    berturut-turut sementara individu domestik menjual"*. Not sonifiable: this is a
    multi-series comparison, which is outside the measured parity zone, so it is spoken.
    """
    months = sorted(panel)
    if len(months) < min_run + 1:
        raise NotDerivable(f"ownership panel has only {len(months)} months")

    runs = []
    # `other` is a residual bucket, not an investor type. A sentence that opens with
    # "lainnya asing" tells a listener nothing about who is buying, so it stays in
    # `numbers` for the table and never leads the sentence.
    for cls in sources.INVESTOR_CLASSES:
        if cls == "other":
            continue
        for origin in ("local", "foreign"):
            shares = [panel[month][cls].get(origin) for month in months]
            if any(share is None for share in shares):
                continue
            deltas = [b - a for a, b in zip(shares, shares[1:])]
            sign, length, start = _longest_run(deltas)
            move = abs(shares[start + length] - shares[start])
            if length >= min_run:
                runs.append({
                    "material": (shares[start + length] >= MATERIAL_SHARE
                                 and move >= MATERIAL_MOVE),
                    "move": move,
                    "cls": cls, "origin": origin, "sign": sign, "length": length,
                    "from_month": months[start], "to_month": months[start + length],
                    "from_share": shares[start], "to_share": shares[start + length],
                })
    if not runs:
        raise NotDerivable(f"no class moved one way for {min_run} months running")

    # Size of the move leads the ranking, length breaks the tie: a listener wants to know
    # who moved, not who moved for the most consecutive months by a rounding error.
    runs.sort(key=lambda run: (run["material"], run["move"], run["length"]), reverse=True)
    headline = [run for run in runs if run["material"]] or runs
    parts = []
    for run in headline[:2]:
        who = f"{CLASS_NAMES[run['cls']]} {'asing' if run['origin'] == 'foreign' else 'domestik'}"
        verb = "menambah" if run["sign"] > 0 else "mengurangi"
        parts.append(
            f"{who} {verb} kepemilikan {say_count(run['length'], 'bulan')} "
            f"berturut-turut, dari {say_percent(run['from_share'])} pada "
            f"{say_date(run['from_month'])} ke {say_percent(run['to_share'])} pada "
            f"{say_date(run['to_month'])}")

    joined = " sementara ".join(parts) + "."
    return Finding(
        key="ownership_runs",
        level=3,
        # Not `.capitalize()` — that lowercases everything after the first letter and
        # turns "31 Agustus" into "31 agustus", which a screen reader reads differently.
        sentence=joined[:1].upper() + joined[1:],
        numbers={"runs": runs, "months": months},
        endpoint=sources.ENDPOINT["shareholders"],
        fields=tuple(f"{cls}_l" for cls in sources.INVESTOR_CLASSES)
               + tuple(f"{cls}_f" for cls in sources.INVESTOR_CLASSES)
               + ("total_l", "total_f", "date"),
        as_of=f"{months[0]} sampai {months[-1]}",
    )


# ----------------------------------------------------------------------- 5. financials


def quarterly_change(rows, symbol):
    """Revenue and earnings quarter on quarter, with the capex field the payload has.

    The capex slot is sector-dependent — banks report
    `realized_capital_goods_investment`, everyone else `capital_expenditure` — and the
    citation names whichever one the payload actually used, so a listener who asks where
    the number came from gets the API's field name, not this product's invention.
    """
    rows = [row for row in rows if row.get("date")]
    if len(rows) < 2:
        raise NotDerivable("fewer than two quarters")
    rows = sorted(rows, key=lambda row: row["date"])
    latest, previous = rows[-1], rows[-2]

    def delta(field):
        old, new = previous.get(field), latest.get(field)
        if not old or new is None:
            return None
        return (new - old) / abs(old)

    revenue_change = delta("revenue")
    earnings_change = delta("earnings")
    capex_field = latest.get("capex_source_field")

    sentence = (
        f"Pada kuartal yang berakhir {say_date(latest['date'])}, pendapatan "
        f"{say_rupiah(latest.get('revenue'))} ({say_change(revenue_change)} dari "
        f"kuartal sebelumnya) dan laba {say_rupiah(latest.get('earnings'))} "
        f"({say_change(earnings_change)}).")
    if latest.get("capex") is not None:
        sentence += (f" Belanja modal {say_rupiah(latest['capex'])}, dilaporkan pada "
                     f"field {capex_field}.")

    return Finding(
        key="quarterly_change",
        level=3,
        sentence=sentence,
        numbers={"latest": latest, "previous": previous,
                 "revenue_change": revenue_change,
                 "earnings_change": earnings_change,
                 "quarters": [row["date"] for row in rows]},
        endpoint=sources.ENDPOINT["quarterly"],
        fields=("revenue", "earnings", "date") + ((capex_field,) if capex_field else ()),
        as_of=latest["date"],
    )


# ---------------------------------------------------------------------------- 6. peers


def peer_rank(report, symbol):
    """Where this issuer sits inside its peer set on the metrics the payload carries.

    Raises `sources.NotRecorded` for everything but BBCA, because that is the truth:
    the only peers payload ever paid for is inside the one bare company report. The
    caller turns that into *belum diambil* and names the endpoint, rather than letting
    the mock hand back another company's peers under this company's name.
    """
    peers = (report or {}).get("peers") or []
    block = peers[0].get("peers_data", {}) if peers else {}
    companies = block.get("companies") or []
    if not companies:
        raise NotDerivable("peers payload carries no companies")

    self_row = next((row for row in companies
                     if sources.bare_symbol(row.get("symbol")) == symbol), None)
    if self_row is None:
        raise NotDerivable(f"{symbol} is not inside its own peer set")

    parts = []
    numbers = {"n_peers": len(companies)}
    for field, label, ascending in (("pe_ttm", "rasio harga terhadap laba", True),
                                    ("pb_mrq", "rasio harga terhadap nilai buku", True),
                                    ("market_cap", "kapitalisasi pasar", False)):
        rated = [row for row in companies if row.get(field) is not None]
        if len(rated) < 2 or self_row.get(field) is None:
            continue
        rated.sort(key=lambda row: row[field], reverse=not ascending)
        rank = 1 + next(index for index, row in enumerate(rated)
                        if sources.bare_symbol(row.get("symbol")) == symbol)
        numbers[field] = {"value": self_row[field], "rank": rank, "of": len(rated)}
        parts.append(f"{label} peringkat {say_count(rank, '')}".strip()
                     + f" dari {say_count(len(rated), 'perusahaan')}")

    if not parts:
        raise NotDerivable("no comparable peer metric")

    return Finding(
        key="peer_rank",
        level=3,
        sentence=(f"Dibanding {say_count(len(companies) - 1, 'perusahaan')} sejenis, "
                  f"{symbol} berada di " + ", ".join(parts) + "."),
        numbers=numbers,
        endpoint=sources.ENDPOINT["peers"],
        fields=("peers_data.companies.pe_ttm", "peers_data.companies.pb_mrq",
                "peers_data.companies.market_cap"),
        as_of=str(companies[0].get("year") or "tahun terakhir"),
    )


# ------------------------------------------------------------------------- the summary


def summary(findings, overview):
    """Two to three level-3 sentences, before any detail.

    VoxLens (DOI 10.1145/3491102.3517431, 21 screen-reader users) moved information
    extraction accuracy from 34% to 75% with a summary mode. Summary first is not a
    stylistic preference; it is the single largest measured effect in this literature.
    """
    order = ("segment_concentration", "price_trend", "flow_runs", "ownership_runs",
             "quarterly_change", "peer_rank")
    by_key = {finding.key: finding for finding in findings}
    chosen = [by_key[key] for key in order if key in by_key][:3]
    if not chosen:
        raise NotDerivable("nothing to summarise")

    # Issuer names already end in "Tbk." on IDX, so a blindly appended full stop
    # gives a screen reader "Tbk dot dot" to read out.
    name = (overview.get("company_name") or overview.get("symbol") or "").rstrip(".")
    head = (f"{name}. Kapitalisasi pasar {say_rupiah(overview.get('market_cap'))}."
            if overview.get("market_cap") else f"{name}.")
    return Finding(
        key="summary",
        level=3,
        sentence=head + " " + " ".join(finding.sentence for finding in chosen),
        numbers={"from": [finding.key for finding in chosen]},
        endpoint=sources.ENDPOINT["overview"],
        fields=("company_name", "market_cap"),
        as_of=overview.get("latest_close_date") or "rekaman 2026-09-06",
    )


# ------------------------------------------------------------------------------ gates


def _bag(symbol, source="recorded"):
    """Everything one symbol needs, loaded once. Used by the gates and by `reader.py`."""
    overview = sources.normalize_overview(
        sources.load(source, "overview", symbol), source, symbol)
    bank = sources.is_bank(overview)
    flow_payload = sources.load(source, "foreign_flow", symbol)
    flow_rows = [sources.normalize_flow(row) for row in sources.rows_of(flow_payload)]
    if source == "synth":
        flow_rows = [row for row in flow_rows if row["symbol"] == symbol]
    return {
        "symbol": symbol,
        "source": source,
        "overview": overview,
        "bank": bank,
        "segments": sources.normalize_segments(
            sources.load(source, "segments", symbol), source, symbol),
        "daily": [sources.normalize_daily(row)
                  for row in sources.rows_of(sources.load(source, "daily", symbol))],
        "panel": sources.normalize_shareholders(
            sources.load(source, "shareholders", symbol)),
        "quarters": [sources.normalize_quarter(row)
                     for row in sources.rows_of(
                         sources.load(source, "quarterly", symbol))],
        "flow": flow_rows,
        "flow_window": sources.flow_window(flow_payload),
    }


def derive(bag):
    """Every finding this bag supports, and why each missing one is missing."""
    findings, gaps = [], {}
    attempts = (
        ("segment_concentration",
         lambda: segment_concentration(bag["segments"], bag["bank"])),
        ("price_trend", lambda: price_trend(bag["daily"], bag["symbol"])),
        ("flow_runs",
         lambda: flow_runs(bag["flow"], bag["flow_window"], bag["symbol"])),
        ("ownership_runs", lambda: ownership_runs(bag["panel"])),
        ("quarterly_change", lambda: quarterly_change(bag["quarters"], bag["symbol"])),
        ("peer_rank", lambda: peer_rank(
            sources.load(bag["source"], "peers", bag["symbol"]), bag["symbol"])),
    )
    for key, build in attempts:
        try:
            finding = build()
            # The templates carry `{symbol}`; a listener asking where a number came from
            # needs the path they could actually call, not the pattern it was built from.
            finding.endpoint = finding.endpoint.format(symbol=bag["symbol"])
            findings.append(finding)
        except sources.NotRecorded:
            dataset = {"peer_rank": "peers"}.get(key, key.split("_")[0])
            gaps[key] = ("belum diambil",
                         sources.ENDPOINT.get(dataset, "").format(symbol=bag["symbol"]))
        except NotDerivable as exc:
            gaps[key] = ("tidak cukup data", str(exc))
    return findings, gaps


def check_derivations():
    """Every offline symbol must produce the five endpoint-backed findings."""
    failures = []
    for symbol in sources.OFFLINE_SYMBOLS:
        findings, gaps = derive(_bag(symbol))
        keys = {finding.key for finding in findings}
        expected = {"segment_concentration", "price_trend", "flow_runs",
                    "ownership_runs", "quarterly_change"}
        missing = expected - keys
        if missing:
            failures.append(f"{symbol}: missing {sorted(missing)} — {gaps}")
        if symbol == "BBCA" and "peer_rank" not in keys:
            failures.append(f"BBCA: peer_rank should be derivable — {gaps.get('peer_rank')}")
        if symbol != "BBCA" and "peer_rank" in keys:
            failures.append(f"{symbol}: peer_rank was derived without a paid payload")
    return failures, len(sources.OFFLINE_SYMBOLS) * 2


def check_segment_root():
    """Bank and non-bank revenue must be walked to different roots, with shares that sum to one."""
    failures = []
    seen = {}
    for symbol in sources.OFFLINE_SYMBOLS:
        bag = _bag(symbol)
        finding = segment_concentration(bag["segments"], bag["bank"])
        root = finding.numbers["root"]
        shares = sum(item["share"] for item in finding.numbers["ranked"])
        seen[symbol] = (root, len(finding.numbers["ranked"]))
        if abs(shares - 1.0) > 1e-9:
            failures.append(f"{symbol}: leaf shares sum to {shares}, not 1")
        expected_root = "Interest Income" if bag["bank"] else "Total Revenue"
        if root != expected_root:
            failures.append(f"{symbol}: walked to {root}, expected {expected_root}")
        # An intermediate node reaching the leaf list is the double-count bug.
        targets = {edge["target"] for edge in bag["segments"]["edges"]}
        for item in finding.numbers["ranked"]:
            if item["name"] in targets:
                failures.append(f"{symbol}: {item['name']!r} is an accounting subtotal, "
                                f"not a business line")
    print("        revenue root · " +
          " · ".join(f"{s}={r} ({n} leaf)" for s, (r, n) in sorted(seen.items())))
    return failures, len(sources.OFFLINE_SYMBOLS) * 3


def check_run_detector():
    """`_longest_run` on hand-built series, including the sign-flip and all-zero edges."""
    failures = []
    cases = [
        ([1, 1, 1, -1], (1, 3, 0)),
        ([-1, -1, 2, 2, 2, 2], (1, 4, 2)),
        ([0, 0, 0], (0, 0, 0)),
        ([1, 0, 1, 1], (1, 2, 2)),
        ([], (0, 0, 0)),
    ]
    for values, expected in cases:
        got = _longest_run(values)
        if got != expected:
            failures.append(f"_longest_run({values}) = {got}, expected {expected}")
    return failures, len(cases)


def check_no_level_one():
    """No sentence any symbol produces may contain level-1 or advice vocabulary."""
    failures = []
    checked = 0
    for symbol in sources.OFFLINE_SYMBOLS:
        bag = _bag(symbol)
        findings, _ = derive(bag)
        findings.append(summary(findings, bag["overview"]))
        for finding in findings:
            checked += 1
            lowered = finding.sentence.lower()
            for word in LEVEL1_VOCAB + ADVICE_VOCAB:
                if word in lowered:
                    failures.append(f"{symbol}/{finding.key}: {word!r} reached output")
            if finding.level == 1:
                failures.append(f"{symbol}/{finding.key}: level 1 was emitted")
    return failures, checked


def check_audio_zone():
    """Only series direction may become audio. Volatility and comparisons stay spoken.

    Fu 2026 measured parity for trend and event detection and a real gap for volatility
    and concurrent multi-indicator judgements. This gate is what keeps a later change
    from quietly routing a comparison into the audio channel.
    """
    failures = []
    checked = 0
    licensed = {"price_trend", "flow_runs"}
    for symbol in sources.OFFLINE_SYMBOLS:
        for finding in derive(_bag(symbol))[0]:
            checked += 1
            if finding.audible and finding.key not in licensed:
                failures.append(f"{symbol}/{finding.key}: sonified outside the parity zone")
            if finding.audible and not finding.series:
                failures.append(f"{symbol}/{finding.key}: audible with no series to play")
            if finding.key == "ownership_runs" and finding.audible:
                failures.append(f"{symbol}: a multi-series comparison was sonified")
    return failures, checked


def check_citations():
    """Every finding names an endpoint, at least one field, and the window it read."""
    failures = []
    checked = 0
    for symbol in sources.OFFLINE_SYMBOLS:
        bag = _bag(symbol)
        findings, _ = derive(bag)
        findings.append(summary(findings, bag["overview"]))
        for finding in findings:
            checked += 1
            citation = finding.citation()
            if not citation["endpoint"].startswith("/v2/"):
                failures.append(f"{symbol}/{finding.key}: endpoint {citation['endpoint']!r}")
            if not citation["fields"]:
                failures.append(f"{symbol}/{finding.key}: no field named")
            if not citation["as_of"]:
                failures.append(f"{symbol}/{finding.key}: no window stated")
    return failures, checked


def main():
    results = [("derivations", *check_derivations()),
               ("segment root walk", *check_segment_root()),
               ("run detector", *check_run_detector()),
               ("no level-1 language", *check_no_level_one()),
               ("audio parity zone", *check_audio_zone()),
               ("citations", *check_citations())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)

    if not failed:
        bag = _bag("BBCA")
        findings, _ = derive(bag)
        print("\n" + summary(findings, bag["overview"]).sentence)
    else:
        print(f"\n{failed} derivation failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
