#! /bin/sh

SCRIPT_PATH=$(cd "$(dirname "$0")" && pwd)
MODULE_PATH=$(cd "${SCRIPT_PATH}/.." && pwd)
cd "$MODULE_PATH" || exit

dagger call --progress=plain  package --source ./tests/charts/ns-configurator
dagger call --progress=plain \
  push \
    --source ./tests/charts/ns-configurator \
    --registry ghcr.io \
    --repository riftonix/helm/test \
    --username rift0nix \
    --password env:GITHUB_TOKEN \
    --version "2.4.0"
