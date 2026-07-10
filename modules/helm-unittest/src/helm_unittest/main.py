from typing import Annotated, Self

import dagger
from dagger import Doc, dag, function, object_type

DEFAULT_IMAGE_REGISTRY = "docker.io"
DEFAULT_IMAGE_REPOSITORY = "helmunittest/helm-unittest"
# renovate: datasource=docker depName=helmunittest/helm-unittest
DEFAULT_IMAGE_TAG = "4.1.4-1.1.0"
DEFAULT_CONTAINER_USER_ID = "65532"


@object_type
class HelmUnittest:
    """Reusable Helm unittest runtime module."""

    source: dagger.Directory
    image_registry: str
    image_repository: str
    image_tag: str
    container_user_id: str
    container_: dagger.Container | None

    @classmethod
    async def create(
        cls,
        source: Annotated[dagger.Directory, Doc("Helm chart directory")],
        image_registry: Annotated[str | None, Doc("Helm unittest image registry")] = DEFAULT_IMAGE_REGISTRY,
        image_repository: Annotated[str | None, Doc("Helm unittest image repository")] = DEFAULT_IMAGE_REPOSITORY,
        image_tag: Annotated[str | None, Doc("Helm unittest image tag")] = DEFAULT_IMAGE_TAG,
        container_user_id: Annotated[str | None, Doc("Helm unittest container user")] = DEFAULT_CONTAINER_USER_ID,
    ):
        """Constructor."""
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
        """Create a container with the configured Helm unittest runtime."""
        if self.container_:
            return self.container_
        self.container_ = (
            dag.container()
            .from_(address=f"{self.image_registry}/{self.image_repository}:{self.image_tag}")
            .with_exec(
                ["mkdir", "-p", "/tmp/helm-unittest/cache", "/tmp/helm-unittest/config", "/tmp/helm-unittest/data"]
            )
            .with_exec(["chmod", "-R", "777", "/tmp/helm-unittest"])
            .with_user(self.container_user_id)
            .with_env_variable("HOME", "/tmp/helm-unittest")
            .with_env_variable("XDG_CACHE_HOME", "/tmp/helm-unittest/cache")
            .with_env_variable("HELM_CACHE_HOME", "/tmp/helm-unittest/cache")
            .with_env_variable("HELM_CONFIG_HOME", "/tmp/helm-unittest/config")
            .with_env_variable("HELM_UNITTEST_CHART_PATH", "/tmp/helm-unittest/chart")
            .with_directory(
                "$HELM_UNITTEST_CHART_PATH",
                self.source,
                owner=self.container_user_id,
                expand=True,
            )
            .with_workdir("$HELM_UNITTEST_CHART_PATH", expand=True)
        )
        return self.container_

    @function
    def with_dependency_update(self) -> Self:
        """Run Helm dependency update before subsequent Helm unittest commands."""
        self.container_ = self.container().with_exec(["helm", "dependency", "update", "."])
        return self

    @function
    async def test(
        self,
        color: Annotated[bool | None, Doc("Enable color output")] = False,
    ) -> str:
        """Run Helm unittest for the configured chart directory."""
        cmd = ["helm", "unittest", "."]
        if color:
            cmd.append("--color")
        return await self.container().with_exec(cmd).stdout()
