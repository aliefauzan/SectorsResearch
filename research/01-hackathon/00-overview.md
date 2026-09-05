# Sectors Hackathon 2026 — Overview

> Source: <https://hackathon.sectors.app/> and <https://hackathon.sectors.app/rules>, captured 4 September 2026.
> Raw scrapes are in [`99-raw/`](../99-raw/).

## What it is

An online, Indonesia-wide hackathon run by **Supertype** (the company behind Sectors),
with **Algoritma** and **Sectors** as co-organizers. The one-line brief:

> "Solve an interesting problem thoughtfully with Sectors API."

The pitch on the landing page is *"Find the signal. Build what markets need next."* —
turn Indonesian financial market data into something a real person could use.

It is explicitly **not** a code-golf competition. The rules say so directly:

> "We don't judge how sophisticated your code is. We judge whether what you build
> can genuinely be used by real people, today, with Sectors data at its core."

## The single hard constraint

Every project, in every track, must use the **Sectors MCP server or the Sectors REST API
as a core data source** — not one decorative call. The stated test is: *the product should
lose its core functionality if Sectors data is removed.*

Whether you use MCP, REST, or both does not affect which track you're in.

## Key dates

| Milestone | Date |
| --- | --- |
| Registration opens | 19 August 2026 |
| Build period opens | 19 August 2026 |
| **Registration closes** | **22 September 2026, 23:59 WIB** |
| **Build period and submissions close** | **30 September 2026, 23:59 WIB** |
| Judging period | 1–8 October 2026 (asynchronous) |
| Winners announced | 9 October 2026 |

Registration closing eight days before submission is deliberate — it gives organizers time
to verify onboarding and credit grants. A team that registers on the final day still has a
full week to build.

**As of 4 September 2026: 18 days left to register, 26 days left to submit.**

## Prizes

Total pool: **IDR 50,000,000**

- IDR 30,000,000 in cash
- IDR 20,000,000 in Sectors API credits

Cash goes to the team representative; credits are applied to the representative's Sectors
account. Prize taxes follow Indonesian law. Winners under 18 receive prizes via a parent or
guardian. Organizers may require identity verification before delivery, with a seven-day
window before the prize can be reassigned.

The rules do not publish a breakdown by placement or by track.

## Three tracks

| # | Track | Core question it answers | AI/LLM required? |
| --- | --- | --- | --- |
| 01 | **AI Agents & Assistants** ("Reason") | Can it reason and act conversationally or autonomously? | **Yes, mandatory** |
| 02 | **Automation & Workflows** ("Act") | Does it run on a schedule or trigger, unattended? | Optional |
| 03 | **Market Intelligence** ("Reveal") | Does it produce *derived* insight, not just a nicer view of the data? | Optional |

Full detail on each in [`02-tracks.md`](02-tracks.md).

Track is determined by **what the product fundamentally does, not what it looks like**.
An agent with a dashboard is still Track 01. If judges think you picked the wrong track,
they will usually move you rather than disqualify you — disqualification on track grounds
happens only if the project fits no track at all.

## How judging works

Fully asynchronous, 1–8 October. **No live presentations.** The video and the repository
have to carry the whole argument on their own.

**Stage 1 — eligibility check (pass/fail).** Submission is complete, the product works,
Sectors data is a core source, every participant's Sectors onboarding is verified.

**Stage 2 — scoring**, by the internal Sectors and Supertype judging team:

| Criterion | Weight | What it rewards |
| --- | --- | --- |
| Real-world usability | **40%** | Does it address a real problem? Could someone use it today and benefit? |
| Video demo & storytelling | **30%** | Is the video exciting, engaging, well produced? Does it communicate the problem to its audience? |
| Technical depth & execution | **30%** | Verified against the GitHub repo: how innovative is the Sectors API/MCP use? Is it real, functional, well engineered, not faked for the demo? |

Judges' decisions are final.

The weighting is the most important strategic fact in this document: **70% of the score is
problem framing and communication.** A modest product with a sharp problem statement and an
excellent three-minute video beats an impressive engine explained badly.

## Team structure and API credits

- Solo or teams of **2–4**. A solo participant counts as a team of one.
- One team per participant. Being on multiple teams gets you removed from all of them; deliberate collusion disqualifies every team involved.
- One project per team.
- Each team appoints a **representative**: official contact, API-credit holder, prize recipient.
- Each registered team gets **1,000 Sectors API credits**, claimable from the portal team page once *every* member has finished Sectors onboarding.
- **Claiming the credits locks the roster.** No adding or removing members afterward.
- Registering extra accounts to farm credits is a disqualifying offence.
- Credits are for this project only, non-transferable, no cash value, and expire when the event ends.

See [`../02-sectors-platform/05-credit-budget.md`](../02-sectors-platform/05-credit-budget.md)
for what 1,000 credits actually buys and how to avoid burning them.

## Eligibility

- Indonesian citizens, or residents domiciled in Indonesia.
- All ages. Under-18s need parental/guardian consent at registration covering media publication and prize acceptance.
- Employees, contractors, judges, mentors and organizers of Supertype, Sectors, and Algoritma — plus immediate family — are **not** eligible.
- Registration is free.
- **Every participant must create a Sectors account and complete Sectors App onboarding at sectors.app before the team writes any project code.** This is verified. A team with any participant who hasn't onboarded by the registration deadline may have its submission ruled invalid.

## Official channels

| Channel | Link |
| --- | --- |
| Site | <https://hackathon.sectors.app/> |
| Rules | <https://hackathon.sectors.app/rules> |
| Register / team portal | <https://hackathon.sectors.app/portal/team> |
| Submit | <https://hackathon.sectors.app/portal/submit> |
| Teammate matching | <https://hackathon.sectors.app/matching> |
| Sign in | <https://hackathon.sectors.app/auth/sign-in> |
| Slack (`#discussion`, `#support`) | [join link](https://join.slack.com/t/sectorshackathon/shared_invite/zt-47a8tdhhz-FgREdKQ46lUETWErcIwNcQ) |
| Email | ask+hackathon@incoming.supertype.ai |
| WhatsApp (sponsorship) | (+62) 822-2100-0749 |

> The whole public site is seven pages: `/`, `/rules`, the three `/tracks/*` pages,
> `/matching`, and `/portal/*`. Everything under `/portal` is gated behind a Sectors account
> login. There is no public FAQ, prizes, judges or timeline page.

Rules were open to change before 19 August 2026. Changes after registration opened get
announced on all official channels and cannot disadvantage teams already building under the
previous rules.

## Community and campus partners

Asosiasi Ilmuwan Data Indonesia (AIDI), Alpha Momentum, Atios, Block71 Innovation Factory,
Bandungdev, Beasiswa Korea, BEM UNS, Cyber Tech, DEMA FSIT UIN, DevOps Indonesia,
Dev Web3 Bandung, Girlskode, Himastika, HIMTI, HMIF Universitas AMIKOM Yogyakarta, ICCOM,
Info Event, Innovare UI, Kalibrr, KSPM Universitas Gunadarma, Media Startup, OmahTI,
PPI Hong Kong, PPI Korea.

Sponsorship slots (hackathon sponsor / community partner / custom) were still open at capture time.
