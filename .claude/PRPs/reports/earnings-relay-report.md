# Implementation Report: Earnings Relay

## Summary

Built `src/earnings-relay/`, the third product in the repo: a scheduled workflow that
turns one newly detected IDX quarterly report into one review-ready content pack whose
every figure carries the endpoint, field, formula and `as_of` it came from. Standard
library only, reading the harness recordings; zero credits spent (`_ledger.jsonl` still
168 lines). All of P0 (ER-FR-01 … ER-FR-14) and every acceptance test (AT-01 … AT-10) are
implemented and gated.

The plan's blocking data finding was confirmed by opening the files: `recorded/` holds
four trailing quarters per symbol, so the PRD's default year-over-year comparator has no
period to compare against — `comparable_symbols("recorded", "yoy")` returns `[]`. The
product handles it as specified: the demo workspace opts into the sequential comparator
(PRD §9 allows this explicitly), every comparing slide carries the label, and
`gate.comparator_mislabelled` rejects any sentence that describes it as year-on-year. The
full YoY path is exercised on `synth/`, labelled `DATA SINTETIS`.

## Assessment vs Reality

| Metric | Predicted (Plan) | Actual |
|---|---|---|
| Complexity | Large, ~2,700 lines across 10 product files | 6,126 lines across 12 product files, plus a 142-line run.sh |
| Confidence | — | Every gate green on the first full suite run |
| Files Changed | 13 created, 3 updated | 15 created, 3 updated |

## Tasks Completed

| # | Task | Status | Notes |
|---|---|---|---|
| 1 | Research folder — mirror the PRD | Complete | `prd.md` (256 lines) + `deep-research.md` (193 lines, Storyboard and User Flow tabs appended) |
| 2 | `sources.py` — the data contract | Complete | Six divergences asserted, not assumed; run order swapped with Task 3 (see Deviations) |
| 3 | `periods.py` — keys and comparators | Complete | Written first; `sources` imports it so no label is ever trusted |
| 4 | `metrics.py` — the three metrics | Complete | |
| 5 | `factset.py` — immutability and restatement | Complete | |
| 6 | `store.py` — SQLite state and audit | Complete | |
| 7 | `adapter.py` — the only socket | Complete | |
| 8 | `template.py` — five slides | Complete | Plus `money.py` (see Deviations) |
| 9 | `gate.py` — the Claim Risk Gate | Complete | 12 adversarial drafts, one per reason code |
| 10 | `relay.py` — CLI, state machine, AT gates | Complete | 13 gates, not 12 (see Deviations) |
| 11 | `webapp.py` and `run.sh` | Complete | Five routes, POST review/edit through the same RBAC |
| 12 | The capture plan, written not run | Complete | 64 credits, `est_total_cost` computed; not executed |
| 13 | Repo integration | Complete | `.gitignore`, `CLAUDE.md`, and two temp-file defects fixed in `src/pump-and-dump/run.sh` |

## Validation Results

| Level | Status | Notes |
|---|---|---|
| Static analysis | Pass | `python3 -m py_compile src/earnings-relay/*.py`, `bash -n run.sh` — silent |
| Unit gates | Pass | Every module has its own `__main__` gate; each has negative cases |
| Product self-test | Pass | `relay.py --self-test`: 13 PASS lines, AT-01 … AT-10 + comparator honesty + YoY on synth + credit ledger |
| Full suite | Pass | `./run.sh test`: 8 module gates, adapter, relay, webapp, then `verify_mock.py` and `reconcile_usage.py` |
| Integration | Pass | Real HTTP: AT-09 drives a local server that answers 503, 503, 200 through `adapter._get`'s retry path; UI POSTs exercised over the wire |
| Edge cases | Pass | Null required field, zero denominator, sign change, rounding boundary, restatement mid-review, stale version, RBAC refusal, empty comparator set |
| Browser | Pass | `/`, `/queue`, `/draft/1`, `/setup` all 200; draft page rendered and inspected; approve-as-ops refused in words, approve-as-compliance accepted, edit → `rejected: number_mismatch` |

## Files Changed

| File | Action | Lines |
|---|---|---|
| `research/plan/earnings-relay/prd.md` | CREATED | +256 |
| `research/plan/earnings-relay/deep-research.md` | CREATED | +193 |
| `src/earnings-relay/sources.py` | CREATED | +527 |
| `src/earnings-relay/periods.py` | CREATED | +253 |
| `src/earnings-relay/metrics.py` | CREATED | +349 |
| `src/earnings-relay/money.py` | CREATED | +320 |
| `src/earnings-relay/factset.py` | CREATED | +556 |
| `src/earnings-relay/store.py` | CREATED | +814 |
| `src/earnings-relay/adapter.py` | CREATED | +485 |
| `src/earnings-relay/template.py` | CREATED | +488 |
| `src/earnings-relay/gate.py` | CREATED | +411 |
| `src/earnings-relay/relay.py` | CREATED | +1342 |
| `src/earnings-relay/webapp.py` | CREATED | +581 |
| `src/earnings-relay/run.sh` | CREATED | +142 |
| `research/harness/plans/plan-earnings-relay.json` | CREATED | +107 |
| `.gitignore` | UPDATED | +5 |
| `CLAUDE.md` | UPDATED | +42 |
| `src/pump-and-dump/run.sh` | UPDATED | +9 / -4 |

## Deviations from Plan

1. **`money.py` added (12 product files, not 10).** WHAT: a small pure module for rupiah
   numerals and the parser that reads them back. WHY: `template.py` prints figures and
   `gate.py` compares the numbers in a claim against the facts it cites — both need the
   same formatter and the same parser, and duplicating them is how the two drift apart.
   `src/tunanetra/money.py` could not be reused: it spells numbers as *words* for a
   screen reader, which is the wrong answer for a carousel slide.
2. **Task 3 (`periods.py`) written before Task 2 (`sources.py`).** WHAT: order swapped.
   WHY: `sources.normalize_quarterly` derives `period_key` from the date rather than
   trusting either layer's label, which is divergence 2 — so `sources` imports `periods`,
   and `periods` stays pure with no import back.
3. **13 gates in `relay.py --self-test`, not 12.** WHAT: added `check_yoy_on_synth`. WHY:
   with the recorded comparator resolving to `unknown`, nothing else would ever execute
   the year-over-year arithmetic end to end. The template/`sources` endpoint-hint drift
   check was folded into `check_comparator_honesty` as planned.
4. **AT-09 is driven by a purpose-built local HTTP server, not `mock_server.py --chaos`.**
   WHAT: the gate starts a `socketserver.TCPServer` that answers 503, 503, then the real
   recorded payloads. WHY: the plan's requirement was that the retry path be real rather
   than monkeypatched, and this keeps that property while making the gate deterministic —
   `--chaos` is a probability per request, which would make the suite flaky.
5. **Two temp-file defects fixed in `src/pump-and-dump/run.sh`, not one.** The plan named
   `/tmp/pnd-mock.log`; `/tmp/pnd-gate.out` in the `test` target is the same defect and is
   now `mktemp` too.
6. **`poll_trigger` keeps only the newest report per symbol.** WHAT: added to
   `adapter.poll_trigger`. WHY: the recorded sweep already holds one latest row per
   symbol, but the synthetic trigger carries a multi-year history — without this, a first
   poll on `SOURCE=synth` announces 2024's Q4 as news and opens eight events per symbol.
   Divergence 1, reconciled on the way in so both layers behave the same.
7. **Not committed.** The working tree was already dirty with in-flight `src/tunanetra/`
   work; per the repo's rules nothing here was committed or pushed.

## Issues Encountered

| Issue | Resolution |
|---|---|
| `store.check_audit_append_only` greps this module's own source and matched its own needles | Needles assembled at runtime (`"update " + table`) so the check cannot find itself |
| `money.magnitudes` read `q1-2026` as `-2026` and `31 Maret 2026` as two sums | `mask()` blanks period keys, ISO and Indonesian dates, `/v2/…` paths and percentage-point figures before the number scan; each of those has its own check elsewhere |
| `"Rp8,00 T."` lost its scale suffix to a trailing full stop | Lookahead narrowed from `(?![\w.])` to `(?!\w)` |
| A rate displayed to one decimal failed a relative tolerance at small magnitudes (6,2% vs 6,247%) | Added `money.close_rate`: rates compare at display precision (half a step), magnitudes keep the relative test |
| A sign change rendered `minus Rp500,00 M` and the parser read `+5e11` | Magnitudes compare on absolute value; the sign is carried by a word and checked by `direction_mismatch` |
| `.capitalize()` lowercased "Admin" in the comparator label | `periods.label_sentence()` |
| `./run.sh help` leaked `set -euo pipefail` | Header range narrowed to lines 2–23 |

## Tests Written

| Test file | Tests | Coverage |
|---|---|---|
| `periods.py` | 4 gates, 32 checks | Quarter derivation, rollover, comparator selection, label honesty |
| `sources.py` | 6 gates, 38 checks | All six recorded/synth divergences, asserted against the files |
| `money.py` | 3 gates, 44 checks | Formatting at every scale, parsing, masking, round trip |
| `metrics.py` | 5 gates, 31 checks | Null, zero, non-numeric, sign change, rounding boundary, real ADRO/BBCA vectors |
| `factset.py` | 5 gates, 44 checks | Determinism, provenance, every validate reason, immutability, restatement |
| `store.py` | 5 gates, 34 checks | Duplicate suppression, state machine, delivery idempotency, append-only audit, foreign keys |
| `template.py` | 6 gates, 46 checks | Citations, numbers-from-facts, unknown rendering, sign change, comparator label, labelling |
| `gate.py` | 4 gates, 41 checks | Clean draft, 12 adversarial drafts (one per reason code), unknown downgrade, parsers |
| `adapter.py` | 4 gates, 33 checks | Live-URL refusal, direct fetch, retry policy, fabricated payloads |
| `relay.py` | 13 gates, 85 checks | AT-01 … AT-10, comparator honesty, YoY on synth, credit ledger |
| `webapp.py` | 3 gates, 47 checks | Every route, the evidence panel, and that no arithmetic happens in the view |

## Next Steps

- [ ] Code review via `/code-review`
- [ ] Commit — the tree also carries uncommitted `src/tunanetra/` work; decide whether to
      split that into its own commit first
- [ ] Optional: run `plans/plan-earnings-relay.json` (64 credits of ~623) to make the
      year-over-year comparator computable on real data. `sources.check_series_depth`
      fails on purpose when that happens, as the reminder to switch the demo workspace
      back to the PRD default comparator.
