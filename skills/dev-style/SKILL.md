---
name: dev-style
description:
    Use ONLY when writing or reviewing Bash or C# code style, naming, formatting, or file
    conventions in mbT projects.
---

# dev-style — Bash / C# formatting and naming

## All languages

- Indent 4 spaces.
- A "word" has no internal spaces incl. acronyms → `MyRpc` not `MyRPC`.

## Bash

- Use full-length args only; short forms allowed only for `-f` (force) / `-r` (recursive).
- Globals use `UPPER_SNAKE_CASE`; functions and locals use `snake_case`.

## C#

- Classes, methods, enums, public members, namespaces use `PascalCase`.
- Locals and params use `camelCase`.
- Private, protected, internal, and protected-internal fields and props use `_camelCase`.
- Interfaces use `I*` prefix.
- Filenames and dirs use `PascalCase` (e.g. `MyFile.cs`).
- Modifier order: `public protected internal private new abstract virtual override sealed static readonly extern unsafe volatile async`.
