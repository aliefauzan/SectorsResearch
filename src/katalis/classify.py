#!/usr/bin/env python3
"""
Menjelaskan atau melaporkan: one article in, one of three labels out.

The fourth pillar asks whether anything **explains** a move or merely **reports** it. That
is a language judgment, and until this module existed the card made it by date arithmetic
alone: an article stamped before the window was called "kabar yang mendahului" even when it
was a Top Gainers round-up of the move itself, or the exchange's own suspension notice.

Three properties this file keeps, because the rest of the product is argued from them:

  1. **Pure.** No file is opened, no socket is opened, no environment variable is read.
     `check_this_module_reads_nothing` scans the source above the gates and fails on any of
     them. A pure classifier is one a hand-written case table can pin down.
  2. **A table, not a chain of `if`s.** `RULES` is data: ordered rows of
     `(label, rule, signal, needle)`, first match wins. Adding a pattern is adding a row,
     and `label()` never grows.
  3. **The model is optional, and that is enforced elsewhere.** `resolve()` is the only way
     to choose an implementation, and an unknown name raises `UnknownClassifier` instead of
     quietly returning the rules — falling back in silence is how a card ends up claiming a
     model it never called. `CLASSIFIER` itself is read in exactly one place in this
     product, `card.selected_classifier()`.

    python3 classify.py     # the hand-labelled case table, and the purity scan
"""
import os
import re

#: The three labels. `tak_terkait` is the honest answer for an article that reached this
#: function without being about the symbol at all.
MENJELASKAN = "menjelaskan"
MELAPORKAN = "melaporkan"
TAK_TERKAIT = "tak_terkait"

LABELS = (MENJELASKAN, MELAPORKAN, TAK_TERKAIT)

#: Name of the implementation used when `CLASSIFIER` is unset. Fase 6 adds `llm` beside it.
DEFAULT = "rules"


class UnknownClassifier(ValueError):
    """Raised by `resolve()`. Carries the offending value so the message can name it."""

    def __init__(self, name, known):
        self.name = name
        super().__init__(f"CLASSIFIER={name!r} tidak dikenal; yang ada: {', '.join(known)}")


# ---------------------------------------------------------------------------- the signals

def _tags(article):
    return [str(tag).lower() for tag in (article.get("tags") or [])]


def _title(article):
    return (article.get("title") or "").lower()


def _symbols(article):
    return [str(s).upper() for s in (article.get("symbols") or [])]


def _has_tag(article, needle):
    return any(needle in tag for tag in _tags(article))


def _in_title(article, needle):
    """Word-bounded, so `ARA` does not match `karya` and `laba` does not match `belabas`."""
    return re.search(rf"(?<![\w-]){re.escape(needle)}(?![\w-])", _title(article)) is not None


def _many_symbols(article, needle):
    return len(_symbols(article)) >= int(needle)


SIGNALS = {"tag": _has_tag, "judul": _in_title, "banyak_simbol": _many_symbols}

#: Ordered. First match wins, and the reporting rows come first on purpose: an article can
#: carry a corporate-event tag and still be a report of a price that already moved — the
#: LIFE round-up is tagged `Rights Issue` and is about a different company's rights issue.
RULES = (
    # --- melaporkan: the exchange acted on this symbol, and the article says so.
    (MELAPORKAN, "tindakan_bursa", "tag", "suspension"),
    (MELAPORKAN, "tindakan_bursa", "judul", "suspends"),
    (MELAPORKAN, "tindakan_bursa", "judul", "suspension"),
    (MELAPORKAN, "tindakan_bursa", "judul", "suspensi"),
    (MELAPORKAN, "tindakan_bursa", "judul", "disuspensi"),
    (MELAPORKAN, "tindakan_bursa", "judul", "dihentikan"),
    (MELAPORKAN, "tindakan_bursa", "judul", "unusual market activity"),
    (MELAPORKAN, "tindakan_bursa", "judul", "uma"),
    (MELAPORKAN, "tindakan_bursa", "judul", "delisting"),
    # --- melaporkan: the price already moved, and the article is the scoreboard.
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "top gainers"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "top losers"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "ara"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "arb"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "auto reject"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "melonjak"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "meroket"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "melesat"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "terbang"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "anjlok"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "ambles"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "soaring"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "jumped"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "surges"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "rally"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "shares move"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "target price"),
    (MELAPORKAN, "harga_sudah_bergerak", "judul", "analysts"),
    # --- melaporkan: a market round-up names a crowd of symbols, not an event of one.
    (MELAPORKAN, "rangkuman_pasar", "banyak_simbol", "5"),
    # --- menjelaskan: a corporate event that precedes a move rather than follows it.
    (MENJELASKAN, "aksi_korporasi", "tag", "rights issue"),
    (MENJELASKAN, "aksi_korporasi", "tag", "dividend"),
    (MENJELASKAN, "aksi_korporasi", "tag", "stock split"),
    (MENJELASKAN, "aksi_korporasi", "tag", "m&a"),
    (MENJELASKAN, "aksi_korporasi", "tag", "business expansion"),
    (MENJELASKAN, "aksi_korporasi", "judul", "rights issue"),
    (MENJELASKAN, "aksi_korporasi", "judul", "right issue"),
    (MENJELASKAN, "aksi_korporasi", "judul", "dividen"),
    (MENJELASKAN, "aksi_korporasi", "judul", "dividend"),
    (MENJELASKAN, "aksi_korporasi", "judul", "akuisisi"),
    (MENJELASKAN, "aksi_korporasi", "judul", "acquisition"),
    (MENJELASKAN, "aksi_korporasi", "judul", "acquires"),
    (MENJELASKAN, "aksi_korporasi", "judul", "merger"),
    (MENJELASKAN, "aksi_korporasi", "judul", "kontrak"),
    (MENJELASKAN, "aksi_korporasi", "judul", "contract"),
    (MENJELASKAN, "aksi_korporasi", "judul", "partnership"),
    (MENJELASKAN, "aksi_korporasi", "judul", "kemitraan"),
    (MENJELASKAN, "aksi_korporasi", "judul", "buyback"),
    (MENJELASKAN, "aksi_korporasi", "judul", "obligasi"),
    (MENJELASKAN, "aksi_korporasi", "judul", "private placement"),
    # --- menjelaskan: an operational or financial fact about the company itself.
    (MENJELASKAN, "kinerja_operasional", "tag", "financial metrics"),
    (MENJELASKAN, "kinerja_operasional", "tag", "earnings"),
    (MENJELASKAN, "kinerja_operasional", "judul", "laba"),
    (MENJELASKAN, "kinerja_operasional", "judul", "rugi"),
    (MENJELASKAN, "kinerja_operasional", "judul", "pendapatan"),
    (MENJELASKAN, "kinerja_operasional", "judul", "kinerja"),
    (MENJELASKAN, "kinerja_operasional", "judul", "profit"),
    (MENJELASKAN, "kinerja_operasional", "judul", "revenue"),
    (MENJELASKAN, "kinerja_operasional", "judul", "earnings"),
    (MENJELASKAN, "kinerja_operasional", "judul", "claims"),
    (MENJELASKAN, "kinerja_operasional", "judul", "klaim"),
)


# ------------------------------------------------------------------------ the one function

def label(article, symbol=None):
    """One article in, one of `LABELS` out. Pure: `article` is the only thing it reads.

    `symbol` is optional and is the only way `tak_terkait` is ever returned: an article that
    does not name the symbol cannot be evidence about it, whatever its tags say.
    """
    if symbol:
        bare = str(symbol).upper().split(".")[0]
        if _symbols(article) and bare not in [s.split(".")[0] for s in _symbols(article)]:
            return TAK_TERKAIT
    for name, _rule, signal, needle in RULES:
        if SIGNALS[signal](article, needle):
            return name
    return TAK_TERKAIT


def rule_for(article, symbol=None):
    """Which row of `RULES` decided it, for a card or a gate that has to show its work."""
    if label(article, symbol) == TAK_TERKAIT:
        return "tak_ada_aturan" if not symbol else "bukan_simbol_ini"
    for _name, rule, signal, needle in RULES:
        if SIGNALS[signal](article, needle):
            return rule
    return "tak_ada_aturan"


#: Every implementation the product knows. Fase 6 adds `"llm"` here and nowhere else.
CLASSIFIERS = {"rules": label}


def resolve(name):
    """Name in, classifying function out. Unknown names raise — they never fall back."""
    if name not in CLASSIFIERS:
        raise UnknownClassifier(name, sorted(CLASSIFIERS))
    return CLASSIFIERS[name]


# --------------------------------------------------------------------------------- gates

#: Hand-written labels. The first three rows are the real LIFE articles in
#: `research/harness/recorded/` — the Top Gainers round-up and the exchange's own suspension
#: notice are the two the card used to read as "kabar yang mendahului", and both are reports.
#: `pillars.check_life_articles_are_reports` re-runs these against the payload on disk, so a
#: title edited here without editing the recording turns the suite red.
CASES = (
    ({"title": "Top Gainers on the IDX on 31 August 2026 led by PT DMS Propertindo Tbk "
               "soaring 34.16% after announcing a rights issue",
      "tags": ["Rights Issue", "Capital & Funding", "Business Expansion", "Bullish"],
      "symbols": ["LIFE.JK", "KOTA.JK", "SRSN.JK", "ASLI.JK", "BSIM.JK", "FORU.JK"]},
     MELAPORKAN, "harga_sudah_bergerak"),
    ({"title": "BEI suspends PT Prima Globalindo Logistik Tbk, PT MSIG Life Insurance "
               "Indonesia Tbk and PT Alakasa Industrindo Tbk",
      "tags": ["Suspension", "Bearish"],
      "symbols": ["PPGL.JK", "LIFE.JK", "ALKA.JK"]},
     MELAPORKAN, "tindakan_bursa"),
    ({"title": "MSIG Life reports 68.61% rise in net profit to Rp 180.6 billion in H1 2026",
      "tags": ["Financial Metrics", "Asset Management", "Bullish"],
      "symbols": ["LIFE.JK"]},
     MENJELASKAN, "kinerja_operasional"),
    ({"title": "MSIG Life’s claims total Rp545 billion, with a majority of death claims "
               "involving young adults",
      "tags": ["Financial Metrics", "OJK", "Risk & Compliance", "Capital & Funding",
               "Bullish"],
      "symbols": ["LIFE.JK"]},
     MENJELASKAN, "kinerja_operasional"),
    ({"title": "BEI Lifts Suspension on PPGL, ALKA, LIFE, and AGAR Shares, Trading Resumes",
      "tags": ["Suspension", "Bullish"],
      "symbols": ["PPGL.JK", "ALKA.JK", "LIFE.JK", "AGAR.JK"]},
     MELAPORKAN, "tindakan_bursa"),
    ({"title": "Primaprima Makmur announces dividend of IDR 430 per share",
      "tags": ["dividend", "52-w-high"], "symbols": ["KVDN.JK"]},
     MENJELASKAN, "aksi_korporasi"),
    ({"title": "Primaprima Makmur signs strategic partnership to expand pharmaceuticals",
      "tags": ["52-w-low"], "symbols": ["KVDN.JK"]},
     MENJELASKAN, "aksi_korporasi"),
    ({"title": "Analysts raise target price on KVDN after strong earnings",
      "tags": ["52-w-low"], "symbols": ["KVDN.JK"]},
     MELAPORKAN, "harga_sudah_bergerak"),
    ({"title": "KVDN shares move on heavy foreign broker activity",
      "tags": ["top-90d-transaction-value"], "symbols": ["KVDN.JK"]},
     MELAPORKAN, "harga_sudah_bergerak"),
    ({"title": "Pemerintah menaikkan cukai rokok mulai tahun depan",
      "tags": ["Politics & Regulation"], "symbols": ["GGRM.JK"]},
     TAK_TERKAIT, "tak_ada_aturan"),
)


def check_hand_labels():
    """The table above is the contract. A rule change that moves a label turns this red."""
    failures = []
    for article, want, rule in CASES:
        got = label(article)
        if got != want:
            failures.append(f"{article['title'][:48]!r}: {got}, expected {want}")
        elif rule_for(article) != rule:
            failures.append(f"{article['title'][:48]!r}: matched {rule_for(article)!r}, "
                            f"expected rule {rule!r}")
    return failures, len(CASES)


def check_three_labels_and_no_fourth():
    failures = []
    for article, _want, _rule in CASES:
        if label(article) not in LABELS:
            failures.append(f"{article['title'][:40]!r} produced a label outside LABELS")
    for name, _rule, _signal, _needle in RULES:
        if name not in (MENJELASKAN, MELAPORKAN):
            failures.append(f"rule row produces {name!r}; only the default may be tak_terkait")
    if label({}) != TAK_TERKAIT:
        failures.append("an empty article did not fall to tak_terkait")
    return failures, len(CASES) + len(RULES) + 1


def check_symbol_mismatch_is_tak_terkait():
    """An article about other symbols is not evidence about this one, whatever its tags."""
    failures = []
    article = {"title": "MSIG Life reports 68.61% rise in net profit",
               "tags": ["Financial Metrics"], "symbols": ["LIFE.JK"]}
    if label(article, symbol="KVDN") != TAK_TERKAIT:
        failures.append("an article naming only LIFE was accepted as evidence about KVDN")
    if label(article, symbol="LIFE.JK") != MENJELASKAN:
        failures.append("the suffix form LIFE.JK was not recognised as the same symbol")
    if label(article, symbol="LIFE") != MENJELASKAN:
        failures.append("the bare form LIFE was not recognised as the same symbol")
    return failures, 3


def check_unknown_classifier_is_named():
    """`resolve` must refuse, and must put the offending value in the message."""
    failures = []
    if resolve(DEFAULT) is not label:
        failures.append("resolve('rules') did not return the rules classifier")
    try:
        resolve("tidak-ada")
        failures.append("resolve('tidak-ada') returned instead of raising")
    except UnknownClassifier as exc:
        if "tidak-ada" not in str(exc):
            failures.append(f"the refusal does not name the value: {exc}")
        if "rules" not in str(exc):
            failures.append("the refusal does not say what is available")
    return failures, 3


def check_this_module_reads_nothing():
    """Purity, scanned rather than asserted: no file, no socket, no environment."""
    failures = []
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        body = handle.read().split("--------- gates", 1)[0]
    for forbidden in ("open(", "os.environ", "urllib", "socket.", "subprocess.", "sources."):
        if forbidden in body:
            failures.append(f"{forbidden!r} appears above the gates — the module is not pure")
    return failures, 6


def main():
    total, bad = 0, []
    for check in (check_hand_labels, check_three_labels_and_no_fourth,
                  check_symbol_mismatch_is_tak_terkait, check_unknown_classifier_is_named,
                  check_this_module_reads_nothing):
        failures, count = check()
        total += count
        bad += failures
        print(f"  {check.__name__:<34} {count - len(failures)}/{count}")
    for line in bad:
        print("FAIL", line)
    print(f"{total - len(bad)}/{total} checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
