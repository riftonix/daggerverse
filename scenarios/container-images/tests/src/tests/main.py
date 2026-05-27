"""Dagger-native tests for the container-images scenario."""

from unittest import TestCase

from dagger import Platform, dag, function, object_type

FORBIDDEN_POLICY_MARKERS = [
    "github",
    "gitlab",
    "github_",
    "gitlab_",
    "ci_",
    "refs/tags",
    "docker/",
    "changed",
]


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
        await self.verifies_image_build_only()
        await self.verifies_image_with_build_options()
        await self.verifies_image_with_smoke_command()
        await self.verifies_multiple_images()
        await self.propagates_multi_image_verification_failure()
        await self.dry_run_publishes_image()
        await self.dry_run_publishes_image_with_options_and_registry_auth()
        await self.dry_run_publishes_multiple_images()
        await self.propagates_multi_image_publication_failure()
        await self.keeps_provider_policy_out_of_scenario_code()

    @function
    async def constructs_scenario(self) -> None:
        """Verify the scenario module is wired into the test module."""
        TestCase().assertEqual("container-images", await dag.container_images().module())

    @function
    async def has_local_docker_dependency(self) -> None:
        """Verify tests can call the local Docker module dependency."""
        TestCase().assertEqual("docker", await dag.docker().module())

    @function
    async def verifies_image_build_only(self) -> None:
        """Verify the scenario builds one explicit image context."""
        result = await dag.container_images().verify_image(
            source=dag.current_module().source(),
            context_path="fixtures/basic-image",
        )

        TestCase().assertEqual("verified fixtures/basic-image", result)

    @function
    async def verifies_image_with_build_options(self) -> None:
        """Verify the scenario forwards build options to the Docker module."""
        result = await dag.container_images().verify_image(
            source=dag.current_module().source(),
            context_path="fixtures/basic-image",
            dockerfile_path="Dockerfile",
            target="runtime",
            build_args=["MESSAGE=hello=scenario"],
            platforms=[Platform("linux/amd64")],
            smoke_command=["grep", "hello=scenario", "/message.txt"],
        )

        TestCase().assertEqual("verified fixtures/basic-image", result)

    @function
    async def verifies_image_with_smoke_command(self) -> None:
        """Verify the scenario runs an optional smoke command."""
        result = await dag.container_images().verify_image(
            source=dag.current_module().source(),
            context_path="fixtures/alt-image",
            smoke_command=["grep", "alt", "/message.txt"],
        )

        TestCase().assertEqual("verified fixtures/alt-image", result)

    @function
    async def verifies_multiple_images(self) -> None:
        """Verify the scenario builds multiple explicit image contexts."""
        results = await dag.container_images().verify_images(
            source=dag.current_module().source(),
            context_paths=[
                "fixtures/basic-image",
                "fixtures/alt-image",
            ],
        )

        TestCase().assertEqual(
            [
                "verified fixtures/basic-image",
                "verified fixtures/alt-image",
            ],
            results,
        )

    @function
    async def propagates_multi_image_verification_failure(self) -> None:
        """Verify multi-image verification fails when any context fails."""
        test_case = TestCase()
        try:
            await dag.container_images().verify_images(
                source=dag.current_module().source(),
                context_paths=[
                    "fixtures/basic-image",
                    "fixtures/missing-image",
                ],
            )
        except Exception as exc:
            test_case.assertIn("missing-image", str(exc))
        else:
            test_case.fail("expected missing image context to fail")

    @function
    async def dry_run_publishes_image(self) -> None:
        """Verify single-image publication wiring without a registry."""
        image_ref = "registry.example.local/container-images/basic:latest"
        result = await dag.container_images().publish_image(
            source=dag.current_module().source(),
            context_path="fixtures/basic-image",
            image_ref=image_ref,
            publish_dry_run=True,
        )

        TestCase().assertEqual(image_ref, result)

    @function
    async def dry_run_publishes_image_with_options_and_registry_auth(self) -> None:
        """Verify publication forwards build options and registry auth."""
        image_ref = "registry.example.local/container-images/basic:runtime"
        result = await dag.container_images().publish_image(
            source=dag.current_module().source(),
            context_path="fixtures/basic-image",
            image_ref=image_ref,
            dockerfile_path="Dockerfile",
            target="runtime",
            build_args=["MESSAGE=published=scenario"],
            platforms=[Platform("linux/amd64")],
            registry_address="registry.example.local",
            registry_username="ci-user",
            registry_password=dag.set_secret("container-images-registry-password", "super-secret"),
            publish_dry_run=True,
        )

        TestCase().assertEqual(image_ref, result)

    @function
    async def dry_run_publishes_multiple_images(self) -> None:
        """Verify multi-image publication wiring without a registry."""
        image_refs = [
            "registry.example.local/container-images/basic:latest",
            "registry.example.local/container-images/alt:latest",
        ]
        results = await dag.container_images().publish_images(
            source=dag.current_module().source(),
            publish_specs=[
                f"fixtures/basic-image={image_refs[0]}",
                f"fixtures/alt-image={image_refs[1]}",
            ],
            publish_dry_run=True,
        )

        TestCase().assertEqual(image_refs, results)

    @function
    async def propagates_multi_image_publication_failure(self) -> None:
        """Verify multi-image publication fails when any spec fails."""
        test_case = TestCase()
        try:
            await dag.container_images().publish_images(
                source=dag.current_module().source(),
                publish_specs=[
                    "fixtures/basic-image=registry.example.local/container-images/basic:latest",
                    "fixtures/missing-image=registry.example.local/container-images/missing:latest",
                ],
                publish_dry_run=True,
            )
        except Exception as exc:
            test_case.assertIn("missing-image", str(exc))
        else:
            test_case.fail("expected missing image context publication to fail")

    @function
    async def keeps_provider_policy_out_of_scenario_code(self) -> None:
        """Verify CI provider and path policy stay outside this scenario."""
        source = dag.current_module().source()
        files = {
            "tests": self._without_forbidden_policy_marker_declaration(
                await source.file("src/tests/main.py").contents()
            ),
        }

        test_case = TestCase()
        for name, contents in files.items():
            normalized = contents.lower()
            for marker in FORBIDDEN_POLICY_MARKERS:
                test_case.assertNotIn(marker, normalized, f"{marker!r} leaked into {name}")

    def _without_forbidden_policy_marker_declaration(self, contents: str) -> str:
        start_marker = "FORBIDDEN_POLICY_MARKERS = ["
        start = contents.index(start_marker)
        end = contents.index("]\n", start) + len("]\n")
        return contents[:start] + contents[end:]
