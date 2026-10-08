---
name: dev-repo-init
description:
    Use ONLY when initializing a new repository, running repository-template.sh, or configuring git
    branches, merge requests, or branch protection in mbT projects.
---

# dev-repo-init — repo init and git defaults

Rule: init via `repository-template.sh`; do not hand-roll.

## Git defaults

- Default branch: `main`.
- Merge requests: always suggest updating PR branches, auto-delete head branches, squash-only
  (default to PR title+description).
- Protect `main`: require PR + at least 1 approval, no force pushes.

## Base init

    git init --initial-branch main
    repository-template.sh all ci/github/all devcontainer

## Per-stack variants

### Android

    rm -rv .devcontainer/
    repository-template.sh builder/build.sh builder/android.sh ci/github/builder

- Compose Empty Activity, package `###DOMAIN_REVERSED###.###APPLICATION_NAME###`, minSdk 28 / target
  latest.
- `Version.txt` single source wiring in `build.gradle.kts` + `app/build.gradle.kts`.

### Docker

    rm -rv .devcontainer/
    repository-template.sh builder/build.sh builder/docker.sh ci/github/builder docker/container

### Go

    repository-template.sh --domain ###DOMAIN### builder/build.sh builder/go.sh go

### Python

    repository-template.sh python
    pip3-latest freeze --local > requirements.txt

### Svelte

    npx sv create

- Minimal + TypeScript + npm; patch `package.json` vite dev `--port 8000`; drop version key;
  `rm README.md .npmrc`.

### TypeScript

    npm install --save-dev typescript
    npx tsc --init --allowJs --outDir static/js --target es2020

- Strip comments and blank lines from `tsconfig.json`.
