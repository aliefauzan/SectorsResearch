# Idea · Licence Runway

> One idea, written up in full. Chosen from the gap analysis because it has a nameable user,
> a one-sentence output, and no published recipe a judge could pattern-match it against.
> Track 03 · Market Intelligence.

## The problem

Indonesian coal and nickel issuers — ADRO, ITMG, PTBA, INCO, MDKA — earn their revenue under
**IUP mining licences that carry hard expiry dates**. When a licence lapses, production at
that site stops.

Retail holders cannot see this. Checking it today means opening a several-hundred-page annual
report and reconciling a licence schedule by hand. Effectively nobody does.

No product answers the question — not Sectors, not a global data provider:

> **How many years of licence sit under this listed company's production?**

## Why the data is unclaimed

The mining extension is 19 endpoints. Across 726,000 characters of Supertype's own recipes it
gets **one passing mention**. No tutorial exists, so no judge has a template to compare
against. See [`already-published.md`](already-published.md).

| Endpoint | What it gives |
| --- | --- |
| `/v2/mining/licenses/` | `license_expiry_date`, `cnc`, `licensed_area_ha`, `commodity_type`, `company_slug`, `location` (GeoJSON) |
| `/v2/mining/sites/` | `production_volume`, `strip_ratio`, `year`, `company_slug` |
| `/v2/mining/resources-reserves/` | reserves, also available per province |
| `/v2/mining/companies/ownership/{slug}/` | `parents[]`, `subsidiaries[]`, each with `symbol` and `percentage_ownership` |

The ownership endpoint is the one that makes the idea possible: it carries both a slug and a
**listed ticker**, so a private mining entity can be walked up to its listed parent. Almost
nothing else in the API exposes corporate structure.

## The derivation

Not a re-render of licence rows — a score built from a cross-endpoint join that no single
Sectors screen produces.

```
For each listed ticker:
  1. Walk the ownership graph down to every mining entity beneath it
  2. Collect every licence held by those entities
  3. Weight each licence by the production_volume of its site
     (ten small licences are not one large one)
  4. Licence Runway   = production-weighted years remaining
  5. Cliff Exposure   = % of production under licences expiring within 3 years
  6. CnC flag         = licences where cnc is false — not clean-and-clear
```

Output, per issuer, in one sentence:

> *68% of ADRO's production sits under licences expiring before 2029.*

A non-investor understands that immediately. That matters for the 30% video score as much as
for the 40% usability score.

## Confirmation signal · `/v2/suspensions/`

Supertype's own GNN recipe uses the pattern: compute one score, then confirm it against an
independent source. `/v2/suspensions/` appears in **no recipe at all** and refreshes daily at
10:00 WIB.

Use it twice:

- **For the user** — short runway *and* a suspension history is layered risk.
- **For your own correctness** — a suspended stock returns a **well-formed all-zero row, not
  an error**. Any screener that does not audit for this will rank suspended names as extreme
  outliers and surface them as findings. Showing the audit is cheap evidence of technical
  depth. See [`../docs/api/10-domain-pitfalls.md`](../docs/api/10-domain-pitfalls.md).

## Limits — state these on screen, do not hide them

**Only 9 of 366 mining companies have detail records**, all listed coal holdings. Filter with
`/v2/mining/companies/?has_financials=true` first; a guessed slug is a billed 404.

The three detail endpoints are **not one universe**:
`/v2/mining/companies/performance/pt-adaro-indonesia/` returns 200 for a slug that
`financials` 404s on.

So scope the product honestly to the set that resolves. Do not imply market-wide coverage —
the repo is judged, and the gap will be visible in it.

## Why Track 03 and not Track 02

The core is a formula deciding what is interesting. That is Track 03 by definition.

Do not force it into Track 02. Licence data moves on a scale of years, so a daily cron over it
is theatre and the unattended-run evidence becomes a log of identical empty cycles. Track 02
needs an input that genuinely moves — the closest candidate is
`/v2/companies/quarterly-financial-dates/?since=`, the only endpoint in the API with a `since`
parameter, and that is a different project.

## Credit cost

Roughly 623 of the 1,000-credit grant remain (portal log: 377 charged).

`licenses` and `sites` are paginated, so compute the sweep cost before starting it:

```python
first = get("/v2/mining/licenses/", limit=30)
pages = -(-first["pagination"]["total_count"] // 30)
print(f"full sweep costs {pages} credits")
```

Ownership is 1 credit per slug, nine slugs. Suspensions is 1. Realistically tens of credits,
pulled once, after which every iteration runs against `mock_server.py` for free.

Standing rules from [`../../CLAUDE.md`](../../CLAUDE.md): rehearse the plan against the mock
first, delete anything a rehearsal wrote into `recorded/` before going live, and never call an
identifier that did not come back in an earlier response.

## What must not be claimed

A directional score with published weights is analysis. A probability, or a buy/sell
recommendation, is financial advice — prohibited by the code of conduct. Automated trade
execution is prohibited in all three tracks.

Put the weights on screen. Supertype does this in their own published work, so it reads as the
expected standard rather than a hedge.
