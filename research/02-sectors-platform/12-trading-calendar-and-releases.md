# The IDX Trading Calendar, and What Sectors Shipped Recently

> Eighth-pass finding, from `sectors.app/indonesia/calendars/trading-calendar` and
> `sectors.app/release`. Both were reached by enumerating the site's own `sitemap.xml`
> (2,006 URLs) rather than from navigation.

---

## ⚠️ The IDX trading calendar — and there is no endpoint for it

**2026: 22 market holidays, 239 trading days.**

There is **no API endpoint** that exposes the trading calendar. Every date-range endpoint will
happily accept a holiday and return nothing for it, and the docs' only guidance is the generic
"ensure your date range includes trading days".

This is a direct problem for **Track 02**, where the whole point is a job that runs unattended
on a schedule. A daily brief that fires on a market holiday produces an empty or stale
report — and if a judge watches your run log and sees a blank Monday, that reads as broken
rather than as a holiday.

### 2026 IDX holidays

| Month | Holidays | Trading days |
| --- | --- | --- |
| January | 1 (New Year), 16 (Isra Mikraj) | 20 |
| February | 16–17 (Chinese New Year 2577 Kongzili) | 18 |
| March | 18–19 (Hindu Saka New Year 1948), 20, 23, 24 (Eid al-Fitr 1447 H) | 17 |
| April | 3 (Good Friday) | 21 |
| May | 1 (Labor Day), 14–15 (Ascension Day), 27–28 (Eid al-Adha 1447 H) | 16 |
| June | 1 (Pancasila Day), 16 (Islamic New Year 1448 H) | 20 |
| **August** | **17 (Independence Day)**, **25 (Birth of Prophet Muhammad SAW)** | 19 |
| **September** | **none** | — |
| December | 24–25 (Christmas), 31 (Trading Holiday) | 20 |

### What this means for the hackathon window

The build period runs **19 August → 30 September 2026**.

- **August 25** is a market holiday, inside the build window. A scheduled job running that day sees no new market data.
- **September 2026 has no holidays** — so the final month, including submission day and any demo recording, is clean.

So the risk is narrow but real: if your unattended-run evidence spans late August, expect one
blank day and be ready to explain it. Better, handle it explicitly.

### Handle it in code

Since there is no endpoint, hardcode the calendar. This is ~20 lines and it turns a
demo-day embarrassment into a visible sign of domain competence:

```python
from datetime import date

# IDX market holidays 2026 — no API endpoint exposes these.
# Source: sectors.app/indonesia/calendars/trading-calendar
IDX_HOLIDAYS_2026 = {
    date(2026, 1, 1),   date(2026, 1, 16),
    date(2026, 2, 16),  date(2026, 2, 17),
    date(2026, 3, 18),  date(2026, 3, 19), date(2026, 3, 20),
    date(2026, 3, 23),  date(2026, 3, 24),
    date(2026, 4, 3),
    date(2026, 5, 1),   date(2026, 5, 14), date(2026, 5, 15),
    date(2026, 5, 27),  date(2026, 5, 28),
    date(2026, 6, 1),   date(2026, 6, 16),
    date(2026, 8, 17),  date(2026, 8, 25),
    date(2026, 12, 24), date(2026, 12, 25), date(2026, 12, 31),
}


def is_trading_day(day: date) -> bool:
    """IDX trades Monday-Friday excluding gazetted market holidays."""
    return day.weekday() < 5 and day not in IDX_HOLIDAYS_2026
```

Then gate the scheduled job on it, and **log the skip** rather than silently doing nothing —
a run log that says `2026-08-25 skipped: IDX market holiday` is evidence your automation is
real, which is exactly what the Track 02 judging requirement asks you to show.

> The synthetic generator in [`../03-mock-data/`](../03-mock-data/) uses a weekdays-only
> approximation and does **not** model holidays. That is fine for volume testing; do not use
> it to validate holiday handling.

---

## What Sectors shipped in 2026

From the release timeline at `sectors.app/release`. Useful for two reasons: it dates the
features, and it shows what the team has been investing in — which is a decent proxy for what
they find interesting.

| Date | Release | Highlights |
| --- | --- | --- |
| 2026-08-10 | **Foreign Flows** | Market-wide IDX foreign-flow reports · slash-commands in Search Console · **"a substantially better MCP experience with a new homepage demo, an improved MCP service, and full observability over your Sectors API keys"** |
| 2026-07-02 | **The Straits** | Group pages for conglomerates (Singapore & Indonesia) · **3× Singapore coverage expansion** · onboarding quests |
| 2026-06-16 | **Search Console** | Financial search engine · **~90 IDX broker report pages** · big expansion to the v2 API |
| 2026-05-12 | **Bandarmology** | **The Orderbook** · Foreign Flow · **Ownership Movements** · official deprecation of API v1 |
| 2026-04-14 | **Treasury of the Republic** | AI Chat upgrade · discover by industry · **government ownership data for IDX companies** · early access to Sectors Workflow |
| 2026-03-18 | **The Crescent Moon** | Redesigned landing · **corporate actions calendar for every company** · Google/GitHub/OTP sign-in |
| 2026-03-04 | **A Journalist's Dream** | News in AI Search · **Watchlist Groups** · Singapore stock report upgrades |

### Three things to take from this

**1. API key observability exists in the product.** The August release mentions "full
observability over your Sectors API keys". If you have an account, that is where to watch
your credit burn — better than inferring it from response headers. Check it early rather
than discovering your consumption pattern at the end.

**2. Their recent investment is exactly the differentiated data.** Bandarmology, foreign flow,
ownership movements, broker report pages, government ownership. That is where the team's
attention has been for six months — a project built on that data is working with the grain,
and the judges will know the datasets well.

**3. Some product features have no API.** "The Orderbook" and "Ownership Movements" appear as
product releases, and the pricing page lists "Order Books" as a Standard-plan feature, but
**no order-book endpoint exists in the 70-endpoint v2 spec**. Don't design a project around
order-book data — verify against
[`02-endpoint-reference.md`](02-endpoint-reference.md) before assuming a product feature is
reachable programmatically.

Government ownership is similar: it shipped as a product feature in April, and the closest API
surface is `/v2/company/shareholders-composition/{symbol}/` plus the screener's
`major_shareholders_*` fields. Those may or may not carry the same classification — test
before you build on it.
