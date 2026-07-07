"""Dagger-native tests for the OpenTofu module."""

from unittest import TestCase

from dagger import dag, function, object_type

DEFAULT_IMAGE_REGISTRY = "ghcr.io"
DEFAULT_IMAGE_REPOSITORY = "opentofu/opentofu"
DEFAULT_IMAGE_TAG = "latest"
DEFAULT_USER_ID = "65532"


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
                image_registry=DEFAULT_IMAGE_REGISTRY,
                image_repository=DEFAULT_IMAGE_REPOSITORY,
                image_tag=DEFAULT_IMAGE_TAG,
                user_id=DEFAULT_USER_ID,
                executor=bogus_executor,
            ).lint(source=dag.directory())
        except BaseException as exc:
            message = getattr(exc, "stderr", None) or str(exc)
            test_case.assertIn(bogus_executor, message)
        else:
            test_case.fail("expected the bogus executor command to fail inside the runtime image")
