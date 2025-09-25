#! /bin/sh

SCRIPT_PATH=$(cd "$(dirname "$0")" && pwd)
MODULE_PATH=$(cd "${SCRIPT_PATH}/.." && pwd)
cd "$MODULE_PATH" || exit

dagger call --progress=plain  \
  package \
   --source ./tests/charts/ns-configurator \
   --version "0.0.1"

dagger call --progress=plain \
  with-registry-login \
    --address ghcr.io \
    --username rift0nix \
    --password env:GITHUB_TOKEN \
  push \
    --oci-url ghcr.io/riftonix/daggerverse/helm/tests/charts \
    --source ./tests/charts/ns-configurator \
    --version "0.0.11" \
    --dependency-update
