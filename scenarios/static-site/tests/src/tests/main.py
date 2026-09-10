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
        await self.unique_content_mount_paths_pass()
        await self.duplicate_content_mount_paths_are_reported()
        await self.composed_content_is_rendered()
        await self.fixture_has_no_go_metadata()

    @function
    async def verify_docsy_fixture(self) -> None:
        """Verify the npm-based Docsy fixture through the scenario API."""
        output = await dag.static_site(source=self._fixture_site()).verify_site(
            site_base_url=SITE_BASE_URL,
            engine="hugo",
        )
        TestCase().assertIn("Pages", output)

    @function
    async def rendered_output_exists(self) -> None:
        """Render the npm-based Docsy fixture through the scenario API."""
        public_dir = await dag.static_site(source=self._fixture_site()).render_site(
            site_base_url=SITE_BASE_URL,
            engine="hugo",
        )
        TestCase().assertGreater(len(await public_dir.file("index.html").contents()), 0)

    @function
    async def unique_content_mount_paths_pass(self) -> None:
        """Accept mounts whose target files are unique."""
        source = self._component_sources()
        result = await dag.static_site(
            content_sources=[source.directory("first"), source.directory("second")],
            content_source_paths=["content", "content"],
            content_target_paths=["content/docs/first", "content/docs/second"],
            content_contributors=["first", "second"],
        ).validate_content_mounts()
        TestCase().assertEqual("validated content mount paths", result)

    @function
    async def duplicate_content_mount_paths_are_reported(self) -> None:
        """Report duplicate target files and their contributors."""
        source = self._component_sources()
        collisions = await dag.static_site(
            content_sources=[source.directory("first"), source.directory("second")],
            content_source_paths=["content", "content"],
            content_target_paths=["content/docs/shared", "content/docs/shared"],
            content_contributors=["first", "second"],
        ).get_content_mount_collisions()
        message = "\n".join(collisions)
        test_case = TestCase()
        test_case.assertIn("content/docs/shared/page.md", message)
        test_case.assertIn("first:content->content/docs/shared", message)
        test_case.assertIn("second:content->content/docs/shared", message)

    @function
    async def composed_content_is_rendered(self) -> None:
        """Render external content under the caller-selected target path."""
        source = self._component_sources()
        public_dir = await dag.static_site(
            source=self._fixture_site(),
            content_sources=[source.directory("first")],
            content_source_paths=["content"],
            content_target_paths=["content/docs/components/first"],
            content_contributors=["first"],
        ).render_site(site_base_url=SITE_BASE_URL, engine="hugo")
        page = await public_dir.file("docs/components/first/page/index.html").contents()
        TestCase().assertIn("First component page", page)

    @function
    async def fixture_has_no_go_metadata(self) -> None:
        """Keep the site fixture independent of Go modules."""
        entries = await self._fixture_site().entries()
        test_case = TestCase()
        test_case.assertNotIn("go.mod", entries)
        test_case.assertNotIn("go.sum", entries)

    @function
    async def unsupported_engine_fails_clearly(self) -> None:
        """Reject unsupported engines before invoking an engine module."""
        test_case = TestCase()
        try:
            await dag.static_site(source=dag.directory()).verify_site(
                site_base_url=SITE_BASE_URL,
                engine="zola",
            )
        except BaseException as exc:
            message = str(exc)
            test_case.assertIn("Unsupported static-site engine", message)
            test_case.assertIn("zola", message)
        else:
            test_case.fail("expected unsupported engine to fail")

    def _fixture_site(self) -> Directory:
        return dag.current_module().source().directory(FIXTURE_SITE_PATH)

    def _component_sources(self) -> Directory:
        return (
            dag.directory()
            .with_new_file(
                "first/content/page.md",
                "---\ntitle: First\n---\n\nFirst component page.\n",
            )
            .with_new_file(
                "second/content/page.md",
                "---\ntitle: Second\n---\n\nSecond component page.\n",
            )
        )
