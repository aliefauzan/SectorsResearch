# Idea · Special Monitoring Board Early Warning

> Verification trail: [`../evidence/rechecks/ppk-verification-2026-09-07.md`](../evidence/rechecks/ppk-verification-2026-09-07.md).
> Fits **Track 03** as a score, or **Track 02** as a daily watcher — the inputs genuinely move
> daily, which is what the mining-licence idea lacks.

## The problem

IDX runs a **Papan Pemantauan Khusus** — a special monitoring board. A stock that meets any of
11 published criteria is moved onto it and traded by **periodic call auction** instead of
continuous matching. Liquidity collapses. Holders cannot get out at a price they choose.

**172 stocks were on it in January 2026** — roughly a fifth of the market. Sixteen entered in
one fortnight.

Retail hate it. When full call auction went live in March 2024, investors sent **protest
flower wreaths to the IDX building**, covered by Kompas and Liputan6.

The list is published only **after** the move takes effect. Stockbit shows the current list.
IDX publishes it per period. **Nothing anywhere says who is about to enter.**

That is the product: *you hold three stocks that are one criterion away from the monitoring
board — here is which criterion, and how close.*

## Why it is open

`grep` over Sectors' full OpenAPI spec and the entire 840 KB docs dump finds **zero mentions**
of pemantauan khusus, special monitoring, notasi khusus or call auction. `listing_board` only
ever returns Main, Development or Acceleration.

So the board is invisible in the API — yet most of its criteria are computable from data
Sectors does expose.

GitHub has **no repository** on the subject. Code search finds one Streamlit tool that keeps a
**hand-pasted PPK ticker list** to filter those stocks out — people maintain this by hand
today. Academic papers apply bankruptcy models to companies *already on* the board. Nobody
predicts entry.

## The derivation

Score each listed company against the criteria IDX publishes, and report **distance to
trigger** rather than a binary.

| # | Criterion | Data |
| --- | --- | --- |
| 1 | Price < Rp51 **and** low liquidity over 3 months | `last_close_price` + `/v2/daily/{symbol}/` — the 90-day window is exactly the 3-month test |
| 3 | No revenue, or no change vs prior statements | `total_revenue_mrq`, `revenue[YYYY]`, `/v2/financials/quarterly/` |
| 4 | Miner past production but not at sales stage by book year 4 | `/v2/mining/companies/performance/{slug}/` + `listing_date` |
| 5 | **Negative equity** | `total_equity_mrq` — one screener call, whole market |
| 6 | Free float below the I-A / I-V floor | `/v2/free-float/`, 1 credit per 100 companies |
| 7 | Low liquidity, standalone | `/v2/daily/{symbol}/` |
| 8 | PKPU or bankruptcy filing | `/v2/news/` + `/v2/filings/` text; tags include `violation`, `ojk` |
| 10 | Suspended more than 1 exchange day for trading activity | `/v2/suspensions/` — dates and reasons, refreshed daily 10:00 WIB |

**Seven of eleven computable, three partial.** Criterion 2 (disclaimer audit opinion) and 11
(exchange discretion) are out of reach — say so on screen.

The output is a sentence, not a dashboard:

> *ABCD is 4% of free float and one quarter of negative equity away from the monitoring board.*

Two extensions, both unclaimed:

- **Exit prediction.** Entries and exits are both dated in the announcements. Of the 172 on the
  board, which are structurally stuck versus temporarily flagged under criterion 10? Holders of
  all 172 want that answer.
- **Ground truth.** The official announcements make this one of the rare hackathon projects you
  can actually score. Backtest your warnings against who really entered.

## Why this beats a dashboard

Not a re-render — Stockbit already renders the list free. This is a **forward-looking
cross-endpoint computation against a published rulebook**, which is exactly the Track 03 bar.
And every warning it produces is falsifiable against IDX's next announcement.

## Prior art to name in the video

**`cuthbertyoungg/FINSCORE`** (Jul 2026) — a deployed LightGBM + Cox survival model scoring
IDX financial distress from annual statements, using pemantauan and delisting as labels. Built
on **yfinance, not Sectors**. Different target and horizon: next-year distress probability from
annual data, versus mechanical criterion proximity on rolling 3-month liquidity and the latest
quarterlies. Adjacent enough that naming it reads as homework rather than risk.

## Engineering constraints, verified live

**`www.idx.co.id` is behind Cloudflare and returns 403 even with a browser User-Agent.** That
includes static announcement PDFs — so the `pdf_url` in every `/v2/suspensions/` row is **not
directly fetchable**. The BCA Sekuritas mirror serves the same announcements fine (HTTP 200,
`application/pdf`). Use it for ground-truth labels.

Criterion 4 inherits the mining limit: only **9 of 366** mining companies have detail records.

## Credit cost

Roughly 623 of the 1,000-credit grant remain (portal log: 377 charged). Rough daily cycle:

- `/v2/suspensions/` — 1 credit, whole market
- one screener call with `where=total_equity_mrq < 0 or last_close_price < 51` and
  `include_query_values=true` — 1 credit, up to 200 rows
- `/v2/daily/{symbol}/` for the shortlist only — 1 credit per ticker, refreshed weekly
- `/v2/free-float/` sweep — ~10 credits, weekly

About **2 credits a day plus ~50 a week**, so roughly 120–150 credits over the build period.
Comfortable. Widen the shortlist only once the rest is working.

## Track choice

**Track 02** if the pitch is the watcher: suspensions refresh daily at 10:00 WIB, prices move
daily, and the board itself changes roughly fortnightly — so the unattended run log has real
content every day, and a warning that later comes true is the strongest possible demo.

**Track 03** if the pitch is the score. Pick one and let the video argue it.

Gate the schedule on the IDX trading calendar and log the skip — there is no calendar endpoint,
so hardcode it. See [`../docs/api/12-trading-calendar-and-releases.md`](../docs/api/12-trading-calendar-and-releases.md).

## What must not be claimed

This predicts an **exchange administrative action against published criteria**. It is not a
bankruptcy forecast and not a sell signal. Publish the criteria, publish the thresholds, show
the distance. A directional warning with disclosed rules is analysis; a probability of ruin is
advice, and advice is prohibited.
