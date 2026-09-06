# Verification Pass 4 — Adversarial Re-audit of Pass 3

**Date:** 5 September 2026 · **Method:** pass 3's report treated as a claim, not as evidence.
Every one of its twelve corrections re-derived from a primary source, then every standing
check re-run independently. **Zero calls were made to any `/v2/*` endpoint on
`api.sectors.app`; that host was excluded from every probe, including the subdomain sweep.**
No account was created, no form submitted, no team registered, no credential entered.

Evidence for everything live is saved to
[`evidence/rechecks/pass4-live-recheck-2026-09-05.md`](../evidence/rechecks/pass4-live-recheck-2026-09-05.md).

**Result: 14 corrections.** Seven of them land in material pass 3 explicitly certified: its own
headline arithmetic (§1.1), its enum diff (§1.2, §1.3), the quote sweep it reported as
"remainder trace" (§1.4, §1.5), a table on the page it edited (§1.8), and the paging loop it
added (§1.11). Two are outright defects in `capture.py`, one of them predating pass 3 and
surviving all three earlier audits. Six sections came through genuinely clean and are named
as such at the end.

`firecrawl scrape` failed on every URL with the same IP-reputation error pass 3 hit. No API
key was obtained (that is account creation). All page fetches used the in-app browser.

---

## 1. Corrections made

### 1.1 The 271-credit figure was wrong — twice over

| | |
| --- | --- |
| **As written** | `15-fetch-strategy.md`: "The same 87 calls with defaults would cost **271 credits — 54% more**"; savings table totalling **95**. README: "against **271** if every parameter defaulted". |
| **Correct** | **297 credits, 69% more**, saving **121**. |
| **Source** | `plan.json` re-costed line by line against the spec's cost sentences and parameter defaults. |

Pass 3 replaced an earlier "roughly three times" with 271 and called the per-line arithmetic
correct. The per-line arithmetic *is* correct; the row set is not.

**The row that should not be there.** The table's fifth row reads
`Screener × 3 | ?q= = 9 | structured where = 3 | 6`. That is not a default. The spec gives
`/v2/companies/` and `/v2/sgx/companies/` a `q` parameter with **no default** — a screener
call carrying no parameters at all is already the 1-credit structured mode. Choosing `?q=` is
opting *into* a more expensive mode, not failing to constrain one. Counting 6 credits "saved"
by not doing something optional inflates the baseline. (It also undercounts its own premise:
the plan has four screener calls, not three — three on `/v2/companies/` and one on
`/v2/sgx/companies/` — so even on its own logic the figure would be 8.)

**The row that is missing.** `/v2/close/` and `/v2/companies/quarterly-financial-dates/` bill
**1 credit per page**, and `limit` is a genuine default: `default: 20, minimum: 1,
maximum: 30`. The plan passes `limit=30` and budgets 32 pages each. At the documented default
of 20 the same ~950-ticker sweep is **48 pages** — 96 credits instead of 64. That is a real
32-credit default effect the table never had.

So:

```
constrained (plan.json est_cost)                              176
+ company/report × 8  at 8 sections                           + 56
+ top-changes × 2     at 2 classifications × 5 periods        + 18
+ subsector/report × 3 at 6 sections                          + 15
+ close & quarterly-dates at limit=20 (48 pages each)         + 32
                                                              ----
all-defaults                                                   297      saving 121, +69%
```

**The `financials/quarterly` exclusion is honest, not convenient.** I checked it as instructed.
The spec gives `n_quarters` `minimum: 1`, **no `default` and no `maximum`**. There is no
number to put in the row. Excluding it also cuts *against* the corrected conclusion — an
unbounded default would make the saving larger, not smaller — so it is not a thumb on the
scale. Verdict on pass 3's reasoning here: **PASS**. Verdict on its total: **FAIL**.

Fixed in `15-fetch-strategy.md` (table, heading and prose) and in the README index line. The
two superseded audit rows in the README are marked rather than rewritten.

### 1.2 An invented enum value survived a machine diff that was supposed to catch exactly this

| | |
| --- | --- |
| **As written** | `06-parameter-cheatsheet.md:174` — `/v2/news/?extension=mining` accepts `Bauxite, Coal, Copper, Gold, Iron, Nickel, Non-Metallic Mineral, **Sand**, "Sand, Stone, Gravel", Tin` — 10 values |
| **Correct** | 9 values. There is **no bare `Sand`**. |
| **Source** | `schema.json` → `/v2/news/` → `commodity_type.enum` = `['Bauxite','Coal','Copper','Gold','Iron','Nickel','Non-Metallic Mineral','Sand, Stone, Gravel','Tin']` |

The bare `Sand` is real on `/v2/mining/licenses/` (14 values, which the doc lists correctly)
and was carried across to the news row. Pass 3 reported "all 45 enum-bearing params
machine-diffed both directions · 30 of 31 doc claims exact; 1 invented". This is the second
invented value, in the same table, in the row directly adjacent to one it checked. Removed.

### 1.3 Two parameters attributed to an endpoint that does not accept them

| | |
| --- | --- |
| **As written** | `06-parameter-cheatsheet.md` broker table: `origin` and `cohort` on "broker-summary top, **broker-activity top**" |
| **Correct** | `/v2/broker-activity/{broker_code}/top/` takes only `broker_code`, `start`, `end`, `n_brokers`. |
| **Source** | `schema.json` → that path → `parameters` |

The *values* are right for `/v2/broker-summary/{symbol}/top/` and `/v2/brokers/top/`. The
endpoint list is wrong. A team building the bandarmology idea would have sent
`origin=foreign&cohort=institutional` to broker-activity and got a 400. Both rows rewritten
with explicit paths, plus a note saying why broker-activity has no cohort filter.

### 1.4 A fabricated quotation, presented as "their framing, explicitly"

| | |
| --- | --- |
| **As written** | `11-data-provenance.md:18` — AI is *"designed to enhance the efficiency and accuracy of our financial data products, and not to replace human judgment."* |
| **Correct** | **That sentence appears nowhere under `evidence/`.** |
| **Source** | `grep -r "replace human\|efficiency and accuracy" evidence/` → zero hits. The capture's actual annotation is `**Reviewed by humans** — human-in-the-loop on every AI step; "led by banking veterans and former data journalists"` (`sectors-api-for-idx-and-dataops.md:70`) |

This is the most serious of the quote findings because of the attribution attached to it.
Replaced with the attested wording, with the removal noted in place.

### 1.5 Two more quote failures in the same file

| Where | Quoted as | Source actually says |
| --- | --- | --- |
| `11-data-provenance.md:76` | "daily updates, self-healing upstream corrections, and event-driven enhancements." | `sectors-api-for-idx-and-dataops.md:15`: **"Daily updates with self-healing corrections"** — a headline-stats bullet. The rest of the phrase does not exist |
| `11-data-provenance.md:68` | "the only financial data provider engineered on top of these standards." | line 81: **"To date, we are the only financial data provider that are engineered on top of these standards."** |

Plus a composite quote: `"3 months free, save 25%"` is two separate lines on the pricing
capture (`### $5313 months free` and `Save 25%`), not one phrase. Reworded.

Pass 3's §1.7 reported 3 drifted and 4 unsourced out of 165 quotes, "remainder trace". These
four are in the remainder. My method differed in one way that matters: I stripped markdown
emphasis and normalised dashes *and* excluded fenced code blocks, which cut the false-positive
rate enough to hand-classify every miss rather than sampling.

### 1.6 A drifted ToS quote

`13-subdomains-and-terms.md:136` writes `"competes with us"`. The ToS capture
(`subdomains-footer-sweep.md:86`) reads *"Use the Services as part of any effort to **compete
with us** or otherwise use the Services…"*. Fixed. The two longer ToS quotes in the same
section — the anti-automation clause and the licence grant — are verbatim.

### 1.7 An unsourced illustration in the search-architecture section

`14-flare-community-and-engineering.md:115` renders the Lite-IDF point as *"otherwise 'Bank
Jago' ties with 'Panin Financial' on a `bank pan` query"*. The captured article
(`footer-pages-opened.md:26`) says only *"Lite-IDF weighting so rare tokens (pan) outweigh
common ones (bank)"*. Neither company name is in the capture. Reworded to mark the worked
example as this dossier's, not the article's.

### 1.8 Two stale figures in the competitive landscape, one of them the third survivor of a count corrected twice

| | |
| --- | --- |
| **As written** | `competitive-landscape.md` "Team sizes on the board" table: 41 / 2 / 1, **total 44**. And "The real competitive field is smaller than **44**." |
| **Correct** | **45 / 2 / 1, total 48**, 52 participants. |
| **Source** | Live recount, 5 September — see §2.1 |

Pass 3 updated the *track* table on this page to 48 and left the *size* table at 44, in the
same document, four sections apart. Same failure mode it diagnosed in passes 1 and 2.

The page also still read *"**Seventeen** teams heading for Track 01"*. Seventeen is from the
discredited 46/17-11-5 count that pass 1 corrected and pass 2 corrected again. It is now 15.
And *"don't treat **9%** as final"* was Track 02's share of the 4 September board (4/44); it is
now 15%. Both fixed. The README's completion-criteria table also still said "44 public teams".

### 1.9 Two headline strategic claims falsified on the live board

Pass 3 recounted the board's *numbers* and did not re-read its *text*. Both of these are
prominent conclusions, and both are now wrong:

**"Nobody is advertising for a video editor."** Two teams are, as of 5 September:

- **Sepi** (Track 02): *"Cari 1 orang video/motion untuk judging video 3 menit. Produk sudah didefinisikan dan backend dikerjakan solo."*
- **StockPro** (Track 03): *"Need a designer, editor, motion graphics and maybe someone who familiar with cron ,automations ,n8n and hermes"*

This mattered: "30% of the rubric is under-contested" was one of the dossier's better
strategic observations. It is narrowing, not gone, and the doc now says so with a shelf-life
warning.

**"Only one team has published a project name and description in enough detail to identify."**
Four do. Twenty-two of the 48 cards carry text. The one that matters most:

- **Apriyanto** (Track 03): *"Hiddwn gems & early accumulation by bandar"* — a broker-accumulation screen, i.e. the same territory as idea 1.1 in `what-we-can-build.md`.

So the row reading *"The unusual-data plays (mining licences, broker cohorts, suspensions) are
very unlikely to be duplicated"* is half wrong. Mining licences and suspensions still look
untouched; **broker cohorts are not**. Corrected, with the four disclosed projects tabulated.

### 1.10 `capture.py`: an unbilled failure permanently deleted a call from the plan

**The most expensive defect found this pass, and it predates pass 3.**

`run()` skipped any plan entry whose key was present in the manifest, and the failure branch
wrote a manifest entry for *every* non-2xx outcome. So a 402, a 400, a 429/5xx that outlived
its retries, or a bare network error — **all of which cost nothing** — were recorded as done
and never retried.

Demonstrated against a dead port:

```
FAIL  /v2/subsectors/   0  {'error': 'URLError: <urlopen error [Errno 61] Connection refused>'}
# manifest now: {"v2_subsectors": {"status": 0, "billed": false, ...}}
# next run, against a working server:
nothing to do; every selected call is already recorded.
```

Zero credits spent, and the call is gone from the plan forever. The docstring's promise —
"Crash halfway through, re-run, pay nothing for what succeeded" — was true, but it also paid
nothing for what *failed*, by never trying again. Three audits called `capture.py` verified.

**Fixed** with an explicit `is_settled()`: only a 2xx (payload on disk) or a 404 (a credit
already paid for a lookup that will not change) is skipped. Everything else prints
`RETRY` and is re-attempted. Verified: three dead-port failures, then a clean re-run against
the mock that fetched all three, then a third run that skipped the two 200s and the 404.

### 1.11 `capture.py`: a mid-sweep stop discarded every page it had paid for, and told the ledger nothing was spent

Pass 3 added the paging loop and verified the happy path. The failure path was not exercised.
Driving the committed code against a mock with only 15 credits:

```
FAIL  /v2/close/  402  {'results': [{'symbol': 'AADI.JK', ...
ledger: {"status": 402, "est_cost": 32, "billed": false}
capture.py --report  ->  estimated credits: 0
mock meter           ->  credits_spent: 15
```

Three faults in one: **15 credits really were spent and the ledger recorded 0**; the 15
fetched pages were thrown away (nothing written to disk); and the manifest entry made the
sweep unretryable under the old skip rule. A fourth, cosmetic: the `error` field held the
*merged partial payload* rather than the 402 body, because `payload` had already been
reassigned by `merge_pages`.

On the question as posed — *does it respect the budget cap per page rather than per plan
entry?* — the budget check is per entry and reserves the full `est_cost` before the sweep
starts, so it can never overshoot. A budget stop therefore cannot happen mid-sweep. The
partial-recording hazard is real but reached through an HTTP failure, not the cap.

**Fixed.** A partial sweep now writes what it fetched, flags it `incomplete` with
`pages_fetched`, bills the pages that actually returned, and resumes from the first missing
page on the next run. Verified end to end:

```
run 1 (15-credit mock):  PART /v2/close/ 402  15/32 pages kept, will resume   ledger 15 == meter 15
run 2 (funded mock):     17 further HTTP calls, merged 32 rows, pages_fetched 32, manifest clean
run 3:                   nothing to do
total 32 credits, not 47 — the resume does not re-buy the first 15 pages
```

Also added a guard: a `"pages": N` entry with no `limit` in its params would have issued N
identical requests at `offset=0`. It is now refused rather than silently repeated.

### 1.12 The mock's own limits were under-documented

`harness/README.md` claims the meter charges "the documented per-endpoint cost". Three
divergences it did not list, all found by exercising the server rather than reading it:

- `?sections=bogus,alsobogus` returns **200 and bills 2 credits**. Live, an unknown section is a `400`, which is free. The mock over-bills a typo instead of teaching you about it. Same for any out-of-enum `classifications` or `commodity_type`.
- `?sections=overview` bills 1 and still returns the **whole eight-section fixture**. A parser developed against the mock can depend on fields that call would not return live.
- `/v2/free-float/` bills a flat 1 against the spec's 1-per-100-rounded-up. This is the entire 9-credit gap between `capture.py`'s ledger (176) and the mock's meter (167) on a full-plan rehearsal — pass 3 called that gap expected, and it is, but it was not written down anywhere a user would find it.

All three added to "What it deliberately does not emulate".

### 1.13 `credit_default_items` means two different things

Pass 3 describes the field as parsing *"Default behavior (all N sections) consumes N credits"*.
For ten of the eleven endpoints that is what it holds. For `/v2/companies/top-changes/` the
sentence is *"Default behavior (2 classifications × 5 periods) consumes 10 credits"* and the
regex captures **2**, not 10 — the field holds a classification count, and the `5` periods
stay hardcoded in `mock_server.py`. The billed result is correct (2 × 5 = 10, verified), so
this is a latent inconsistency rather than a live bug, and it is recorded here rather than
"fixed" into a behaviour change nobody asked for.

### 1.14 `status.supertype.ai` does not exist

Pass 3 recorded it as "referenced-but-unreachable rather than asserted either way". It can be
asserted: **NXDOMAIN** from both Google (`8.8.8.8`) and Cloudflare (`1.1.1.1`), and absent from
all 22 names in `supertype.ai`'s certificate-transparency record. The apex resolves fine, so
this is not a network condition at this end. The OAuth-connector docs point twice at a status
page that has never existed. README gap ledger and closure argument updated.

---

## 2. Confirmed — re-derived this pass, taking no prior record as evidence

### 2.1 The matching board — recounted live, and it has *not* moved

| | 4 Sep | 5 Sep (pass 3) | 5 Sep (pass 4, independent) |
| --- | --- | --- | --- |
| Public team cards | 44 | 48 | **48** |
| Track 01 | 16 | 15 | **15** |
| Track 02 | 4 | 7 | **7** |
| Track 03 | 11 | 12 | **12** |
| No track yet | 13 | 14 | **14** |

Counted three ways inside the "Public teams" section only — join buttons, `N/4 participant(s)`
strings, and name extraction after each `TRACK` label — all three returning 48. Pass 3's
recount is **confirmed**, and the only reason this figure is not stale is that both passes ran
on the same day. Registration closes 22 September; re-count it then.

Two things pass 3's count did not surface. Size distribution is **45 solo, 2 pairs, 1 trio,
zero 4/4** — no card can show 4/4, because the board lists only teams with room to grow. And
the board is a lower bound on the field: the Slack workspace reports **105 members** against
52 people on the board.

### 2.2 Documentation has not drifted since capture

Re-fetched and hashed:

| File | Live | Committed | |
| --- | --- | --- | --- |
| `docs.sectors.app/schema.json` | 951,210 B | 951,210 B | **md5 identical** |
| `docs.sectors.app/llms.txt` | 32,677 B | 32,677 B | **md5 identical** |
| `docs.sectors.app/llms-full.txt` | 839,575 B | 839,575 B | **md5 identical** |

`sectors.app/release` — latest entry still 2026-08-10, "Foreign Flows". Nothing added since
the 4 September capture.

### 2.3 The rules page is unchanged

Sentence-level hash diff (≥40 characters, normalised): **111 capture sentences, 108 live, 7
capture-only, all 7 markdown-table-versus-innerText line joins**. Zero content differences.
Deadlines, eligibility, 2–4 teams, 1,000 credits, the 90-day repo, 1-minute + 3-minute videos,
40/30/30, IDR 50M split, the trade-execution ban, the financial-advice ban and the leaked-key
freeze exception all verified word for word.

### 2.4 The 17 index codes — and `sti` is real

Pass 3's §1.4 is **correct**: the accordion on `/v2/index-daily/{index_code}/` lists exactly 17
codes, verbatim, and `idxv30`, `sminfra18`, `sti`, `idxvesta28` were genuinely absent from the
dossier before. Verified byte-for-byte in both `schema.json` and `llms-full.txt:902`.

Its `sti` caution was the right call on the evidence it had — **and Phase 2 resolves it the
other way.** `supertypeai/sectors_indices_company_list` is the ingestion pipeline for that
endpoint. Its registry `index_name.csv` carries **18** rows including `STI,Straits Times
Index,^STI` and `KLSE,Bursa Malaysia,^KLSE`, and `index_daily_data_scraper.py` reads
`# Fetch STI, KLSE, FTSE from yf` / `indices = ["^STI","^KLSE","WIIDN.FGI"]` and inserts into
the `index_daily_data` table. So `sti` is a real series, and **`klse` is a candidate 18th code
the spec's accordion omits** (still unverifiable-until-live).

Two things pass 3 missed here. A **second, contradicting list** exists in the docs: the
agent-skills reference page (`llms-full.txt:10629`, `evidence/sectors/agent-skills/SKILL.md:282`) gives
only **15** codes, dropping `ihsg` and `sti`. Since `ihsg` is unquestionably valid that list is
incomplete rather than authoritative — but it is the same pair the CSV directory omits, which
is worth knowing. And `srikehati` is spelled `SRI-KEHATI` in the pipeline registry.

### 2.5 The mock's cost model — every per-item endpoint exercised, not sampled

Pass 2 tested one endpoint and missed three bugs. This is all of them, plus constrained
variants, measured off `X-Credits-Charged`:

| Call | Charged | Spec |
| --- | --- | --- |
| `/v2/company/report/BBCA/` and `/v2/company/report/` | 8 · 8 | 8 ✓ |
| `/v2/subsector/report/banks/` and `/v2/subsector/report/` | 6 · 6 | 6 ✓ |
| `/v2/sgx/company/report/D05/` and `/v2/sgx/company/report/` | 4 · 4 | 4 ✓ |
| `/v2/klse/company/report/MAYBANK/` and `/v2/klse/company/report/` | 4 · 4 | 4 ✓ |
| `/v2/companies/top-changes/` | 10 | 2 × 5 ✓ |
| `/v2/sgx/companies/top/` · `/v2/klse/companies/top/` | 5 · 5 | 5 ✓ |
| `?sections=overview` / `overview,valuation,dividend` | 1 · 3 | per section ✓ |
| `?sections=statistics` / `statistics,growth` (subsector) | 1 · 2 | ✓ |
| `?sections=overview` (SGX) · `overview,dividend` (KLSE) | 1 · 2 | ✓ |
| top-changes `?classifications=top_gainers&periods=1d` | 1 | ✓ |
| top-changes `?classifications=…,…&periods=1d,7d,1m` | 6 | 2 × 3 ✓ |
| top-changes `?periods=1d` only | 2 | 2 default classes × 1 ✓ |
| top-changes `?classifications=top_gainers` only | 5 | 1 × 5 default periods ✓ |
| `/v2/companies/` · `?q=` | 1 · 3 | ✓ |
| `/v2/sgx/companies/` · `?q=` | 1 · **3** | ✓ — pass 3's §1.11 fix holds |
| `most-traded`, `brokers/top`, `broker-summary/{}/top`, `broker-activity/{}/top` | 2 each | ✓ |
| `financials/quarterly` default · `?n_quarters=4` | 1 · 4 | per quarter ✓ |

**PASS** on pass 3's §1.10 and §1.11. All eleven `credit_default_items` values are populated
and all eleven price correctly. The caveats are in §1.12 and §1.13 above.

### 2.6 The billed 404

`--unknown ZZZZ,XXXX,NOTREAL`: `/v2/company/report/ZZZZ/`, `/v2/company/report/XXXX/`,
`/v2/daily/NOTREAL/`, `/v2/mining/companies/NOTREAL/` and `/v2/subsector/report/ZZZZ/` all
return **404 with `X-Credits-Charged: 1`** and body `{"error": "Company not found."}` — which
is a verbatim spec example (three endpoints use that exact string). `/v2/company/report/BBCA/`
still returns 200 at 8 credits, `/v2/daily/BBCA/` 200 at 1. An unknown *endpoint path* 404s
free. **PASS.** One cosmetic note: the same "Company not found." is returned for a subsector
slug and a mining slug, where the spec has per-endpoint 404 strings.

### 2.7 `capture.py` pagination, against the mock only

32 HTTP calls for the `/v2/close/` entry (mock meter attributes 32 to that path), merged into
one recording with `pages_fetched: 32`, idempotent on re-run (0 further calls). Full-plan
rehearsal: **87 entries → 149 HTTP calls** (87 + 2 × 31 extra pages), 87 recordings, ledger
176, mock meter 167. Reproduces pass 3's figures exactly. **PASS** on the mechanism; the two
defects are in §1.11.

Budget cap: stops **before** exceeding — `STOP: next call would exceed budget (20 + 1 > 20)`,
cumulative landing exactly on 20, mock meter 20. Resume at a raised cap works. Ledger sums to
33 against a mock meter of 33. Cost headers detected and surfaced. 404 recorded `billed: true`
and never re-called. **All PASS.**

### 2.8 Everything else re-run

| # | Check | Method | Result |
| --- | --- | --- | --- |
| 7 | Generated docs | Both scripts re-run, md5 before/after, `git status` | **byte-identical**, both, twice |
| 8 | Endpoint count | Operations counted in the spec | **70 path items, 70 GET, 0 non-GET** |
| 8b | Prose ↔ spec, both directions | 135 distinct `/v2/…` strings resolved against templates; then every template searched for in prose | **128 resolve; 7 are docs-site URLs or bare base references. Zero spec templates unreferenced** |
| 9 | Declared costs | Cost sentence extracted from all 70; machine-diffed against every path+number line in prose, `plan.json` and `plan/` | **49 flat-1, 4 flat-2 (`most-traded`, `brokers/top`, `broker-summary/{}/top`, `broker-activity/{}/top`), 17 non-flat.** 70 flat-cost line checks, 1 flagged, that one a false positive (three paths on one line) |
| 9b | Worked examples | Every one re-computed | Track budgets 4+40+20+30+30+30+50+100 = 304 ✓ · 4+160+60+80+100 = 404 ✓ · 4+400+150+100+200 = 854 ✓ · 32 × 40 = 1,280 ✓ · 950/100 → 10 ✓ · 942/30 → 32 ✓ · tiers 5/28/74/55/14 = 176 ✓ · 1000−176 = 824 ✓ · idea 1.1 at 2+1+1 = 4/ticker, ×50 = 200 ✓ · mock README 8+8+3+1 = 20 over 11 calls, 1000−20 = 980 ✓ |
| 10 | IDX screener fields | Re-extracted from the spec, diffed against the doc tables in both directions | **219 spec, 226 doc rows, zero in spec-not-doc, 7 in doc-not-spec — all seven the query-parameter table (`q`, `where`, `order_by`, `desc`, `limit`, `offset`, `include_query_values`)** |
| 10b | SGX screener fields | Same | **85 / 85, zero symmetric difference** |
| 10c | Category subtotals | Nested-accordion parse | IDX **24 / 3 / 31 / 107 / 44 / 10 = 219** ✓ · SGX **34 / 1 / 16 / 34 = 85** ✓ · every doc heading matches |
| 10d | SGX coverage markers | Counted in the spec | **20** `(coverage: Big caps only)` and **10** `(coverage: Banks only)`, field lists matching the doc member-for-member ✓ |
| 11 | Enums, both directions | All 33 enum-bearing params, 239 enum values, machine-diffed | 1 invented (§1.2), 1 mis-attributed (§1.3). Province counts **37 / 33 / 22 / 8** exact; the 8-province auction list member-for-member ✓; the 64 values "absent" from the cheat sheet are the three long province lists (given as counts by design) and `-`-prefixed `order_by` variants (given as "± `-`") |
| 11b | Defaults | All 46 documented defaults extracted; every default-bearing parameter name searched in the cheat sheet | **zero omissions.** `limit` 50/200 and 20/30 ✓ · `min_mcap_billion` 5000 ✓ · `approx` true ✓ · `n_stock` 5 (1–10) ✓ · `n_brokers` 1–90 ✓ · `extension` idx ✓ · `order_by` symbol ✓ · `desc` false ✓ · `adjusted` false ✓ · `classifications`/`periods` "all" ✓ · `n_quarters` no default, min 1 ✓ |
| 11c | `sections` sets | Parsed from each report description | IDX 8, subsector 6, SGX 4, KLSE 4 — all match the cheat sheet ✓ |
| 12 | Auth | Spec `securitySchemes` + `llms-full.txt` | `ApiKeyAuth` = header `Authorization`, and `llms-full.txt:10341` verbatim: *"The Authorization header uses the raw key (no "Bearer" prefix)"*. MCP config blocks use `"Authorization": "Bearer YOUR_API_KEY_HERE"`. The spec **also** declares `OAuthBearerAuth` for the `/oauth/` flow, which `01-api-guide.md:23` already documents. All three forms correct |
| 13 | Query syntax | Each construct traced individually | Spec accordions give `=`, `!=`, `>`, `>=`, `<`, `<=`, `like`, `in`, `and`/`or`, quoting, `in` lists, `field[YYYY]`, `field[Qi-YYYY]` ("Must use bracket notation `field[Qi-YYYY]`"), arithmetic on both sides — all verbatim. `order_by` parenthesis rule verbatim at `llms-full.txt:124` |
| 13b | `is null` | Grepped the whole raw corpus | **One hit in all of `evidence/`** — `llms-full.txt:7495`, a Google Sheets recipe ("exclude any rows where the `Symbol` field is null"). Not the query language. Pass 3's removal was **correct** |
| 13c | The three query-builder constructs | Located in the capture | All three in `authenticated-session-captures.md`, lines 98 and 111: `where=(sub_sector="banks" and eps[2024]>0 and total_yield[2024] is not null)&order_by=-total_yield[2024], -market_cap` — parenthesised group, `is not null`, multi-column ordering with per-column direction. `is not null` appears **zero** times in `llms-full.txt`, so the capture really is its only source ✓ |
| 14 | Quotes | 106 quotations ≥15 chars outside fenced code, normalised and grepped | 4 real failures (§1.4–1.6), the rest either trace or are the dossier's own scare quotes and invented examples |
| 15 | Hackathon rules | Full live re-read + hash diff | Unchanged — §2.3 |
| 16 | `plan.json` | Every path resolved; every param checked against the spec's enums, minimums and maximums; every `sections`/`classifications`/`periods` value checked for membership; totals re-summed | **87/87 paths · 0 unknown params · 0 enum violations · 0 out-of-range values · 176 total · tiers 5/28/74/55/14.** Subsector slugs `oil-gas-coal` and `telecommunication` both attested in `llms-full.txt:8688-8689` |
| 17 | Generators | Run from empty, twice, into separate directories | **347 files, identical aggregate hash across runs, and byte-identical to the committed `synth/`** (`diff -rq` clean). All promised outputs present: 17 index series, 120 quarterly series, 300 mining sites, 400 licences, 60 auctions, 1,308 price points |
| 17b | Holiday calendar | `synth_extended.py` set vs doc-12 code block vs doc-12 table, then recomputed | **22 dates, all three identical.** 239 trading days for 2026 independently recomputed ✓. Per-month trading days 20/18/17/21/16/20/23/19/22/22/21/20 match the table ✓. September has no holidays ✓. 25 August is a holiday inside the build window ✓ |
| 18 | `capture.py` | Driven against the mock only | §2.7 |
| 19 | Internal links | 181 relative links across 45 markdown files | **Zero broken** outside fenced code blocks. The 3 dangling links in `evidence/sectors/agent-skills/SKILL.md` are inside a verbatim third-party capture |
| 19b | Cross-doc numbers | Recurring figures scanned | Three stale (§1.8). All surviving "46 teams" are in audit narrative describing the correction. MCP tool count: `sectors-mcp-repo-tree.txt` has **67** `.ts` files under `src/tools/generated/`, of which one is `index.ts` — so **66 tools, 65 `fetch-*` plus `get-subsectors`**. Pass 3's §1.9 confirmed |

---

## 3. Unverifiable until live

Unchanged in kind. Two entries got materially stronger this pass, one is resolved, one is new.

| Claim | Status |
| --- | --- |
| **Response shapes** | Still documented shapes. **Stronger**: a third independent copy of the spec (§4.1) agrees on all 70 response examples with zero structural difference. Three sources agreeing is still not one observation |
| **Actual billing** | Still declared costs, now declared by three artefacts of the same organisation |
| **Spend header names** | Still undocumented. `X-Credits-Charged` / `X-Credits-Remaining` remain **invented by the mock**. `capture.py --tier 0` is still the 5-credit way to learn the real names |
| **`is null`** | Still attested nowhere. Unchanged |
| **`sti` as an `index_code`** | **Resolved, without a live call.** The ingestion pipeline fetches `^STI` into the table the endpoint reads (§2.4) |
| **`klse` as an `index_code`** | **New.** In the pipeline's registry, absent from the spec's accordion. One call settles it |
| **`srikehati` vs `SRI-KEHATI`** | **New.** The API code in the spec is `srikehati`; the pipeline registry uses `SRI-KEHATI`. Whether the endpoint normalises is unknown |
| **`include_query_values` semantics** | Unchanged; the doc already flags the conflict between the parameter description and the official example |
| **Empty results** | Unchanged. Documented by the Postman collection, unreproducible on the mock |
| **The `?q=` 400 exception** | Documented (a `?q=` 400 after the model runs costs 1 credit) but never observed. Now stated in `05-credit-budget.md` as well as `01-api-guide.md` |
| **Per-dataset freshness** | **New, and explicitly not an SLA.** The cadences in §4.3 are read off committed cron expressions and READMEs in public repos, not observed against the API |
| **Numeric rate limit** | Unchanged. The 0.3 s sleep is documented; "~3 req/s" is an inference the dossier already labels as one |
| **Anything behind a login** | Portal, playground, key management, Slack, Discord. Unchanged and out of scope by instruction |

---

## 4. New material

### 4.1 `sectors-mcp` ships its own `schema.json`, and it agrees on everything that matters

945,791 bytes against the committed 951,210. Diffed field by field:

```
paths                       70 in both, zero unique to either
parameter names             0 differences across all 70 endpoints
parameter schemas           0 differences (enums, defaults, minimums, maximums)
credit-cost sentences       0 differences
"Default behavior (…)"      0 differences
200-example response shapes 0 differences
securitySchemes             identical
screener field sets         IDX 219 = 219, SGX 85 = 85, zero symmetric difference
index-daily accordion       byte-identical, all 17 codes
```

46 endpoints differ — **in prose only**, overwhelmingly relative-versus-absolute documentation
links — the MCP copy writes `[SGX Sectors]` against a relative `../singapore/sgx-sectors`
target where the committed copy uses the full `docs.sectors.app` URL.

This is a **third** independent source, after the OpenAPI spec and the Postman collection,
agreeing on every structural fact in this dossier. It is the strongest evidence the structural
layer has.

### 4.2 The `supertypeai` org, read rather than listed

Pass 3 enumerated 74 repos and read three. This pass read the READMEs and workflow schedules
of fifteen, which is what `11-data-provenance.md` needed — that document previously described
provenance from marketing copy, and now names the actual upstream sources. Full detail in
[`evidence/rechecks/pass4-live-recheck-2026-09-05.md`](../evidence/rechecks/pass4-live-recheck-2026-09-05.md) §9;
the substance is now a table in `11-data-provenance.md`. The four findings that change how you
would use the API:

1. **Everything lands in Supabase**, in tables that map onto endpoints (`idx_filings`, `idx_news`, `index_daily_data`).
2. **Freshness is per-dataset, not global.** Filings every 2 hours; news every 4; indices weekdays at 18:00 WIB; suspensions daily at 10:00 WIB; mining commodity prices weekly. The docs give one blanket "end of day".
3. **"Human in the loop" is literal.** `sectors_corporate_actions` states that rights issues, reverse stock splits and buybacks are **typed in by hand** through a Streamlit app because the upstream source lacks them. Expect those three to lag.
4. **The HBA benchmark is upstream but not exposed.** `coalresearch` scrapes `minerba.esdm.go.id/harga_acuan` — the official Indonesian coal reference-price page — weekly. `13-subdomains-and-terms.md` correctly said HBA appears nowhere in the API; it can now also say where the data actually comes from, and that the gap is a product decision rather than missing data.

Also worth flagging for anyone extending this dossier: `sectors_us_insider_trading`,
`sectors_us_cron` and `us-sectors-kb` imply a **US-market surface** the dossier has never
considered, and `sectors_guard` / `sectors_guard_validator` are the implementation behind the
"self-healing corrections" marketing line.

One negative finding worth recording: `sectors-kb` links to a "Sectors Glossary" wiki, which
would close the dossier's "internal data dictionary is not published" gap. **It does not.** The
wiki is a single "Welcome to the sectors-kb wiki!" page, one revision, last edited 17 October
2023. The gap stays open.

### 4.3 Host enumeration — corroborated, and shown to be uncloseable

**crt.sh and certspotter, queried independently, return the identical 10 names.** Pass 3's
`admin.` and `insider.` findings are confirmed, and nothing new has appeared.

The second method the brief asked for returns nothing, and that is the finding. A 103-name DNS
brute force (excluding `api.`) produced 103 "hits", because `*.sectors.app` is **wildcard
DNS** — `definitely-not-real-1234.sectors.app` resolves to the same two Vercel edge IPs as
everything else. DNS enumeration cannot distinguish a host from a typo here.

The consequence for the dossier's closure argument is stronger than "footer enumeration is not
sufficient": because the certificate is a **wildcard**, certificate transparency can only show
which names were *separately* certificated. It cannot prove no other host exists. Host
enumeration on this domain is best-effort, not closed, and the README now says so.

Separately, the enumeration was scoped to the wrong apex. `supertype.ai` has **22** CT names of
its own, two Sectors-related: `sectors-mcp.supertype.ai` (already documented as the MCP
endpoint) and `sectors.supertype.ai` (never noted).

### 4.4 Bahasa Indonesia rules — a definitive negative

The brief asked for "look harder or state definitively". Four independent checks, all negative:

1. **Twenty candidate routes 404** — `/rules/id`, `/id/rules`, `/aturan`, `/peraturan`, `/ketentuan`, `/syarat`, `/rules/bahasa`, `/rules/indonesia`, and twelve more.
2. **The Next.js client bundle knows five routes.** Scanning all 25 loaded scripts for path literals yields exactly `/matching`, `/portal`, `/portal/team`, `/rules`, `/tracks/`. There is no Indonesian route to reach.
3. **`?lang=id` and `Accept-Language: id-ID` are both ignored** — all three fetches return the same 130,787-byte English document.
4. **No i18n markup**: `<html lang="en">`, zero `<link hreflang>`, zero links mentioning `id`/`bahasa`/`indonesia`/`lang`.

**They are not published on the website.** The rules page still says they exist, so they are
distributed some other way — Slack, or a document. Gap ledger updated from "likely distributed
via Slack" (a guess) to a sourced negative.

### 4.5 Discord and Slack — metadata read, neither joined

Both remain closed, as instructed. But both yield useful public metadata without
authenticating:

**Discord** `discord.gg/TAnZMmNS4X` is **not a hackathon channel**. It is the general
**Supertype** community server — 1,346 members, ~80 online, landing channel `👋・welcome`,
description "Supertype is the makers of Sectors Financial Data Suite and an industry-leading
AI consultant / product incubator." It carries a member-verification gate. Reading it requires
an account → closed.

**Slack** — the invite landing page renders without signing in: workspace **Sectors
Hackathon**, invite from Aurellia Christie, **105 members**, and *"This invitation expires in
15 days."* That is **around 20 September — two days before registration closes on the 22nd.**
Anyone planning to join should do it well before then. Reading the channels requires an
account → closed. Both facts are now in the README.

### 4.6 An API area with no worked example — checked, and pass 3's answer holds

Re-checked. Six areas have no worked example anywhere in the documentation: **suspensions,
corporate actions, shareholders composition, free float, listing performance, and the entire
mining extension.** All six appear in the MCP tool table and carry a runnable request in the
Postman collection, so "runnable example" is covered everywhere and "worked example showing
what to do with the data" is not. That distinction, introduced in pass 2 and re-affirmed in
pass 3, survives a third check.

### 4.7 What the generators still cannot produce

I did not extend `synth_extended.py` this pass, and I want to be explicit about why rather
than pad the deliverable. Its 17 index series already match the spec's documented set (pass 3
extended it from 8), and the three gaps I found are not generator gaps:

- **Empty result sets.** Every generated collection is non-empty, so the Postman collection's documented "200 with an empty collection, still billed" case is unreproducible. This is a *fixture* property, not a generator one — the right fix is a `--empty` flag on `mock_server.py`, which would change behaviour nobody asked for.
- **Per-100 free-float billing.** Fixing this means generating ~950 free-float rows, which the mock does not read from `synth/` at all — it serves the spec fixture. That is a mock wiring change, not a generator change.
- **`klse` as an index series.** Adding it would bake an unverified code into the offline data. It is in §3 for a reason.

All three are recorded in `harness/README.md` under "What it deliberately does not
emulate" so the next person can decide, rather than being silently absent.

---

## 5. Bottom line

**The structural layer** is now the best-evidenced material in the dossier and got stronger
again this pass. The 70 endpoints, their parameters, enums, defaults, declared costs and
response shapes, the 219 and 85 screener fields with all six category subtotals, and the 17
index codes are machine-derived from `schema.json` and corroborated by **two** independent
copies of the same contract — the public Postman collection (pass 3) and `sectors-mcp`'s own
`schema.json` (this pass), the latter agreeing on every parameter, every cost sentence and
every response example with zero differences. The live `schema.json`, `llms.txt` and
`llms-full.txt` are byte-identical to the captures a day later, so nothing has drifted. The
generated docs regenerate byte-identical. The generators are deterministic and reproduce the
committed data exactly. The holiday calendar agrees three ways and recomputes. `plan.json`
validates completely. **I would rely on this layer.** The two errors found in it this pass —
one invented enum value and one wrong endpoint attribution — were both in the same hand-written
table, which is the part of this layer that is *not* machine-generated. That is where the
remaining risk is concentrated.

**The behavioural layer** is unchanged: still hypothesis, still not one observed response.
What moved is that it is now hypothesis stated by three artefacts instead of two, which
reduces the chance of a transcription error and does nothing about the chance that the
documentation is simply wrong about the running system. The spend headers the mock emits are
still invented. One item did leave this bucket without a live call — `sti` — but by reading
the ingestion pipeline, which is a different kind of evidence, not a stronger kind of
documentation.

**The code layer** was over-certified again. Pass 3 said plainly that "exercised" in earlier
records had meant *sampled*, fixed six defects, and then verified its own paging loop on the
happy path only. Two of the four code defects found this pass are in that loop's failure path,
and one of them — a mid-sweep stop silently reporting zero spend while fifteen credits had
actually been billed — is precisely the class of error this whole corpus exists to prevent.
The third, that any unbilled failure permanently deleted a call from the plan, predates pass 3
and survived three audits that each called `capture.py` verified. All four are fixed and
re-verified end to end against the mock, including the resume path, which now costs 32 credits
for a 32-page sweep interrupted at page 15 instead of 47. **The lesson has not changed since
pass 3, only its target: happy paths get tested, failure paths do not.** If a fifth pass runs,
the failure paths in `mock_server.py` and `synth_extended.py` are where I would look.

**The time-sensitive layer** is where this pass found the most consequential errors, and not
the ones I expected. The matching-board *count* did not move at all — three independent
counting methods reproduce pass 3's 48 / 15-7-12 exactly, which only means both passes ran on
the same day and says nothing about 22 September. What moved was the board's *text*, which
pass 3 did not re-read: two of the dossier's named strategic advantages ("nobody is competing
for video skill", "the broker-cohort play will not be duplicated") were falsified inside 24
hours by two new recruiting notes and one team's one-line project description. A count is easy
to re-verify and a conclusion drawn from prose is not, so the prose is what goes stale
unnoticed. The Slack invite expiring around 20 September is the other time-sensitive item, and
it was not in the dossier at all.

**On the clean-sweep question.** Fourteen corrections, six of them substantive: the
297-vs-271 arithmetic, the fabricated provenance quotation, the two falsified competitive
claims, and the two `capture.py` failure-path defects. Six sections came through genuinely
clean, and I want to name them rather than manufacture findings in them:

- **The generated docs and the endpoint census** — 70 GET, byte-identical regeneration, every spec template referenced in prose and every prose path resolving.
- **The screener field extraction** — 219 and 85, exact in both directions, all six IDX and all four SGX category subtotals matching, plus the 20/10 coverage-marker split.
- **The holiday calendar** — 22 dates identical across three places, 239 trading days and all twelve per-month counts independently recomputed.
- **The hackathon rules** — re-read in full and hash-diffed against the capture, unchanged to the sentence.
- **`plan.json`** — 87/87 paths, zero invalid parameters, zero enum violations, zero out-of-range values, totals correct.
- **The generators** — deterministic across runs and byte-identical to the committed output.

Four of those six were also clean in pass 3, which is what you would expect of
machine-generated material checked by machine. Every error found in four consecutive audits has
been in hand-written prose, hand-maintained tables, or code failure paths. That is a pattern,
and it is the most useful thing this pass can hand to a fifth: **stop re-checking the
generated artefacts and go straight to the sentences somebody typed.**

The highest-value next step is unchanged and now cheaper to rehearse: claim the credits, run
`capture.py --tier 0`, and reconcile the declared cost model against the real ledger and the
real header names. Everything in §3 turns on that one 5-credit call.
