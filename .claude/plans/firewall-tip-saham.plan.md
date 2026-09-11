# Plan: Firewall Tip Saham — MVP

**Source research**: `research/plan/pump-and-dump/deep-research.md`, `ringkas.md`, `agen-risiko-belajar-mandiri.md`
**Selected milestone**: MVP (Stage 1 — engine on local data, zero credits)
**Complexity**: Medium
**Credits spent by this plan**: 0 of ~623 remaining

## Summary

One IDX symbol in, a fragility verdict out, every number carrying its own
`(endpoint, field)` citation. The MVP runs entirely against `research/harness/recorded/`
and `research/harness/synth/` through `mock_server.py`, so the whole engine can be
finished and tested before a single credit is charged. Three fragility axes ship — the
three the research rates `tinggi` — and the learning loop, the ownership axis, and the
real-label evaluation are explicitly deferred.

---

## Part 1 — Verification of the research findings

Every claim below was re-checked this session. Local checks read
`research/harness/recorded/` (the paid 2026-09-06 capture) and
`research/evidence/spec/schema.json`. Two external primary sources were re-fetched.

### Confirmed

| # | Claim | Check | Result |
|---|---|---|---|
| V1 | `/v2/suspensions/` holds 583 rows | `pagination.total_count` | **583**, `has_next: true`, limit 20 |
| V2 | 18 of the 20 most recent rows are cooling-down notices | substring `peningkatan harga kumulatif yang signifikan` | **18/20**, dates 2026-08-11 … 2026-09-04 |
| V3 | Suspension row fields | key set | `symbol, suspension_date, reason, pdf_url` — exact, `pdf_url` points at `idx.co.id` |
| V4 | `/v2/daily/` field set | key set | `symbol, date, open, high, low, close, volume, market_cap` — exact |
| V5 | BNBR was the top-volume name on 2026-08-06 | `recorded/v2_most-traded.json` | **7,994,414,100 shares @ Rp105**, rank 1 of 5 — exact to the digit |
| V6 | `/v2/free-float/` is an undated snapshot, 961 rows | key set | **961 rows**, fields `symbol, company_name, free_float`, **no date field** — the leakage warning stands |
| V7 | `shareholders-composition` is monthly and dated | payload | `{symbol, year, data[]}`, each row dated `2026-08-31`, `2026-07-31`, …, 9 `_l` + 9 `_f` categories + `total_l`/`total_f` |
| V8 | `/v2/news/` carries a scored `dimension` | payload | 8 themes: `future, dividend, ownership, technical, valuation, financials, management, sustainability` |
| V9 | Credit position | `python3 src/reconcile_usage.py` | exit 0 — portal 377, ledger 265, difference 112, **no unexplained discrepancy**. ~623 remain |
| V10 | Nam & Skillicorn, arXiv 2301.11403 | re-fetched from arxiv.org | title, authors, 2023, and **"prediction accuracy of 85% and an F1-score of 62%"** all confirmed |
| V11 | OJK SP 38/GKPB/OJK/II/2026 | re-fetched from ojk.go.id | **"denda sebesar Rp5,35 miliar kepada pegiat media sosial Sdr. BVN"**, 20 Feb 2026, AYLS / FILM / BSML — confirmed verbatim |

### Corrections the research needs

| # | Where | What the research says | What the payload says | Consequence |
|---|---|---|---|---|
| C1 | `deep-research.md` §B8 | `/v2/brokers/` returns `origin` and `cohort` | returns `code, cohort, is_foreign, license_type, name` — **there is no `origin` field**; foreign-ness is the boolean `is_foreign` | a P2 parser reading `broker["origin"]` raises `KeyError` on real data |
| C2 | §B8, §B11 P2 | `broker-summary/{symbol}/top/` returns `origin, cohort` per broker | those two keys are **request echoes** (`"all"`, `"all"`). Each `top_buyers` entry has only `rank, broker_code, net_idr, buy_idr, sell_idr` | cohort weighting needs either a join to `/v2/brokers/` or the `cohort=` query parameter — it is not free in the response |
| C3 | §S3 item 7 (`UNVERIFIED`) | cohort reliability unknown | **resolved, free**: n=88 → `mixed` 42, `institutional` 39, `retail` **5**, `unknown` 2 | only 5 of 88 brokers are labelled `retail`. Output copy like *"four of the five brokers are retail-cohort"* is close to unproducible. **Re-specify the axis as institutional-vs-mixed dominance**, not retail participation |
| C4 | `ringkas.md` §6, §B8 | "on `top-changes` for 2026-09-04 the top three are UANG +24.92%, RONY +24.90%, SMMT +24.88%" | true **only** with `min_mcap_billion=0`. The default call returns SMMT +24.88%, NATO +24.63%, PKPK +17.43% | the video frame must pin `?classifications=top_gainers&min_mcap_billion=0&periods=1d`. A defaulted `top-changes` also costs 10 credits instead of 1 (CLAUDE.md) |
| C5 | §B10 / §B11 P1 | "OHLCV ≤90 days" from `/v2/daily/{symbol}/` | spec has **no `limit` parameter** — only `start`/`end`. The cap is on the range | pass an explicit 90-day `start`/`end`; do not expect a `limit` to work |

### Upgrades found while verifying

- **`/v2/suspensions/` accepts `start` and `end`.** The 583-row sweep can be date-bounded instead of blind-paginated, and the P5 per-symbol lookup is a supported filter, not a client-side scan.
- **`/v2/broker-summary/{symbol}/top/` accepts `cohort` (`all|institutional|mixed|retail|unknown`) and `origin` (`all|domestic|foreign`) as query parameters.** Given C3, asking the API for `cohort=institutional` is more honest than weighting a nearly-empty retail label.
- **`/v2/news/` accepts `start`/`end` alongside `symbols`.** The P4 causal filter can be windowed to the anomaly date properly, which the research assumed but did not confirm.
- **`/v2/filings/` is richer than §B11 records**: `holder_type` (`insider`), `transaction_value`, `share_percentage_before/after/transaction`, and a `price_transaction[]` breakdown. A cheap fourth axis later, at 1 credit.

### Still unverified (unchanged, and none block the MVP)

The `reason` vocabulary of the remaining 563 suspensions (~30 credits, blocks the real
evaluation protocol — not the MVP); the "Finfluencers" publication venue; the authors of
ProQuest 2088916427; Victor & Hagemann read second-hand; the KSEI PDF; and X/Telegram,
still uncrawled. The 5-day / 2-SD labelling scheme is quoted from the body of arXiv
2301.11403 — the abstract confirms the 85% / 62% headline but not the threshold text, so
that quote is trusted from the research document, not independently re-read.

---

## Part 2 — What the dummy data actually is

The user's "use dummy data for now" is already the sanctioned development path: CLAUDE.md
requires that iteration happen against local recordings, and forbids shipping synthetic
data as the product's data source. So: **`recorded/` first, `synth/` only for volume.**
Four divergences were measured this session and each one is a bug waiting to happen.

| Dataset | `recorded/` (real) | `synth/` (dummy) | Handling |
|---|---|---|---|
| daily | `symbol, date, open, high, low, close, volume, market_cap`; 20 rows captured | **identical field set**; 120 symbols × 90 rows | safe — this is the MVP's main input |
| suspensions | `symbol, suspension_date, reason, pdf_url`; Indonesian cooling-down text | `symbol, company_name, suspension_date, resumption_date, reason, notice_url`; **English generic reasons**, only 1 of 20 is "Significant price and volume movement" | normalize `notice_url`→`pdf_url`; keep the label vocabulary in **one table** with a real set and a synth set |
| news | `{results, pagination}` | **bare list** | one `results_of()` helper, used everywhere |
| broker top | `{symbol, start, end, origin, cohort, top_buyers, top_sellers}` | **no `origin`, no `cohort`** | read the echoes with `.get()`, never `[]` |

**Feasibility probe run this session.** The literature rule — close and volume both above
`mean + 2·SD` of the prior 5 days — was executed over all 120 synthetic symbols:

```
symbols=120  test-days=10200  pump_flag fired=209  rate=2.0490%
102 of 120 symbols produce at least one flag
```

The engine will therefore produce visible, non-degenerate output on dummy data from day
one. **But synth contains no planted pump events**, so 2.05% is the rule's false-positive
rate under a null, not a detection rate. Synthetic data validates the plumbing and nothing
else, and the demo must say so on screen.

---

## Part 3 — MVP scope

**One command. One symbol. Three axes. Zero credits.**

```
$ python3 src/firewall.py BNBR --source mock

BNBR · Bakrie & Brothers Tbk · as of 2026-08-06
Fragile on 2 of 3 axes.

  VOLUME    7,994,414,100 shares, 4.3 SD above its own 5-day baseline.
            (/v2/daily/BNBR/ · volume)
  PRICE     Rp105, 2.6 SD above the same baseline.
            (/v2/daily/BNBR/ · close)
  BROKER    Top 5 buyers hold 61% of buy value; 4 of 5 are institutional-cohort.
            (/v2/broker-summary/BNBR/top/ · buy_idr  ×  /v2/brokers/ · cohort)
  CATALYST  No company news in the same window.
            (/v2/news/?symbols=BNBR&start=…&end=… · results)

Not a buy or sell recommendation. Every figure traces to one endpoint and one field.
SOURCE: local recording, 2026-09-06 capture. No live call was made.
```

### In

1. Price-and-volume anomaly, 5-day baseline, 2 SD on both, per arXiv 2301.11403.
2. Broker concentration — top-5 share of buy value, **institutional/mixed dominance** (per C3, not retail participation).
3. Catalyst absence — `/v2/news/` windowed to the anomaly date.
4. Fail-closed citation verifier — a figure without an `(endpoint, field)` pair is not printed; missing data prints *"not fetched"*, never a guess.
5. `warnings.jsonl` append-only ledger, written from the first run.

### Out of the MVP, deliberately

Ownership rotation (medium evidence, monthly cadence); free float and market cap (low
evidence, C1/K1/K2, and free float leaks); the self-learning threshold loop; the 583-row
real evaluation; a web UI; sonification; `tip_text` parsing. `warnings.jsonl` exists from
day one only because retrofitting append-only state is expensive and writing it is ~20
lines.

---

## Part 4 — Tasks

Mirror the existing harness conventions throughout: standard library only, no venv, module
docstring explaining *why* the file exists, `main()` returning an exit code, `PASS`/`FAIL`
lines with a count, and `sys.exit(main())` at the bottom — as in
`src/sectors_env.py` and `src/verify_mock.py`.

### Task 1 — `src/fragility.py`, the pure scorer
- **Action**: `[{date, close, volume, …}] → [AxisResult]`. No I/O, no HTTP, no file paths. Baseline = `mean`/`pstdev` over the 5 rows before the test date; `pump_flag = close > mp+2·sp AND volume > mv+2·sv`; observation window `t+4`.
- **Mirror**: `ForecastFeatures`-style contract — plain values in, no knowledge of what they mean.
- **Validate**: `python3 src/fragility.py` self-tests on run and prints the synth base rate; assert it reproduces `209 / 10200`.

### Task 2 — `src/sources.py`, the shape normalizer
- **Action**: `results_of(payload)`, `notice_url`→`pdf_url`, `.get()` for the broker echoes, and `LABEL_VOCAB = {"real": [...], "synth": [...]}` in one place. Every divergence from Part 2 is handled here and nowhere else.
- **Mirror**: `sectors_env.py` — one shared way to read a thing so nobody hardcodes it twice.
- **Validate**: load the same call slug from `recorded/` and from `synth/` and assert the normalized dicts have identical key sets.

### Task 3 — `src/firewall.py`, the CLI and the fail-closed verifier
- **Action**: `--source mock|recorded|synth|live` (`live` refuses unless `--i-mean-it` and a budget are both passed). Every rendered figure carries `(endpoint, field)`; a figure without one raises before printing. Appends to `warnings.jsonl`.
- **Mirror**: `capture.py`'s refusal posture — the safe path is the default and the live path is opt-in.
- **Validate**: run against a payload with `/v2/news/` deleted; assert the catalyst line reads *"not fetched"* and the process still exits 0.

### Task 4 — `src/eval_fragility.py`, the evaluation skeleton
- **Action**: positives = suspensions whose `reason` matches the vocabulary for that source; negatives = ≥2 SD volume spikes with no suspension inside 10 trading days; score at **T−1**; report precision and recall split by market-cap bucket (K2), never accuracy.
- **Mirror**: `reconcile_usage.py` — a table, an explicit statement of what is explained, exit 1 on disagreement.
- **Validate**: runs to completion on synth and **prints that its own numbers are meaningless because synth has no planted events**. The real run is Phase 2 and costs ~30 credits.

## Validation

```bash
cd research/harness && python3 src/mock_server.py --port 8787 --credits 1000 &
cd research/harness && python3 src/fragility.py
cd research/harness && python3 src/sources.py
cd research/harness && SECTORS_BASE_URL=http://127.0.0.1:8787 python3 src/firewall.py BNBR --source mock
cd research/harness && python3 src/eval_fragility.py --source synth
cd research/harness && python3 src/reconcile_usage.py   # must still exit 0: no credits spent
```

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| A parser written against `synth/` breaks on real payloads | **High** — four measured divergences | Task 2 is the only place shapes are read; its test compares real against synth key sets |
| Reads as investment advice under POJK 5/2019 | Medium | no price target, no buy/sell, no sizing, no execution; verdict is a fragility count, and the disclaimer is a rendered line, not a footnote |
| Cohort axis cannot be written as researched | **Confirmed** (C3) | axis re-specified as institutional/mixed dominance before any code is written |
| Credits burned during iteration | Medium | `--source live` refuses without an explicit flag; `reconcile_usage.py` is in the validation list so a leak shows up as a failing gate |
| Synthetic data reaches the demo unlabelled | Medium — hackathon rule | `SOURCE:` line is part of the output contract, not a debug flag, and is asserted in Task 3's test |
| Label leakage from undated snapshots | Low for the MVP | free float and market cap are out of scope; when they return, the rule is: every feature carries a date earlier than the event date |

## Acceptance

- [x] Four tasks complete, all self-tests pass
- [x] ~~`firewall.py BNBR --source mock` reproduces the V5 figures~~ → **superseded, see C6 below**:
      `firewall.py ADRO --source mock --date 2026-08-31` scores 4 of 4 axes on real recorded
      payloads (volume 102,100,700 at 3.4 SD, close Rp2,840 at 4.0 SD), and the `recorded`
      and `mock` paths agree figure for figure
- [x] Every printed figure carries an `(endpoint, field)` pair; deleting an input degrades to "not fetched"
- [x] `reconcile_usage.py` still exits 0 — the MVP charged nothing (`_ledger.jsonl` unchanged at 168 lines)
- [x] The five research corrections C1–C5 are written back into `deep-research.md` and `ringkas.md`
- [x] No price target, buy/sell signal, sizing, or execution path exists anywhere in the output

### C6 — the correction this plan needed itself

**BNBR cannot be the demo symbol, and the sample output in Part 3 was unsourceable.**
Measured before any code was written:

| Finding | Evidence |
|---|---|
| There is no `/v2/daily/BNBR/` recording | `recorded/v2_daily_*` is ADRO, ANTM, ASII, BBCA, BBRI, BMRI, BREN, TLKM — eight blue chips |
| BNBR's 15 `most-traded` rows **begin at** 2026-08-06 | the anomaly date is the first date in the capture, so there are zero prior days and the 5-day baseline does not exist |
| There is no `broker-summary/BNBR/top/` recording | only ADRO, BBCA, BBRI, TLKM |
| The citations were wrong | 7,994,414,100 @ Rp105 lives in `v2_most-traded.json` as `volume`/`price`. That payload has **no `close`** and no OHLC, so `(/v2/daily/BNBR/ · close)` names a field that does not exist in the source of the number |
| The mock would have hidden it | `/v2/daily/BNBR/` falls through to the 193-byte spec-example fixture and returns `X-Mock-Source: spec-example` |

The `4.3 SD` and `2.6 SD` figures in the Part 3 sample were illustrative, not computed.
**Demo re-pointed at ADRO**, which carries all three axes on paid recordings. `daily ∩ broker-top`
is exactly {ADRO, BBCA, BBRI, TLKM}.

### C7 — two divergences Part 2 missed

Part 2 lists four real-vs-synth divergences. There are six. The two extra ones both bite:

- **`/v2/brokers/` has `origin` in `synth/` and not in `recorded/`.** This is correction C1
  inverted, and it is the exact shape of the Risk-1 failure: a parser written against dummy
  data raises `KeyError` on the payload that matters. `normalize_broker` drops the field.
- **broker-top *buyer rows* differ too.** `recorded/` carries `rank` and `sell_idr`; `synth/`
  carries inline `origin`/`cohort` and neither of those. So synthetic cohort is free and real
  cohort requires the join to `/v2/brokers/` — code that leans on the free one stops working live.

### Bug found in review

`score()` anchored the catalyst news window to the **last row of the series** instead of to
`as_of`. Scoring any date before the end of the capture produced a window whose start was after
its end — empty by construction — so CATALYST reported "No company news in the same window" for
every symbol on every past date. It is a constant masquerading as an axis, and it would have
been invisible in the demo, which scores the most recent date. Fixed, with a regression test at
three dates asserting the axis count matches the window contents.

### What the evaluation gate reports

`eval_fragility.py --source synth` exits 0 and prints, in its own words, that its numbers mean
nothing. `--source recorded` **exits 1** — and correctly: the 15 real pump-suspended symbols
(LIFE, TRUK, PACK, ASLI, NICK, …) have no daily series in `recorded/`, so not one positive is
scoreable. Phase 2 is now enforced by a failing gate instead of asserted in prose.

## Phase 2 (not now)

Pull the 583 suspensions (~30 credits) and read the real `reason` vocabulary — everything
about honest evaluation is blocked on it. Then the ownership axis, then the guarded
learning loop from `agen-risiko-belajar-mandiri.md`. Deadlines: registration 22 Sep 2026,
submission 30 Sep 2026.
