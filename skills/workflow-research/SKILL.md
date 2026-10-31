---
name: workflow-research
description: >-
    Research a question using code, docs, and web sources, then synthesize a cited answer with
    confidence and tradeoffs. Use for technology comparisons, architecture options, and open-ended
    investigations.
---

# Workflow: Research

Answer a question with evidence. The output is a decision-ready brief, not a link dump.

## Use when

- The user asks what, why, which option, or what is the state of the art.
- The answer needs external sources, internal code, or both.

Do not use for a quick fact that one search resolves; answer directly instead.

## Artifacts

- `research-<subquestion>.md`: one artifact per researcher.
- `sources.md`: source list with dates and quality notes.
- `research.md`: merged brief.
- `verification.md`: claim checks.

## Phases

1. Frame
    - Restate the question and the decision it informs. Ask at depth 0 if the decision is unclear.
    - Set scope, freshness, source constraints, and the stopping condition.

2. Decompose
    - Split into 3-5 independent subquestions. Avoid overlapping searches.
    - For each, state the objective, the sources to prefer, and the output format.

3. Fan out
    - Launch multiple `researcher` in parallel, each with a unique artifact path.
    - Cap the first wave at five. Run a second wave only for a real gap.
    - Start broad, then narrow. Prefer primary sources and record dates.

4. Verify
    - Use `verifier` on the claims that drive the recommendation, not every sentence.
    - Mark claims `confirmed`, `refuted`, or `unverifiable`.
    - Resolve contradictions explicitly; do not average them.

5. Synthesize
    - Write `research.md` as one coherent answer. Do not paste subagent reports together.
    - Put the answer first, then evidence, alternatives, tradeoffs, recommendation, and open
      questions.
    - Keep a source list with title, URL or `path:line`, date, and credibility note.

6. Report
    - Write `report.md` with Summary, Question, Method, Answer, Confidence, Sources checked,
      Contradictions, Open questions, Recommended next step.

## Gates

- Every non-obvious factual claim has a source or a code reference.
- Fact, inference, and opinion are labelled.
- Source quality and date are recorded.
- The recommendation follows from the evidence and states its assumptions.
- No source changes.
