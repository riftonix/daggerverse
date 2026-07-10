from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type

DEFAULT_IMAGE_REGISTRY = "ghcr.io"
DEFAULT_IMAGE_REPOSITORY = "riftonix/container-images/hugo-autoprefixer"
# renovate: datasource=docker depName=ghcr.io/riftonix/container-images/hugo-autoprefixer
DEFAULT_IMAGE_TAG = "0.154.5-10.5.0"
DEFAULT_CONTAINER_USER_ID = "65532"


@object_type
class Hugo:
    source: dagger.Directory
    image_registry: str
    image_repository: str
    image_tag: str
    user_id: str
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
    ):
        """Constructor"""
        return cls(
            source=source,
            image_registry=image_registry,
            image_repository=image_repository,
            image_tag=image_tag,
            user_id=user_id,
            container_=None,
        )

    @function
    def container(self) -> dagger.Container:
        """Creates container with configured Hugo"""
        if self.container_:
            return self.container_
        self.container_ = (
            dag.container()
            .from_(address=f"{self.image_registry}/{self.image_repository}:{self.image_tag}")
            .with_user(self.user_id)
            .with_env_variable("NODE_PATH", "/usr/local/lib/node_modules")
            .with_env_variable("NPM_CONFIG_CACHE", "/tmp/npm-cache")
            .with_env_variable("NPM_CONFIG_USERCONFIG", "/tmp/.npmrc")
            .with_exec(["mkdir", "-p", "-m", "770", "/tmp/hugo/site"])
            .with_directory("/tmp/hugo/site", self.source, owner=self.user_id)
            .with_workdir("/tmp/hugo/site")
            .with_exposed_port(1313)
        )
        return self.container_

    @function
    async def build(
        self,
        hugo_theme_url: Annotated[str, Doc("Hugo theme module URL")],  # github.com/google/docsy@v0.13.0
        site_base_url: Annotated[str, Doc("Site base URL for Hugo")],  # example.com
    ) -> dagger.Directory:
        """Build Hugo site and return the public directory"""
        container = (
            self.container()
            .with_env_variable("SITE_THEME_URL", hugo_theme_url)
            .with_env_variable("SITE_BASE_URL", site_base_url)
            .with_exec(["hugo", "version"])
            .with_exec(["hugo", "mod", "get", "$SITE_THEME_URL"], expand=True)
            .with_exec(
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
        )
        public_dir = container.directory("public")
        return public_dir

    @function
    async def init_module(
        self,
        module_path: Annotated[str, Doc("Go module path for the Hugo module")],
    ) -> dagger.Directory:
        """Initialize Hugo module metadata without rendering a static site."""
        container = (
            self.container()
            .with_env_variable("HUGO_MODULE_PATH", module_path)
            .with_exec(["hugo", "version"])
            .with_exec(["hugo", "mod", "init", "$HUGO_MODULE_PATH"], expand=True)
        )
        return container.directory(".")

    @function
    async def prepare_module(
        self,
        hugo_module_url: Annotated[
            str | None,
            Doc("Optional Hugo module URL to resolve, for example github.com/google/docsy@v0.13.0"),
        ] = None,
    ) -> dagger.Directory:
        """Resolve Hugo module dependencies without rendering a static site."""
        container = self.container().with_exec(["hugo", "version"])
        if hugo_module_url:
            container = container.with_env_variable("HUGO_MODULE_URL", hugo_module_url).with_exec(
                ["hugo", "mod", "get", "$HUGO_MODULE_URL"], expand=True
            )
        container = container.with_exec(["hugo", "mod", "tidy"])
        return container.directory(".")

    @function
    async def validate(
        self,
        hugo_theme_url: Annotated[str, Doc("Hugo theme module URL")],  # github.com/google/docsy@v0.13.0
        site_base_url: Annotated[str, Doc("Site base URL for Hugo")],  # example.com
    ) -> str:
        """Validate Hugo site configuration and strict rendering."""
        container = (
            self.container()
            .with_env_variable("SITE_THEME_URL", hugo_theme_url)
            .with_env_variable("SITE_BASE_URL", site_base_url)
            .with_exec(["hugo", "version"])
            .with_exec(["hugo", "mod", "get", "$SITE_THEME_URL"], expand=True)
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
