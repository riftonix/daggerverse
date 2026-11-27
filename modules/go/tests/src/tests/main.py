"""Contract checks through the local Go module dependency."""

from collections.abc import Awaitable
from unittest import TestCase

from dagger import Directory, ExecError, QueryError, dag, function, object_type

# renovate: datasource=docker depName=library/golang versioning=regex:^(?<compatibility>1\.26)\.(?<patch>\d+)$
COMPATIBLE_GO_IMAGE_TAG = "1.26.11"
# renovate: datasource=docker depName=library/golang versioning=regex:^(?<compatibility>1\.25)\.(?<patch>\d+)$
OLDER_GO_IMAGE_TAG = "1.25.14"


@object_type
class Tests:
    """Go module contract tests."""

    @function
    async def all(self) -> None:
        """Exercise all standalone Go operations."""
        await self.validate_package()
        await self.check_format()
        await self.test_and_build()
        await self.verify_runtime()
        await self.verify_toolchain_override()

    @function
    async def validate_package(self) -> None:
        """Accept one root main package and reject invalid selections and manifests."""
        source = _app_fixture()
        go = dag.go(source=source)
        TestCase().assertEqual(".", await go.validate_package(package="./"))
        for package in ("", "../app", "/tmp", "./...", "./missing", "./internal/greeting"):
            await _assert_failure(go.validate_package(package=package), "package", repr(package))

        escaped = source.with_symlink("/tmp", "escaped")
        await _assert_failure(
            dag.go(source=escaped).validate_package(package="./escaped"), "package directory is outside the source tree"
        )
        nested = dag.directory().with_directory("nested", source)
        await _assert_failure(dag.go(source=nested).validate_package(package="./nested"), "missing root go.mod")
        await _assert_failure(
            dag.go(source=nested.with_new_directory("go.mod")).validate_package(package="./nested"),
            "missing root go.mod",
        )
        await _assert_failure(
            dag.go(source=source.with_directory("nested", source)).validate_package(package="./nested"),
            "package",
            "./nested",
        )
        await _assert_failure(dag.go(source=nested).test(), "missing root go.mod")
        await _assert_failure(dag.go(source=nested).build(package="./nested"), "missing root go.mod")

    @function
    async def check_format(self) -> None:
        """Allow formatting to run without a manifest and report paths without changing them."""
        unformatted = "package example\nfunc  ignored() {}\n"
        source = (
            dag.directory()
            .with_new_file(".git/unformatted.go", unformatted)
            .with_new_file("nested/vendor/unformatted.go", unformatted)
            .with_new_file("formatted.go", "package example\n")
        )
        await dag.go(source=source).check_format()

        path = "unformatted file.go"
        source = source.with_new_file(path, unformatted)
        await _assert_failure(dag.go(source=source).check_format(), "formatting check failed", path)
        TestCase().assertEqual(unformatted, await source.file(path).contents())

    @function
    async def test_and_build(self) -> None:
        """Run root-module tests and build independently, preserving Go errors."""
        source = _app_fixture()
        go = dag.go(source=source)
        TestCase().assertIn("example.com/go-tool-test/internal/greeting", await go.test())
        await go.build(package=".")

        missing_embed = source.without_file("message.txt")
        await _assert_failure(dag.go(source=missing_embed).build(package="."), "message.txt")

        failing_test = source.with_new_file(
            "internal/greeting/greeting.go", 'package greeting\n\nconst Greeting = "bye"\n'
        )
        go_with_failing_test = dag.go(source=failing_test)
        await _assert_failure(go_with_failing_test.test(), "go test ./... failed", 'unexpected greeting: "bye"')
        await go_with_failing_test.build(package=".")

        missing_main = dag.go(source=source.with_new_file("main.go", "package main\n"))
        await missing_main.test()
        await _assert_failure(missing_main.build(package="."), "go build failed", "main is undeclared")
        await _assert_failure(go.build(package="./internal/greeting"), "expected a main package")

    @function
    async def verify_runtime(self) -> None:
        """Check the real UID and writable cache, home, and temporary paths."""
        fixture = await dag.current_module().source().file("fixtures/runtime_test.go").contents()
        source = _app_fixture()
        default = source.with_new_file("runtime_test.go", fixture)
        await dag.go(source=default).test()
        custom = source.with_new_file("runtime_test.go", fixture.replace("65532", "12345"))
        go = dag.go(source=custom, container_user_id="12345")
        await go.test()
        await go.build(package=".")

    @function
    async def verify_toolchain_override(self) -> None:
        """Ignore the workspace and enforce the minimum Go version of the root module."""
        source = _app_fixture().with_new_file("go.work", "go 1.26.0\n\nuse ./missing\n")
        compatible = dag.go(source=source, image_tag=COMPATIBLE_GO_IMAGE_TAG)
        await compatible.test()
        await compatible.build(package=".")

        older = dag.go(source=source, image_tag=OLDER_GO_IMAGE_TAG)
        await _assert_failure(older.validate_package(package="."), "go.mod requires go >= 1.26.0", "GOTOOLCHAIN=local")


def _app_fixture() -> Directory:
    return dag.current_module().source().directory("fixtures/app")


async def _assert_failure(call: Awaitable[object], *expected: str) -> None:
    test = TestCase()
    with test.assertRaises(QueryError) as failure:
        await call
    error = failure.exception
    message = str(error)
    if isinstance(error, ExecError):
        message = f"{message}\n{error.stdout}\n{error.stderr}"
    for fragment in expected:
        test.assertIn(fragment, message)
