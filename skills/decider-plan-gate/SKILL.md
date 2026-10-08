---
name: decider-plan-gate
description: Decider plan approval risk gate. Call after the planner finishes a plan and before build writes code to get safe_to_auto_execute probability, risk score, and proceed/refine/escalate verdict. Use for plan approval risk gate after planner before build writes code.
compatibility: Requires bash, curl, jq; env AI_API_URL, AI_API_KEY, optional AI_DECIDER_MODEL (default decider)
license: Apache-2.0
metadata:
  endpoint: "${AI_API_URL%/}/systemone (no /v1; strip trailing slash)"
  auth: "Bearer AI_API_KEY (env only, never logged)"
  model: "${AI_DECIDER_MODEL:-decider}"
---

# decider-plan-gate

Plan approval / risk gate between planner and build. Asks a System One /
Jev-class decision model for calibrated numbers (no generated text) and maps
them to proceed / refine / escalate.

## Terminology (read first)

- `decider` has three meanings: (1) the role (this gate), (2) the Mapika
  open-weight System One model family name, (3) this task's default `model`
  id alias (`decider`). The endpoint is `$AI_API_URL`-configured; never claim
  it IS TypeSafe or Mapika.
- Question types: `choice` (named options), `score` (ordered levels, returns
  fractional expectation), `noul` ("yes/no" probability in [0,1]).
- v1 `confidence` semantics changed upstream; thresholds below are tunable
  placeholders pending 50-100 gold labels and must be recalibrated.

## When to use

- Planner produced steps + file list + irreversible ops; before any build
  agent writes code, runs migrations, or pushes.
- Re-plan after reviewer rejection; gate the revised plan again.

## Do NOT use

- As a code reviewer or test router (use reviewer skill / `decider-test-triage`).
- For per-tool-call allow/deny (use `decider-tool-gate`).
- When `AI_API_URL`/`AI_API_KEY` are unset: fail closed, do not proceed.

## Inputs to `state` construction

Build `state` as a compact JSON object:

```json
{
  "plan_summary": "<steps, 5-15 lines>",
  "files_touched": ["<paths>"],
  "irreversible_ops": ["<e.g. migration, push, deploy, rm>"],
  "permission_summary": "<what the plan will run>"
}
```

Truncate logs/diffs to fit: total request body MUST be <=32 KiB; keep 1-8
questions per call. Prefer summaries over raw dumps.

## Questions to ask

Ask exactly these three questions in one call (`type`, `instructions`,
`criteria` are literal):

- `q_safe` (`noul`): `instructions: "Is it safe to auto-execute this plan
  without human review?"`, no `criteria` (or `{"true":"safe","false":"unsafe"}`).
- `q_risk` (`score`): `instructions: "Rate overall execution risk."`,
  `criteria: ["negligible","low","moderate","high","critical"]`
  (5 levels, indices 0-4).
- `q_gate` (`choice`): `instructions: "Gate verdict for this plan."`,
  `criteria: {"proceed":"plan is safe and complete, execute now",
  "refine_plan":"plan needs revision before execution",
  "escalate_human":"needs human decision"}`.

`jq -n` snippet (run from this skill root; model defaults to `"${AI_DECIDER_MODEL:-decider}"`; pass `--model ID` to override):

```bash
STATE_JSON=$(jq -n --arg plan "$PLAN_SUMMARY" '{plan_summary:$plan}')
QUESTIONS_JSON=$(jq -n '{q_safe:{type:"noul", instructions:"Is it safe to auto-execute this plan without human review?"}, q_risk:{type:"score", instructions:"Rate overall execution risk.", criteria:["negligible","low","moderate","high","critical"]}, q_gate:{type:"choice", instructions:"Gate verdict for this plan.", criteria:{proceed:"plan is safe and complete, execute now", refine_plan:"plan needs revision before execution", escalate_human:"needs human decision"}}}')
scripts/decide.sh --state "$STATE_JSON" --questions "$QUESTIONS_JSON" > resp.json
```

Run `scripts/decide.sh --help` for full flags (`--model`, `--silent`) and exit codes.

## Thresholds / decision table (tunable placeholders)

`q_safe` returns `noul` in [0,1]; `q_risk` returns fractional `score`
expectation in [0,4]; `q_gate` returns `choice`.

| Condition | Action |
|---|---|
| `noul>=0.6 AND risk<=1 AND gate=proceed` | proceed to build |
| `0.4<=noul<0.6 OR risk~=2` | refine_plan / ask clarifying question |
| `noul<=0.4 OR risk>=3 OR gate=escalate_human` | escalate to human, do not execute |

Record the raw probabilities in the build log as the decision receipt.

## Fail-closed + error handling

- Missing env: `scripts/decide.sh` exits non-zero via
  `: "${AI_API_URL:?...}"` / `: "${AI_API_KEY:?...}"`. Treat as escalate.
- 401: bad/missing key, do NOT retry. 422: schema/criteria violation, fix
  questions, no retry. 429: back off. 529/5xx: transport already retried,
  fail closed. Error output shows `Bearer <redacted>`, never the key.
- Never `echo $AI_API_KEY`, never `set -x` with the key in env, never write
  the key to disk, logs, or SKILL.md. Endpoint is always
  `${AI_API_URL%/}/systemone` (strip trailing slash, no `/v1`).

## Worked parse example

```bash
# (response already in resp.json from the call above)
SAFE=$(jq -e '.answers.q_safe.noul' resp.json)
RISK=$(jq -e '.answers.q_risk.score' resp.json)
GATE=$(jq -e -r '.answers.q_gate.choice' resp.json)
echo "safe=$SAFE risk=$RISK gate=$GATE"
```
