# Fetch Strategy — Spend Once, Develop Forever

> The grant is **1,000 credits with no top-up**. What burns credits is *iteration*, not the
> demo. This is the plan that keeps iteration free.

## The rule

**Every live call is made at most once, recorded to disk, and replayed from then on.**

```
plan  →  capture once  →  replay forever
```

Three files implement it, all in [`../03-mock-data/`](../03-mock-data/):

| File | Job |
| --- | --- |
| `plan.json` | 87 calls in 5 tiers, every parameter constrained on purpose. **176 credits total.** |
| `capture.py` | Runs the plan against the live API. Idempotent, budget-capped, rate-limited, ledgered. |
| `mock_server.py` | Serves the recordings back at `localhost`, falling back to spec examples for anything not yet captured. |

---

## Before anything: you cannot call the API yet

Verified on a live free account — API Key Management says *"Please upgrade your subscription
to access Sectors API."* API access arrives only via the **Insider plan** or the **hackathon's
1,000-credit grant**, which requires the team registered and every member onboarded.

So the honest sequence is:

1. Build against the mock and synthetic data — **starting now, at zero cost**
2. Team registers, everyone onboards, credits claimed
3. Run `capture.py --tier 0` and reconcile the cost model against reality
4. Run the remaining tiers
5. Go back to developing against recordings

---

## The tiers

Stop after any tier. Each is independently useful.

| Tier | What | Credits | Why |
| --- | --- | --- | --- |
| **0** | Taxonomy + broker registry | **5** | Every later call validates its slugs against these. Run first, always. |
| **1** | Screener pulls, market state, an 8-name basket | **28** | Enough real data to build most projects end to end. |
| **2** | Full-universe sweeps (free float, all closes, all quarterly dates) | **74** | Breadth. Only if your project needs the whole market. |
| **3** | Broker flow, quarterly financials, segments, corporate actions, ownership | **55** | The differentiated data — where the unusual project ideas live. |
| **4** | Mining, SGX, KLSE | **14** | Cheapest tier, zero recipes exist for any of it. |
| | **Total** | **176** | Leaves **824** for development, evaluation and the demo. |

```bash
python3 capture.py --base-url http://localhost:8787 --tier 0   # full rehearsal, 0 credits
python3 capture.py --dry-run                  # cost it, call nothing
python3 capture.py --tier 0                   # 5 credits, reconcile the model
python3 capture.py --tier 0 --tier 1          # 33 credits, enough to build
python3 capture.py --budget 200               # everything, hard-capped
python3 capture.py --report                   # what has actually been spent
```

---

## Why 176 and not 271

Every parameter in the plan is constrained deliberately. The same 87 calls with defaults would
cost **271 credits — 54% more**:

| Call | Default | In the plan | Saved |
| --- | --- | --- | --- |
| `company/report` × 8 | 8 sections = **64** | `sections=overview` = **8** | 56 |
| `top-changes` × 2 | 2 class × 5 periods = **20** | 1 class × 1 period = **2** | 18 |
| `subsector/report` × 3 | 6 sections = **18** | `sections=statistics` = **3** | 15 |
| `financials/quarterly` × 4 | unbounded | `n_quarters=4` = **16** | — |
| Screener × 3 | `?q=` = 9 | structured `where` = **3** | 6 |

**95 credits saved on 87 calls**, purely from not letting parameters default — 176 against
a 271-credit default run. (An earlier draft called this "roughly three times"; the table's own
arithmetic does not support that. `financials/quarterly` is excluded from the total because the
spec documents no default for `n_quarters`, so its default cost is genuinely unknown.)

Also constrained: `top-changes` passes `min_mcap_billion=0`, because the default of 5000
silently hides every company under IDR 5 trillion — a correctness fix, not just a cost one.

---

## What `capture.py` guarantees

| Property | Why it saves money |
| --- | --- |
| **Idempotent** | A recorded call is skipped. Crash halfway through, re-run, pay nothing for what succeeded. |
| **Hard budget cap** | Refuses to start a call that would exceed `--budget`. Default 250. |
| **Dry run** | Full plan with cumulative cost, calls nothing. |
| **404s recorded** | A 404 costs 1 credit. It is written to the manifest as a negative result so the same bad symbol is never paid for twice. |
| **Retries only what is free** | 429 and 5xx are unbilled, so they back off and retry. 4xx do not. |
| **0.35 s between calls** | Above the 0.3 s the docs call mandatory past ~10 sequential calls. |
| **Paginates the full-universe sweeps** | A plan entry may carry `"pages": 32`; `capture.py` walks every `offset` and merges the pages into one recording. Without this the two tier-2 sweeps would bill for 32 pages and record one. |
| **`--base-url`** | Point the whole harness at `mock_server.py` and rehearse the entire run for zero credits before spending anything. Also honours `SECTORS_BASE_URL`. |
| **Ledger** | Every attempt appended to `recorded/_ledger.jsonl` with status, estimated cost, and any cost header the API returned. |

### The header reconciliation step

The OpenAPI spec documents **no** spend headers — the `X-Credits-Charged` header the mock
emits is invented. `capture.py` records **any** response header matching
`credit|quota|rate.?limit|usage|balance`, so **tier 0 tells you what they are actually
called**, for 5 credits.

Do that before running the expensive tiers, and reconcile `est_cost` in the ledger against
whatever the API really reports. If the model is wrong, fix `plan.json` before tier 2 spends 74.

---

## Replay

Once anything is captured, the mock prefers it:

```
$ python3 mock_server.py --port 8787
Sectors mock API on http://127.0.0.1:8787
  70 endpoints · 1000 simulated credits
  33 real recordings replayed (rest fall back to spec examples)
```

Every response carries `X-Mock-Source: recording` or `spec-example`, so you always know
whether you are looking at real data or a documented shape.

```bash
SECTORS_BASE_URL=http://localhost:8787 python3 app.py   # free, real payloads
```

**Recordings beat spec examples** because they are what the API actually returned — including
fields the documentation omits and nulls the examples do not show. A parser built against a
recording cannot be surprised in the demo.

---

## Three layers, and when to use each

| Layer | Fidelity | Volume | Cost | Use for |
| --- | --- | --- | --- | --- |
| **Recordings** (`capture.py`) | **Real** | Small — what you captured | 176 once | Correctness. Parsers, field names, nulls, edge cases. |
| **Spec fixtures** | Documented shape | 1 per endpoint | Free | Endpoints you haven't captured. Wiring, 404/402 handling. |
| **Synthetic** (`synth_*.py`) | Plausible | Unlimited | Free | Volume. Screener logic, backtests, anomaly detection, load tests, charts. |

The workflow that uses all three:

1. **Now** — build against fixtures + synthetic. Costs nothing, needs no account.
2. **After credits** — `capture.py --tier 0`, reconcile, then tiers 1–4. 176 credits.
3. **Rest of the build** — develop against recordings. Free.
4. **Demo day** — one fresh live pull of only what must be current. Budget ~50.
5. **Fallback** — keep the mock running; if the live API rate-limits mid-recording, flip one environment variable.

---

## Rules that survive contact with a deadline

1. **Never let `sections`, `classifications`, `periods` default.** Three endpoints bill per item and default to all of them.
2. **Never call `?q=` twice with the same shape.** 3 credits vs 1. Run it once, read `llm_translation` out of the response, hardcode the structured form.
3. **Validate symbols against a cached list before looping.** A 404 costs a credit.
4. **Use `is not null` server-side** rather than fetching and filtering locally.
5. **Poll with `?since=`**, never re-sweep. A full quarterly-dates sweep is 32 credits; the incremental poll is a fraction.
6. **Cache with a real TTL.** Taxonomy forever; reports until the next filing; prices until the next close.
7. **Watch the ledger, not your memory.** `capture.py --report` is the truth.

---

## If the cost model turns out wrong

The per-call costs in `plan.json` are the spec's **declared** costs. They have never been
observed. Tier 0 is deliberately tiny so that discovering a discrepancy costs 5 credits rather
than 74. If reality differs:

```bash
python3 capture.py --report      # compare est_cost against observed cost headers
```

Then edit `est_cost` in `plan.json` and re-run `--dry-run` before spending anything else.
