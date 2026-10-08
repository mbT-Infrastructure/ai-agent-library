---
name: decider-tool-gate
description:
    Decider risky tool-call gate. Call before running rm, migration, push, deploy, or mass edit to
    get an allow/ask/deny verdict plus irreversibility probability. Use for risky tool call gating
    rm migration push deploy mass edit.
compatibility:
    Requires bash, curl, jq; env AI_API_URL, AI_API_KEY, optional AI_DECIDER_MODEL (default decider)
license: Apache-2.0
metadata:
    endpoint: "${AI_API_URL%/}/systemone (no /v1; strip trailing slash)"
    auth: "Bearer AI_API_KEY (env only, never logged)"
    model: "${AI_DECIDER_MODEL:-decider}"
---

# decider-tool-gate

Risky tool-call gating for irreversible or production-affecting actions (`rm`, migrations, `push`,
deploys, mass edits). Returns a calibrated allow / ask / deny verdict in milliseconds.

## Terminology (read first)

- `decider` has three meanings: (1) the role (this gate), (2) the Mapika open-weight System One
  model family name, (3) this task's default `model` id alias (`decider`). The endpoint is
  `$AI_API_URL`-configured; never claim it IS TypeSafe or Mapika.
- Question types: `choice` (named options), `noul` ("yes/no" probability in [0,1]); `score` (ordered
  levels) is not used by this skill.
- v1 `confidence` semantics changed upstream; thresholds below are tunable placeholders pending
  50-100 gold labels and must be recalibrated.

## When to use

- Before `rm -rf`, file mass-delete/overwrite, DB migration, `git push`, deploy, chmod/chown, or any
  bulk edit touching >5 files or prod.
- When blast radius or reversibility is unclear.

## Do NOT use

- For plan approval (use `decider-plan-gate`), test triage (use `decider-test-triage`), or loop
  control (use `decider-continue-stop`).
- As a substitute for opencode `permission: ask` — this skill informs the allow/ask/deny decision;
  the permission system still enforces it.
- When env is unset: fail closed (deny), do not run the tool.

## Inputs to `state` construction

```json
{
    "command": "<exact command or tool call>",
    "diff_stat": "<truncated diff --stat>",
    "blast_radius": "<files/envs affected>",
    "reversible": "<yes/no + how>",
    "env": "<dev/staging/prod>"
}
```

Truncate diffs/logs: total request body MUST be <=32 KiB; 1-8 questions per call (this skill uses
2).

## Questions to ask

- `q_allow` (`choice`): `instructions: "Verdict for this tool call."`,
  `criteria: {"allow":"safe to run now", "ask_human":"needs human confirmation first", "deny":"must not run"}`.
- `q_irrev` (`noul`): `instructions: "Is this action irreversible or production-affecting?"`, no
  `criteria` (or `{"true":"irreversible/prod","false":"reversible/dev-only"}`).

`jq -n` snippet (run from this skill root):

```bash
STATE_JSON=$(jq -n --arg cmd "$CMD" --arg env "$TARGET_ENV" '{command:$cmd, env:$env}')
QUESTIONS_JSON=$(jq -n '{q_allow:{type:"choice", instructions:"Verdict for this tool call.", criteria:{allow:"safe to run now", ask_human:"needs human confirmation first", deny:"must not run"}}, q_irrev:{type:"noul", instructions:"Is this action irreversible or production-affecting?"}}')
scripts/decide.sh --state "$STATE_JSON" --questions "$QUESTIONS_JSON" > resp.json
```

## Thresholds / decision table (tunable placeholders)

| Condition                     | Action                          |
| ----------------------------- | ------------------------------- |
| `allow AND irrev<0.4`         | allow: run the tool             |
| `ask_human OR 0.4<=irrev<0.6` | ask: request human confirmation |
| `deny OR irrev>=0.6`          | deny: do not run, escalate      |

On ties or missing fields, take the more restrictive action (deny > ask > allow). Log verdict +
`irrev` probability as the decision receipt.

## Fail-closed + error handling

- Missing env: transport exits non-zero (`: "${AI_API_URL:?...}"` / `: "${AI_API_KEY:?...}"`) —
  treat as deny.
- 401: bad/missing key, do NOT retry. 422: fix `criteria`/schema, no retry. 429: back off. 529/5xx:
  already retried once via curl flags; deny this call. Errors print `Bearer <redacted>`, never the
  key.
- Never `echo $AI_API_KEY`, never `set -x` with the key in env, never write the key to disk, logs,
  or SKILL.md. Endpoint is always `${AI_API_URL%/}/systemone` (strip trailing slash, no `/v1`).

## Worked parse example

```bash
# (response already in resp.json from the call above)
VERDICT=$(jq -e -r '.answers.q_allow.choice' resp.json)
IRREV=$(jq -e '.answers.q_irrev.noul' resp.json)
echo "verdict=$VERDICT irrev=$IRREV"
```
