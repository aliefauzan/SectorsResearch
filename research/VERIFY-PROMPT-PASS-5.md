You are running the **fifth** verification pass on a research corpus in `research/`. Four
passes exist already and **every one of them found real errors in the pass before it** —
including errors the previous auditor had explicitly certified as checked. Pass 4 did exactly
that to pass 3: it found 14, seven of them inside sections pass 3 had signed off.

Assume pass 4 did the same thing to you. **Treat `VERIFICATION-PASS-4.md` as a claim, not as
evidence.** Its author verified nobody's work but their own, and several of its edits are new
code and new prose that no one has ever checked.

Your job, in this order: (1) adversarially verify pass 4's corrections, (2) re-run the
standing checks independently, (3) close what pass 4 left open — and it left a lot, some of
which it admitted and some of which it did not.

---

## Hard constraints

- **Do not register a team, submit any form, sign in to the hackathon portal, or create an
  account.** The user has said explicitly: "dont sign my team". Reading pages already
  authenticated in their browser session is fine; authenticating is not.
- Never enter credentials, complete an OAuth flow, or read/echo an API key value.
- **Do not make a single call to any `/v2/*` endpoint on `api.sectors.app`.** The user has no
  credits. Exclude that host from bulk probes entirely — pass 3 slipped once by including
  `api.sectors.app/` in a subdomain sweep. Nothing billed, but do not repeat it.
- Verify only against public sources — `docs.sectors.app/schema.json`, `llms-full.txt`,
  `llms.txt`, the public Postman collection, public GitHub, public web pages, public DNS/CT —
  or against the local mock server.
- If a claim cannot be settled without spending credits, mark it **unverifiable-until-live**
  rather than asserting it.
- Joining Discord or Slack requires an account. Read public metadata if you can; otherwise
  report them closed. Do not join.

## Web tooling

Try `/firecrawl:firecrawl-scrape` (or `/agent-reach`) first. **Known issue:** in both the
pass-3 and pass-4 sessions `firecrawl scrape` failed on every URL with *"your IP address looks
suspicious, so Firecrawl can't be used without an API key"*. Do **not** sign up for a key —
that is account creation. If it fails the same way, fall back to the in-app browser:

- `mcp__Claude_Browser__navigate` then `mcp__Claude_Browser__get_page_text`
- `mcp__Claude_Browser__javascript_tool` for DOM counts, in-origin `fetch()` status probes,
  reading `sitemap.xml` / `robots.txt`, and scanning JS bundles for route literals

`sectors.app` sits behind a Vercel checkpoint — `await new Promise(r=>setTimeout(r,3000))`
before reading the DOM. Plain `curl` works for GitHub API, `raw.githubusercontent.com`,
`crt.sh`, `api.certspotter.com`, `discord.com/api`, and `docs.sectors.app`.

`dig` works. Note `*.sectors.app` is wildcard DNS — every label resolves. Verify that before
trusting any DNS-based enumeration.

---

## What exists

- `research/README.md` — index, key facts, gap ledger, closure argument, and **four** audit records. Read first.
- `research/VERIFICATION-PASS-4.md` — the most recent audit. **This is your primary target.**
- `research/VERIFICATION-PASS-3.md` — the one pass 4 audited. Useful for checking whether pass 4's verdicts on it were fair.
- `research/01-hackathon/`, `research/02-sectors-platform/` (16 docs), `research/04-build-plan/`
- `02-sectors-platform/02-endpoint-reference.md` and `07-response-shapes.md` are **generated** from `99-raw/schema.json` by scripts in `99-raw/scripts/`
- `research/03-mock-data/` — `extract_fixtures.py`, `mock_server.py`, `synth_universe.py`, `synth_extended.py`, `plan.json`, `capture.py`, `fixtures/`, `synth/`
- `research/99-raw/` — 27 evidence files including the OpenAPI spec, `llms-full.txt`, the public Postman collection, and the pass-3 and pass-4 live-recheck captures

---

## Phase 0 — the meta-finding, and what it implies for where you look

Pass 4's bottom line was that **every error found across four audits has been in one of three
places**: hand-written prose, hand-maintained tables, or code failure paths. The
machine-generated artefacts (the two generated docs, the screener extraction, `plan.json`
validation, the generators) have come through clean repeatedly.

Do not take that as permission to skip them — verify the claim itself, cheaply, then spend
your effort where the base rate says errors live. But treat it as a hypothesis to test, not a
finding to inherit. If a fifth pass finds an error in a generated artefact, that is a much
more interesting result than another prose typo.

---

## Phase 1 — verify pass 4's own corrections

Every item below is an edit pass 4 made. Re-derive each from a primary source and report
**PASS / FAIL / PARTIAL** with the evidence.

1. **The 297-credit claim.** Pass 4 said pass 3's 271 was wrong and replaced it with **297**,
   saving **121**. Re-derive both totals yourself from `plan.json` and the spec.
   - Is removing the screener `?q=` row correct? Check `q`'s schema in the spec yourself.
   - Is adding the `limit` row correct? `/v2/close/` and `/v2/companies/quarterly-financial-dates/` default `limit` to 20 against a max of 30. Does "the same 87 calls with defaults" legitimately mean the sweep becomes 48 pages, or is that a category error of the same kind pass 4 accused pass 3 of? Argue it both ways before deciding.
   - The universe size is quoted as ~950 in the spec and 942 in one pagination example; the `quarterly-financial-dates` fixture says `total_count: 959`. Does 48 hold under all three?
   - Does `financials/quarterly`'s exclusion still hold? Pass 4 said yes. Check it.
   - Verify the corrected table's own arithmetic: 56+18+15+32 = 121, 176+121 = 297.
2. **The invented `Sand` value.** Pass 4 removed a bare `Sand` from `/v2/news/?extension=mining`. Confirm the spec enum has exactly 9 values and no bare `Sand`. Then **check the whole mining section again in both directions** — pass 3 found one invented value there and pass 4 found a second, which is a bad sign for the rest of that table.
3. **The broker-activity attribution.** Pass 4 says `/v2/broker-activity/{broker_code}/top/` takes only `broker_code`, `start`, `end`, `n_brokers`. Verify. Then check every other endpoint attribution in `06-parameter-cheatsheet.md` the same way — pass 4 fixed the one it tripped over and did not systematically re-check the rest.
4. **The "fabricated quotation".** This is pass 4's most serious claim and its weakest evidence.
   It asserts that *"designed to enhance the efficiency and accuracy of our financial data
   products, and not to replace human judgment."* appears nowhere in `99-raw/` — which is true —
   and concludes the quotation was fabricated. **Pass 4 never fetched the live page.**
   Go to `sectors.app/data-operations` and read it. If that sentence is there, pass 4's
   correction is wrong in substance (the quote was real, merely uncaptured) and the fix should
   be to capture the source, not to delete the quotation. Report which it is.
5. **The two other provenance quote fixes** (§1.5) and the ToS `"compete with us"` fix (§1.6).
   Verify each against `99-raw/`, and check the live pages where the capture is thin.
6. **The provenance / cadence table** in `11-data-provenance.md`. Pass 4 added 12 rows. It
   verified crons directly for **three** of them (`sectors_news`, `sectors_idx_suspension`,
   `sectors_indices_company_list`) and wrote the rest from README prose or from the mere
   existence of a workflow file. Specifically unverified:
   - `sectors_idx_daily_data` — cron never read; "daily" comes from the README sentence
   - `sectors_corporate_actions` — cron fetch returned empty
   - `sgx_buyback_pipeline`, `sectors_sgx_short_sell`, `sectors_get_closed_ipo` — "scheduled Action" with no cron read
   - The **endpoint↔repo mapping itself** is inference from Supabase table names (`idx_filings`, `idx_news`, `index_daily_data`). Nothing proves the live API serves from these tables.
   Read the actual workflow files (try both `main` and `master`) and either confirm each row or
   mark it inferred. Also verify the claim "roughly forty `sectors_*` repositories" — count them.
7. **The `sti` resolution.** Pass 4 moved `sti` out of unverifiable-until-live on the strength
   of `sectors_indices_company_list` inserting `^STI` into a Supabase table called
   `index_daily_data`. That is an inference from a table name. Decide whether it is strong
   enough to justify the status change, or whether `sti` belongs back in §3 with the evidence
   noted. Same question for the new `klse` candidate.
8. **`capture.py`'s two fixes.** Pass 4 rewrote the skip logic (`is_settled`) and added partial-
   sweep recording plus offset resume. New code, tested by its author against one scenario.
   Exercise it properly against the mock:
   - Resume when the recording file on disk is missing or corrupt
   - Resume when `pages` or `limit` changed in `plan.json` between runs
   - A **404 mid-sweep** — does `billed_cost = pages_billed + 1` do the right thing, and is the entry settled or retryable afterwards?
   - A sweep whose `has_next` legitimately goes false before `pages` is exhausted
   - `merge_pages` on a resumed prefix: are `offset`, `next_offset` and `has_next` in the merged envelope coherent, or stale?
   - Does the ledger's `billed_cost` still reconcile exactly with the mock's meter in every one of those cases?
   - Re-run the full-plan rehearsal: 87 entries → 149 HTTP calls, ledger 176, meter 167. Confirm the 9-credit gap is still only `free-float`.
9. **The mock divergences pass 4 documented** (§1.12): out-of-enum `sections` billed instead of
   400-free, reports not sliced by `sections`, `free-float` flat-billed. Verify all three, and
   look for a fourth — pass 4 found these by poking, not by enumerating.
10. **The matching-board recount.** Pass 4 got 48 / 15-7-12-14, 45-2-1 sizes, 52 participants,
    22 of 48 cards carrying text, four projects disclosed. Its card parser used **positional
    indexing** (`L[j+3]`) into the rendered text, which is fragile. **Recount live yourself**,
    with a different method, and expect different numbers — this is the one figure guaranteed
    to be stale, registration closes 22 September, and the board moves daily.
11. **The Slack and Discord metadata.** Pass 4 read "105 members" and "This invitation expires
    in 15 days" off the invite landing page and derived "expires ~20 September". Re-read it.
    Does the page personalise per visitor? Is the expiry countdown relative to page load?
    Recompute the date against today. Same for the Discord member count.
12. **The Bahasa Indonesia negative.** Pass 4 declared definitively that the Indonesian rules
    are not on the site, on four legs: 20 candidate 404s, a JS-bundle route scan, `?lang=id`
    and `Accept-Language` being ignored, and no i18n markup. The bundle scan matched a
    **specific regex over 25 script `src`s** — that is the weakest leg. Re-derive it, ideally
    by a different route (Next.js build manifest, `_next/static/chunks/app` listing, or the
    RSC payload). If you cannot reproduce the negative, say so.
13. **The wildcard-DNS finding.** Pass 4 claims host enumeration on `sectors.app` is
    uncloseable because both the DNS and the certificate are wildcards. Verify both halves.
    Then try at least one enumeration method neither pass 3 nor pass 4 used — passive DNS,
    Shodan/Censys host search, `_dmarc`/SPF records, Vercel project-name probing, or the
    `sitemap.xml` of each known host.

---

## Phase 1b — re-run the standing checks independently

Accept no prior PASS, from any pass.

14. Regenerate both generated docs and diff against committed.
15. Count GET endpoints in the spec; reconcile against 70. List anything in prose but not spec, and vice versa.
16. Extract every declared cost from all 70 endpoint descriptions; diff against every cost stated in prose, `plan.json`, and `04-build-plan/`. Re-check the arithmetic in **every** worked example, not just the tables. Four passes have each found a cost error.
17. Re-extract IDX (219) and SGX (85) screener fields and all ten per-category subtotals, plus the 20 `[Big caps only]` and 10 `[Banks only]` SGX markers.
18. Diff every enum, default, min/max and required flag in `06-parameter-cheatsheet.md` against the spec, both directions. Flag invented values and wrong endpoint attributions.
19. **`07-response-shapes.md` has never been cross-checked against the fixtures by any pass.** It is generated, so it should match — verify that the row keys it documents are the keys the fixtures actually contain, for all 70.
20. Auth: REST raw-key header, MCP `Bearer` header, and the spec's `OAuthBearerAuth` scheme, from primary sources.
21. Query syntax: bracket notation, `is not null`, parenthesised groups, multi-column `order_by`, the `order_by` arithmetic-parentheses rule, quarterly `field[Qi-YYYY]`, `q=` vs `where`. Confirm `is null` still appears nowhere, and that the three constructs resting on the query-builder capture really appear there.
22. Every quoted string in the corpus must appear verbatim under `99-raw/`. Pass 3 found 7 problems, pass 4 found 4 more in material pass 3 certified. **Pass 4's checker had a naive fenced-code detector** (toggles on any line starting with triple-backtick; does not handle `~~~` or indented fences) — write a better one and re-run. Also check quotes pass 4 itself introduced.
23. Hackathon rules, tracks, prizes, deadlines, eligibility, submission requirements — live. **Pass 4 re-read `/rules` and did NOT re-read the three `/tracks/*` pages.** Read those.
24. `plan.json`: every path, every param against the spec's enums and ranges, every slug attested, total arithmetic.
25. Generators run clean from empty; every promised output present; deterministic across runs; byte-identical to committed `synth/`.
26. `capture.py` against the mock only: idempotency, budget cap stopping *before* exceeding, resume, 404 recorded-and-not-retried, ledger accounting, cost-header detection.
27. Internal consistency: stale numbers, broken relative links, contradictions between docs. Pass 4 left three dangling links inside `99-raw/agent-skills/SKILL.md` (a verbatim third-party capture) — confirm those are the only ones.
28. **Re-verify the Postman collection diff.** Pass 3 claimed 70 endpoints, zero path differences, zero query-parameter differences against `schema.json`. Pass 4 did not re-check it. Do.
29. **Re-verify pass 3 §1.8**, the four mining `/learn` guide titles. Pass 4 explicitly did not re-check this one.

---

## Phase 2 — close what pass 4 left open

Pass 4 admitted some of these and did not mention others. Prioritise by what Phase 1 exposes.

- **`github.com/supertypeai` — 74 repos, ~15 read.** Roughly 59 remain. Pass 4 flagged but never explored a **US-market surface**: `sectors_us_insider_trading`, `sectors_us_cron`, `us-sectors-kb`, `sectors_us_institution_holding`. Also unread: `sectors_idx_fear_and_greed_index`, `sectors_get_esg_score`, `sectors_price_anomaly_updater`, `sectors_generate_subsector_index`, `sectors_get_market_cap_worldwide_data`, `summarize-agm-result`, `sectors_ticker_pdf_generator`, `sectors_dcf_calculation`, `sectors_forecast_growth_rate`, `broksum`, `buyback_notify`, `run_sectors_watchlist_notification`, `sectors_guard_validator`, `sectors_news_endpoint`, `sectors_news_form`, `financial_analytics_workshop`. Several of these imply API surface or scoring methodology the dossier does not document.
- **`sectors.supertype.ai`** — found in `supertype.ai`'s CT record by pass 4 and never probed. Determine what it is.
- **`admin.sectors.app` and `insider.sectors.app`** — found by pass 3, not re-probed by pass 4. Confirm they still behave as described. Do not authenticate.
- **`mining.sectors.app` and `reits.sectors.app`** — their sitemaps and `llms.txt` have not been re-fetched since 4 September. Check for drift the way pass 4 checked `docs.sectors.app`.
- **21 of 39 documentation recipes remain unread** (visualization, no-code, OAuth-connector). The judgement that they are out of scope is reasonable and still untested. Spot-check at least three for API content the dossier lacks.
- **FLARE part 2 (NII/NIM/IRR)** — enumerated, never read.
- **The `/portal/*` routes** are login-gated and stay closed. Confirm the gate string is unchanged; do not attempt to pass it.
- **Anything added or changed on the hackathon site or `sectors.app` since 5 September.** Re-hash `schema.json`, `llms.txt`, `llms-full.txt`; re-read `/release`; re-read `/rules` and `/tracks/*`.
- **The failure paths pass 4 named as the next target and did not test**: `mock_server.py`'s own error handling (malformed query strings, concurrent credit exhaustion, a corrupt recording in `recorded/`, a fixture that fails to parse) and `synth_extended.py`'s (zero companies, a missing input directory, `--years 0`). Pass 4 predicted errors live here. Test the prediction.
- **`synth_extended.py`'s `is_trading_day`** applies the 2026 holiday set by `(month, day)` to dates in any year, so a 2025 date matching a 2026 holiday is wrongly excluded. Pass 4 noticed and did not act. Decide whether it matters and fix or document it.
- If you find data the mock generators still cannot produce, extend `synth_extended.py` and say what you added. Pass 4 declined to extend it and gave three reasons — check whether those reasons hold.

---

## Reporting

Write to `research/VERIFICATION-PASS-5.md`, save live evidence to
`research/99-raw/pass5-live-recheck-<date>.md`, and add a summary row to the audit section of
`research/README.md`. Fix errors directly in the docs. Structure:

- **Corrections made** — the claim as written, the correct value, the primary source.
- **Confirmed** — what you checked and the check you ran.
- **Unverifiable-until-live** — what genuinely needs credits to settle.
- **New material** — what Phase 2 added.

End with the honest bottom line: how much of this corpus is evidence-backed versus inferred,
broken out by layer (structural / behavioural / code / time-sensitive).

If a section is clean, say so plainly rather than manufacturing findings. But note that **four**
consecutive audits have each found real errors in their predecessor — including in sections the
predecessor certified — so a clean sweep is a strong claim and needs strong support. Pass 4
found seven of its fourteen inside material pass 3 had signed off; assume the same rate applies
to pass 4's own work.

One specific warning. Pass 4's report is confident and well-cited, which makes it easy to
inherit rather than check. Two of its headline findings rest on evidence it did not fully
close: the "fabricated quotation" (§1.4 — it never read the live page) and the `sti`
resolution (§2.4 — an inference from a database table name). Start there.
