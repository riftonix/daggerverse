"""Contract checks for verify-app through the local go-ci dependency."""

from collections.abc import Awaitable
from unittest import TestCase

from dagger import Directory, ExecError, QueryError, dag, function, object_type

APP_PACKAGE = "./cmd/app"
# renovate: datasource=docker depName=library/golang versioning=regex:^(?<compatibility>1\.26)\.(?<patch>\d+)$
COMPATIBLE_GO_IMAGE_TAG = "1.26.11"
# renovate: datasource=docker depName=library/golang versioning=regex:^(?<compatibility>1\.25)\.(?<patch>\d+)$
OLDER_GO_IMAGE_TAG = "1.25.14"


@object_type
class Tests:
    """Go CI scenario contract tests."""

    @function
    async def all(self) -> None:
        """Run all Go CI scenario tests."""
        await self.verify_embedded_app()
        await self.reject_invalid_inputs()
        await self.verify_formatting()
        await self.report_test_and_build_failures()
        await self.verify_toolchain_override()
        await self.verify_container_user()

    @function
    async def verify_embedded_app(self) -> None:
        """Verify plain source with an embedded file and normalize the package path."""
        output = await dag.go_ci(source=_app_fixture()).verify_app(package="cmd/./app")
        TestCase().assertIn(f"Verified {APP_PACKAGE} using", output)

    @function
    async def reject_invalid_inputs(self) -> None:
        """Reject missing root manifests and non-application packages."""
        source = _app_fixture()
        nested = dag.directory().with_directory("nested", source)
        for missing_manifest in (nested, nested.with_new_directory("go.mod")):
            await _assert_failure(
                dag.go_ci(source=missing_manifest).verify_app(package="./nested/cmd/app"), "missing root go.mod"
            )
        scenario = dag.go_ci(source=source)
        for package in ("", "/cmd/app", "../app", "./cmd/...", "./cmd/missing", "./internal/greeting"):
            await _assert_failure(scenario.verify_app(package=package), "package", repr(package))

        escaped = source.with_symlink("/tmp", "escaped")
        await _assert_failure(
            dag.go_ci(source=escaped).verify_app(package="./escaped"), "package directory is outside the source tree"
        )
        nested = source.with_directory("nested", source)
        await _assert_failure(
            dag.go_ci(source=nested).verify_app(package="./nested/cmd/app"), "package", "./nested/cmd/app"
        )

    @function
    async def verify_formatting(self) -> None:
        """Skip Git and vendor trees and report unformatted files without changing them."""
        unformatted = "package ignored\nfunc  ignored() {}\n"
        source = (
            _app_fixture()
            .with_new_file(".git/unformatted.go", unformatted)
            .with_new_file("cmd/app/vendor/unformatted.go", unformatted)
        )
        await dag.go_ci(source=source).verify_app(package=APP_PACKAGE)

        path = "internal/greeting/unformatted file.go"
        unformatted = unformatted.replace("package ignored", "package greeting")
        source = source.with_new_file(path, unformatted)
        await _assert_failure(dag.go_ci(source=source).verify_app(package=APP_PACKAGE), "formatting", path)
        TestCase().assertEqual(unformatted, await source.file(path).contents())

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

    @function
    async def verify_toolchain_override(self) -> None:
        """Keep workspace mode off and enforce the module's minimum with the selected image."""
        source = _app_fixture().with_new_file("go.work", "go 1.26.0\n\nuse ./missing\n")
        compatible = dag.go_ci(source=source, go_image_tag=COMPATIBLE_GO_IMAGE_TAG)
        TestCase().assertIn(f":{COMPATIBLE_GO_IMAGE_TAG}", await compatible.verify_app(package=APP_PACKAGE))

        older = dag.go_ci(source=source, go_image_tag=OLDER_GO_IMAGE_TAG)
        await _assert_failure(
            older.verify_app(package=APP_PACKAGE), "go.mod requires go >= 1.26.0", "GOTOOLCHAIN=local"
        )

    @function
    async def verify_container_user(self) -> None:
        """Pass the default UID and a distinct numeric UID to the Go module."""
        fixture = await dag.current_module().source().file("fixtures/user_test.go").contents()
        source = _app_fixture()
        default = source.with_new_file("cmd/app/user_test.go", fixture)
        await dag.go_ci(source=default).verify_app(package=APP_PACKAGE)

        custom = source.with_new_file("cmd/app/user_test.go", fixture.replace("65532", "12345"))
        await dag.go_ci(source=custom, go_container_user_id="12345").verify_app(package=APP_PACKAGE)


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
