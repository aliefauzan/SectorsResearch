# Verification Pass 3 — Adversarial Re-audit

**Date:** 5 September 2026 · **Method:** every claim re-derived from a primary source, taking
no prior audit record as evidence. **Zero calls were made to any `/v2/*` endpoint on
`api.sectors.app`.** No account was created, no form submitted, no team registered, no
credential entered.

Two prior audits each found real errors. This one found **twelve** — four in the prose, six in
the code, two in the mock's own documentation — plus one headline number that has gone stale
since capture. It also added four primary sources the dossier had never opened, two of which
independently corroborate large parts of it.

---

## 1. Corrections made

### 1.1 The fetch plan's headline saving was overstated by 2×

| | |
| --- | --- |
| **As written** | `15-fetch-strategy.md`: "The same 87 calls with defaults would cost roughly **three times** as much." README: "**176 of 1,000 credits**, why that is **a third** of what the same calls cost with defaults." |
| **Correct** | Defaults cost **271** credits against the plan's 176 — **54% more, not 200% more.** |
| **Source** | The doc's own savings table. It itemises 56 + 18 + 15 + 6 = **95** credits saved. 176 + 95 = 271, and 176/271 = 65%. For "a third" the saving would have to be ~352. |

The per-line arithmetic in that table is correct; only the summary sentence was wrong. It had
survived two audits because both checked the table and neither added it to the total.
`financials/quarterly` is legitimately excluded — the spec documents **no default** for
`n_quarters` (`minimum: 1`, no `default`, no `maximum`), so its default cost is unknowable.

### 1.2 A second surviving "2 credits" for shareholders composition

| | |
| --- | --- |
| **As written** | `what-we-can-build.md:135` — ``/v2/company/shareholders-composition/{symbol}/` (2 credits)` |
| **Correct** | **1 credit** |
| **Source** | `schema.json` → that path → `"Costs 1 API credit."` |

Pass 1 recorded fixing this exact error ("corporate actions and shareholders composition are 1
credit each, not 2") and pass 2 re-checked costs. One instance survived both — the same failure
mode as the "46 teams" survivor. I re-extracted the credit sentence from **all 70** endpoints
programmatically and diffed against every cost stated anywhere in the prose; this was the only
remaining mismatch.

### 1.3 A stale screener field count

`what-we-can-build.md:34` said **220-field screener**; every other one of the eight mentions in
the dossier says 219. Re-derived from source: the spec's `/v2/companies/` description defines
exactly **219** fields as `- **name**:` bullets. Corrected to 219.

### 1.4 `index_code` is documented — the dossier said it was not

| | |
| --- | --- |
| **As written** | `06-parameter-cheatsheet.md`: "a **free-form string with no enum and no helper endpoint that lists valid values** — the spec only gives `lq45`, `ihsg`, `idx30` as examples", then 8 codes "confirmed from the product's index pages" and 5 "plausible candidates". README gap ledger: "Full IDX index code list — No helper endpoint enumerates them." |
| **Correct** | The endpoint's own description carries `<Accordion title="Available index codes">` listing **all 17**. |
| **Source** | `schema.json` → `/v2/index-daily/{index_code}/` → description: `` `ftse`, `idx30`, `idxbumn20`, `idxesgl`, `idxg30`, `idxhidiv20`, `idxq30`, `idxv30`, `ihsg`, `jii70`, `kompas100`, `lq45`, `sminfra18`, `srikehati`, `sti`, `economic30`, `idxvesta28` `` |

The 8 confirmed codes and all 5 "candidates" are real. But **four codes appear nowhere in the
dossier**: `idxv30`, `sminfra18`, `sti`, `idxvesta28`. The claim was true of the JSON-Schema
`enum` field and of the parameter's `description`, and false of the endpoint description — the
audits had checked the first two and not the third.

Corroborated a third way: `supertypeai/sectors_indices_company_list` publishes a constituent
CSV for 15 of the 17. Rewritten with a per-code source column, and `synth_extended.py` extended
from 8 index series to 17.

### 1.5 An invented parameter in the mining table

`06-parameter-cheatsheet.md` listed `/v2/mining/resources-reserves/` (the index endpoint) as
accepting `commodity_type` values `Coal, Copper, Gold, Nickel`. **That endpoint takes no
parameters at all** — `schema.json` gives it an empty `parameters` list. Only the
`/{province}/` detail variant is parameterised. Removed from the table.

This was the single invented value out of 31 enum claims machine-checked against the spec; the
other 30 match exactly, including all four province lists (37 / 33 / 22 / 8) and the 8-province
auction set member-for-member.

### 1.6 `is null` has no primary source anywhere

| | |
| --- | --- |
| **As written** | `03-screener-query-language.md` Syntax: "**Operators:** … `like`, `in`, **`is null`**, **`is not null`**" |
| **Correct** | `is not null` is attested. **`is null` is not — in any source.** |
| **Source** | Spec's *Syntax and Operators* accordion lists only `=`, `!=`, `>`, `>=`, `<`, `<=`, `like`, `in`. The Deterministic Query Builder capture attests `is not null` three times. Grepping the entire `evidence/` corpus for `is null` returns **one** hit — `llms-full.txt:7495`, in a Google Sheets recipe ("exclude any rows where the `Symbol` field is null"), not the query language. |

The README notes this operator was got wrong twice before and corrected only after the live
query builder contradicted it. The correction over-shot: it added the *complement* by symmetry.
`is null` probably works, but that is an inference, and the dossier presented it as documented.
Removed from the operator list and moved to unverifiable-until-live, with an explicit note on
which three constructs rest on the query builder rather than the spec.

**The other three constructs check out.** Verbatim from the query builder capture:
`where=(sub_sector="banks" and eps[2024]>0 and total_yield[2024] is not null)&order_by=-total_yield[2024], -market_cap`
— parenthesised group, `is not null`, and multi-column ordering with per-column direction, in
one string.

### 1.7 Two misquotes and one quote drift

| Where | Quoted as | Source actually says |
| --- | --- | --- |
| `03-screener…md:129` | "500+ financial metrics" | `sectors-pricing.md`: "filter companies by **more than 500** financial metrics" |
| `14-flare…md:71` | "create remarkable tutorials featuring Sectors datasets" | `footer-pages-opened.md:52`: "create remarkable tutorials **or guides ft.** Sectors datasets" |
| `what-we-can-build.md:179` | "innovative use of the Sectors API" | `hack-rules.md:254`: "how **innovative is the use of** Sectors API **or MCP**" |

Method: extracted all 165 quoted strings ≥15 characters from every doc and grepped each against
the concatenated `evidence/` corpus with punctuation normalised, then hand-classified the misses
to separate real quotations from code fragments and scare quotes.

### 1.8 Four mining guide titles quoted from nothing — one of which does not exist

`13-subdomains-and-terms.md` quoted coal's learn guides as "Coal Mining in Indonesia",
"Coal Types and Quality", "HBA Coal Price & Royalty", a glossary, and "Coal Resources and
Reserves". None had saved provenance. Enumerated from `mining.sectors.app/sitemap.xml` (445
URLs, 17 under `/learn`) and read each `<title>`:

- "Coal Mining in Indonesia" → **"Coal Mining in Indonesia Background"**
- "Coal Types and Quality" → **"Types of Coal"**
- "HBA Coal Price & Royalty" → **"HBA Coal Prices and Royalties"**
- **"Coal Resources and Reserves" is not a page.** Coal has exactly four learn pages. Resources
  and reserves live at `/indonesia/insights/resources-and-reserves`, a different section.

"17 orientation articles" is also off by one: 17 `/learn` URLs = **16 articles + 1 index page**.

### 1.9 MCP tool count

"65+ tools" appeared in three docs. The documentation catalogue names **exactly 65**, all
`fetch-*`. The MCP server's own source — `supertypeai/sectors-mcp`, `src/tools/generated/*.ts`
— contains **66** files. The 66th is **`get-subsectors`**, the only tool not named `fetch-*`,
documented nowhere. Rewritten as "65 documented, 66 implemented" with the extra tool named.

Per-market splits all check out: IDX 31 / SGX 11 / KLSE 4 / mining 19 = 65.

### 1.10 `mock_server.py` mispriced every report endpoint except one

The mock hardcoded `return len(sections.split(",")) if sections else 8` for the whole
per-section family. Measured against the mock, before the fix:

| Endpoint | Mock charged | Spec says |
| --- | --- | --- |
| `/v2/company/report/{symbol}/` | 8 | 8 ✓ |
| `/v2/subsector/report/{sub_sector}/` | **8** | **6** |
| `/v2/sgx/company/report/{symbol}/` | **8** | **4** |
| `/v2/klse/company/report/{symbol}/` | **8** | **4** |

Pass 2's record reads "report 8→1 and top-changes 10 confirmed" — it exercised the IDX report
only, so the bug was invisible. A team budgeting an SGX/KLSE comparison against this mock would
have over-provisioned by 2× per report.

**Fixed at the source of truth.** `extract_fixtures.py` now parses the spec's own
"Default behavior (all *N* sections) consumes *N* credits" into a `credit_default_items` field
(11 endpoints carry one), and the mock reads it. Re-verified: 8 / 6 / 4 / 4 / 10 / 5 / 5, plus
constrained calls, all now correct.

### 1.11 `mock_server.py` under-billed the SGX screener

The 3-credit natural-language override was gated on `template == "/v2/companies/"`, so
`/v2/sgx/companies/?q=` billed **1** instead of **3**. Now keyed on the endpoint's own
"for structured queries" cost string, which covers both screeners. Verified: both charge 3.

### 1.12 `capture.py` could not be run against the mock, and did not paginate

Two defects in the one tool that spends real credits:

1. **`BASE` was hardcoded to `https://api.sectors.app`** with no flag and no env var — despite
   `harness/README.md` recommending exactly that switch (`SECTORS_BASE_URL`) for user
   code. Pass 2 recorded driving `capture.py` "against the local mock"; as committed that is
   not possible without editing the file. Added `--base-url` and `SECTORS_BASE_URL` support.

2. **No pagination.** `plan.json` budgets 32 credits each for `/v2/close/` and
   `/v2/companies/quarterly-financial-dates/`, annotated "~32 pages for the full universe".
   `capture.py` issued **one** call per plan entry. So those two entries would have billed 2
   credits, recorded 60 of ~942 tickers, and reported spending 64 — while tier 2 is documented
   as "Full-universe sweeps". Added `"pages": 32` to those entries and a paging loop that walks
   `offset`, honours `pagination.has_next`, sleeps between pages, and merges into one recording
   with `pages_fetched`. Verified against the mock: **32 HTTP calls, one merged recording,
   still idempotent on re-run.**

### 1.13 The mock's own documentation

- `harness/README.md` showed a worked `__usage` example under `--credits 1000` reading
  `"credits_spent": 20, "credits_remaining": 0`. Corrected to **980**. (The other fields are
  self-consistent: 1 report×8 + 8 tags×1 + 1 `?q=`×3 + 1 subsectors×1 = 11 calls, 20 credits.)
- It claimed the meter charges "the documented per-endpoint cost, including the per-section …
  formulas". That was false for three of four report endpoints until 1.10. Claim now states
  the per-endpoint defaults explicitly.

### 1.14 The matching board has moved

Not an error — the count was right against its evidence — but the dossier's most prominent
strategic claim is now stale.

| | 4 Sep capture | 5 Sep live |
| --- | --- | --- |
| Public team cards | 44 | **48** |
| Track 01 | 16 | **15** |
| Track 02 | **4** | **7** |
| Track 03 | 11 | **12** |
| No track yet | 13 | **14** |

Counted twice (rendered text, then DOM: `{"team_cards":48,"byTrack":{"1":15,"2":7,"3":12},"noTrackPref":14}`).
I also re-derived the 4 Sep figures from `evidence/hackathon/hack-matching.md` and they match the dossier's
44 / 16-4-11 exactly, so pass 1's correction was sound.

Track 02 is **still the least crowded**, but "a quarter as popular as Track 01" is now wrong —
it is roughly half, and three of the four teams that joined in one day chose it. Updated in
`competitive-landscape.md` and README, with an explicit instruction to re-count near the
22 September close.

---

## 2. Confirmed

Everything below was re-derived this pass, not taken from an audit record.

| # | Check | Method | Result |
| --- | --- | --- | --- |
| 1 | Generated docs reproducible | Ran both scripts in `tools/`, diffed against committed | **byte-identical**, both |
| 2 | Endpoint count | Counted operations in `schema.json` | **70 path items, 70 GET, 0 non-GET.** IDX 34 / SGX 12 / mining 19 / KLSE 5 = 70 |
| 2b | Prose ↔ spec path reconciliation | Regexed every `/v2/…` string in every file, resolved against spec templates | **133 distinct strings, 127 resolve.** The 6 that don't are `docs.sectors.app` URLs (`/get-started/v2/overview`, `/v2/migration-guide`, `/api-references/v2/changelog`, `/api-references/v2/indonesia/screener/companies`), a bare `/v2` base-URL reference, and a bare `/v2/index-daily` family reference. No endpoint is documented in prose and absent from the spec |
| 3 | Credit costs | Extracted the credit sentence from all 70 endpoint descriptions; diffed against every cost stated in prose, `plan.json` and `plan/` | 49 flat-1, exactly 4 two-credit (`most-traded`, `brokers/top`, `broker-summary/{}/top`, `broker-activity/{}/top`), 17 non-flat. One prose mismatch (§1.2) |
| 3b | Non-flat formulas | Each re-read from the spec | per-section 8/6/4, per-classification×period 2×5=10, per-classification 5, per-quarter, per-page, per-100-rounded-up — all as documented |
| 3c | Worked examples | Re-computed | Track budgets 304 / 404 / 854 all sum correctly · 365 days ÷ 90-day cap = 5 calls ✓ · 942 ÷ 30 = 32 pages ✓ · ~950 ÷ 100 rounded up = 10 ✓ · 200 companies × 8 sections = 1,600 ✓ · tier sums 5/28/74/55/14 = 176 ✓ · 1000 − 176 = 824 ✓ |
| 4 | IDX screener fields | Re-extracted from the spec description | **219**, and 219/219 match the doc's tables. The 7 extra rows are the query-parameter table, correctly |
| 4b | SGX screener fields | Same | **85**, 85/85 exact, zero drift |
| 4c | Category counts | Parsed the spec's per-category accordions | IDX 24 / 3 / 31 / 107 / 44 / 10 = **219**; SGX 34 / 1 / 16 / 34 = **85**. Every per-category figure in the docs matches |
| 5 | Parameter enums | All 45 enum-bearing params machine-diffed both directions | 30 of 31 doc claims exact; 1 invented (§1.5). Province counts 37/33/22/8 exact |
| 5b | Defaults | All 47 documented defaults extracted | Cheat sheet correct throughout: `limit` 50/200 and 20/30, `min_mcap_billion` 5000, `approx` true, `n_stock` 5 (1–10), `n_brokers` 1–90, `extension` idx, `order_by` symbol, `desc` false. Date-range defaults quoted **verbatim** from the spec |
| 6 | Auth, REST | Spec `securitySchemes` + docs | `apiKey` in header `Authorization`; docs state plainly "The Authorization header uses the raw key (no "Bearer" prefix)" |
| 6b | Auth, MCP | Client config blocks in `llms-full.txt` | `"Authorization": "Bearer YOUR_API_KEY_HERE"` — the prefix **is** required. The dossier documents both forms correctly |
| 7 | Query syntax | Each construct traced individually | Operators, `and`/`or`, quoting, `in` lists, `field[YYYY]`, `field[Qi-YYYY]`, arithmetic — all in the spec's accordions. Parentheses, multi-column `order_by`, `is not null` — query-builder capture. `is null` — nothing (§1.6) |
| 8 | Quotes | 165 quoted strings ≥15 chars grepped against `evidence/` | 3 drifted (§1.7), 4 unsourced (§1.8), remainder trace |
| 9 | Hackathon rules | Full live re-read of `/rules` | **Unchanged since capture.** Dates, eligibility, 2–4 teams, 1,000 credits, 90-day repo, 1-min + 3-min videos, 40/30/30, IDR 50M split, trade-execution ban, no-financial-advice — all word for word |
| 9b | Site surface | 25 paths probed | 7 public pages, `/portal/*` gated. 18 candidates 404 including 5 Bahasa-Indonesia routes. `/robots.txt` exists (not previously captured); no sitemap |
| 9c | Portal gate string | Fetched `/portal/team` HTML | Contains "Checking your Sectors Account…" verbatim — the README quote was right but had no saved provenance; now captured |
| 10 | `plan.json` | Every path resolved, every param checked against the spec's enums/min/max, every cost re-derived | **87/87 paths resolve · 0 unknown params · 0 enum violations · 0 out-of-range values · 176 total, tiers 5/28/74/55/14.** The only cost divergences from my independent model were the two pagination entries, which turned out to be a `capture.py` defect (§1.12), not a plan error |
| 11 | `extract_fixtures.py` | Run clean | 70 fixtures + index, **0 endpoints without an example**, byte-identical to committed |
| 11b | Generators | Run from empty, twice | All 6 + 15 promised outputs present; **identical hashes across runs** — deterministic |
| 11c | Holiday calendar | Doc-12 code block vs doc-12 table vs `synth_extended.py` | **22 dates, all three identical.** 239 trading days independently recomputed ✓. All 8 per-month counts correct ✓. September has none ✓. 25 August is a holiday inside the build window ✓ |
| 11d | Mock error codes | Exercised live | 401 + `subscription_not_active` · 410 + `version_gone` · 402 + `insufficient_credits` (refuses the call, does not go negative) · 404 free on unknown path · 429 body **verbatim from the spec** · 503 + `service_unavailable`. Two report-cost bugs found (§1.10–1.11) |
| 11e | Recording replay | Manifest + fallback | Recordings served in preference to fixtures; non-200s recorded and skipped |
| 12 | `capture.py` | Driven against the mock only | Dry run **0 calls** and 87/176 ✓ · idempotent re-run **0 calls** ✓ · budget cap stops **before** exceeding ("next call would exceed budget (20 + 1 > 20)"), cumulative lands exactly on 20 ✓ · resume after raising the cap ✓ · 404 recorded `"billed": true` and never re-called ✓ · ledger sums to the mock's meter exactly ✓ · cost headers detected and surfaced ✓. Two defects found (§1.12) |
| 12b | Full-plan rehearsal | Whole plan against the mock post-fix | 87 entries → **149 HTTP calls** (87 + 2×31 pages), 87 recordings, ledger 176, mock meter 167. The 9-credit gap is `free-float`, budgeted 10 for ~950 rows and charged 1 by a small fixture — expected, not a defect |
| 13 | Internal links | All 43 markdown files | **Zero broken relative links** in the dossier. 3 dangling links exist inside `evidence/sectors/agent-skills/SKILL.md`, which is a verbatim third-party capture |
| 13b | Cross-doc numbers | Scanned 10 recurring figures | One stale (§1.3). All four surviving "46 teams" are in audit narrative describing the correction, not live claims. Six screener categories sum to 219 in the doc and in the spec |
| 13c | Universe figures | Each re-sourced | 617 SGX (changelog) · 942 IDX (spec pagination example) · 99.99% IDX coverage (pricing page) · 594 coal companies · 37 S-REIT profiles (37 distinct slugs in `reits-llms.txt`) · 118 REIT sitemap URLs · 445 mining sitemap URLs |

---

## 3. Unverifiable until live

Unchanged in kind from the previous passes, and I want to be exact about which of these got
*stronger* this pass rather than resolved.

| Claim | Status |
| --- | --- |
| **Response shapes** | Still documented shapes, not observed ones. All 70 fixtures are spec examples |
| **Actual billing** | Still declared costs. **Materially stronger**: the Postman collection's billing table is a second, independent primary source that agrees with the spec and with `01-api-guide.md` line for line, including 404 = 1 credit and the screener's `?q=` 400 exception. Two sources agreeing is not the same as one observation |
| **Spend header names** | Still undocumented. `X-Credits-Charged` / `X-Credits-Remaining` remain **invented by the mock**. The Postman collection does not name them either. `capture.py`'s header sniffer is still the intended way to learn the real names, for 5 credits |
| **`is null`** | Newly moved into this bucket. Not attested anywhere; probably works |
| **`sti` as an `index_code`** | Listed in the spec's accordion for an otherwise IDX-only endpoint, and it is Singapore's index. Either genuinely supported or a spec artefact — one call settles it |
| **`include_query_values` semantics** | The parameter description says it returns "the interpreted year and country"; the official example returns the queried field values. The dossier already flags the conflict |
| **Empty results** | Newly documented, unobserved: the Postman collection states a filter matching nothing returns `200` with an empty collection **and still consumes credits**. The mock cannot reproduce it — fixtures are never empty |
| **Numeric rate limit** | Still unpublished. The 0.3 s sleep is documented; "~3 req/s" remains an inference, and the dossier already says so |
| **Anything behind a login** | Portal, playground, key management, Slack, Discord. Unchanged and out of scope by instruction |

---

## 4. New material

### 4.1 The public Postman collection — corroboration from a source never opened

`github.com/supertypeai/sectors_api_docs` → `recipes/postman-collection/json/Sectors_API.postman_collection.json`,
451 KB. Saved to [`evidence/spec/postman/Sectors_API.postman_collection.json`](../evidence/spec/postman/Sectors_API.postman_collection.json).

Diffed against `schema.json`: **70 endpoints in both, zero paths unique to either, zero
query-parameter differences across all 70.** That is independent corroboration of
`02-endpoint-reference.md` and `06-parameter-cheatsheet.md` from a source with no shared
generation path with the OpenAPI file.

Its description carries a **billing table** and an **empty-results rule**, quoted in full in
[`evidence/rechecks/pass3-live-recheck-2026-09-05.md`](../evidence/rechecks/pass3-live-recheck-2026-09-05.md).

### 4.2 Two hosts the closure argument missed

The dossier claims "**All five hosts** are now enumerated exhaustively rather than explored
opportunistically", reached by opening footer links. Certificate transparency
(`crt.sh?q=%.sectors.app`) returns **9 names**:

- **`admin.sectors.app`** — 200, "Sectors Admin", staff email/password login at `#/login`. Not participant-facing. No authentication attempted.
- **`insider.sectors.app`** — redirects to `mining.sectors.app`; the pre-2026-01-09 hostname, matching the changelog's "use `/mining` instead of `/insider`".
- plus `www.` and `api.`, and the five already known.

Neither new host is linked from any footer, and neither appears in any sitemap. The dossier's
own lesson — "sitemap enumeration is necessary but not sufficient" — extends one step further:
**footer enumeration is not sufficient either.** Certificate transparency is the enumeration
method that closes it.

The footer sweep itself re-ran clean: 71 internal paths, every one already captured or
classified; 8 external destinations, no further subdomain.

### 4.3 The `supertypeai` GitHub organisation — 74 public repositories

The dossier had captured one repo (`sectors-agent-skills`) and never looked at the org. It
contains, among 74 public repos pushed almost daily:

| Repo | Why it matters |
| --- | --- |
| `sectors-mcp` | **The MCP server source.** Settles the tool count (§1.9); also ships its own `schema.json` and OAuth implementation notes |
| `sectors_api_docs` | The docs site source, and where the Postman collection lives |
| `sectors_indices_company_list` | A constituent CSV per index — third independent source for the index codes |
| `coalresearch`, `singapore_reits_pipeline` | The data behind `mining.` and `reits.` |
| ~40 `sectors_*` pipelines | `sectors_idx_filing_pipeline`, `sectors_corporate_actions`, `sectors_idx_suspension`, `sectors_dividend_checker`, `sectors_stock_split_checker`, `sectors_get_closed_ipo`, `sectors_sgx_short_sell`, … — the **ingestion code for individual API datasets**. `11-data-provenance.md` describes provenance from marketing copy; this is the implementation |
| `sectors_chrome_extension`, `sectors_excel_addin` | Client surfaces with no API documentation |

File tree of `sectors-mcp` saved to [`evidence/sectors/sectors-mcp-repo-tree.txt`](../evidence/sectors/sectors-mcp-repo-tree.txt).
This is the largest genuinely new surface found this pass and it is **not** exhausted — I
enumerated the org and read three repos.

### 4.4 A query-language rule the dossier did not have

`llms-full.txt` changelog, 2026-01-09: "Added **parentheses forcing for arithmetic expression
on `order_by`** query parameter to avoid ambiguity with the negative sign." Arithmetic in
`order_by` must be parenthesised, because `-` is also the descending prefix. Added to
`03-screener-query-language.md`.

### 4.5 `status.supertype.ai`

Referenced twice in the OAuth-connector docs as where to check when authorization fails. Did
not resolve from here. Recorded as referenced-but-unreachable rather than asserted either way.

### 4.6 Generator and mock extensions

- `synth_extended.py`: **8 → 17 index series**, matching the spec's documented set. Any code iterating the mock's indices previously never saw `idxv30`, `sminfra18`, `sti`, `idxvesta28`.
- `extract_fixtures.py`: records `credit_default_items` per endpoint (11 carry one), so the mock's cost model is derived from the spec instead of hardcoded.
- `mock_server.py`: **a billed 404.** `--unknown ZZZZ,XXXX,NOTREAL` (default) makes a well-formed request naming a non-existent symbol return 404 **and charge 1 credit**, as the real API bills it. This is the only error path that costs money, and the mock previously could not exercise it at all.
- `capture.py`: `--base-url` / `SECTORS_BASE_URL`, and pagination for full-universe sweeps.

### 4.7 API areas still without a worked example

Re-checked against the recipe list. Six areas have no worked example anywhere in the
documentation: **suspensions, corporate actions, shareholders composition, free float, listing
performance, and the entire mining extension.** They do appear in the MCP tool table and in the
Postman collection — which is where the previous pass's "no recipe at all" was correctly
softened to "no *worked example*". That distinction survives this audit intact. The Postman
collection gives a runnable request for all 70 endpoints, so "runnable example" is now covered
everywhere; "worked example showing what to do with the data" is still absent for those six.

---

## 5. Bottom line

**How much of this corpus is evidence-backed rather than inferred, honestly.**

The **structural** layer is now very strongly evidenced, and stronger than it was before this
pass. The 70 endpoints, their parameters, enums, defaults, and declared costs, the 219 and 85
screener fields, and the response shapes are all machine-derived from `schema.json` and now
**independently corroborated by a Postman collection that agrees on all 70 endpoints and every
query parameter with zero differences**. The generated docs regenerate byte-identical. The
holiday calendar agrees across three places and recomputes to 239 trading days. `plan.json`
validates completely against the spec. This layer I would rely on.

The **behavioural** layer remains hypothesis. Not one live response has been observed. Every
response shape is a documented example; every credit cost is a declared cost, now declared
twice by the same organisation rather than confirmed once by the API. The spend headers the
mock emits are still invented. That gap is unchanged and cannot be closed from outside.

The **code** layer was the weakest part and had been over-certified. Two audits reported
`capture.py` and the mock as verified; this pass found six defects in them, including a mock
that mispriced three of four report endpoints, a `capture.py` that could not be pointed at the
mock at all, and a plan entry that budgeted 32 credits for a call that fetched one page. All
six are fixed and re-verified, but the lesson is that "exercised" in the earlier records meant
*sampled*, not *enumerated* — the IDX report was tested and the SGX one was not.

The **time-sensitive** layer is exactly as fragile as advertised. The matching board moved by
four teams in one day and Track 02 nearly doubled. Any number sourced from that board should be
re-counted before it is acted on.

**On the clean-sweep question.** A third audit finding nothing would have been the suspicious
result, and it did not happen: twelve corrections, four of them substantive (the 2× saving
overstatement, the undocumented-index-codes claim, the mock's report pricing, and `capture.py`'s
missing pagination). Three sections *did* come through clean and I want to say so plainly
rather than manufacture findings in them — the **screener field extraction** (219 and 85, exact
in both directions, with every per-category subtotal matching), the **holiday calendar** (22
dates, three-way identical, 239 days independently recomputed), and the **hackathon rules**
(re-read in full against the live page, unchanged). Those three are the best-verified material
in the dossier.

The single highest-value next step is still unchanged from what the README says: claim the
credits, run `capture.py --tier 0`, and reconcile the declared cost model against the real
ledger and the real header names. Everything in §3 turns on that one 5-credit call. It can now
be rehearsed end-to-end against the mock first, which it could not be before this pass.
