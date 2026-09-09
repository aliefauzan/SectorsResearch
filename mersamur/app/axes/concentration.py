"""Sumbu konsentrasi — how much of the buying sits with one broker.

The strongest axis in the feasibility run. Across the ten suspended names, the
median top buyer held **61,6%** of the visible buy value; the blue-chip comparison
runs 11–34% (`riset/temuan-kelayakan.md` §Q1). One retail broker, `XL`, was top
buyer in 7 of those 10.

Two measurements come out of `/v2/broker-summary/{symbol}/top/`, and they answer
different questions:

  * **Concentration ratio** — `top_buyers[0].buy_idr / sum(buy_idr)`. How crowded
    one side of the book is. Also reported for the top three.
  * **Net dominance** — the largest accumulator against the largest distributor.

Net dominance is where bandarmology projects break. Equities are zero-sum: sum the
net of every buyer and every seller and the answer is near zero no matter what the
tape did, so the signal looks flat and the reader concludes nothing is happening.
The organizers warn about this explicitly in their own GNN recipe
(`research/docs/api/10-domain-pitfalls.md` §1):

    # WRONG — always lands near zero, the market is zero-sum
    total = sum(b["net_idr"] for b in buyers) + sum(s["net_idr"] for s in sellers)

    # RIGHT — net_idr is ALREADY negative for sellers, so this ADDS
    dominance = buyers[0]["net_idr"] + sellers[0]["net_idr"]

The sign convention is the trap inside the trap: `net_idr` comes back negative for
sellers, so the correct formula *adds* where the intuitive one subtracts. Getting
it backwards inverts the whole axis, and it inverts it quietly —
`test_concentration.py` exists mostly to make that specific mistake fail loudly.

Everything is descriptive. This module reports what the broker panel contained; it
does not say the stock is being cornered, and `fired` means "past the bar recorded
in `state/thresholds.json` today", not "act on this".

Zero credits: reads only `research/harness/recorded/`. No socket is opened, and
`SectorsClient` is never imported.
"""
from dataclasses import dataclass
from datetime import timedelta

from app import axes, labels, universe
from app.cache import Cache

AXIS = "concentration"

# The call, and the parameter forms it was actually captured under. `n_brokers=10`
# is what the ten suspended names were bought with; the four blue chips predate
# that decision and were captured bare. Tried in order, so a symbol recorded both
# ways answers from the ten-broker panel.
BROKER_SUMMARY_PATH = "/v2/broker-summary/{symbol}/top/"
PARAM_VARIANTS = ({"n_brokers": 10}, {})
BROKERS_PATH = "/v2/brokers/"
BROKERS_PARAMS = {}

# What `n_brokers=10` asked for. A shorter list is not a truncated response and not
# an error — it is the whole book. NICK has five buyers because five brokers bought
# it. Scarcity is the finding, so it is carried on the result as `thin_book` rather
# than padded, dropped, or raised.
BOOK_FULL = 10


class NoBrokerDataError(LookupError):
    """No settled broker panel for this symbol in the recording.

    Raised instead of fetching. `/v2/broker-summary/{symbol}/top/` bills a credit,
    and a 404 on a guessed ticker bills one too, so a missing panel is a decision
    for `capture.py` to make deliberately — never a side effect of scoring.
    """


# --- the broker registry ----------------------------------------------------
_REGISTRY = None


def registry(cache=None, reload=False):
    """`/v2/brokers/` as `{code: row}` — 88 brokers, one credit, already paid.

    The field that matters is **`is_foreign` (boolean), not `origin`**. The spec is
    misleading here: `origin` is a *query* parameter on the broker endpoints and
    echoes back in the summary payload as `"all"`, while the registry describes a
    broker with `is_foreign`. Code written against `origin` reads `None` for every
    broker and quietly classifies the whole market as domestic.
    """
    global _REGISTRY
    if cache is None and _REGISTRY is not None and not reload:
        return _REGISTRY

    # `cache if cache is not None` — NOT `cache or`: an empty Cache is falsy
    # (it defines __len__), so `or` would silently fall back to the real corpus.
    source = cache if cache is not None else Cache()
    hit = source.get(BROKERS_PATH, BROKERS_PARAMS)
    rows = []
    if hit is not None and hit.found:
        payload = hit.payload
        rows = payload.get("results") if isinstance(payload, dict) else payload
        rows = rows or []

    out = {}
    for row in rows:
        code = (row.get("code") or "").strip().upper()
        if code:
            out[code] = row

    if cache is None:
        _REGISTRY = out
    return out


def broker(code, cache=None):
    """One registry row, or `None` for a code the registry does not carry."""
    return registry(cache=cache).get((code or "").strip().upper())


def cohort_of(code, cache=None):
    """`retail` / `mixed` / `institutional` / `unknown` for a broker code."""
    row = broker(code, cache=cache)
    return (row or {}).get("cohort") or "unknown"


# --- the panel --------------------------------------------------------------
def panel(symbol, cache=None):
    """The settled `/v2/broker-summary/.../top/` payload, or `NoBrokerDataError`."""
    want = universe.normalize(symbol)
    source = cache if cache is not None else Cache()
    path = BROKER_SUMMARY_PATH.format(symbol=want)
    for params in PARAM_VARIANTS:
        hit = source.get(path, params)
        if hit is not None and hit.found:
            return hit.payload
    raise NoBrokerDataError(
        f"Tidak ada panel broker terekam untuk {want!r}. "
        f"Panggilan itu berbiaya 1 kredit dan tidak dijalankan diam-diam — "
        f"ambil lewat capture.py kalau memang diperlukan."
    )


def _rows(payload, key):
    """The buy or sell side as a list of dicts, whatever the payload does wrong."""
    rows = payload.get(key) if isinstance(payload, dict) else None
    return [r for r in (rows or []) if isinstance(r, dict)]


def _num(row, key):
    try:
        return float(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0.0


# --- the result -------------------------------------------------------------
@dataclass(frozen=True)
class Concentration:
    """One symbol's broker panel, measured. Immutable — no caller re-scores it.

    `top1_ratio` and `top3_ratio` are `None`, not `0.0`, when the panel carries no
    value at all: zero would be a measurement ("nobody dominates"), and the truth
    is that nothing was measured.
    """

    symbol: str
    start: str = ""
    end: str = ""
    n_buyers: int = 0
    n_sellers: int = 0
    thin_book: bool = False
    top_buyer: str = ""
    top_buyer_name: str = ""
    cohort: str = "unknown"
    is_foreign: bool = False
    top_seller: str = ""
    top1_ratio: float = None
    top3_ratio: float = None
    total_buy_idr: float = 0.0
    net_dominance: float = 0.0
    dominance_ratio: float = None
    panel_value_idr: float = 0.0
    all_zero: bool = False
    suspensions_in_window: tuple = ()
    threshold: float = 0.0
    cohort_factor: float = 1.0
    effective_threshold: float = 0.0
    thresholds_version: int = None
    fired: bool = False

    @property
    def accumulating(self):
        """True when the largest accumulator outweighs the largest distributor.

        A direction, not a verdict: positive means the top buyer took on more than
        the top seller let go over the panel's own window.
        """
        return self.net_dominance > 0

    def __str__(self):
        return describe(self)


def _suspensions_in_window(symbol, start, end, cache=None):
    """Suspension announcements dated inside the panel's own window.

    This is a **data-quality check, not a feature**. It exists only to answer "is
    this all-zero panel a suspended stock?" — a suspended IDX stock returns a
    well-formed, entirely zero series rather than an error
    (`research/docs/api/10-domain-pitfalls.md` §2), and scoring that as "no
    concentration" is a conclusion drawn from an absence of trading.

    It deliberately does *not* go through `labels.history_before`: that accessor
    cannot see inside the window, which is exactly the property that makes it safe
    for features and useless here. Nothing derived from this may be fed to a model
    — it explains a hole in the data, it does not describe the days before it.
    """
    first, last = labels.parse_date(start), labels.parse_date(end)
    if first is None or last is None:
        return ()
    found = labels.events(symbol=symbol, after=first, before=last + timedelta(days=1),
                          cache=cache)
    return tuple(found)


def score(symbol, cache=None, thresholds_path=None):
    """Measure the concentration axis for one symbol. Reads the recording only.

    `thresholds_path` is injectable so a test can prove the bar comes from the file
    rather than from this module — an axis with the number baked in passes every
    test that only reads the shipped document.
    """
    want = universe.normalize(symbol)
    payload = panel(want, cache=cache)

    buyers = _rows(payload, "top_buyers")
    sellers = _rows(payload, "top_sellers")
    start = str(payload.get("start") or "")
    end = str(payload.get("end") or "")

    total_buy = sum(_num(b, "buy_idr") for b in buyers)
    total_sell = sum(_num(s, "sell_idr") for s in sellers)
    # Buy value from the buy side plus sell value from the sell side. The two lists
    # do not overlap in any recorded panel, so nothing is counted twice; it is the
    # value visible in this panel, not the day's whole tape.
    panel_value = total_buy + total_sell

    top_buyer = buyers[0] if buyers else {}
    top_seller = sellers[0] if sellers else {}
    code = (top_buyer.get("broker_code") or "").strip().upper()
    row = broker(code, cache=cache) or {}

    # ZERO-SUM TRAP, the corrected form. `net_idr` is already negative on the sell
    # side, so the largest accumulator and the largest distributor are ADDED. Summing
    # both sides in full instead lands near zero for every symbol on the exchange;
    # subtracting here inverts the sign of the entire axis.
    dominance = _num(top_buyer, "net_idr") + _num(top_seller, "net_idr")

    all_zero = panel_value == 0
    ratio1 = ratio3 = dominance_ratio = None
    if total_buy > 0:
        ratio1 = _num(top_buyer, "buy_idr") / total_buy
        ratio3 = sum(_num(b, "buy_idr") for b in buyers[:3]) / total_buy
    if panel_value > 0:
        dominance_ratio = dominance / panel_value

    cohort = row.get("cohort") or "unknown"
    base = axes.threshold(AXIS, thresholds_path)
    factor = axes.cohort_factor(cohort, thresholds_path)
    effective = base * factor

    # An all-zero panel never fires. It is not a quiet stock — it is very often a
    # halted one, and the window's suspension announcements are attached so the
    # reader is told which.
    fired = bool(ratio1 is not None and not all_zero and ratio1 >= effective)

    return Concentration(
        symbol=want,
        start=start,
        end=end,
        n_buyers=len(buyers),
        n_sellers=len(sellers),
        thin_book=len(buyers) < BOOK_FULL,
        top_buyer=code,
        top_buyer_name=row.get("name") or "",
        cohort=cohort,
        # `is_foreign`, not `origin` — see `registry()`.
        is_foreign=bool(row.get("is_foreign")),
        top_seller=(top_seller.get("broker_code") or "").strip().upper(),
        top1_ratio=ratio1,
        top3_ratio=ratio3,
        total_buy_idr=total_buy,
        net_dominance=dominance,
        dominance_ratio=dominance_ratio,
        panel_value_idr=panel_value,
        all_zero=all_zero,
        suspensions_in_window=(_suspensions_in_window(want, start, end, cache=cache)
                               if all_zero else ()),
        threshold=base,
        cohort_factor=factor,
        effective_threshold=effective,
        thresholds_version=axes.version(thresholds_path),
        fired=fired,
    )


# --- description ------------------------------------------------------------
def _id(value):
    """Format a number the Indonesian way: comma as the decimal separator."""
    return str(value).replace(".", ",")


def _pct(value):
    return "-" if value is None else _id("%.1f" % (value * 100)) + "%"


def _rupiah(value):
    """Signed, in the largest unit that keeps the number readable."""
    sign = "-" if value < 0 else ""
    size = abs(value)
    if size >= 1_000_000_000_000:
        return sign + "Rp" + _id("%.2f" % (size / 1_000_000_000_000)) + " triliun"
    if size >= 1_000_000_000:
        return sign + "Rp" + _id("%.2f" % (size / 1_000_000_000)) + " miliar"
    return sign + "Rp" + _id("%.2f" % (size / 1_000_000)) + " juta"


def describe(result):
    """A descriptive account of one panel. No verdict, no buy/sell, no colour."""
    lines = [f"Konsentrasi broker {result.symbol} — panel {result.start} .. {result.end} "
             f"(0 kredit, dari rekaman)"]

    if result.all_zero:
        lines.append("  panel nol seluruhnya: tidak ada nilai transaksi tercatat "
                     "di sisi mana pun.")
        if result.suspensions_in_window:
            for event in result.suspensions_in_window:
                lines.append(f"  suspensi di dalam jendela: {event.date} — "
                             f"{event.reason_class}")
            lines.append("  Deret nol ini menyertai suspensi, bukan sepinya minat. "
                         "Tidak ada konsentrasi yang bisa dibaca dari sini.")
        else:
            lines.append("  Tidak ada suspensi tercatat di jendela ini, jadi sebab "
                         "deret nol belum diketahui. Tidak ada yang disimpulkan.")
        lines.append(f"  ambang berlaku   : {_id('%.2f' % result.effective_threshold)} "
                     f"(v{result.thresholds_version}) · sumbu tidak menyala")
        return "\n".join(lines)

    lines += [
        f"  akumulator top   : {result.top_buyer} "
        f"({result.top_buyer_name or 'tidak ada di registri'}) · kohort "
        f"{result.cohort} · {'asing' if result.is_foreign else 'domestik'}",
        f"  pangsa top-1     : {_pct(result.top1_ratio)} dari nilai akumulasi panel",
        f"  pangsa top-3     : {_pct(result.top3_ratio)}",
        f"  distributor top  : {result.top_seller or '-'}",
        f"  dominansi neto   : {_rupiah(result.net_dominance)} "
        f"({_pct(result.dominance_ratio)} dari nilai panel) — "
        f"{'akumulasi' if result.accumulating else 'distribusi'} yang lebih besar",
        f"  kedalaman buku   : {result.n_buyers} akumulator / "
        f"{result.n_sellers} distributor"
        + (f" — buku tipis, kurang dari {BOOK_FULL} baris yang diminta"
           if result.thin_book else ""),
        f"  ambang berlaku   : {_id('%.2f' % result.effective_threshold)} "
        f"= {_id('%.2f' % result.threshold)} x {_id('%.2f' % result.cohort_factor)} "
        f"(kohort {result.cohort}, ambang v{result.thresholds_version})",
        f"  sumbu            : {'menyala' if result.fired else 'tidak menyala'}",
        "  Angka ini deskriptif: isi panel broker apa adanya, bukan penilaian atas "
        "emiten maupun anjuran tindakan.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    for arg in (sys.argv[1:] or ["LIFE"]):
        print(score(arg))
        print()
