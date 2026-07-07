"""Dagger-native tests for the Hugo module."""

from typing import Annotated
from unittest import TestCase

from dagger import Directory, Doc, dag, function, object_type

FIXTURE_SITE_PATH = "site"
DOCSY_THEME_URL = "github.com/google/docsy@v0.13.0"
SITE_BASE_URL = "https://example.com/"

DEFAULT_HUGO_IMAGE_REGISTRY = "ghcr.io"
DEFAULT_HUGO_IMAGE_REPOSITORY = "riftonix/container-images/hugo-autoprefixer"
DEFAULT_HUGO_IMAGE_TAG = "0.154.5-10.5.0"
DEFAULT_HUGO_CONTAINER_USER_ID = "65532"


@object_type
class Tests:
    """Test module entrypoint for Hugo checks."""

    hugo_image_registry: str
    hugo_image_repository: str
    hugo_image_tag: str
    hugo_container_user_id: str

    @classmethod
    async def create(
        cls,
        hugo_image_registry: Annotated[
            str | None,
            Doc("Hugo image registry override for offline or mirrored-registry runs"),
        ] = DEFAULT_HUGO_IMAGE_REGISTRY,
        hugo_image_repository: Annotated[
            str | None,
            Doc("Hugo image repository override for offline or mirrored-registry runs"),
        ] = DEFAULT_HUGO_IMAGE_REPOSITORY,
        hugo_image_tag: Annotated[
            str | None,
            Doc("Hugo image tag override for offline or mirrored-registry runs"),
        ] = DEFAULT_HUGO_IMAGE_TAG,
        hugo_container_user_id: Annotated[
            str | None,
            Doc("Hugo container user id override for offline or mirrored-registry runs"),
        ] = DEFAULT_HUGO_CONTAINER_USER_ID,
    ):
        """Constructor exposing optional Hugo runtime image overrides for offline runs."""
        return cls(
            hugo_image_registry=hugo_image_registry or DEFAULT_HUGO_IMAGE_REGISTRY,
            hugo_image_repository=hugo_image_repository or DEFAULT_HUGO_IMAGE_REPOSITORY,
            hugo_image_tag=hugo_image_tag or DEFAULT_HUGO_IMAGE_TAG,
            hugo_container_user_id=hugo_container_user_id or DEFAULT_HUGO_CONTAINER_USER_ID,
        )

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "hugo-tests"

    @function
    async def all(self) -> None:
        """Run all Hugo module tests."""
        await self.build_docsy_fixture()
        await self.rendered_output_exists()
        await self.validate_docsy_fixture()
        await self.module_can_be_initialized()
        await self.module_imports_can_be_resolved()
        await self.content_module_mount_target_is_chosen_by_importing_site()
        await self.independent_docs_and_openspec_roots_can_be_prepared()
        await self.main_site_renders_imported_component_modules()

    @function
    async def build_docsy_fixture(self) -> None:
        """Build the Docsy fixture using the prepared Hugo image."""
        public_dir = await self._hugo(source=self._fixture_site()).build(
            hugo_theme_url=DOCSY_THEME_URL,
            site_base_url=SITE_BASE_URL,
        )

        entries = await public_dir.entries()
        TestCase().assertIn("index.html", entries)

    @function
    async def rendered_output_exists(self) -> None:
        """Build output is a rendered directory for the caller-provided base URL."""
        public_dir = await self._hugo(source=self._fixture_site()).build(
            hugo_theme_url=DOCSY_THEME_URL,
            site_base_url=SITE_BASE_URL,
        )

        index_html = await public_dir.file("index.html").contents()
        TestCase().assertGreater(len(index_html), 0)
        TestCase().assertIn(f"data-site-base-url={SITE_BASE_URL}", index_html)

    @function
    async def validate_docsy_fixture(self) -> None:
        """Validate the Docsy fixture with strict Hugo checks."""
        validation_output = await self._hugo(source=self._fixture_site()).validate(
            hugo_theme_url=DOCSY_THEME_URL,
            site_base_url=SITE_BASE_URL,
        )

        TestCase().assertIn("Pages", validation_output)

    @function
    async def module_can_be_initialized(self) -> None:
        """Initialize Hugo module metadata without rendering a site."""
        prepared_dir = await self._hugo(source=self._uninitialized_module()).init_module(
            module_path="example.com/docs",
        )

        test_case = TestCase()
        test_case.assertIn("module example.com/docs", await prepared_dir.file("go.mod").contents())
        test_case.assertNotIn("public", await prepared_dir.entries())

    @function
    async def module_imports_can_be_resolved(self) -> None:
        """Resolve Hugo module dependencies without rendering a site."""
        prepared_dir = await self._hugo(source=self._module_with_import()).prepare_module(
            hugo_module_url=DOCSY_THEME_URL,
        )

        go_mod = await prepared_dir.file("go.mod").contents()
        test_case = TestCase()
        test_case.assertIn("github.com/google/docsy v0.13.0", go_mod)
        test_case.assertNotIn("public", await prepared_dir.entries())

    @function
    async def content_module_mount_target_is_chosen_by_importing_site(self) -> None:
        """Importing site chooses where path-neutral module content is mounted."""
        source = self._site_with_path_neutral_content_module()
        content_entries = await source.directory("component-docs/content").entries()
        public_dir = await self._hugo(source=source).build(
            hugo_theme_url=DOCSY_THEME_URL,
            site_base_url=SITE_BASE_URL,
        )

        rendered_page = await public_dir.file(
            "docs/components/daggerverse/how-to/path-neutral/index.html",
        ).contents()
        test_case = TestCase()
        test_case.assertIn("how-to/", content_entries)
        test_case.assertIn("Path-neutral component documentation", rendered_page)

    @function
    async def independent_docs_and_openspec_roots_can_be_prepared(self) -> None:
        """Prepare docs and OpenSpec module roots without requiring a main site."""
        docs_dir = await self._hugo(source=self._docs_module_root()).prepare_module()
        openspec_dir = await self._hugo(source=self._openspec_module_root()).prepare_module()

        test_case = TestCase()
        test_case.assertIn("module example.com/component-docs", await docs_dir.file("go.mod").contents())
        test_case.assertIn("guide.md", await docs_dir.directory("content").entries())
        test_case.assertNotIn("public", await docs_dir.entries())
        test_case.assertIn("module example.com/component-openspec", await openspec_dir.file("go.mod").contents())
        test_case.assertIn("sample-spec/", await openspec_dir.directory("specs").entries())
        test_case.assertIn("sample-change/", await openspec_dir.directory("changes/archive").entries())
        test_case.assertNotIn("public", await openspec_dir.entries())

    @function
    async def main_site_renders_imported_component_modules(self) -> None:
        """Render a main site that imports component docs and OpenSpec modules."""
        source = self._main_site_with_component_modules()
        await self._hugo(source=source.directory("daggerverse-docs")).prepare_module()
        await self._hugo(source=source.directory("container-images-docs")).prepare_module()
        await self._hugo(source=source.directory("daggerverse-openspec")).prepare_module()
        await self._hugo(source=source.directory("container-images-openspec")).prepare_module()

        public_dir = await self._hugo(source=source).build(
            hugo_theme_url=DOCSY_THEME_URL,
            site_base_url=SITE_BASE_URL,
        )

        test_case = TestCase()
        test_case.assertIn(
            "Daggerverse component guide",
            await public_dir.file("docs/components/daggerverse/how-to/foo/index.html").contents(),
        )
        test_case.assertIn(
            "Container images component guide",
            await public_dir.file("docs/components/container-images/how-to/foo/index.html").contents(),
        )
        test_case.assertIn(
            "Daggerverse Git module spec",
            await public_dir.file("docs/specs/git-module/spec/index.html").contents(),
        )
        test_case.assertIn(
            "Container images scenario spec",
            await public_dir.file("docs/specs/container-images-scenario/spec/index.html").contents(),
        )
        test_case.assertIn(
            "Daggerverse archived change",
            await public_dir.file("docs/changes/archive/git-module-change/proposal/index.html").contents(),
        )
        test_case.assertIn(
            "Container images archived change",
            await public_dir.file(
                "docs/changes/archive/container-images-scenario-change/proposal/index.html",
            ).contents(),
        )

    def _hugo(self, source: Directory):
        """Return the tested Hugo module with configured runtime image inputs."""
        return dag.hugo(
            source=source,
            image_registry=self.hugo_image_registry,
            image_repository=self.hugo_image_repository,
            image_tag=self.hugo_image_tag,
            user_id=self.hugo_container_user_id,
        )

    def _fixture_site(self) -> Directory:
        """Return the fixture Hugo site directory."""
        return dag.current_module().source().directory(FIXTURE_SITE_PATH)

    def _uninitialized_module(self) -> Directory:
        """Return a minimal Hugo module source without go.mod."""
        return dag.directory().with_new_file(
            "content/_index.md",
            "---\ntitle: Docs\n---\n\nPath-neutral module content.\n",
        )

    def _module_with_import(self) -> Directory:
        """Return a minimal Hugo module source with a theme import."""
        return (
            dag.directory()
            .with_new_file("go.mod", "module example.com/docs\n")
            .with_new_file(
                "hugo.yml",
                "module:\n  imports:\n    - path: github.com/google/docsy\n",
            )
        )

    def _site_with_path_neutral_content_module(self) -> Directory:
        """Return a site importing standard content under a site-owned target."""
        return (
            dag.directory()
            .with_new_file(
                "go.mod",
                "module example.com/importing-site\n\n"
                "require example.com/component-docs v0.0.0\n\n"
                "replace example.com/component-docs => ./component-docs\n",
            )
            .with_new_file(
                "hugo.yml",
                "baseURL: ''\n"
                "title: Importing Site\n"
                "module:\n"
                "  imports:\n"
                "    - path: example.com/component-docs\n"
                "      mounts:\n"
                "        - source: content\n"
                "          target: content/docs/components/daggerverse\n",
            )
            .with_new_file(
                "layouts/_default/single.html",
                "<!doctype html><title>{{ .Title }}</title>{{ .Content }}",
            )
            .with_new_file(
                "component-docs/go.mod",
                "module example.com/component-docs\n",
            )
            .with_new_file(
                "component-docs/content/how-to/path-neutral.md",
                "---\ntitle: Path Neutral\n---\n\nPath-neutral component documentation.\n",
            )
        )

    def _docs_module_root(self) -> Directory:
        """Return an independent docs Hugo module root."""
        return (
            dag.directory()
            .with_new_file("go.mod", "module example.com/component-docs\n")
            .with_new_file("content/guide.md", "---\ntitle: Guide\n---\n\nComponent guide.\n")
        )

    def _openspec_module_root(self) -> Directory:
        """Return an independent OpenSpec Hugo module root."""
        return (
            dag.directory()
            .with_new_file("go.mod", "module example.com/component-openspec\n")
            .with_new_file("specs/sample-spec/spec.md", "# Sample Spec\n")
            .with_new_file("changes/archive/sample-change/proposal.md", "# Sample Change\n")
        )

    def _main_site_with_component_modules(self) -> Directory:
        """Return a main Hugo site importing component docs and OpenSpec modules."""
        return (
            dag.directory()
            .with_new_file(
                "go.mod",
                "module example.com/main-site\n\n"
                "require (\n"
                "\tgithub.com/riftonix/daggerverse/docs v0.0.0\n"
                "\tgithub.com/riftonix/container-images/docs v0.0.0\n"
                "\tgithub.com/riftonix/daggerverse/openspec v0.0.0\n"
                "\tgithub.com/riftonix/container-images/openspec v0.0.0\n"
                ")\n\n"
                "replace github.com/riftonix/daggerverse/docs => ./daggerverse-docs\n"
                "replace github.com/riftonix/container-images/docs => ./container-images-docs\n"
                "replace github.com/riftonix/daggerverse/openspec => ./daggerverse-openspec\n"
                "replace github.com/riftonix/container-images/openspec => ./container-images-openspec\n",
            )
            .with_new_file(
                "hugo.yml",
                "baseURL: ''\n"
                "title: Component Documentation\n"
                "module:\n"
                "  imports:\n"
                "    - path: github.com/riftonix/daggerverse/docs\n"
                "      mounts:\n"
                "        - source: content\n"
                "          target: content/docs/components/daggerverse\n"
                "    - path: github.com/riftonix/container-images/docs\n"
                "      mounts:\n"
                "        - source: content\n"
                "          target: content/docs/components/container-images\n"
                "    - path: github.com/riftonix/daggerverse/openspec\n"
                "      mounts:\n"
                "        - source: specs\n"
                "          target: content/docs/specs\n"
                "        - source: changes/archive\n"
                "          target: content/docs/changes/archive\n"
                "    - path: github.com/riftonix/container-images/openspec\n"
                "      mounts:\n"
                "        - source: specs\n"
                "          target: content/docs/specs\n"
                "        - source: changes/archive\n"
                "          target: content/docs/changes/archive\n",
            )
            .with_new_file(
                "layouts/_default/single.html",
                "<!doctype html><html><head><title>{{ .Title }}</title></head><body>{{ .Content }}</body></html>",
            )
            .with_new_file("daggerverse-docs/go.mod", "module github.com/riftonix/daggerverse/docs\n")
            .with_new_file(
                "daggerverse-docs/content/how-to/foo.md",
                "---\ntitle: Daggerverse Foo\n---\n\nDaggerverse component guide.\n",
            )
            .with_new_file(
                "container-images-docs/go.mod",
                "module github.com/riftonix/container-images/docs\n",
            )
            .with_new_file(
                "container-images-docs/content/how-to/foo.md",
                "---\ntitle: Container Images Foo\n---\n\nContainer images component guide.\n",
            )
            .with_new_file(
                "daggerverse-openspec/go.mod",
                "module github.com/riftonix/daggerverse/openspec\n",
            )
            .with_new_file(
                "daggerverse-openspec/specs/git-module/spec.md",
                "---\ntitle: Git Module Spec\n---\n\nDaggerverse Git module spec.\n",
            )
            .with_new_file(
                "daggerverse-openspec/changes/archive/git-module-change/proposal.md",
                "---\ntitle: Git Module Change\n---\n\nDaggerverse archived change.\n",
            )
            .with_new_file(
                "container-images-openspec/go.mod",
                "module github.com/riftonix/container-images/openspec\n",
            )
            .with_new_file(
                "container-images-openspec/specs/container-images-scenario/spec.md",
                "---\ntitle: Container Images Scenario Spec\n---\n\nContainer images scenario spec.\n",
            )
            .with_new_file(
                "container-images-openspec/changes/archive/container-images-scenario-change/proposal.md",
                "---\ntitle: Container Images Scenario Change\n---\n\nContainer images archived change.\n",
            )
        )
