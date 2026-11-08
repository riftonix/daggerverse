"""Run Updatecli manifests in a configurable container."""

from typing import Annotated, Self
from uuid import uuid4

import dagger
from dagger import Doc, dag, function, object_type

DEFAULT_IMAGE_REGISTRY = "ghcr.io"
DEFAULT_IMAGE_REPOSITORY = "updatecli/updatecli"
# renovate: datasource=docker depName=ghcr.io/updatecli/updatecli
DEFAULT_IMAGE_TAG = "v0.123.0"
DEFAULT_CONTAINER_USER_ID = "65532"

WORK_DIRECTORY = "/work"
CONFIG_DIRECTORY = "/updatecli"
HOME_DIRECTORY = "/tmp/updatecli-home"


@object_type
class Updatecli:
    """Reusable Updatecli runtime without source-specific orchestration."""

    source: dagger.Directory | None
    image_registry: str
    image_repository: str
    image_tag: str
    container_user_id: str
    container_: dagger.Container | None

    @classmethod
    async def create(
        cls,
        source: Annotated[dagger.Directory | None, Doc("Optional working tree for local targets")] = None,
        image_registry: Annotated[str | None, Doc("Updatecli runtime image registry")] = DEFAULT_IMAGE_REGISTRY,
        image_repository: Annotated[str | None, Doc("Updatecli runtime image repository")] = DEFAULT_IMAGE_REPOSITORY,
        image_tag: Annotated[str | None, Doc("Updatecli runtime image tag")] = DEFAULT_IMAGE_TAG,
        container_user_id: Annotated[str | None, Doc("Container execution user")] = DEFAULT_CONTAINER_USER_ID,
    ) -> Self:
        """Configure the runtime; source may be omitted for SCM-backed manifests."""
        return cls(
            source=source,
            image_registry=image_registry or DEFAULT_IMAGE_REGISTRY,
            image_repository=image_repository or DEFAULT_IMAGE_REPOSITORY,
            image_tag=image_tag or DEFAULT_IMAGE_TAG,
            container_user_id=container_user_id or DEFAULT_CONTAINER_USER_ID,
            container_=None,
        )

    @function
    def container(self) -> dagger.Container:
        """Return the runtime with a writable home and working tree."""
        if self.container_ is None:
            self.container_ = (
                dag.container()
                .from_(f"{self.image_registry}/{self.image_repository}:{self.image_tag}")
                .with_user("0")
                .with_exec(["mkdir", "-p", WORK_DIRECTORY, CONFIG_DIRECTORY, HOME_DIRECTORY])
                .with_exec(["chown", "-R", self.container_user_id, WORK_DIRECTORY, CONFIG_DIRECTORY, HOME_DIRECTORY])
                .with_user(self.container_user_id)
                .with_env_variable("HOME", HOME_DIRECTORY)
                .with_env_variable("NO_COLOR", "1")
                .with_directory(
                    WORK_DIRECTORY,
                    self.source if self.source is not None else dag.directory(),
                    owner=self.container_user_id,
                )
                .with_workdir(WORK_DIRECTORY)
            )
        return self.container_

    @function
    def with_secret_variable(
        self,
        name: Annotated[str, Doc("Secret environment variable name")],
        secret: Annotated[dagger.Secret, Doc("Secret value supplied by the caller")],
    ) -> Self:
        """Add a secret environment variable without exposing its value in logs."""
        self.container_ = self.container().with_secret_variable(name, secret)
        return self

    @function
    def with_env_variable(
        self,
        name: Annotated[str, Doc("Environment variable name")],
        value: Annotated[str, Doc("Non-secret environment variable value")],
    ) -> Self:
        """Add a plain environment variable; use with_secret_variable for tokens."""
        self.container_ = self.container().with_env_variable(name, value)
        return self

    @function
    def with_directory(
        self,
        path: Annotated[str, Doc("Destination path inside the runtime container")],
        directory: Annotated[dagger.Directory, Doc("Directory containing helpers or other runtime files")],
    ) -> Self:
        """Add helper files owned by the runtime user."""
        self.container_ = self.container().with_directory(path, directory, owner=self.container_user_id)
        return self

    @function
    async def diff(
        self,
        config: Annotated[dagger.File, Doc("Updatecli YAML or JSON manifest, including Go templates")],
        values: Annotated[list[dagger.File] | None, Doc("Optional values files, merged in supplied order")] = None,
    ) -> str:
        """Preview pipeline changes and return combined stdout and stderr."""
        return await self._exec(["pipeline", "diff"], config, values).stdout()

    @function
    async def apply(
        self,
        config: Annotated[dagger.File, Doc("Updatecli YAML or JSON manifest, including Go templates")],
        values: Annotated[list[dagger.File] | None, Doc("Optional values files, merged in supplied order")] = None,
    ) -> str:
        """Apply pipeline changes, commits, and actions declared by the manifest."""
        return await self._exec(["pipeline", "apply"], config, values).stdout()

    @function
    async def applied_source(
        self,
        config: Annotated[dagger.File, Doc("Updatecli manifest whose targets update the local working tree")],
        values: Annotated[list[dagger.File] | None, Doc("Optional values files, merged in supplied order")] = None,
    ) -> dagger.Directory:
        """Apply the manifest and return the resulting /work tree, not SCM clones."""
        container = self._exec(["pipeline", "apply"], config, values)
        await container.sync()
        return container.directory(WORK_DIRECTORY)

    @function
    async def manifest_show(
        self,
        config: Annotated[dagger.File, Doc("Updatecli manifest to render without executing pipelines")],
        values: Annotated[list[dagger.File] | None, Doc("Optional values files, merged in supplied order")] = None,
    ) -> str:
        """Render manifests using Updatecli without running sources or targets."""
        return await self._exec(["manifest", "show", "--disable-prepare"], config, values).stdout()

    def _exec(
        self,
        command: list[str],
        config: dagger.File,
        values: list[dagger.File] | None,
    ) -> dagger.Container:
        config_path = f"{CONFIG_DIRECTORY}/manifest.yaml"
        container = self.container().with_file(config_path, config, owner=self.container_user_id)
        # The runtime is pinned and ephemeral; skip the release lookup on every run.
        args = [*command, "--config", config_path, "--disable-version-check"]
        for index, value in enumerate(values or []):
            value_path = f"{CONFIG_DIRECTORY}/values-{index}.yaml"
            container = container.with_file(value_path, value, owner=self.container_user_id)
            args.extend(["--values", value_path])

        # Upstream state is external to Dagger's input tree; recheck it on each run.
        container = container.with_env_variable("UPDATECLI_RUN_ID", str(uuid4()))
        # Updatecli writes its report to stderr; merge it into the returned stdout.
        return container.with_exec(["sh", "-c", 'exec updatecli "$@" 2>&1', "updatecli", *args])
