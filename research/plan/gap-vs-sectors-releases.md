# Gap Analysis · Our Ideas vs 28 Sectors Releases

Source: [`../evidence/sectors/release-timeline-2026-09-07.md`](../evidence/sectors/release-timeline-2026-09-07.md),
the complete Dev Log from 2024-06-12 to 2026-08-10, read 7 September 2026.

Companion to [`already-published.md`](already-published.md), which covers the 39 documentation
recipes. That file answers "did they write a tutorial for it". This one answers "did they ship
it as product". Both have to be clear before an idea is safe.

---

## The shape of what they build

Every one of the 28 releases is **descriptive**: it reports a fact that has already happened —
a price, a flow, a filing, a ratio, an ownership change. Reporting is the whole product line.

There is exactly one exception, and it is not user-facing: "Automated Treatment Flags"
(2025-11-12) detects outliers in their own ingestion pipeline.

**Sectors has never shipped a forward-looking signal.** No forecast, no risk score, no "this is
about to happen to your holding". That is the unoccupied category, and it is where all three of
our live ideas sit.

## Territory they now own — do not enter

| Their feature | Shipped | Kills the idea |
| --- | --- | --- |
| Foreign Flow, market-wide | 2026-05 and 2026-08 | any foreign-flow dashboard |
| The Orderbook, ~90 broker report pages | 2026-05, 2026-06 | bandarmology / broker-accumulation tooling |
| Ownership Movements | 2026-05 | ownership-change tracker |
| Government Ownership, BUMN pages | 2026-04, 2024-12 | state-ownership screener |
| Conglomerate & group pages | 2026-07 | conglomerate ownership graph as a product |
| NL screener + SQL-like queries | 2026-02 | "ask the market a question" screener |
| AI Chat, AI Search, Search Console | 2025-06 → 2026-06 | stock-analyst chatbot (also a published recipe) |
| Events Calendar, dividend calendar | 2026-03, 2025-01 | corporate-action calendar |
| Watchlist + weekly email summary | 2024-09, 2024-11 | watchlist digest bot |
| Bank NPL, liquidity, LAR, loan portfolio | 2025-04, 2025-09 | banking credit-risk dashboard |
| REITs depth (SGX) | 2025-10 | SGX REIT screener |
| Intrinsic value calculator, peers, radar charts | 2024-09 → 2024-12 | valuation calculator |
| Weekly Digest, Snapshot publications | 2025-07 | AI market newsletter |
| MCP service + API-key observability | 2026-08 | MCP-plumbing projects |

Two of these are recent enough to matter: bandarmology and foreign flow were their **May and
August 2026** headline releases. A hackathon entry in that territory is competing with what
the judges shipped four weeks ago.

## Where they are absent

### 1. Papan Pemantauan Khusus — clean gap, best of the three

Zero mentions across 28 releases: no `pemantauan`, `special monitoring`, `full call auction`,
`suspension`, `delisting`, `notasi khusus`.

Meanwhile `/v2/suspensions/` is a live endpoint in their own API. **They collect the data and
have never built a surface on it.** 172 stocks were on the board in January 2026 — about a
fifth of the market — and the list is published only after the move takes effect.

Combined with the recipe check in `already-published.md` and the prior-art sweep in
`../evidence/rechecks/ppk-verification-2026-09-07.md`, this idea is unclaimed on all three
fronts: not a product, not a recipe, not a third-party tool.

See [`idea-ppk-early-warning.md`](idea-ppk-early-warning.md).

### 2. Mining licence runway — data shipped, product never

Mining is the strangest hole in the timeline. `/v2/mining/*` is 20+ endpoints including
`/v2/mining/licenses/`, `/v2/mining/license-auctions/` and `/v2/mining/contracts/`, and
"Mining, Metals & Minerals" sits in the site footer — but **no release has ever announced a
mining feature**. REITs, the other footer vertical, got a full release in October 2025.

So the data is paid for and live, and the product surface does not exist. `licence`, `IUP` and
`expiry` appear nowhere in the timeline.

The weakness stays what it already was: licence expiries move on a multi-year clock, so the
screen looks the same every day. Weaker demo, real gap.

See [`idea-licence-runway.md`](idea-licence-runway.md).

### 3. Suspension-to-delisting ladder — same gap, second door

`/v2/suspensions/` unused, Peraturan BEI I-N is a published clock in months, and the timeline
never touches it. This is the same absence as #1 approached from the other end, and it can
share a build.

See [`problem-inventory-delisting-ladder.md`](problem-inventory-delisting-ladder.md).

## Timing risk

Releases land monthly, most often the 12th–14th. The next one is due **around 12 September
2026** — before the 30 September submission deadline. They also run a roadmap newsletter and
previewed a quarter of work in the January release, so a shipped feature can land mid-build.

Nothing in the visible roadmap points at the monitoring board. Re-read the release page once
after the September drop and before recording the video; if PPK appears there, the pitch has
to change.

## Verdict

Build **PPK early warning**. It is the only idea that is simultaneously: absent from 28
releases, absent from 39 recipes, absent from third-party tools, daily-moving enough to demo,
and buildable on endpoints already recorded in `harness/recorded/`.
