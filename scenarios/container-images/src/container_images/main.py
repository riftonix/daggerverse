from dataclasses import field
from typing import Annotated, Self

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type


@object_type
class ContainerImagesRegistryAuth:
    """Registry authentication configuration."""

    address_: str
    username_: str
    password_: dagger.Secret


@object_type
class ContainerImages:
    """Container image scenario entrypoint."""

    registry_auths_: list[ContainerImagesRegistryAuth] = field(default_factory=list)

    @function
    def module(self) -> str:
        """Return the scenario name."""
        return "container-images"

    @function
    def registry_auth_addresses(self) -> list[str]:
        """Return configured registry auth addresses."""
        return [registry_auth.address_ for registry_auth in self.registry_auths_]

    @function
    def with_registry_auth(
        self,
        address: Annotated[str, Doc("Registry address to authenticate against")],
        username: Annotated[str, Doc("Registry username")],
        password: Annotated[dagger.Secret, Doc("Registry password or token secret")],
    ) -> Self:
        """Configure registry authentication for later publication."""
        if not address:
            msg = "Registry address must not be empty"
            raise ValueError(msg)
        if not username:
            msg = "Registry username must not be empty"
            raise ValueError(msg)
        return ContainerImages(
            registry_auths_=[
                *self.registry_auths_,
                ContainerImagesRegistryAuth(
                    address_=address,
                    username_=username,
                    password_=password,
                ),
            ]
        )

    @function
    async def verify_image(
        self,
        source: Annotated[
            dagger.Directory,
            DefaultPath("."),
            Doc("Source directory containing the image build context"),
        ],
        context_path: Annotated[str, Doc("Build context path relative to source")],
        dockerfile_path: Annotated[str, Doc("Dockerfile path relative to context")] = "Dockerfile",
        target: Annotated[str | None, Doc("Optional Docker build target")] = None,
        build_args: Annotated[list[str] | None, Doc("Optional build arguments in KEY=VALUE form")] = None,
        platforms: Annotated[list[dagger.Platform] | None, Doc("Optional target platforms")] = None,
        smoke_command: Annotated[list[str] | None, Doc("Optional command to run in the built image")] = None,
    ) -> str:
        """Build and optionally smoke-check one explicit image context."""
        build = dag.docker().build(
            source=source,
            context_path=context_path,
            dockerfile_path=dockerfile_path,
            target=target,
            build_args=build_args,
            platforms=platforms,
        )

        if smoke_command is not None:
            build = build.with_smoke_check(smoke_command)

        platform_variants = await build.platform_variants()
        if platform_variants:
            for variant in platform_variants:
                await variant.sync()
        else:
            await build.container().sync()

        return f"verified {context_path}"

    @function
    async def verify_images(
        self,
        source: Annotated[
            dagger.Directory,
            DefaultPath("."),
            Doc("Source directory containing the image build contexts"),
        ],
        context_paths: Annotated[list[str], Doc("Build context paths relative to source")],
        dockerfile_path: Annotated[str, Doc("Dockerfile path relative to each context")] = "Dockerfile",
        target: Annotated[str | None, Doc("Optional Docker build target")] = None,
        build_args: Annotated[list[str] | None, Doc("Optional build arguments in KEY=VALUE form")] = None,
        platforms: Annotated[list[dagger.Platform] | None, Doc("Optional target platforms")] = None,
        smoke_command: Annotated[list[str] | None, Doc("Optional command to run in each built image")] = None,
    ) -> list[str]:
        """Build and optionally smoke-check multiple explicit image contexts."""
        if not context_paths:
            msg = "At least one image context path is required"
            raise ValueError(msg)

        results: list[str] = []
        for context_path in context_paths:
            results.append(
                await self.verify_image(
                    source=source,
                    context_path=context_path,
                    dockerfile_path=dockerfile_path,
                    target=target,
                    build_args=build_args,
                    platforms=platforms,
                    smoke_command=smoke_command,
                )
            )

        return results

    @function
    async def verify_bake_target(
        self,
        source: Annotated[
            dagger.Directory,
            DefaultPath("."),
            Doc("Source directory containing the Bake file and image build context"),
        ],
        bake_path: Annotated[str, Doc("Path to the Bake file relative to source")],
        bake_target: Annotated[
            str | None,
            Doc("Optional Bake target to verify; omit when the manifest contains exactly one target"),
        ] = None,
        variable_overrides: Annotated[
            list[str] | None,
            Doc("Optional Bake variable overrides in KEY=VALUE form"),
        ] = None,
        smoke_command: Annotated[list[str] | None, Doc("Optional command to run in the built image")] = None,
    ) -> str:
        """Build and optionally smoke-check one Bake target without publishing."""
        build = dag.docker().build_from_bake(
            source=source,
            bake_path=bake_path,
            target=bake_target,
            variable_overrides=variable_overrides,
        )

        if smoke_command is not None:
            build = build.with_smoke_check(smoke_command)

        platform_variants = await build.platform_variants()
        if platform_variants:
            for variant in platform_variants:
                await variant.sync()
        else:
            await build.container().sync()

        return (
            f"verified Bake target {bake_target}"
            if bake_target is not None
            else f"verified Bake target from {bake_path}"
        )

    @function
    async def publish_image(
        self,
        source: Annotated[
            dagger.Directory,
            DefaultPath("."),
            Doc("Source directory containing the image build context"),
        ],
        context_path: Annotated[str, Doc("Build context path relative to source")],
        image_ref: Annotated[str, Doc("Destination OCI image reference")],
        dockerfile_path: Annotated[str, Doc("Dockerfile path relative to context")] = "Dockerfile",
        target: Annotated[str | None, Doc("Optional Docker build target")] = None,
        build_args: Annotated[list[str] | None, Doc("Optional build arguments in KEY=VALUE form")] = None,
        platforms: Annotated[list[dagger.Platform] | None, Doc("Optional target platforms")] = None,
        publish_dry_run: Annotated[bool, Doc("Validate publish inputs without pushing to a registry")] = False,
    ) -> str:
        """Build and publish one explicit image context."""
        docker = self._docker()
        build = docker.build(
            source=source,
            context_path=context_path,
            dockerfile_path=dockerfile_path,
            target=target,
            build_args=build_args,
            platforms=platforms,
        )
        if publish_dry_run:
            build = build.with_publish_dry_run()

        image = build.publish(image_refs=[image_ref])
        return await image.image_ref()

    @function
    async def publish_bake_target(
        self,
        source: Annotated[
            dagger.Directory,
            DefaultPath("."),
            Doc("Source directory containing the Bake file and image build context"),
        ],
        bake_path: Annotated[str, Doc("Path to the Bake file relative to source")],
        bake_target: Annotated[
            str | None,
            Doc("Optional Bake target to publish; omit when the manifest contains exactly one target"),
        ] = None,
        variable_overrides: Annotated[
            list[str] | None,
            Doc("Optional Bake variable overrides in KEY=VALUE form"),
        ] = None,
        publish_dry_run: Annotated[bool, Doc("Validate publish inputs without pushing to a registry")] = False,
    ) -> list[str]:
        """Build and publish the resolved image references for one Bake target."""
        docker = self._docker()
        build = docker.build_from_bake(
            source=source,
            bake_path=bake_path,
            target=bake_target,
            variable_overrides=variable_overrides,
        )
        if publish_dry_run:
            build = build.with_publish_dry_run()

        image_refs = await build.image_refs()
        image = build.publish(image_refs=image_refs)
        return await image.image_refs()

    @function
    async def get_bake_release_tag(
        self,
        source: Annotated[
            dagger.Directory,
            DefaultPath("."),
            Doc("Source directory containing the Bake file"),
        ],
        bake_path: Annotated[str, Doc("Path to the Bake file relative to source")],
        component_path: Annotated[str, Doc("Repository component path used as the Git release tag prefix")],
        bake_target: Annotated[
            str | None,
            Doc("Optional Bake target to inspect; omit when the manifest contains exactly one target"),
        ] = None,
        variable_overrides: Annotated[
            list[str] | None,
            Doc("Optional Bake variable overrides in KEY=VALUE form"),
        ] = None,
    ) -> str:
        """Return a Git release tag rendered from resolved Bake metadata."""
        normalized_component_path = component_path.strip("/")
        if not normalized_component_path:
            msg = "Component path must not be empty"
            raise ValueError(msg)

        target = dag.docker().resolve_bake_target(
            source=source,
            bake_path=bake_path,
            target=bake_target,
            variable_overrides=variable_overrides,
        )
        image_refs = await target.image_refs()
        release_tags = {self._image_ref_tag(image_ref) for image_ref in image_refs}
        if len(release_tags) != 1:
            msg = f"Bake image references must resolve to exactly one release tag; found {sorted(release_tags)}"
            raise ValueError(msg)

        return f"{normalized_component_path}/{release_tags.pop()}"

    @function
    async def publish_images(
        self,
        source: Annotated[
            dagger.Directory,
            DefaultPath("."),
            Doc("Source directory containing the image build contexts"),
        ],
        publish_specs: Annotated[list[str], Doc("Image publish specs in CONTEXT_PATH=IMAGE_REF form")],
        dockerfile_path: Annotated[str, Doc("Dockerfile path relative to each context")] = "Dockerfile",
        target: Annotated[str | None, Doc("Optional Docker build target")] = None,
        build_args: Annotated[list[str] | None, Doc("Optional build arguments in KEY=VALUE form")] = None,
        platforms: Annotated[list[dagger.Platform] | None, Doc("Optional target platforms")] = None,
        publish_dry_run: Annotated[bool, Doc("Validate publish inputs without pushing to a registry")] = False,
    ) -> list[str]:
        """Build and publish multiple explicit image contexts."""
        if not publish_specs:
            msg = "At least one image publish spec is required"
            raise ValueError(msg)

        published_refs: list[str] = []
        for publish_spec in publish_specs:
            context_path, image_ref = self._parse_publish_spec(publish_spec)
            published_refs.append(
                await self.publish_image(
                    source=source,
                    context_path=context_path,
                    image_ref=image_ref,
                    dockerfile_path=dockerfile_path,
                    target=target,
                    build_args=build_args,
                    platforms=platforms,
                    publish_dry_run=publish_dry_run,
                )
            )

        return published_refs

    def _parse_publish_spec(self, publish_spec: str) -> tuple[str, str]:
        context_path, separator, image_ref = publish_spec.partition("=")
        if separator != "=" or not context_path or not image_ref:
            msg = f"Invalid publish spec {publish_spec!r}: expected CONTEXT_PATH=IMAGE_REF"
            raise ValueError(msg)
        return context_path, image_ref

    def _image_ref_tag(self, image_ref: str) -> str:
        repository, separator, tag = image_ref.rpartition(":")
        if separator != ":" or not repository or not tag or "/" in tag:
            msg = f"Image reference {image_ref!r} must include a release tag"
            raise ValueError(msg)
        return tag

    def _docker(self):
        docker = dag.docker()
        for registry_auth in self.registry_auths_:
            docker = docker.with_registry_auth(
                address=registry_auth.address_,
                username=registry_auth.username_,
                password=registry_auth.password_,
            )
        return docker
