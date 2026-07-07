from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type

DEFAULT_IMAGE_REGISTRY = "ghcr.io"
DEFAULT_IMAGE_REPOSITORY = "opentofu/opentofu"
DEFAULT_IMAGE_TAG = "latest"
DEFAULT_USER_ID = "65532"


@object_type
class Opentofu:
    image_registry: str
    image_repository: str
    image_tag: str
    user_id: str
    executor: str
    container_: dagger.Container | None

    @classmethod
    async def create(
        cls,
        image_registry: Annotated[str | None, Doc("OpenTofu image registry")] = DEFAULT_IMAGE_REGISTRY,
        image_repository: Annotated[str | None, Doc("OpenTofu image repository")] = DEFAULT_IMAGE_REPOSITORY,
        image_tag: Annotated[str | None, Doc("OpenTofu image tag")] = DEFAULT_IMAGE_TAG,
        user_id: Annotated[str | None, Doc("OpenTofu image user")] = DEFAULT_USER_ID,
        executor: Annotated[str, Doc("Choice of IaC executor")] = "tofu",
    ):
        """Constructor"""
        return cls(
            image_registry=image_registry or DEFAULT_IMAGE_REGISTRY,
            image_repository=image_repository or DEFAULT_IMAGE_REPOSITORY,
            image_tag=image_tag or DEFAULT_IMAGE_TAG,
            user_id=user_id or DEFAULT_USER_ID,
            executor=executor,
            container_=None,
        )

    @function
    def container(self) -> dagger.Container:
        """Returns container"""
        if self.container_:
            return self.container_
        address = f"{self.image_registry}/{self.image_repository}:{self.image_tag}"
        container: dagger.Container = dag.container()
        self.container_ = (
            container.from_(address=address)
            .with_user(self.user_id)
            .with_env_variable("TF_CLI_CONFIG_FILE", "/src/.tf.rc")
        )
        return self.container_

    @function
    async def lint(self, source: Annotated[dagger.Directory, Doc("IaC project path")]) -> str:
        """Verify that the manifests is well-formed"""
        container: dagger.Container = self.container().with_directory("/src", source).with_workdir("/src")
        lint_cmd: list[str] = [self.executor, "fmt", "-recursive", "-check", "-diff", "-no-color"]
        init_cmd: list[str] = [self.executor, "init"]
        validate_cmd: list[str] = [self.executor, "validate", "-no-color"]
        return await container.with_exec(lint_cmd).with_exec(init_cmd).with_exec(validate_cmd).stdout()
