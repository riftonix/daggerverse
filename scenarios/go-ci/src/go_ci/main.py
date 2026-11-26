"""Dagger workflow for verifying one Go application."""

import json
import posixpath
from typing import Annotated, Self

import dagger
from dagger import Doc, dag, function, object_type

DEFAULT_GO_IMAGE_REGISTRY = "docker.io"
DEFAULT_GO_IMAGE_REPOSITORY = "library/golang"
# renovate: datasource=docker depName=library/golang
DEFAULT_GO_IMAGE_TAG = "1.27.4"

WORKDIR = "/workspace"
BINARY_PATH = "/tmp/go-ci-app"

LIST_PACKAGE = r"""
root=$(pwd -P)
package_dir=$(cd -P "$1" && pwd -P)
case "$package_dir" in
    "$root"|"$root"/*) exec go list -json=Name,Module "$1" ;;
    *) printf '%s\n' 'package directory is outside the source tree' >&2; exit 1 ;;
esac
"""
FORMAT_COMMAND = [
    "find", ".",
    "-type", "d", "(", "-name", ".git", "-o", "-name", "vendor", ")", "-prune", "-o",
    "-type", "f", "-name", "*.go", "-exec", "gofmt", "-l", "{}", "+",
]  # fmt: skip


@object_type
class GoCi:
    """Check formatting, run tests, and compile a Go application."""

    source: dagger.Directory
    go_image: str

    @classmethod
    def create(
        cls,
        source: Annotated[dagger.Directory, Doc("Source directory containing the root go.mod")],
        go_image_registry: Annotated[str, Doc("Go runtime image registry")] = DEFAULT_GO_IMAGE_REGISTRY,
        go_image_repository: Annotated[str, Doc("Go runtime image repository")] = DEFAULT_GO_IMAGE_REPOSITORY,
        go_image_tag: Annotated[str, Doc("Go runtime image tag")] = DEFAULT_GO_IMAGE_TAG,
    ) -> Self:
        """Select the source and Go runtime image."""
        return cls(source=source, go_image=f"{go_image_registry}/{go_image_repository}:{go_image_tag}")

    @function
    async def verify_app(
        self,
        package: Annotated[str, Doc("One main package directory relative to the module root")],
    ) -> str:
        """Check formatting, test the root module, and compile an application without exporting it."""
        package = _normalize_package(package)
        if not await self.source.exists("go.mod", expected_type=dagger.ExistsType.REGULAR_TYPE):
            raise ValueError("missing root go.mod in the source directory")

        runtime = self._runtime()
        await _check_package(runtime, package)

        unformatted = await _run(runtime, FORMAT_COMMAND, "formatting check")
        if unformatted:
            raise ValueError(f"formatting check failed; gofmt reported unformatted files:\n{unformatted}")

        await _run(runtime, ["go", "test", "-buildvcs=false", "./..."], "go test ./...")
        await _run(runtime, ["go", "build", "-buildvcs=false", "-o", BINARY_PATH, package], "go build")
        return f"Verified {package} using {self.go_image}: gofmt, go test ./..., go build passed."

    def _runtime(self) -> dagger.Container:
        module_cache = "/cache/go/mod"
        build_cache = "/cache/go/build"
        return (
            dag.container()
            .from_(self.go_image)
            .with_env_variable("GOTOOLCHAIN", "local")
            .with_env_variable("GOWORK", "off")
            .with_env_variable("GOMODCACHE", module_cache)
            .with_env_variable("GOCACHE", build_cache)
            .with_mounted_cache(module_cache, dag.cache_volume("go-ci-gomod"))
            .with_mounted_cache(build_cache, dag.cache_volume("go-ci-gobuild"))
            .with_mounted_directory(WORKDIR, self.source)
            .with_workdir(WORKDIR)
        )


def _normalize_package(package: str) -> str:
    normalized = posixpath.normpath(package)
    if (
        not package.strip()
        or package.startswith("/")
        or normalized == ".."
        or normalized.startswith("../")
        or "..." in package
        or "\0" in package
    ):
        raise ValueError(f"invalid package {package!r}; expected one directory relative to the module root")
    return "." if normalized == "." else f"./{normalized}"


async def _check_package(runtime: dagger.Container, package: str) -> None:
    step = f"package {package!r} validation"
    output = await _run(runtime, ["sh", "-ec", LIST_PACKAGE, "go-ci", package], step)
    metadata = json.loads(output)
    module = metadata.get("Module") or {}
    if metadata.get("Name") != "main" or not module.get("Main") or module.get("Dir") != WORKDIR:
        raise ValueError(f"{step} failed: expected a main package in the root Go module")


async def _run(runtime: dagger.Container, command: list[str], step: str) -> str:
    try:
        return await runtime.with_exec(command).stdout()
    except dagger.ExecError as error:
        diagnostic = "\n".join(output for output in (error.stdout.strip(), error.stderr.strip()) if output)
        raise RuntimeError(f"{step} failed:\n{diagnostic or error}") from None
