# Plan: Riset Fundamental IDX yang Bisa Didengar — M1–M3

**Source PRD**: `.claude/prds/tunanetra.prd.md`
**Source research**: `research/plan/tunanetra/deep-research.md`, `research/plan/tunanetra/ringkas.md`
**Selected milestones**: M1 (engine), M2 (accessible surface), M3 (sonification)
**Status**: M1–M3 built and green, 2026-09-10. Track layer (M5) deferred — the user asked
for the MVP only, so no LLM narrator and no track declaration were added.
**Complexity**: Large
**Credits spent by this plan**: 0 of ~623 remaining. M4 asks for ~10, separately.

## Summary

One IDX symbol in, an ordered set of sentences and semantic tables out, every number carrying
`(endpoint, field, as_of)`. The engine runs entirely against `research/harness/recorded/`, so
M1–M3 finish before a credit is charged. Four symbols are fully buildable offline —
**ADRO, BBCA, BBRI, TLKM** — and the research document's `peers`/`ownership` section and its
90-day price series are *not* among them; both are deferred to M4 with an exact 10-credit ask.

---

# Part 1 — Verification of the research findings

Every claim below was re-checked on 2026-09-10. Local checks read
`research/harness/recorded/` (the paid 2026-09-06 capture). External checks re-fetched the
primary sources. Nothing here cost a Sectors credit.

## 1.1 Confirmed — academic evidence

| # | Claim | Check | Result |
|---|---|---|---|
| V1 | Sharif 2021 DOI `10.1145/3441852.3471202` | doi.org CSL metadata | resolves; title, ASSETS 2021, authors Sharif/Chintalapati/Wobbrock/Reinecke — exact |
| V2 | "61.48% less accurately … 210.96% more time" | paper PDF, `faculty.washington.edu/wobbrock/pubs/assets-21.01.pdf` | **verbatim** |
| V3 | AEI 34% vs 87% | same PDF | **verbatim**: *"AEI is considerably lower for screen-reader users (34%) compared to non-screen-reader users (87%)"* |
| V4 | Google Charts 73% / D3 17% / ChartJS 11% | same PDF | **verbatim**, and the paper states the cause: *"as it provides an alternate tabular representation of data that is only visible to screen readers"* |
| V5 | 33% of 27 visualizations undiscoverable | same PDF | **verbatim** |
| V6 | Study sizes "9 qualitative, 36 vs 36 quantitative" | same PDF | **verbatim** — the doc's "36 vs 36" is right |
| V7 | Screen-reader users asked for tables/text | same PDF | **verbatim**, wording is *"suggested tabular and textual representation of data"* |
| V8 | VoxLens DOI `10.1145/3491102.3517431` | doi.org + published sources | resolves; CHI 2022; 75% vs 34%, +122%, gap 62%→15%, time −36%, 21 screen-reader users — all confirmed |
| V9 | Lundgard & Satyanarayan DOI `10.1109/TVCG.2021.3114770`, arXiv `2110.04406` | arXiv abstract | resolves; **30 blind + 90 sighted readers, 2,147 sentences**, four-level model — exact |
| V10 | Adib 2020 DOI `10.24042/al-mal.v1i2.5924` | doi.org CSL | resolves; *Al-Mal* 1(2), 2020 |
| V11 | Fu 2026 DOI `10.82308/55987` | doi.org CSL | resolves as a **thesis**, no author in metadata — see W3 |

## 1.2 Confirmed — legal and prior art

| # | Claim | Check | Result |
|---|---|---|---|
| V12 | POJK 22/2023 is 848 KB, 131 pages | re-downloaded from `ojk.go.id` | **848.2 KB, 131 pages** — exact |
| V13 | Pasal 8 ayat (3) huruf a and b | `pdftotext -layout` | **verbatim**: *"a. kesetaraan akses kepada setiap Konsumen; b. layanan khusus terkait Konsumen penyandang disabilitas dan lanjut usia;"* |
| V14 | Pasal 8 ayat (2) binds product design | same | **verbatim**, `a. desain produk dan/atau layanan` is the first item |
| V15 | Pasal 54 ayat (3) | same | **verbatim**: *"PUJK mempunyai tanggung jawab untuk mendukung penyediaan layanan khusus kepada Konsumen penyandang disabilitas dan lanjut usia."* |
| V16 | Penjelasan Pasal 54(3) letters b and g | same | **verbatim**, both quoted correctly |
| V17 | "Penyandang disabilitas" covers long-term **sensorik** limitation | same | **verbatim** |
| V18 | `churst90/accessible-trade-terminal` metadata | GitHub API, burner account | **GPL-3.0, C#, created 2023-06-11, pushed 2026-09-07, 4 stars** — exact to the digit |

## 1.3 Confirmed — Sectors data layer

| # | Claim | Check | Result |
|---|---|---|---|
| V19 | `get-segments` returns `revenue_breakdown` | 4 recordings | confirmed, shape `{symbol, financial_year, revenue_breakdown[]}` |
| V20 | Quarterly financials are sector-dependent | 4 recordings | confirmed: BBCA/BBRI carry `realized_capital_goods_investment`, ADRO/TLKM carry `capital_expenditure`, never both |
| V21 | `shareholders-composition` is a dated monthly panel | 4 recordings | confirmed: 8 rows, 2026-01-30 … 2026-08-31, 9 `_l` + 9 `_f` investor classes plus `total_l`/`total_f` |
| V22 | `?sections=` bills one credit per named section | `mock_server.py:449-455` + manifest | confirmed: `sections=overview` cost 1, bare report cost 8, default item count 8 |
| V23 | ~623 credits remain | `reconcile_usage.py` | confirmed: portal total **377**, capture 265 + 112 outside, no unexplained discrepancy |
| V24 | Repo created inside the eligibility window | `git log --reverse` | first commit **2026-09-05**, after the 19 Aug 2026 floor |

## 1.4 Corrections — findings that did not survive the check

**W1. The 90-day price series does not exist in the recordings.** `/v2/daily/{symbol}/`
returns **20 rows, 2026-08-06 … 2026-09-04** for all four symbols. The research document's
"sonifikasi tren harga 90 hari" is not buildable offline. Asking the mock for a window
(`?start=…&end=…`) returns `X-Mock-Source: spec-example` — **BBCA rows dated 2025-05-02, for
any symbol**. Consequence: either say "20 hari bursa terakhir, 6 Agustus – 4 September 2026"
and sonify 20 points, or buy the window in M4. `/v2/foreign-flow/` *does* carry 62 points
across 2026-06-07 … 2026-09-05, so the 90-day trend claim survives on foreign flow only.

**W2. `?sections=peers` and `?sections=ownership` are not in the recordings at all.** The
only peers/ownership payload on disk is inside the one bare `/v2/company/report/BBCA/`
capture that cost 8 credits. The mock answers `?sections=peers` with
`X-Mock-Source: spec-example`, and — verified by request — returns **BBCA's payload when
asked for TLKM**. This is the same class of trap as the pump-and-dump BNBR blocker: a demo
built on it would show one company's peers under another company's name. The peer section
must degrade explicitly ("belum diambil") until M4 buys it.

**W3. The sonification design rules rest on a single unrefereed thesis.** Fu 2026 resolves as
`type: thesis` with no author in DOI metadata, and its own design is N=18 **sighted**
participants plus 3 blind/low-vision qualitative validators. The research document reports
this honestly, but the plan should not present the parity/failure zones as settled findings.
Treat them as a conservative design constraint — the failure direction (do not sonify
volatility, do not layer indicators) is safe whether or not the thesis replicates.

**W4. "Belum ada aturan pemberian sanksi yang tegas" is stale for this regulation.** Adib
2020 predates POJK 22/2023 by three years, and the 2023 text contradicts it in part.
**Pasal 8 ayat (4)** attaches administrative sanctions — written warning, business
restriction, freeze, removal of directors, **administrative fine up to Rp15,000,000,000**
(ayat 6), licence revocation — to failure to have and apply the written consumer-protection
policy whose required contents include the disability clause. The gap is narrower and
sharper than the document states: **Pasal 54 ayat (4) sanctions only ayat (1) and ayat (2)** —
ayat (3), the disability special-service duty, is phrased as *tanggung jawab untuk mendukung*
and carries no sanction of its own. Use that precise framing; it is stronger and it is true.

**W5. The example sentence in `ringkas.md` §8 cannot be produced from the data.** *"Tiga
perempat pendapatan berasal dari satu segmen, dan porsinya naik tiga tahun berturut-turut"*
needs a multi-year segment series. `get-segments` returns **one** `financial_year` per symbol
(ADRO 2024, TLKM 2024, BBCA 2025, BBRI 2025). The multi-year segment series exists **only in
`synth/`**, which is exactly the shape of mistake the hackathon rules forbid shipping. Rewrite
the example to a single-year concentration claim, or source the trend from quarterly
financials instead.

**W6. `revenue_breakdown` is a whole profit-and-loss Sankey, not a revenue segment list.**
It is a multi-level edge list mixing revenue *and* expense flows, and the graph shape is
sector-dependent: banks route through `Interest Income → Net Interest Income → Total Revenue`
(BBCA 20 edges, BBRI 22), non-banks through `Total Revenue → Gross Profit → Operating Income`
(ADRO 9 edges, TLKM 17). A naive "share of total" over the flat edge list double-counts
intermediate nodes. The narrator must walk the graph and normalise per sector — the same
bank/non-bank divergence already known from the capex field.

**W7. The claim that `?sections=peers` buys "the whole peer set + financials" needs
rewording.** Sections bill individually, so `peers` and `financials` are separate credits.
What is true is that the `peers` payload embeds a per-peer financial summary —
`net_income`, `total_assets`, `total_equity`, `pretax_income`, `total_revenue`, `pe_ttm`,
`pb_mrq`, `point_summaries`. Say "peer-set financial summary", not "the financials section".

**W8. None of the tunanetra primary sources are archived in `research/evidence/`.** The
document states the POJK PDF, `accessibletrader.com`, the GitHub metadata, and the Highcharts
docs were pulled in full, but the provenance store contains no capture for any of them. Every
quote is currently unreproducible from the repository, against the repo's own convention.

**W9. Lundgard & Satyanarayan is dated 2021 in the document and 2022-01 by the publisher.**
Both are defensible — arXiv `2110.04406` is October 2021, the TVCG issue is January 2022.
Cite "IEEE TVCG (Proc. VIS 2021)" to be unambiguous.

## 1.5 Still unverified

| # | Item | Status after this pass |
|---|---|---|
| U1 | Which Indonesian brokerage apps are actually screen-reader readable | unchanged — no named source found |
| U2 | Primary population figure | **a primary source now exists**: BPS, *Potret Penyandang Disabilitas di Indonesia: Hasil Long Form SP2020* (2024-12-20), dataset *Tingkat Kesulitan Melihat*. Note it measures graded seeing difficulty (Washington Group style), which is **not** the same construct as "tunanetra" — do not equate it with AIDRAN's 1.5% |
| U3 | NDI/FINRA 2015, FDIC 2023 | unchanged — still third-party quotations; keep out of the video |
| U4 | `r/Blind` community voice | unchanged — OpenCLI bridge down, Firecrawl needs a key |
| U5 | Highcharts docs cite WCAG 2.2 | not re-fetched; low stakes, we do not depend on Highcharts |

---

# Part 2 — Ground truth for the build

## 2.1 What is buildable offline, exactly

Intersection of all five research endpoints: **ADRO, BBCA, BBRI, TLKM**. `foreign-flow`
additionally covers ANTM, ASII, BMRI, BREN.

| Dataset | Symbols | Shape on disk | Window |
|---|---|---|---|
| `report ?sections=overview` | ADRO ANTM ASII BBCA BBRI BMRI BREN TLKM | `{symbol, company_name, overview{22 fields}}` | snapshot |
| `get-segments` | ADRO BBCA BBRI TLKM | `{symbol, financial_year, revenue_breakdown[]}` | one FY |
| `daily` | 8 symbols | list of 20 | 2026-08-06 … 2026-09-04 |
| `shareholders-composition` | ADRO BBCA BBRI TLKM | `{symbol, year, data[8]}` | 2026-01-30 … 2026-08-31 |
| `financials/quarterly ?n_quarters=4` | ADRO BBCA BBRI TLKM | list of 4 | BBCA/TLKM to 2026-06-30; ADRO/BBRI to 2026-03-31 |
| `foreign-flow` | 8 symbols | `{symbol, start, end, data[62]}` | 2026-06-07 … 2026-09-05 |
| `peers`, `ownership` | **BBCA only** | inside the bare 8-credit report | snapshot |

Every window above is **fixed and stale by design** — these are 2026-09-06 recordings. Print
the date next to every series, exactly as `firewall.py` was made to do for the broker axis.

## 2.2 Divergences `sources.py` must reconcile

`synth/` is not shaped like `recorded/`. Confirmed differences:

| Dataset | `recorded/` | `synth/` |
|---|---|---|
| segments | `revenue_breakdown` edge list, one `financial_year` | `{symbol: {year: {revenue_segments{}, cost_segments{}}}}`, **4 years** |
| shareholders | absolute share counts, 9 `_l` + 9 `_f` fields, dated rows | fractions, `local_breakdown{}`/`foreign_breakdown{}`, `month` string, 5 classes |
| quarterly | `date`, 40 fields, sector-dependent capex field | `report_date` + `quarter`, 11 fields, no capex field at all |

The multi-year synth segment series is a trap: it makes W5's forbidden sentence look
buildable. `sources.py` must refuse to emit a multi-year segment claim on any source.

## 2.3 Patterns to mirror

| Category | Source | Pattern |
|---|---|---|
| Layout | `src/pump-and-dump/` | one folder per idea, own `run.sh`, own vocabulary, no router |
| Path constants | `src/pump-and-dump/sources.py:41-50` | `HERE` → `ROOT` → `HARNESS` → `RECORDED`/`SYNTH` |
| Loader | `sources.py:95` `load(source, dataset, symbol)` + `ENDPOINT` dict | one place where source divergence is reconciled |
| Fail-closed errors | `sources.py:79` `NotRecorded`, `firewall.py:57` `UncitedFigure` | raise rather than degrade silently |
| Citation | `firewall.py:61-78` `_flatten` / `cite` | every figure carries `(endpoint, field)` |
| Pure core | `fragility.py` — no I/O, no HTTP, no paths | scorer is unit-testable in isolation |
| Tests | `check_*()` + `self_test()` + `main()` in every module | `./run.sh test` runs the product's gates then the harness's |
| Ledger gate | `firewall.py:339` `check_ledger` | a run that leaked a credit fails the suite |
| Run log | `warnings.jsonl`, git-ignored | opinions are not paid data |

No accessibility pattern exists to mirror: `src/pump-and-dump/webapp.py` has zero `<th>`,
zero `scope=`, zero `<caption>`, and one `aria-` attribute in 17 KB. This product sets the
pattern.

---

# Part 3 — Tasks

## Files

| File | Action | Why |
|---|---|---|
| `src/tunanetra/run.sh` | CREATE | bare start; `read`, `symbols`, `test`, `help` |
| `src/tunanetra/sources.py` | CREATE | six datasets, recorded↔synth reconciliation, `NotRecorded` |
| `src/tunanetra/money.py` | CREATE | number → Indonesian words; pure, no I/O |
| `src/tunanetra/narrate.py` | CREATE | derivations + level-2/3 sentence templates; pure |
| `src/tunanetra/reader.py` | CREATE | CLI + fail-closed citation verifier |
| `src/tunanetra/webapp.py` | CREATE | semantic HTML surface over `reader.py` |
| `src/tunanetra/sonify.js` | CREATE | Web Audio trend tone + event earcon |
| `src/tunanetra/a11y_check.py` | CREATE | structural WCAG checks over rendered HTML |
| `src/tunanetra/eval_narrate.py` | CREATE | coverage and citation-completeness metrics |
| `.gitignore` | UPDATE | ignore `src/tunanetra/runs.jsonl` |
| `CLAUDE.md` | UPDATE | add the second idea to Layout and Commands |
| `research/plan/tunanetra/deep-research.md` | UPDATE | corrections W1–W9 |
| `research/plan/tunanetra/ringkas.md` | UPDATE | corrections W1, W4, W5 |

### Task 1 — `sources.py`

- **Action**: `load(source, dataset, symbol)` over the six datasets; `ENDPOINT` dict mapping
  dataset → path template; normalisers that flatten `recorded/` and `synth/` into one shape;
  `NotRecorded` when a symbol is missing; `available_symbols()` returning the 4-symbol
  intersection; a hard refusal to serve a multi-year segment series from any source (W5).
- **Mirror**: `src/pump-and-dump/sources.py` end to end.
- **Validate**: `python3 sources.py` runs `check_key_parity`, `check_shape_helpers`, and a new
  `check_no_multiyear_segments`; all pass.

### Task 2 — `money.py`

- **Action**: `say_rupiah(1_200_000_000_000) == "satu koma dua triliun rupiah"`;
  `say_percent(0.2492) == "dua puluh empat koma sembilan persen"`; ordinals, negatives,
  zero, and the ribu/juta/miliar/triliun ladder.
- **Mirror**: pure-module convention of `fragility.py` — no I/O.
- **Validate**: `python3 money.py` self-test with boundary cases at each magnitude step.

### Task 3 — `narrate.py` (the derivations)

- **Action**: pure functions, one per picture replaced.
  - `segment_concentration(payload)` — walk the `revenue_breakdown` DAG, identify the leaf
    inflows to the revenue root (bank root `Interest Income`, non-bank root `Total Revenue`),
    drop intermediate nodes, return ranked shares plus a concentration index. Sector-aware
    per W6.
  - `price_trend(rows)` — direction, magnitude, extremes over the recorded 20 days, always
    date-stamped.
  - `flow_runs(rows)` — longest consecutive sign run of `net_foreign_inflow` over 62 points.
  - `ownership_runs(panel)` — per investor class, consecutive-month direction runs over the
    8-point panel; this is what produces the "foreign pension funds bought four months
    running" sentence, and it is genuinely supported by the data.
  - `quarterly_change(rows)` — QoQ and YoY on revenue and earnings, selecting
    `capital_expenditure` or `realized_capital_goods_investment` by which key exists (V20).
  - `peer_rank(peers)` — rank on `pe_ttm`, `pb_mrq`, `point_summaries`; raises `NotRecorded`
    for any symbol other than BBCA until M4.
  - Sentence templates locked to semantic levels 2–3, with a `LEVEL1_VOCAB` blacklist.
- **Mirror**: `fragility.py` — pure, returns result objects, no strings printed.
- **Validate**: `python3 narrate.py` — each derivation has a hand-computed fixture; a test
  asserts no `LEVEL1_VOCAB` token can appear in any template output.

### Task 4 — `reader.py` (CLI + verifier)

- **Action**: `cite()`/`UncitedFigure` fail-closed verifier — a figure without
  `(endpoint, field, as_of)` raises before render. `read SYMBOL [--lengkap] [--audio]`.
  `symbols` prints the 4 buildable symbols and each series' real window. Degradation path:
  a missing dataset says *"belum diambil"* and names the endpoint, never invents. A hard
  refusal when a response carries `X-Mock-Source: spec-example` (W1, W2). Advice-word
  refusal, mirroring `firewall.py:238`. Append-only `runs.jsonl`.
- **Mirror**: `firewall.py` structure, including `check_degradation`, `check_citation`,
  `check_no_advice`, `check_ledger`.
- **Validate**: `python3 reader.py --self-test` — all gates green; a deliberately uncited
  figure must raise.

### Task 5 — `webapp.py` (the accessible surface)

- **Action**: standard-library HTTP server. `<html lang="id">`; one `<h1>`, real `<h2>`/`<h3>`
  per topic; summary block first; every table with `<caption>` and `<th scope="col|row">`;
  a citation `<dl>` per section; a Q&A form whose answer lands in an `aria-live="polite"`
  region; skip link; visible focus; no colour-only meaning; audio off by default behind a
  labelled control.
- **Mirror**: `src/pump-and-dump/webapp.py` for the serving skeleton only — its markup is the
  counter-example, not the pattern.
- **Validate**: `a11y_check.py` passes; one manual VoiceOver pass completes the flow with the
  screen dark.

### Task 6 — `a11y_check.py`

- **Action**: standard-library HTML parse of the rendered page, asserting the criteria we
  actually claim: 1.3.1 (every data table has `<caption>` and `<th scope>`), 2.4.1 (skip
  link), 2.4.6 (heading order has no gaps, exactly one `<h1>`), 3.1.1 (`lang`), 4.1.2 (every
  control has an accessible name), 1.4.3 (contrast computed from our own palette constants).
- **Mirror**: `check_*()` + `main()` convention.
- **Validate**: `python3 a11y_check.py` exits 0 on the rendered page, and exits 1 on a
  deliberately broken fixture.

### Task 7 — `sonify.js`

- **Action**: Web Audio only, no library. Two behaviours and no more: a pitch-mapped tone
  sweep for a series direction (20-point price, 62-point foreign flow), and a short
  high-contrast symmetric earcon for a discrete event. Volatility and multi-indicator
  comparison are spoken numbers, never tones (W3). Keyboard start/stop, honours
  `prefers-reduced-motion` as a default-off signal.
- **Mirror**: no in-repo precedent; keep it small and readable, it is the technical-depth
  exhibit.
- **Validate**: manual — tone plays, earcon fires, and a test in `narrate.py` asserts
  volatility never routes to the audio channel.

### Task 8 — `run.sh` and repo wiring

- **Action**: mirror `src/pump-and-dump/run.sh` — bare start brings up the mock then the UI;
  `read`, `symbols`, `test`, `help`; `SOURCE`, `PORT`, `MOCK_PORT` env overrides. Write the
  mock log to a `mktemp -d` directory, not a fixed `/tmp` path.
- **Validate**: `./run.sh test` runs this product's gates then the harness's, all green.

### Task 9 — research corrections

- **Action**: fold W1–W9 into `deep-research.md` as a corrections block (the document already
  has a `Koreksi` section for K1/K2) and fix the three affected lines in `ringkas.md`.
  Archive the POJK PDF text and the GitHub metadata into `research/evidence/` (W8).
- **Validate**: no claim in either document contradicts §2.1 of this plan.

## Validation

```bash
cd src/tunanetra && ./run.sh test
```

```bash
cd src/tunanetra && python3 a11y_check.py && python3 eval_narrate.py
```

```bash
cd research/harness && python3 src/reconcile_usage.py
```

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Peer section stays empty through the demo | High | Degrade explicitly and name the endpoint; M4 buys 6 credits |
| Segment DAG walk gets bank normalisation wrong | Medium | Hand-computed fixtures for all four symbols, two of each sector |
| A judge's NVDA finds what VoiceOver missed | Medium | Claim only VoiceOver; ship `a11y_check.py` so the structure is inspectable |
| Track 03 reads the product as a re-render | Medium | Lead with derivations; see the open decision below |
| Sonification eats time on long series | Low | 62 points is the ceiling; summary always precedes audio |
| 20 days to the deadline, five modules | Medium | M1 is the only milestone that must be complete; M3 is droppable |

## Acceptance

- [ ] All tasks complete
- [ ] `./run.sh test` green, harness gates included
- [ ] Every number on the page traces to `(endpoint, field, as_of)`; an uncited figure raises
- [ ] One recorded VoiceOver run completes an issuer flow with the screen dark
- [ ] Zero credits spent by M1–M3; `reconcile_usage.py` unchanged
- [ ] No synthetic data reachable from the product's default source
- [ ] Patterns mirrored from `src/pump-and-dump/`, not reinvented

---

# Part 4 — Verification of this plan

Checks run against the plan itself, not the research.

| # | Check | Result |
|---|---|---|
| P1 | Every endpoint the tasks name exists in the recordings | **Pass** for six datasets; **fails for `peers`/`ownership` on 3 of 4 symbols** — handled by Task 4's explicit degradation and M4 |
| P2 | Every symbol the demo uses is in the offline intersection | **Pass** — ADRO, BBCA, BBRI, TLKM only |
| P3 | Every sentence the plan promises is producible from the data | **Pass after W5** — the multi-year segment sentence is removed; ownership runs and single-year concentration survive |
| P4 | Credits spent by M1–M3 | **Zero** — no task calls the live API |
| P5 | Standard library only | **Pass** — Web Audio is browser-native, not a dependency |
| P6 | Hackathon "core data source" test | **Pass** — remove Sectors and there is nothing to narrate |
| P7 | Hackathon "no synthetic as product data" test | **Pass** — Task 1 refuses the one synth-only claim |
| P8 | Hackathon track qualifying test | **Unresolved** — see below |
| P9 | Time budget | 20 days to 30 Sep 23:59 WIB; M1 alone is ~2 days, M1–M3 ~6–8; feasible with M3 droppable |
| P10 | Repo eligibility | **Pass** — first commit 2026-09-05 |
| P11 | Plan does not silently widen scope | **Pass** — M4 (credits) and M5 (submission) are named and excluded |

**P8, the one open item.** Track 03 explicitly rejects *"a product that only displays raw
Sectors data in a different visual form, however well presented"*. Text instead of a chart is
a change of visual form. The product clears Track 03 only on its derivations — segment
concentration over a normalised DAG, ownership direction runs, peer-relative rank,
sector-aware financial normalisation — and that argument has to be made explicitly, in the
video and the README, or the accessibility story becomes the reason it is disqualified from
the track it picked.

Track 01 fits the architecture better: the budget-aware planner, the custom tool layer over
the REST API, and the fail-closed verifier are the "custom-built agent logic or orchestration"
the track requires, and *"a purpose-built interface for a specific participant and problem"*
is listed verbatim as qualifying. Track 01 makes an LLM mandatory, which this plan does not
currently include.

**Recommendation**: Track 01, with the LLM writing the prose and the fail-closed verifier
refusing to publish any sentence whose figures do not trace to an endpoint and a field. That
fork touches only a thin top layer above `narrate.py`; M1–M3 as written are needed either way,
so the decision does not block the start of the build.

**Resolved 2026-09-10**: deferred. M1–M3 were built as the MVP with no track layer. The
deterministic sentence engine is what shipped; adding an LLM narrator behind
`reader.cite()` remains a thin top layer whenever the track is declared.

---

# Part 5 — What M1–M3 actually shipped

| File | Gates | Notes |
|---|---|---|
| `src/tunanetra/sources.py` | 22 checked | six datasets, six divergences, the multi-year segment refusal |
| `src/tunanetra/money.py` | 46 checked | Indonesian number words; `say_exact` for prices, `say_number` for magnitudes |
| `src/tunanetra/narrate.py` | 96 checked | six derivations, level-1 and advice blacklists, the audio parity gate |
| `src/tunanetra/reader.py` | 17 checked | fail-closed `cite()`, explicit degradation, credit-ledger gate |
| `src/tunanetra/webapp.py` | 11 checked | semantic HTML, no `<canvas>`, no `<svg>` |
| `src/tunanetra/a11y_check.py` | 4 pages + 8 colour pairs | 1.3.1, 1.4.3, 2.4.1, 2.4.6, 3.1.1, 4.1.2, plus a broken fixture that must fail |
| `src/tunanetra/sonify.js` | manual | Web Audio only; 20-point price sweep and 62-point flow sweep |

Two derivations changed shape during the build, both because the first version produced a
true sentence that told a listener nothing:

* **Prices were being rounded.** `say_rupiah(6350, places=0)` spoke "enam ribu rupiah" and
  `say_rupiah(6700, places=0)` spoke "tujuh ribu rupiah", turning a 5.5% move into a
  fabricated 17% one. `say_exact` now spells every digit for price levels; `say_number`
  keeps rounding only where the magnitude is the fact.
* **Ownership runs ranked by length.** That surfaced *lembaga keuangan domestik* drifting
  from 0.01% to 0.01% for seven months ahead of *reksa dana asing* moving 32.3% to 35.0%.
  Runs are now ranked by size of move, with a materiality floor, and the full list stays in
  the table.

Still open, unchanged by this build: M4's ~10 credits (peers and ownership for the three
non-BBCA symbols, plus a real 90-day daily window), the manual VoiceOver pass, and folding
corrections W1–W9 back into the research documents.
