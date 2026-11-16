# Persistent agent-internal files

All agent-internal files **not** intended for the user to read but to persist beyond the session
must go in `./.agent/`:

- project-scoped scratch, guides, memory, notes, plans, TODOs, research
- Create the `./.agent/` subdirectory if it does not exist.
- Never write these files to repo root, `/tmp`, or source dirs.
- Only files explicitly requested by the user go elsewhere.

## Task artifacts

Tasks keep their internal state in the task dir `.agent/<task>/` so agents can hand off work without
relying on chat history:

- `request.md`, `clarify.md`: verbatim user request and clarifications.
- `meta.md`: depth, parent, workflow, scale.
- `state.md`: decisions, open questions, next actions, artifact links.
- `plan.md`, `findings.md`, `sources.md`, `research.md`, `report.md`: workflow-specific artifacts.
- `step-*/`, `review-*.md`, `bugs-*.md`, `research-*.md`: child and specialist artifacts.

If a task needs artifacts and no task dir is given, create one with
`mkdir --parents ./.agent/$(timestamp.sh --no-whitespace)-TASKNAME` (`TASKNAME` in kebab-case).
Write artifacts as you go. A subagent must read the artifacts it needs before starting and write
only in its own artifact path.

When the task is finished, ask the user whether to remove the task dir. Name it and say what it
contains, and delete only after an explicit yes.

## Project guides

Keep things you struggled with in project guides: how to build, install or run something, device and
environment quirks, where things live, what does not work here. They are durable project memory so
the next session does not rediscover them at full cost.

- One file per subject in `./.agent/guides/`, named after the subject (for example
`testing-android-device.md`)
- Start the file with `Verified: <date> on <environment>`.
- Read first: check `./.agent/guides/` for the subject and read the guide before the first action it
  affects. Use its values instead of re-deriving them.
- Write as you go: add a dated line when something costs a retry. A failing command, a timeout, a
  workaround. Correct wrong entries instead of appendin. Delete what is no longer true.
- Keep it a guide, not a log: project- and device-specific facts only, short enough to re-read. No
  copy of a skill or tool help.

# Temp files

- For temp files always run `mktemp --tmpdir --directory agent-XXXXXX` first and only use that dir.
- Never write directly to `/tmp`, never reuse other runs dirs.
- Make sure the folder is deleted when the session ends.
