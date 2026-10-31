# Persistent agent-internal files

All agent-internal files **not** intended for the user to read but to persist beyond the session
must go in `./.agent/`:

- project-scoped scratch notes, plans, TODOs, research
- Create the `./.agent/` subdirectory if it does not exist.
- Never write these files to repo root, `/tmp`, or source dirs.
- Only files explicitly requested by the user go elsewhere.

## Task artifacts

Orchestrated tasks keep their state in `.agent/<task>/` so agents can hand off work without
relying on chat history:

- `request.md`, `clarify.md`: verbatim user request and clarifications.
- `meta.md`: depth, parent, workflow, scale.
- `state.md`: decisions, open questions, next actions, artifact links.
- `plan.md`, `findings.md`, `sources.md`, `research.md`, `report.md`: workflow-specific artifacts.
- `step-*/`, `review-*.md`, `bugs-*.md`, `research-*.md`: child and specialist artifacts.

Write artifacts as you go. A subagent must read the artifacts it needs before starting and write
only its own artifact path.

# Temp files

- For temp files always run `mktemp --tmpdir --directory agent-XXXXXX` first and only use that dir.
- Never write directly to `/tmp`, never reuse other runs dirs.
- Make sure the folder is deleted when the session ends.
