# Competitive Landscape — What Other Teams Are Doing

> Source: the public matching board at <https://hackathon.sectors.app/matching>,
> captured 4 September 2026. Verbatim: [`../99-raw/hack-matching.md`](../99-raw/hack-matching.md).

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
> [`99-raw/hack-matching.md`](../99-raw/hack-matching.md) and
> [`99-raw/pass3-live-recheck-2026-09-05.md`](../99-raw/pass3-live-recheck-2026-09-05.md).
> **Re-count this yourself near the 22 September registration close** — it is the one number
> in this dossier guaranteed to be wrong by then.

This lines up with intuition about how hackathons go: "build an AI agent" is the exciting
brief, and "build a thing that runs on a cron at 7am" is not. But the scoring rubric does not
reward excitement — it rewards **real-world usability (40%)** and **a video that communicates
the problem (30%)**. A daily brief that has genuinely been running unattended for three weeks
demonstrates both more convincingly than a chat interface does.

There's a second reason Track 01's popularity is a warning rather than an invitation: it has
the strictest disqualifying test in the event. Seventeen teams heading for Track 01 means the
judges will see a lot of off-the-shelf-client-plus-MCP projects, and will be well calibrated
on the difference between those and real orchestration by the time they reach yours.

## Team sizes on the board

| Size | Teams |
| --- | --- |
| 1 of 4 | 41 |
| 2 of 4 | 2 |
| 3 of 4 | 1 |
| **Total** | **44** |

All but three listed teams are solo builders looking for people. Two implications:

- **Recruiting is easy right now.** Lots of people are unattached, and several list exactly what they bring (AI engineer, designer, video editor, financial analyst).
- **Many of these will not finish.** Solo teams that were still forming in early September, on a 30 September deadline, have a high attrition rate. The real competitive field is smaller than 44.

## What teams say they need

Reading the "looking for" text across the board, the most-requested roles are, in order:

1. **Designers** — requested by name repeatedly
2. **Financial / data analysts** — people who understand Indonesian equities
3. **Backend and product engineers**
4. **Business analyst / marketing**

Notably scarce: nobody is advertising for a **video editor** — and one participant lists
themselves as a "Creative Technologist, Video Editor & Creative Designer."

That's worth pausing on. **Thirty percent of the score is the video**, judged asynchronously
with no live session. The field is competing for designers and analysts while under-valuing
the one skill that maps directly onto nearly a third of the rubric.

## Named projects visible on the board

Only one team has published a project name and description in enough detail to identify:
**Xninetzy** — a solo builder in Track 03, "Building SAKTI end-to-end across AI/agentic
systems, backend infrastructure, data pipelines, and product development."

Everything else is either "No description yet" or a recruiting note. There is no public
information about what the majority of the field is actually building, and no leaderboard,
so **do not over-fit to this**. It tells you which tracks are crowded; it does not tell you
which ideas are taken.

## What this changes

| Finding | So |
| --- | --- |
| Track 02 has ~1/2 the teams of Track 01 (was ~1/4 on 4 Sep) | Least crowded, and the one where the qualifying bar is objective and easy to prove |
| 30% of teams haven't picked a track | The distribution will shift; don't treat 9% as final |
| Track 01 is crowded *and* has the strictest disqualifier | Only pick it if you're genuinely building orchestration — see [the trap](../02-sectors-platform/04-mcp-and-ai-agents.md) |
| Almost all teams are solo and still forming | Easy to recruit; real field is smaller than it looks |
| Nobody is competing for video skill | 30% of the rubric is under-contested |
| No visible project ideas | The unusual-data plays (mining licences, broker cohorts, suspensions) are very unlikely to be duplicated |

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
