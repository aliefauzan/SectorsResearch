# Live Verification Pass — First Contact With the Real API

The corpus in `research/` has been audited five times without a single `/v2/*` call. Every
claim about *structure* (paths, parameters, enums, declared costs, response schemas) rests on
`99-raw/schema.json`, the public Postman collection, `llms-full.txt`, and the `sectors-mcp`
copy of the spec. Every claim about *behaviour* — what the API actually charges, what headers
it returns, what a 429 looks like, whether a documented default is the real default — rests on
nothing but the documentation's own word.

Credits now exist. **1,000, non-transferable, expiring when the event ends.** This pass turns
the "unverifiable-until-live" ledger into evidence, and does it without burning the grant.

Your deliverable is `research/VERIFICATION-LIVE.md` plus a raw evidence file and the recorded
payloads. Your constraint is that the build still needs credits after you are done.

---

## Hard constraints

- **Budget ceiling for this entire pass: 300 credits.** Not 301. If a check would push past
  it, stop and mark the remainder unverified rather than spending. At least 700 credits must
  survive for development and demo day.
- **Never read, echo, log, or write the API key.** It comes from `SECTORS_API_KEY`, set in
  the git-ignored `.env` at the repository root or exported in the shell. `capture.py`
  refuses to run without it and never persists it — do not add code paths that print headers
  verbatim, and never paste the key into this report, a commit, or an issue.
- **Every live call goes through `research/03-mock-data/capture.py`.** No ad-hoc `curl`, no
  one-off `requests.get` in a scratch file. The ledger is the audit trail; a call that is not
  in `recorded/_ledger.jsonl` did not happen as far as this report is concerned. If you need a
  call the plan does not have, *add it to a plan file* and run it through the tool.
- **Never call a symbol, slug, or code that did not appear in a tier-0 or tier-1 response.**
  A 404 is billed 1 credit. Guessing tickers is how you lose the grant one credit at a time.
- **Do not let `sections`, `classifications`, `periods`, or `n_quarters` default.** Defaults
  bill per item: a defaulted company report is 8 credits, defaulted top-changes is 10.
- Do not register a team, sign in to the hackathon portal, create an account, or join
  Discord/Slack. Reading pages already authenticated in the user's browser is fine.
- 429 and 5xx are free. 400 is free *except* a `?q=` screener 400 that fails after the model
  ran, which bills 1. Retrying a free failure is safe; retrying a 404 is not.
- Sleep 0.3s between sequential calls. The docs claim >~10 rapid sequential calls produces
  429s — that claim is itself one of the things to test, but test it deliberately, not by
  accident inside a paid sweep.

---

## Start here — the sequence, in order

Each phase gates the next. Do not run phase N+1 until phase N's reconciliation is written down.

### Phase 0 — cost the plan, call nothing (0 credits)

```bash
cp .env.example .env            # then paste the team key into SECTORS_API_KEY=
cd research/03-mock-data
python3 capture.py --plan plan.json --dry-run
```

`.env` lives at the repository root, is git-ignored, and is loaded automatically by
`capture.py`; a shell variable still overrides it. Full team setup: `SETUP.md`.

Confirm the printed total matches the corpus: **176 declared credits across 87 calls** —
tier 0: 5 calls / 5 credits · tier 1: 28 / 28 · tier 2: 3 / 74 · tier 3: 37 / 55 ·
tier 4: 14 / 14. If the tool prints anything else, the discrepancy is a finding before you
have spent a credit.

Then verify the tool against the mock one more time, since you are about to point it at
something that charges money:

```bash
python3 mock_server.py --port 8787 &
SECTORS_BASE_URL=http://127.0.0.1:8787 python3 capture.py --plan plan.json --budget 300
```

Confirm idempotency, the budget cap, the 404 skip, and the pagination merge all behave.
Then **delete the mock recordings** so real payloads cannot be confused with synthetic ones.

### Phase 1 — tier 0, then stop and reconcile (5 credits)

```bash
python3 capture.py --plan plan.json --tier 0 --budget 5
```

Five helper lists. Before running anything else, settle these, because everything downstream
depends on them:

1. **What are the real spend headers?** The corpus says the mock emits `X-Credits-Charged`
   and `X-Credits-Remaining` and explicitly flags that the live names are undocumented. Dump
   the response header *names* (names only, no values that could contain the key) from a
   tier-0 response and write down the truth. If the API returns no spend header at all, that
   is a significant finding: it means the ledger's `charged` field is unverifiable and every
   cost claim in the corpus can only be checked by differencing a balance.
2. **Is there a balance endpoint or a portal balance page?** If a remaining-credit figure is
   readable anywhere, capture it now — it is your ground truth for every later reconciliation.
3. **Did five 1-credit calls cost exactly five credits?** Difference the balance. If not, the
   entire declared-cost table is suspect and you should stop and report rather than continue.
4. **Do the taxonomy slugs match the corpus?** Subsectors, industries, subindustries, tags.
   The generated docs and `plan.json` both encode these; a drift here invalidates later calls.

Write the reconciliation into the evidence file before proceeding.

### Phase 2 — tier 1, the core surface (28 credits, running total 33)

```bash
python3 capture.py --plan plan.json --tier 1 --budget 40
```

Reconcile again: declared 28 versus balance delta. Any per-call divergence is a correction to
`02-sectors-platform/05-credit-budget.md` and to the mock's cost model.

### Phase 3 — the pricing experiments (~35 credits, running total ~68)

These are the claims the corpus most wants settled, and each is cheap if run deliberately.
Run each as a *single* call, log the delta, and never repeat it.

| Claim to settle | Probe | Declared |
| --- | --- | --- |
| Constrained report is 1, defaulted is 8 | `company/report/BBCA/?sections=overview` then, only if budget allows, the defaulted call | 1 vs 8 |
| Report `sections` slicing | Does a 2-section call bill 2? | 2 |
| Top-changes constrained | `classifications=top_gainers&periods=1d` | 1 vs 10 default |
| `min_mcap_billion` default of 5000 | Compare constrained vs explicit `min_mcap_billion=0` result counts | correctness bug claim |
| Natural-language screener is 3× | one `?q=` call; read `llm_translation` out of the body and record it | 3 vs 1 |
| A `?q=` 400 after the model runs bills 1 | deliberately malformed `?q=` | 1 |
| A plain 400 is free | bad enum value on any endpoint | 0 |
| A 404 bills 1 | one unknown-but-plausible slug, **exactly one** | 1 |
| Free float bills per 100 companies | one bounded call | 1 per 100 |
| Quarterly financials bills per quarter | `n_quarters=2` | 2 |
| Pagination default is `limit=20` not 30 | one `/v2/close/` page, read the page size and `has_next` shape | affects the 297-credit sweep arithmetic |

The mock's three known divergences from the spec are the priority: enum errors billed instead
of 400-free, reports not sliced by `sections`, free-float flat-billed. Settle all three.

### Phase 4 — the 30 endpoints `plan.json` never touches (~35 credits, running total ~103)

`plan.json` covers **40 of the 70 documented endpoints**. These 30 have never been called by
anyone, and their response shapes in `07-response-shapes.md` come from the spec's declared
examples alone:

```
/v2/broker-activity/{broker_code}/            /v2/mining/companies/{slug}/
/v2/broker-activity/{broker_code}/top/        /v2/mining/companies/financials/{slug}/
/v2/broker-summary/{symbol}/                  /v2/mining/companies/ownership/{slug}/
/v2/companies/list_companies_with_segments/   /v2/mining/companies/performance/{slug}/
/v2/company/get_quarterly_financial_dates/{symbol}/   /v2/mining/global-commodity/
/v2/company/report/                           /v2/mining/license-auctions/{wiup_code}/
/v2/subsector/report/                         /v2/mining/resources-reserves/{province}/
/v2/klse/companies/                           /v2/mining/sales-destination/{slug}/
/v2/klse/companies/top/                       /v2/mining/sites/{slug}/
/v2/klse/company/report/                      /v2/sgx/buybacks/
/v2/klse/company/report/{symbol}/             /v2/sgx/companies/top/
/v2/sgx/subsectors/                           /v2/sgx/company/report/
/v2/sgx/tags/                                 /v2/sgx/company/report/{symbol}/
/v2/sgx/filings/                              /v2/sgx/daily/{symbol}/
/v2/sgx/news/                                 /v2/sgx/short-sell/
```

Write these into `plan-live.json` as a new tier, **one cheapest-possible constrained call
each**, sourcing every path parameter from a payload already on disk. Priorities, if the
budget forces a subset: the four bare `report/` roots (they are the undocumented "list" form),
the KLSE and SGX report pairs (the corpus's coverage claims in `09-sgx-klse-coverage.md` rest
entirely on the spec), and the mining `{slug}` family (nine endpoints, one shape claim).

For each, record: HTTP status, actual credit delta versus declared, top-level response keys
versus `07-response-shapes.md`, and any field the spec does not document.

### Phase 5 — behaviour the docs assert and never demonstrate (~20 credits, running total ~125)

- **Rate limiting.** The spec declares 429 on all 70 endpoints and publishes no number. Find
  the number: burst the cheapest 1-credit helper list until you get a 429, note the count, the
  window, and whether `Retry-After` is present. 429s are free — this experiment costs only the
  successful calls before the first 429. Cap it at 25 successes.
- **`?since=` on quarterly-financial-dates.** The corpus claims it makes repeat polls cheap.
  Two calls, one bounded by `since`, compare payload size and cost.
- **The 17 index codes.** Call `/v2/index-daily/{code}/` for a *documented* code, then settle
  the two open questions: does `sti` resolve (pass 4 inferred it from an ingestion table name),
  and does the undocumented `klse` resolve (found in the same registry, absent from the spec)?
  Two calls. A 404 on either bills 1 and is itself the answer.
- **Screener operators, especially `is null`.** `03-screener-query-language.md` marks `is null`
  as resting on no source at all. One structured screener call settles it — 1 credit.
- **Idempotency of a repeated identical call.** Does the API bill twice for the same query
  inside a short window, or is there server-side caching? One repeat of any 1-credit call.

### Phase 6 — the rest of the plan, only if the budget holds (143 credits, total ~268)

Tiers 2, 3, and 4 are the bulk recording that development will replay against. Run them only
after the cost model has been confirmed by phases 1–3, and re-cost them first: if phase 3
proves any declared cost wrong, the 176-credit estimate is wrong too.

```bash
python3 capture.py --plan plan.json --tier 2 --tier 3 --tier 4 --budget 150
```

If the reconciled arithmetic would breach the 300-credit ceiling, drop tier 2 (74 credits, 3
calls — the universe sweeps) and record the decision. Tier 2 is the most replaceable: the
synthetic generators in `03-mock-data/` can stand in for a full universe sweep, and no other
tier can.

---

## What counts as a finding

Rank by consequence, not by how interesting the discovery was:

1. **A declared cost that is wrong.** Every credit-budget number, the mock's cost model, and
   `plan.json`'s estimate all inherit from the spec's cost sentences. One wrong sentence
   propagates to four files.
2. **A response shape that differs from `07-response-shapes.md`.** That document is generated
   from the spec's declared examples; the live payload is the authority. Note added fields,
   missing fields, and type differences separately — an undocumented field is an opportunity,
   a missing documented field is a bug in the build plan.
3. **A parameter that does not behave as documented** — a default that is not the declared
   default, an enum value the API rejects, a range limit enforced differently.
4. **Anything that makes a documented endpoint unusable** — permanent 5xx, an empty dataset, a
   coverage claim (SGX/KLSE/mining) that returns nothing for the whole market.
5. **Header, rate-limit, and error-body facts** that no document currently records.

For each finding: the claim as written and where, the observed behaviour, the ledger line
proving it, and the fix applied to the corpus.

---

## Reporting

Write `research/VERIFICATION-LIVE.md`. Save raw captures to
`research/99-raw/live-recheck-<date>.md`, keep the payloads under
`research/03-mock-data/recorded/`, and add a row to the audit section of `research/README.md`.

Structure:

- **Ledger reconciliation** — declared versus actual, per phase and in total, with the closing
  balance. This is the first section, because it is the one number the team needs.
- **Corrections made** — with the primary evidence (a ledger line, a payload path).
- **Confirmed** — the claims that survived contact, and the call that confirmed each.
- **Still unverified** — what you deliberately did not spend on, and what it would cost to
  settle later.
- **New material** — undocumented fields, headers, limits, and endpoints that behave
  differently from their documentation.
- **Credits remaining**, stated plainly, and whether that is enough for the build as planned in
  `04-build-plan/`.

Update the mock to match reality: `mock_server.py`'s cost model and any fixture whose shape is
now known to be wrong. The mock is what development runs against — a mock that disagrees with
the live API is worse than no mock. Re-run `extract_fixtures.py` against the new recordings so
the fixtures are real payloads rather than spec examples.

End with the honest bottom line: after five offline audits and one live pass, what fraction of
this corpus is now evidence-backed, broken out by layer — structural, behavioural, cost, code,
time-sensitive — and what remains inference.
