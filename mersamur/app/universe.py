"""Siapa yang di-screen — the working universe, and the only safe way to name it.

Two decisions live here, and both are statistical rather than cosmetic.

**Which stocks.** The market-wide cooling-down base rate is 0,77% per stock per
10 trading days (`app.labels.base_rate`). In the **200 smallest listed companies
by market cap, 98 — 49% — have a suspension on record** (`riset/temuan-kelayakan.md`
§"Satu temuan yang mengubah penentuan universe"). That is the tier Telegram tips
come from, and restricting the product to it turns the problem from a needle in a
haystack into sorting a group that is already high-risk. `watchlist()` is that
tier; `control_group()` is the 102 of them that have *never* been suspended, which
tasks 10 and 11 need as the comparison arm.

**Which names are allowed to reach the client.** A guessed identifier is not free:
a routed 404 bills one credit, because the lookup ran. So `resolve()` refuses any
symbol that has not already come back inside a response the project has paid for —
the screener rows plus every symbol in every settled payload under
`research/harness/recorded/`. `ZZZZ` stops here, not at the API.

The `.JK` suffix is normalised in exactly one place — `normalize()` — because the
API returns `LIFE.JK` from the screener and `LIFE` from the path templates, and a
product that handles that in two places eventually handles it in two ways.

Zero credits: the screener call was already bought (1 credit, tier 3, slug
`v2_companies__include_query_values-true_limit-200_...`). Nothing here opens a socket.
"""
import re
from dataclasses import dataclass

from app import labels
from app.cache import Cache

# The settled screener call. `where` filters out the large caps, `order_by` is
# ascending — so the 200 rows the API returns *are* the 200 smallest — and
# `include_query_values=true` is what makes `market_cap` come back at all: the
# screener otherwise returns only `symbol` and `company_name`
# (research/docs/api/03-screener-query-language.md §"a filter, not a data fetcher").
# These params must match the manifest byte for byte or the lookup misses and the
# product starts paying for a row it already owns.
SCREENER_PATH = "/v2/companies/"
SCREENER_PARAMS = {
    "include_query_values": "true",
    "limit": 200,
    "order_by": "market_cap",
    "where": "market_cap<1000000000000",
}

# The working tier. 200 is the screener's own maximum page size and the number the
# 49% figure was measured on; changing it invalidates that measurement.
DEFAULT_SIZE = 200

# IDX tickers are four letters. The recording also holds SGX (`1D0.SI`) and KLSE
# (`1155`) symbols; they are real, but they are not this product's market and they
# must not become resolvable IDX identifiers by accident.
IDX_SYMBOL = re.compile(r"^[A-Z]{4}$")

# Payload keys that carry a ticker. Used to build the set of symbols the project
# has actually seen come back from the API.
SYMBOL_KEYS = ("symbol", "ticker")


class UnknownSymbolError(ValueError):
    """A symbol that never appeared in a paid-for response. Refused before the socket."""


def normalize(symbol):
    """`" life.jk "` -> `"LIFE"`. The single place the `.JK` suffix is handled.

    Returns `""` for anything that is not a string, so callers can test the result
    rather than catching. Only `.JK` is stripped: an `.SI` or `.KL` symbol keeps
    its suffix and therefore fails `IDX_SYMBOL`, which is the intended outcome.
    """
    if not isinstance(symbol, str):
        return ""
    text = symbol.strip().upper()
    if text.endswith(".JK"):
        text = text[:-3]
    return text


@dataclass(frozen=True)
class Company:
    """One screener row. Immutable — a caller must not re-price it in place.

    `market_cap` is the only metric available: it is the field the `where` clause
    named, and `query_values` echoes back nothing else.
    """

    symbol: str
    name: str
    market_cap: int = 0


_COMPANIES = None


def load_screener(cache=None, reload=False):
    """The screener rows as `Company`, smallest market cap first.

    Sorted here rather than trusted from the response: `order_by=market_cap` did
    return ascending order, but the ordering is load-bearing — it is what "the 200
    smallest" means — and re-sorting costs nothing. Rows without a `market_cap`
    sort last instead of masquerading as the smallest company on the exchange.

    `cache` is injectable so tests can build their own corpus; an empty recording
    yields an empty universe rather than an exception, the same contract
    `app.labels` uses.
    """
    global _COMPANIES
    if cache is None and _COMPANIES is not None and not reload:
        return _COMPANIES

    # `cache if cache is not None` — NOT `cache or`: an empty Cache is falsy
    # (it defines __len__), so `or` would silently fall back to the real corpus.
    source = cache if cache is not None else Cache()
    hit = source.get(SCREENER_PATH, SCREENER_PARAMS)
    rows = []
    if hit is not None and hit.found:
        payload = hit.payload
        rows = payload.get("results") if isinstance(payload, dict) else payload
        rows = rows or []

    out = []
    for row in rows:
        symbol = normalize(row.get("symbol"))
        if not symbol:
            continue
        values = row.get("query_values") or {}
        try:
            cap = int(values.get("market_cap") or 0)
        except (TypeError, ValueError):
            cap = 0
        out.append(Company(symbol=symbol,
                           name=row.get("company_name") or "",
                           market_cap=cap))
    # Missing caps (0) go last, not first; symbol breaks ties so the order is stable.
    out.sort(key=lambda c: (c.market_cap == 0, c.market_cap, c.symbol))

    if cache is None:
        _COMPANIES = out
    return out


def companies(size=DEFAULT_SIZE, cache=None):
    """The `size` smallest companies as rows, not just tickers."""
    return load_screener(cache=cache)[:size]


def watchlist(size=DEFAULT_SIZE, cache=None):
    """The working universe: the `size` smallest listed companies, as bare tickers.

    Default 200 — the tier in which half the members have a suspension on record.
    """
    return [c.symbol for c in companies(size=size, cache=cache)]


def control_group(size=DEFAULT_SIZE, cache=None):
    """The members of the watchlist that have **never** been suspended. 102 of 200.

    "Never" is measured over the whole archive — all nine reason classes and all
    years, not just the `cooling_down` label class since 2025. A stock halted in
    2019 for a late report is not a clean control: it is a company the market has
    already had reason to look at. Tasks 10 and 11 compare against this arm, and a
    contaminated control would flatter every number they produce.

    No cutoff date is threaded through here on purpose. This is universe
    construction, not feature construction: any module that wants a stock's
    suspension history as a *feature* must go through
    `labels.history_before(symbol, cutoff)`, which is the only accessor that
    cannot hand back the future.
    """
    ever_suspended = {e.symbol for e in labels.load_events(cache=cache)}
    return [s for s in watchlist(size=size, cache=cache) if s not in ever_suspended]


def market_cap(symbol, cache=None):
    """Market cap in IDR for a screener member, or None if it is not one.

    The only metric the screener carries. Everything else about a company costs a
    credit per section per company through `/v2/company/report/`.
    """
    want = normalize(symbol)
    for company in load_screener(cache=cache):
        if company.symbol == want:
            return company.market_cap
    return None


# --- symbol resolution ------------------------------------------------------
_KNOWN = None


def known_symbols(cache=None, reload=False):
    """Every IDX ticker that has already come back inside a paid-for response.

    Built by walking the settled payloads in the recording — screener rows,
    suspension announcements, broker summaries, top-changes tables — and keeping
    every `symbol`/`ticker` value that looks like an IDX ticker. The path template
    of a 2xx call is folded in too, because a per-symbol call that answered proves
    the symbol exists even in the rare case where the body does not repeat it.

    Only entries that *answered* are read — a settled 404 contributes neither its
    path nor a payload. The 404 was billed because the lookup ran, and treating the
    identifier it failed on as known would let one paid-for miss authorise the next
    one.
    """
    global _KNOWN
    if cache is None and _KNOWN is not None and not reload:
        return _KNOWN

    source = cache if cache is not None else Cache()
    found = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in SYMBOL_KEYS and isinstance(value, str):
                    found.add(normalize(value))
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for entry in source.manifest().values():
        path = entry.get("path") or ""
        hit = source.get(path, entry.get("params"), entry.get("method", "GET"))
        if hit is None or not hit.found:
            # Unsettled, or a settled 404. Neither is evidence the symbol exists,
            # and the path segments of a 404 are the guess that failed — folding
            # them in would let one billed miss authorise the next one.
            continue
        for segment in path.strip("/").split("/"):
            found.add(normalize(segment))
        walk(hit.payload)

    symbols = frozenset(s for s in found if IDX_SYMBOL.match(s))
    if cache is None:
        _KNOWN = symbols
    return symbols


def is_known(symbol, cache=None):
    """True when `symbol` may be sent to the API without gambling a credit."""
    return normalize(symbol) in known_symbols(cache=cache)


def resolve(symbol, cache=None):
    """The canonical bare ticker, or `UnknownSymbolError` — never a network call.

    This is the guard the whole credit policy rests on. A symbol that was never in
    a response is a guess, and a guess that reaches the API costs a credit whether
    or not it exists: the 404 is billed because the lookup ran. Refusing here is
    the difference between a typo costing nothing and a typo costing money.
    """
    want = normalize(symbol)
    if not want:
        raise UnknownSymbolError(
            "Simbol kosong. Sebutkan kode emiten IDX empat huruf, misalnya LIFE.")
    if not IDX_SYMBOL.match(want):
        raise UnknownSymbolError(
            f"{want!r} bukan bentuk kode emiten IDX (empat huruf). "
            f"Simbol SGX dan KLSE tidak dilayani produk ini.")
    if want not in known_symbols(cache=cache):
        raise UnknownSymbolError(
            f"{want!r} belum pernah muncul di respons API yang sudah dibayar. "
            f"Simbol tebakan tidak diteruskan ke klien: 404 pun ditagih 1 kredit.")
    return want


# --- description ------------------------------------------------------------
def _id(value):
    """Format a number the Indonesian way: comma as the decimal separator."""
    return str(value).replace(".", ",")


def _rupiah(value):
    """`4752982378` -> `Rp4,75 miliar`. Descriptive, no judgement attached."""
    if value >= 1_000_000_000_000:
        return "Rp" + _id("%.2f" % (value / 1_000_000_000_000)) + " triliun"
    if value >= 1_000_000_000:
        return "Rp" + _id("%.2f" % (value / 1_000_000_000)) + " miliar"
    return "Rp" + _id("%.2f" % (value / 1_000_000)) + " juta"


def summary(cache=None):
    """A descriptive account of the universe. No verdict, no score, no signal."""
    rows = companies(cache=cache)
    if not rows:
        return "Universe kosong — rekaman screener tidak ditemukan di recorded/."

    clean = control_group(cache=cache)
    suspended = len(rows) - len(clean)
    share = round(suspended / len(rows) * 100)
    return "\n".join([
        "Universe kerja — dari /v2/companies/ yang sudah terekam (0 kredit)",
        f"  lapis            : {len(rows)} emiten dengan kapitalisasi terkecil",
        f"  rentang kap      : {_rupiah(rows[0].market_cap)} .. "
        f"{_rupiah(rows[-1].market_cap)}",
        f"  pernah disuspensi: {suspended} ({share}%) — seluruh kelas alasan, "
        f"seluruh tahun",
        f"  kelompok kontrol : {len(clean)} emiten tanpa riwayat suspensi",
        f"  simbol dikenal   : {len(known_symbols(cache=cache))} kode IDX yang "
        f"pernah muncul di respons berbayar",
        "  Angka ini deskriptif: siapa yang diamati, bukan penilaian atas emitennya.",
    ])


if __name__ == "__main__":
    print(summary())
