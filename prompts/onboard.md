---
description: Fast project Overview
---

Summarize the current state of this project so I can start working quickly.

Be factual. Only report what you find in files, git, and configs. Don't guess. If something is
unclear, say so.

1. Overview
    - What is this project for?
    - Codebase type: [app / library / monorepo / infra / other]
    - Maturity: [new / active / maintenance / stale] + why
2. Stack
    - Languages, frameworks, package manager, build system
    - Runtime versions (.nvmrc, .python-version, Dockerfile, CI config)
    - Key dependencies
3. Structure
    - Top-level directory map (1 line per dir: purpose)
    - Where is entrypoint / main / CLI / API / UI?
    - Where are configs, tests, docs, scripts?
    - Important files to read first (max 10)
4. How to work here
    - How to install, run locally, build, test, lint, format (exact commands from package.json
      scripts, Makefile, justfile, README, CI)
    - Env vars / secrets needed?
    - Conventions
5. Git + current state
    - Uncommitted / untracked changes?
    - Recent work? Branches?
    - Open TODO/FIXME/HACK (max 10)?
6. Health + risks
    - Broken / missing: Readme, tests, CI, lockfile, .gitignore, ...?
    - Obvious tech debt, outdated deps, security red flags?
    - What would you check next?

Format: markdown with headers, bullets, tables where useful. Keep it below 1 page.
