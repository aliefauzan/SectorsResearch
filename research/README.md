# Sectors Hackathon 2026 — Research Dossier

Everything found about the **Sectors Hackathon 2026** and the **Sectors platform / Financial
API**, organized so you can act on it.

Researched 4 September 2026. Primary sources: `hackathon.sectors.app`, `sectors.app`,
`docs.sectors.app`, and the official OpenAPI spec. Raw captures are preserved in
[`evidence/`](evidence/) so every claim here is traceable.

---

## Start here

**If you have five minutes**, read this page and
[`docs/hackathon/00-overview.md`](docs/hackathon/00-overview.md).

**If you are setting up to run anything**, read [`SETUP.md`](../SETUP.md) first: one
git-ignored `.env` at the repository root holds `SECTORS_API_KEY`, `SECTORS_BASE_URL` and
`SECTORS_BUDGET`, and [`harness/src/sectors_env.py`](harness/src/sectors_env.py) loads it
for every script here. No script in this repository reads a key from anywhere else, and none
writes one to disk.

**The four facts that shape every decision:**

1. **Deadlines.** Registration closes **22 Sep 2026, 23:59 WIB**. Submissions close **30 Sep 2026, 23:59 WIB**. As of 4 September: 18 days to register, 26 to submit.
2. **Scoring.** Real-world usability 40%, video & storytelling 30%, technical depth 30%. **Seventy percent is problem framing and communication**, not engineering.
3. **The one hard constraint.** Sectors MCP or REST API must be a *core* data source — remove it and the product must stop working. Automated trade execution is banned in every track.
4. **Credits.** 1,000 per team, no top-up. That is one fifth of a single month of an Insider plan. Develop against the [local mock](harness/), not the live API.
5. **Track 02 is the least crowded**, but by less than it was. Recounted live 5 Sep and re-counted independently in pass 4: of **48** teams on the public matching board, 15 chose Track 01, 12 chose Track 03, **7 chose Track 02**, 14 have not chosen. On 4 Sep it was 44 and 16/11/4 — the board moved by four teams in a day and three of them picked Track 02. Still the thinnest field and still the most objective qualifying test; **re-count it near the 22 September close.** Note the board is a lower bound on the field: the hackathon Slack reports **105 members** against 52 people on the board.
6. **The obvious project in each track is already a published Supertype tutorial.** A 7am scheduled top-movers digest to Discord, a natural-language stock chatbot, and a multi-agent fundamental/technical/news analyst are all recipes on docs.sectors.app. See [`already-published.md`](plan/already-published.md).
7. **Sectors already ships an alerting product.** Sectors Workflow does entity → trigger → WhatsApp/Email/Slack/Telegram/Sheets with ~60 templates. A bare Track 02 "alert bot" reimplements it. See [`competitive-landscape.md`](plan/competitive-landscape.md).
8. **The screener returns only `symbol` and `company_name`.** You can filter on 219 fields but the response doesn't contain them — pass `include_query_values=true` and name your metrics in `where`. This shapes your whole data architecture; see [`08-hidden-data.md`](docs/api/08-hidden-data.md).

---

## Map of this folder

```
research/
  docs/hackathon/     the competition — rules, tracks, checklist
  docs/api/           the Sectors API in depth — 16 reference docs
  harness/            the offline harness
    src/              the 10 scripts — run from harness/ as `python3 src/<name>.py`
    plans/            the capture plans
    fixtures/         spec examples, split idx/ sgx/ klse/ mining/
    recorded/         real payloads, flat and keyed by _manifest.json
    synth/            generated universe, split market/ flow/ company/ mining/
  plan/               what to build — ideas, competitive landscape, what is already published
    tunanetra/        deep research: non-visual access to IDX stock research
    pump-and-dump/    deep research: pre-trade firewall for social-media stock tips
  evidence/           provenance
    spec/             schema.json, llms.txt, llms-full.txt, postman/
    hackathon/        captures of the hackathon site
    sectors/          captures of the Sectors product, docs and agent skills
    subdomains/       mining/reits sweeps and footer crawls
    rechecks/         the live re-check notes behind the audit reports
    usage-log/        portal CSV exports — what the API actually charged
  audit/              the six verification passes and the prompts that drove them
  tools/              generators for the two generated docs in docs/api/
```

### `docs/hackathon/` — the competition

| Doc | What's in it |
| --- | --- |
| [`00-overview.md`](docs/hackathon/00-overview.md) | What the hackathon is, dates, prizes, judging, teams, eligibility, official channels, partners |
| [`01-rules.md`](docs/hackathon/01-rules.md) | All 14 rule sections in full, plus **the ten rules that most often cost teams the prize** |
| [`02-tracks.md`](docs/hackathon/02-tracks.md) | Each track's qualifying test, what does and doesn't qualify, example directions, and how to choose between them |
| [`03-submission-checklist.md`](docs/hackathon/03-submission-checklist.md) | Phase-by-phase checklist from onboarding to post-submission, plus a minute-by-minute plan for the 3-minute judging video |

### `docs/api/` — the data

| Doc | What's in it |
| --- | --- |
| [`00-what-is-sectors.md`](docs/api/00-what-is-sectors.md) | The product, market coverage, all plans and pricing, every surface, documentation map, and the recipes worth reading before you design |
| [`01-api-guide.md`](docs/api/01-api-guide.md) | Auth, base URL, the v1 sunset, **how credit billing actually works**, error codes, hard limits, ticker/slug conventions, pagination, freshness, and nine gotchas |
| [`02-endpoint-reference.md`](docs/api/02-endpoint-reference.md) | **All 70 endpoints** — summary tables by market, then full per-endpoint detail with every parameter and credit cost. Generated from the OpenAPI spec |
| [`03-screener-query-language.md`](docs/api/03-screener-query-language.md) | The screener in depth: both query modes, full syntax, **all 219 queryable fields in six categories**, twelve worked query patterns, and how to build a defensible composite score |
| [`04-mcp-and-ai-agents.md`](docs/api/04-mcp-and-ai-agents.md) | MCP server setup for every client, the full 66-tool catalogue (65 documented), agent skills, OAuth connectors — **and the Track 01 trap** |
| [`05-credit-budget.md`](docs/api/05-credit-budget.md) | What everything costs, five rules that save the most, sample budgets per track, and a metered caching client |
| [`06-parameter-cheatsheet.md`](docs/api/06-parameter-cheatsheet.md) | Every enum value, default, minimum and maximum in the API — including **four defaults that silently change your results** — plus what's known about rate limits |
| [`07-response-shapes.md`](docs/api/07-response-shapes.md) | Data dictionary: the envelope and row keys each of the 70 endpoints returns. The API is **not** uniform — read this before writing a parser |
| [`15-fetch-strategy.md`](docs/api/15-fetch-strategy.md) | **The spend plan.** 87 calls in 5 tiers for **176 of 1,000 credits** — against 297 if every parameter defaulted — and the record-once-replay-forever loop |
| [`14-flare-community-and-engineering.md`](docs/api/14-flare-community-and-engineering.md) | **FLARE** — the missing definitions for every banking field in the API, with the OJK/Basel III citations · the referral-to-API-credits program · **Stories**, which show what the organizers consider good derived insight · and their search-architecture write-up as engineering calibration |
| [`13-subdomains-and-terms.md`](docs/api/13-subdomains-and-terms.md) | **Two entire products on subdomains the sitemap never showed** — `mining.sectors.app` (594 coal companies, unlisted firms, the HBA benchmark) and `reits.sectors.app` (37 S-REITs, **no API at all**) — plus the **Terms of Service commercial-use restriction** |
| [`12-trading-calendar-and-releases.md`](docs/api/12-trading-calendar-and-releases.md) | **IDX has 22 market holidays in 2026 and no endpoint exposes them** — a scheduled job that ignores them produces blank days. Plus Sectors' 2026 release timeline and which product features have no API |
| [`11-data-provenance.md`](docs/api/11-data-provenance.md) | Where the numbers come from — PDF/XBRL extraction, human-in-the-loop standardization, IDX-IC and OJK/Basel III standards, self-healing corrections, and the datasets that **exist nowhere else** |
| [`10-domain-pitfalls.md`](docs/api/10-domain-pitfalls.md) | Mistakes the organizers themselves warn about in their published recipes — the **zero-sum trap** that flattens any broker-flow signal, suspended stocks returning all-zero rows, and the confirmation pattern they use |
| [`09-sgx-klse-coverage.md`](docs/api/09-sgx-klse-coverage.md) | SGX's own 85 screener fields, what SGX and KLSE **cannot** do, and three SGX data traps — including duplicate sector labels that silently drop results |
| [`08-hidden-data.md`](docs/api/08-hidden-data.md) | **What's actually inside the payloads** — field-level findings that appear in no endpoint description: named institutional flow, whale investors, conglomerate groups, a monthly local/foreign ownership panel, pre-classified news, full OHLC, complete IPO book-building records, and the mining ownership graph |

### `harness/` — simulating Sectors offline

| File | What it is |
| --- | --- |
| [`README.md`](harness/README.md) | Both approaches, when to use which, the recommended workflow, and the one-env-var client switch |
| `extract_fixtures.py` | Pulls the official example response for all 70 endpoints out of the OpenAPI spec |
| `mock_server.py` | Local `api.sectors.app` — serves every endpoint, meters credits, emulates 401/402/410/429/503, `GET /__usage` |
| `synth_universe.py` | Generates an arbitrarily large synthetic IDX universe in Sectors' exact field naming |
| `plan.json` | 87 live calls in 5 tiers, every parameter constrained — 176 credits total |
| `capture.py` | Runs the plan once: idempotent, budget-capped, rate-limited, ledgered. Records raw responses to `recorded/` |
| `synth_extended.py` | Adds the datasets the first generator misses — **all 19 mining endpoints**, bank Loan-at-Risk components, suspensions, corporate actions, shareholder panels, insider filings, segments with key customers, quarterly financials, free float, the eight real index codes, and the **real IDX holiday calendar**. Preserves the zero-sum broker property so the trap is reproducible offline |
| `fixtures/` | 70 fixtures + `_index.json`, already generated |
| `synth/` | A sample generated universe (120 companies × 90 days) |

### `plan/` — what to actually build

| Doc | What's in it |
| --- | --- |
| [`what-we-can-build.md`](plan/what-we-can-build.md) | The data nobody else has, then **thirteen concrete project ideas** mapped to tracks, with the exact endpoints and credit cost of each — and a recommendation if you have to pick one |
| [`competitive-landscape.md`](plan/competitive-landscape.md) | What the other 48 public teams are doing: **track distribution, team sizes, which skills the field is under-valuing** — plus **Sectors Workflow**, the shipping product that competes with Track 02 |
| [`already-published.md`](plan/already-published.md) | **The organizers have already published working tutorials for the most obvious project in each track.** What's taken, the test to apply to your pitch, and the six areas of the API with no recipe at all |
| [`idea-shortlist-2026-09-08.md`](plan/idea-shortlist-2026-09-08.md) | The five ideas actually under consideration, each judged against the four gates a judge walks, plus the ranking and the TimesFM appendix |
| [`tunanetra/`](plan/tunanetra/deep-research.md) | Deep research on **non-visual access to IDX stock research** — the blind and low-vision investor who cannot read the charts. [`ringkas.md`](plan/tunanetra/ringkas.md) is the plain-language companion; [`diagrams/alur.png`](plan/tunanetra/diagrams/alur.png) is the flow |
| [`pump-and-dump/`](plan/pump-and-dump/deep-research.md) | Deep research on the **pre-trade firewall for social-media stock tips**. [`ringkas.md`](plan/pump-and-dump/ringkas.md) is the plain-language companion, [`agen-risiko-belajar-mandiri.md`](plan/pump-and-dump/agen-risiko-belajar-mandiri.md) the self-learning orchestration layer, [`diagrams/alur.png`](plan/pump-and-dump/diagrams/alur.png) the flow |

Seventeen ideas total across the two, four of them built on data found only by reading the
raw payloads.

### `evidence/` — provenance

Verbatim captures: every hackathon page, the Sectors home/pricing/API pages, the complete
`schema.json` (OpenAPI 3.0.3, 70 endpoints, 929 KB) and `llms-full.txt` (the entire docs site
as one 820 KB text file). Both of the latter are fetchable without auth and are the fastest
way to give a coding agent complete knowledge of this API.

### `audit/` — how far to trust this

Six verification passes, each auditing the one before it.
[`audit/README.md`](audit/README.md) gives the order and states what supersedes what — in
short, [`audit/VERIFICATION-LIVE.md`](audit/VERIFICATION-LIVE.md) is the only pass that called
the API and wins every behavioural disagreement with the five documentation-only passes.

### `tools/` — the doc generators

`gen_endpoint_ref.py` and `gen_response_shapes.py` produce
[`docs/api/02-endpoint-reference.md`](docs/api/02-endpoint-reference.md) and
[`docs/api/07-response-shapes.md`](docs/api/07-response-shapes.md) from `evidence/spec/schema.json`
and `harness/fixtures/`. **Edit the generator, not the markdown.** Both run with `research/` as
the working directory.

---

## The three-minute version

**The hackathon.** Online, Indonesia-wide, run by Supertype with Sectors and Algoritma.
IDR 50,000,000 pool (30M cash + 20M credits). Teams of 1–4. Three tracks: AI Agents (LLM
mandatory), Automation & Workflows (must run unattended on a schedule/trigger), Market
Intelligence (must produce derived insight, not a re-render). Judging is fully asynchronous
1–8 Oct from your repo and videos — **there is no live presentation**. Winners 9 Oct.

**The platform.** Sectors is an API-first financial data platform for IDX (99.99% of ~950
companies), SGX (617 companies), KLSE (sector-level), plus a 19-endpoint Indonesian mining
extension covering private and unlisted companies. The API is 70 GET endpoints at
`https://api.sectors.app/v2`, gated behind the Insider plan. There is also a cloud-hosted MCP
server with 66 tools (65 documented).

**The differentiated data:** per-broker daily flow with foreign/domestic and
retail/institutional cohorts (bandarmology), the mining extension, revenue/cost segments,
monthly shareholder composition, suspensions with official reasons, insider filings, and a
219-field screener that costs 1 credit per query and supports arithmetic and year/quarter
bracket notation.

**Simulating it.** Yes — two ways. The OpenAPI spec ships a real example response for every
one of the 70 endpoints, so `mock_server.py` serves an exact-shape local clone with a working
credit meter. For volume, `synth_universe.py` generates hundreds of companies and years of
price, broker and flow data in the same field naming. Develop against those; spend live
credits only on verification and the demo.

---

## Immediate next actions

| ☐ | Action | Deadline |
| --- | --- | --- |
| ☐ | Every member creates a Sectors account and **completes onboarding** at [sectors.app](https://sectors.app) | Before any project code |
| ☐ | Finalize the roster — claiming credits locks it permanently | Before claiming |
| ☐ | Register at [`/portal/team`](https://hackathon.sectors.app/portal/team) | **22 Sep 2026** |
| ☐ | Claim the 1,000 credits once everyone has onboarded | After onboarding |
| ☐ | Join the [Slack](https://join.slack.com/t/sectorshackathon/shared_invite/zt-47a8tdhhz-FgREdKQ46lUETWErcIwNcQ) — `#discussion`, `#support` | Now |
| ☐ | Create the repo (must be **on or after 19 Aug 2026**), `.env` gitignored from commit #1 | Before building |
| ☐ | Start the mock server and build the base-URL switch | Day one |
| ☐ | **If Track 02:** stand up the scheduler immediately, even against a stub, so you accumulate real unattended-run history for the video | Day one |
| ☐ | Draft the one-sentence problem statement **before** writing code — it is 40% of the score | Day one |

---

## Coverage notes

**What was captured.** The hackathon site has exactly seven public pages — `/`, `/rules`,
the three `/tracks/*` pages, `/matching`, and the `/portal/*` routes. All seven were captured;
there is no FAQ, prizes, judges, timeline or sponsor page (all 404). Everything under
`/portal` is gated behind "Checking your Sectors Account…" and needs a registered login.

**Known gaps, and why.**

| Gap | Status |
| --- | --- |
| Bahasa Indonesia rules | **Closed in pass 4: they are not on the website.** The client bundle ships exactly five routes (`/`, `/rules`, `/tracks/*`, `/matching`, `/portal*`); 20 candidate Indonesian paths 404; `?lang=id` and `Accept-Language: id-ID` are both ignored; `<html lang="en">` with no `hreflang`. The rules page still says they exist, so they are distributed some other way — Slack or a document |
| Prize breakdown by placement or track | Not published anywhere — only the IDR 50M total split (30M cash / 20M credits) |
| Judge identities | Stated only as "the internal Sectors and Supertype judging team" |
| Numeric rate limit | Never published. The docs' own recipe implies ~3 req/sec is safe — see [`06-parameter-cheatsheet.md`](docs/api/06-parameter-cheatsheet.md) |
| Live Slack discussion | Requires joining; the only place organizers answer track-boundary questions. **105 members as of 5 Sep, and the shared invite link expires ~20 September — before registration closes on the 22nd** |
| Portal contents (team page, submit form) | Login-gated |
| ~~Full IDX index code list~~ | **Closed in pass 3.** No *helper endpoint* enumerates them, but the `/v2/index-daily/{index_code}/` description carries an accordion listing all **17**, and `supertypeai/sectors_indices_company_list` publishes a constituent CSV for 15. See [`06-parameter-cheatsheet.md`](docs/api/06-parameter-cheatsheet.md) |

**Two sources worth re-checking before locking a track:** the Slack `#discussion` channel,
and the matching board near the 22 September registration close for the final track split.

### ⚠️ What this dossier does NOT have

Read this before trusting any of it operationally. The honest ledger:

**1. Not a single live API call was ever made.** There is no API key in this project. Every
statement about endpoint behaviour comes from the **OpenAPI spec and its documented examples**,
not from observed responses. The 70 fixtures are spec examples. So:

- Response shapes are *documented* shapes. Real payloads may differ, carry extra fields, or null out differently.
- The credit costs are *declared* costs from endpoint descriptions. Actual billing is unverified.
- The `X-Credits-Charged` / `X-Credits-Remaining` headers the mock emits are **invented** — the spec does not document spend headers. Confirm the real header names on your first live call.
- Rate limits, latency, pagination edge cases, and error bodies beyond the three documented examples are all unobserved.

**Everything in this dossier should be treated as a well-sourced hypothesis until your first
live call confirms it.**

*Update, 5 September 2026:* a signed-in session on a **free** account confirmed that **the API
is genuinely Insider-gated** — API Key Management reports *"Please upgrade your subscription to
access Sectors API"* and no key can be created. So a live call is not possible until the
hackathon credits are claimed. That session did verify the **Deterministic Query Builder**,
which corrected two errors in this dossier (see
[`03-screener-query-language.md`](docs/api/03-screener-query-language.md)) — but the
Playground itself runs in **Demo Mode with mock data** below the Insider tier, so it is not a
substitute for live responses either.

**2. Everything behind a login is missing.** The hackathon portal (team page, submission form,
credit claiming), the API Playground, API Key Management, Sectors AI Chat, the screener UI,
watchlists, and Sectors Workflow's actual builder. All were confirmed to exist and were
classified, none were used.

**3. The private channels are unread.** The hackathon Slack (`#discussion`, `#support`) is
where organizers answer track-boundary questions and post rule clarifications — arguably the
highest-value information source for this competition, and it needs an account. The Sectors
Discord likewise.

**4. Content read at headline level only.** ~2,000 per-ticker product pages on sectors.app,
~400 mining company pages, 37 REIT profiles, 37 REIT glossary entries, the Stories articles
(headlines and summaries only), the IDX Weekly Digest, and FLARE part 2 (NII/NIM/IRR) were
enumerated and classified but not read in full.

**5. 21 of the 39 documentation recipes are unread** — the visualization (R animated plots),
no-code (Excel, Sheets, Looker), and OAuth-connector guides. They were judged out of scope
because their API content is a subset of what is already captured. That judgement is
reasonable but untested.

**6. Simply not published anywhere.** The Bahasa Indonesia rules, the prize breakdown by
placement or track, judge identities, the numeric rate limit, Sectors' internal data
dictionary, and past workshop recordings (Insider-gated).

**What this dossier *is* good for:** knowing what exists, what it costs, what shape it takes,
what the rules require, what the competition is doing, and what has already been built. It is
a map, not the territory.

**The single highest-value next step is not another research pass** — it is registering,
claiming the credits, making one live call per endpoint family, and diffing the real responses
against [`07-response-shapes.md`](docs/api/07-response-shapes.md).

### Verification audit — 5 September 2026

Every claim in this dossier was re-checked against the saved raw sources. Method and result:

| Check | Method | Result |
| --- | --- | --- |
| Endpoint paths | Every `/v2/...` path cited in any doc matched against `schema.json` | **78/78 resolve** (6 apparent misses were documentation URLs, not API paths) |
| Numeric claims | 21 assertions re-derived from the spec and fixtures | **21/21 pass** |
| Hackathon facts | 21 dates, figures and rules matched against the raw rules/tracks captures | **21/21 pass** |
| Verbatim quotes | Every `> "..."` block searched in the raw corpus | **19/19 now trace to saved evidence** (4 required capturing the source; 1 was a misquote, corrected) |
| Browser-derived claims | 28 figures from live pages | **28/28** after capturing 2 further evidence files |
| Enum values | `sections`, `periods`, `cohort`, `license_type`, `extension` re-read from the spec | match |
| Code behaviour | Mock server's documented costs and status codes exercised live | 401/410/402 correct; report 8→1 and top-changes 10 confirmed |
| Generators | Full rebuild from empty, twice | deterministic, identical hashes |
| Holiday calendar | Set in `synth_extended.py` and in doc 12 vs the captured calendar | **all three identical, 22 dates** |

**Errors found and fixed in this audit:**

1. **Matching-board counts were wrong.** Reported 46 teams and 17/11/5; the true figures are **44 teams, 16/11/4**. The earlier count included track labels from the separate *participant profiles* section. The conclusion strengthens — Track 02 is a quarter of Track 01, not a third.
2. **MCP mining tool count** said 18; the docs list **19**.
3. **A misquote.** "Three independent signals is much stronger evidence…" was presented as verbatim; the source sentence begins "…the convergence of three independent signals…". Now quoted in full.
4. **Four quotes had no saved provenance** — they came from live browser sessions never written to `evidence/`. Evidence captured in [`evidence/sectors/authenticated-session-captures.md`](evidence/sectors/authenticated-session-captures.md) and [`evidence/sectors/calendar-releases-flare-captures.md`](evidence/sectors/calendar-releases-flare-captures.md).

Earlier passes had already caught and fixed: two wrong credit costs (corporate actions and
shareholders composition are 1 credit, not 2), a wrong 2-credit endpoint list, a premature
closure claim that missed two subdomains, and — twice — the `is null` / `is not null` operator.

#### Second audit pass — same day

Re-run deeper, covering what the first pass sampled rather than enumerated:

| Check | Result |
| --- | --- |
| Regenerate both generated docs from `schema.json` and diff | **byte-identical** — reproducible from source |
| All 45 schema parameter enums vs the cheat sheet | no invented values |
| `plan.json`: every path resolves, every param exists, flat costs match the spec | **87/87 paths, 0 invalid params, 0 cost mismatches** |
| IDX screener doc tables vs extracted source | **219/219 exact** (7 extras are the query-parameter table, correctly) |
| SGX screener doc tables vs extracted source | **85/85 exact** |
| `synth_extended.py` docstring vs files actually produced | all 16 outputs present |
| `capture.py` behaviour, driven against the local mock | idempotency, budget cap, resume, 404-recorded-once, ledger, cost-header detection — **all confirmed** |
| Build-plan per-idea cost claims vs spec costs | 9/9 pass; one estimate corrected (idea 3.1 is 4 credits/ticker, not ~3) |
| Fetch-strategy savings arithmetic | 95 saved, 824 remaining — both check out · **superseded in pass 4: the saving is 121 and the default run 297** |
| Cross-document numeric consistency | one stale "46 teams" found and fixed |

**Further corrections made:**

5. **A missed instance of the wrong team count** — one "46 teams" survived the first fix.
6. **Idea 3.1's cost estimate** said ~3 credits/ticker; with the `daily` call it is 4.
7. **"~3 requests/second" was phrased as documented.** What is documented is a 0.3 s sleep; the rate is my inference. Re-worded in all three places it appears.

**What the audit cannot certify:** anything requiring a live API call. See the gap ledger
above. Declared credit costs, response shapes and rate limits remain unverified against the
running API.

### Third audit pass — 5 September 2026, adversarial

Run on the assumption that the corpus contains hallucinations and that **neither prior audit
record is evidence**. *(Pass 4 re-derived all twelve: **ten stand**, §1.1 is wrong — the correct figure is 297, not 271 — and §1.12 was incomplete, having verified only the paging happy path. §1.8 was not re-checked. See the fourth-pass section below.)* Every check re-derived from a primary source. No live `/v2/*` call, no
account, no form. Full report: [`VERIFICATION-PASS-3.md`](audit/VERIFICATION-PASS-3.md).

| Check | Method | Result |
| --- | --- | --- |
| Generated docs | Both scripts re-run, diffed | **byte-identical** |
| Endpoint count | Operations counted in the spec | **70 GET, 0 non-GET**; 34/12/19/5 by market |
| Prose ↔ spec paths | All 133 `/v2/…` strings resolved | 127 resolve; the 6 others are docs URLs |
| Credit costs | Cost sentence extracted from all 70, diffed against all prose | **1 error** — shareholders composition still said 2 |
| Non-flat formulas + worked examples | Re-computed | all correct; **the 176-vs-defaults ratio was wrong** (271, not ~528) · **271 was itself wrong — pass 4 derives 297** |
| Screener fields | Re-extracted from the spec | **IDX 219/219, SGX 85/85 exact**, all 6 category subtotals match |
| Enums & defaults | All 45 enum params machine-diffed both ways | 30/31 claims exact; **1 invented** (`resources-reserves` index takes no params) |
| Index codes | Spec accordion vs docs | **17 documented, dossier had 8 + 5 guesses and called the set undocumented** |
| Auth | Spec `securitySchemes` + docs | REST raw key / MCP `Bearer` — both correct |
| Query syntax | Each construct traced | 3 rest on the query-builder capture; **`is null` rests on nothing** |
| Quotes | 165 quoted strings grepped | **3 drifted, 4 unsourced** (one names a page that does not exist) |
| Hackathon rules | Full live re-read | **unchanged since capture** |
| Matching board | Recounted live, twice | **48 / 15-7-12 — moved from 44 / 16-4-11** |
| `plan.json` | Paths, params, enums, ranges, costs | **87/87 clean** |
| Generators | Run from empty, twice | deterministic, all 21 promised outputs |
| Holiday calendar | 3-way diff + recompute | **22 dates identical, 239 trading days**, all 8 month counts |
| Mock server | Every cost family exercised | **2 pricing bugs** — subsector/SGX/KLSE reports all billed 8; SGX `?q=` billed 1 |
| `capture.py` | Driven against the mock | idempotency/cap/resume/404/ledger ✓; **2 defects** — no base-URL override, no pagination |
| Internal links | 43 files | **zero broken** |

**Twelve corrections**, four substantive: the 2× overstated saving, the "undocumented" index
codes, the mock's report pricing, and a plan entry budgeting 32 credits for a call that fetched
one page. All fixed and re-verified.

**New primary sources**, none previously opened: the **public Postman collection** (agrees with
the spec on all 70 endpoints and every query parameter, zero differences, and carries its own
billing table); the **`supertypeai` GitHub org**, 74 public repos including the MCP server
source and ~40 dataset ingestion pipelines; **two further hosts** — `admin.sectors.app` and
`insider.sectors.app` — found by certificate transparency, linked from no footer and no sitemap.

> The closure argument below says footer enumeration is what sitemap enumeration missed.
> Pass 3 extends the same lesson one step: **footer enumeration missed two hosts too.**
> Certificate transparency is what closes host enumeration.

### Fourth audit pass — 5 September 2026, adversarial, targeting pass 3

Run on the assumption that **pass 3's report is a claim, not evidence**. Each of its twelve
corrections re-derived from a primary source, then every standing check re-run independently.
No live `/v2/*` call, no account, no form. Full report:
[`VERIFICATION-PASS-4.md`](audit/VERIFICATION-PASS-4.md); live evidence:
[`evidence/rechecks/pass4-live-recheck-2026-09-05.md`](evidence/rechecks/pass4-live-recheck-2026-09-05.md).

| Check | Method | Result |
| --- | --- | --- |
| **Pass 3's 271-credit claim** | `plan.json` re-costed against the spec's defaults | **FAIL — 297, not 271.** Its table counted `?q=` as a "default" (it has none) and missed `limit`'s 20-vs-30 effect on the two paginated sweeps. Saving is 121, not 95. The `financials/quarterly` exclusion **is** honest — `n_quarters` has no documented default |
| **Pass 3's 17 index codes** | Spec accordion + `llms-full.txt` | **PASS**, verbatim. Its `sti` caution was right on its evidence — and Phase 2 **resolves it**: the ingestion pipeline fetches `^STI` into the very table the endpoint reads. A candidate 18th code, `klse`, is in that registry and not in the spec |
| **Pass 3's mock cost model** | **Every** per-item endpoint exercised, plus constrained variants | **PASS** — 8/6/4/4/10/5/5 and every constrained combination correct. Three undocumented divergences found and written down (enum values billed instead of 400-free, reports not sliced by `sections`, free-float flat-billed) |
| **Pass 3's `capture.py` pagination** | Driven against the mock, happy path **and failure path** | Mechanism **PASS** (32 calls, merged, idempotent; full plan 149 calls / ledger 176). **Two defects in the failure path** — a mid-sweep stop billed 15 credits and logged 0, discarding every page it paid for |
| **Pass 3's billed-404** | Five unknown slugs, plus real symbols | **PASS** — charges 1, body is a verbatim spec string, real symbols still 200 |
| **Matching board** | Recounted live, three independent methods | **48 / 15-7-12-14 confirmed.** But the board's *text* moved: two claims falsified (see below) |
| Generated docs · endpoint census | Both scripts re-run; operations counted | **byte-identical**; 70 GET, 0 non-GET; every spec template referenced, every prose path resolving |
| Declared costs · worked examples | All 70 cost sentences extracted and machine-diffed; every example recomputed | 49 flat-1, 4 flat-2, 17 non-flat; **zero prose mismatches**; all arithmetic correct |
| Screener fields | Re-extracted both directions | **IDX 219/219, SGX 85/85 exact**, all ten category subtotals, plus the 20/10 SGX coverage-marker split |
| Enums · defaults | 239 enum values and 46 defaults machine-diffed both ways | **2 errors** — one invented value (`Sand` on `/v2/news/`), one wrong endpoint attribution (`origin`/`cohort` on broker-activity top) |
| Quotes | 106 quotations outside code fences, normalised and grepped | **4 failures**, including **a fabricated sentence attributed as "their framing, explicitly"** |
| Hackathon rules | Full live re-read, sentence-hash diff | **Unchanged** — 7 differences, all markdown-vs-innerText line joins |
| Docs drift | `schema.json`, `llms.txt`, `llms-full.txt` re-fetched | **All three byte-identical to the captures.** Release page unchanged |
| `plan.json` · generators · holiday calendar · links | Re-run from scratch | **87/87 clean · deterministic and byte-identical to committed · 22 dates and 239 days · zero broken links** |

**Fourteen corrections, six substantive:** the 297-vs-271 arithmetic; a fabricated provenance
quotation; two falsified competitive claims (**two teams now recruit video/motion skill, and a
team has published a bandarmology brief**); and two `capture.py` failure-path defects, one of
which — any unbilled failure permanently deleting a call from the plan — predates pass 3 and
survived three audits that each certified that file.

**New material:** `sectors-mcp` ships its **own `schema.json`** which agrees with the committed
one on all 70 endpoints, every parameter, every cost sentence and every response example, with
zero differences — a third independent source. Fifteen `supertypeai` ingestion repos read,
giving **real provenance and per-dataset refresh cadences** in place of marketing copy.
`status.supertype.ai` **does not exist** (NXDOMAIN on two public resolvers). The Bahasa
Indonesia rules are **definitively not on the website**. Host enumeration is **uncloseable**:
`*.sectors.app` is wildcard DNS *and* a wildcard certificate, so CT corroborates but cannot
prove completeness. The Slack invite **expires around 20 September**, before registration
closes.


### Live capture — 6 September 2026, the first pass that called the API

Five audits verified this corpus against documentation. This one called it. **66 of 70
documented paths returned 200; the other four are duplicate spec entries that cannot be called.
214 credits of the 1,000 grant. 116 payloads recorded, and the mock replays all of them.** Full
report: [`VERIFICATION-LIVE.md`](audit/VERIFICATION-LIVE.md); machine-generated evidence:
[`evidence/rechecks/live-capture-2026-09-06.md`](evidence/rechecks/live-capture-2026-09-06.md).

| Check | Method | Result |
| --- | --- | --- |
| Endpoint coverage | Every documented path called with identifiers read from prior responses | **66/66 callable endpoints returned 200** |
| Spend headers | 116 responses scanned for `credit\|quota\|rate.?limit\|usage\|balance` | **None exist.** The mock's `X-Credits-Charged` is fiction; a client cannot read its own spend |
| The 70-endpoint count | Four bare `report/` roots called | **The surface is 66 distinct endpoints.** The four extras declare a path parameter with no template and return a free 400 |
| Response shapes | Live payload diffed field-by-field against the spec example, all 66 | Agree everywhere but one: **quarterly financials rename a field by sector** — `capital_expenditure` for non-banks, `realized_capital_goods_investment` for banks |
| `plan.json` | Run end to end | **174 of 176 declared credits**; two mining calls were missing required parameters, and the `listing-performance` basket 404'd on every blue chip (4 billed credits) — all three corrected |
| Rate limit | Bisected across four spacings, free and billed paths | **25 billed requests per rolling ~30 s.** Spacing is not counted — 25 back-to-back and 25 a second apart both stop on the 26th. Free 400s are exempt; no `Retry-After`; polling a 429 extends the lockout. `capture.py` now self-throttles: 28 back-to-back billed calls, zero 429s |
| Transport | First five calls | **Cloudflare 403 "error code: 1010"** on the stdlib user agent — unbilled, and fatal to any naive client until a browser `User-Agent` is set |
| Mining detail coverage | `has_financials` filter | **9 companies of 366** carry financials/performance/sales-destination records |
| Mock replay | Every recording served | `X-Mock-Source: recording` on all 116 |

**Six corrections to the corpus**, three of them things no amount of documentation reading
would have found: the absent spend headers, the sector-dependent field rename, and the
Cloudflare user-agent block.

Every failing call was then root-caused and either fixed or proven unfixable, and the mock was
audited against the result. **All 127 recordings replay byte-identical, and all 66 callable
endpoints are now served from real data — zero spec-example fallbacks.** Eleven divergences
from live behaviour were closed, including four that would have shaped client code wrongly:
a missing key is **403, not 401**; a non-GET is **405**; an unrouted path returns a
`{"details","urls"}` body with no `error` key; and an unknown identifier now 404s and bills
instead of quietly returning BBCA's fixture. `harness/src/verify_mock.py` re-runs the whole
audit — replay, error, method and header parity — for zero credits.

Two long-open questions closed by probe, at a cost of 1 credit: **`sti` resolves** (200), and
**`klse` is not an index code** (free 400) — the set is the documented 17. And the four bare
`report/` roots were probed eleven ways (`?symbol=`, `?ticker=`, `?q=`, bare, …): every form
returns the same free 400. The identifier must be a path segment; they are spec artefacts, not
endpoints.

**Cost model settled against the portal's own usage log** (408 rows, committed at
[`evidence/usage-log/`](evidence/usage-log/)): **377 charged, 377 modelled — exact.** Every
non-flat claim confirmed by a charged row (free-float 10, defaulted report 8, defaulted
top-changes 10, `?q=` 3, the four flat-2 endpoints). **429s and 403s never appear in the log**,
confirming from the billing side that they cost nothing. The reconciliation also caught two
errors in this harness that had cancelled each other out — a plan entry under-costing
`broker-activity/{code}/top/` by 1, and `capture.py` billing an unrouted 404 that is free —
plus a third in the mock, which billed free-float 1 where the API charges 10. All fixed;
`harness/src/reconcile_usage.py` re-runs the check.

**Census, three independent sources:** the spec declares 70 operations (66 callable); the
documentation site names 67 `GET /v2/…` literals, all inside the spec; the live MCP server
exposes 66 tools that map 1:1 onto the 66 callable endpoints. **No endpoint is missing.**

### Research completion criteria

This dossier is considered complete against the following checklist. Every item is verified,
not asserted — the verification command is given where one exists.

| # | Criterion | Status |
| --- | --- | --- |
| 1 | Every public page on hackathon.sectors.app captured | ✅ 7 of 7 (`/`, `/rules`, 3× `/tracks/*`, `/matching`, `/portal/*` — portal is login-gated) |
| 2 | All other public paths probed for missed pages | ✅ 24 candidate paths tested; 17 return 404 |
| 3 | Every one of the 70 API endpoints documented with params and credit cost | ✅ generated from the OpenAPI spec |
| 4 | Every endpoint's response shape catalogued | ✅ 70 fixtures + data dictionary |
| 5 | Every parameter enum, default, min and max extracted | ✅ from the spec |
| 6 | Both screener field sets extracted | ✅ IDX 219, SGX 85 |
| 7 | All 39 documentation recipes enumerated; track-relevant ones read | ✅ 10 mined, 8 skimmed, 21 identified as visualization/no-code and out of scope |
| 7b | **All v2 documentation pages captured** | ✅ **69 of 69** v2 pages in the live sitemap are in `llms-full.txt`. The 34 uncaptured sitemap entries are all **v1** docs for the discontinued version (410 Gone) plus two index pages |
| 7c | Every public sectors.app product surface examined | ✅ `/`, `/pricing`, `/api`, `/api-for-idx`, `/workflow`, `/data-operations`, `/faq`, `/release`, `/indonesia/calendars/trading-calendar` — Playground and Key Management tabs are login-gated |
| 7d | **sectors.app sitemap fully enumerated and classified** | ✅ **2,006 URLs**. ~1,960 are per-entity product pages generated from the same data the API exposes (129 company pages, 89 broker pages, 82 group pages, 53 list pages, 15 index pages, 11 IPO pages, 7 ownership pages). The ~45 distinct informational pages are all visited or classified |
| 8 | Competing Sectors products examined | ✅ Sectors Workflow captured |
| 9 | Competitor field surveyed | ✅ **48** public teams (recounted live 5 Sep), track distribution computed. The Slack has 105 members, so the board is a lower bound |
| 10 | Offline simulation working end to end | ✅ mock server 14/14 endpoints, generators run clean from scratch |
| 11 | Every numeric claim re-derived from source | ✅ see below |
| 12 | Zero broken internal links | ✅ verified each pass |

Known-unavailable items are listed under "Known gaps" above and are gated behind a login, a
private Slack, or simply unpublished — no further passes can close them from outside.

**Closure argument.** *Superseded in part by pass 3 — see the box above; certificate
transparency found two further hosts (`admin.` and `insider.`) that no footer links.* The five
participant-relevant hosts are enumerated exhaustively rather than explored opportunistically:

- **hackathon.sectors.app** — 7 of 7 public pages captured; 17 further candidate paths confirmed 404; `/portal/*` is login-gated.
- **docs.sectors.app** — 69 of 69 v2 pages captured, verified against the live sitemap. The only uncaptured pages are v1 docs for an API version that returns 410 Gone.
- **sectors.app** — all 2,006 sitemap URLs enumerated and bucketed. Every distinct informational page visited; the rest are per-ticker product pages re-presenting data the API already exposes.
- **mining.sectors.app** — 445 sitemap URLs enumerated; structure and key pages captured. No `llms.txt`.
- **reits.sectors.app** — 118 sitemap URLs enumerated; `llms.txt` captured. **No API.**

> A previous pass claimed closure after enumerating `sectors.app/sitemap.xml` alone. That was
> wrong: **`mining.` and `reits.` are separate hosts and appear in no sectors.app sitemap** —
> only the footer links to them. Opening the footer link-by-link is what surfaced them, which
> is a reminder that sitemap enumeration is necessary but not sufficient for closure.

**Every footer link has now been opened individually and classified** — see the table at the
end of [`14-flare-community-and-engineering.md`](docs/api/14-flare-community-and-engineering.md).
That sweep is what surfaced the two subdomains, FLARE, the referral program, Stories, and the
search-architecture article; a sitemap listing alone would have missed all of them.

There is no remaining public surface on any of the five hosts that has not been captured or
explicitly classified. **Two caveats from pass 3:** certificate transparency lists
`admin.sectors.app` (staff console) and `insider.sectors.app` (redirects to `mining.`), neither
linked from any footer or sitemap; and `github.com/supertypeai` is a 74-repo public surface —
including the MCP server source and ~40 dataset pipelines — that this closure argument never
considered and that pass 3 enumerated but did not exhaust.

**Three further caveats from pass 4:**

- **Certificate transparency cannot close this either.** A second, independent CT source
  (certspotter) returns exactly the same 10 names as crt.sh, which corroborates pass 3 — but
  `*.sectors.app` is a **wildcard certificate**, so CT can only show which names were
  separately certificated, never that no other host exists. A 103-name DNS brute force
  returned 103 "hits" because `*.sectors.app` is also **wildcard DNS**: every label, including
  `definitely-not-real-1234.sectors.app`, resolves to the same two Vercel edge IPs. DNS
  enumeration is worthless against this domain. Host enumeration here is *best-effort*, not
  closed.
- **The enumeration was scoped to the wrong apex.** It covered `*.sectors.app` only.
  `supertype.ai` has **22** CT names of its own, two of them Sectors-related:
  `sectors-mcp.supertype.ai` (already documented as the MCP endpoint) and
  `sectors.supertype.ai` (not previously noted).
- **`status.supertype.ai`, referenced twice in the OAuth docs, does not exist** — NXDOMAIN on
  both Google and Cloudflare public resolvers, and absent from those 22 CT names.

**Self-audit.** Every numeric claim in these docs was re-derived from the OpenAPI spec and
the fixtures on the final pass: 70 endpoints (IDX 34 / SGX 12 / mining 19 / KLSE 5), 219 IDX
screener fields, 85 SGX screener fields, 942 tickers in the IDX universe (~32 pages at
`limit=30`), 49 flat-1-credit endpoints, exactly 4 two-credit endpoints. Two credit-cost
errors in an earlier draft were found and corrected this way — corporate actions and
shareholders composition are **1 credit each**, not 2. A later pass corrected an over-broad
claim that six API areas had "no recipe at all" — they have no *worked example*, but several
appear in the MCP tool table or the Postman listing, and the doc now states the difference
with the counts to back it.

---

*Compiled 4 September 2026; four verification passes 4–5 September, the third and fourth adversarial. Rules, pricing and the
matching board were captured on that date — verify anything time-sensitive against the
official sources before relying on it.*
