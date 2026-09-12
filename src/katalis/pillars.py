#!/usr/bin/env python3
"""
The four pillars: concentration, volume, momentum, catalyst — and the verdict they produce.

Pure derivation. No I/O, no HTTP, no file paths: it takes rows that `sources.py` already
normalized and returns `Pillar` records whose every figure carries the `(endpoint, field)`
it came from. That is what lets the card cite itself and what lets a judge replay a number
without running the product.

    from pillars import assess
    result = assess(bag, symbol="BBCA", as_of="2026-08-14")

Three rules the file enforces rather than documents:

  1. **A figure that cannot be derived is `None` with a reason, never a guess.** Free float
     absorbed needs lot counts; on a source without them the pillar says so on the card.
  2. **Nothing reads past `as_of`.** Every series is cut before it is used, in one place
     (`upto`), so a replay cannot quietly see the future it is being tested against.
  3. **A verdict is a statement about the shape of the tape, never about what to do.**
     There is no threshold in this file that turns into "buy" or "sell".

    python3 pillars.py     # the gates, including a synthetic single-buyer tape
"""
import math
from dataclasses import dataclass, field

import sources
import thresholds as T

#: Card vocabulary. Indonesian, because the reader is.
TENANG = "tenang"
WASPADA = "waspada"
BAHAYA = "bahaya"
TAK_TERUKUR = "tidak terukur"

#: The cases the gates run end to end. `synth/` carries 90 trading days per symbol, which is
#: what a full baseline needs; `recorded/LIFE` is the real IDX tape the whole product is argued
#: from, and leaving it out of the gates is what let "73 green" say nothing about the one card
#: anybody is asked to believe. Every card gate iterates all of these — none may index [0].
DEMO_CASES = (("synth", "KVDN", "2026-09-04"),
              ("recorded", "LIFE", "2026-09-01"))


@dataclass
class Figure:
    """One number, and where it came from. A figure without a citation cannot be built."""
    name: str
    value: object
    endpoint: str
    fields: tuple
    unit: str = ""
    note: str = ""

    def __post_init__(self):
        if not self.endpoint or not self.fields:
            raise ValueError(f"figure {self.name!r} has no citation")


@dataclass
class Pillar:
    name: str
    status: str
    headline: str
    figures: list = field(default_factory=list)
    unchecked: list = field(default_factory=list)

    def value(self, name):
        for fig in self.figures:
            if fig.name == name:
                return fig.value
        return None


@dataclass
class Rejected(Exception):
    """A symbol that cannot be scored, with the named reason it cannot."""
    reason: str
    detail: str = ""

    def __str__(self):
        return f"{self.reason}: {self.detail}" if self.detail else self.reason


# ------------------------------------------------------------------------------ helpers

def upto(rows, as_of, key="date"):
    """Every row on or before `as_of`. The single place the as-of cut happens."""
    if not as_of:
        return list(rows)
    return [r for r in rows if (r.get(key) or "") <= as_of]


def window_dates(daily_rows, as_of, size):
    """The last `size` trading days ending at `as_of`, taken from the price series itself.

    Trading days come from the data rather than from a calendar, so a holiday or a halt
    shortens the window instead of silently reaching further back than it should.
    """
    dates = [r["date"] for r in upto(daily_rows, as_of)]
    return dates[-size:] if dates else []


def median(values):
    ordered = sorted(values)
    n = len(ordered)
    if not n:
        return None
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def robust_z(value, series, mad_floor):
    """0.6745 * (x - median) / max(MAD, floor).

    Robust rather than standard because the thing being measured — a spike — is exactly
    what would inflate a standard deviation and hide itself.
    """
    if value is None or not series:
        return None
    med = median(series)
    mad = median([abs(x - med) for x in series])
    scale = max(mad if mad is not None else 0.0, mad_floor)
    if scale <= 0:
        return None
    return 0.6745 * (value - med) / scale


def log_returns(rows):
    """(date, log return) pairs, skipping any day whose neighbours are not both positive."""
    out = []
    for prev, cur in zip(rows, rows[1:]):
        a, b = prev.get("close"), cur.get("close")
        if a and b and a > 0 and b > 0:
            out.append((cur["date"], math.log(b / a)))
    return out


def ols_beta(stock, market):
    """Slope of stock on market over paired returns. None when the pair is too short."""
    pairs = [(m, s) for (d, s), m in zip(stock, market) if m is not None]
    if len(pairs) < 10:
        return None
    mx = sum(m for m, _ in pairs) / len(pairs)
    my = sum(s for _, s in pairs) / len(pairs)
    var = sum((m - mx) ** 2 for m, _ in pairs)
    if var <= 0:
        return None
    cov = sum((m - mx) * (s - my) for m, s in pairs)
    return cov / var


def align(stock_returns, index_returns):
    """Index returns lined up with the stock's own trading days, None where the index is absent."""
    index_by_date = dict(index_returns)
    return [index_by_date.get(date) for date, _ in stock_returns]


# ------------------------------------------------------------------------------- pillars

def concentration(flow_rows, registry, window, free_float=None, shares=None,
                  shares_fields=(), shares_exact=True):
    """Pilar 1 — who lifted it: how few hands, which origin, which cohort, how much float.

    Buyers are brokers whose summed net is positive across the window. Sellers are not the
    question being asked: "who bought this" has an answer even on a day when the same desk
    also sold, and netting is what separates the two.
    """
    endpoint = sources.ENDPOINT["broker_flow"]
    fields = ("summary[].broker_code", "summary[].nval", "summary[].nlot",
              "summary[].bavg_per_share")
    rows = [r for r in flow_rows if r["date"] in set(window)]
    if not rows:
        raise Rejected("tanpa_broker", T.REJECTS["tanpa_broker"])

    net_by_broker, lot_by_broker, price_by_broker = {}, {}, {}
    for row in rows:
        code = row["broker_code"]
        net_by_broker[code] = net_by_broker.get(code, 0) + (row["net_idr"] or 0)
        if row["net_lot"] is not None:
            lot_by_broker[code] = lot_by_broker.get(code, 0) + row["net_lot"]
        if row["avg_buy_price"]:
            price_by_broker.setdefault(code, []).append(row["avg_buy_price"])

    buyers = {c: v for c, v in net_by_broker.items() if v > 0}
    total = sum(buyers.values())
    if not buyers or total <= 0:
        return Pillar("konsentrasi", TENANG,
                      "Tidak ada sisi pembeli bersih dalam jendela ini.",
                      [Figure("pembeli", 0, endpoint, fields)],
                      ["siapa yang menjual — pertanyaan lain, tidak diperiksa di sini"])

    shares_of = {c: v / total for c, v in buyers.items()}
    top_code = max(buyers, key=buyers.get)
    top1 = shares_of[top_code]
    hhi = sum(s * s for s in shares_of.values())
    n_eff = 1 / hhi if hhi else None

    foreign = sum(v for c, v in buyers.items() if (registry.get(c) or {}).get("is_foreign"))
    cohorts = {}
    for code, value in buyers.items():
        cohort = (registry.get(code) or {}).get("cohort") or "unknown"
        cohorts[cohort] = cohorts.get(cohort, 0) + value

    top_meta = registry.get(top_code) or {}
    top_prices = price_by_broker.get(top_code) or []
    top_avg = sum(top_prices) / len(top_prices) if top_prices else None

    # Float absorbed is the sentence no other service prints, and it needs lots. When the
    # source has none, it stays None — see the docstring's rule 1.
    absorbed = None
    if free_float and shares and lot_by_broker:  # lots are the whole point — see rule 1
        float_shares = free_float * shares
        if float_shares > 0:
            absorbed = sum(max(v, 0) for v in lot_by_broker.values()) * 100 / float_shares

    figures = [
        Figure("broker_puncak", top_code, sources.ENDPOINT["broker_flow"],
               ("summary[].broker_code",),
               note=top_meta.get("name") or "nama tidak ada di registri"),
        Figure("pangsa_puncak", top1, endpoint, ("summary[].nval",), unit="fraksi"),
        Figure("hhi", hhi, endpoint, ("summary[].nval",)),
        Figure("pembeli_efektif", n_eff, endpoint, ("summary[].nval",)),
        Figure("pangsa_asing", foreign / total, sources.ENDPOINT["brokers"],
               ("code", "is_foreign"), unit="fraksi"),
        Figure("pangsa_kohort", {k: v / total for k, v in cohorts.items()},
               sources.ENDPOINT["brokers"], ("code", "cohort")),
        Figure("net_beli_total", total, endpoint, ("summary[].nval",), unit="IDR"),
    ]
    if top_avg is not None:
        figures.append(Figure("harga_masuk_puncak", top_avg, endpoint,
                              ("summary[].bavg_per_share",), unit="IDR"))
    if absorbed is not None:
        figures.append(Figure(
            "float_terserap", absorbed, endpoint,
            ("summary[].nlot",) + tuple(shares_fields) + ("free_float",),
            unit="fraksi float",
            note="" if shares_exact else "jumlah saham diturunkan dari market_cap ÷ close, "
                                         "bukan dari outstanding_shares"))

    unchecked = []
    if absorbed is None:
        unchecked.append("persen free float yang berpindah — sumber ini tidak membawa "
                         "hitungan lot, jadi tidak dihitung, bukan diperkirakan")
    stray = sorted({r["broker_code"] for r in rows if r["broker_code"] not in registry})
    if stray:
        unchecked.append(f"asal dan kohort {len(stray)} kode broker di luar registri: "
                         f"{', '.join(stray)}")

    if top1 >= T.get("top1_dominant") and (n_eff or 99) <= T.get("neff_dominant"):
        status = BAHAYA
        headline = (f"Satu broker, {top_code} ({top_meta.get('name') or 'nama tidak diketahui'}), "
                    f"mengambil {top1:.0%} dari net beli. Pembeli efektif: {n_eff:.1f}.")
    elif (n_eff or 0) >= T.get("neff_crowd"):
        status = TENANG
        headline = (f"{n_eff:.1f} pembeli efektif — tidak ada satu tangan yang menonjol. "
                    f"Terbesar {top_code} di {top1:.0%}.")
    else:
        status = WASPADA
        headline = (f"{top_code} mengambil {top1:.0%} dari net beli; "
                    f"{n_eff:.1f} pembeli efektif.")
    return Pillar("konsentrasi", status, headline, figures, unchecked)


def volume(daily_rows, as_of, window):
    """Pilar 2 — is the turnover outside this stock's own habit, measured robustly."""
    endpoint = sources.ENDPOINT["daily"]
    rows = upto(daily_rows, as_of)
    if len(rows) < 2:
        raise Rejected("baseline_tipis", T.REJECTS["baseline_tipis"])

    in_window = [r for r in rows if r["date"] in set(window)]
    baseline = [r for r in rows if r["date"] not in set(window)][-T.get("baseline_days"):]
    if len(baseline) < 10:
        raise Rejected("baseline_tipis",
                       f"{len(baseline)} hari baseline, butuh lebih dari 10")

    logs = [math.log(r["volume"]) for r in baseline if r.get("volume") and r["volume"] > 0]
    peak = max((r["volume"] for r in in_window if r.get("volume")), default=None)
    z = robust_z(math.log(peak), logs, T.get("volume_mad_floor")) if peak and logs else None

    figures = [
        Figure("volume_puncak", peak, endpoint, ("volume",), unit="lembar"),
        Figure("volume_z", z, endpoint, ("volume",),
               note=f"baseline {len(baseline)} hari bursa"),
    ]
    if z is None:
        return Pillar("volume", TAK_TERUKUR,
                      "Volume tidak bisa dinilai: baseline tidak punya hari dengan volume positif.",
                      figures, ["z volume"])
    if z >= T.get("volume_z"):
        status, headline = BAHAYA, (f"Volume puncak {z:.1f} z di atas kebiasaannya sendiri "
                                    f"({len(baseline)} hari bursa).")
    elif z >= T.get("volume_z") * 0.6:
        status, headline = WASPADA, f"Volume naik, {z:.1f} z di atas baseline."
    else:
        status, headline = TENANG, f"Volume dalam kebiasaannya, {z:.1f} z."
    return Pillar("volume", status, headline, figures)


def momentum(daily_rows, index_rows, as_of, window):
    """Pilar 3 — how much of the move is the stock's own, once IHSG is taken out.

    The beta is shrunk towards 1 because a thin baseline will happily hand a small stock a
    beta of four, and a beta of four erases its own move by attributing it to the index.
    """
    endpoint = sources.ENDPOINT["daily"]
    rows = upto(daily_rows, as_of)
    index = upto(index_rows, as_of)
    if not index:
        raise Rejected("tanpa_indeks", T.REJECTS["tanpa_indeks"])

    stock_returns = log_returns(rows)
    index_returns = log_returns([{"date": r["date"], "close": r["close"]} for r in index])
    if len(stock_returns) < 12:
        raise Rejected("baseline_tipis", f"{len(stock_returns)} return, butuh lebih dari 12")

    in_window = set(window)
    baseline_pairs = [(d, r) for d, r in stock_returns if d not in in_window]
    baseline_pairs = baseline_pairs[-T.get("baseline_days"):]
    dead = sum(1 for _, r in baseline_pairs if r == 0)
    if baseline_pairs and dead / len(baseline_pairs) > T.get("dead_day_share"):
        raise Rejected("baseline_mati",
                       f"{dead}/{len(baseline_pairs)} hari baseline tanpa gerak")

    beta_ols = ols_beta(baseline_pairs, align(baseline_pairs, index_returns))
    shrink = T.get("beta_shrink")
    beta_eff = shrink * beta_ols + (1 - shrink) if beta_ols is not None else 1.0

    index_by_date = dict(index_returns)
    residual = {d: r - beta_eff * index_by_date.get(d, 0.0) for d, r in stock_returns}
    cum = sum(residual[d] for d in window if d in residual)
    baseline_resid = [residual[d] for d, _ in baseline_pairs if d in residual]
    z = robust_z(cum, baseline_resid, T.get("price_mad_floor") * math.sqrt(len(window) or 1))

    raw = sum(r for d, r in stock_returns if d in in_window)
    figures = [
        Figure("return_kumulatif", math.expm1(raw), endpoint, ("close",), unit="fraksi"),
        Figure("return_residual", math.expm1(cum), endpoint, ("close",), unit="fraksi",
               note="setelah gerak IHSG dikeluarkan"),
        Figure("beta_efektif", beta_eff, sources.ENDPOINT["index_daily"], ("price",),
               note="0,7*beta_OLS + 0,3" if beta_ols is not None else "baseline tipis, beta=1"),
        Figure("residual_z", z, endpoint, ("close",),
               note=f"baseline {len(baseline_resid)} hari bursa"),
    ]
    if z is None:
        return Pillar("momentum", TAK_TERUKUR, "Momentum tidak bisa dinilai dari baseline ini.",
                      figures, ["z residual"])
    if z >= T.get("resid_z"):
        status = BAHAYA
        headline = (f"Naik {math.expm1(raw):+.1%} dalam {len(window)} hari bursa; "
                    f"{math.expm1(cum):+.1%} setelah gerak IHSG dikeluarkan, {z:.1f} z.")
    elif z >= T.get("resid_z") * 0.6:
        status = WASPADA
        headline = f"Gerak sendiri {math.expm1(cum):+.1%}, {z:.1f} z di atas baseline."
    else:
        status = TENANG
        headline = (f"Geraknya sejalan pasar: {math.expm1(raw):+.1%} kotor, "
                    f"{math.expm1(cum):+.1%} sendiri, {z:.1f} z.")
    return Pillar("momentum", status, headline, figures)


def catalyst(articles, filings, actions, as_of, window):
    """Pilar 4 — is there anything that explains it, and did it arrive before or after.

    The two judgments that matter here are not fields: whether an article **precedes** the
    move or follows it, and whether it **explains** or merely reports it. The first is
    arithmetic and lives here. The second is a language judgment and belongs to the planner;
    what this function records is the temporal split and the structured evidence.
    """
    start = window[0] if window else as_of
    before, after = [], []
    for row in articles:
        stamp = (row.get("timestamp") or "")[:10]
        if not stamp or stamp > as_of:
            continue
        (before if stamp < start else after).append(row)

    material = [f for f in filings
                if (f.get("share_percentage_transaction") or 0) >= T.get("filing_material_pct")
                and (f.get("transaction_type") or "") == "buy"]
    # Cut at `as_of`, not just at `start`. The payload carries the action's own date and no
    # announcement date, so an action dated after the card cannot be shown to have been
    # knowable on the card's day — and a figure on a card dated D that comes from data dated
    # after D is the defect that makes any replay of this product invalid.
    in_window = [a for a in upto(actions, as_of) if (a.get("date") or "") >= start]

    figures = [
        Figure("artikel_mendahului", len(before), sources.ENDPOINT["news"],
               ("timestamp", "symbols")),
        Figure("artikel_mengikuti", len(after), sources.ENDPOINT["news"],
               ("timestamp", "symbols")),
        Figure("filing_material", len(material), sources.ENDPOINT["filings"],
               ("holder_name", "share_percentage_transaction", "transaction_type")),
        Figure("aksi_korporasi", len(in_window), sources.ENDPOINT["corporate_actions"],
               ("action_type", "date")),
    ]
    unchecked = ["cuaca dan fase iklim — belum dipasang",
                 "kanal di luar cakupan kami: Telegram, Stockbit, X"]

    if material:
        top = max(material, key=lambda f: f.get("share_percentage_transaction") or 0)
        return Pillar("katalis", TENANG,
                      f"{top['holder_name']} ({top['holder_type']}) menambah "
                      f"{top['share_percentage_transaction']:.2f} poin persen.",
                      figures, unchecked)
    if before:
        head = before[-1]
        return Pillar("katalis", TENANG,
                      f"Ada kabar yang mendahului: \"{head['title']}\" "
                      f"({(head.get('timestamp') or '')[:10]}).",
                      figures, unchecked)
    if after:
        return Pillar("katalis", WASPADA,
                      f"Tidak ada kabar yang mendahului lonjakan. {len(after)} artikel terbit "
                      f"SESUDAHNYA dan melaporkan kenaikannya.",
                      figures, unchecked)
    if in_window:
        return Pillar("katalis", WASPADA,
                      f"Tidak ada kabar; {len(in_window)} aksi korporasi di jendela.",
                      figures, unchecked)
    return Pillar("katalis", BAHAYA,
                  "Tidak ada apa pun yang menjelaskannya: nol artikel, nol filing material, "
                  "nol aksi korporasi.", figures, unchecked)


def suspension_history(rows, as_of):
    """Pilar-level context, not a pillar: has the exchange ever halted this symbol before now.

    Returns `None` when it never has, so the card stays silent rather than printing a zero.
    `rows` must already be cut at `as_of` — `bag_from` does it, and
    `check_suspension_modifier_respects_as_of` is what proves it stayed done.
    """
    seen = [r for r in rows if (r.get("suspension_date") or "") <= as_of]
    if not seen:
        return None
    last = max(r["suspension_date"] for r in seen)
    return Figure("pernah_disuspensi", len(seen), sources.ENDPOINT["suspensions"],
                  ("symbol", "suspension_date"),
                  note=f"terakhir {last}")


# ------------------------------------------------------------------------------- verdict

def verdict(pillars, free_float=None, suspensions=None):
    """Mechanical, ordered, always filled. Never advice — see the module docstring, rule 3."""
    by_name = {p.name: p for p in pillars}
    conc = by_name.get("konsentrasi")
    vol = by_name.get("volume")
    mom = by_name.get("momentum")
    cat = by_name.get("katalis")

    modifiers = []
    if free_float is not None and free_float < T.get("thin_float"):
        modifiers.append(f"FLOAT TIPIS · free float {free_float:.1%}")
    absorbed = conc.value("float_terserap") if conc else None
    if absorbed is not None and absorbed >= T.get("float_absorbed"):
        modifiers.append(f"FLOAT TERSERAP · {absorbed:.1%} berpindah tangan")
    if conc and (conc.value("pangsa_asing") or 0) >= T.get("foreign_share_in"):
        modifiers.append(f"ASING DOMINAN · {conc.value('pangsa_asing'):.0%} dari net beli")
    if suspensions is not None and suspensions.value:
        modifiers.append(f"PERNAH DISUSPENSI · {suspensions.note.split()[-1]}")

    danger = [p.name for p in pillars if p.status == BAHAYA]
    if conc and conc.status == BAHAYA and mom and mom.status in (BAHAYA, WASPADA):
        name = "SATU PEMBELI DOMINAN"
    elif len(danger) >= 3:
        name = "TIGA PILAR MENYALA"
    elif conc and conc.status == BAHAYA:
        name = "TERKONSENTRASI, TANPA GERAK LUAR BIASA"
    elif mom and mom.status == BAHAYA and cat and cat.status == BAHAYA:
        name = "BERGERAK TANPA PENJELASAN"
    elif danger:
        name = "SATU PILAR MENYALA"
    else:
        name = "TIDAK ADA YANG MENONJOL"
    return name, modifiers


def assess(bag, symbol, as_of):
    """Run all four pillars over one pre-fetched bag of rows. Raises Rejected with a reason."""
    daily_rows = bag["daily"]
    if not daily_rows:
        raise Rejected("baseline_tipis", "tidak ada deret harga")
    window = window_dates(daily_rows, as_of, T.get("event_window"))
    if not window:
        raise Rejected("baseline_tipis", f"tidak ada hari bursa sampai {as_of}")

    pillars = [
        concentration(bag["flow"], bag["registry"], window,
                      free_float=bag.get("free_float"), shares=bag.get("shares"),
                      shares_fields=bag.get("shares_fields") or (),
                      shares_exact=bag.get("shares_exact", True)),
        volume(daily_rows, as_of, window),
        momentum(daily_rows, bag["index"], as_of, window),
        catalyst(bag.get("news") or [], bag.get("filings") or [],
                 bag.get("actions") or [], as_of, window),
    ]
    halts = suspension_history(bag.get("suspensions") or [], as_of)
    name, modifiers = verdict(pillars, bag.get("free_float"), halts)
    return {"symbol": sources.bare(symbol), "as_of": as_of, "window": window,
            "verdict": name, "modifiers": modifiers, "pillars": pillars,
            # Card-level figures: they cite a modifier on the headline rather than a pillar,
            # and the FIELD block has to print their endpoint like any other.
            "modifier_figures": [f for f in (halts,) if f is not None]}


def bag_from(source, symbol, as_of, cut=True):
    """Everything the pillars need, read locally. Missing datasets degrade to empty lists.

    `cut=False` builds the same bag with every as-of cut removed. Nothing in the product
    calls it that way — `check_as_of_does_not_leak` does, because the only honest way to
    prove a cut happened is to build the card without it and show the card did not move.
    """
    def maybe(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (sources.NotRecorded, ValueError, KeyError):
            return None

    def cutoff(rows):
        return upto(rows, as_of) if cut else list(rows)

    end = as_of if cut else None
    shares, shares_fields, shares_exact = (maybe(sources.shares_outstanding, source, symbol)
                                           or (None, (), False))
    return {
        "daily": cutoff(sources.daily(source, symbol)),
        "index": cutoff(sources.index_daily(source)),
        "flow": cutoff(maybe(sources.broker_flow, source, symbol) or []),
        "registry": maybe(sources.registry_index, source) or {},
        "free_float": maybe(sources.free_float, source, symbol),
        "shares": shares, "shares_fields": shares_fields, "shares_exact": shares_exact,
        "news": maybe(sources.news_for, source, symbol, None, end) or [],
        "filings": maybe(sources.filings_for, source, symbol, None, end) or [],
        "actions": cutoff(maybe(sources.corporate_actions, source, symbol) or []),
        "suspensions": maybe(sources.suspensions_for, source, symbol, end) or [],
    }


# --------------------------------------------------------------------------------- gates

def _tape(shares_by_broker, date="2026-08-14"):
    return [{"date": date, "broker_code": code, "net_idr": value, "net_lot": None,
             "buy_idr": max(value, 0), "sell_idr": 0, "buy_lot": None, "buy_freq": None,
             "avg_buy_price": 100.0, "origin_inline": None, "cohort_inline": None}
            for code, value in shares_by_broker.items()]


def check_single_buyer():
    """A tape with exactly one buyer must read as one buyer, not as a rounding artefact."""
    failures = []
    registry = {"YP": {"name": "Satu", "is_foreign": False, "cohort": "retail"}}
    pillar = concentration(_tape({"YP": 1_000_000}), registry, ["2026-08-14"])
    if abs(pillar.value("pangsa_puncak") - 1.0) > 1e-9:
        failures.append(f"single buyer top1 = {pillar.value('pangsa_puncak')}, expected 1.0")
    if abs(pillar.value("pembeli_efektif") - 1.0) > 1e-9:
        failures.append(f"single buyer N_eff = {pillar.value('pembeli_efektif')}, expected 1.0")
    if pillar.status != BAHAYA:
        failures.append(f"single buyer read as {pillar.status}")

    even = concentration(_tape({c: 100 for c in "ABCDEFGHIJ"}),
                         {c: {"name": c, "is_foreign": False, "cohort": "retail"}
                          for c in "ABCDEFGHIJ"}, ["2026-08-14"])
    if abs(even.value("pembeli_efektif") - 10.0) > 1e-6:
        failures.append(f"ten equal buyers gave N_eff {even.value('pembeli_efektif')}")
    if even.status != TENANG:
        failures.append(f"ten equal buyers read as {even.status}")
    return failures, 5


def check_sellers_do_not_count():
    """Net sellers must not dilute the buyer concentration — the question is who bought."""
    failures = []
    registry = {c: {"name": c, "is_foreign": False, "cohort": "retail"} for c in "ABC"}
    pillar = concentration(_tape({"A": 1000, "B": -900, "C": -100}), registry, ["2026-08-14"])
    if abs(pillar.value("pangsa_puncak") - 1.0) > 1e-9:
        failures.append("a net seller was counted on the buying side")
    return failures, 1


def check_no_lots_no_float():
    """Rule 1: without lot counts, float absorbed is absent and said to be absent."""
    failures = []
    registry = {"YP": {"name": "Satu", "is_foreign": False, "cohort": "retail"}}
    pillar = concentration(_tape({"YP": 1_000_000}), registry, ["2026-08-14"],
                           free_float=0.1, shares=1_000_000_000)
    if pillar.value("float_terserap") is not None:
        failures.append("float absorbed was computed without lot counts")
    if not any("lot" in note for note in pillar.unchecked):
        failures.append("the missing lot count was not declared on the card")
    return failures, 2


def check_as_of_does_not_leak():
    """Rule 2: no figure may change when rows after `as_of` are added to the source.

    Two halves. The first is the original mid-series volume test, kept because it isolates
    the cut from everything else. The second is the one that matters: build every demo card
    twice, once with the cuts and once without, and require **every figure** to be identical.
    The old form tested one figure (`volume_z`) on one synthetic symbol, which is how
    `actions` reached the card uncut for as long as it did.
    """
    failures = []
    rows = sources.daily("synth", sources.available_symbols("synth")[0])
    cut = rows[len(rows) // 2]["date"]
    full = volume(rows, cut, window_dates(rows, cut, 3))
    trimmed = volume(upto(rows, cut), cut, window_dates(rows, cut, 3))
    if full.value("volume_z") != trimmed.value("volume_z"):
        failures.append("volume changed when future rows were present — the as-of cut leaks")

    for source, symbol, as_of in DEMO_CASES:
        cut_card = assess(bag_from(source, symbol, as_of), symbol, as_of)
        raw_card = assess(bag_from(source, symbol, as_of, cut=False), symbol, as_of)
        if (cut_card["verdict"], cut_card["modifiers"]) != (raw_card["verdict"],
                                                            raw_card["modifiers"]):
            failures.append(f"{symbol} {as_of}: the verdict moved when future rows were "
                            f"present — {raw_card['verdict']!r} vs {cut_card['verdict']!r}")
        for cut_pillar, raw_pillar in zip(cut_card["pillars"], raw_card["pillars"]):
            for figure in cut_pillar.figures:
                if figure.value != raw_pillar.value(figure.name):
                    failures.append(
                        f"{symbol} {as_of}: {cut_pillar.name}.{figure.name} = "
                        f"{raw_pillar.value(figure.name)!r} with future rows present, "
                        f"{figure.value!r} without — the as-of cut leaks")
        cut_mods = {f.name: f.value for f in cut_card.get("modifier_figures") or []}
        raw_mods = {f.name: f.value for f in raw_card.get("modifier_figures") or []}
        if cut_mods != raw_mods:
            failures.append(f"{symbol} {as_of}: card-level figures moved when future rows "
                            f"were present — {raw_mods!r} vs {cut_mods!r}")
    return failures, 1 + len(DEMO_CASES)


def check_suspension_modifier_respects_as_of():
    """The halt modifier must appear only after the halt, and never before it.

    LIFE was suspended on 2026-09-02 and again on 2026-09-04. A card dated 2026-09-01 that
    already knows either of those is not an early warning; it is the answer read off the back
    of the paper. Both directions are tested, because a modifier that never fires is as wrong
    as one that fires early — and only the second direction proves the feature exists.
    """
    failures = []
    before = assess(bag_from("recorded", "LIFE", "2026-09-01"), "LIFE", "2026-09-01")
    if any("DISUSPENSI" in m for m in before["modifiers"]):
        failures.append("LIFE 2026-09-01 carries a suspension modifier dated after the card")
    if any(f.name == "pernah_disuspensi" for f in before["modifier_figures"]):
        failures.append("LIFE 2026-09-01 built a pernah_disuspensi figure from the future")

    # 2026-09-04, not 2026-09-10: the broker tape for LIFE ends on 2026-09-04, so a later
    # card is rejected `tanpa_broker` before any modifier is reached. That rejection is
    # correct, and it is the wrong fixture for this question.
    after = assess(bag_from("recorded", "LIFE", "2026-09-04"), "LIFE", "2026-09-04")
    tagged = [m for m in after["modifiers"] if "DISUSPENSI" in m]
    if not tagged:
        failures.append("LIFE 2026-09-04 lost the suspension modifier it should carry")
    elif not tagged[0].endswith("2026-09-04"):
        failures.append(f"LIFE 2026-09-04 names the wrong halt date: {tagged[0]!r}")
    halts = [f for f in after["modifier_figures"] if f.name == "pernah_disuspensi"]
    if not halts:
        failures.append("LIFE 2026-09-04 printed the modifier without a figure behind it")
    elif halts[0].value != 2 or halts[0].endpoint != sources.ENDPOINT["suspensions"]:
        failures.append(f"pernah_disuspensi = {halts[0].value!r} from {halts[0].endpoint!r}")
    return failures, 4


def check_verdict_is_never_advice():
    """Rule 3: no verdict or headline may contain a word that tells the reader what to do."""
    failures = []
    prohibited = ("beli", "jual", "buy", "sell", "target", "cuan", "rekomendasi",
                  "sebaiknya", "hold", "akumulasi sekarang")
    texts = []
    for source, symbol, as_of in DEMO_CASES:
        result = assess(bag_from(source, symbol, as_of), symbol, as_of)
        texts.append(result["verdict"])
        texts += result["modifiers"]
        texts += [p.headline for p in result["pillars"]]
    for text in texts:
        low = text.lower()
        for word in prohibited:
            # "net beli" is a quantity, not an instruction; the advice test is the verb.
            if word == "beli" and ("net beli" in low or "pembeli" in low):
                continue
            if word in low:
                failures.append(f"advice word {word!r} reached the card: {text!r}")
    return failures, len(texts)


def check_end_to_end():
    """The demo path has to work on local data, with every citation intact.

    It runs on `synth/` because the two recorded windows do not overlap far enough: the
    paid-for BBCA daily series starts 2026-08-06 and its daily broker summary ends
    2026-08-14, leaving seven trading days — fewer than any honest baseline. That is the
    open question about buying one `/v2/daily/` window, stated as a failing fixture rather
    than as a paragraph.
    """
    failures = []
    for source, symbol, as_of in DEMO_CASES:
        result = assess(bag_from(source, symbol, as_of), symbol, as_of)
        if len(result["pillars"]) != 4:
            failures.append(f"{symbol}: {len(result['pillars'])} pillars, expected 4")
        for pillar in result["pillars"]:
            if pillar.status not in (TENANG, WASPADA, BAHAYA, TAK_TERUKUR):
                failures.append(f"{symbol}.{pillar.name}: unknown status {pillar.status}")
            if not pillar.headline:
                failures.append(f"{symbol}.{pillar.name}: no headline")
            for figure in pillar.figures:
                if not figure.endpoint or not figure.fields:
                    failures.append(f"{symbol}.{pillar.name}.{figure.name}: uncited figure")
        print(f"        {symbol} {as_of} [{source}] → {result['verdict']}"
              + (f" · {' · '.join(result['modifiers'])}" if result["modifiers"] else ""))
        for pillar in result["pillars"]:
            print(f"          {pillar.name:<13} {pillar.status:<14} {pillar.headline[:70]}")
    return failures, 4 * len(DEMO_CASES)


def check_recorded_concentration():
    """Pilar 1 must still run on the payload that was actually paid for.

    Concentration needs no baseline, so the recorded BBCA tape exercises the real join —
    85 broker codes against an 88-code registry — even while the other three pillars wait
    for a longer price window.
    """
    failures = []
    bag = bag_from("recorded", "BBCA", "2026-08-14")
    window = sorted({r["date"] for r in bag["flow"]})[-T.get("event_window"):]
    pillar = concentration(bag["flow"], bag["registry"], window,
                           free_float=bag.get("free_float"), shares=bag.get("shares"),
                           shares_fields=bag.get("shares_fields") or (),
                           shares_exact=bag.get("shares_exact", True))
    if pillar.value("pangsa_puncak") is None:
        failures.append("recorded BBCA produced no top share")
    if not 0 < pillar.value("pembeli_efektif") <= 100:
        failures.append(f"implausible N_eff {pillar.value('pembeli_efektif')}")
    if pillar.value("pangsa_kohort") is None:
        failures.append("the registry join produced no cohort split")
    if pillar.value("float_terserap") is None:
        failures.append("recorded lots are present, so float absorbed should be computed")
    print(f"        BBCA {window[0]}..{window[-1]} [recorded] {pillar.status}: "
          f"{pillar.headline[:64]}")
    print(f"          float terserap {pillar.value('float_terserap'):.3%} · "
          f"asing {pillar.value('pangsa_asing'):.0%} · kohort "
          + ", ".join(f"{k} {v:.0%}" for k, v in sorted(pillar.value("pangsa_kohort").items())))
    return failures, 4


def check_rejects_are_named():
    """A symbol that cannot be scored must fail with a reason from the threshold table."""
    failures = []
    try:
        concentration([], {}, ["2026-08-14"])
        failures.append("an empty tape did not raise")
    except Rejected as exc:
        if exc.reason not in T.REJECTS:
            failures.append(f"unnamed reject reason {exc.reason!r}")
    return failures, 1


def main():
    total, bad = 0, []
    for check in (check_single_buyer, check_sellers_do_not_count, check_no_lots_no_float,
                  check_as_of_does_not_leak, check_suspension_modifier_respects_as_of,
                  check_verdict_is_never_advice,
                  check_end_to_end, check_recorded_concentration,
                  check_rejects_are_named):
        failures, count = check()
        total += count
        bad += failures
        print(f"  {check.__name__:<32} {count - len(failures)}/{count}")
    for line in bad:
        print("FAIL", line)
    print(f"{total - len(bad)}/{total} checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
