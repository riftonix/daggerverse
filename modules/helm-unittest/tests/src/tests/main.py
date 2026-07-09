"""Dagger-native tests for the Helm unittest module."""

from unittest import TestCase

from dagger import Directory, QueryError, dag, function, object_type

PASSING_CHART_PATH = "charts/passing-chart"
FAILING_CHART_PATH = "charts/failing-chart"


@object_type
class Tests:
    """Test module entrypoint for Helm unittest checks."""

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "helm-unittest-tests"

    @function
    async def all(self) -> None:
        """Run all Helm unittest module tests."""
        await self.failing_suite()
        await self.successful_suite()

    @function
    async def successful_suite(self) -> None:
        """Assert Helm unittest succeeds for a passing chart suite."""
        output = await dag.helm_unittest(source=self._passing_chart()).test()

        test_case = TestCase()
        test_case.assertIn("PASS", output)
        test_case.assertIn("tests/deployment_test.yaml", output)

    @function
    async def failing_suite(self) -> None:
        """Assert Helm unittest fails the Dagger call for a failing chart suite."""
        test_case = TestCase()
        with test_case.assertRaises(QueryError):
            await dag.helm_unittest(source=self._failing_chart()).test()

    def _passing_chart(self) -> Directory:
        """Return the passing fixture chart directory."""
        return dag.current_module().source().directory(PASSING_CHART_PATH)

    def _failing_chart(self) -> Directory:
        """Return the failing fixture chart directory."""
        return dag.current_module().source().directory(FAILING_CHART_PATH)
