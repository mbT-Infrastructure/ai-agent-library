---
name: clarify
description: >-
    Interview the user until a shared understanding is reached.
---

# Clarify: interview to shared understanding

Interview the user relentlessly until you reach a shared understanding. Keep asking while a material
uncertainty remains, and stop only when you and the user can predict the same result.

## Use when

- Only at `DEPTH = 0`.
- The request leaves anything material unsettled.
- The user asks for a change, investigation, review, or research whose success is not yet testable.
- Multiple reasonable interpretations would produce different work.

## Artifacts

- `TASK_DIR/clarify.md`: the clarification decision record, based on this skill's
  `assets/clarify-template.md`.

## Method

Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already
settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the
whole frontier in one round.

Use the integrated tool to ask the user. Offer 2-4 mutually exclusive options. Put the recommended
option first.

Each round the user answers reshape the tree: settled decisions push the frontier outward and
unblock questions that depended on them. Recompute the frontier and ask the next round. A question
whose answer depends on another question still open in this round belongs to a _later_ round, not
this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the
environment (filesystem, tools, etc.), dispatch a `researcher` sub-agent to find it. Don't ask the
user for anything you could look up yourself. Don't block on it: a running exploration is an
unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report. Ask
the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The interview is done when the frontier is empty: every branch of the design tree visited, nothing
left silently assumed. Mark `clarify.md` `confirmed` only after the user approves the read-back.
