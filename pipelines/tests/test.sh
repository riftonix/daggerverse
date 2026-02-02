#! /bin/sh

SCRIPT_PATH=$(cd "$(dirname "$0")" && pwd)
MODULE_PATH=$(cd "${SCRIPT_PATH}/.." && pwd)
cd "$MODULE_PATH" || exit

dagger call helm-verify --progress="plain" --source="./tests/charts/ns-configurator"
dagger call helm-verify-changed --progress="plain" --source=".." --diff-dir="pipelines/tests/charts"
