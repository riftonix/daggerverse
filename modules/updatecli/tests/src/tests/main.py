"""Dagger-native Updatecli tests with local manifests and no service credentials."""

from collections.abc import Awaitable
from typing import Annotated, Self
from unittest import TestCase

import dagger
from dagger import Doc, ExecError, QueryError, dag, function, object_type

DEFAULT_IMAGE_REGISTRY = "ghcr.io"
DEFAULT_IMAGE_REPOSITORY = "updatecli/updatecli"
# renovate: datasource=docker depName=ghcr.io/updatecli/updatecli
DEFAULT_IMAGE_TAG = "v0.123.0"
DEFAULT_CONTAINER_USER_ID = "65532"


@object_type
class Tests:
    """Exercise the parent module API with optional mirrored image inputs."""

    image_registry: str
    image_repository: str
    image_tag: str
    container_user_id: str

    @classmethod
    async def create(
        cls,
        image_registry: Annotated[str | None, Doc("Updatecli image registry")] = DEFAULT_IMAGE_REGISTRY,
        image_repository: Annotated[str | None, Doc("Updatecli image repository")] = DEFAULT_IMAGE_REPOSITORY,
        image_tag: Annotated[str | None, Doc("Updatecli image tag")] = DEFAULT_IMAGE_TAG,
        container_user_id: Annotated[str | None, Doc("Runtime user")] = DEFAULT_CONTAINER_USER_ID,
    ) -> Self:
        """Use parent image defaults unless a caller provides a mirror."""
        return cls(
            image_registry=image_registry or DEFAULT_IMAGE_REGISTRY,
            image_repository=image_repository or DEFAULT_IMAGE_REPOSITORY,
            image_tag=image_tag or DEFAULT_IMAGE_TAG,
            container_user_id=container_user_id or DEFAULT_CONTAINER_USER_ID,
        )

    @function
    def module(self) -> str:
        """Return the test module identifier."""
        return "updatecli-tests"

    @function
    async def all(self) -> None:
        """Run local-manifest tests without external services or credentials."""
        await self.runtime()
        await self.preview()
        await self.execution_modes()
        await self.apply_report()
        await self.applied_working_tree()
        await self.empty_working_tree()
        await self.render()
        await self.multiple_values()
        await self.json_values()
        await self.render_does_not_run_sources()
        await self.invalid_manifest_fails()
        await self.failing_pipeline()
        await self.skipped_pipeline()
        await self.runtime_additions_and_secret()

    @function
    async def runtime(self) -> None:
        """Check the configured image and its writable working tree and home."""
        container = self._module().container()
        test = TestCase()
        test.assertEqual("/work", await container.workdir())
        test.assertEqual(self.container_user_id, await container.user())
        output = await container.with_exec(
            ["sh", "-c", 'test -w /work && test -w "$HOME" && updatecli version']
        ).stdout()
        test.assertIn("Application:", output)

    @function
    async def preview(self) -> None:
        """Report the pending version without changing the input snapshot."""
        source = self._fixture_source()
        output = await self._module(source).diff(config=self._manifest("local.yaml"))
        test = TestCase()
        test.assertIn("2.0.0", output)
        test.assertIn("version.txt", output)
        test.assertEqual("1.0.0\n", await source.file("version.txt").contents())

    @function
    async def execution_modes(self) -> None:
        """Distinguish diff from apply through the shell target DRY_RUN contract."""
        module = self._module().with_directory(
            path="/opt/updatecli-test", directory=self._fixtures().directory("helpers")
        )
        config = self._manifest("mode.yaml")
        preview = await module.diff(config=config)
        applied = await module.apply(config=config)
        test = TestCase()
        test.assertIn("preview-only-marker", preview)
        test.assertNotIn("apply-only-marker", preview)
        test.assertIn("apply-only-marker", applied)
        test.assertNotIn("preview-only-marker", applied)

    @function
    async def apply_report(self) -> None:
        """Return the successful Updatecli apply report, including stderr logs."""
        output = await self._module(self._fixture_source()).apply(config=self._manifest("local.yaml"))
        test = TestCase()
        test.assertIn("2.0.0", output)
        test.assertIn("version.txt", output)

    @function
    async def applied_working_tree(self) -> None:
        """Return changed files while preserving the original caller directory."""
        source = self._fixture_source()
        updated = await self._module(source).applied_source(config=self._manifest("local.yaml"))
        test = TestCase()
        test.assertEqual("2.0.0", (await updated.file("version.txt").contents()).strip())
        test.assertEqual("1.0.0\n", await source.file("version.txt").contents())
        test.assertNotIn("manifest.yaml", await updated.entries())

    @function
    async def empty_working_tree(self) -> None:
        """Run without source and return a newly created local target file."""
        updated = await self._module().applied_source(config=self._manifest("local.yaml"))
        TestCase().assertEqual("2.0.0", (await updated.file("version.txt").contents()).strip())

    @function
    async def render(self) -> None:
        """Resolve Go template values through Updatecli without running pipelines."""
        output = await self._module().manifest_show(
            config=self._manifest("template.yaml"),
            values=[self._fixtures().file("defaults/values.yaml")],
        )
        test = TestCase()
        test.assertIn("Templated version 3.0.0", output)
        test.assertNotIn("{{ .version }}", output)

    @function
    async def multiple_values(self) -> None:
        """Keep equal values-file basenames distinct and preserve merge order."""
        updated = await self._module().applied_source(
            config=self._manifest("template.yaml"),
            values=[
                self._fixtures().file("defaults/values.yaml"),
                self._fixtures().file("overrides/values.yaml"),
            ],
        )
        TestCase().assertEqual("4.0.0", (await updated.file("version.txt").contents()).strip())

    @function
    async def json_values(self) -> None:
        """Accept JSON values through Updatecli's YAML-compatible values reader."""
        values = dag.directory().with_new_file("values.json", '{"version":"5.0.0"}').file("values.json")
        updated = await self._module().applied_source(config=self._manifest("template.yaml"), values=[values])
        TestCase().assertEqual("5.0.0", (await updated.file("version.txt").contents()).strip())

    @function
    async def render_does_not_run_sources(self) -> None:
        """Render a manifest whose pipeline would fail if it were executed."""
        output = await self._module().manifest_show(config=self._manifest("failing.yaml"))
        TestCase().assertIn("Deliberately failing target", output)

    @function
    async def invalid_manifest_fails(self) -> None:
        """Propagate invalid YAML failures from preview, apply, and rendering."""
        test = TestCase()
        module = self._module()
        config = self._manifest("invalid.yaml")
        with test.assertRaises(QueryError):
            await module.diff(config=config)
        with test.assertRaises(QueryError):
            await module.apply(config=config)
        with test.assertRaises(QueryError):
            await module.manifest_show(config=config)

    @function
    async def failing_pipeline(self) -> None:
        """Fail preview, apply, and artifact export with output when the target fails."""
        module = self._module()
        config = self._manifest("failing.yaml")
        await self._assert_fails_with(module.diff(config=config), "fixture-target-failure")
        await self._assert_fails_with(module.apply(config=config), "fixture-target-failure")
        await self._assert_fails_with(module.applied_source(config=config).sync(), "fixture-target-failure")

    @function
    async def skipped_pipeline(self) -> None:
        """Return the report when Updatecli skips a pipeline after a source failure."""
        test = TestCase()
        source = self._fixture_source()
        module = self._module(source)
        config = self._manifest("skipped.yaml")
        test.assertIn("fixture-source-failure", await module.diff(config=config))
        test.assertIn("fixture-source-failure", await module.apply(config=config))
        updated = await module.applied_source(config=config)
        test.assertEqual("1.0.0\n", await updated.file("version.txt").contents())

    @function
    async def runtime_additions_and_secret(self) -> None:
        """Expose helper files and environment while scrubbing a fixture secret."""
        secret_value = "updatecli-fixture-token-not-a-real-credential"
        output = (
            await self._module()
            .with_directory(path="/opt/updatecli-test", directory=self._fixtures().directory("helpers"))
            .with_env_variable(name="UPDATECLI_TEST_PLAIN", value="plain-value-marker")
            .with_secret_variable(
                name="UPDATECLI_TEST_SECRET", secret=dag.set_secret("updatecli-fixture", secret_value)
            )
            .apply(config=self._manifest("helpers.yaml"))
        )
        test = TestCase()
        test.assertIn("plain-value-marker", output)
        test.assertIn("helper-target-changed", output)
        test.assertNotIn(secret_value, output)
        test.assertIn("***", output)

    async def _assert_fails_with(self, call: Awaitable[object], expected: str) -> None:
        test = TestCase()
        try:
            await call
        except QueryError as error:
            output = f"{error.stdout}{error.stderr}" if isinstance(error, ExecError) else str(error)
            test.assertIn(expected, output)
        else:
            test.fail(f"expected the Updatecli call to fail with {expected!r}")

    def _module(self, source: dagger.Directory | None = None) -> dagger.Updatecli:
        module = dag.updatecli(
            source=source,
            image_registry=self.image_registry,
            image_repository=self.image_repository,
            image_tag=self.image_tag,
            container_user_id=self.container_user_id,
        )
        # Keep fixture runs independent of any inherited OpenTelemetry collector.
        for name in ("OTEL_TRACES_EXPORTER", "OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"):
            module = module.with_env_variable(name=name, value="")
        return module

    def _fixtures(self) -> dagger.Directory:
        return dag.current_module().source().directory("fixtures")

    def _fixture_source(self) -> dagger.Directory:
        return self._fixtures().directory("source")

    def _manifest(self, name: str) -> dagger.File:
        return self._fixtures().file(f"manifests/{name}")
