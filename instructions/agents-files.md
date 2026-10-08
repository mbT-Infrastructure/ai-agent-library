# Persistent agent-internal files

All agent-internal files **not** intended for the user to read but to persist beyond the session
must go in `./.agent/`:

- project-scoped scratch notes, plans, TODOs, research
- Create the `./.agent/` subdirectory if it does not exist.
- Never write these files to repo root, `/tmp`, or source dirs.
- Only files explicitly requested by the user go elsewhere.

# Temp files

- For temp files always run `mktemp --tmpdir --directory agent-XXXXXX` first and only use that dir.
- Never write directly to `/tmp`, never reuse other runs dirs.
- Make sure the folder is deleted when the session ends.
