#!/usr/bin/env bash
set -euo pipefail
readonly FILE_PATTERN='\.(svelte|ts|js|css|html|kt)$'
readonly COLOR_PATTERN='#[0-9a-fA-F]{3,8}\b|rgb\(|hsl\('
readonly CTA_PATTERN='--md-filled-button-container-color: var(--md-sys-color-tertiary)'
FAILURES=0
WARNINGS=0
FILE_COUNT=0
function report_matches {
    local file="$1"
    local matches="$2"
    local message="$3"
    local line
    while IFS= read -r line; do
        printf '%s\n' "${file}:${line}: ${message}" >&2
        FAILURES=$((FAILURES + 1))
    done <<< "$matches"
}
function scan {
    local file="$1"
    local pattern="$2"
    local message="$3"
    local matches
    matches="$(grep --line-number --extended-regexp -- "$pattern" "$file" || true)"
    if [[ -n "$matches" ]]; then
        report_matches "$file" "$matches" "$message"
    fi
}
function collect_files {
    if (( $# > 0 )); then
        printf '%s\n' "$@"
    else
        git diff --name-only HEAD
    fi | grep --extended-regexp "$FILE_PATTERN" || true
}
function check_web_colors {
    local file="$1"
    local name
    name="$(basename "$file")"
    if [[ "$name" == "tokens.css" || "$name" == "theme.ts" || "$name" == *.tokens.* ]]; then
        return 0
    fi
    scan "$file" "$COLOR_PATTERN" "hardcoded color (use var(--md-sys-color-*) or var(--cd-*))"
}

function check_kotlin_colors {
    local file="$1"
    local name
    name="$(basename "$file")"
    if [[ "$name" == Cd*.kt ]]; then
        return 0
    fi
    scan "$file" 'Color\(0x' "hardcoded Color(0x...) (use MaterialTheme.colorScheme)"
}

function check_file {
    local file="$1"
    local count
    case "$file" in
        *.svelte|*.ts|*.js|*.css|*.html) check_web_colors "$file" ;;
        *.kt) check_kotlin_colors "$file" ;;
    esac
    scan "$file" \
        'ColorScheme\.fromSeed|dynamicColor|dynamicDarkColorScheme|dynamicLightColorScheme' \
        "dynamic color is forbidden"
    scan "$file" '--md-ref-palette-' "--md-ref-palette- override is forbidden"
    count="$(grep --count --fixed-strings -- "$CTA_PATTERN" "$file" || true)"
    if (( count > 1 )); then
        printf '%s: warning: %d orange CTA overrides in one file\n' "$file" "$count" >&2
        WARNINGS=$((WARNINGS + 1))
    fi
}

mapfile -t FILES < <(collect_files "$@")
for FILE in "${FILES[@]}"; do
    [[ -f "$FILE" ]] || continue
    FILE_COUNT=$((FILE_COUNT + 1))
    check_file "$FILE"
done
printf 'check-design: %d file(s), %d error(s), %d warning(s)\n' \
    "$FILE_COUNT" "$FAILURES" "$WARNINGS"
(( FAILURES == 0 ))
