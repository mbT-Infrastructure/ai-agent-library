---
description: Continue an aborted session as if it never stopped
---

You were interrupted. Resume where you left off.

- No history? Stop and ask for a transcript; don't guess.
- Reconstruct: request, done steps, in-flight step, subagents, pending gate.
- Verify claimed writes; interrupted writes may be partial.
- Resume the earliest incomplete action; re-run checks invalidated by the stop.
- Subagents: resume the subagent session if possible, else re-dispatch with brief, done/remaining.
- Never re-ask or redo settled work.
- Honor unpassed gates.
- Continue from where it stopped and finish the work.
