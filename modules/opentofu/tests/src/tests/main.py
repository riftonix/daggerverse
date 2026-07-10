"""Dagger-native tests for the OpenTofu module."""

from unittest import TestCase

from dagger import dag, function, object_type


@object_type
class Tests:
    """Test module entrypoint for OpenTofu module checks."""

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "opentofu-tests"

    @function
    async def all(self) -> None:
        """Run all OpenTofu module tests."""
        await self.executor_input_is_separate_from_image()

    @function
    async def executor_input_is_separate_from_image(self) -> None:
        """The executor input selects the IaC command and does not change image identity."""
        bogus_executor = "not-a-real-iac-executor"
        test_case = TestCase()
        try:
            await dag.opentofu(
                executor=bogus_executor,
            ).lint(source=dag.directory())
        except BaseException as exc:
            message = getattr(exc, "stderr", None) or str(exc)
            test_case.assertIn(bogus_executor, message)
        else:
            test_case.fail("expected the bogus executor command to fail inside the runtime image")
