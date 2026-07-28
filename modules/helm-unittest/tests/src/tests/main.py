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
        await self.filtered_suite()
        await self.multiple_suite_filters()
        await self.filtered_failing_suite()
        await self.filtered_suite_with_color()
        await self.default_suite_discovery()
        await self.custom_suite_discovery()
        await self.unmatched_suite_discovery()
        await self.empty_suite_discovery()

    @function
    async def successful_suite(self) -> None:
        """Assert omitted filters run only suites matching module defaults."""
        output = await dag.helm_unittest(source=self._passing_chart()).test()

        test_case = TestCase()
        test_case.assertIn("PASS", output)
        test_case.assertIn("tests/selected/deployment_test.yaml", output)
        test_case.assertIn("tests/additional/service_test.yml", output)
        test_case.assertNotIn("checks/excluded/failing_test.yaml", output)

    @function
    async def failing_suite(self) -> None:
        """Assert Helm unittest fails the Dagger call for a failing chart suite."""
        test_case = TestCase()
        with test_case.assertRaises(QueryError):
            await dag.helm_unittest(source=self._failing_chart()).test()

    @function
    async def filtered_suite(self) -> None:
        """Assert a selected suite runs while a valid suite outside the filter is ignored."""
        output = await dag.helm_unittest(source=self._passing_chart()).test(suite_files=["tests/selected/*_test.yaml"])

        test_case = TestCase()
        test_case.assertIn("PASS", output)
        test_case.assertIn("tests/selected/deployment_test.yaml", output)
        test_case.assertNotIn("checks/excluded/failing_test.yaml", output)

    @function
    async def multiple_suite_filters(self) -> None:
        """Assert multiple supplied suite filters are applied."""
        output = await dag.helm_unittest(source=self._passing_chart()).test(
            suite_files=["tests/selected/*_test.yaml", "tests/additional/*_test.yml"]
        )

        test_case = TestCase()
        test_case.assertIn("tests/selected/deployment_test.yaml", output)
        test_case.assertIn("tests/additional/service_test.yml", output)
        test_case.assertNotIn("checks/excluded/failing_test.yaml", output)

    @function
    async def filtered_failing_suite(self) -> None:
        """Assert a selected failing suite fails the Dagger call."""
        with TestCase().assertRaises(QueryError):
            await dag.helm_unittest(source=self._passing_chart()).test(suite_files=["checks/excluded/*_test.yaml"])

    @function
    async def filtered_suite_with_color(self) -> None:
        """Assert color output remains compatible with suite filters."""
        output = await dag.helm_unittest(source=self._passing_chart()).test(
            color=True,
            suite_files=["tests/selected/*_test.yaml"],
        )

        test_case = TestCase()
        test_case.assertIn("deployment_test.yaml", output)
        test_case.assertIn("\x1b[", output)

    @function
    async def default_suite_discovery(self) -> None:
        """Assert omitted filters discover suites matching module defaults."""
        found = await dag.helm_unittest(source=self._passing_chart()).has_suites()

        TestCase().assertTrue(found)

    @function
    async def custom_suite_discovery(self) -> None:
        """Assert custom filters replace defaults during discovery."""
        found = await dag.helm_unittest(source=self._passing_chart()).has_suites(
            suite_files=["checks/excluded/*_test.yaml"]
        )

        TestCase().assertTrue(found)

    @function
    async def unmatched_suite_discovery(self) -> None:
        """Assert unmatched custom filters report no selected suites."""
        found = await dag.helm_unittest(source=self._passing_chart()).has_suites(suite_files=["missing/*_test.yaml"])

        TestCase().assertFalse(found)

    @function
    async def empty_suite_discovery(self) -> None:
        """Assert an explicit empty filter list selects no suites."""
        found = await dag.helm_unittest(source=self._passing_chart()).has_suites(suite_files=[])

        TestCase().assertFalse(found)

    def _passing_chart(self) -> Directory:
        """Return the passing fixture chart directory."""
        return dag.current_module().source().directory(PASSING_CHART_PATH)

    def _failing_chart(self) -> Directory:
        """Return the failing fixture chart directory."""
        return dag.current_module().source().directory(FAILING_CHART_PATH)
