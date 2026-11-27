"""Contract checks for verify-app through the local go-ci dependency."""

from collections.abc import Awaitable
from unittest import TestCase

from dagger import Directory, ExecError, QueryError, dag, function, object_type

APP_PACKAGE = "./cmd/app"
# renovate: datasource=docker depName=library/golang versioning=regex:^(?<compatibility>1\.26)\.(?<patch>\d+)$
COMPATIBLE_GO_IMAGE_TAG = "1.26.11"


@object_type
class Tests:
    """Go CI scenario contract tests."""

    @function
    async def all(self) -> None:
        """Run all Go CI scenario tests."""
        await self.verify_embedded_app()
        await self.verify_runtime_overrides()
        await self.report_formatting_failure()
        await self.report_test_and_build_failures()

    @function
    async def verify_embedded_app(self) -> None:
        """Verify plain source with an embedded file and normalize the package path."""
        fixture = await dag.current_module().source().file("fixtures/user_test.go").contents()
        source = _app_fixture().with_new_file("cmd/app/user_test.go", fixture)
        output = await dag.go_ci(source=source).verify_app(package="cmd/./app")
        TestCase().assertIn(f"Verified {APP_PACKAGE} using", output)

    @function
    async def verify_runtime_overrides(self) -> None:
        """Forward the runtime image and a distinct numeric UID to the Go module."""
        fixture = await dag.current_module().source().file("fixtures/user_test.go").contents()
        fixture = fixture.replace("65532", "12345").replace(
            'expectedVersion = ""', f'expectedVersion = "go{COMPATIBLE_GO_IMAGE_TAG}"'
        )
        source = _app_fixture().with_new_file("cmd/app/user_test.go", fixture)
        scenario = dag.go_ci(
            source=source,
            go_image_tag=COMPATIBLE_GO_IMAGE_TAG,
            go_container_user_id="12345",
        )
        TestCase().assertIn(f":{COMPATIBLE_GO_IMAGE_TAG}", await scenario.verify_app(package=APP_PACKAGE))

    @function
    async def report_formatting_failure(self) -> None:
        """Return the module's formatting diagnostic to the scenario caller."""
        path = "internal/greeting/unformatted file.go"
        source = _app_fixture().with_new_file(path, "package greeting\nfunc  ignored() {}\n")
        await _assert_failure(dag.go_ci(source=source).verify_app(package=APP_PACKAGE), "formatting check failed", path)

    @function
    async def report_test_and_build_failures(self) -> None:
        """Keep diagnostics from a sibling package's test and from application linking."""
        source = _app_fixture()
        failing_test = source.with_new_file(
            "internal/greeting/greeting.go", 'package greeting\n\nconst Hello = "bye"\n'
        )
        await _assert_failure(
            dag.go_ci(source=failing_test).verify_app(package=APP_PACKAGE),
            "go test ./... failed",
            'unexpected greeting: "bye"',
        )

        missing_main = source.with_new_file("cmd/app/main.go", "package main\n")
        await _assert_failure(
            dag.go_ci(source=missing_main).verify_app(package=APP_PACKAGE), "go build failed", "main is undeclared"
        )


def _app_fixture() -> Directory:
    return dag.current_module().source().directory("fixtures/app")


async def _assert_failure(call: Awaitable[str], *expected: str) -> None:
    test = TestCase()
    with test.assertRaises(QueryError) as failure:
        await call
    error = failure.exception
    message = str(error)
    if isinstance(error, ExecError):
        message = f"{message}\n{error.stdout}\n{error.stderr}"
    for fragment in expected:
        test.assertIn(fragment, message)
