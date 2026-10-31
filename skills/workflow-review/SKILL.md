---
name: workflow-review
description: >-
    Review current changes, a module, or a whole codebase for correctness, regressions, security,
    tests, and design. Use for code review, architecture review, and pre-merge assessment.
---

# Workflow: Review

Assess existing work without changing it. The output is a prioritized review, not a patch.

## Use when

- The user asks to review a diff, PR, module, architecture, or codebase.
- The user wants a second opinion before merging or continuing.

## Scope

Accept one of:

- `changes`: current uncommitted or branch diff.
- `path`: a file, module, or directory.
- `codebase`: whole repository.

A focus such as `security` or `tests` narrows the lenses; it does not replace the scope. If the
scope is ambiguous, ask at depth 0. Otherwise choose the narrowest scope that answers the request
and state it.

## Artifacts

- `review-X.md`: one artifact per lens or module.
- `review.md`: merged review.
- `verification.md`: verifier results.

## Phases

1. Define the review
    - Restate scope, change intent, and acceptance criteria.
    - Pick 3-5 lenses: correctness, regressions, security, tests, architecture, performance,
      maintainability, or a project-specific focus.
    - Do not run every lens on every file; assign lenses to the areas where they matter.

2. Map
    - For `codebase` or a large `path`, survey structure, entry points, data flow, dependencies, and
      hotspots before fanning out.
    - For `changes`, read the diff and the affected callers first.

3. Fan out
    - Launch one `reviewer` per lens or module, in parallel, with:
        - scope and files
        - focus and checklist
        - severity and confidence rubric
        - its unique artifact path
    - Cap the fan-out at five. Keep the review clean-context: do not pass the implementation
      rationale unless it is needed to judge intent.

4. Verify
    - Check high-severity findings against the code. Use `verifier` when a finding depends on
      runtime behavior or a disputed interpretation.
    - Mark each finding `confirmed`, `suspected`, or `needs-repro`.

5. Synthesize
    - Merge into `review.md`, deduplicated and ranked.
    - Identify systemic issues that span findings.
    - State coverage: what was reviewed, what was skipped, and why.

6. Report
    - Write `report.md` with Summary, Scope, Findings by severity, Systemic issues, Verification,
      Coverage gaps, Recommendation (approve, approve with follow-ups, or block).

## Gates

- No source changes.
- Every finding has `path:line`, evidence, impact, and status.
- The review states its scope and coverage gaps.
- A clean review is not an exhaustive review; say what was not checked.
- Approval requires the project's checks to pass and no confirmed high-severity finding to remain.
