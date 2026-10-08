#!/usr/bin/env bash
set -e -o pipefail

COMPRESS_COMMAND=(compress.sh)
DEPENDENCIES=(find)
PULL_POLICY="${PULL_POLICY:-always}"
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
WORKING_DIR="${TMPDIR:-/tmp}/temp-$(basename "$0")-$(cat /proc/sys/kernel/random/uuid)"

# Help message
for ARGUMENT in "$@"; do
    if [ "$ARGUMENT" == "-h" ] || [ "$ARGUMENT" == "--help" ]; then
        echo "Usage: $(basename "$0") [ARGUMENT]"
        echo "Create archives for all config sets."
        exit
    fi
done

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

mkdir "$WORKING_DIR"

PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION="$(cat Version.txt)"
cd "$PROJECT_DIR"
mkdir --parents builds

mkdir "${WORKING_DIR}/ai-agent-library"
cp --recursive agents instructions prompts skills "${WORKING_DIR}/ai-agent-library"
OUTPUT="builds/ai-agent-library-${VERSION}"
if [[ -z "$(which "${COMPRESS_COMMAND[0]}")" ]]; then
    CONTAINER_NAME="$(basename "${PROJECT_DIR}")-builder-$(basename "$0")"
    COMPRESS_COMMAND=(
        docker run --interactive --name "$CONTAINER_NAME" --pull "$PULL_POLICY" --read-only --rm \
            --tmpfs "/media/user/.cache:size=64M" \
            --volume "${WORKING_DIR}:${WORKING_DIR}" \
            --volume "${PROJECT_DIR}:/media/workdir" \
            --workdir /media/workdir
            docker.io/madebytimo/scripts compress.sh
    )
fi
rm --force "${OUTPUT}."*
"${COMPRESS_COMMAND[@]}" --output "$OUTPUT" "${WORKING_DIR}/ai-agent-library"
rm -r "${WORKING_DIR}/ai-agent-library"
