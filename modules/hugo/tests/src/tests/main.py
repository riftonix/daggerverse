"""Dagger-native tests for the Hugo module."""

from typing import Annotated, Self
from unittest import TestCase

from dagger import Directory, Doc, ExecError, dag, function, object_type

FIXTURE_SITE_PATH = "site"
SITE_BASE_URL = "https://example.com/"


@object_type
class Tests:
    """Test module entrypoint for Hugo checks."""

    image_registry: str | None
    image_repository: str | None
    image_tag: str | None
    container_user_id: str | None
    npm_registry: str | None

    @classmethod
    async def create(
        cls,
        image_registry: Annotated[str | None, Doc("Hugo image registry override")] = None,
        image_repository: Annotated[str | None, Doc("Hugo image repository override")] = None,
        image_tag: Annotated[str | None, Doc("Hugo image tag override")] = None,
        container_user_id: Annotated[str | None, Doc("Hugo container user ID override")] = None,
        npm_registry: Annotated[str | None, Doc("Optional npm registry or proxy URL")] = None,
    ) -> Self:
        """Accept mirrored Hugo runtime settings without duplicating its defaults."""
        return cls(
            image_registry=image_registry,
            image_repository=image_repository,
            image_tag=image_tag,
            container_user_id=container_user_id,
            npm_registry=npm_registry,
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
        container_user_id = self.container_user_id or "12345"
        hugo = self._hugo(self._site_with_local_npm_dependency(), container_user_id=container_user_id)
        container = hugo.with_npm_dependencies()
        installed = await container.file("node_modules/local-fixture/package.json").contents()
        test_case = TestCase()
        test_case.assertIn('"name":"local-fixture"', installed)
        test_case.assertEqual(container_user_id, await container.user())

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
            await self._hugo(self._fixture_site(), npm_registry=registry)
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

    def _hugo(self, source: Directory, *, container_user_id: str | None = None, npm_registry: str | None = None):
        return dag.hugo(
            source=source,
            image_registry=self.image_registry,
            image_repository=self.image_repository,
            image_tag=self.image_tag,
            container_user_id=container_user_id or self.container_user_id,
            npm_registry=npm_registry or self.npm_registry,
        )

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
