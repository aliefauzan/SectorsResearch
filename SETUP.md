# Team setup

One shared configuration file, one shared recording set. Five minutes, no dependencies
beyond Python 3.

## 1. Configure

```bash
cp .env.example .env
```

Open `.env` and paste the team's Sectors API key into `SECTORS_API_KEY=`. That is the
only required line.

`.env` is git-ignored and stays on your machine. **Share the key through whatever the
team already uses for secrets — never through a commit, an issue, a screenshot, or a
public channel.** Farming extra accounts to get more credits is a disqualifying offence
under the hackathon rules, so one key, shared carefully, is also the only compliant
option.

Everything reads the file automatically: `capture.py` walks up from its own directory to
the repository root, loads the first `.env` it finds, and never overwrites a variable
that is already set in your shell. So a one-off override still works:

```bash
SECTORS_BUDGET=5 python3 research/harness/src/capture.py --plan research/harness/plans/plan.json --tier 0
```

## 2. Verify without spending anything

```bash
cd research/harness
python3 src/capture.py --plan plans/plan.json --dry-run
```

The header should print your `.env` path, the base URL, and `key: set`. The plan should
cost **176 credits across 87 calls**. Nothing is called.

## 3. Rehearse against the mock

The mock serves the spec's own examples and the same credit meter, so the whole harness
can be exercised for free before a single live call:

```bash
python3 src/mock_server.py --port 8787 &
SECTORS_BASE_URL=http://127.0.0.1:8787 python3 src/capture.py --plan plans/plan.json --budget 300
```

Delete anything the rehearsal wrote to `recorded/` before going live, so synthetic
payloads never get mistaken for real ones.

## 4. Go live, cheaply

```bash
python3 src/capture.py --plan plans/plan.json --tier 0 --budget 5
```

Then stop and reconcile before anything else. The full procedure — phases, budget
ceiling, and what to check at each gate — is in
[`research/audit/prompts/VERIFY-PROMPT-LIVE.md`](research/audit/prompts/VERIFY-PROMPT-LIVE.md).

## The rules that protect the grant

The grant is **1,000 credits, non-transferable, expiring at the end of the event**. It
does not top up. Four things burn it fastest:

1. **Letting `sections`, `classifications`, `periods`, or `n_quarters` default.** A
   defaulted company report costs 8 credits instead of 1; defaulted top-changes costs 10
   instead of 1.
2. **Calling a ticker or slug that does not exist.** A 404 bills 1 credit — the lookup
   ran. Only ever call identifiers that came back in an earlier response.
3. **Re-running an exploratory call.** `capture.py` writes every payload to `recorded/`
   and skips anything already settled, so re-running a plan is free. Ad-hoc `curl` is
   not — it pays again every time.
4. **Natural-language screener queries.** `?q=` costs 3 credits; the identical structured
   query costs 1. Run `?q=` once, read `llm_translation` out of the response, and hardcode
   the `where`/`order_by` it produced.

## Sharing recordings

`research/harness/recorded/` **is** committed on purpose. Those payloads were paid
for in credits, and `mock_server.py` serves them in preference to the spec examples — so
once one person has captured a call, everyone else develops against the real response for
free. Commit new recordings along with the ledger entry that produced them.

`recorded/_ledger.jsonl` is the team's shared spend log: every attempt, its status, the
estimated cost, and whatever cost header the API returned. Check it before a big run:

```bash
python3 src/capture.py --report
```

## What is in this repository

- `research/README.md` — the dossier index, key facts, and the audit record.
- `research/docs/hackathon/` — the competition: rules, tracks, submission checklist.
- `research/docs/api/` — the API in depth: endpoint reference, response shapes,
  screener query language, credit budget, pitfalls.
- `research/harness/` — the mock server, the capture harness, the fixtures and the
  synthetic generators. Develop here; call the live API as little as possible.
- `research/plan/` — what we are building and the competitive landscape.
- `research/evidence/` — provenance: verbatim captures, the OpenAPI spec, the portal
  usage logs that independently confirm what the API charged.
- `research/audit/` — the six verification passes. `VERIFICATION-LIVE.md` is the one
  that actually called the API and supersedes the others on behaviour;
  `prompts/VERIFY-PROMPT-LIVE.md` is the live procedure it followed.
- `research/tools/` — generators for the two generated docs in `research/docs/api/`.
