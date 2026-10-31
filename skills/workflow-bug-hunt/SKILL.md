---
name: workflow-bug-hunt
description: >-
    Find, verify, and rank defects across a codebase without changing code. Use for bug hunts,
    audits, regression investigations, security defect discovery, and "find bugs" requests.
---

# Workflow: Bug Hunt

Produce a ranked, evidence-backed list of defects. Do not fix them in this workflow.

## Use when

- The user asks to find bugs, audit a codebase, investigate a regression, or assess risk.
- The output is a findings list, not a patch.

If the user asks to fix the findings, run this workflow first and then `workflow-implement` with the
approved subset.

## Artifacts

- `findings.md`: merged, ranked findings.
- `bugs-<area>.md`: one artifact per hunter, with a unique path.
- `verification.md`: verifier results.

## Phases

1. Frame
    - Record symptoms, scope, recent changes, existing tests, known issues, and risk areas.
    - Decide the areas that can be hunted independently.

2. Map
    - Survey entry points, trust boundaries, state transitions, error handling, and dependencies.
    - Pick 3-5 high-risk areas. Do not try to cover everything equally.

3. Fan out
    - Launch one `bug-hunter` per independent area, in parallel, with:
        - objective and files in scope
        - hypotheses to test
        - output format and severity rubric
        - its unique artifact path
    - Cap the fan-out at five. If there are more areas, run a second wave only when the first wave
      leaves a real gap.

4. Verify
    - Reproduce or trace each high-severity candidate. Use `verifier` when evidence is contested.
    - Drop candidates that cannot be supported. Mark the rest `confirmed`, `suspected`, or
      `needs-repro`.
    - Deduplicate findings that share a root cause.

5. Synthesize
    - Merge into `findings.md`, ranked by severity and confidence.
    - Group findings by root cause and note clusters that suggest a systemic problem.
    - Include a coverage statement: what was inspected, what was not, and where confidence is low.

6. Report
    - Write `report.md` with Summary, Scope, Findings count by severity, Top findings, Verification,
      Coverage gaps, Recommended next step.
    - Do not include fixes as if they were implemented.

## Severity

- `critical`: data loss, auth bypass, remote code execution, or a broken core path.
- `high`: common-path failure, security exposure, or a regression with no workaround.
- `medium`: edge-case failure, degraded behavior, or a risky pattern.
- `low`: minor correctness issue or a localized robustness gap.

## Gates

- No source changes.
- Every finding has `path:line`, evidence, impact, and status.
- Confirmed and suspected findings are separated.
- No duplicate IDs; no two artifacts claim the same finding without a cross-reference.
- The final report states coverage gaps and does not imply exhaustive coverage.

## Budget

- At most five hunters and two waves unless the user approves more.
- Stop when the top risks are covered and new areas stop producing new findings.
