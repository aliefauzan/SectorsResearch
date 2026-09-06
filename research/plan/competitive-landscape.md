# Competitive Landscape — What Other Teams Are Doing

> Source: the public matching board at <https://hackathon.sectors.app/matching>,
> captured 4 September 2026. Verbatim: [`evidence/hackathon/hack-matching.md`](../evidence/hackathon/hack-matching.md).

## What the board is

A public directory of teams **with room to grow** and individuals looking to join one. It is
not the full registration list — teams that are already complete, or that simply never
published a profile, don't appear.

That makes it a **biased but genuinely useful sample**: it over-represents teams still
forming and under-represents teams that were assembled and started early. Read it as a
signal about the field, not a census.

## Track distribution among 48 public teams

Recounted live on **5 September 2026**. The board is mutable and it moved by four teams in
one day, so treat any figure here as a snapshot, not a constant.

| Track | Teams (5 Sep) | Share | (4 Sep) |
| --- | --- | --- | --- |
| **01 · AI Agents & Assistants** | 15 | 31% | 16 |
| **03 · Market Intelligence** | 12 | 25% | 11 |
| **02 · Automation & Workflows** | **7** | **15%** | 4 |
| No track chosen yet | 14 | 29% | 13 |

**Track 02 is still the least crowded** — but it is now roughly *half* as popular as Track
01, not a quarter. Three of the four teams that joined the board on 5 September chose it,
which is the direction you would expect once people read the rubric. The structural argument
below still holds; the size of the edge does not.

> Counted from the "Public teams" section only, verified twice (rendered text and DOM).
> An earlier draft said 46 teams and 17/11/5 because it also counted the track labels on the
> separate *participant profiles* section further down the page; the 4 Sep capture is
> genuinely 44 / 16-4-11. Evidence for both counts:
> [`evidence/hackathon/hack-matching.md`](../evidence/hackathon/hack-matching.md) and
> [`evidence/rechecks/pass3-live-recheck-2026-09-05.md`](../evidence/rechecks/pass3-live-recheck-2026-09-05.md).
> **Re-count this yourself near the 22 September registration close** — it is the one number
> in this dossier guaranteed to be wrong by then.

This lines up with intuition about how hackathons go: "build an AI agent" is the exciting
brief, and "build a thing that runs on a cron at 7am" is not. But the scoring rubric does not
reward excitement — it rewards **real-world usability (40%)** and **a video that communicates
the problem (30%)**. A daily brief that has genuinely been running unattended for three weeks
demonstrates both more convincingly than a chat interface does.

There's a second reason Track 01's popularity is a warning rather than an invitation: it has
the strictest disqualifying test in the event. Fifteen teams heading for Track 01 means the
judges will see a lot of off-the-shelf-client-plus-MCP projects, and will be well calibrated
on the difference between those and real orchestration by the time they reach yours.

## Team sizes on the board

| Size | Teams (5 Sep, recounted) | (4 Sep) |
| --- | --- | --- |
| 1 of 4 | **45** | 41 |
| 2 of 4 | 2 | 2 |
| 3 of 4 | 1 | 1 |
| **Total** | **48** | 44 |
| **Participants on the board** | **52** | 47 |

No card shows 4 of 4 — by construction, since the board only lists teams with room to grow.

All but three listed teams are solo builders looking for people. Two implications:

- **Recruiting is easy right now.** Lots of people are unattached, and several list exactly what they bring (AI engineer, designer, video editor, financial analyst).
- **Many of these will not finish.** Solo teams that were still forming in early September, on a 30 September deadline, have a high attrition rate. The real competitive field is smaller than 48.

> **The board is not the field.** The hackathon Slack invite page reports **105 members**
> ("Aurellia Christie and 104 other members") against 52 people on the board, so most
> participants never publish a profile. Treat every figure here as a lower bound.

## What teams say they need

Reading the "looking for" text across the board, the most-requested roles are, in order:

1. **Designers** — requested by name repeatedly
2. **Financial / data analysts** — people who understand Indonesian equities
3. **Backend and product engineers**
4. **Business analyst / marketing**

**This changed between 4 and 5 September, and it is the finding in this document with the
shortest shelf life.** On 4 September nobody on the board was advertising for a video editor,
while one participant listed themselves as a "Creative Technologist, Video Editor & Creative
Designer". On the 5 September recount **two teams are now recruiting for exactly that**:

- **Sepi** (Track 02) — *"Cari 1 orang video/motion untuk judging video 3 menit. Produk sudah didefinisikan dan backend dikerjakan solo."*
- **StockPro** (Track 03) — *"Need a designer, editor, motion graphics and maybe someone who familiar with cron ,automations ,n8n and hermes"* (spacing as written on the board)

**Thirty percent of the score is the video**, judged asynchronously with no live session. The
field is still mostly competing for designers and analysts, but the edge here is narrowing —
at least one team has read the rubric the same way. Treat it as an advantage worth taking
now rather than a gap that will still be open on 22 September.

## Named projects visible on the board

On the 5 September recount, **22 of the 48 cards carry text** and four disclose enough to
identify the project:

| Team | Track | What they say |
| --- | --- | --- |
| **Xninetzy** | 03 | "Solo builder. Not currently looking for additional teammates. Building SAKTI end-to-end across AI/agentic systems, backend infrastructure, data pipelines, and product development." |
| **Apriyanto** | 03 | "Hiddwn gems & early accumulation by bandar" |
| **RWL** | 02 | "daily watch of stock with certain filter (RSI/MA/MACD)" |
| **StockPro** | 03 | recruiting for "cron ,automations ,n8n and hermes" — i.e. a scheduled pipeline |

The rest is either "No description yet" or a recruiting note. Two things follow.

**Bandarmology is taken, at least once.** Apriyanto's one-liner is a broker-accumulation
screen — the same territory as idea 1.1 in
[`what-we-can-build.md`](what-we-can-build.md). It does not make the idea unavailable, but
"nobody else will think of this" is no longer true of the broker-cohort data specifically.

**RWL's brief is a Track 02 project built on indicators the Sectors API does not compute** —
none of RSI, MA or MACD is among the 219 screener fields. Whoever builds that is deriving them
from `/v2/daily/`. Worth knowing before you copy it: Sectors' own recipes
`quick-start-in-python/03-simple-moving-average` and `05-EDA-stock-price` already do exactly
that, the second one computing `MA_21`, `RSI`, `OBV`, `MACD` and rolling volatility with the
`ta` library and feeding them to a model. So it is a derivation the API does not hand you —
but not one the organizers have never seen.

There is still no leaderboard and no public information about what the other 26 silent teams
are doing, so **do not over-fit to this**. It tells you which tracks are crowded and gives a
sample of what four teams are building; it does not tell you which ideas are taken.

## What this changes

| Finding | So |
| --- | --- |
| Track 02 has ~1/2 the teams of Track 01 (was ~1/4 on 4 Sep) | Least crowded, and the one where the qualifying bar is objective and easy to prove |
| 29% of teams haven't picked a track | The distribution will shift; don't treat Track 02's 15% as final |
| Track 01 is crowded *and* has the strictest disqualifier | Only pick it if you're genuinely building orchestration — see [the trap](../docs/api/04-mcp-and-ai-agents.md) |
| Almost all teams are solo and still forming | Easy to recruit; real field is smaller than it looks |
| Two teams now recruit video/motion skill (was zero on 4 Sep) | 30% of the rubric is still under-contested, but the gap is closing — act on it now |
| Four visible project ideas, one of them a bandarmology screen | Mining licences and suspensions still look untouched; **broker cohorts are not** — at least one team is on them |

## ⚠️ Your real Track 02 competitor is Sectors Workflow

The 48 teams on the matching board are not the only thing you're measured against. **Sectors
already ships an if-this-then-that alerting product**, and it does most of what a naive
Track 02 project would do. Captured from <https://sectors.app/workflow>, 4 September 2026:

**Three-step builder:**

1. **Select entities** — specific stocks, your watchlist, or whole sectors, sub-sectors, industries, sub-industries
2. **Define trigger conditions** — event tags, significant price movements, or news mentions
3. **Choose an action** — deliver to **WhatsApp, Email, Slack, Telegram, or Google Sheets**, or execute a Sectors Financial API call

**Ten pages of pre-built templates**, including:

- "Notify Slack if Indonesian banks hit a new high"
- "Email alert if SGX banks appear in top 20 institutional buying"
- "WhatsApp alert for Astra Group stocks hitting new highs"
- "Slack alert if technology stocks are top 10 monthly leaders"
- "Email when SGX tech giants have insider buying"
- "Sheet export of Food & Beverage stocks hitting new lows"

Trigger tags visible in those templates: `new-high`, `new-low`, `top-20-institution-buying`,
`top-ten-1m-leaders`, `insider-1-month-buy`.

**Also noted:** "Each successful execution consumes 1 Sectors credit" — Workflow runs bill
against the same credit pool as the API.

### What this means

Read that template list again. "A bot that watches defined Sectors signals and pushes an
alert when conditions are met" — the example direction printed on the Track 02 page — is
**already a product Sectors sells**, with five delivery channels and sixty-odd templates.

A judge who works at Sectors will recognise a reimplementation of Sectors Workflow instantly.

### How to be different anyway

Track 02 is still the least crowded track and still the best structural bet. But the brief
has to be sharper than "alerts":

| Workflow already does | So differentiate on |
| --- | --- |
| Tag-based triggers on entities you pick | **Derived conditions** — a threshold on a metric *you* computed, not a tag Sectors pre-assigned |
| Single-condition fires | **State transitions and diffing** — alert when a name *enters* a screen, not while it's in one |
| Five delivery channels | **A destination Workflow doesn't have** — a generated document, a dashboard that rebuilds itself, a PR into a repo, a podcast |
| One alert per condition | **Synthesis** — one daily brief that aggregates and ranks, rather than N separate alerts |
| Per-company or per-sector scope | **Cross-endpoint joins** — combining broker flow, filings and composition in a way no single trigger expresses |

The daily-brief idea in [`what-we-can-build.md`](what-we-can-build.md) survives this test —
Workflow fires discrete alerts; a brief that gathers, ranks, summarizes and explains is a
different product. The bare "alert bot" idea does not survive it. Choose accordingly.

Worth saying explicitly in your video: name what Sectors Workflow does and say why yours is
different. Judges will be thinking it regardless; getting there first reads as confidence and
as having done the homework.

## Where to look for late-breaking signal

The board is a snapshot and will move. Two live sources this dossier can't capture:

- **Slack** `#discussion` and `#support` — the only channel where organizers answer track-boundary questions, and where rule clarifications land
- The **matching board itself** — re-check it near the 22 September registration close for the final track distribution

Neither is scrapeable without an account. If you register, both are worth reading before you
lock in a track.
