#! /bin/sh

SCRIPT_PATH=$(cd "$(dirname "$0")" && pwd)
MODULE_PATH=$(cd "${SCRIPT_PATH}/.." && pwd)
cd "$MODULE_PATH" || exit

dagger call --progress=plain --source="./tests/site" --output ./tests/site/public build --hugo_theme_url="github.com/google/docsy@v0.13.0" --site_base_url="example.com"
dagger call --progress=plain --source="./tests/site" container with-exec --args=hugo,config,--format,yaml stdout

# As service
# dagger call --progress=plain --source="./tests/site" container with-default-args --args=hugo,serve,--bind,0.0.0.0,--port,1313 with-exposed-port --port=1313 as-service up --ports=1313:1313
