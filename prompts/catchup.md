---
description: Catchup changes since you last worked on the project
---

Summarize the current state of this project to resume work. Focus on delta, not basics.

If a reference is given by me, use it as resume point. If no reference is given, try to determine
when I last worked here from commits, AI-chat sessions/history, file mtimes, branches/tags, and
other sources. If you are not sure about your findings, ask me for the reference instead of assuming
one.

Be factual. Only report what you find in files, git, and configs. Don't guess. If something is
unclear, say so.

1. Resume point
    - Uncommitted / untracked changes? Stash list?
    - Current branch? Recent branches/tags?
    - Git log since resume point (or last 20)?
2. What changed
    - What was worked on since I left? Themes from commits/diffs?
    - New deps, migrations, breaking changes, config changes?
    - New TODO/FIXME/HACK?
3. Health now
    - Broken / missing: Readme, tests, CI, lockfile, .gitignore, ...?
    - Blockers, failing checks, merge conflicts, outdated branch?
    - What would you check next?
4. Next
    - Suggested next 3 steps to continue, with exact files/commands.

Format: markdown with headers, bullets, tables where useful. Keep it below 1 page.
