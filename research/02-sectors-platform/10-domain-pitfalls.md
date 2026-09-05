# Domain Pitfalls — From the Organizers' Own Recipes

> Fifth-pass finding. Sectors' documentation contains fully worked multi-part projects written
> by Supertype engineers — the same organization judging this hackathon. Buried in them are
> **explicit warnings about mistakes they have seen people make** with this data.
>
> These are worth more than they look. They are the failure modes the judges already know
> about, so hitting one is visible; avoiding one visibly is evidence of depth.

---

## 1. The zero-sum trap (broker data)

**This one will silently break any bandarmology project.** Quoted from the GNN anomaly-detection
recipe, part 3:

> "The most common mistake when working with this endpoint is to compute a net total by
> summing all buyer net values and adding them to all seller net values."

```python
# WRONG: always produces a result near zero
total = sum(b["net_idr"] for b in buyers) + sum(s["net_idr"] for s in sellers)
```

Why: equity markets are zero-sum. For every buyer there is a seller. The top 10 buyers and
top 10 sellers of any stock roughly cancel when summed — **the result is near zero regardless
of the actual market dynamics.** Your signal looks flat and you conclude nothing is happening.

The recipe's fix is a **dominance score** — largest accumulator against largest distributor:

```python
# CORRECT: dominance score
top_buy_net  = buyers[0].get("net_idr", 0)    # positive: net bought
top_sell_net = sellers[0].get("net_idr", 0)   # negative: net sold (API returns negative)
net_dominance = top_buy_net + top_sell_net    # positive = accumulation dominant
```

Positive means the biggest buyer is accumulating more than the biggest seller is distributing.
Negative means distribution is outpacing accumulation.

> Note the sign convention: **`net_idr` is already negative for sellers**, so the dominance
> score *adds* rather than subtracts. Getting this backwards inverts your entire signal.

If you build the accumulation-detector idea from
[`../04-build-plan/what-we-can-build.md`](../04-build-plan/what-we-can-build.md), this is the
single most important paragraph in this dossier for you.

---

## 2. Zero-feature stocks are suspended stocks

The recipe audits for companies whose every computed feature is exactly zero:

```python
zero_mask = (result_df[numeric_feat_cols] == 0).all(axis=1)
```

> "Likely cause: stock suspended on IDX during {START_DATE} to {END_DATE}"

IDX suspends stocks reasonably often, and a suspended stock returns a valid, well-formed,
**all-zero** series rather than an error. Feed that into a scoring model and it will look like
an extreme outlier — or cluster with other zero rows and drag your thresholds around.

**Audit for all-zero rows and drop them before scoring.** Cross-check against
`/v2/suspensions/` (1 credit) to confirm why, and you get a free explanatory sentence for your
demo at the same time.

---

## 3. Duplicated scores mean duplicated rows

```python
score_counts = result_df["anomaly_score"].value_counts()
duplicated = score_counts[score_counts > 1]
```

Identical floating-point scores across different tickers essentially never happen by chance.
When they do, it means duplicated or corrupted rows upstream — usually a join that fanned out.
Cheap assertion, catches a whole class of silent data bugs.

---

## 4. `.map()`, not `.merge()`, for signal injection

From the recipe's "Common Errors and Fixes":

> "NaN in combined_risk_score. Usually caused by running `.merge()` on a DataFrame that
> already has the column from a previous run. pandas does not overwrite existing columns on
> merge; it creates `column_x` and `column_y` variants."

```python
# Correct approach: always use .map() not .merge() for signal injection
confirm_df["broker_net_total"] = confirm_df["ticker"].map(
    broker_result_all_df.set_index("ticker")["broker_net_total"]
)
```

This bites specifically in notebook workflows where you re-run a cell. Your column silently
becomes `broker_net_total_x` / `_y`, the original name resolves to NaN, and every downstream
score is NaN. Very easy to lose an hour to on deadline day.

---

## 5. Sleep between sequential calls

Repeated from [`01-api-guide.md`](01-api-guide.md) because the recipe is emphatic:

> "The `sleep(0.3)` in the Fetch Data section is not optional if you expand the universe
> beyond 10 banks. Omitting it on the free/Insider tier will result in 429 Too Many Requests
> errors."

The OpenAPI spec declares `429` on **all 70 endpoints**. Rate limiting is universal, the
numeric limit is unpublished. The 0.3 s sleep is documented; ~3 requests/second is the
implication drawn from it, not a published limit.

---

## 6. Interpret composite scores directionally

The recipe attaches a warning to its own output:

> "Combined scores should be interpreted directionally, not as precise probabilities. The
> weights (50/25/25) are a reasonable default but can be adjusted based on your investment
> thesis."

Two things to take from this. First, **stating your weights and calling them a choice is the
expected standard**, not a weakness — the organizers do it in their own published work.
Second, it keeps you the right side of the code-of-conduct rule that projects must not
provide financial advice: a directional score with disclosed weights is analysis, a
probability is a claim.

The recipe also demonstrates the point honestly — BBCA ranked first on combined risk despite
*not* clearing the anomaly threshold, purely because its foreign outflow was the largest in
the universe. Showing a case where your score disagrees with its own components is exactly
the kind of intellectual honesty that reads well in a three-minute video.

---

## 7. Confirmation beats a single signal

The recipe's framing, from "Why Confirmation Matters":

> "If a stock has a high GNN anomaly score *and* its top broker is net distributing *and*
> foreign investors are net selling, the convergence of three independent signals is much
> stronger evidence than any one signal alone."

Its structure — a model-based anomaly score, then **independent** confirmation from broker
activity and foreign flow — is a template worth copying at the architecture level. Sectors'
API is unusually well suited to it because broker flow, foreign flow, shareholder composition
and insider filings are four genuinely independent views of the same question.

A project that confirms its signal across two or three of those is materially more
defensible under the 30% technical-depth criterion than one that computes a single number.

---

## Pitfalls confirmed live, 6 September 2026

These four cost real credits to discover. Full account in
[`../VERIFICATION-LIVE.md`](../VERIFICATION-LIVE.md).

**Quarterly financials rename a field by sector.** `/v2/financials/quarterly/{symbol}/` returns
`realized_capital_goods_investment` for banks (BBCA, BBRI) — the name the spec example shows —
and `capital_expenditure` in the same slot for everyone else (ADRO, TLKM). `financials_sector_metrics`
is populated for banks and an empty object otherwise. A parser written against the documented
example handles banks and silently drops capex for the rest of the market. Read both keys.

**`listing-performance` has no data for anything listed before May 2005.** Every Indonesian
blue chip 404s, and a 404 bills 1 credit. Use a recent listing — the spec's own example is
`BREN`.

**SGX and KLSE `classifications` are not the IDX vocabulary.** `top_gainers` / `top_losers`
belong to `/v2/companies/top-changes/` only. The SGX and KLSE `top` endpoints take
`dividend_yield | revenue | earnings | market_cap | pe`, bill per classification, and default
to all five.

**The rate limiter counts calls, not seconds.** 25 billed requests per rolling ~30 s. Sleeping
between calls does not help unless the sleep is long enough to keep 25 out of any window —
1.0 s is not (trips on the 26th), 1.5 s is. A 429 carries no `Retry-After`, and polling one
keeps it shut: retrying every 5 s stayed blocked for 36 s where waiting quietly cleared in
under a second.

**A missing key is a 403, not a 401.** Client code branching on 401 never fires. There is no
`code` field either — just `{"error": "Authentication credentials were not provided."}`.

**Mining detail endpoints cover 9 companies, not 366.** `financials`, `performance` and
`sales-destination` 404 for almost every slug. `/v2/mining/companies/?has_financials=true`
returns the nine that work — all listed coal holdings. Filter first; a guessed slug is a
billed 404. The three are **not** one universe, either:
`/v2/mining/companies/performance/pt-adaro-indonesia/` answers 200 for a slug that `financials`
404s on, so "has financials" does not mean "has performance".

**`klse` is not an index code.** It appears in the ingestion registry that populates
`/v2/index-daily/`, which is why an earlier pass listed it as a candidate. The API rejects it
with a free 400. `sti` — flagged unverifiable for two passes — **does** resolve.

---

## Where these come from

| Recipe | What to mine it for |
| --- | --- |
| [GNN Anomaly Detection, parts 1–3](https://docs.sectors.app/recipes/gnn-anomaly-detection/01-gnn-part-1) | The zero-sum trap, data-quality audits, the confirmation pattern, honest score interpretation |
| [Benchmarking IDX Banking Stocks](https://docs.sectors.app/recipes/stock-investing-and-finance/02-benchmarking-idx-banking-stocks-sectors-api) | Rate-limit sleep, banking-metric interpretation (cost-to-income trends) |
| [API Security Best Practices](https://docs.sectors.app/recipes/api-security/01-securing-api-usage) | Error handling, logging without leaking keys, timeouts, backoff |
| [Multi-Agent Workflows](https://docs.sectors.app/recipes/generative-ai-python/03-multiagent-workflows) | Sequential chains and judge-critic patterns for reliability |

Reading these is also calibration: they show the depth Supertype considers normal, and they
tell you which demos the judges have already seen many times.
