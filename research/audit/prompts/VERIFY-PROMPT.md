# Prompt: independent verification + deeper research pass

Paste the block below into a fresh Claude Code session opened at `/Users/af/dumpProject/Sectors`.

---

You are auditing a research corpus that a previous session produced in `research/`. Your job is two things, in this order: **(1) independently verify what is already there, assuming it may contain hallucinations, and (2) extend it where verification exposes gaps.** Treat every claim as unproven until you have re-derived it from a primary source.

## Hard constraints

- **Do not register a team, do not submit any form, do not sign in to the hackathon portal, do not create an account.** The user has explicitly said "dont sign my team". Reading pages that are already authenticated in their browser session is fine; authenticating is not.
- **Never enter credentials, complete an OAuth flow, or read/echo an API key value.**
- **Do not make a single live call to `api.sectors.app`.** The user has no credits yet and burning them is the exact failure mode this corpus exists to prevent. Everything must be verified against public sources (`docs.sectors.app/schema.json`, `llms-full.txt`, `llms.txt`, public web pages) or against the local mock server.
- If a claim cannot be verified without spending credits, mark it explicitly as **unverifiable-until-live** rather than asserting it.

## What exists

- `research/README.md` — index, key facts, gap ledger, and the records of two prior verification audits. Read this first; it tells you what the previous session already claims to have checked.
- `research/docs/hackathon/` — overview, rules, tracks, submission checklist.
- `research/docs/api/` — 16 docs. `02-endpoint-reference.md` and `07-response-shapes.md` are **generated** from `evidence/spec/schema.json`; the generators live in `tools/`.
- `research/harness/` — `extract_fixtures.py`, `mock_server.py` (credit meter + recording replay), `synth_universe.py`, `synth_extended.py`, `plan.json` (87 calls / 176 credits / 5 tiers), `capture.py` (idempotent budget-capped fetch harness).
- `research/plan/` — build ideas, competitive landscape, already-published work.
- `research/evidence/` — 22 evidence files, including the full OpenAPI spec and `llms-full.txt`.

## Phase 1 — adversarial verification

Work through these and report **PASS/FAIL with evidence** for each. Do not take the previous session's audit records as proof; re-run the checks yourself.

1. **Regenerate both generated docs** from `evidence/spec/schema.json` using the scripts in `tools/` and diff against the committed versions. Any drift is a finding.
2. **Endpoint count and paths.** Independently count GET endpoints in the spec and reconcile against the 70 claimed. List any endpoint documented in prose but absent from the spec, and vice versa.
3. **Credit costs.** Extract every declared cost from the spec/docs and diff against every cost stated anywhere in the prose docs, `plan.json`, and `plan/`. The previous session got costs wrong at least twice — assume more remain. Pay attention to the non-flat formulas (per-section, per-classification×period, per-quarter, per-page) and check the arithmetic in every worked example.
4. **Screener field lists.** Re-extract the IDX (219 claimed) and SGX (85 claimed) field sets from source and diff against `03-screener-query-language.md` and `09-sgx-klse-coverage.md`. Report exact counts.
5. **Parameter enums and defaults.** Diff every enum, default, and required/optional flag in `06-parameter-cheatsheet.md` against the spec. Flag invented values.
6. **Auth mechanics.** Confirm the REST header form vs the MCP header form from primary sources. These differ; verify both rather than assuming symmetry.
7. **Query-language syntax.** Verify each documented construct (bracket notation, null predicates, parenthesised groups, multi-column ordering, natural-language `q=` vs deterministic `where`/`order_by`) against a primary source. The previous session asserted a wrong answer here twice and only corrected it after being contradicted by the live query builder — re-check it independently.
8. **Quotes.** Every quoted string in the corpus must appear verbatim in a file under `evidence/`. Grep each one. Report any quote with no saved provenance, and any that has drifted from its source.
9. **Hackathon facts.** Re-verify rules, tracks, prizes, deadlines, eligibility, submission requirements, and team counts against the live pages. Numbers in this corpus have been wrong before.
10. **`plan.json`.** Validate every path against the spec, every parameter against the spec's enums, and the total credit arithmetic.
11. **Mock and generators.** Run `extract_fixtures.py`, `synth_universe.py`, `synth_extended.py` clean; confirm every output file the docstrings promise actually appears. Start `mock_server.py` and verify the credit meter, the error codes it claims to emit, and the recording-replay path.
12. **`capture.py` behaviour, against the mock only.** Verify idempotency (second run makes zero calls), the budget cap (stops before exceeding, not after), resume-after-cap, 404 handling (recorded as billed and not retried), ledger accounting, and cost-header detection.
13. **Internal consistency.** Check for stale numbers that survived earlier edits, broken relative links, and contradictions between any two docs.

## Phase 2 — extend

Only after Phase 1, and prioritised by what Phase 1 exposed:

- Re-sweep the hackathon site and `sectors.app` for anything added or changed since the corpus was written; diff against `evidence/`.
- The previous session found that `mining.sectors.app` and `reits.sectors.app` are separate hosts appearing in no sitemap, discovered only by opening footer links one at a time. Repeat that exercise properly: enumerate every host, subdomain, and footer destination, open each, and confirm nothing else is hiding. Do not accept a sitemap as proof of completeness.
- Look for primary sources the corpus never captured: Postman collections, the MCP tool listing, changelogs, status pages, developer blog posts, GitHub organisations, community/Discord announcements, and any published example projects.
- For any API area the docs describe but no worked example covers, either find an example or state plainly that none exists.
- If you find data the mock generators cannot yet produce, extend `synth_extended.py` and say what you added.

## Reporting

Write findings to `research/VERIFICATION-PASS-3.md` and add a summary row to the audit section of `research/README.md`. Fix the errors you find directly in the docs. Structure the report as:

- **Corrections made** — the claim as written, the correct value, and the primary source.
- **Confirmed** — what you checked and found sound, with the check you ran.
- **Unverifiable-until-live** — claims that genuinely cannot be settled without spending credits.
- **New material** — anything Phase 2 added.

State the honest bottom line at the end: how much of this corpus is now evidence-backed versus inferred. If you find nothing wrong in a section, say so plainly rather than manufacturing findings — but note that two prior audits each found real errors, so a clean sweep is a claim that needs strong support.
