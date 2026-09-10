"""Dagger-native tests for the Hugo module."""

from unittest import TestCase

from dagger import Directory, ExecError, dag, function, object_type

FIXTURE_SITE_PATH = "site"
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
        await self.installs_lockfile_dependencies()
        await self.missing_package_json_fails()
        await self.missing_package_lock_fails()
        await self.fixture_has_no_go_metadata()
        await self.configures_npm_registry()

    @function
    async def build_docsy_fixture(self) -> None:
        """Build the npm-based Docsy fixture using the prepared Hugo image."""
        public_dir = await self._hugo(self._fixture_site()).build(site_base_url=SITE_BASE_URL)
        TestCase().assertIn("index.html", await public_dir.entries())

    @function
    async def rendered_output_exists(self) -> None:
        """Build output is a rendered directory for the caller-provided base URL."""
        public_dir = await self._hugo(self._fixture_site()).build(site_base_url=SITE_BASE_URL)
        index_html = await public_dir.file("index.html").contents()
        TestCase().assertGreater(len(index_html), 0)
        TestCase().assertIn(f"data-site-base-url={SITE_BASE_URL}", index_html)

    @function
    async def validate_docsy_fixture(self) -> None:
        """Validate the npm-based Docsy fixture with strict Hugo checks."""
        output = await self._hugo(self._fixture_site()).validate(site_base_url=SITE_BASE_URL)
        TestCase().assertIn("Pages", output)

    @function
    async def installs_lockfile_dependencies(self) -> None:
        """Install dependencies from package-lock.json with scripts disabled."""
        container = self._hugo(self._site_with_local_npm_dependency()).with_npm_dependencies()
        installed = await container.file("node_modules/local-fixture/package.json").contents()
        TestCase().assertIn('"name":"local-fixture"', installed)

    @function
    async def missing_package_json_fails(self) -> None:
        """Reject a Hugo site without package.json."""
        await self._assert_dependency_error(
            dag.directory().with_new_file("package-lock.json", '{"lockfileVersion":3,"packages":{}}\n'),
            "package.json is required",
        )

    @function
    async def missing_package_lock_fails(self) -> None:
        """Reject a Hugo site without package-lock.json."""
        await self._assert_dependency_error(
            dag.directory().with_new_file("package.json", '{"name":"missing-lock","private":true}\n'),
            "package-lock.json is required",
        )

    @function
    async def fixture_has_no_go_metadata(self) -> None:
        """Keep the npm-based site fixture independent of Go modules."""
        entries = await self._fixture_site().entries()
        test_case = TestCase()
        test_case.assertNotIn("go.mod", entries)
        test_case.assertNotIn("go.sum", entries)

    @function
    async def configures_npm_registry(self) -> None:
        """Configure an optional npm registry or proxy URL."""
        registry = "https://npm.example.test/"
        value = (
            await dag.hugo(source=self._fixture_site(), npm_registry=registry)
            .container()
            .with_exec(["sh", "-c", 'printf %s "$NPM_CONFIG_REGISTRY"'])
            .stdout()
        )
        TestCase().assertEqual(registry, value)

    async def _assert_dependency_error(self, source: Directory, expected: str) -> None:
        test_case = TestCase()
        try:
            await self._hugo(source).with_npm_dependencies().stdout()
        except ExecError as exc:
            test_case.assertIn(expected, exc.stderr)
        else:
            test_case.fail(f"expected dependency preparation to fail with {expected!r}")

    def _hugo(self, source: Directory):
        return dag.hugo(source=source)

    def _fixture_site(self) -> Directory:
        return dag.current_module().source().directory(FIXTURE_SITE_PATH)

    def _site_with_local_npm_dependency(self) -> Directory:
        return (
            dag.directory()
            .with_new_file(
                "package.json",
                '{"name":"npm-site","private":true,"dependencies":{"local-fixture":"file:vendor/local-fixture"}}\n',
            )
            .with_new_file(
                "package-lock.json",
                '{"name":"npm-site","lockfileVersion":3,"requires":true,"packages":{"":{"name":"npm-site",'
                '"dependencies":{"local-fixture":"file:vendor/local-fixture"}},'
                '"node_modules/local-fixture":{"resolved":"vendor/local-fixture","link":true},'
                '"vendor/local-fixture":{"name":"local-fixture","version":"1.0.0"}}}\n',
            )
            .with_new_file("vendor/local-fixture/package.json", '{"name":"local-fixture","version":"1.0.0"}\n')
        )
