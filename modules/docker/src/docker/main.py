import json
import re
from dataclasses import field
from typing import Annotated, Self

import dagger
from dagger import DefaultPath, Doc, function, object_type

SUPPORTED_BAKE_TARGET_FIELDS = {
    "args",
    "context",
    "dockerfile",
    "labels",
    "platforms",
    "tags",
    "target",
}


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
    tags_: list[str] = field(default_factory=list)
    labels_: dict[str, str] = field(default_factory=dict)

    @function
    def container(self) -> dagger.Container:
        """Return the built container."""
        return self.container_

    @function
    def tags(self) -> list[str]:
        """Return the configured image tags."""
        return self.tags_

    @function
    def image_refs(self) -> list[str]:
        """Return the full OCI image references."""
        return self.tags_

    @function
    def labels(self) -> list[str]:
        """Return the configured image labels in KEY=VALUE form."""
        return [f"{k}={v}" for k, v in self.labels_.items()]

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
            tags_=self.tags_,
            labels_=self.labels_,
        )

    @function
    async def publish(
        self,
        image_refs: Annotated[list[str] | None, Doc("Optional OCI image references to publish")] = None,
    ) -> "DockerImage":
        """Publish the built image to explicit or build-configured OCI image references."""
        publish_refs = self.tags_ if image_refs is None else image_refs
        if not publish_refs:
            msg = "At least one image reference is required"
            raise ValueError(msg)

        container = self._with_registry_auths(self.container_)
        platform_variants = [self._with_registry_auths(variant) for variant in self.platform_variants_[1:]]

        published_refs: list[str] = []
        for image_ref in publish_refs:
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
        if not address:
            msg = "Registry address must not be empty"
            raise ValueError(msg)
        if not username:
            msg = "Registry username must not be empty"
            raise ValueError(msg)
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
        tags: Annotated[list[str] | None, Doc("Optional image tags")] = None,
        labels: Annotated[list[str] | None, Doc("Optional image labels in KEY=VALUE form")] = None,
    ) -> DockerBuild:
        """Build a container image from a Dockerfile context."""
        parsed_build_args = self._parse_build_args(build_args or [])
        parsed_labels = self._parse_labels(labels or [])
        context = source.directory(context_path)
        platform_variants = [
            self._with_labels(
                context.docker_build(
                    dockerfile=dockerfile_path,
                    target=target or "",
                    build_args=parsed_build_args,
                    platform=platform,
                ),
                parsed_labels,
            )
            for platform in platforms or []
        ]
        container = (
            platform_variants[0]
            if platform_variants
            else self._with_labels(
                context.docker_build(
                    dockerfile=dockerfile_path,
                    target=target or "",
                    build_args=parsed_build_args,
                ),
                parsed_labels,
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
            tags_=tags or [],
            labels_=parsed_labels,
        )

    @function
    async def build_from_bake(
        self,
        source: Annotated[
            dagger.Directory,
            DefaultPath("."),
            Doc("Source directory containing the Docker build context and Bake file"),
        ],
        target: Annotated[
            str | None,
            Doc("Optional Bake target to build; omit when the manifest contains exactly one target"),
        ] = None,
        bake_path: Annotated[str, Doc("Path to the Bake file relative to source")] = "docker-bake.json",
        variable_overrides: Annotated[
            list[str] | None,
            Doc("Optional Bake variable overrides in KEY=VALUE form"),
        ] = None,
    ) -> DockerBuild:
        """Build a container image from a Docker Buildx Bake target."""
        try:
            bake_contents = await source.file(bake_path).contents()
        except Exception as exc:
            msg = f"Bake file not found: {bake_path}"
            raise ValueError(msg) from exc
        try:
            bake_data = json.loads(bake_contents)
        except json.JSONDecodeError as exc:
            msg = f"Failed to parse Bake file {bake_path}: {exc}"
            raise ValueError(msg) from exc

        variables = bake_data.get("variable", {})
        vars_map: dict[str, str] = {
            name: str(variable.get("default", "")) for name, variable in variables.items() if isinstance(variable, dict)
        }
        vars_map.update(self._parse_key_values(variable_overrides or [], "Bake variable override"))

        targets = bake_data.get("target", {})
        if target is None:
            if len(targets) != 1:
                msg = (
                    f"Bake file {bake_path} must define exactly one target when target is omitted; found {len(targets)}"
                )
                raise ValueError(msg)
            target = next(iter(targets))
        if target not in targets:
            msg = f"Bake target {target!r} not found in {bake_path}"
            raise ValueError(msg)

        target_data = targets[target]
        unsupported_fields = sorted(set(target_data) - SUPPORTED_BAKE_TARGET_FIELDS)
        if unsupported_fields:
            msg = f"Unsupported fields in Bake target {target!r}: {', '.join(unsupported_fields)}"
            raise ValueError(msg)

        bake_args = target_data.get("args", {})
        build_args: list[str] = []
        if isinstance(bake_args, dict):
            for k, v in bake_args.items():
                build_args.append(f"{k}={self._interpolate_bake_string(str(v), vars_map, f'args.{k}')}")
        elif isinstance(bake_args, list):
            for arg in bake_args:
                name, _, value = arg.partition("=")
                if name:
                    build_args.append(f"{name}={self._interpolate_bake_string(value, vars_map, f'args.{name}')}")

        context_path = self._interpolate_bake_string(target_data.get("context", "."), vars_map, "context")
        dockerfile_path = self._interpolate_bake_string(
            target_data.get("dockerfile", "Dockerfile"),
            vars_map,
            "dockerfile",
        )
        docker_target = self._interpolate_bake_string(target_data.get("target", "") or "", vars_map, "target")

        bake_platforms = target_data.get("platforms", [])
        platforms: list[dagger.Platform] = [
            dagger.Platform(self._interpolate_bake_string(p, vars_map, "platforms")) for p in bake_platforms
        ]

        bake_tags = target_data.get("tags", [])
        tags: list[str] = [self._interpolate_bake_string(t, vars_map, "tags") for t in bake_tags]
        if not tags or any(not tag for tag in tags):
            msg = f"Bake target {target!r} must define at least one non-empty tag"
            raise ValueError(msg)

        bake_labels = target_data.get("labels", {})
        labels: list[str] = []
        if isinstance(bake_labels, dict):
            labels = [
                f"{k}={self._interpolate_bake_string(str(v), vars_map, f'labels.{k}')}" for k, v in bake_labels.items()
            ]
        elif isinstance(bake_labels, list):
            labels = [self._interpolate_bake_string(label, vars_map, "labels") for label in bake_labels]

        return self.build(
            source=source,
            context_path=context_path,
            dockerfile_path=dockerfile_path,
            target=docker_target or None,
            build_args=build_args,
            platforms=platforms,
            tags=tags,
            labels=labels,
        )

    def _interpolate_bake_string(self, text: str, vars_map: dict[str, str], field: str) -> str:
        """Interpolate ${VAR} placeholders in a string."""
        if not text:
            return ""

        def replace(match: re.Match) -> str:
            var_name = match.group(1)
            return vars_map.get(var_name, match.group(0))

        resolved = re.sub(r"\${(\w+)}", replace, text)
        if "$" in resolved:
            msg = f"Unsupported Bake interpolation in {field}: {text!r}"
            raise ValueError(msg)
        return resolved

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

    def _parse_labels(self, labels: list[str]) -> dict[str, str]:
        return self._parse_key_values(labels, "label")

    def _parse_key_values(self, values: list[str], kind: str) -> dict[str, str]:
        parsed: dict[str, str] = {}
        for item in values:
            name, separator, value = item.partition("=")
            if separator != "=" or not name:
                msg = f"Invalid {kind} {item!r}: expected KEY=VALUE with a non-empty key"
                raise ValueError(msg)
            parsed[name] = value
        return parsed

    def _with_labels(self, container: dagger.Container, labels: dict[str, str]) -> dagger.Container:
        for name, value in labels.items():
            container = container.with_label(name, value)
        return container
