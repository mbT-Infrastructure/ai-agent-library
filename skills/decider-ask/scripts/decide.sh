#!/usr/bin/env bash
set -e -o pipefail
DEPENDENCIES=(curl jq)
ENDPOINT=""
ERROR_EXIT_CODE=0
HTTP_CODE=""
MODEL="${AI_DECIDER_MODEL:-decider}"
STATE_JSON=""
QUESTIONS_JSON=""
SILENT=false
SCRIPT_NAME="$(basename "$0")"
WORKING_DIR="${TMPDIR:-/tmp}/temp-$(basename "$0")-$BASHPID"

# Help message
for ARGUMENT in "$@"; do
    if [ "$ARGUMENT" == "-h" ] || [ "$ARGUMENT" == "--help" ]; then
        echo "Usage: $(basename "$0") [--silent] [--model MODEL_ID]" \
            "--state STATE_JSON --questions QUESTIONS_JSON"
        echo "Shared System One / Jev-class transport for decider-* skills."
        echo "Builds {model, state, questions} internally with jq and POSTs it to"
        echo "\"\${AI_API_URL%/}/systemone\", printing the response body to stdout."
        echo "Examples:"
        echo "    STATE='{\"command\":\"rm -rf /tmp/x\",\"env\":\"dev\"}'"
        echo "    QUESTIONS='{\"q_allow\":{\"type\":\"choice\",\"instructions\":\"Verdict for this tool call.\",\"criteria\":{\"allow\":\"safe to run now\",\"ask_human\":\"needs human confirmation first\",\"deny\":\"must not run\"}}}'"
        echo "    $(basename "$0") --state \"\$STATE\"" \
            "--questions \"\$QUESTIONS\" | jq -e '.answers'"
        echo "ARGUMENTs:"
        echo "    --state STATE_JSON        Inline JSON object for \"state\" (required)."
        echo "    --questions QUESTIONS_JSON Inline JSON object for \"questions\", 1-8 entries (required)."
        echo "    --model MODEL_ID          Override model id (default \"\${AI_DECIDER_MODEL:-decider}\")."
        echo "    --silent                  Suppress status messages, only errors."
        echo "Env (only source of truth):"
        echo "    AI_API_URL Required base URL, endpoint is \"\${AI_API_URL%/}/systemone\" (no /v1)."
        echo "    AI_API_KEY Required bearer key, env only, never logged, never written to disk."
        echo "    AI_DECIDER_MODEL Optional model id, fallback \"\${AI_DECIDER_MODEL:-decider}\"."
        echo "Exit codes:"
        echo "     0: Everything fine."
        echo "     1: General error (including transport/HTTP failure, see stderr for 401/422/429/5xx detail)."
        echo "    10: Missing dependency."
        echo "    13: Unknown or invalid arguments."
        echo "    14: Retired (no longer emitted, was missing file)."
        echo "    15: Missing argument."
        exit 0
    fi
done

# Fail-closed env guards (no defaults for URL/key).
: "${AI_API_URL:?AI_API_URL must be set}"
: "${AI_API_KEY:?AI_API_KEY must be set}"
MODEL="${AI_DECIDER_MODEL:-decider}"
ENDPOINT="${AI_API_URL%/}/systemone"

# Check dependencies
for CMD in "${DEPENDENCIES[@]}"; do
    if [[ -z "$(which "$CMD")" ]]; then
        echo "Error: \"${CMD}\" is missing!" >&2
        exit 10
    fi
done

function cleanup {
    rm -f -r "$WORKING_DIR"
}
trap cleanup EXIT

function redact {
    # Redact bearer value in any error output, never print the key.
    sed -e 's/Bearer .*/Bearer <redacted>/' "$TMP_ERR" >&2 || true
}

# Check arguments
while [[ "$#" -gt 0 ]]; do
    if [[ "$1" == "--silent" ]]; then
        SILENT=true
        shift
    elif [[ "$1" == "--model" ]]; then
        if [[ -z "${2:-}" ]]; then
            echo 'Error: Missing value for --model MODEL_ID.' >&2
            exit 15
        fi
        MODEL="$2"
        shift 2
    elif [[ "$1" == "--state" ]]; then
        if [[ -z "${2:-}" ]]; then
            echo 'Error: Missing value for --state STATE_JSON.' >&2
            exit 15
        fi
        STATE_JSON="$2"
        shift 2
    elif [[ "$1" == "--questions" ]]; then
        if [[ -z "${2:-}" ]]; then
            echo 'Error: Missing value for --questions QUESTIONS_JSON.' >&2
            exit 15
        fi
        QUESTIONS_JSON="$2"
        shift 2
    elif [[ "$1" == "--"* ]]; then
        echo "Error: Unknown argument: \"$1\"" >&2
        exit 13
    else
        echo 'Error: Positional REQUEST_JSON_FILE no longer supported.' \
            'Pass --state ... --questions ... (request is built inside this script).' >&2
        exit 13
    fi
done

if [[ -z "$STATE_JSON" ]]; then
    echo 'Error: Missing --state STATE_JSON.' >&2
    exit 15
fi
if [[ -z "$QUESTIONS_JSON" ]]; then
    echo 'Error: Missing --questions QUESTIONS_JSON.' >&2
    exit 15
fi
if ! jq -e . >/dev/null 2>&1 <<<"$STATE_JSON"; then
    echo 'Error: --state is not valid JSON.' >&2
    exit 13
fi
if ! jq -e 'type=="object"' >/dev/null 2>&1 <<<"$STATE_JSON"; then
    echo 'Error: --state must be a JSON object.' >&2
    exit 13
fi
if ! jq -e . >/dev/null 2>&1 <<<"$QUESTIONS_JSON"; then
    echo 'Error: --questions is not valid JSON.' >&2
    exit 13
fi
if ! jq -e 'type=="object"' >/dev/null 2>&1 <<<"$QUESTIONS_JSON"; then
    echo 'Error: --questions must be a JSON object.' >&2
    exit 13
fi

mkdir "$WORKING_DIR"
cd "$WORKING_DIR"
REQ_FILE="${WORKING_DIR}/req.json"
jq -n --arg model "$MODEL" --argjson state "$STATE_JSON" --argjson questions "$QUESTIONS_JSON" \
  '{model:$model, state:$state, questions:$questions}' > "$REQ_FILE"
ERROR_EXIT_CODE=0

TMP_OUT="${WORKING_DIR}/response.json"
TMP_ERR="${WORKING_DIR}/curl.stderr"
TMP_CODE="${WORKING_DIR}/http.code"

# Conservative limits: body <=32 KiB, 1-8 questions per call.
REQ_BYTES=$(wc -c <"$REQ_FILE" | tr -d ' ')
if [[ "$REQ_BYTES" -gt 32768 ]]; then
    echo "Error: Request body ${REQ_BYTES} bytes exceeds 32 KiB cap, truncate state/logs/diffs and retry." >&2
    exit 13
fi
if ! jq -e 'has("model") and has("state") and has("questions")' "$REQ_FILE" >/dev/null 2>&1; then
    echo "Error: Internal request shape invalid (expected {model, state, questions})." >&2
    exit 13
fi
QCOUNT=$(jq '.questions | length' "$REQ_FILE" 2>/dev/null || echo 0)
if [[ "$QCOUNT" -lt 1 || "$QCOUNT" -gt 8 ]]; then
    echo "Error: Question count ${QCOUNT} outside 1-8 range, split into 1-8 questions per call." >&2
    exit 13
fi

CURL_EXIT=0
set +e
curl --fail-with-body --show-error --silent \
    --max-time 20 --connect-timeout 5 \
    --retry 2 --retry-delay 1 \
    -H "Authorization: Bearer ${AI_API_KEY}" \
    -H 'Content-Type: application/json' \
    -d @"$REQ_FILE" "$ENDPOINT" \
    -o "$TMP_OUT" -w "%{http_code}" >"$TMP_CODE" 2>"$TMP_ERR"
CURL_EXIT=$?
set -e
if [[ -f "$TMP_CODE" ]]; then
    HTTP_CODE=$(tr -d ' \n' <"$TMP_CODE" || true)
    rm -f "$TMP_CODE"
fi

if [[ "$CURL_EXIT" -ne 0 ]]; then
    case "${HTTP_CODE:-}" in
        401)
            echo "Error: 401 Unauthorized, bad/missing AI_API_KEY. Do NOT retry, check env wiring. Failing closed." >&2
            redact
            ERROR_EXIT_CODE=1
            ;;
        422)
            echo "Error: 422 Unprocessable, schema/criteria violation. No retry. Redacted body:" >&2
            sed -e 's/Bearer .*/Bearer <redacted>/' "$TMP_OUT" >&2 || true
            redact
            ERROR_EXIT_CODE=1
            ;;
        429)
            echo "Error: 429 Rate-limited, back off and retry later. Failing closed for this call." >&2
            redact
            ERROR_EXIT_CODE=1
            ;;
        529|500|502|503|504)
            echo "Error: ${HTTP_CODE:-5xx} Server/overloaded, curl retried (see flags), giving up. Failing closed." >&2
            redact
            ERROR_EXIT_CODE=1
            ;;
        *)
            echo "Error: Request failed (curl exit ${CURL_EXIT}, http ${HTTP_CODE:-unknown}). Failing closed." >&2
            redact
            ERROR_EXIT_CODE=1
            ;;
    esac
else
    # Success: emit response body to stdout
    cat "$TMP_OUT"
fi

if [[ "$SILENT" != true ]]; then
    if [[ "$ERROR_EXIT_CODE" -eq 0 ]]; then
        echo "$SCRIPT_NAME finished." >&2
    else
        echo "$SCRIPT_NAME failed." >&2
    fi
fi
exit "$ERROR_EXIT_CODE"
