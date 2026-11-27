"""Run Go checks in a configurable container."""

import json
import posixpath
from typing import Annotated, Self

import dagger
from dagger import Doc, dag, function, object_type

DEFAULT_IMAGE_REGISTRY = "docker.io"
DEFAULT_IMAGE_REPOSITORY = "library/golang"
# renovate: datasource=docker depName=library/golang
DEFAULT_IMAGE_TAG = "1.27.4"
DEFAULT_CONTAINER_USER_ID = "65532"

WORKDIR = "/workspace"
RUNTIME_DIR = "/tmp/dagger-go"
TMPDIR = f"{RUNTIME_DIR}/tmp"
MODULE_CACHE = "/cache/go/mod"
BUILD_CACHE = "/cache/go/build"

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
class Go:
    """Verify source in a root Go module."""

    source: dagger.Directory
    image: str
    container_user_id: str

    @classmethod
    def create(
        cls,
        source: Annotated[dagger.Directory, Doc("Go source directory")],
        image_registry: Annotated[str, Doc("Go runtime image registry")] = DEFAULT_IMAGE_REGISTRY,
        image_repository: Annotated[str, Doc("Go runtime image repository")] = DEFAULT_IMAGE_REPOSITORY,
        image_tag: Annotated[str, Doc("Go runtime image tag")] = DEFAULT_IMAGE_TAG,
        container_user_id: Annotated[str, Doc("Numeric UID for Go commands")] = DEFAULT_CONTAINER_USER_ID,
    ) -> Self:
        """Select the source, image, and Go execution user."""
        if not container_user_id.isascii() or not container_user_id.isdecimal():
            raise ValueError("container_user_id must be a numeric UID")
        return cls(
            source=source,
            image=f"{image_registry}/{image_repository}:{image_tag}",
            container_user_id=str(int(container_user_id)),
        )

    @function
    async def validate_package(
        self,
        package: Annotated[str, Doc("One main package directory relative to the module root")],
    ) -> str:
        """Validate a local executable package and return its normalized path."""
        package = _normalize_package(package)
        await self._require_module()
        await _check_package(self._runtime(), package)
        return package

    @function
    async def check_format(self) -> None:
        """Report Go files that need formatting without rewriting them."""
        unformatted = await _run(self._runtime(), FORMAT_COMMAND, "formatting check")
        if unformatted:
            raise ValueError(f"formatting check failed; gofmt reported unformatted files:\n{unformatted}")

    @function
    async def test(self) -> str:
        """Run all tests in the root Go module and return their output."""
        await self._require_module()
        return await _run(self._runtime(), ["go", "test", "-buildvcs=false", "./..."], "go test ./...")

    @function
    async def build(
        self,
        package: Annotated[str, Doc("One main package directory relative to the module root")],
    ) -> None:
        """Compile a local executable without exporting it."""
        package = await self.validate_package(package)
        await _run(self._runtime(), ["go", "build", "-buildvcs=false", "-o", f"{TMPDIR}/app", package], "go build")

    async def _require_module(self) -> None:
        if not await self.source.exists("go.mod", expected_type=dagger.ExistsType.REGULAR_TYPE):
            raise ValueError("missing root go.mod in the source directory")

    def _runtime(self) -> dagger.Container:
        uid = self.container_user_id
        runtime_dirs = dag.directory().with_new_directory("home", permissions=0o700)
        runtime_dirs = runtime_dirs.with_new_directory("tmp", permissions=0o700)
        return (
            dag.container()
            .from_(self.image)
            .with_directory(RUNTIME_DIR, runtime_dirs, owner=uid)
            .with_user(uid)
            .with_env_variable("HOME", f"{RUNTIME_DIR}/home")
            .with_env_variable("TMPDIR", TMPDIR)
            .with_env_variable("GOTOOLCHAIN", "local")
            .with_env_variable("GOWORK", "off")
            .with_env_variable("GOMODCACHE", MODULE_CACHE)
            .with_env_variable("GOCACHE", BUILD_CACHE)
            .with_mounted_cache(MODULE_CACHE, dag.cache_volume(f"go-mod-{uid}"), owner=uid)
            .with_mounted_cache(BUILD_CACHE, dag.cache_volume(f"go-build-{uid}"), owner=uid)
            .with_mounted_directory(WORKDIR, self.source, owner=uid)
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
    output = await _run(runtime, ["sh", "-ec", LIST_PACKAGE, "go", package], step)
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
