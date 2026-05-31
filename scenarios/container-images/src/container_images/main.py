from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type


@object_type
class ContainerImages:
    """Container image scenario entrypoint."""

    @function
    def module(self) -> str:
        """Return the scenario name."""
        return "container-images"

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
        registry_address: Annotated[str | None, Doc("Optional registry address for authentication")] = None,
        registry_username: Annotated[str | None, Doc("Optional registry username")] = None,
        registry_password: Annotated[dagger.Secret | None, Doc("Optional registry password or token secret")] = None,
        publish_dry_run: Annotated[bool, Doc("Validate publish inputs without pushing to a registry")] = False,
    ) -> str:
        """Build and publish one explicit image context."""
        docker = dag.docker()
        registry_auth_values = [registry_address, registry_username, registry_password]
        if any(value is not None for value in registry_auth_values):
            if registry_address is None or registry_username is None or registry_password is None:
                msg = "Registry auth requires registry_address, registry_username, and registry_password"
                raise ValueError(msg)
            docker = docker.with_registry_auth(
                address=registry_address,
                username=registry_username,
                password=registry_password,
            )

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
        registry_address: Annotated[str | None, Doc("Optional registry address for authentication")] = None,
        registry_username: Annotated[str | None, Doc("Optional registry username")] = None,
        registry_password: Annotated[dagger.Secret | None, Doc("Optional registry password or token secret")] = None,
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
                    registry_address=registry_address,
                    registry_username=registry_username,
                    registry_password=registry_password,
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
