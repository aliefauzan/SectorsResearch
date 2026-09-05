# The Three Tracks — Full Detail

> Sources: <https://hackathon.sectors.app/tracks/ai-agents-assistants>,
> `/tracks/automation-workflows`, `/tracks/market-intelligence`. Captured 4 September 2026.

Every project picks **one** track. Track is decided by **what the product fundamentally
does, not what it looks like**. Rules that apply to all three:

- Sectors MCP or the Sectors REST API must be a **core data source**.
- **Automated trade execution is prohibited.**
- If your project misses its declared track's bar, judges will usually **move** it to the
  fitting track rather than disqualify. Disqualification on track grounds only if it fits none.
- An autonomous pipeline that also produces scores could be Track 02 or Track 03 — you choose
  which best represents the core.

---

## Track 01 · AI Agents & Assistants — "Reason"

**Definition:** conversational or autonomous AI products for Indonesian financial markets,
with an AI/LLM component at their core.

**AI/LLM component: mandatory.**

### The qualifying test

> The project must include **custom-built agent logic or orchestration**. The team must build
> something of its own around the model — not only connect an existing client to Sectors.

### What qualifies

- Multi-step reasoning flows
- Custom tool-use pipelines
- Routing between data sources
- Memory or state management
- Autonomous task execution
- A purpose-built interface for a specific participant and problem

### What does **not** qualify

Connecting an off-the-shelf AI client — Claude, OpenClaw, Hermes — to the Sectors MCP with
custom prompts or configuration alone.

> The sharpest phrasing of the bar, straight from the track page:
> **"If the product would disappear when the team's prompt is removed from someone else's
> client, it does not meet this track's bar."**

### Example directions (illustrations, not a fixed list)

1. A research agent that plans and executes a multi-step company comparison using Sectors data
2. A market assistant with purpose-built tools, memory, and a workflow for a specific analyst task
3. An autonomous research pipeline that chooses which Sectors sources to query and synthesizes the result

### Reading between the lines

This is the track where the "core data source" rule and the "custom orchestration" rule
interact awkwardly. Sectors MCP makes it *very* easy to build something that is really just
a prompt. To clear the bar, the orchestration has to be yours: your own planner, your own
tool layer over the REST API, your own memory, your own evaluation or verification step.

A practical way to prove it in the video: show the agent's intermediate steps — the plan it
made, the endpoints it chose, why it re-queried. That is visible evidence of orchestration.

---

## Track 02 · Automation & Workflows — "Act"

**Definition:** products in which Sectors data works inside real, recurring routines.

**AI/LLM component: optional.**

### The qualifying test

> The automation must **run autonomously on a schedule or trigger, without human intervention
> per cycle**. Once set up, it should do its job on its own.

And, critically, an evidence requirement that is unique to this track:

> In the judging video, show the **schedule or trigger configuration together with logs,
> timestamps, or screenshots of unattended runs**. A manual run without that evidence is not
> sufficient.

### What qualifies

- A workflow that fires on a market event
- A scheduled pipeline that runs every trading day
- A bot that pushes alerts when defined conditions are met
- Custom scripts, n8n, messaging bots, or CI schedulers
- Any other platform that can run a repeatable routine autonomously

### What does **not** qualify

A workflow that requires a human to manually run it each time.

### Example directions

1. A daily market brief generated and delivered automatically before the market opens
2. A bot that watches defined Sectors signals and pushes an alert when conditions are met
3. A triggered workflow that updates a recurring research process when market data changes

### Reading between the lines

The evidence requirement is the whole game here. Plan for it from day one:

- Structured run logs with real timestamps, retained across days
- A visible schedule config (cron expression, n8n schedule node, GitHub Actions `schedule:`)
- Ideally a run history in a real destination — a Telegram/Slack channel with several days of
  messages at 07:00 is far more convincing than one triggered demo run

Start the scheduler early, even against a stub, so that by demo day you have a genuine
multi-day history to show. This is the cheapest 30-percentage-point insurance in the event.

---

## Track 03 · Market Intelligence — "Reveal"

**Definition:** products that turn Sectors data into insight for financial market decisions.

**AI/LLM component: optional.**

### The qualifying test

> The project must produce **derived insight: analysis generated from the data rather than
> the data itself**.

### What qualifies

- Signals or scores
- Rankings
- Screeners with custom logic
- Anomaly detection
- Comparative analysis
- Synthesized research outputs

### What does **not** qualify

> "A product that only displays raw Sectors data in a different visual form, however well
> presented, does not qualify for this track."

### Example directions

1. A custom screener that ranks companies using a team's own financial logic
2. An anomaly detector that surfaces unusual market or company behavior
3. A comparative research product that turns multiple Sectors data points into a decision-support view

### Reading between the lines

The trap is building a beautiful dashboard. A dashboard of Sectors fields is a re-render, not
a derivation. What clears the bar is a **transformation you can defend**: a composite score
with stated weights, a statistical anomaly threshold, a peer-relative ranking, a
cross-endpoint join that no single Sectors screen gives you.

Sectors' own docs contain a fully worked example of the kind of thing that qualifies:
the three-part [GNN anomaly detection recipe](https://docs.sectors.app/recipes/gnn-anomaly-detection/01-gnn-part-1)
which builds a correlation graph from daily prices, scores anomalies with a graph autoencoder,
then confirms with broker activity and foreign flow. Read it as a calibration of the expected
depth, not as something to copy.

---

## Choosing between tracks

| If your core is… | Track |
| --- | --- |
| A model deciding what to do next | 01 |
| A clock or an event deciding what to do next | 02 |
| A formula or model deciding what is interesting | 03 |

Common ambiguities and how the rules resolve them:

| Project | Track | Why |
| --- | --- | --- |
| Agent with a dashboard UI | 01 | Track follows the core, not the interface |
| Scheduled pipeline that emits scores | 02 or 03 | Team's choice; pick the one your video actually argues |
| LLM that summarizes a nightly digest | 02 | The scheduler is the core; the LLM is a stage |
| Screener with a chat box bolted on | 03 | The chat is decoration unless it does the reasoning |

Since the AI/LLM component is optional in Tracks 02 and 03, an LLM does not upgrade your
track — and adding one to a Track 03 project does not make it Track 01.
