# Submission Checklist & Timeline

Everything the rules require, in the order you have to do it. Dates in WIB.

---

## Phase 0 — Before you write any code

| ☐ | Item | Deadline | Notes |
| --- | --- | --- | --- |
| ☐ | Every member creates a Sectors account at [sectors.app](https://sectors.app) | Before first commit | Rules are explicit: onboarding comes before project code |
| ☐ | Every member **completes Sectors App onboarding** | Before registration closes | Verified during the eligibility check; one unonboarded member can invalidate the submission |
| ☐ | Settle the final roster (1–4 people) | Before claiming credits | Claiming credits **locks the roster permanently** |
| ☐ | Register the team at [`/portal/team`](https://hackathon.sectors.app/portal/team) | **22 Sep 2026, 23:59** | Free |
| ☐ | Appoint the representative | At registration | Official contact + credit holder + prize recipient |
| ☐ | Claim the 1,000 API credits from the portal team page | After all onboarding | Locks the roster — do this only when the team is final |
| ☐ | Under-18 members: parental/guardian consent | At registration | Covers media publication and prize acceptance |
| ☐ | Join the [Slack](https://join.slack.com/t/sectorshackathon/shared_invite/zt-47a8tdhhz-FgREdKQ46lUETWErcIwNcQ) | Now | `#discussion` for questions, `#support` for incidents |

---

## Phase 1 — Repository hygiene

| ☐ | Item | Why |
| --- | --- | --- |
| ☐ | Create the repo **on or after 19 August 2026** | Repos created earlier may be disqualified |
| ☐ | Verify with `git log --reverse --format='%ad %s' \| head -3` | Judges may inspect commit history |
| ☐ | Public template or boilerplate is fine — just make the **first commit** fall inside the window | Explicitly allowed by the rules |
| ☐ | No code from prior projects, and no open-sourcing your old project in order to reuse it | Explicit violation |
| ☐ | `.env` in `.gitignore` from commit #1 — commit `.env.example` instead | Committed keys are the classic disqualifier. This repo is already set up that way: see [`SETUP.md`](../../SETUP.md) |
| ☐ | Add a `LICENSE` if you like — **no specific license is required** | Public repo is sufficient |
| ☐ | Commit regularly, with real messages | Commit history is the evidence that the project is real and not faked |

---

## Phase 2 — Build (19 Aug → 30 Sep)

| ☐ | Item |
| --- | --- |
| ☐ | Sectors MCP and/or REST API is a **core** data source — remove it and the product stops working |
| ☐ | Core workflow functions **end to end** (rough edges acceptable, non-functioning is not) |
| ☐ | Pick one track; make sure the product's *core* matches its qualifying test |
| ☐ | **Track 02 only:** start the scheduler early and retain logs, so you have a real multi-day unattended run history to show |
| ☐ | No automated trade execution anywhere in the product |
| ☐ | Not submitted to any other competition; exclusive to this hackathon |
| ☐ | Add a disclaimer: information and analysis tool, **not** investment advice |

---

## Phase 3 — Submission package

Submitted at [`/portal/submit`](https://hackathon.sectors.app/portal/submit) by
**30 September 2026, 23:59 WIB**. The server decides whether you were on time.

| ☐ | Deliverable | Spec |
| --- | --- | --- |
| ☐ | **Public repository link** | Must stay public ≥ 90 days after winners are announced. All API keys removed — check history, not just HEAD |
| ☐ | **Teaser video, 1 minute** | Screen recording of the product working. Published **publicly** on YouTube or social media |
| ☐ | **Judging video, max 3 minutes** | Full walkthrough: problem, intended audience, core workflow. YouTube/Vimeo (public or unlisted), Google Drive **with link sharing enabled**, or Loom. Inaccessible = not judged |
| ☐ | **One-sentence problem statement** | Who it's for + what problem it solves |
| ☐ | **Track selection** | One of the three |
| ☐ | **Team participant names** | Full list |
| ☐ | **Social media post** | Publishing the project and **tagging the official Sectors account**. Keep the link |

Bahasa Indonesia or English — no scoring preference either way.

---

## Phase 4 — After submitting

**Submitting freezes the repository and application immediately.** No commits, pushes, edits
or changes of any kind — including bug fixes. Violation = disqualification.

The **only** exception: a leaked API key or credential.
1. Notify organizers in Slack `#support`
2. Revoke and rotate the credential **first**
3. Then push a commit containing **only** its removal

| ☐ | Item |
| --- | --- |
| ☐ | Keep the repo public through at least 9 January 2027 (90 days after the 9 Oct announcement) |
| ☐ | Keep video links live and accessible |
| ☐ | Representative available for identity verification within 7 days if you win |

---

## Video plan — 30% of the score

Two separate videos with different jobs. Do not just trim one into the other.

**The 1-minute teaser** is marketing. Public, on YouTube or social. Product working, fast.
No setup, no architecture, no talking head. Open on the output.

**The 3-minute judging video** carries 30% of your score directly and heavily influences the
40% usability score. Judges never see you live — this *is* your presentation.

A structure that fits three minutes:

| Time | Content |
| --- | --- |
| 0:00–0:25 | The problem, and who has it. Name a specific person: a retail investor in Surabaya, a junior equity analyst, a campus investment club treasurer |
| 0:25–0:45 | What the product does, in one sentence, over a shot of it working |
| 0:45–2:15 | The core workflow, end to end, unedited enough to be believable. Track 02: **show the schedule config and the unattended run logs here** |
| 2:15–2:40 | Where Sectors data is load-bearing — name the endpoints or MCP tools. This is what the technical-depth judges are checking against your repo |
| 2:40–3:00 | Who benefits and what changes for them. Disclaimer on screen |

Things that lose points cheaply: silent screen recordings, five minutes of architecture
diagrams, a demo on obviously fake data, an unreadable 720p terminal, and any claim your repo
does not support — technical depth is *verified against the repository*.
