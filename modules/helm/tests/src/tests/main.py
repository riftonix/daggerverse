"""Dagger-native tests for the Helm module."""

from unittest import TestCase

import yaml
from dagger import Directory, dag, function, object_type

FIXTURE_CHART_PATH = "charts/ns-configurator"


@object_type
class Tests:
    """Test module entrypoint for Helm checks."""

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "helm-tests"

    @function
    async def all(self) -> None:
        """Run all Helm module tests."""
        await self.lint()
        await self.template()
        await self.package()

    @function
    async def lint(self) -> str:
        """Run Helm lint against the fixture chart."""
        return await dag.helm(source=self._fixture_chart()).with_dependency_update().lint(strict=True, errors_only=True)

    @function
    async def template(self) -> None:
        """Run Helm template against the fixture chart."""
        rendered_template = await dag.helm(source=self._fixture_chart()).with_dependency_update().template()
        manifests = [manifest for manifest in yaml.safe_load_all(rendered_template) if manifest]
        test_case = TestCase()
        test_case.assertEqual(1, len(manifests))

        limit_range = manifests[0]
        test_case.assertEqual("v1", limit_range["apiVersion"])
        test_case.assertEqual("LimitRange", limit_range["kind"])
        test_case.assertEqual("limit-range", limit_range["metadata"]["name"])
        test_case.assertEqual(
            [
                {
                    "type": "Container",
                    "default": {"cpu": "250m", "memory": "512Mi"},
                    "defaultRequest": {"cpu": "25m", "memory": "64Mi"},
                    "max": {"cpu": "16000m", "memory": "32Gi"},
                    "min": {"cpu": "5m", "memory": "16Mi"},
                },
                {
                    "type": "Pod",
                    "max": {"cpu": "16000m", "memory": "32Gi"},
                },
            ],
            limit_range["spec"]["limits"],
        )

    @function
    async def package(self) -> None:
        """Package the fixture chart and assert the output archive."""
        chart_archive = await dag.helm(source=self._fixture_chart()).with_dependency_update().package()
        test_case = TestCase()
        test_case.assertEqual("ns-configurator-1.0.0.tgz", await chart_archive.name())
        test_case.assertGreater(await chart_archive.size(), 0)

    def _fixture_chart(self) -> Directory:
        """Return the fixture chart directory."""
        return dag.current_module().source().directory(FIXTURE_CHART_PATH)
