from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type


@object_type
class DockerBuild:
    """Container image build result."""

    container_: dagger.Container
    context_path_: str
    dockerfile_path_: str
    target_: str | None
    build_args_: list[str]

    @function
    def container(self) -> dagger.Container:
        """Return the built container."""
        return self.container_

    @function
    def context_path(self) -> str:
        """Return the build context path."""
        return self.context_path_

    @function
    def dockerfile_path(self) -> str:
        """Return the Dockerfile path."""
        return self.dockerfile_path_

    @function
    def target(self) -> str:
        """Return the build target, if configured."""
        return self.target_ or ""

    @function
    def build_args(self) -> list[str]:
        """Return configured build arguments."""
        return self.build_args_


@object_type
class DockerImage:
    """Published image result."""

    image_ref_: str

    @function
    def image_ref(self) -> str:
        """Return the published image reference."""
        return self.image_ref_


@object_type
class Docker:
    """Docker module entrypoint."""

    @function
    def module(self) -> str:
        """Return the module name."""
        return "docker"

    @function
    def build(
        self,
        source: Annotated[
            dagger.Directory,
            DefaultPath("."),
            Doc("Source directory containing the Docker build context"),
        ],
        context_path: Annotated[str, Doc("Build context path relative to source")] = ".",
        dockerfile_path: Annotated[str, Doc("Dockerfile path relative to context")] = "Dockerfile",
        target: Annotated[str | None, Doc("Optional Docker build target")] = None,
        build_args: Annotated[list[str] | None, Doc("Optional build arguments in KEY=VALUE form")] = None,
    ) -> DockerBuild:
        """Create a Docker build result."""
        return DockerBuild(
            container_=dag.container(),
            context_path_=context_path,
            dockerfile_path_=dockerfile_path,
            target_=target,
            build_args_=build_args or [],
        )

    @function
    def image(
        self,
        image_ref: Annotated[str, Doc("OCI image reference")],
    ) -> DockerImage:
        """Create a Docker image result."""
        return DockerImage(image_ref_=image_ref)
