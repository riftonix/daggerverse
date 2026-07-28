"""Dagger-native tests for the Helm CI scenario."""

from unittest import TestCase

from dagger import Directory, dag, function, object_type

FIXTURE_GIT_IMAGE_REGISTRY = "docker.io"
FIXTURE_GIT_IMAGE_REPOSITORY = "alpine/git"
# renovate: datasource=docker depName=alpine/git
FIXTURE_GIT_IMAGE_TAG = "v2.54.0"


@object_type
class Tests:
    """Test module entrypoint for Helm CI scenario checks."""

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "helm-ci-tests"

    @function
    async def all(self) -> None:
        """Run all Helm CI scenario tests."""
        await self.verify_chart()
        await self.verify_library_chart()
        await self.verify_chart_rejects_non_chart_directory()

    @function
    async def verify_chart(self) -> None:
        """Verify one application chart supplied as scenario source."""
        helm_ci = dag.helm_ci(source=self._fixture_chart())
        output = await helm_ci.verify_chart()

        TestCase().assertIn("lint:", output)
        TestCase().assertIn("template:", output)

    @function
    async def verify_library_chart(self) -> None:
        """Verify a library chart skips templating."""
        helm_ci = dag.helm_ci(source=self._fixture_library_chart())
        output = await helm_ci.verify_chart()

        TestCase().assertIn("template: skipped (library chart)", output)

    @function
    async def verify_chart_rejects_non_chart_directory(self) -> None:
        """Verify a directory without Chart.yaml is rejected."""
        helm_ci = dag.helm_ci(source=self._non_chart_directory())
        try:
            await helm_ci.verify_chart()
        except Exception as error:
            TestCase().assertIn("not a Helm chart", str(error))
        else:
            raise AssertionError("Expected non-chart directory validation to fail")

    def _non_chart_directory(self) -> Directory:
        """Return a directory without Chart.yaml."""
        return (
            dag.container()
            .from_(f"{FIXTURE_GIT_IMAGE_REGISTRY}/{FIXTURE_GIT_IMAGE_REPOSITORY}:{FIXTURE_GIT_IMAGE_TAG}")
            .with_new_file("/work/chart/README.md", "not a chart")
            .directory("/work/chart")
        )

    def _fixture_chart(self) -> Directory:
        """Return the fixture chart directory."""
        return dag.current_module().source().directory("charts/ns-configurator")

    def _fixture_library_chart(self) -> Directory:
        """Return a copy of the fixture chart with library type metadata."""
        return (
            dag.current_module()
            .source()
            .directory("charts/ns-configurator")
            .with_new_file(
                "Chart.yaml",
                "apiVersion: v2\nname: ns-configurator\nversion: 0.1.0\ntype: library\n",
            )
        )
