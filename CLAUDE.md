# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A research dossier and offline data harness for the **Sectors Hackathon 2026** (Supertype /
Sectors / Algoritma). There is **no product code yet** — `research/` holds the competition
research, the Sectors API reference, and a standard-library Python harness whose whole purpose
is to let the product be built without spending API credits.

The team grant is **1,000 credits, non-transferable, no top-up, expiring at the end of the
event**. **377 were charged to the grant** — 265 by `capture.py` on the 6 Sep 2026 live capture plus
112 by traffic outside it, per the portal usage log (`reconcile_usage.py`) — so roughly
**623 remain**. Iteration —
not the demo — is what burns them. Everything in `research/harness/` exists so that
development happens against local recordings and a live call is made at most once.

## Commands

All Python is standard library only. No venv, no pip install, no build step.

```bash
python3 research/harness/src/sectors_env.py          # preflight: env path, base URL, budget, key set/missing
```

```bash
cd research/harness && python3 src/mock_server.py --port 8787 --credits 1000
```

```bash
cd research/harness && python3 src/verify_mock.py     # mock-vs-captured-API parity; exit 0/1, zero credits
```

```bash
cd research/harness && python3 src/capture.py --plan plans/plan.json --dry-run
```

Key `capture.py` flags: `--tier N` (repeatable, selects plan tiers), `--budget N` (hard cap,
default from `SECTORS_BUDGET`), `--only SUBSTR`, `--report` (what has been spent),
`--base-url`. Point it at the mock to rehearse a plan for free:

```bash
cd research/harness && SECTORS_BASE_URL=http://127.0.0.1:8787 python3 src/capture.py --plan plans/plan.json --budget 300
```

Regenerating data and generated docs:

```bash
cd research/harness && python3 src/extract_fixtures.py                      # fixtures/ from ../../evidence/spec/schema.json
cd research/harness && python3 src/synth_universe.py --companies 300 --days 180 && python3 src/synth_extended.py
cd research && python3 tools/gen_endpoint_ref.py                    # writes docs/api/02-endpoint-reference.md
cd research && python3 tools/gen_response_shapes.py                 # writes docs/api/07-response-shapes.md
cd research/harness && python3 src/reconcile_usage.py                       # ledger vs portal usage-log CSVs; exit 1 on disagreement
```

`gen_*.py` must run with `research/` as the working directory — their paths are relative to it.
`synth_extended.py` reads `synth/market/companies.json`, so `synth_universe.py` runs first.

## Configuration

One git-ignored `.env` at the repository root, read by `research/harness/src/sectors_env.py`,
which every script imports instead of touching `os.environ` directly. It walks up from its own
directory to find the nearest `.env` and **never overwrites a variable already set in the
shell**, so a real env var always wins — that is how one-off overrides and CI work.

`SECTORS_API_KEY` (raw `Authorization` value, no `Bearer ` prefix) · `SECTORS_BASE_URL`
(default `https://api.sectors.app`; set to the mock to spend nothing) · `SECTORS_BUDGET`
(default 250). Also read by `capture.py`: `SECTORS_RATE_LIMIT_SLEEP`, `SECTORS_USER_AGENT`.

Never print, log, or persist the key. `sectors_env.dotenv_path()` exposes the path only.

## Architecture

**Three data layers, in descending fidelity.** Build against the highest one that has what you
need; drop down only for volume.

1. `recorded/` — real payloads captured from the live API on 6 Sep 2026. 66 of 66 callable
   endpoints. **Committed on purpose** (they were paid for in credits and contain no key), so
   the second person to need a call gets it free.
2. `fixtures/` — the OpenAPI spec's own example response for each of the 70 documented
   operations, extracted by `extract_fixtures.py`. Exact shapes, one example each.
3. `synth/` — `synth_universe.py` (~22 endpoints: screener rows, daily prices, broker summary,
   foreign flow, news) plus `synth_extended.py` (mining, banking LAR, suspensions, corporate
   actions, shareholder panels, filings, segments, quarterly financials, index series, the real
   IDX 2026 holiday calendar). Deterministic per `--seed`. Unlimited volume, not real.

**`mock_server.py`** serves layer 1 in preference to layer 2 (`X-Mock-Source: recording`) and
emulates the failure modes that otherwise only appear in production: `Authorization` required,
a credit meter using each endpoint's own per-section / per-classification×period / per-quarter
formula, `402 insufficient_credits`, `410 Gone` on `/v1/*`, path templating, `GET /__usage`,
`--chaos` (429/503 with the real, *differing* body shapes), `--latency-ms`, `--rate-limit`, and
a **billed 404** for `--unknown` symbols. Point any client at it by changing one base URL.

**`capture.py`** is the only thing that should ever call the live API. Its safety properties
are the design, not incidental: idempotent *for calls that settled* (a 2xx or a 404 is skipped
on re-run; an unbilled 402/400/exhausted-retry/network error is retried), a hard budget cap, a
dry run, a `recorded/_ledger.jsonl` append-only spend log, resumable paginated sweeps that keep
pages already paid for, and a `RateWindow` that models the real limiter (see below).

**The plans.** `plan.json` — 87 calls in 5 tiers, every parameter constrained, 176 credits.
`plan-live.json` is *generated* by `plan_live.py`, which reads path parameters (broker codes,
mining slugs, SGX symbols) out of payloads already on disk rather than inventing them, because
a guessed identifier costs a credit. `plan-probe*.json` are free failure probes;
`plan-fidelity.json` buys the expensive defaulted forms once.

**Generated documentation.** `research/docs/api/02-endpoint-reference.md` and
`07-response-shapes.md` are produced by `research/tools/`. Edit the generator, not the
markdown. `research/evidence/` is the provenance store — verbatim captures, `schema.json`
(OpenAPI 3.0.3), `llms-full.txt`, and the committed portal `usage-log/` CSVs that are the only
independent record of what was actually charged.

## Rules that protect the grant

- **Never make an ad-hoc live call.** `curl` and one-off scripts pay again every time;
  `capture.py` pays once and records. Rehearse every plan against the mock first.
- **Never call an identifier that did not come back in an earlier response.** A 404 bills
  1 credit — the lookup ran.
- **Never let `sections`, `classifications`, `periods` or `n_quarters` default.** A defaulted
  company report costs 8 instead of 1; defaulted top-changes costs 10 instead of 1.
- **Run a natural-language screener `?q=` at most once** (3 credits vs 1). Read
  `llm_translation` out of the response and hardcode the `where`/`order_by` it produced.
- Delete anything a mock rehearsal wrote to `recorded/` before going live, so synthetic
  payloads are never mistaken for real ones. Commit new recordings with their ledger entry.

## API behaviour learned the hard way (see `research/audit/VERIFICATION-LIVE.md`)

- **Cloudflare blocks `Python-urllib` outright** — `403 {"error": "error code: 1010"}`, which
  says nothing about user agents. Any client needs a browser `User-Agent`.
- **Rate limit is 25 *billed* requests per rolling ~30 s**, not a spacing rule. Free responses
  (400s) are not counted, so parameter probing is unlimited. No `Retry-After` is ever sent, and
  retrying into a 429 extends the lockout — wait the window out.
- **The surface is 66 endpoints, not 70.** `/v2/company/report/`, `/v2/subsector/report/`,
  `/v2/sgx/company/report/`, `/v2/klse/company/report/` are duplicate spec entries with no path
  template; called bare they return a free 400.
- **`/v2/financials/quarterly/{symbol}/` is sector-dependent.** Banks return
  `realized_capital_goods_investment`; everyone else returns `capital_expenditure` in that slot.
  A parser written against the spec example silently drops capex for the whole non-bank market.
- **`/v2/listing-performance/{symbol}/` only covers tickers listed after May 2005** — every IDX
  blue chip 404s, at 1 credit each.
- **SGX/KLSE `top` endpoints use a different `classifications` vocabulary** than IDX
  (`dividend_yield|revenue|earnings|market_cap|pe`, not `top_gainers|top_losers`).
- **Only 9 of 366 mining companies have detail records** — filter with `?has_financials=true`.
- **The screener returns only `symbol` and `company_name`.** 219 fields are filterable but not
  returned; pass `include_query_values=true` and name the metrics in `where`.
- Known mock divergences (documented in `research/harness/README.md`): it does not validate
  enums, does not slice responses by `sections`, and under-bills `/v2/free-float/` — the source
  of the 176-vs-167 gap on a full-plan rehearsal.

## Hackathon constraints that bind the build

- Sectors MCP or REST API must be a **core** data source — remove it and the product must stop
  working. **Never ship synthetic data as the product's data source**, and label it on screen if
  it appears in the video.
- Automated trade execution is banned in every track.
- The repo must have been created on or after 19 Aug 2026, with `.env` git-ignored from commit
  #1. Registration closes 22 Sep 2026; submissions 30 Sep 2026 (both 23:59 WIB).
- Judging is fully asynchronous from the repo and video: real-world usability 40%, video and
  storytelling 30%, technical depth 30%.

## Layout and reading order

```
research/
  docs/hackathon/     rules, tracks, submission checklist
  docs/api/           the Sectors API in depth — 16 reference docs
  harness/
    src/              the 10 scripts — run them from harness/ as `python3 src/<name>.py`
    plans/            plan.json (87 calls / 176 credits) + the probe and fidelity plans
    fixtures/         one OpenAPI example per endpoint, split idx/ sgx/ klse/ mining/
    recorded/         real payloads + _ledger.jsonl + _manifest.json (flat: keyed by
                      call slug via _manifest.json — a cache, not a browsable tree)
    synth/            generated universe, split market/ flow/ company/ mining/
  plan/               build ideas, competitive landscape, what is already published
  evidence/
    spec/             schema.json, llms.txt, llms-full.txt, postman/
    hackathon/        captures of the hackathon site
    sectors/          captures of the Sectors product, docs and agent skills
    subdomains/       mining/reits sweeps and footer crawls
    rechecks/         the live re-check notes behind the audit reports
    usage-log/        portal CSV exports — what the API actually charged
  audit/              six verification passes + the prompts that drove them
  tools/              generators for the two generated docs in docs/api/
```

`research/README.md` is the index and states the facts that shape every decision.
`SETUP.md` is the five-minute team onboarding. `research/audit/VERIFICATION-LIVE.md` is the
record of the only pass that actually called the API — it supersedes documentation-only claims
in the earlier passes, and `research/audit/README.md` states the pass order.
