---
name: dev-cli-env
description:
    Use ONLY when parsing CLI args, choosing env var names, returning exit codes, or choosing
    backend/frontend dev ports in mbT projects.
---

# dev-cli-env — CLI args, env vars, exit codes, ports

Fixed project values. Reuse exact names; never invent a near-synonym.

## Ports

- Backend: `8080`
- Frontend: `8000`

## CLI args

Kebab-case, `--`-prefixed:

| Arg                    | Meaning                              |
| ---------------------- | ------------------------------------ |
| `--ai-model`           | AI model name                        |
| `--bandwidth`          | Bandwidth limit                      |
| `--buffer`             | Buffer size                          |
| `--create-checksum`    | Create checksum file                 |
| `--detach`             | Run detached                         |
| `--dry-run`            | Simulate without changes             |
| `--env VARIABLE=VALUE` | Set environment variable             |
| `--fail`               | Fail on error                        |
| `--id`                 | Identifier                           |
| `--image IMAGE`        | Container image                      |
| `--no-network`         | Disable network                      |
| `--output PATH`        | Output path                          |
| `--os OS`              | Operating system                     |
| `--platform PLATFORM`  | Target platform (e.g. `linux/amd64`) |
| `--proxychains FILE`   | Proxychains config file              |
| `--publish`            | Publish ports                        |
| `--replace`            | Replace existing                     |
| `--silent`             | Suppress output                      |
| `--threads`            | Thread count                         |
| `--user USER`          | User name                            |

## Env vars

Uppercase with underscores. Full list — key subset:

- `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_USERNAME` (default admin)
- `AI_API_KEY` / `AI_API_URL` / `AI_MODEL`
- `DATABASE_URL` (scheme `postgresql://HOST/DATABASE`) / `DATABASE_USERNAME` / `DATABASE_PASSWORD`
- `EMAIL_HOST` / `EMAIL_PORT` (default `465`) / `EMAIL_USERNAME` / `EMAIL_PASSWORD` / `EMAIL_FROM`
- `OIDC_CLIENT_ID` / `OIDC_CLIENT_SECRET` / `OIDC_ISSUER_URL` / `OIDC_FORCE`
- `SERVER_URL` / `SERVER_USERNAME` / `SERVER_PASSWORD` / `SERVER_KEY` / `SERVER_IDENTITY`
- `FRONTEND_URL`
- `DOMAIN`
- `PROXY_URL` (protocol://USERNAME:PASSWORD@HOST:PORT)
- `TRUSTED_PROXY`
- `NETWORK` / `NETWORK_ROUTE` (CIDR)
- `SOURCE_ADDRESS` / `TARGET_ADDRESS` (HOST:PORT)
- `INPUT_PATH` / `OUTPUT_PATH`
- `NUM_THREADS` / `NUM_TRANSFERS` / `BATCH_SIZE`
- `MAX_BANDWIDTH`
- `REQUEST_TIMEOUT` / `DURATION` / `INTERVAL` / `CRON_SCHEDULE` / `RUN_AT_STARTUP` / `RUN_ON_IDLE`
- `CREATE_CHECKSUM` / `BUILDER_EXPORT_ARCHIVE`
- `EXIT_ON_FINISH`
- `USERNAME` / `PASSWORD` / `USER_GROUPS`
- Document-domain vars (`SENDER_*` / `RECEIVER_*`, `PRICE` / `PRICE_WORDS`, etc.)

## Exit codes

| Code | Meaning                   |
| ---- | ------------------------- |
| `0`  | Fine                      |
| `1`  | General error             |
| `10` | Missing dependency        |
| `11` | Already running           |
| `12` | Must be run as root       |
| `13` | Unknown/invalid args      |
| `14` | File/dir missing or empty |
| `15` | Missing arg/env           |
| `16` | File already exists       |

## Hard rules

- Reuse the exact name from the lists above; never invent a near-synonym.
- CLI args are kebab-case and `--`-prefixed.
- Env names are uppercase with underscores.
- Exit codes are limited to `0` / `1` / `10-16`.
