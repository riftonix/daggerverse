from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type

DEFAULT_IMAGE_REGISTRY = "ghcr.io"
DEFAULT_IMAGE_REPOSITORY = "riftonix/container-images/hugo-autoprefixer"
# renovate: datasource=docker depName=ghcr.io/riftonix/container-images/hugo-autoprefixer versioning=loose
DEFAULT_IMAGE_TAG = "0.165.0-10.6.0"
DEFAULT_CONTAINER_USER_ID = "65532"


def npm_ci_command() -> list[str]:
    """Return the reproducible npm install command for a site lockfile."""
    return ["npm", "ci", "--ignore-scripts"]


def normalize_npm_registry(registry: str | None) -> str | None:
    """Normalize an optional npm registry URL."""
    normalized = registry.strip() if registry else ""
    return normalized or None


@object_type
class Hugo:
    source: dagger.Directory
    image_registry: str
    image_repository: str
    image_tag: str
    user_id: str
    npm_registry: str | None
    container_: dagger.Container | None

    @classmethod
    async def create(
        cls,
        source: Annotated[
            dagger.Directory,
            DefaultPath("."),
            Doc("Hugo site directory"),
        ],
        image_registry: Annotated[str | None, Doc("Hugo image registry")] = DEFAULT_IMAGE_REGISTRY,
        image_repository: Annotated[str | None, Doc("Hugo image repository")] = DEFAULT_IMAGE_REPOSITORY,
        image_tag: Annotated[str | None, Doc("Hugo image tag")] = DEFAULT_IMAGE_TAG,
        user_id: Annotated[str | None, Doc("Hugo image user")] = DEFAULT_CONTAINER_USER_ID,
        npm_registry: Annotated[str | None, Doc("Optional npm registry or proxy URL")] = None,
    ):
        """Constructor"""
        return cls(
            source=source,
            image_registry=image_registry,
            image_repository=image_repository,
            image_tag=image_tag,
            user_id=user_id,
            npm_registry=normalize_npm_registry(npm_registry),
            container_=None,
        )

    @function
    def container(self) -> dagger.Container:
        """Creates container with configured Hugo"""
        if self.container_:
            return self.container_
        container = (
            dag.container()
            .from_(address=f"{self.image_registry}/{self.image_repository}:{self.image_tag}")
            .with_user(self.user_id)
            .with_env_variable("NODE_PATH", "/usr/local/lib/node_modules")
            .with_env_variable("NPM_CONFIG_CACHE", "/tmp/npm-cache")
            .with_env_variable("NPM_CONFIG_USERCONFIG", "/tmp/.npmrc")
            .with_mounted_cache("/tmp/npm-cache", dag.cache_volume("hugo-npm-cache"), owner=self.user_id)
            .with_exec(["mkdir", "-p", "-m", "770", "/tmp/hugo/site"])
            .with_directory("/tmp/hugo/site", self.source, owner=self.user_id)
            .with_workdir("/tmp/hugo/site")
            .with_exposed_port(1313)
        )
        if self.npm_registry:
            container = container.with_env_variable("NPM_CONFIG_REGISTRY", self.npm_registry)
        self.container_ = container
        return self.container_

    def _with_npm_dependencies(self, container: dagger.Container) -> dagger.Container:
        """Install the site's lockfile-pinned npm dependencies."""
        command = npm_ci_command()
        return container.with_exec(
            [
                "sh",
                "-c",
                "test -f package.json || { echo 'package.json is required for npm-based Hugo sites' >&2; exit 1; }; "
                "test -f package-lock.json || { echo 'package-lock.json is required for npm-based Hugo sites' >&2; exit 1; }; "
                f"{' '.join(command)}",
            ],
        )

    @function
    def with_npm_dependencies(self) -> dagger.Container:
        """Return the runtime after optional lockfile-pinned npm installation."""
        return self._with_npm_dependencies(self.container())

    @function
    async def build(
        self,
        site_base_url: Annotated[str, Doc("Site base URL for Hugo")],  # example.com
    ) -> dagger.Directory:
        """Build Hugo site and return the public directory"""
        container = self._with_npm_dependencies(
            self.container().with_env_variable("SITE_BASE_URL", site_base_url).with_exec(["hugo", "version"])
        ).with_exec(
            [
                "hugo",
                "--minify",
                "--destination",
                "public",
                "--baseURL",
                "$SITE_BASE_URL",
                "--forceSyncStatic",
                "--cleanDestinationDir",
            ],
            expand=True,
        )
        public_dir = container.directory("public")
        return public_dir

    @function
    async def validate(
        self,
        site_base_url: Annotated[str, Doc("Site base URL for Hugo")],  # example.com
    ) -> str:
        """Validate Hugo site configuration and strict rendering."""
        container = (
            self._with_npm_dependencies(
                self.container().with_env_variable("SITE_BASE_URL", site_base_url).with_exec(["hugo", "version"])
            )
            .with_exec(["hugo", "config", "--format", "yaml"])
            .with_exec(
                [
                    "hugo",
                    "--minify",
                    "--destination",
                    "validation-public",
                    "--baseURL",
                    "$SITE_BASE_URL",
                    "--forceSyncStatic",
                    "--cleanDestinationDir",
                    "--panicOnWarning",
                    "--printPathWarnings",
                    "--printI18nWarnings",
                ],
                expand=True,
            )
        )
        return await container.stdout()
