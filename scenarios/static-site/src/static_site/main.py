from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type

DEFAULT_ENGINE = "hugo"
SUPPORTED_ENGINES = (DEFAULT_ENGINE,)
DEFAULT_HUGO_IMAGE_REGISTRY = "ghcr.io"
DEFAULT_HUGO_IMAGE_REPOSITORY = "riftonix/container-images/hugo-autoprefixer"
# renovate: datasource=docker depName=ghcr.io/riftonix/container-images/hugo-autoprefixer versioning=loose
DEFAULT_HUGO_IMAGE_TAG = "0.165.0-10.5.6"
DEFAULT_HUGO_CONTAINER_USER_ID = "65532"


@object_type
class StaticSite:
    """Static-site scenario entrypoint."""

    source: dagger.Directory
    content_sources: list[dagger.Directory]
    content_source_paths: list[str]
    content_target_paths: list[str]
    content_contributors: list[str]
    hugo_image_registry: str
    hugo_image_repository: str
    hugo_image_tag: str
    hugo_container_user_id: str
    npm_registry: str | None

    @classmethod
    async def create(
        cls,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Static site source directory")],
        content_sources: Annotated[list[dagger.Directory] | None, Doc("External content source directories")] = None,
        content_source_paths: Annotated[list[str] | None, Doc("Paths selected within content sources")] = None,
        content_target_paths: Annotated[list[str] | None, Doc("Content target paths within the site")] = None,
        content_contributors: Annotated[list[str] | None, Doc("Contributor names for collision diagnostics")] = None,
        hugo_image_registry: Annotated[str | None, Doc("Hugo image registry")] = DEFAULT_HUGO_IMAGE_REGISTRY,
        hugo_image_repository: Annotated[str | None, Doc("Hugo image repository")] = DEFAULT_HUGO_IMAGE_REPOSITORY,
        hugo_image_tag: Annotated[str | None, Doc("Hugo image tag")] = DEFAULT_HUGO_IMAGE_TAG,
        hugo_container_user_id: Annotated[str | None, Doc("Hugo container user")] = DEFAULT_HUGO_CONTAINER_USER_ID,
        npm_registry: Annotated[str | None, Doc("Optional npm registry or proxy URL")] = None,
    ):
        """Constructor."""
        return cls(
            source=source,
            content_sources=content_sources or [],
            content_source_paths=content_source_paths or [],
            content_target_paths=content_target_paths or [],
            content_contributors=content_contributors or [],
            hugo_image_registry=hugo_image_registry or DEFAULT_HUGO_IMAGE_REGISTRY,
            hugo_image_repository=hugo_image_repository or DEFAULT_HUGO_IMAGE_REPOSITORY,
            hugo_image_tag=hugo_image_tag or DEFAULT_HUGO_IMAGE_TAG,
            hugo_container_user_id=hugo_container_user_id or DEFAULT_HUGO_CONTAINER_USER_ID,
            npm_registry=npm_registry,
        )

    @function
    def module(self) -> str:
        """Return the scenario name."""
        return "static-site"

    @function
    async def verify_site(
        self,
        site_base_url: Annotated[str, Doc("Base URL to render and validate the site with")],
        engine: Annotated[str, Doc("Static-site engine to use")] = DEFAULT_ENGINE,
    ) -> str:
        """Verify a static site with the selected engine."""
        selected_engine = self._select_engine(engine)

        if selected_engine == "hugo":
            return await self._hugo(await self._composed_source()).validate(
                site_base_url=site_base_url,
            )

        msg = f"Static-site engine dispatch is incomplete for {selected_engine!r}"
        raise RuntimeError(msg)

    @function
    async def render_site(
        self,
        site_base_url: Annotated[str, Doc("Base URL to render the site with")],
        engine: Annotated[str, Doc("Static-site engine to use")] = DEFAULT_ENGINE,
    ) -> dagger.Directory:
        """Render a static site with the selected engine."""
        selected_engine = self._select_engine(engine)

        if selected_engine == "hugo":
            return await self._hugo(await self._composed_source()).build(
                site_base_url=site_base_url,
            )

        msg = f"Static-site engine dispatch is incomplete for {selected_engine!r}"
        raise RuntimeError(msg)

    def _hugo(self, source: dagger.Directory):
        """Return a Hugo module configured with the scenario Hugo runtime image inputs."""
        return dag.hugo(
            source=source,
            image_registry=self.hugo_image_registry,
            image_repository=self.hugo_image_repository,
            image_tag=self.hugo_image_tag,
            user_id=self.hugo_container_user_id,
            npm_registry=self.npm_registry,
        )

    @function
    async def validate_content_mounts(self) -> str:
        """Validate that content mounts do not overwrite target paths."""
        collisions = await self.get_content_mount_collisions()
        if collisions:
            msg = "Static-site content path collision: " + "; ".join(collisions)
            raise ValueError(msg)

        return "validated content mount paths"

    @function
    async def get_content_mount_collisions(self) -> list[str]:
        """Return content mount path collisions without failing."""
        contributors_by_virtual_path: dict[str, list[str]] = {}

        for source, source_path, target_path, contributor in self._mounts():
            for relative_path in await self._directory_files(source.directory(source_path)):
                virtual_path = f"{target_path}/{relative_path}"
                mapping = f"{contributor}:{source_path}->{target_path}"
                contributors_by_virtual_path.setdefault(virtual_path, []).append(mapping)

        collisions: list[str] = []
        for virtual_path, contributors in sorted(contributors_by_virtual_path.items()):
            unique_contributors = sorted(set(contributors))
            if len(unique_contributors) > 1:
                collisions.append(f"{virtual_path}: {', '.join(unique_contributors)}")

        return collisions

    def _select_engine(self, engine: str) -> str:
        selected_engine = engine.strip().lower()
        if selected_engine in SUPPORTED_ENGINES:
            return selected_engine

        supported_engines = ", ".join(SUPPORTED_ENGINES)
        msg = f"Unsupported static-site engine {engine!r}. Supported engines: {supported_engines}"
        raise ValueError(msg)

    async def _composed_source(self) -> dagger.Directory:
        await self.validate_content_mounts()
        source = self.source
        for content_source, source_path, target_path, _ in self._mounts():
            source = source.with_directory(target_path, content_source.directory(source_path))
        return source

    def _mounts(self) -> list[tuple[dagger.Directory, str, str, str]]:
        lengths = {
            len(self.content_sources),
            len(self.content_source_paths),
            len(self.content_target_paths),
            len(self.content_contributors),
        }
        if len(lengths) != 1:
            raise ValueError("content source, source path, target path, and contributor counts must match")

        mounts: list[tuple[dagger.Directory, str, str, str]] = []
        for source, raw_source_path, raw_target_path, raw_contributor in zip(
            self.content_sources,
            self.content_source_paths,
            self.content_target_paths,
            self.content_contributors,
            strict=True,
        ):
            source_path = self._clean_path(raw_source_path)
            target_path = self._clean_path(raw_target_path)
            contributor = raw_contributor.strip()
            if not source_path:
                raise ValueError("content source path is required")
            if not target_path:
                raise ValueError("content target path is required")
            if not contributor:
                raise ValueError("content contributor is required")
            mounts.append((source, source_path, target_path, contributor))
        return mounts

    def _clean_path(self, path: str) -> str:
        return path.strip().strip("/")

    async def _directory_files(self, directory: dagger.Directory, prefix: str = "") -> list[str]:
        files: list[str] = []
        for entry in await directory.entries():
            if entry.endswith("/"):
                child_prefix = f"{prefix}{entry}"
                child_files = await self._directory_files(
                    directory.directory(entry.rstrip("/")),
                    prefix=child_prefix,
                )
                files.extend(child_files)
            else:
                files.append(f"{prefix}{entry}")
        return files
