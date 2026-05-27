from typing import Annotated, Self

import dagger
from dagger import DefaultPath, Doc, function, object_type


@object_type
class DockerRegistryAuth:
    """Registry authentication configuration."""

    address_: str
    username_: str
    password_: dagger.Secret

    @function
    def address(self) -> str:
        """Return the registry address."""
        return self.address_

    @function
    def username(self) -> str:
        """Return the registry username."""
        return self.username_


@object_type
class DockerBuild:
    """Container image build result."""

    container_: dagger.Container
    context_path_: str
    dockerfile_path_: str
    target_: str | None
    build_args_: list[str]
    platforms_: list[dagger.Platform]
    platform_variants_: list[dagger.Container]
    registry_auths_: list[DockerRegistryAuth] | None = None
    publish_dry_run_: bool = False

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

    @function
    def platforms(self) -> list[dagger.Platform]:
        """Return configured target platforms."""
        return self.platforms_

    @function
    def platform_variants(self) -> list[dagger.Container]:
        """Return platform-specific container variants."""
        return self.platform_variants_

    @function
    async def with_smoke_check(
        self,
        command: Annotated[list[str], Doc("Command to run in the built container")],
    ) -> Self:
        """Run a smoke command in the built container."""
        if not command:
            msg = "Smoke command must not be empty"
            raise ValueError(msg)

        containers = self.platform_variants_ or [self.container_]
        for container in containers:
            await container.with_exec(command).sync()
        return self

    @function
    def with_publish_dry_run(self) -> Self:
        """Return a build that validates publish inputs without pushing."""
        return DockerBuild(
            container_=self.container_,
            context_path_=self.context_path_,
            dockerfile_path_=self.dockerfile_path_,
            target_=self.target_,
            build_args_=self.build_args_,
            platforms_=self.platforms_,
            platform_variants_=self.platform_variants_,
            registry_auths_=self.registry_auths_,
            publish_dry_run_=True,
        )

    @function
    async def publish(
        self,
        image_refs: Annotated[list[str], Doc("OCI image references to publish")],
    ) -> "DockerImage":
        """Publish the built image to one or more OCI image references."""
        if not image_refs:
            msg = "At least one image reference is required"
            raise ValueError(msg)

        container = self._with_registry_auths(self.container_)
        platform_variants = [self._with_registry_auths(variant) for variant in self.platform_variants_[1:]]

        published_refs: list[str] = []
        for image_ref in image_refs:
            if not image_ref:
                msg = "Image references must not be empty"
                raise ValueError(msg)
            if self.publish_dry_run_:
                published_refs.append(image_ref)
                continue
            published_refs.append(await container.publish(image_ref, platform_variants=platform_variants))

        return DockerImage(
            image_ref_=published_refs[0],
            image_refs_=published_refs,
        )

    def _with_registry_auths(self, container: dagger.Container) -> dagger.Container:
        for registry_auth in self.registry_auths_ or []:
            container = container.with_registry_auth(
                address=registry_auth.address_,
                username=registry_auth.username_,
                secret=registry_auth.password_,
            )
        return container


@object_type
class DockerImage:
    """Published image result."""

    image_ref_: str
    image_refs_: list[str] | None = None

    @function
    def image_ref(self) -> str:
        """Return the published image reference."""
        return self.image_ref_

    @function
    def image_refs(self) -> list[str]:
        """Return all published image references."""
        return self.image_refs_ or [self.image_ref_]


@object_type
class Docker:
    """Docker module entrypoint."""

    registry_auths_: list[DockerRegistryAuth] | None = None

    @function
    def module(self) -> str:
        """Return the module name."""
        return "docker"

    @function
    def registry_auth_addresses(self) -> list[str]:
        """Return configured registry auth addresses."""
        return [registry_auth.address_ for registry_auth in self.registry_auths_ or []]

    @function
    def with_registry_auth(
        self,
        address: Annotated[str, Doc("Registry address to authenticate against")],
        username: Annotated[str, Doc("Registry username")],
        password: Annotated[dagger.Secret, Doc("Registry password or token secret")],
    ) -> Self:
        """Configure registry authentication for later registry operations."""
        return Docker(
            registry_auths_=[
                *(self.registry_auths_ or []),
                DockerRegistryAuth(
                    address_=address,
                    username_=username,
                    password_=password,
                ),
            ]
        )

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
        platforms: Annotated[list[dagger.Platform] | None, Doc("Optional target platforms")] = None,
    ) -> DockerBuild:
        """Build a container image from a Dockerfile context."""
        parsed_build_args = self._parse_build_args(build_args or [])
        context = source.directory(context_path)
        platform_variants = [
            context.docker_build(
                dockerfile=dockerfile_path,
                target=target or "",
                build_args=parsed_build_args,
                platform=platform,
            )
            for platform in platforms or []
        ]
        container = (
            platform_variants[0]
            if platform_variants
            else context.docker_build(
                dockerfile=dockerfile_path,
                target=target or "",
                build_args=parsed_build_args,
            )
        )
        return DockerBuild(
            container_=container,
            context_path_=context_path,
            dockerfile_path_=dockerfile_path,
            target_=target,
            build_args_=build_args or [],
            platforms_=platforms or [],
            platform_variants_=platform_variants,
            registry_auths_=self.registry_auths_,
            publish_dry_run_=False,
        )

    @function
    def image(
        self,
        image_ref: Annotated[str, Doc("OCI image reference")],
    ) -> DockerImage:
        """Create a Docker image result."""
        return DockerImage(image_ref_=image_ref, image_refs_=[image_ref])

    def _parse_build_args(self, build_args: list[str]) -> list[dagger.BuildArg]:
        parsed: list[dagger.BuildArg] = []
        for build_arg in build_args:
            name, separator, value = build_arg.partition("=")
            if separator != "=" or not name:
                msg = f"Invalid build argument {build_arg!r}: expected KEY=VALUE with a non-empty key"
                raise ValueError(msg)
            parsed.append(dagger.BuildArg(name=name, value=value))
        return parsed
