# Audit record

Six passes were run over the dossier in `research/`, each treating the one before it as an
unproven claim. Every pass found real errors in its predecessor — including claims the
previous auditor had explicitly certified as checked.

**Read [`VERIFICATION-LIVE.md`](VERIFICATION-LIVE.md) first, and treat it as authoritative
wherever it disagrees with an earlier pass.** Passes 1–5 verified the corpus against
documentation only; every behavioural claim in them was the documentation's word. The live
pass is the only one that called the API, and it overturned several of them — the endpoint
count (66 callable, not 70), the rate limit (25 billed requests per rolling 30 s, not a
spacing rule), the Cloudflare block on `Python-urllib`, and the sector-dependent field name in
`/v2/financials/quarterly/{symbol}/`.

## Reports

| Pass | Date | Method | Findings still standing |
| --- | --- | --- | --- |
| 1–2 | 4–5 Sep 2026 | Documentation-only; recorded inline in [`../README.md`](../README.md) rather than as separate reports | Superseded |
| 3 | 5 Sep 2026 | [`VERIFICATION-PASS-3.md`](VERIFICATION-PASS-3.md) — every claim re-derived from a primary source, taking no prior audit as evidence. Zero `/v2/*` calls | Twelve corrections, all re-checked by pass 4 |
| 4 | 5 Sep 2026 | [`VERIFICATION-PASS-4.md`](VERIFICATION-PASS-4.md) — pass 3's report treated as a claim. Zero `/v2/*` calls | Corrections to pass 3, plus the independent team-board recount |
| Live | 6 Sep 2026 | [`VERIFICATION-LIVE.md`](VERIFICATION-LIVE.md) — **the first pass that called the API.** All 66 callable endpoints hit and recorded; 265 credits | **Authoritative on every behavioural claim** |

## Prompts

The instructions each pass was given, kept because they encode the constraints that made the
audits trustworthy — no account creation, no form submission, no credential entry, and (before
the live pass) no `/v2/*` call at all.

- [`prompts/VERIFY-PROMPT.md`](prompts/VERIFY-PROMPT.md) — the original independent-verification brief
- [`prompts/VERIFY-PROMPT-PASS-5.md`](prompts/VERIFY-PROMPT-PASS-5.md) — the fifth doc-only pass
- [`prompts/VERIFY-PROMPT-LIVE.md`](prompts/VERIFY-PROMPT-LIVE.md) — the live procedure: phases, budget ceiling, and the gate to check before each one

> **Paths in these documents are as they were when each pass ran.** The dossier was
> reorganized after the live pass — `03-mock-data/` is now `harness/` (scripts under
> `harness/src/`, plans under `harness/plans/`) and `99-raw/` is now `evidence/`. Commands
> quoted in the reports below are left verbatim, because they are a record of what was
> executed, not instructions to re-run.

## Supporting evidence

The raw re-check notes live with the rest of the provenance in
[`../evidence/`](../evidence/): `pass3-live-recheck-2026-09-05.md`,
`pass4-live-recheck-2026-09-05.md`, `live-capture-2026-09-06.md`, and the portal
`usage-log/` CSVs that independently confirm what the API actually charged.
