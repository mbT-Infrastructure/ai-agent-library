---
name: decider-test-triage
description: Decider test-failure triage router. Call when tests fail to route to fix_code, fix_test, flaky_infra, or needs_human with a confidence score, stopping fix loops. Use for test failure triage route fix loop.
compatibility: Requires bash, curl, jq; env AI_API_URL, AI_API_KEY, optional AI_DECIDER_MODEL (default decider)
license: Apache-2.0
metadata:
  endpoint: "${AI_API_URL%/}/systemone (no /v1; strip trailing slash)"
  auth: "Bearer AI_API_KEY (env only, never logged)"
  model: "${AI_DECIDER_MODEL:-decider}"
---

# decider-test-triage

Test-failure triage router. After a test failure, routes the retry loop
deterministically instead of re-asking the primary model each iteration.

## Terminology (read first)

- `decider` has three meanings: (1) the role (this router), (2) the Mapika
  open-weight System One model family name, (3) this task's default `model`
  id alias (`decider`). The endpoint is `$AI_API_URL`-configured; never claim
  it IS TypeSafe or Mapika.
- Question types: `choice` (named options), `score` (ordered levels, returns
  fractional expectation), `noul` (not used by this skill).
- v1 `confidence` semantics changed upstream; thresholds below are tunable
  placeholders pending 50-100 gold labels and must be recalibrated.

## When to use

- Any test/command failure after a code change, before retrying the fix.
- Repeated failures (suspected flaky infra or fix loop).

## Do NOT use

- For plan gating (use `decider-plan-gate`) or risky tool allow/deny
  (use `decider-tool-gate`).
- When failure output is missing: collect truncated logs first; do not call
  with an empty state.
- When env is unset: fail closed to `needs_human`.

## Inputs to `state` construction

```json
{
  "failing_tests": ["<names>"],
  "output_tail": "<last ~100 lines of failure output>",
  "diff_summary": "<truncated diff of recent change>",
  "attempt": "<retry count, 0-based>"
}
```

Truncate output/diffs: total request body MUST be <=32 KiB; 1-8 questions per
call (this skill uses 2). Never paste secrets from logs.

## Questions to ask

- `q_route` (`choice`): `instructions: "Where should the retry go next?"`,
  `criteria: {"fix_code":"production code is wrong, patch it",
  "fix_test":"test/expectation is wrong, update test",
  "flaky_infra":"flaky test or infra, re-run without code change",
  "needs_human":"ambiguous, needs human"}`.
- `q_conf` (`score`): `instructions: "Confidence in the route."`,
  `criteria: ["guess","weak","moderate","strong","certain"]`
  (5 levels, indices 0-4).

`jq -n` snippet (run from this skill root):

```bash
STATE_JSON=$(jq -n --arg out "$FAIL_TAIL" --arg diff "$DIFF_SUM" '{output_tail:$out, diff_summary:$diff}')
QUESTIONS_JSON=$(jq -n '{q_route:{type:"choice", instructions:"Where should the retry go next?", criteria:{fix_code:"production code is wrong, patch it", fix_test:"test/expectation is wrong, update test", flaky_infra:"flaky test or infra, re-run without code change", needs_human:"ambiguous, needs human"}}, q_conf:{type:"score", instructions:"Confidence in the route.", criteria:["guess","weak","moderate","strong","certain"]}}')
scripts/decide.sh --state "$STATE_JSON" --questions "$QUESTIONS_JSON" > resp.json
```

## Thresholds / decision table (tunable placeholders)

`q_conf` returns fractional `score` expectation in [0,4].

| Condition | Action |
|---|---|
| `route=X AND conf>=2` | act on route X (fix_code / fix_test / flaky_infra) |
| `conf<2 OR route=needs_human` | needs_human: escalate with logs |
| `attempt>=3` | escalate regardless (cap 3 auto-retries) |

Log route + confidence as the decision receipt.

## Fail-closed + error handling

- Missing env: transport exits non-zero
  (`: "${AI_API_URL:?...}"` / `: "${AI_API_KEY:?...}"`) — treat as
  `needs_human`.
- 401: bad/missing key, do NOT retry. 422: fix `criteria`/schema, no retry.
  429: back off. 529/5xx: already retried via curl flags; escalate.
  Errors print `Bearer <redacted>`, never the key.
- Never `echo $AI_API_KEY`, never `set -x` with the key in env, never write
  the key to disk, logs, or SKILL.md. Endpoint is always
  `${AI_API_URL%/}/systemone` (strip trailing slash, no `/v1`).

## Worked parse example

```bash
# (response already in resp.json from the call above)
ROUTE=$(jq -e -r '.answers.q_route.choice' resp.json)
CONF=$(jq -e '.answers.q_conf.score' resp.json)
echo "route=$ROUTE conf=$CONF"
```
