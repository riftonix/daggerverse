"""Dagger-native tests for the container-images scenario."""

from unittest import TestCase

from dagger import dag, function, object_type


@object_type
class Tests:
    """Test module entrypoint for container image scenario checks."""

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "container-images-tests"

    @function
    async def all(self) -> None:
        """Run all container image scenario tests."""
        await self.constructs_scenario()
        await self.has_local_docker_dependency()

    @function
    async def constructs_scenario(self) -> None:
        """Verify the scenario module is wired into the test module."""
        TestCase().assertEqual("container-images", await dag.container_images().module())

    @function
    async def has_local_docker_dependency(self) -> None:
        """Verify tests can call the local Docker module dependency."""
        TestCase().assertEqual("docker", await dag.docker().module())
