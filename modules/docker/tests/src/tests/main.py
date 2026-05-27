"""Dagger-native tests for the Docker module."""

from unittest import TestCase

from dagger import Platform, dag, function, object_type


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
        await self.builds_image_from_context()
        await self.builds_image_with_options()
        await self.builds_image_for_explicit_platforms()
        await self.runs_smoke_check()
        await self.fails_smoke_check()
        await self.rejects_invalid_build_arg()
        await self.configures_registry_auth_without_exposing_secret()
        await self.dry_run_publishes_image_refs()
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
    async def builds_image_for_explicit_platforms(self) -> None:
        """Verify Docker.build records explicit platform variants."""
        build = dag.docker().build(
            source=dag.current_module().source(),
            context_path="fixtures/basic-image",
            platforms=[Platform("linux/amd64")],
        )

        test_case = TestCase()
        test_case.assertEqual(["linux/amd64"], await build.platforms())
        test_case.assertEqual(1, len(await build.platform_variants()))

    @function
    async def builds_image_from_context(self) -> None:
        """Verify Docker.build builds the fixture image."""
        build = dag.docker().build(
            source=dag.current_module().source(),
            context_path="fixtures/basic-image",
        )

        output = await build.container().with_exec(["cat", "/message.txt"]).stdout()
        TestCase().assertEqual("hello\n", output)

    @function
    async def builds_image_with_options(self) -> None:
        """Verify Docker.build applies Dockerfile, target, and build args."""
        build = dag.docker().build(
            source=dag.current_module().source(),
            context_path="fixtures/basic-image",
            dockerfile_path="Dockerfile",
            target="runtime",
            build_args=["MESSAGE=hello=dagger"],
        )

        output = await build.container().with_exec(["cat", "/message.txt"]).stdout()
        TestCase().assertEqual("hello=dagger\n", output)

    @function
    async def runs_smoke_check(self) -> None:
        """Verify DockerBuild.with_smoke_check succeeds for a passing command."""
        build = (
            dag.docker()
            .build(
                source=dag.current_module().source(),
                context_path="fixtures/basic-image",
            )
            .with_smoke_check(["cat", "/message.txt"])
        )

        TestCase().assertEqual("fixtures/basic-image", await build.context_path())

    @function
    async def fails_smoke_check(self) -> None:
        """Verify DockerBuild.with_smoke_check fails for a failing command."""
        test_case = TestCase()
        try:
            await (
                dag.docker()
                .build(
                    source=dag.current_module().source(),
                    context_path="fixtures/basic-image",
                )
                .with_smoke_check(["sh", "-c", "exit 42"])
                .context_path()
            )
        except Exception as exc:
            test_case.assertIn("exit code: 42", str(exc))
        else:
            test_case.fail("expected failing smoke command to fail")

    @function
    async def rejects_invalid_build_arg(self) -> None:
        """Verify malformed build args fail clearly."""
        test_case = TestCase()
        try:
            await (
                dag.docker()
                .build(
                    source=dag.current_module().source(),
                    context_path="fixtures/basic-image",
                    build_args=["MESSAGE"],
                )
                .context_path()
            )
        except Exception as exc:
            test_case.assertIn("Invalid build argument", str(exc))
            test_case.assertIn("KEY=VALUE", str(exc))
        else:
            test_case.fail("expected invalid build argument to fail")

    @function
    async def configures_registry_auth_without_exposing_secret(self) -> None:
        """Verify Docker.with_registry_auth records auth without exposing the secret."""
        docker = dag.docker().with_registry_auth(
            address="registry.example.local",
            username="ci-user",
            password=dag.set_secret("registry-password", "super-secret"),
        )

        test_case = TestCase()
        test_case.assertEqual(["registry.example.local"], await docker.registry_auth_addresses())

    @function
    async def dry_run_publishes_image_refs(self) -> None:
        """Verify DockerBuild.publish wiring without requiring a registry."""
        image_refs = [
            "registry.example.local/docker-test:latest",
            "registry.example.local/docker-test:stable",
        ]
        image = (
            dag.docker()
            .build(
                source=dag.current_module().source(),
                context_path="fixtures/basic-image",
            )
            .with_publish_dry_run()
            .publish(image_refs)
        )

        test_case = TestCase()
        test_case.assertEqual(image_refs[0], await image.image_ref())
        test_case.assertEqual(image_refs, await image.image_refs())

    @function
    async def constructs_image_result(self) -> None:
        """Verify Docker.image returns an image result object."""
        image = dag.docker().image(image_ref="registry.example.local/app:latest")

        test_case = TestCase()
        test_case.assertEqual("registry.example.local/app:latest", await image.image_ref())
