---
name: decider-continue-stop
description: Decider continuation controller. Call after N tool steps or repeated outputs to pick continue, verify_then_continue, stop_and_report, or escalate and break loops. Use for continuation vs stop loop detection termination control.
compatibility: Requires bash, curl, jq; env AI_API_URL, AI_API_KEY, optional AI_DECIDER_MODEL (default decider)
license: Apache-2.0
metadata:
  endpoint: "${AI_API_URL%/}/systemone (no /v1; strip trailing slash)"
  auth: "Bearer AI_API_KEY (env only, never logged)"
  model: "${AI_DECIDER_MODEL:-decider}"
---

# decider-continue-stop

Continuation vs stop / loop detection. Termination control for long agent
runs: decides whether to continue, verify first, stop and report, or
escalate, preventing token burn on stalls and loops.

## Terminology (read first)

- `decider` has three meanings: (1) the role (this controller), (2) the
  Mapika open-weight System One model family name, (3) this task's default
  `model` id alias (`decider`). The endpoint is `$AI_API_URL`-configured;
  never claim it IS TypeSafe or Mapika.
- Question types: `choice` (named options); `score`/`noul` are not used by
  this skill (single-question call). `confidence` may be absent on some
  gateways — tolerate it.
- v1 `confidence` semantics changed upstream; thresholds below are tunable
  placeholders pending 50-100 gold labels and must be recalibrated.

## When to use

- After every N tool steps (e.g. N=5) or when outputs repeat / stall.
- When budget (steps, tokens, time) is running low and scope is unclear.
- Before an unbounded retry or search loop.

## Do NOT use

- For plan approval (use `decider-plan-gate`), tool allow/deny
  (use `decider-tool-gate`), or failure routing (use `decider-test-triage`).
- As the only stop condition: always combine with a hard step cap.
- When env is unset: fail closed to `stop_and_report`.

## Inputs to `state` construction

```json
{
  "steps_done": "<count + 1-line summary each>",
  "last_outputs": "<truncated last 2-3 tool results>",
  "stall_signals": "<repeats, same error, no progress>",
  "remaining_budget": "<steps/tokens left + goal>"
}
```

Truncate aggressively: total request body MUST be <=32 KiB; 1-8 questions per
call (this skill uses 1).

## Questions to ask

- `q_next` (`choice`): `instructions: "Should the run continue or stop?"`,
  `criteria: {"continue":"progress is being made, keep going",
  "verify_then_continue":"uncertain, verify state before continuing",
  "stop_and_report":"done or stalled, stop and summarize",
  "escalate":"blocked, needs human"}`.

`jq -n` snippet (run from this skill root):

```bash
STATE_JSON=$(jq -n --arg steps "$STEPS" --arg budget "$BUDGET" '{steps_done:$steps, remaining_budget:$budget}')
QUESTIONS_JSON=$(jq -n '{q_next:{type:"choice", instructions:"Should the run continue or stop?", criteria:{continue:"progress is being made, keep going", verify_then_continue:"uncertain, verify state before continuing", stop_and_report:"done or stalled, stop and summarize", escalate:"blocked, needs human"}}}")
scripts/decide.sh --state "$STATE_JSON" --questions "$QUESTIONS_JSON" > resp.json
```

## Thresholds / decision table (tunable placeholders)

| Condition | Action |
|---|---|
| majority `choice` = X | act on X |
| `confidence` present and `<0.5` | `verify_then_continue` (verify state, then re-ask) |
| stall count `N>=3` (same result 3x) | `stop_and_report`, do not continue |

Single-question call: the returned `choice` (plus `probabilities` if
present) is the signal. Log choice + confidence/probabilities as receipt.

## Fail-closed + error handling

- Missing env: transport exits non-zero
  (`: "${AI_API_URL:?...}"` / `: "${AI_API_KEY:?...}"`) — treat as
  `stop_and_report`.
- 401: bad/missing key, do NOT retry. 422: fix `criteria`/schema, no retry.
  429: back off. 529/5xx: already retried via curl flags; stop and report.
  Errors print `Bearer <redacted>`, never the key.
- Never `echo $AI_API_KEY`, never `set -x` with the key in env, never write
  the key to disk, logs, or SKILL.md. Endpoint is always
  `${AI_API_URL%/}/systemone` (strip trailing slash, no `/v1`).

## Worked parse example

```bash
# (response already in resp.json from the call above)
NEXT=$(jq -e -r '.answers.q_next.choice' resp.json)
echo "next=$NEXT"
```
