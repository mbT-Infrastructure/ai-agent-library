---
name: decider-ask
description: Decider general arbitrary A-vs-B preference choice gate. Call when you need to know which of two options prefer between caller-defined options A and B (extendable to N options) and get a calibrated pick in one forward pass. Use to choose between options A B general choice gate for any other preference decision.
compatibility: Requires bash, curl, jq; env AI_API_URL, AI_API_KEY, optional AI_DECIDER_MODEL (default decider)
license: Apache-2.0
metadata:
  endpoint: "${AI_API_URL%/}/systemone (no /v1; strip trailing slash)"
  auth: "Bearer AI_API_KEY (env only, never logged)"
  model: "${AI_DECIDER_MODEL:-decider}"
---

# decider-ask

General preference choice for any 2 (extendable to N) caller-defined options.
Returns a calibrated `choice` pick in one forward pass via the System One
decider.

## Terminology (read first)

- `decider` has three meanings: (1) the role (this gate), (2) the Mapika
  open-weight System One model family name, (3) this task's default `model`
  id alias (`decider`). The endpoint is `$AI_API_URL`-configured; never claim
  it IS TypeSafe or Mapika.
- Question types: `choice` (named options), `noul` ("yes/no" probability in
  [0,1]); `score` (ordered levels) is not used by this skill.
- v1 `confidence` semantics changed upstream; thresholds below are tunable
  placeholders pending 50-100 gold labels and must be recalibrated.

## When to use

- For any other A-vs-B (or N-option) "which do you prefer" decision with
  caller-defined options, when none of the 4 fixed skills fits.
- When the options, criteria, and context are supplied by the caller at
  call time (no fixed choice set lives in this skill).

| If the decision is … | Use … |
|---|---|
| plan approval / risk gate | `decider-plan-gate` |
| rm/migration/push/deploy/mass-edit gating | `decider-tool-gate` |
| test-failure triage | `decider-test-triage` |
| continue/stop/loop control | `decider-continue-stop` |
| any other A-vs-B (or N-option) "which do you prefer" with caller-defined options | `decider-ask` (this skill) |

## Inputs to `state` construction

```json
{
  "options": {"A": "<meaning of A>", "B": "<meaning of B>"},
  "context": "<background facts>",
  "goal": "<what the pick is for>",
  "constraints": "<hard requirements>",
  "evidence": "<truncated supporting material>"
}
```

For N > 2, extend `options` with `C…N` keys. Truncate context/evidence:
total request body MUST be <=32 KiB; 1-8 questions per call (this skill
uses 1-2).

## Questions to ask

- `q_pick` (`choice`, REQUIRED): `instructions: "Which option is preferred
  given the state?"`, `criteria`: caller-defined map of 2..N entries
  (`{"A":"<what A means>","B":"<what B means>"}`; extend keys for N>2).
  Caller MUST define criteria per call — no fixed set.
- `q_conf` (`noul`, OPTIONAL): `instructions: "Is the preferred option
  clearly better (vs toss-up)?"`, for confidence signal.

`jq -n` snippet (run from this skill root):

```bash
STATE_JSON=$(jq -n --arg a "$OPT_A" --arg b "$OPT_B" --arg ctx "$CONTEXT" '{options:{A:$a,B:$b}, context:$ctx}')
QUESTIONS_JSON=$(jq -n '{q_pick:{type:"choice", instructions:"Which option is preferred given the state?", criteria:{A:"<meaning of A>", B:"<meaning of B>"}}, q_conf:{type:"noul", instructions:"Is the preferred option clearly better (vs toss-up)?"}}')
scripts/decide.sh --state "$STATE_JSON" --questions "$QUESTIONS_JSON" > resp.json
```

## Thresholds / decision table (tunable placeholders)

| Condition | Action |
|---|---|
| highest-probability option, margin >= 0.05, `q_conf` absent or >= 0.5 | pick: take the winning option |
| tie (Δp < 0.05) or missing fields | fail closed to ask/escalate, never silently pick |
| `q_conf` present and < 0.5 | treat as toss-up: ask human |

Cutoffs are tunable placeholders pending 50-100 gold-label recalibration.

## Do NOT use

- For plan approval (use `decider-plan-gate`); risky tool calls
  (use `decider-tool-gate`); test triage (use `decider-test-triage`);
  loop control (use `decider-continue-stop`).
- As a substitute for opencode `permission: ask` — this skill informs the
  choice; the permission system still enforces it.

## Fail-closed + error handling

- Missing env: transport exits non-zero
  (`: "${AI_API_URL:?...}"` / `: "${AI_API_KEY:?...}"`) — treat as
  ask/escalate, do not pick.
- 401: bad/missing key, do NOT retry. 422: fix `criteria`/schema, no retry.
  429: back off. 529/5xx: already retried once via curl flags; escalate this
  call. Errors print `Bearer <redacted>`, never the key.
- Never `echo $AI_API_KEY`, never `set -x` with the key in env, never write
  the key to disk, logs, or SKILL.md. Endpoint is always
  `${AI_API_URL%/}/systemone` (strip trailing slash, no `/v1`).

## Worked parse example

```bash
# (response already in resp.json from the call above)
PICK=$(jq -e -r '.answers.q_pick.choice' resp.json)
jq -e '.answers.q_pick.probabilities' resp.json
echo "pick=$PICK"
```
