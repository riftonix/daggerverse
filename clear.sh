#! /bin/sh

DAGGER_ENGINE_DOCKER_CONTAINER="$(docker container list --all --filter 'name=^dagger-engine-*' --format '{{.Names}}')"
docker container stop "$DAGGER_ENGINE_DOCKER_CONTAINER"
docker container rm "$DAGGER_ENGINE_DOCKER_CONTAINER"
docker volume prune -f
docker system prune -f
