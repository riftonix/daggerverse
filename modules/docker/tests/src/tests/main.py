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
        await self.builds_image_from_bake()
        await self.builds_image_from_single_bake_target_without_explicit_target()
        await self.builds_image_from_bake_explicit_path()
        await self.builds_image_with_interpolation()
        await self.builds_image_with_variable_override()
        await self.exposes_bake_image_refs()
        await self.explicit_build_has_no_image_refs()
        await self.dry_run_publishes_bake_image_refs_with_registry_auth()
        await self.rejects_empty_registry_auth_address()
        await self.rejects_empty_registry_auth_username()
        await self.rejects_missing_bake_file()
        await self.rejects_missing_bake_target()
        await self.rejects_omitted_bake_target_for_multiple_targets()
        await self.rejects_missing_bake_tags()
        await self.rejects_unsupported_bake_target_field()
        await self.rejects_unsupported_bake_interpolation()

    @function
    async def builds_image_from_bake(self) -> None:
        """Verify Docker.build_from_bake builds the fixture image using Bake settings."""
        build = dag.docker().build_from_bake(
            source=dag.current_module().source().directory("fixtures/bake-image"),
            target="app",
        )

        output = await build.container().with_exec(["cat", "/message.txt"]).stdout()
        TestCase().assertEqual("bake-says-hello\n", output)
        TestCase().assertEqual("base", await build.target())

    @function
    async def builds_image_from_single_bake_target_without_explicit_target(self) -> None:
        """Verify Docker.build_from_bake selects the only Bake target when omitted."""
        build = dag.docker().build_from_bake(
            source=dag.current_module().source().directory("fixtures/bake-image"),
        )

        output = await build.container().with_exec(["cat", "/message.txt"]).stdout()
        TestCase().assertEqual("bake-says-hello\n", output)

    @function
    async def builds_image_from_bake_explicit_path(self) -> None:
        """Verify Docker.build_from_bake builds from an explicit Bake file path."""
        build = dag.docker().build_from_bake(
            source=dag.current_module().source().directory("fixtures/bake-image"),
            target="app",
            bake_path="custom-bake.json",
        )

        output = await build.container().with_exec(["cat", "/message.txt"]).stdout()
        TestCase().assertEqual("custom-bake-says-hello\n", output)

    @function
    async def builds_image_with_interpolation(self) -> None:
        """Verify Docker.build_from_bake handles variable interpolation."""
        build = dag.docker().build_from_bake(
            source=dag.current_module().source().directory("fixtures/bake-image"),
            target="app",
            bake_path="interpolation.json",
        )

        test_case = TestCase()
        # Verify interpolated build args
        build_args = await build.build_args()
        test_case.assertIn("VERSION=0.140.0", build_args)
        test_case.assertIn("BASE=alpine:latest", build_args)
        test_case.assertNotIn("REGISTRY=ghcr.io/riftonix", build_args)

        tags = await build.tags()
        test_case.assertEqual(["ghcr.io/riftonix/hugo:0.140.0"], tags)

        labels = await build.labels()
        test_case.assertIn("org.opencontainers.image.version=0.140.0", labels)
        container_labels = await build.container().labels()
        rendered_container_labels = [f"{await label.name()}={await label.value()}" for label in container_labels]
        test_case.assertIn("org.opencontainers.image.version=0.140.0", rendered_container_labels)

        test_case.assertEqual(["linux/amd64"], await build.platforms())
        output = await build.container().with_exec(["cat", "/version.txt"]).stdout()
        test_case.assertEqual("0.140.0\n", output)

    @function
    async def builds_image_with_variable_override(self) -> None:
        """Verify Docker.build_from_bake applies Bake variable overrides."""
        build = dag.docker().build_from_bake(
            source=dag.current_module().source().directory("fixtures/bake-image"),
            target="app",
            bake_path="interpolation.json",
            variable_overrides=["REGISTRY=registry.example.local/team"],
        )

        TestCase().assertEqual(["registry.example.local/team/hugo:0.140.0"], await build.tags())

    @function
    async def exposes_bake_image_refs(self) -> None:
        """Verify Bake builds expose resolved image references and tags."""
        build = dag.docker().build_from_bake(
            source=dag.current_module().source().directory("fixtures/bake-image"),
            target="app",
        )
        expected = ["registry.example.local/bake-image:latest"]

        test_case = TestCase()
        test_case.assertEqual(expected, await build.image_refs())
        test_case.assertEqual(expected, await build.tags())

    @function
    async def explicit_build_has_no_image_refs(self) -> None:
        """Verify explicit builds do not expose Bake image references."""
        build = dag.docker().build(
            source=dag.current_module().source(),
            context_path="fixtures/basic-image",
        )

        test_case = TestCase()
        test_case.assertEqual([], await build.image_refs())
        test_case.assertEqual([], await build.tags())

    @function
    async def dry_run_publishes_bake_image_refs_with_registry_auth(self) -> None:
        """Verify Bake builds dry-run publish their resolved image references with registry auth."""
        image = (
            dag.docker()
            .with_registry_auth(
                address="registry.example.local",
                username="ci-user",
                password=dag.set_secret("bake-registry-password", "super-secret"),
            )
            .build_from_bake(
                source=dag.current_module().source().directory("fixtures/bake-image"),
                target="app",
            )
            .with_publish_dry_run()
            .publish()
        )

        expected = ["registry.example.local/bake-image:latest"]
        test_case = TestCase()
        test_case.assertEqual(expected[0], await image.image_ref())
        test_case.assertEqual(expected, await image.image_refs())

    @function
    async def rejects_empty_registry_auth_address(self) -> None:
        """Verify registry auth requires a non-empty address."""
        await self._assert_registry_auth_error(
            address="",
            username="ci-user",
            expected="Registry address must not be empty",
        )

    @function
    async def rejects_empty_registry_auth_username(self) -> None:
        """Verify registry auth requires a non-empty username."""
        await self._assert_registry_auth_error(
            address="registry.example.local",
            username="",
            expected="Registry username must not be empty",
        )

    async def _assert_registry_auth_error(self, address: str, username: str, expected: str) -> None:
        test_case = TestCase()
        try:
            await (
                dag.docker()
                .with_registry_auth(
                    address=address,
                    username=username,
                    password=dag.set_secret("invalid-registry-password", "super-secret"),
                )
                .registry_auth_addresses()
            )
        except Exception as exc:
            test_case.assertIn(expected, str(exc))
        else:
            test_case.fail(f"expected registry auth validation failure containing {expected!r}")

    @function
    async def rejects_missing_bake_file(self) -> None:
        """Verify a missing Bake file fails clearly."""
        await self._assert_bake_error(
            target="app",
            bake_path="missing.json",
            expected="Bake file not found: missing.json",
        )

    @function
    async def rejects_missing_bake_target(self) -> None:
        """Verify a missing Bake target fails clearly."""
        await self._assert_bake_error(
            target="missing",
            bake_path="docker-bake.json",
            expected="Bake target 'missing' not found in docker-bake.json",
        )

    @function
    async def rejects_omitted_bake_target_for_multiple_targets(self) -> None:
        """Verify an omitted Bake target fails when the manifest is ambiguous."""
        await self._assert_bake_error(
            target=None,
            bake_path="validation-errors.json",
            expected="Bake file validation-errors.json must define exactly one target when target is omitted; found 3",
        )

    @function
    async def rejects_missing_bake_tags(self) -> None:
        """Verify a Bake target without tags fails clearly."""
        await self._assert_bake_error(
            target="missing-tags",
            bake_path="validation-errors.json",
            expected="Bake target 'missing-tags' must define at least one non-empty tag",
        )

    @function
    async def rejects_unsupported_bake_target_field(self) -> None:
        """Verify unsupported Bake target fields fail clearly."""
        await self._assert_bake_error(
            target="unsupported-field",
            bake_path="validation-errors.json",
            expected="Unsupported fields in Bake target 'unsupported-field': cache-from",
        )

    @function
    async def rejects_unsupported_bake_interpolation(self) -> None:
        """Verify unsupported Bake interpolation fails clearly."""
        await self._assert_bake_error(
            target="unsupported-interpolation",
            bake_path="validation-errors.json",
            expected="Unsupported Bake interpolation in tags",
        )

    async def _assert_bake_error(self, target: str | None, bake_path: str, expected: str) -> None:
        test_case = TestCase()
        try:
            await (
                dag.docker()
                .build_from_bake(
                    source=dag.current_module().source().directory("fixtures/bake-image"),
                    target=target,
                    bake_path=bake_path,
                )
                .tags()
            )
        except Exception as exc:
            test_case.assertIn(expected, str(exc))
        else:
            test_case.fail(f"expected Bake validation failure containing {expected!r}")

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
            .publish(image_refs=image_refs)
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
