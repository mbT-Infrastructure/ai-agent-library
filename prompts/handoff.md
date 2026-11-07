---
description: Prepare handoff to a fresh session
---

Prepare a handoff so a fresh session can continue the work.

- Bring every artifact in the task dir up to date.
- Update `TASK_DIR/state.md` so it contains the done steps, the in-flight step, open questions and
  pending decisions, unpassed gates, and the next action with links to artifacts.

This session will end after the handoff.

Answer with:

1. A minimal summary of the current state
2. A 1-3 sentence initial prompt that names the task dir, tells the new agent to read
   `TASK_DIR/state.md` and `meta.md` first, and continues where you left off.
