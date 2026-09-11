# Plan: Earnings Relay — evidence-locked earnings content workflow

## Summary

A scheduled workflow that turns a newly detected IDX quarterly report into one
review-ready content pack whose every number carries the endpoint, field, formula and
`as_of` it came from. Facts are locked before any sentence is written; a claim without a
`fact_id` cannot be rendered. Third product in `src/`, built on the same standard-library
shape as `src/tunanetra/`, reading the harness recordings — zero credits spent.

## User Story

As a Content Operations Manager watching 5–10 IDX tickers,
I want one auditable draft per report event with every figure traceable to its source
field,
So that review time is spent on judgement instead of re-finding numbers, and no
unsupported claim can reach a reviewer.

## Problem → Solution

**Current state.** Generic AI content tools produce fluent earnings captions with numbers
nobody can trace, comparators nobody checked, and claims with no evidence. The bottleneck
is not writing the caption — it is producing a financial draft that can be audited before
a human reads it.

**Desired state.** A poll detects a new report event, deduplicates it by `event_hash`,
fetches facts, validates them, computes exactly three deterministic metrics, freezes them
into an immutable `FactSet`, fills a five-slide Indonesian template whose every factual
slot names a `fact_id`, runs a Claim Risk Gate that blocks unsupported claims, and files
the result in a review queue with a readable audit trail. No auto-publish, no buy/sell
language, no LLM anywhere near a number.

## Metadata

- **Complexity**: Large (10 new product files, ~2,700 lines, plus one capture plan and
  one research folder)
- **Source PRD**: Google Doc `178O5IZHb5bZw-1WZ431E8z_elZ8JeHYk601i3ZBuWR4`, tab 1
  (PRD — Engineering Handoff) and tab 2 (Deep Research — Earnings Relay). Full text
  mirrored during planning; §§1–22 are the authority for every requirement ID below.
- **PRD Phase**: whole P0 (ER-FR-01 … ER-FR-14) + AT-01 … AT-10. P1 (ER-FR-15 … 18) is
  explicitly out of scope.
- **Estimated Files**: 13 created, 3 updated
- **Track**: Sectors Hackathon 2026, Track 2 — Automation & Workflows

## Decisions taken before this plan (user, 2026-09-10)

1. **Scope**: Earnings Relay only. FloatPath (Track 3, doc tabs 3–4) is not planned here.
2. **Stack**: Python standard library only, mirroring `src/tunanetra/`. `sqlite3` and
   `http.server` are stdlib and therefore allowed; no pip, no venv, no build step.
3. **Credits**: none. Build entirely on `research/harness/recorded/` and
   `research/harness/synth/`. A capture plan file is *written* but never run.

---

## Data feasibility — read this before writing any metric code

Verified against the 2026-09-06 capture on 2026-09-10 by opening the files.

### What exists, free

| Need | Source | Reality |
|---|---|---|
| Trigger (ER-FR-02) | `recorded/v2_companies_quarterly-financial-dates__limit-30.json` | `{results:[{symbol,date,quarter}], pagination:{total_count:962, showing:960, merged:true}}` — a **merged full sweep**, one latest row per symbol, 960 symbols. 32 credits already paid. |
| Facts (ER-FR-04) | `recorded/v2_financials_quarterly_{ADRO,BBCA,BBRI,TLKM}__n_quarters-4.json` | list of 4 dicts, ~40 fields, keyed on `date`. **Four symbols only.** |
| Facts at volume | `synth/company/quarterly/{SYMBOL}.json` | 120 symbols × 8 quarters, `Q4-2024 … Q3-2026`. |
| Trigger at volume | `synth/company/quarterly_financial_dates.json` | 120 symbols, nested by year. |

### The blocking finding: YoY is not computable on recorded data

The three PRD metrics (§9) all need the **same fiscal quarter one year earlier**.
Recorded holds only the trailing four quarters:

```
ADRO  2026-03-31  2025-12-31  2025-09-30  2025-06-30     latest q1-2026, no q1-2025
BBCA  2026-06-30  2026-03-31  2025-12-31  2025-09-30     latest q2-2026, no q2-2025
BBRI  2026-03-31  2025-12-31  2025-09-30  2025-06-30
TLKM  2026-06-30  2026-03-31  2025-12-31  2025-09-30
```

There is no recorded payload anywhere that supplies the prior-year quarter. The only
year-over-year figures on disk are BBCA's vendor-computed
`financials.yoy_quarter_revenue_growth = 0.00305775623420816` and
`yoy_quarter_earnings_growth = -0.00136772238340106` inside the one bare company report —
vendor output, not our formula, and BBCA only.

**Resolution, and it is the honest one.** This is exactly the condition PRD §9 and
ER-FR-05 describe, so the product handles it rather than hiding it:

- On `SOURCE=recorded`, the **YoY comparator resolves to
  `metric_status = unknown`, `reason_code = comparator_unavailable`**, and the evidence
  drawer names the exact call that would supply it:
  `/v2/financials/quarterly/{symbol}/?n_quarters=8`. This is the same convention
  `src/tunanetra/reader.py` already uses (*belum diambil* + the endpoint that would have
  had it), and it is a demonstrable fail-closed moment, not a gap.
- The **sequential comparator** (q1-2026 vs q4-2025) *is* computable on recorded data.
  PRD §9 already gates it: "Sequential comparison hanya berjalan jika Admin
  mengaktifkannya secara eksplisit." The recorded demo therefore runs with
  `comparator=sequential` explicitly enabled in workspace config, and every draft carries
  a banner saying so. A sequential comparison must never be narrated with YoY wording.
- The **full YoY path is exercised on `SOURCE=synth`**, which has real same-quarter pairs
  across three years — labelled `DATA SINTETIS` on screen and on the terminal, never the
  product's data source. Metric unit tests run against synth and against hand-built
  fixtures.

A ready-to-run capture tier is written to
`research/harness/plans/plan-earnings-relay.json` (Task 12) so the YoY path can be turned
on later for ~32–48 credits of the 623 remaining. **Do not run it.**

### Six recorded ↔ synth divergences this product must reconcile

`sources.py` exists only for these. Every one is a `KeyError` waiting for the demo.

1. **Trigger shape.** recorded QFD is `{"results":[{symbol,date,quarter}],"pagination":{…}}` —
   flat, one latest row per symbol, `quarter` lowercase (`"q1"`). synth QFD is
   `{symbol: {year: [{quarter,date}]}}` — nested, multi-year, `quarter` uppercase
   (`"Q1"`). Normalize both to `{"symbol","report_date","quarter","period_key"}`.
2. **Quarterly period key.** recorded keys the period on `date` (`"2026-03-31"`) and has
   no quarter label at all; synth uses `report_date` + `quarter` (`"Q1-2026"`).
   `periods.py` derives `period_key` from the date in both cases and never trusts a
   supplied label.
3. **Quarterly field count.** recorded carries ~40 fields; synth carries 11
   (`revenue, earnings, gross_profit, operating_pnl, total_assets, total_equity,
   total_liabilities, operating_cash_flow` + keys). Normalization fills the missing keys
   with `None`, never drops them, so a caller cannot depend on a field only one layer has.
4. **The capex slot is sector-dependent in recorded.** Banks (BBCA, BBRI) carry
   `realized_capital_goods_investment`; everyone else (ADRO, TLKM) carries
   `capital_expenditure`, never both. Already documented at
   [sources.py:24](src/tunanetra/sources.py:24). Earnings Relay does not use capex in its
   three metrics, but the validator must not treat the absent one as a null failure.
5. **Symbol suffix.** every payload uses `ADRO.JK`; the CLI, watchlist and `event_hash`
   use `ADRO`. One `bare_symbol()` on the way in.
6. **Series depth.** recorded = 4 quarters, synth = 8. `available_symbols()` must open
   the files and compute what can actually produce a comparator, per source — never
   assume.

### Mock divergences that matter here

- The mock ignores `?since=`. It replays the merged 960-row QFD sweep whole. The
  incremental cursor is therefore applied **client-side after fetch**, which is what
  ER-FR-02 and PRD §10 ("filter watchlist setelah fetch") already specify. Document it.
- `mock_server.py:737` sets `X-Mock-Source: spec-example` when it has no recording and
  falls back to the OpenAPI example. Treat that header as a hard failure, exactly as
  [reader.py:70](src/tunanetra/reader.py:70) does — a spec example under a real ticker's
  name is a fabricated fact.
- `cost_for` at `mock_server.py:445` bills `n_quarters` per quarter. The mock is the only
  thing this product ever talks to over HTTP.

---

## UX Design

### Before

```
┌──────────────────────────────────────────────────────────┐
│ Laporan Q2 keluar                                        │
│   → cek IDX / portal      → salin angka ke spreadsheet   │
│   → hitung YoY di kalkulator                             │
│   → tulis caption di Docs → kirim ke desain              │
│   → chat compliance: "angka ini dari mana?"              │
│   → cari ulang sumbernya                                 │
│ Tidak ada satu tempat pun yang tahu run ini sudah jalan. │
└──────────────────────────────────────────────────────────┘
```

### After

```
┌──────────────────────────────────────────────────────────┐
│ ./run.sh poll                                            │
│   RUN 3  ADRO  q1-2026   new       → draft #7            │
│   RUN 4  ADRO  q1-2026   duplicate → event_hash cocok    │
│   RUN 5  TLKM  q2-2026   failed    → 503, retry 2/3      │
│   RUN 6  TLKM  q2-2026   new       → draft #8  (pulih)   │
│                                                          │
│ Review Queue → Draft #7                                  │
│   Slide 2 "Pendapatan Rp8,00 T"      supported  ▸fact_3  │
│     └ /v2/financials/quarterly/ADRO/ · revenue           │
│       · 8004471444300 · 2026-03-31 · as_of 2026-09-06    │
│   Slide 3 "tumbuh 12% YoY"           rejected            │
│     └ comparator_unavailable — butuh ?n_quarters=8       │
│   [Approve] disabled: 1 klaim belum selesai              │
└──────────────────────────────────────────────────────────┘
```

### Interaction changes

| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Detecting a new report | manual portal check | `poll` tick, cursor + `event_hash` | ER-FR-02, ER-FR-03 |
| Same report seen twice | duplicate draft, nobody notices | `duplicate`, points at canonical `event_id`, no new Draft | AT-02 |
| A number's provenance | ask in chat | evidence drawer: endpoint, field, raw, normalized, formula, comparator, `as_of` | ER-FR-14 |
| A number that cannot be computed | silently becomes 0 or gets guessed | `unknown` + `reason_code` + the endpoint that would supply it | ER-FR-05, AT-03, AT-04 |
| Editing a factual span | caption ships as edited | claim drops to `needs_review`, revalidation runs | ER-FR-11, AT-07 |
| Approving | informal | blocked while any claim is `rejected`/`needs_review` | AT-08 |

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | [src/tunanetra/sources.py](src/tunanetra/sources.py) | 1–200 | The exact divergence-layer shape to copy: module docstring lists every measured divergence, `load()` slug map, `rows_of`, `bare_symbol`, `available_symbols`, `NotRecorded`, `SyntheticOnly`, `window_of` |
| P0 | [src/tunanetra/reader.py](src/tunanetra/reader.py) | 1–100, 200–332 | `cite()` fail-closed verifier, `UncitedFigure`/`Fabricated`, `SOURCE_NOTE`, `DISCLAIMER`, the `check_*` → `self_test()` gate protocol, `main()` argparse shape |
| P0 | [src/tunanetra/run.sh](src/tunanetra/run.sh) | all (89) | Command dispatch, `SOURCE`/`PORT` env, the `test` target that runs product gates then harness gates, `help` via `sed` on its own header |
| P0 | [src/pump-and-dump/run.sh](src/pump-and-dump/run.sh) | 26–95 | Mock lifecycle: `mock_is_up`, reuse-if-running, background start, readiness poll, `trap cleanup EXIT INT TERM`, only killing what this invocation started |
| P1 | [src/pump-and-dump/sources.py](src/pump-and-dump/sources.py) | 1–120 | Second worked example of the same divergence layer, on different endpoints |
| P1 | [src/tunanetra/webapp.py](src/tunanetra/webapp.py) | 1–60, 322–401 | `STYLE` block, semantic-HTML conventions, `do_GET` routing, `socketserver.TCPServer` + `allow_reuse_address`, `--self-test` |
| P1 | [src/tunanetra/money.py](src/tunanetra/money.py) | all (319) | A pure module with its own `__main__` gate — the shape `metrics.py` and `periods.py` must take |
| P1 | [src/pump-and-dump/fragility.py](src/pump-and-dump/fragility.py) | 1–80 | Pure scorer: no I/O, no HTTP, no file paths. Same contract for `metrics.py` |
| P2 | [research/harness/src/mock_server.py](research/harness/src/mock_server.py) | 180–200, 440–490, 570–600, 730–745 | Path→fixture map, `cost_for`, `/__usage`, `X-Mock-Source` |
| P2 | [CLAUDE.md](CLAUDE.md) | all | Grant rules, layer fidelity order, hackathon constraints |
| P2 | [src/tunanetra/a11y_check.py](src/tunanetra/a11y_check.py) | all (294) | The `--broken` self-check idiom: prove a gate fails on bad input, not just passes on good |

## External Documentation

| Topic | Source | Key takeaway |
|---|---|---|
| Trigger endpoint | `research/docs/api/` + PRD §10 | `GET /v2/companies/quarterly-financial-dates/?since={cursor}`; ~950 issuers, 30/page, ~32 credits for a full sweep |
| Facts endpoint | PRD §10, `research/docs/api/02-endpoint-reference.md` | `GET /v2/financials/quarterly/{symbol}/?approx=true`; **never let `n_quarters` default** (CLAUDE.md) |
| Regulatory frame | PRD research §2 | POJK 22/2023 and POJK 6/2026 make published financial claims a supervised activity. The product must never emit a compliance verdict; a human approver is mandatory |
| Track 2 rubric | PRD research §9 | Automation proof = schedule, state, no-op, dedupe, delivery, audit — all four must be visible in the demo |

**No external library research needed** — standard library only, and every pattern is
already in this repository.

---

## Patterns to Mirror

Copy these shapes exactly. New code should be indistinguishable from existing code.

### MODULE_DOCSTRING — a module opens by naming what would otherwise break
```python
# SOURCE: src/tunanetra/sources.py:1-40
"""
One shared way to read the six payloads this product narrates.

Everything here exists because `recorded/` and `synth/` disagree, and every disagreement
is a `KeyError` waiting for the demo. `narrate.py` never sees a raw payload and
`reader.py` never reaches into a dict with `[]`.

    from sources import load, rows_of, normalize_daily, available_symbols

The measured divergences, all re-checked against the 2026-09-06 capture on 2026-09-10:

  1. segments — `recorded/` is `{symbol, financial_year, revenue_breakdown[]}`, …
"""
```

### PATH_CONSTANTS — one file knows where the harness is
```python
# SOURCE: src/tunanetra/sources.py:44-52
HERE = os.path.dirname(os.path.abspath(__file__))          # src/tunanetra/
ROOT = os.path.dirname(os.path.dirname(HERE))              # the repository root

#: The data layers live in the research harness, not beside the product: they were paid
#: for in credits, they are evidence, and the ledger that records what they cost lives
#: next to them. This is the only file that knows the path.
HARNESS = os.path.join(ROOT, "research", "harness")
RECORDED = os.path.join(HARNESS, "recorded")
SYNTH = os.path.join(HARNESS, "synth")
```

### ENDPOINT_MAP — every figure can name the call it came from
```python
# SOURCE: src/tunanetra/sources.py:56-64
ENDPOINT = {
    "overview": "/v2/company/report/{symbol}/?sections=overview",
    "daily": "/v2/daily/{symbol}/",
    "quarterly": "/v2/financials/quarterly/{symbol}/?n_quarters=4",
}
```

### ERROR_HANDLING — named exceptions whose docstring is the reason they exist
```python
# SOURCE: src/tunanetra/sources.py:90-105
class NotRecorded(Exception):
    """Asked for a payload this source does not hold.

    Raised rather than returning an empty list, because "no data" and "no file" produce
    different sentences: the first is a finding, the second is *belum diambil*. Only the
    caller knows which it is looking at, so this never degrades on its own.
    """


class SyntheticOnly(Exception):
    """A claim that only the synthetic layer can support.

    The hackathon rules forbid shipping synthetic data as the product's data source.
    """
```

### DEFENSIVE_ACCESS — never index a payload
```python
# SOURCE: src/tunanetra/sources.py:150-168
def rows_of(payload):
    """The rows of a payload, whether it wraps them or is already a list."""
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "results"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def bare_symbol(symbol):
    """`BBCA.JK` and `BBCA` are the same stock. Payloads use the suffix, the CLI does not."""
    if not symbol:
        return ""
    return symbol.split(".")[0].upper()
```

### CAPABILITY_DISCOVERY — open the files, never assume
```python
# SOURCE: src/tunanetra/sources.py:170-183
def available_symbols(source="recorded"):
    """Which symbols have every core dataset. Never guesses — it opens the files."""
    found = []
    for symbol in OFFLINE_SYMBOLS:
        try:
            for dataset in CORE_DATASETS:
                load("recorded", dataset, symbol)
        except NotRecorded:
            continue
        found.append(symbol)
    return found
```

### FAIL_CLOSED_VERIFIER — the citation gate raises, it does not degrade
```python
# SOURCE: src/tunanetra/reader.py:65-80
class UncitedFigure(Exception):
    """A figure reached render without an endpoint, a field, and a window."""


class Fabricated(Exception):
    """A payload the mock invented rather than replayed.

    `X-Mock-Source: spec-example` means the answer is the OpenAPI example, not this
    company's data. Treated as a hard failure here, not a warning.
    """


def cite(citation):
    """Return a printable citation, or raise. The only way a figure gets to the page."""
```

### GATE_PROTOCOL — every check returns (failures, checked) and self_test tallies
```python
# SOURCE: src/tunanetra/reader.py:277-296
def self_test():
    results = [("citation verifier", *check_citation()),
               ("degradation", *check_degradation()),
               ("no advice, no level-1", *check_no_advice()),
               ("source labelling", *check_source_labelled()),
               ("credit ledger", *check_ledger())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)
    return 1 if failed else 0
```

### NEGATIVE_TEST — prove the gate rejects, not only that it accepts
```python
# SOURCE: src/tunanetra/reader.py:196-212
    bad = [
        ({"endpoint": "", "fields": ["close"], "as_of": "x"}, "empty endpoint"),
        ({"endpoint": "daily", "fields": ["close"], "as_of": "x"}, "non-Sectors path"),
        ({"endpoint": "/v2/daily/", "fields": [], "as_of": "x"}, "no field"),
        ({"endpoint": "/v2/daily/", "fields": ["close"], "as_of": ""}, "no window"),
        ("not a dict", "wrong type"),
    ]
    for citation, why in bad:
        try:
            cite(citation)
        except UncitedFigure:
            continue
        failures.append(f"an uncited figure was allowed through: {why}")
```

### CREDIT_LEDGER_GATE — a run that leaked a credit fails the suite
```python
# SOURCE: src/tunanetra/reader.py:262-274
def check_ledger():
    """This product spends nothing. A run that leaked a credit fails the suite."""
    failures = []
    ledger = os.path.join(sources.RECORDED, "_ledger.jsonl")
    with open(ledger) as handle:
        lines = sum(1 for _ in handle)
    if lines != 168:
        failures.append(f"the credit ledger moved: {lines} lines, expected 168 — "
                        f"something in this product reached the live API")
    return failures, 1
```
**Verified 2026-09-10: `_ledger.jsonl` is still 168 lines.** Reuse the same constant.

### SOURCE_LABELLING — a hackathon rule, not a nicety
```python
# SOURCE: src/tunanetra/reader.py:41-52
DISCLAIMER = ("Alat informasi dan analisis, bukan nasihat investasi. "
              "Tidak ada rekomendasi beli atau jual, dan tidak ada eksekusi transaksi.")

SOURCE_NOTE = {
    "recorded": ("data asli Sectors, rekaman 6 September 2026 — "
                 "jendela setiap deret dicantumkan"),
    "synth": ("DATA SINTETIS, bukan pasar sungguhan — hanya untuk pengembangan, "
              "tidak pernah menjadi sumber data produk"),
    "mock": "mock lokal di atas rekaman yang sama; nol kredit",
}
```

### CLI_SHAPE
```python
# SOURCE: src/tunanetra/reader.py:299-332
def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="reader.py",
        description="Riset fundamental IDX yang bisa didengar. …")
    parser.add_argument("command", nargs="?", default="read",
                        choices=("read", "symbols"))
    parser.add_argument("--source", default="recorded", choices=("recorded", "synth"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    …
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### RUNSH_DISPATCH
```bash
# SOURCE: src/tunanetra/run.sh:20-46
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"
HARNESS="$ROOT/research/harness"
PORT="${PORT:-8081}"
SOURCE="${SOURCE:-recorded}"

command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 127; }

case "${1:-all}" in
  all|ui)
    exec python3 "$DIR/webapp.py" --port "$PORT" --source "$SOURCE"
    ;;
```

### RUNSH_MOCK_LIFECYCLE
```bash
# SOURCE: src/pump-and-dump/run.sh:30-79
mock_is_up() { … curl -fsS "http://127.0.0.1:$MOCK_PORT/v2/subsectors/" 2>/dev/null ; }

    mock_pid=""
    if mock_is_up; then
      echo "mock API   ·  already running on :$MOCK_PORT — reusing it"
    else
      python3 "$HARNESS/src/mock_server.py" --port "$MOCK_PORT" --credits 1000 \
        >/tmp/pnd-mock.log 2>&1 &
      mock_pid=$!
      for _ in $(seq 1 40); do mock_is_up && break; sleep 0.25; done
    fi
    # Only what this invocation started: a mock that was already up belongs to somebody
    cleanup() { trap - EXIT INT TERM; [ -n "$mock_pid" ] && kill "$mock_pid" 2>/dev/null || true; }
    trap cleanup EXIT INT TERM
```
**GOTCHA — do not copy the log path.** `>/tmp/pnd-mock.log` is a fixed predictable path in
a world-writable directory: a pre-planted symlink there makes this a redirect-to-arbitrary-file
sink. Use `LOG="$(mktemp -t er-mock)"` and print that path instead. Fix the same defect in
`src/pump-and-dump/run.sh` while you are here (Task 13).

### RUNSH_TEST_TARGET
```bash
# SOURCE: src/tunanetra/run.sh:53-78
  test)
    # This product's gates first, then the harness's, so a failure here is attributable
    # to this folder rather than to the data layer underneath it.
    status=0
    for gate in sources money narrate; do
      echo "── $gate"
      python3 "$DIR/$gate.py" || status=1
    done
    echo "── harness: mock vs captured API"
    (cd "$HARNESS" && python3 src/verify_mock.py >/dev/null) || status=1
    echo "── harness: credit ledger vs portal usage log"
    (cd "$HARNESS" && python3 src/reconcile_usage.py >/dev/null) || status=1
    exit "$status"
    ;;
```

### WEBAPP_SERVER
```python
# SOURCE: src/tunanetra/webapp.py:322, 373-391
    def do_GET(self):
        …

def main(argv=None):
    parser.add_argument("--self-test", action="store_true")
    …
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), Handler) as server:
        server.serve_forever()
```

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `research/plan/earnings-relay/prd.md` | CREATE | CLAUDE.md: every `src/` folder is named after its research folder. The PRD lives in a Google Doc today; mirror it into the repo so the product has provenance |
| `research/plan/earnings-relay/deep-research.md` | CREATE | Doc tab 2 (research + competitive matrix + sources) |
| `src/earnings-relay/run.sh` | CREATE | Per-idea launcher. Bare = mock + UI |
| `src/earnings-relay/sources.py` | CREATE | The one place the six recorded/synth divergences reconcile |
| `src/earnings-relay/periods.py` | CREATE | `period_key`, fiscal-quarter derivation, comparator selection. Pure |
| `src/earnings-relay/metrics.py` | CREATE | The three metrics. Pure, no I/O |
| `src/earnings-relay/factset.py` | CREATE | Immutable FactSet, provenance, `source_hash`, versioning/restatement |
| `src/earnings-relay/template.py` | CREATE | Five-slide outline + Indonesian caption, every factual slot naming a `fact_id`. Pure |
| `src/earnings-relay/gate.py` | CREATE | Claim Risk Gate: fact linkage, prohibited phrase, number/period/direction check |
| `src/earnings-relay/store.py` | CREATE | SQLite state + idempotency + append-only audit |
| `src/earnings-relay/adapter.py` | CREATE | The only module that speaks HTTP, and only to the mock |
| `src/earnings-relay/relay.py` | CREATE | CLI, orchestrator, state machine, `self_test()` with AT-01…AT-10 |
| `src/earnings-relay/webapp.py` | CREATE | Runs / Review Queue / Draft & Evidence / Audit. A view over `relay.py` |
| `research/harness/plans/plan-earnings-relay.json` | CREATE | The YoY capture tier — **written, never run** |
| `.gitignore` | UPDATE | Add `src/earnings-relay/runs.jsonl` and `src/earnings-relay/state/` |
| `CLAUDE.md` | UPDATE | Third idea in the layout tree and the commands block |
| `src/pump-and-dump/run.sh` | UPDATE | Fix the `/tmp/pnd-mock.log` predictable-path defect |

## NOT Building

- **Any live API call.** No `capture.py` run, no `curl`, no client that can reach
  `api.sectors.app`. The only HTTP this product speaks is to `mock_server.py` on
  localhost.
- **An LLM narrative engine.** PRD §21 leaves it open; MVP resolves it as
  template-only. No API key, no dependency, and a template cannot invent a number. The
  Claim Risk Gate stays and is tested against hand-written adversarial drafts.
- **Auto-publish, webhooks, Canva, PNG/PDF export** (ER-FR-17, P1).
- **ER-FR-15 tone variants, ER-FR-16 per-sector templates, ER-FR-18 rule analytics** (P1).
- **Real authentication.** RBAC is enforced as a role passed on the command/request and
  checked server-side; there is no login, no password, no session store. Documented as a
  limitation in the README.
- **A cron daemon.** `poll` is one tick; `poll --watch --every N` loops in-process for the
  unattended demo.
- **FloatPath** (doc tabs 3–4). Separate plan, separate folder, if it happens at all.
- **Any compliance verdict.** The UI never says "compliant", "aman", or "sesuai
  ketentuan".

---

## Step-by-Step Tasks

### Task 1: Research folder — mirror the PRD into the repo
- **ACTION**: Create `research/plan/earnings-relay/` with `prd.md` (doc tab 1, §§1–22
  verbatim) and `deep-research.md` (doc tab 2, including the sources list [1]–[23] and
  the competitive matrix table).
- **IMPLEMENT**: Straight markdown. Add a header line naming the Google Doc ID and the
  date the mirror was taken (2026-09-10), because the doc can change and the repo copy is
  what the build answers to.
- **MIRROR**: `research/plan/tunanetra/` layout — `deep-research.md`, `ringkas.md`,
  `diagrams/`.
- **GOTCHA**: CLAUDE.md states products are named after their research folder. Getting
  this wrong breaks the repo's one structural rule. Folder name is `earnings-relay`, and
  the product folder must match exactly.
- **VALIDATE**: `ls research/plan/earnings-relay/` shows both files; the `src/` folder
  created in Task 3 has the identical name.

### Task 2: Freeze the data contract — write `sources.py` first, before any logic
- **ACTION**: Create `src/earnings-relay/sources.py`.
- **IMPLEMENT**:
  - Module docstring listing the **six divergences** from the "Data feasibility" section
    above, each with the concrete shape on both sides, re-checked today.
  - `HERE`/`ROOT`/`HARNESS`/`RECORDED`/`SYNTH` exactly as MIRROR:PATH_CONSTANTS.
  - `ENDPOINT = {"trigger": "/v2/companies/quarterly-financial-dates/",
    "quarterly": "/v2/financials/quarterly/{symbol}/?n_quarters=4",
    "quarterly_yoy": "/v2/financials/quarterly/{symbol}/?n_quarters=8"}` — the third one
    is never called; it is the string the `unknown` reason quotes.
  - `NotRecorded`, `SyntheticOnly` (MIRROR:ERROR_HANDLING).
  - `load(source, dataset, symbol=None)` with the recorded slug map
    (`v2_companies_quarterly-financial-dates__limit-30`,
    `v2_financials_quarterly_{symbol}__n_quarters-4`) and the synth path map
    (`synth/company/quarterly_financial_dates.json`,
    `synth/company/quarterly/{symbol}.json`).
  - `rows_of`, `bare_symbol` (MIRROR:DEFENSIVE_ACCESS).
  - `normalize_trigger_row(row, source)` → `{"symbol","report_date","quarter","source"}`,
    flattening synth's nested `{symbol:{year:[…]}}` and lowercasing `quarter`.
  - `normalize_quarterly(row, source)` → a fixed key set with `None` for absent fields,
    reading the period from `date` (recorded) or `report_date` (synth).
  - `OFFLINE_SYMBOLS = ("ADRO", "BBCA", "BBRI", "TLKM")` with the comment that this is the
    intersection of the recorded quarterly payloads, computed by opening the files.
  - `available_symbols(source)` (MIRROR:CAPABILITY_DISCOVERY), plus
    `comparable_symbols(source, comparator)` which returns only symbols where the chosen
    comparator has both periods present.
  - `__main__` gate asserting all six divergences are **still exactly these** — a
    self-check that fails loudly if the harness data is regenerated.
- **IMPORTS**: `glob`, `json`, `os`.
- **GOTCHA**: recorded QFD is a single merged sweep — `pagination.merged == true`,
  `showing == 960`, `total_count == 962`. It is not paginated at read time and it holds
  exactly one latest row per symbol. Do not write pagination-walking code against it.
- **VALIDATE**: `python3 src/earnings-relay/sources.py` exits 0 and prints the six
  divergences it confirmed.

### Task 3: `periods.py` — period keys and comparator selection
- **ACTION**: Create `src/earnings-relay/periods.py`. Pure: no I/O, no imports from
  `sources`.
- **IMPLEMENT**:
  - `period_key(date_str)` → `"q1-2026"`. Derive from the month: 03→q1, 06→q2, 09→q3,
    12→q4. Any other month raises `UnknownPeriod` — never guess.
  - `prior_year_same_quarter(key)` → `"q1-2025"`.
  - `prior_sequential(key)` → `"q4-2025"` (rolls the year at q1).
  - `select_comparator(target_key, available_keys, mode)` where mode is
    `"yoy"` (PRD default) or `"sequential"` (Admin opt-in). Returns
    `(comparator_key, status, reason_code)` — `("q1-2025", "unavailable",
    "comparator_unavailable")` when the prior period is absent.
  - `COMPARATOR_LABEL = {"yoy": "vs kuartal yang sama tahun lalu",
    "sequential": "vs kuartal sebelumnya (perbandingan berurutan, diaktifkan Admin)"}` —
    the wording is load-bearing: a sequential comparison narrated as YoY is a factual
    error, and `gate.py` checks for it.
  - `__main__` gate: q1↔q4 year rollover, a December-31 FY date, an unknown month, an
    empty availability set.
- **IMPORTS**: `datetime` only.
- **GOTCHA**: IDX quarterly dates are period-end dates (`2026-03-31`), not filing dates.
  A fiscal year that is not calendar-aligned would break the month mapping — none of the
  four recorded symbols has one, so raise `UnknownPeriod` rather than inferring.
- **VALIDATE**: `python3 src/earnings-relay/periods.py` exits 0.

### Task 4: `metrics.py` — the three metrics, pure
- **ACTION**: Create `src/earnings-relay/metrics.py`.
- **IMPLEMENT**: Exactly three functions, exactly as PRD §9. Each returns a dict
  `{"type","value","display","status","reason_code","inputs","formula","comparator"}`.
  - `revenue_yoy(rev_t, rev_prior)` = `rev_t / rev_prior - 1`. Prior `None` or `0` →
    `status="unknown"`, `reason_code="denominator_zero"` (or `"missing_input"`), value
    `None`. **Never render a percentage for an unknown.**
  - `net_income_yoy(ni_t, ni_prior)` — same, plus: if the sign flips,
    `status="sign_change"` and `display` carries absolute values, never a growth
    percentage. A profit-to-loss swing narrated as "-340% growth" is the exact failure
    mode PRD §9 names.
  - `net_margin_delta(ni_t, rev_t, ni_prior, rev_prior)` =
    `(ni_t/rev_t) - (ni_prior/rev_prior)`, expressed in **percentage points**, not
    percent. Either denominator zero/null → `unknown`.
  - `direction(value)` → `"naik" | "turun" | "datar"`, computed on the **unrounded**
    value (PRD §9). `round_display(value)` lives here and is applied only at display.
  - `MetricStatus` constants: `ok`, `unknown`, `sign_change`.
  - `__main__` gate with a table of cases: null prior, zero prior, sign change,
    zero revenue, negative revenue, a rounding boundary that flips direction if rounded
    first, and both real ADRO/BBCA vectors from the recorded payloads.
- **IMPORTS**: nothing but the standard library; no `sources` import (MIRROR:
  `fragility.py` is pure — "no I/O, no HTTP, no file paths").
- **GOTCHA**: `-0.0` and float boundaries. `src/pump-and-dump/fragility.py` already hit
  and fixed a float-boundary defect; use `>=`/`<=` deliberately and pin the intended side
  in a comment.
- **VALIDATE**: `python3 src/earnings-relay/metrics.py` exits 0.

### Task 5: `factset.py` — immutability, provenance, restatement
- **ACTION**: Create `src/earnings-relay/factset.py`.
- **IMPLEMENT**:
  - `Fact` = `{"fact_id","field","raw_value","normalized_value","unit","period",
    "endpoint","as_of","quality"}`. `fact_id` is deterministic:
    `sha256(f"{symbol}|{period_key}|{field}|{raw_value}")[:12]`.
  - `build_factset(symbol, period_key, rows, comparator, source)` → the fact list plus
    `{"fact_set_id","version","source_hash","rule_version","locked_at"}`.
    `source_hash = sha256(canonical_json(rows))` — the reproducibility key.
  - `validate(facts)` implementing ER-FR-05: required field null → reject; comparator
    periods of different kinds → reject; unknown unit → reject; denominator zero →
    `unknown`, not reject. Returns `(ok, [reason_codes])`.
  - `lock(factset)` — after this, mutation raises `FactSetLocked`. Implement as a frozen
    dict-of-tuples plus an explicit guard; do not rely on convention.
  - `restate(old, new_rows)` → **version 2, never an overwrite** (ER-FR-07). Returns the
    new FactSet plus the list of `fact_id`s whose value changed, which `relay.py` uses to
    push affected claims back to `needs_review` (AT-05).
  - `RULE_VERSION = "er-rules-1"` and `FORMULA_VERSION = "er-formula-1"` constants,
    stamped on everything.
  - `__main__` gate: same inputs → same `source_hash` and same `fact_id`s (determinism);
    mutation after lock raises; restatement bumps version and reports changed ids.
- **IMPORTS**: `hashlib`, `json`, `time`.
- **GOTCHA**: `canonical_json` must be `json.dumps(obj, sort_keys=True,
  separators=(",", ":"))`. A hash over default `json.dumps` is not stable across dict
  insertion order and silently breaks the determinism gate.
- **VALIDATE**: `python3 src/earnings-relay/factset.py` exits 0.

### Task 6: `store.py` — state, idempotency, append-only audit
- **ACTION**: Create `src/earnings-relay/store.py`. SQLite (`sqlite3`, standard library)
  at `src/earnings-relay/state/relay.db`, created on first use.
- **IMPLEMENT**:
  - Schema per PRD §13: `workspace`, `watchlist_item`, `report_event`, `run`, `fact_set`,
    `metric`, `draft`, `claim`, `review_decision`, `delivery`, `audit_event`.
  - `event_hash = sha256(f"{workspace_id}|{symbol}|{period_key}|{report_date}|{source_version}")`
    (ER-FR-03), with **`UNIQUE(event_hash)` on `report_event`** — PRD §15 makes the
    database constraint the last line of deduplication, so it must actually exist.
  - `UNIQUE(idempotency_key)` on `delivery` (ER-FR-12).
  - `transition(event_id, from_state, to_state, actor, reason_code, correlation_id)` —
    atomic, in one transaction, writing both the new state and one `audit_event` row.
    Refuses a transition whose `from_state` does not match the current state, so a
    concurrent writer cannot skip a step (PRD §12).
  - `STATES` and `ALLOWED` transition table, exactly PRD §12:
    `discovered → fetching → validated → fact_locked → drafted → needs_review → approved`;
    `needs_review → rejected → revised → needs_review`; terminals `no_op`, `duplicate`,
    `failed`.
  - `audit_event` is append-only: no `UPDATE` or `DELETE` statement anywhere in the file.
  - `append_run_ledger(record)` writing a human-readable line to
    `src/earnings-relay/runs.jsonl`, mirroring tunanetra's `runs.jsonl` convention.
  - `__main__` gate: inserting the same `event_hash` twice raises `IntegrityError` and is
    reported as `duplicate`; an out-of-order transition is refused; the audit table has no
    mutating SQL.
- **IMPORTS**: `hashlib`, `json`, `os`, `sqlite3`, `time`.
- **GOTCHA**: `sqlite3` autocommit. Use an explicit `with conn:` block for `transition()`
  so the state write and the audit write commit or roll back together. Also set
  `PRAGMA foreign_keys=ON` per connection — SQLite ignores foreign keys by default.
- **VALIDATE**: `python3 src/earnings-relay/store.py` exits 0.

### Task 7: `adapter.py` — the only module that speaks HTTP
- **ACTION**: Create `src/earnings-relay/adapter.py`.
- **IMPLEMENT**:
  - Two modes. `direct` reads through `sources.load()` (no socket at all — the default,
    and what the tests use). `http` talks to `mock_server.py` at
    `MOCK_URL = "http://127.0.0.1:8787"`, for the unattended-poll demo.
  - `RefuseLiveAPI` raised at import time if the configured base URL is not
    `127.0.0.1`/`localhost`. This product must be structurally incapable of billing a
    credit; a hostname check is cheaper than trusting discipline.
  - `Fabricated` check: any response whose `X-Mock-Source` is not `recording` is a hard
    failure (MIRROR:FAIL_CLOSED_VERIFIER). `mock_server.py:737` sets `spec-example` on
    fallback and that is a fabricated fact under a real ticker's name.
  - Retry per PRD §15: max 3 attempts on 429/5xx/network, exponential backoff **with
    jitter**; 4xx schema/auth errors are not retried. Return
    `(payload, {"attempts", "source_as_of", "endpoint", "fetched_at"})`.
  - `poll_trigger(cursor)` — fetch, then filter **client-side** to the watchlist and to
    `report_date > cursor` (ER-FR-02, and the mock ignores `?since=`).
- **IMPORTS**: `json`, `os`, `random`, `time`, `urllib.error`, `urllib.request`.
- **GOTCHA**: Cloudflare blocks `Python-urllib` on the real API (CLAUDE.md). Irrelevant
  against the mock, but set a browser `User-Agent` anyway so the code does not become a
  trap if someone repoints it. Retrying into a 429 extends the lockout — back off, do not
  hammer.
- **VALIDATE**: `python3 src/earnings-relay/adapter.py --self-test` with the mock up;
  asserts `RefuseLiveAPI` fires for `https://api.sectors.app`.

### Task 8: `template.py` — five slides, Indonesian, every factual slot cited
- **ACTION**: Create `src/earnings-relay/template.py`. Pure.
- **IMPLEMENT**:
  - `TEMPLATE_VERSION = "er-carousel-1"`.
  - Five slides: (1) issuer + period, (2) revenue, (3) net income, (4) net margin,
    (5) source and disclaimer.
  - A slot is `{"text","fact_ids","kind"}` where `kind` is `"factual"` or `"framing"`. A
    `factual` slot with an empty `fact_ids` is a bug the gate will reject — assert it here
    too, so it fails at build time rather than gate time.
  - `caption(factset, metrics)` — Bahasa Indonesia, plain, no superlatives. Numbers
    rendered through a money helper (adapt `src/tunanetra/money.py`'s Indonesian
    formatting; do not re-derive it).
  - An `unknown` metric renders as an explicit sentence naming what is missing and the
    endpoint that would supply it — never as an omitted slide and never as zero.
  - The comparator label from `periods.COMPARATOR_LABEL` appears on every slide that
    compares two periods.
  - `DISCLAIMER` and `SOURCE_NOTE` reused verbatim (MIRROR:SOURCE_LABELLING).
  - `__main__` gate: every factual slot has ≥1 `fact_id`; no slide references a `fact_id`
    not in the FactSet; an `unknown` metric never produces a `%` character.
- **IMPORTS**: `periods`, plus the money helper.
- **GOTCHA**: The five-slide count is a PRD requirement (ER-FR-01, §5). Do not make it
  configurable in MVP — ER-FR-16 (per-sector templates) is P1.
- **VALIDATE**: `python3 src/earnings-relay/template.py` exits 0.

### Task 9: `gate.py` — the Claim Risk Gate
- **ACTION**: Create `src/earnings-relay/gate.py`. Pure.
- **IMPLEMENT**: `check_claim(claim, factset, metrics)` →
  `(status, [reason_codes])` where status ∈ `supported | needs_review | rejected`
  (ER-FR-09). Checks, each with its own reason code:
  - `no_fact_id` → **rejected**. A claim without a `fact_id` is rejected, full stop
    (PRD §9).
  - `number_mismatch` → rejected. Every number appearing in the claim text must match a
    fact's `display` value. Parse the numerals out of the string; do not trust the writer.
  - `period_mismatch` → rejected. The period named in the text must equal the fact's
    period.
  - `direction_mismatch` → rejected. "naik"/"turun" must match `metrics.direction()` on
    the unrounded value.
  - `comparator_mislabelled` → rejected. YoY wording (`"YoY"`, `"tahun lalu"`,
    `"year-on-year"`) on a `sequential` comparator. This is the one that protects the
    recorded-data demo from lying.
  - `prohibited_phrase` → rejected. `PROHIBITED = (…)` covering transaction invitations
    (`beli`, `jual`, `akumulasi`, `entry`, `cuan`), price targets (`target harga`, `TP`),
    unbacked superlatives (`terbaik`, `paling untung`, `pasti`), plus an Admin-supplied
    list. Reuse `narrate.ADVICE_VOCAB` from `src/tunanetra/narrate.py` as the seed — that
    list is already gate-tested.
  - `unknown_metric_narrated` → needs_review, when a slot cites a fact whose metric status
    is `unknown` or `sign_change`.
  - `__main__` gate with **adversarial drafts**, mirroring the `--broken` idiom in
    `a11y_check.py`: one draft per reason code that the gate must reject, plus one clean
    draft it must pass. A gate that only ever passes is not tested.
- **IMPORTS**: `re`, `metrics`, `periods`.
- **GOTCHA**: Number matching must normalize Indonesian formatting (`8,00 T`,
  `Rp8.004.471.444.300`) before comparing. Compare on the parsed magnitude, not the
  string.
- **VALIDATE**: `python3 src/earnings-relay/gate.py` exits 0 and reports one rejection per
  adversarial draft.

### Task 10: `relay.py` — CLI, orchestrator, state machine, AT-01…AT-10
- **ACTION**: Create `src/earnings-relay/relay.py`.
- **IMPLEMENT**:
  - Commands: `poll` (one tick; `--watch --every N` loops), `runs`, `draft <id>`,
    `review <draft_id> --decision approve|reject --comment … --as <role>`,
    `symbols`, `--self-test`.
  - `poll()` walks the pipeline per PRD §6: trigger → watchlist filter → `period_key` →
    `event_hash` → new/duplicate/no-op → fetch facts → validate → metrics → lock FactSet →
    template → gate → deliver to review queue. Every step calls `store.transition()`.
  - `--now <iso>` injects the clock so the three-run demo is reproducible; never call
    `time.time()` for anything that lands in a hash.
  - RBAC (ER-FR-10, PRD §15): `approve` requires `--as compliance`; `edit` requires
    `--as ops`. Checked in `relay.py`, not in the UI.
  - Optimistic concurrency on review (PRD §14): `--expected-version`; a stale version is
    refused with a readable message.
  - Edit revalidation (ER-FR-11): changing a factual span drops the claim to
    `needs_review` and reruns `gate.check_claim`.
  - `self_test()` (MIRROR:GATE_PROTOCOL) with one check per acceptance test:

    | Check | Test | Assertion |
    |---|---|---|
    | `check_new_event` | AT-01 | one FactSet, one Draft, one review item |
    | `check_duplicate` | AT-02 | second poll → `duplicate`, Draft count unchanged |
    | `check_null_data` | AT-03 | null required field → `failed`/`needs_review`, never 0 |
    | `check_zero_prior` | AT-04 | → `unknown` + `denominator_zero` |
    | `check_restatement` | AT-05 | new `source_as_of` → FactSet v2, claims back to `needs_review` |
    | `check_unsupported_claim` | AT-06 | no `fact_id` or prohibited wording → `rejected`, cannot submit |
    | `check_edit_invalidates` | AT-07 | factual edit clears `supported` |
    | `check_review_loop` | AT-08 | reject → ops; approve blocked while any claim unresolved |
    | `check_transient_failure` | AT-09 | two retries, one draft, canonical event reused |
    | `check_demo_proof` | AT-10 | alert + no-op + dedup/recovery all readable from the run log |
    | `check_comparator_honesty` | — | on `recorded`, YoY is `unknown` and no output contains YoY wording |
    | `check_ledger` | — | `_ledger.jsonl` still 168 lines (MIRROR:CREDIT_LEDGER_GATE) |

- **IMPORTS**: `argparse`, `json`, `os`, `sys`, `time`, plus every product module.
- **GOTCHA**: AT-09 needs a *transient* failure. Drive it with
  `mock_server.py --chaos`, which returns 429/503 with the real differing body shapes.
  Do not fake it with a monkeypatch — the point is that the retry path is real.
- **VALIDATE**: `python3 src/earnings-relay/relay.py --self-test` exits 0 with 12 PASS
  lines.

### Task 11: `webapp.py` and `run.sh`
- **ACTION**: Create `src/earnings-relay/webapp.py` and `src/earnings-relay/run.sh`.
- **IMPLEMENT**:
  - `webapp.py`: five routes matching PRD §7 — `/` (Runs), `/queue` (Review Queue),
    `/draft/<id>` (Draft & Evidence, with the right-hand evidence panel of ER-FR-14),
    `/audit/<event_id>`, `/setup` (read-only view of workspace config). A **view over
    `relay.py`, not a second engine** — no metric arithmetic in this file.
    `socketserver.TCPServer` + `allow_reuse_address` (MIRROR:WEBAPP_SERVER). Semantic
    HTML: one `<h1>`, `<h2>` per section, `<table>` with `<caption>` and `<th scope>`,
    status never conveyed by colour alone, keyboard reachable (PRD §16 accessibility).
    `--self-test` asserting every route returns 200 and that the evidence panel contains
    endpoint + field + `as_of` for every rendered figure.
  - `run.sh`: bare = mock + UI (MIRROR:RUNSH_MOCK_LIFECYCLE, with `mktemp` for the log).
    Commands: `poll`, `runs`, `draft`, `review`, `symbols`, `demo` (the scripted
    three-run proof for AT-10), `test`, `help`. `SOURCE`, `PORT` (default 8082 — 8080 and
    8081 are taken), `MOCK_PORT` (8787).
  - `test` target runs product gates then harness gates (MIRROR:RUNSH_TEST_TARGET).
- **GOTCHA**: Use `mktemp` for the mock log, not `/tmp/er-mock.log`. See the
  RUNSH_MOCK_LIFECYCLE note.
- **VALIDATE**: `cd src/earnings-relay && ./run.sh test` — all gates green.
  `./run.sh` then load `http://127.0.0.1:8082` and walk Runs → Queue → Draft → Audit.

### Task 12: The capture plan that is written and not run
- **ACTION**: Create `research/harness/plans/plan-earnings-relay.json`.
- **IMPLEMENT**: One tier: `/v2/financials/quarterly/{symbol}/?n_quarters=8` for the four
  recorded symbols plus up to four more from the QFD sweep, every parameter explicit.
  Estimated cost 32–64 credits (`cost_for` bills per quarter). A comment field in the plan
  stating: *not executed as of 2026-09-10; running it flips the YoY comparator from
  `unknown` to computable.*
- **MIRROR**: `research/harness/plans/plan.json` structure.
- **GOTCHA**: **Do not run it.** Not even `--dry-run` against the live base URL. If it is
  ever rehearsed, rehearse against the mock (`SECTORS_BASE_URL=http://127.0.0.1:8787`) and
  delete anything the rehearsal writes into `recorded/` — CLAUDE.md rule.
- **VALIDATE**: `cd research/harness && python3 -c "import json;
  json.load(open('plans/plan-earnings-relay.json'))"` parses. `_ledger.jsonl` still
  168 lines.

### Task 13: Repo integration
- **ACTION**: Update `.gitignore`, `CLAUDE.md`, and `src/pump-and-dump/run.sh`.
- **IMPLEMENT**:
  - `.gitignore`: `src/earnings-relay/runs.jsonl`, `src/earnings-relay/state/`,
    `src/earnings-relay/__pycache__/`.
  - `CLAUDE.md`: third entry in the layout tree with a one-line-per-file description
    matching the existing style; a commands block for `cd src/earnings-relay && ./run.sh`;
    a line in "Architecture" noting that the YoY comparator is unavailable on recorded
    data and why.
  - `src/pump-and-dump/run.sh`: replace the fixed `/tmp/pnd-mock.log` with `mktemp`.
- **GOTCHA**: `CLAUDE.md` is currently modified in the working tree (`git status` shows
  ` M CLAUDE.md`) and `src/tunanetra/` is untracked. Check what is uncommitted before
  editing so you do not clobber an in-flight change.
- **VALIDATE**: `git status` shows only intended changes; `cd src/pump-and-dump &&
  ./run.sh test` still green.

---

## Testing Strategy

### Unit tests (each module's `__main__` gate — the repo has no test framework and needs none)

| Test | Input | Expected output | Edge case? |
|---|---|---|---|
| `revenue_yoy` normal | `8004471444300`, `7000000000000` | `0.1435…`, `status=ok` | no |
| `revenue_yoy` null prior | `8e12`, `None` | `value=None`, `unknown`, `missing_input` | yes |
| `revenue_yoy` zero prior | `8e12`, `0` | `unknown`, `denominator_zero` | yes |
| `net_income_yoy` sign flip | `-500`, `1000` | `sign_change`, absolute display, no `%` | yes |
| `net_margin_delta` | ADRO q1-2026 vs q4-2025 | value in **percentage points** | no |
| `net_margin_delta` zero rev | `ni=100`, `rev=0` | `unknown` | yes |
| `direction` rounding | value `0.00049` | `naik` (unrounded), display `0,0%` | yes |
| `period_key` | `"2026-03-31"` | `"q1-2026"` | no |
| `period_key` bad month | `"2026-05-31"` | raises `UnknownPeriod` | yes |
| `prior_sequential` rollover | `"q1-2026"` | `"q4-2025"` | yes |
| `select_comparator` yoy on recorded | ADRO keys | `("q1-2025","unavailable","comparator_unavailable")` | yes |
| `event_hash` stability | same 5 inputs | identical hash across processes | no |
| `event_hash` uniqueness | second insert | `IntegrityError` → `duplicate` | yes |
| `source_hash` determinism | same rows, shuffled dict order | identical hash | yes |
| FactSet mutation after lock | any write | raises `FactSetLocked` | yes |
| `restate` | new `source_as_of` | version 2, changed `fact_id` list | yes |
| `transition` out of order | `discovered → approved` | refused | yes |
| gate: no `fact_id` | factual slot, empty ids | `rejected`, `no_fact_id` | yes |
| gate: wrong number | text says `9,00 T`, fact `8,00 T` | `rejected`, `number_mismatch` | yes |
| gate: YoY word on sequential | `"naik 3% YoY"` | `rejected`, `comparator_mislabelled` | yes |
| gate: `"target harga 9000"` | any | `rejected`, `prohibited_phrase` | yes |
| gate: clean draft | valid slots | `supported` | no |
| template: unknown metric | `status=unknown` | sentence names the missing endpoint, contains no `%` | yes |
| adapter: live URL | `https://api.sectors.app` | raises `RefuseLiveAPI` | yes |
| adapter: `X-Mock-Source: spec-example` | any | raises `Fabricated` | yes |

### Edge-case checklist

- [ ] Empty watchlist → `no_op`, not a crash
- [ ] Symbol in QFD but with no recorded quarterly → `failed` with `facts_unavailable`,
      naming the endpoint
- [ ] Symbol with quarterly but no comparator period → draft renders, metrics `unknown`
- [ ] Same event polled 3× → 1 draft, 2 `duplicate`
- [ ] Restatement mid-review → v2 FactSet, claims back to `needs_review`, old export
      marked superseded not deleted
- [ ] Mock down entirely → `failed` after 3 retries, run visible, replayable with the same
      idempotency key
- [ ] `--chaos` 429 then success → 1 draft
- [ ] Approve attempted with `--as ops` → refused
- [ ] Approve attempted while one claim is `needs_review` → refused (AT-08)
- [ ] Two reviewers, stale `--expected-version` → refused
- [ ] `SOURCE=synth` anywhere on screen → the string `DATA SINTETIS` is present
- [ ] Negative revenue and negative equity rows do not produce a rendered percentage
- [ ] Concurrent access: two `poll` processes on the same DB → `UNIQUE(event_hash)` makes
      one of them `duplicate`, not a crash

---

## Validation Commands

### Static analysis
```bash
python3 -m py_compile src/earnings-relay/*.py
```
EXPECT: silent, exit 0. (No type checker or linter is configured in this repo; adding one
is out of scope.)

### Per-module gates
```bash
cd src/earnings-relay && for m in sources periods metrics factset store template gate; do python3 $m.py || echo "FAIL $m"; done
```
EXPECT: every module exits 0.

### Product self-test
```bash
cd src/earnings-relay && python3 relay.py --self-test
```
EXPECT: 12 PASS lines, AT-01 through AT-10 plus comparator honesty and the credit ledger.

### Full gate suite, product then harness
```bash
cd src/earnings-relay && ./run.sh test
```
EXPECT: all product gates, then `verify_mock.py` and `reconcile_usage.py`, then
`semua gate lulus · nol kredit terpakai`.

### The three-run demo proof (AT-10)
```bash
cd src/earnings-relay && ./run.sh demo
```
EXPECT: run A `new` → draft; run B `duplicate`, no new draft; run C `failed` under
`--chaos` then recovery to `new` with one draft, all four states readable in the run log.

### Credit guard — the one that must never regress
```bash
wc -l research/harness/recorded/_ledger.jsonl
```
EXPECT: `168`. Any other number means something in this product reached the live API.

### Browser validation
```bash
cd src/earnings-relay && ./run.sh
```
EXPECT: mock on :8787, UI on :8082. Runs → Review Queue → Draft & Evidence → Audit all
render; every figure in the evidence panel shows endpoint, field, raw, normalized,
formula, comparator, `as_of`.

### Manual validation
- [ ] Open a draft whose YoY metric is `unknown`; confirm the reason names
      `/v2/financials/quarterly/{symbol}/?n_quarters=8`
- [ ] Edit a factual span in the queue; confirm the claim drops to `needs_review`
- [ ] Try to approve with an unresolved claim; confirm refusal and readable reason
- [ ] Switch `SOURCE=synth`; confirm `DATA SINTETIS` appears on every screen
- [ ] Confirm no screen anywhere says "compliant", "aman", "sesuai ketentuan", or offers
      a buy/sell action
- [ ] Tab through the queue and the draft page with the keyboard alone

---

## Acceptance Criteria

- [ ] Setup → unattended poll → FactSet → draft → claim validation → review → approval
      runs end to end (PRD §22)
- [ ] ER-FR-01 … ER-FR-14 all implemented
- [ ] AT-01 … AT-10 all pass in `relay.py --self-test`
- [ ] Every factual claim carries `fact_id`, source, period, formula, `as_of`, status
- [ ] Metric logic has unit gates for null, zero, sign change, rounding, period mismatch
- [ ] Scheduler, state, retry, idempotency, deduplication and audit are all demonstrable
      **without opening the database**
- [ ] No buy/sell advice and no auto-publish anywhere in the UI
- [ ] `_ledger.jsonl` unchanged at 168 lines
- [ ] README section in `run.sh help` covers setup, architecture, data contract, demo
      script, limitations

## Completion Checklist

- [ ] Code follows the discovered patterns — a reader cannot tell which product a file
      came from
- [ ] Errors are named exceptions whose docstring says why they exist
- [ ] Synthetic data labelled everywhere it appears
- [ ] Each module has its own `__main__` gate; no gate only tests the happy path
- [ ] No hardcoded numbers outside the named `*_VERSION` and threshold constants
- [ ] `CLAUDE.md` layout tree and commands block updated
- [ ] `src/pump-and-dump/run.sh` temp-file defect fixed
- [ ] No new scope beyond P0

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The demo shows `unknown` for its headline metrics on real data and reads as broken | High | High | Make it the story: fail-closed is the differentiator against generic AI content tools. Sequential comparator carries the numeric demo; the `unknown` panel names the exact call that would fix it. Have `plan-earnings-relay.json` ready to run if the judgement changes |
| Judges read "four symbols" as thin coverage | Medium | Medium | `symbols` command states exactly what is readable and why; synth demonstrates the same pipeline at 120 symbols, labelled |
| Track 2 needs unattended proof; a one-shot `poll` looks manual | Medium | High | `./run.sh demo` scripts the three-run proof with an injected clock; `--watch --every N` shows a real loop |
| Claim Risk Gate is trivially passable because the template is deterministic | Medium | Medium | Adversarial drafts in `gate.py`'s own gate, one per reason code — the `--broken` idiom from `a11y_check.py` |
| Ten modules is more surface than 20 remaining days allow | Medium | High | Tasks 2–6 are the product; 7–11 are shell around them. If time runs short, cut `webapp.py` to Runs + Draft only and keep the CLI complete |
| Accidental live call while wiring the adapter | Low | Severe | `RefuseLiveAPI` at import, no `capture.py` invocation anywhere, ledger gate in the test suite |
| Working tree already dirty (`CLAUDE.md` modified, `src/tunanetra/` untracked) | High | Low | Commit or stash the in-flight tunanetra work before Task 13 |

## Notes

- **Why the folder is `src/earnings-relay/`**: CLAUDE.md's one structural rule is that a
  product folder is named after its research folder. Task 1 creates
  `research/plan/earnings-relay/` so the rule holds.
- **Why SQLite and not JSONL**: PRD §15 makes a database unique constraint the last line
  of deduplication, and PRD §12 requires atomic transitions. `sqlite3` is standard library,
  so this costs nothing against the no-dependency rule and buys a real `UNIQUE` index and
  a real transaction. `runs.jsonl` is kept alongside as the human-readable ledger, matching
  the other two products.
- **Why template-only and no LLM**: PRD §21 leaves it open. Zero dependencies, no API key,
  and a template cannot invent a number. The gate remains, because a template can still
  mislabel a comparator — which is the failure this data situation actually produces.
- **The comparator honesty check is the load-bearing gate.** With recorded data the only
  computable comparison is sequential. A sequential comparison narrated as year-on-year is
  a factual error that would look completely fine on screen. `check_comparator_honesty`
  and `gate.comparator_mislabelled` exist for exactly that, and they are the reason this
  product is not just a caption generator.
- **Untouched**: FloatPath (doc tabs 3–4) is fully researched and specified but not
  planned here. Its data position is better than Earnings Relay's — the 961-row free-float
  sweep is already paid for — so it remains a live option.
