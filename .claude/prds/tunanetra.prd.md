# PRD: Riset Fundamental IDX yang Bisa Didengar

**Source research**: `research/plan/tunanetra/deep-research.md`, `research/plan/tunanetra/ringkas.md`
**Status**: draft, awaiting confirmation
**Date**: 2026-09-10
**Repo slot**: `src/tunanetra/` (second idea alongside `src/pump-and-dump/`)

---

## 1. One-sentence problem statement

Blind and low-vision IDX investors can already place orders with TalkBack or VoiceOver, but
they have no independent way to *research an issuer* — financial statements arrive as table
images, and every comparison the market offers is a chart — so this product turns Sectors
data into ordered sentences and semantic tables that a screen reader can actually extract
information from.

## 2. Who it is for

Primary: a retail investor in Indonesia who uses NVDA, VoiceOver, or TalkBack and who has
already learned to transact (the Sekolah Pasar Modal graduates named in the published
testimony — Tutus in Surabaya, Toviyani in Yogyakarta, I Nyoman Suandi in Denpasar).

Secondary: any sighted user who prefers reading a summary to reading a chart. The design is
a text-first surface, not an assistive add-on, so this is the same product, not a fallback.

## 3. Why text, not "chart plus alt text"

Verified this session against the primary paper (see §7 of the plan). Screen-reader users
extract information **61.48% less accurately** and take **210.96% longer** on online charts;
**33% of 27 charts were undiscoverable** to a screen reader entirely. The library that won
that study — Google Charts at 73% accuracy vs Chart.js at 11% — won because, in the paper's
own words, *"it provides an alternate tabular representation of data that is only visible to
screen readers"*. The winning path is the table, not the accessible chart. Sectors already
returns JSON; rendering a chart in order to make the chart accessible is a 4–7× detour.

## 4. Goals

| # | Goal | How it is measured |
|---|---|---|
| G1 | A blind user completes an issuer research flow with no sighted help | Recorded VoiceOver session, task completed end to end |
| G2 | Every number on screen traces to one endpoint and one field | Fail-closed verifier; an uncited figure raises, it does not render |
| G3 | Summary arrives before detail | Page order and the CLI's default `ringkas` verbosity |
| G4 | Sentences sit at semantic level 2–3, never level 1 | Locked templates; a test asserts no level-1 vocabulary reaches output |
| G5 | Sonification only inside its verified parity zone | Trend and event only; volatility and multi-indicator are spoken numbers |
| G6 | The product ships on real Sectors data, never synthetic | Source badge on screen and in the CLI; synth is a development-only layer |

## 5. Non-goals

- No order entry, no portfolio, no position sizing. Order entry is already solved by
  TalkBack/VoiceOver on some Indonesian brokerages; rebuilding it adds nothing.
- No price targets, buy/sell signals, or recommendations. Hackathon rules ban automated
  execution; the research also records a blind investor warning against instant-tip
  dependency.
- No accessible charting terminal. `churst90/accessible-trade-terminal` (GPL-3.0, C#,
  created 2023-06-11, pushed 2026-09-07, 4 stars — re-verified this session) already occupies
  that category. It is cross-market **technical** analysis; it does not do IDX issuers,
  Indonesian financial statements, segments, local shareholder structure, or Bahasa Indonesia.
- No claim of NVDA or TalkBack conformance unless those runs actually happen on the hardware
  we have. See risk R6.

## 6. Scope of the data surface

Six Sectors endpoints replace the six things this domain normally draws as pictures.

| Picture normally drawn | Endpoint | Replaced by |
|---|---|---|
| Sankey of revenue | `/v2/company/get-segments/{symbol}/` | ranked segment sentences + table |
| Candlestick | `/v2/daily/{symbol}/` | trend sentence, extremes, optional sonification |
| Stacked area of ownership | `/v2/company/shareholders-composition/{symbol}/` | direction runs per investor class |
| Foreign-flow area chart | `/v2/foreign-flow/{symbol}/` | cumulative direction + sonification |
| Financial-statement image | `/v2/financials/quarterly/{symbol}/?n_quarters=4` | QoQ/YoY sentences + semantic table |
| Peer scatter / bar | `/v2/company/report/{symbol}/?sections=overview,peers,ownership` | peer-relative rank sentences |

## 7. Product surface

**CLI** — `./run.sh read BBCA`, plus `symbols`, `test`, `help`. Bare `./run.sh` starts the
mock and the web UI, matching `src/pump-and-dump/run.sh`.

**Web** — one HTML page per symbol, served by the standard library:
- `<h1>`/`<h2>`/`<h3>` real headings so a screen reader can navigate by heading
- a 2–3 sentence summary **before** any detail
- `<table>` with `<caption>`, `<th scope=…>`, and raw numbers for every derived claim
- a citation list giving `(endpoint, field, as_of)` per figure
- `aria-live` region for question-and-answer drill-down answers
- optional Web Audio sonification, off by default

**Never rendered**: level-1 description ("bar chart with a date x-axis"), price targets,
buy/sell language.

## 8. Delivery milestones

| # | Milestone | Contents | Credits | Status | Plan |
|---|---|---|---|---|---|
| M1 | Engine on recorded data | `sources.py`, `narrate.py`, `money.py`, fail-closed verifier, CLI | 0 | pending | `.claude/plans/tunanetra.plan.md` |
| M2 | Accessible surface | `webapp.py`, semantic HTML, `a11y_check.py`, VoiceOver pass | 0 | pending | — |
| M3 | Sonification | `sonify.js` over Web Audio, trend + earcon only | 0 | pending | — |
| M4 | Live top-up capture | peers/ownership for 3 symbols + 90-day daily for 4 | ~10 of 623 | pending | — |
| M5 | Track layer + submission | track-specific top layer, README, videos | 0 | pending | — |

## 9. Open decision

Track selection forks the top layer and nothing below it.

- **Track 01 (AI Agents & Assistants)** — LLM mandatory. The budget-aware planner, the
  custom tool layer over the REST API, and the fail-closed verifier are exactly the
  "custom-built agent logic or orchestration" the track asks for, and "a purpose-built
  interface for a specific participant and problem" is listed as qualifying. Requires an LLM
  in the loop, constrained by the verifier.
- **Track 03 (Market Intelligence)** — LLM optional, but the track explicitly rejects "a
  product that only displays raw Sectors data in a different visual form, however well
  presented". Qualifying therefore rests on the derivations (segment concentration, ownership
  direction runs, peer-relative rank, sector-aware financial normalisation) being defended as
  derived insight, not on the accessibility of the presentation.

Recommendation in the plan: **Track 01**, with the LLM writing prose that the fail-closed
verifier refuses to publish unless every figure traces to an endpoint and field.

## 10. Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Accessibility claim fails under a judge's own screen reader | Test with VoiceOver for real; ship `a11y_check.py`; claim only what was run |
| R2 | Product reads as a re-presentation, not derived insight | Lead with the derivations; name them in the video and the README |
| R3 | `peers`/`ownership` exist in recordings for BBCA only | M4 buys 6 credits of sections; until then the peer section degrades explicitly |
| R4 | Mock fabricates `?sections=peers` and dated `/v2/daily/` | Treat `X-Mock-Source: spec-example` as a hard failure in this product |
| R5 | Sonification used past its parity zone | Volatility and multi-indicator comparisons are spoken numbers, enforced by test |
| R6 | NVDA and TalkBack unavailable on this machine | State exactly which AT was used; do not claim the others |
| R7 | Two products in one repo dilutes the submission | One track, one product argued in the video; the other stays as repo context |
| R8 | Population figure is secondary-sourced | Use one number with explicit attribution, or pull BPS Long Form SP2020 |

## 11. Constraints inherited from the repository

- Standard library only. No venv, no pip, no build step.
- Sectors REST API must be a **core** data source; synthetic data must never be the
  product's data source, and must be labelled on screen if it appears in the video.
- No ad-hoc live calls. `capture.py` only, rehearsed against the mock first.
- Never let `sections`, `classifications`, `periods`, or `n_quarters` default.
- Submissions close **30 Sep 2026, 23:59 WIB**; submitting freezes the repository.
