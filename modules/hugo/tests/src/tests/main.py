"""Dagger-native tests for the Hugo module."""

from unittest import TestCase

from dagger import Directory, dag, function, object_type

FIXTURE_SITE_PATH = "site"
DOCSY_THEME_URL = "github.com/google/docsy@v0.13.0"
SITE_BASE_URL = "https://example.com/"


@object_type
class Tests:
    """Test module entrypoint for Hugo checks."""

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

    @function
    async def build_docsy_fixture(self) -> None:
        """Build the Docsy fixture using the prepared Hugo image."""
        public_dir = await dag.hugo(source=self._fixture_site()).build(
            hugo_theme_url=DOCSY_THEME_URL,
            site_base_url=SITE_BASE_URL,
        )

        entries = await public_dir.entries()
        TestCase().assertIn("index.html", entries)

    @function
    async def rendered_output_exists(self) -> None:
        """Build output is a rendered directory for the caller-provided base URL."""
        public_dir = await dag.hugo(source=self._fixture_site()).build(
            hugo_theme_url=DOCSY_THEME_URL,
            site_base_url=SITE_BASE_URL,
        )

        index_html = await public_dir.file("index.html").contents()
        TestCase().assertGreater(len(index_html), 0)
        TestCase().assertIn(f"data-site-base-url={SITE_BASE_URL}", index_html)

    @function
    async def validate_docsy_fixture(self) -> None:
        """Validate the Docsy fixture with strict Hugo checks."""
        validation_output = await dag.hugo(source=self._fixture_site()).validate(
            hugo_theme_url=DOCSY_THEME_URL,
            site_base_url=SITE_BASE_URL,
        )

        TestCase().assertIn("Pages", validation_output)

    @function
    async def module_can_be_initialized(self) -> None:
        """Initialize Hugo module metadata without rendering a site."""
        prepared_dir = await dag.hugo(source=self._uninitialized_module()).init_module(
            module_path="example.com/docs",
        )

        test_case = TestCase()
        test_case.assertIn("module example.com/docs", await prepared_dir.file("go.mod").contents())
        test_case.assertNotIn("public", await prepared_dir.entries())

    @function
    async def module_imports_can_be_resolved(self) -> None:
        """Resolve Hugo module dependencies without rendering a site."""
        prepared_dir = await dag.hugo(source=self._module_with_import()).prepare_module(
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
        public_dir = await dag.hugo(source=source).build(
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
        docs_dir = await dag.hugo(source=self._docs_module_root()).prepare_module()
        openspec_dir = await dag.hugo(source=self._openspec_module_root()).prepare_module()

        test_case = TestCase()
        test_case.assertIn("module example.com/component-docs", await docs_dir.file("go.mod").contents())
        test_case.assertIn("guide.md", await docs_dir.directory("content").entries())
        test_case.assertNotIn("public", await docs_dir.entries())
        test_case.assertIn("module example.com/component-openspec", await openspec_dir.file("go.mod").contents())
        test_case.assertIn("sample-spec/", await openspec_dir.directory("specs").entries())
        test_case.assertIn("sample-change/", await openspec_dir.directory("changes/archive").entries())
        test_case.assertNotIn("public", await openspec_dir.entries())

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
