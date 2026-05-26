"""Dagger-native tests for the Docker module."""

from unittest import TestCase

from dagger import dag, function, object_type


@object_type
class Tests:
    """Test module entrypoint for Docker checks."""

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "docker-tests"

    @function
    async def all(self) -> None:
        """Run all Docker module tests."""
        await self.constructs_build_result()
        await self.constructs_image_result()

    @function
    async def constructs_build_result(self) -> None:
        """Verify Docker.build returns a result object with configured accessors."""
        build = dag.docker().build(
            source=dag.current_module().source().directory("fixtures/basic-image"),
            context_path=".",
            dockerfile_path="Dockerfile",
            target="runtime",
            build_args=["MESSAGE=hello=dagger"],
        )

        test_case = TestCase()
        test_case.assertEqual(".", await build.context_path())
        test_case.assertEqual("Dockerfile", await build.dockerfile_path())
        test_case.assertEqual("runtime", await build.target())
        test_case.assertEqual(["MESSAGE=hello=dagger"], await build.build_args())

    @function
    async def constructs_image_result(self) -> None:
        """Verify Docker.image returns an image result object."""
        image = dag.docker().image(image_ref="registry.example.local/app:latest")

        test_case = TestCase()
        test_case.assertEqual("registry.example.local/app:latest", await image.image_ref())
