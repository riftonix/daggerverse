#! /bin/sh

SCRIPT_PATH=$(cd "$(dirname "$0")" && pwd)
MODULE_PATH=$(cd "${SCRIPT_PATH}/.." && pwd)
cd "$MODULE_PATH" || exit

dagger call --progress=plain --source=".." get-changed-paths --target-branch=master
# dagger call --progress=plain --source=".." fetch-tags
dagger call --progress=plain --source=".." list-tags
dagger call --progress=plain --source=".." get-short-commit-sha --length=6
# dagger call --progress=plain --source=".." get-tags-pointing-at-head