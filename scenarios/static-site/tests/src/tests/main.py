"""Dagger-native tests for the static-site scenario."""

from unittest import TestCase

from dagger import Directory, dag, function, object_type

FIXTURE_SITE_PATH = "site"
SITE_BASE_URL = "https://example.com/"


@object_type
class Tests:
    """Test module entrypoint for static-site scenario checks."""

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "static-site-tests"

    @function
    async def all(self) -> None:
        """Run all static-site scenario tests."""
        await self.verify_docsy_fixture()
        await self.unsupported_engine_fails_clearly()
        await self.rendered_output_exists()
        await self.main_site_renders_imported_component_modules()
        await self.unique_hugo_mount_paths_pass()
        await self.duplicate_hugo_mount_paths_are_reported()

    @function
    async def verify_docsy_fixture(self) -> None:
        """Verify the Docsy fixture through the provider-neutral scenario API."""
        validation_output = await dag.static_site().verify_site(
            site=self._fixture_site(),
            site_base_url=SITE_BASE_URL,
            engine="hugo",
        )

        TestCase().assertIn("Pages", validation_output)

    @function
    async def rendered_output_exists(self) -> None:
        """Render the Docsy fixture through the provider-neutral scenario API."""
        public_dir = await dag.static_site().render_site(
            site=self._fixture_site(),
            site_base_url=SITE_BASE_URL,
            engine="hugo",
        )

        index_html = await public_dir.file("index.html").contents()
        TestCase().assertGreater(len(index_html), 0)

    @function
    async def main_site_renders_imported_component_modules(self) -> None:
        """Render a main site that imports component docs and OpenSpec modules."""
        source = self._main_site_with_component_modules()
        await dag.hugo(source=source.directory("daggerverse-docs")).prepare_module()
        await dag.hugo(source=source.directory("container-images-docs")).prepare_module()
        await dag.hugo(source=source.directory("daggerverse-openspec")).prepare_module()
        await dag.hugo(source=source.directory("container-images-openspec")).prepare_module()

        public_dir = await dag.static_site().render_site(
            site=source,
            site_base_url=SITE_BASE_URL,
            engine="hugo",
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

    @function
    async def unique_hugo_mount_paths_pass(self) -> None:
        """Accept Hugo imports whose mounts produce unique virtual paths."""
        source = self._main_site_with_component_modules()
        result = await dag.static_site().validate_hugo_mounts(
            config=source.file("hugo.yml"),
            modules=[
                source.directory("daggerverse-docs"),
                source.directory("container-images-docs"),
                source.directory("daggerverse-openspec"),
                source.directory("container-images-openspec"),
            ],
        )

        TestCase().assertEqual("validated Hugo mount paths", result)

    @function
    async def duplicate_hugo_mount_paths_are_reported(self) -> None:
        """Report duplicate virtual paths for arbitrary Hugo module mounts."""
        source = self._site_with_duplicate_hugo_mounts()
        collisions = await dag.static_site().get_hugo_mount_collisions(
            config=source.file("hugo.yml"),
            modules=[
                source.directory("first-module"),
                source.directory("second-module"),
            ],
        )

        message = "\n".join(collisions)
        test_case = TestCase()
        test_case.assertIn("content/docs/shared/page.md", message)
        test_case.assertIn("example.com/first-module:content->content/docs/shared", message)
        test_case.assertIn("example.com/second-module:docs->content/docs/shared", message)

    @function
    async def unsupported_engine_fails_clearly(self) -> None:
        """Reject unsupported engines before invoking an engine module."""
        test_case = TestCase()
        try:
            await dag.static_site().verify_site(
                site=dag.directory(),
                site_base_url="https://example.com/",
                engine="zola",
            )
        except BaseException as exc:
            message = str(exc)
            test_case.assertIn("Unsupported static-site engine", message)
            test_case.assertIn("zola", message)
            test_case.assertIn("hugo", message)
        else:
            test_case.fail("expected unsupported engine to fail")

    def _fixture_site(self) -> Directory:
        """Return the fixture Hugo site directory."""
        return dag.current_module().source().directory(FIXTURE_SITE_PATH)

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

    def _site_with_duplicate_hugo_mounts(self) -> Directory:
        """Return a Hugo config and modules with duplicate virtual mount paths."""
        return (
            dag.directory()
            .with_new_file(
                "hugo.yml",
                "module:\n"
                "  imports:\n"
                "    - path: example.com/first-module\n"
                "      mounts:\n"
                "        - source: content\n"
                "          target: content/docs/shared\n"
                "    - path: example.com/second-module\n"
                "      mounts:\n"
                "        - source: docs\n"
                "          target: content/docs/shared\n",
            )
            .with_new_file(
                "first-module/content/page.md",
                "---\ntitle: First\n---\n\nFirst module page.\n",
            )
            .with_new_file(
                "second-module/docs/page.md",
                "---\ntitle: Second\n---\n\nSecond module page.\n",
            )
        )
