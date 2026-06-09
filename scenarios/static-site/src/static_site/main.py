from typing import Annotated

import dagger
import yaml
from dagger import DefaultPath, Doc, dag, function, object_type

DEFAULT_ENGINE = "hugo"
SUPPORTED_ENGINES = (DEFAULT_ENGINE,)


@object_type
class StaticSite:
    """Static-site scenario entrypoint."""

    source: dagger.Directory
    hugo_theme_url: str | None

    @classmethod
    async def create(
        cls,
        source: Annotated[
            dagger.Directory,
            DefaultPath("."),
            Doc("Static site source directory"),
        ],
        hugo_theme_url: Annotated[
            str | None,
            Doc("Hugo theme module URL, required when engine is hugo"),
        ] = None,
    ):
        """Constructor."""
        return cls(source=source, hugo_theme_url=hugo_theme_url)

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
            return await dag.hugo(source=self.source).validate(
                hugo_theme_url=self._required_hugo_theme_url(),
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
            return await dag.hugo(source=self.source).build(
                hugo_theme_url=self._required_hugo_theme_url(),
                site_base_url=site_base_url,
            )

        msg = f"Static-site engine dispatch is incomplete for {selected_engine!r}"
        raise RuntimeError(msg)

    @function
    async def validate_hugo_mounts(
        self,
        config: Annotated[
            dagger.File,
            Doc("Hugo YAML config file containing module imports and mounts"),
        ],
        modules: Annotated[
            list[dagger.Directory],
            Doc("Imported module roots in the same order as module.imports in the config"),
        ],
    ) -> str:
        """Validate that Hugo imports do not overwrite shared virtual paths."""
        collisions = await self.get_hugo_mount_collisions(
            config=config,
            modules=modules,
        )
        if collisions:
            msg = "Hugo virtual path collision: " + "; ".join(collisions)
            raise ValueError(msg)

        return "validated Hugo mount paths"

    @function
    async def get_hugo_mount_collisions(
        self,
        config: Annotated[
            dagger.File,
            Doc("Hugo YAML config file containing module imports and mounts"),
        ],
        modules: Annotated[
            list[dagger.Directory],
            Doc("Imported module roots in the same order as module.imports in the config"),
        ],
    ) -> list[str]:
        """Return Hugo virtual mount path collisions without failing."""
        imports = await self._hugo_imports(config)
        if len(imports) != len(modules):
            msg = "modules length must match module.imports length in the Hugo config"
            raise ValueError(msg)

        contributors_by_virtual_path: dict[str, list[str]] = {}

        for module_index, module in enumerate(modules):
            module_path = str(imports[module_index].get("path") or f"module {module_index + 1}")
            for mount in imports[module_index].get("mounts") or []:
                source_path = self._clean_path(str(mount.get("source") or ""))
                target_path = self._clean_path(str(mount.get("target") or ""))
                if not source_path or not target_path:
                    continue
                for relative_path in await self._directory_files(module.directory(source_path)):
                    virtual_path = f"{target_path}/{relative_path}"
                    contributor = f"{module_path}:{source_path}->{target_path}"
                    contributors_by_virtual_path.setdefault(virtual_path, []).append(contributor)

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

    def _required_hugo_theme_url(self) -> str:
        if self.hugo_theme_url and self.hugo_theme_url.strip():
            return self.hugo_theme_url

        msg = "hugo_theme_url is required when engine is hugo"
        raise ValueError(msg)

    async def _hugo_imports(self, config: dagger.File) -> list[dict]:
        config_data = yaml.safe_load(await config.contents()) or {}
        if not isinstance(config_data, dict):
            msg = "Hugo config must be a YAML mapping"
            raise ValueError(msg)
        module_config = config_data.get("module") or {}
        if not isinstance(module_config, dict):
            msg = "Hugo config module section must be a mapping"
            raise ValueError(msg)
        imports = module_config.get("imports") or []
        if not isinstance(imports, list):
            msg = "Hugo config module.imports section must be a list"
            raise ValueError(msg)
        return [import_config for import_config in imports if isinstance(import_config, dict)]

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
