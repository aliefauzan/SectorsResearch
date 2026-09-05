# Official Rules — Full Reference

> Faithful restatement of <https://hackathon.sectors.app/rules>, captured 4 September 2026.
> Verbatim scrape: [`99-raw/hack-rules.md`](../99-raw/hack-rules.md).
> The official rules also exist in Bahasa Indonesia. Submissions and videos are accepted in
> **either Bahasa Indonesia or English** — neither language is favored in scoring.

Sections below follow the site's own numbering.

---

## 01 · Spirit of the competition

Not a typical coding competition. Sophistication of code is explicitly not the metric.
The metric is whether what you build can genuinely be used by real people, today, with
Sectors data at its core.

---

## 02 · Key dates

| Milestone | Date |
| --- | --- |
| Registration opens | 19 August 2026 |
| Build period opens | 19 August 2026 |
| Registration closes | 22 September 2026, 23:59 WIB |
| Build period and submissions close | 30 September 2026, 23:59 WIB |
| Judging period | 1–8 October 2026 |
| Winners announced | 9 October 2026 |

---

## 03 · Eligibility

- Indonesian citizens or residents domiciled in Indonesia.
- All ages; under-18 participants must provide parental or guardian consent at registration, covering media publication consent and prize acceptance through a guardian.
- Employees, contractors, judges, mentors and organizers of **Supertype, Sectors, and Algoritma**, and their immediate families, are not eligible.
- Registration is free.
- Every participant must create a Sectors account and **fully complete Sectors App onboarding at sectors.app before the team writes any project code**. Onboarding is verified during the eligibility check. A team with any participant who has not onboarded by the registration deadline may have its submission deemed invalid.
- Registering means you have read and agreed to the rules in full.

---

## 04 · Teams & API credits

- Solo, or teams of 2–4. Solo counts as a team of one.
- One team per participant (solo teams included). Someone found on multiple teams is removed from all of them; the remaining teams may continue, unless organizers find deliberate collusion — then every team involved is disqualified.
- One project per team.
- **Rosters lock when the team claims its bonus API credits** (available once all members complete onboarding).
- Each team appoints one representative: official contact, API-credit holder, prize recipient.
- Prizes are awarded per team; splitting is the team's internal matter.

### API credits

- **1,000 Sectors API credits per registered team**, claimed from the portal team page once all members complete onboarding.
- Registering additional accounts to obtain extra credits for the same project is a rules violation and grounds for disqualification.
- Credits are exclusively for developing the team's competition project during the build period. Non-transferable, no cash or compensation equivalent, and they expire when the event concludes unless organizers state otherwise.

---

## 05 · Build period & work restrictions

Build period: **19 August 2026 → 30 September 2026, 23:59 WIB**. Start whenever you're ready
inside that window; there is no separate fixed build week.

- **Before** the build period: ideas, research, sketches, designs, and planning are allowed. **No project code may be written before 19 August 2026.**
- The **repository must be created during the build period**. Judges may inspect commit history. Repos created before 19 August 2026, or code migrated from previous projects, may cause disqualification. Multiple repositories are fine if all were created inside the window.
- Starting from a **public template or boilerplate is allowed**. What matters is that your first commit falls inside the build period.
- Boilerplate, templates, frameworks, libraries and public open-source code may be used, **provided they are not a finished product**. Open-sourcing your own prior project just before the event in order to reuse its code is prohibited.
- Projects must be **exclusive to Sectors Hackathon**. No work from previous projects; no simultaneous submission to other competitions or hackathons.
- **Code freeze:** the repo and app freeze the moment you submit, or at the 30 September deadline, whichever comes first. After freezing: no commits, pushes, edits or changes of any kind — *including bug fixes*. Violating this means disqualification.
- **The only freeze exception** is a leaked API key or other credential. Notify organizers in Slack `#support`, revoke and rotate the credential first, then push a commit containing only its removal.

> Practical consequence: submitting early does *not* buy you extra polish time — it costs
> you the rest of the window. Submit when you are done, not when you are nervous.

---

## 06 · Project requirements

### General requirements, every track

- Projects must use **Sectors MCP or the Sectors REST API as a core data source**, not a single decorative call. The product should lose its core functionality if Sectors data is removed. Any track may use MCP, REST, or both; the data interface does not determine the track.
- Must be a **working prototype or MVP** with a core workflow that functions end to end. Rough edges are fine; a product that does not work will not pass judging.
- **Live deployment is not required.** A public repository plus a judging video showing the core workflow end to end is enough to clear the eligibility check's "product works" gate. But real-world usability carries the highest weight, so something judges can see working convincingly will score better.
- **Stack, tools, languages, licenses and platforms are unrestricted.** A public repo is sufficient; no specific open-source license is required.
- **Automated trade execution is prohibited in every track.** You may analyze, screen, score, alert, and support decisions. You may not place, execute, or automate buy/sell orders on real or brokerage-connected accounts.

### Track definitions

Summarized here; full detail in [`02-tracks.md`](02-tracks.md).

| Track | Definition |
| --- | --- |
| 01 · AI Agents & Assistants | Conversational or autonomous AI products for Indonesian financial markets, with an AI/LLM component at their core. |
| 02 · Automation & Workflows | Products where Sectors data works inside real, recurring routines. |
| 03 · Market Intelligence | Products that turn Sectors data into insight for financial market decisions. |

### Track boundaries and support

Track is determined by what the product fundamentally does, not what it looks like. An agent
with a dashboard belongs in Track 01. An autonomous pipeline that also produces scores may
fit Track 02 or Track 03 — the team picks whichever best represents the core.

If a project does not meet its declared track's requirement, **judges may move it to the
track that fits rather than disqualify it**. Track-based disqualification applies only when
the project fits no track. Ask in Slack `#discussion` during the build period if unsure.

---

## 07 · Use of AI

AI coding tools — code generation, completion, agents, and similar — are **fully permitted,
without restriction and without a disclosure requirement**. The rules put it plainly:
"It's 2026, so use your best tools. What we judge is the result."

---

## 08 · Submission requirements

Submitted through the [hackathon portal](https://hackathon.sectors.app/portal/submit) before
**30 September 2026, 23:59 WIB**. The server decides whether a submission is on time.

Required:

1. **Public repository link.** Must stay public for **at least 90 days after winners are announced**. Making it private before then forfeits prize eligibility and a replacement winner may be selected. **Remove all API keys before submitting.**
2. **One-minute teaser video** — a screen recording of the product working, published publicly on YouTube or social media.
3. **Judging video, max three minutes** — a full walkthrough of the problem, intended audience, and core workflow. Accepted: public or unlisted YouTube and Vimeo, Google Drive links with link sharing on, and Loom. **Inaccessible videos will not be judged.**
4. **One-sentence problem statement** — who the product is for and what problem it solves.
5. **Track selection** and the list of team participant names.
6. **A social media post publishing the project, tagging the official Sectors account.**

Submissions and videos may be in Bahasa Indonesia or English.

---

## 09 · Judging

Fully asynchronous, 1–8 October 2026, based only on submission materials. **No live
presentation sessions.**

**Eligibility check — pass/fail:** submission complete, product works, Sectors data used as a
core source, every participant's Sectors onboarding verified.

**Scoring** (internal Sectors and Supertype judging team):

| Criterion | Weight | What it rewards |
| --- | --- | --- |
| Real-world usability | 40% | How well does the project address a real-world problem? Can someone use it today and benefit from it? |
| Video demo & storytelling | 30% | How exciting, engaging, and well produced is the video? Does it communicate the problem effectively for the intended audience? |
| Technical depth & execution | 30% | Verified against the GitHub repository: how innovative is the use of Sectors API or MCP? Is the project real, functional, well engineered, and not faked for the demo? |

Judges' decisions are final and binding.

---

## 10 · Prizes

Total pool **IDR 50,000,000**: IDR 30,000,000 cash + IDR 20,000,000 in Sectors API credits.

- Cash transferred to the team representative. Prize taxes follow Indonesian law.
- Credit prizes applied directly to the representative's Sectors account.
- Winners under 18 receive prizes through a parent or guardian.
- Organizers may require identity verification before delivery. Failing to verify within seven days may mean the prize is reassigned.

---

## 11 · Publicity & content rights

- Submitting grants Sectors and Supertype permission to display, publish and promote the submission — videos, screenshots, project names, participant names — on their sites, social media, newsletters and promotional materials, without additional compensation.
- **Intellectual property stays entirely with the participants.** Sectors and Supertype claim no ownership of any code or product built during the event.
- Participants are responsible for making sure the project doesn't infringe others' IP.

---

## 12 · Code of conduct

- Safe, welcoming, harassment-free conduct on Slack, social media and every event channel.
- Discriminatory (SARA), harassing or unlawful content is automatically disqualified.
- **Projects must not provide financial advice.** Position the product as an information and analysis tool, not investment recommendations. Include a disclaimer where relevant.
- Report violations in `#support` on the official Slack.

---

## 13 · Disqualification

Organizers may disqualify any participant or team at their sole discretion, including for
rules violations, cheating (pre-event code and code-freeze violations included), multiple
accounts for extra API credits, duplicate submissions, code-of-conduct violations, or other
unsporting behavior.

---

## 14 · Support

Rules could be updated before 19 August 2026. Post-registration changes are announced on all
official channels and will not disadvantage teams already building under previous rules.

Questions: ask+hackathon@incoming.supertype.ai or Slack `#discussion`.

---

## Rules that most often cost teams the prize

Ranked by how easy they are to trip over:

1. **Code freeze on submit.** No bug fixes after. Submit last.
2. **Repo created before 19 August 2026.** Check `git log --reverse | head`. If your first commit predates the window, start a fresh repo and re-commit.
3. **An unonboarded teammate.** One person who never finished Sectors onboarding can invalidate the whole submission.
4. **Roster locked by claiming credits.** Settle the team *before* clicking claim.
5. **API key committed to the public repo.** Scan history, not just the working tree.
6. **Inaccessible judging video.** A Drive link without link-sharing is simply not judged.
7. **Missing the social post.** It is a listed submission requirement, not a nice-to-have.
8. **Repo going private inside 90 days after the announcement.** Forfeits the prize.
9. **Anything that executes trades.** Prohibited in all three tracks.
10. **Language that reads as financial advice.** Ship a disclaimer.
