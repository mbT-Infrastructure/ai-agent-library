---
name: workflow-implement
description: >-
    Plan, implement, and review a code, config, docs, or test change. Use when the user asks to
    build, fix, refactor, migrate, or change project files. Do not use for read-only research,
    reviews, or bug hunts.
---

# Workflow: Implement

Change project files through one writer and an independent review.

## Use when

- The user asks for a concrete change to code, config, docs, tests, or infrastructure.
- The change has acceptance criteria that can be verified.

Do not use for open-ended reviews, research, or defect discovery with no requested fix. Use
`workflow-bug-hunt`, `workflow-review`, or `workflow-research` first.

## Roles

- `planner`: explores and writes `plan.md`. Read-only.
- `implementer`: the only source writer. One at a time.
- `reviewer`: reviews the combined result. Read-only.
- `verifier`: verifies a risky or disputed acceptance criterion.

## Artifacts

- `request.md`: verbatim request.
- `plan.md`: goal, context, files, ordered steps, verification, out of scope, splits.
- `report.md`: summary, steps, files changed, verification, deviations, follow-ups.
- `review-X.md`: review findings.

## Phases

1. Scope
    - Restate the goal and acceptance criteria.
    - Identify constraints, non-goals, and the project's checks.
    - At depth 0, ask about ambiguity before planning.

2. Plan
    - Launch `planner` with the goal, constraints, `TASK_DIR`, and instruction to write `plan.md`.
    - Require scope, files to touch, ordered steps, verification, out of scope, and a
      `Candidate splits` section.

3. Plan review
    - Read `plan.md`. Check completeness, simplicity, and alignment with `request.md`.
    - If imperfect, give concrete feedback and repeat. Never build on a flawed plan.

4. Execute
    - For each step, launch `implementer` with the relevant plan section and the instruction to
      report changed files and checks run.
    - One implementer at a time. Never run two on overlapping files.
    - If a step is too large for one context, run it as sequential sub-steps in the same task
      folder. Do not spawn a child orchestrator by default.

5. Review
    - Launch `reviewer` on the combined changes; require `review-X.md`.
    - Pass confirmed findings to `implementer`, then re-review. Stop after three rounds and escalate
      with the remaining findings.
    - A child review covers its slice only. Always review the seams at this node.

6. Verify
    - Compare the diff against `plan.md` and `request.md`.
    - Run `git status`; no stray files outside `.agent/` and intended changes.
    - Confirm the project's checks passed and `reviewer` approved.
    - Run the end-to-end or cross-step check that individual steps could not cover.

7. Report
    - Write `report.md` with Summary, Steps, Files changed, Verification, Deviations, Follow-ups.

## Gates

- The orchestrator never edits source. Only `implementer` writes.
- Every acceptance criterion is verified or explicitly marked unverified.
- `reviewer` approves before the workflow finishes.
- No commit, push, or branch change without user approval.

## Splits

Split a step only when it has at least three ordered substeps, touches at least two independently
verifiable areas, is verifiable on its own, and shares no files with a sibling. When in doubt, keep
it a leaf.
