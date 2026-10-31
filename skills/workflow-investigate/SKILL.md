---
name: workflow-investigate
description: >-
    Investigate, explain, or diagnose a behavior that is not yet a confirmed bug or a research
    question. Use for "why does this happen", "how does this work", and "what would happen if".
---

# Workflow: Investigate

Build an evidence-based explanation. Do not change code or present a guess as a conclusion.

## Use when

- The request is to understand, explain, trace, or diagnose.
- The issue is not yet a confirmed defect and not primarily external research.

## Artifacts

- `state.md`: hypotheses, evidence, and decisions.
- `report.md`: the explanation and its confidence.

## Phases

1. Frame
    - Restate the observed behavior, expected behavior, and scope.
    - List the questions that must be answered.

2. Map
    - Trace the relevant entry points, data flow, state, and configuration.
    - Identify the smallest set of files that can explain the behavior.

3. Test hypotheses
    - For each hypothesis, state the predicted evidence and check it.
    - Use history, tests, logs, or a minimal reproduction. Prefer converging evidence.
    - Drop hypotheses that do not survive.

4. Verify
    - Ask `verifier` to check the final explanation against the code or a reproduction.
    - Separate what is proven from what remains probable.

5. Report
    - Write `report.md` with Question, Answer, Evidence, Confidence, What was ruled out, Open
      questions, Recommended next step.

## Gates

- No source changes.
- The explanation cites `path:line` or a source.
- Uncertainty is explicit.
