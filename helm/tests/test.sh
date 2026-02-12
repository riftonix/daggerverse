#! /bin/sh

SCRIPT_PATH=$(cd "$(dirname "$0")" && pwd)
MODULE_PATH=$(cd "${SCRIPT_PATH}/.." && pwd)
cd "$MODULE_PATH" || exit

dagger call --progress="plain" --source="./tests/charts/ns-configurator" \
  with-dependency-update \
  lint \
    --strict \
    --errors-only

dagger call --progress=plain --source=./tests/charts/ns-configurator \
  with-dependency-update \
  package \
    --version "0.0.1"

dagger call --progress=plain --source=./tests/charts/ns-configurator \
  with-registry-login \
    --address ghcr.io \
    --username rift0nix \
    --password env:GITHUB_TOKEN \
  with-dependency-update \
  push \
    --oci-url ghcr.io/riftonix/daggerverse/helm/tests/charts \
    --version "0.0.11"

dagger call --progress=plain --source=./tests/charts/ns-configurator get_chart_version

dagger call --progress=plain --source=./tests/charts/ns-configurator \
  with-registry-login \
    --address ghcr.io \
    --username rift0nix \
    --password env:GITHUB_TOKEN \
  is-already-published \
    --oci-chart-url ghcr.io/riftonix/daggerverse/helm/tests/charts/ns-configurator \
    --version "0.0.11"
