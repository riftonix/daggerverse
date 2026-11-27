"""Dagger-native tests for the Helm CI scenario."""

from typing import Annotated, Self
from unittest import TestCase

from dagger import Directory, Doc, QueryError, dag, function, object_type

from .sync_charts import SyncChartsTests

FIXTURE_GIT_IMAGE_REGISTRY = "docker.io"
FIXTURE_GIT_IMAGE_REPOSITORY = "alpine/git"
# renovate: datasource=docker depName=alpine/git
FIXTURE_GIT_IMAGE_TAG = "v2.54.1"


@object_type
class Tests:
    """Test module entrypoint for Helm CI scenario checks."""

    helm_image_registry: str | None
    helm_image_repository: str | None
    helm_image_tag: str | None
    helm_container_user_id: str | None
    helm_unittest_image_registry: str | None
    helm_unittest_image_repository: str | None
    helm_unittest_image_tag: str | None
    helm_unittest_container_user_id: str | None
    git_image_registry: str | None
    git_image_repository: str | None
    git_image_tag: str | None
    git_container_user_id: str | None

    @classmethod
    async def create(
        cls,
        helm_image_registry: Annotated[str | None, Doc("Helm image registry override")] = None,
        helm_image_repository: Annotated[str | None, Doc("Helm image repository override")] = None,
        helm_image_tag: Annotated[str | None, Doc("Helm image tag override")] = None,
        helm_container_user_id: Annotated[str | None, Doc("Helm container user ID override")] = None,
        helm_unittest_image_registry: Annotated[str | None, Doc("Helm unittest image registry override")] = None,
        helm_unittest_image_repository: Annotated[str | None, Doc("Helm unittest image repository override")] = None,
        helm_unittest_image_tag: Annotated[str | None, Doc("Helm unittest image tag override")] = None,
        helm_unittest_container_user_id: Annotated[str | None, Doc("Helm unittest container user ID override")] = None,
        git_image_registry: Annotated[str | None, Doc("Git image registry override")] = None,
        git_image_repository: Annotated[str | None, Doc("Git image repository override")] = None,
        git_image_tag: Annotated[str | None, Doc("Git image tag override")] = None,
        git_container_user_id: Annotated[str | None, Doc("Git container user ID override")] = None,
    ) -> Self:
        """Allow verification and publication to use mirrored images and custom UIDs."""
        return cls(
            helm_image_registry=helm_image_registry,
            helm_image_repository=helm_image_repository,
            helm_image_tag=helm_image_tag,
            helm_container_user_id=helm_container_user_id,
            helm_unittest_image_registry=helm_unittest_image_registry,
            helm_unittest_image_repository=helm_unittest_image_repository,
            helm_unittest_image_tag=helm_unittest_image_tag,
            helm_unittest_container_user_id=helm_unittest_container_user_id,
            git_image_registry=git_image_registry,
            git_image_repository=git_image_repository,
            git_image_tag=git_image_tag,
            git_container_user_id=git_container_user_id,
        )

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "helm-ci-tests"

    @function
    async def all(self) -> None:
        """Run all Helm CI scenario tests."""
        await self.verify_chart()
        await self.verify_chart_uses_chart_source_override()
        await self.verify_chart_rejects_invalid_chart_source_override()
        await self.verify_library_chart()
        await self.verify_chart_rejects_non_chart_directory()
        await self.custom_suite_patterns_replace_defaults()
        await self.empty_suite_patterns_skip_unittest()
        await self.selected_failing_suite_fails()
        await self.publish_chart_requires_git_tag_prefix()
        await self.publish_chart_uses_chart_source_override()
        await self.gets_chart_release_tag()
        await self.gets_chart_release_tag_with_version_override()
        await self.normalizes_chart_release_tag_prefix()
        await self.publish_chart_requires_registry_credentials_together()
        await self.publish_chart_skips_existing_release_tag()
        await self.gets_oci_registry_host()
        await self.gets_oci_registry_host_with_port()
        await self.sync_charts().all()

    @function
    def sync_charts(self) -> SyncChartsTests:
        """Return the chart sync tests."""
        return SyncChartsTests()

    @function
    async def verify_chart(self) -> None:
        """Verify the scenario source, including both default suite extensions."""
        chart = self._chart_with_passing_suite("tests/units/config_test.yaml").with_new_file(
            "tests/units/second_test.yml", self._passing_suite("second default suite")
        )
        output = await self._helm_ci(chart).verify_chart()

        test = TestCase()
        test.assertIn("lint:", output)
        test.assertIn("template:", output)
        test.assertIn("unittest:\n", output)
        test.assertIn("tests/units/config_test.yaml", output)
        test.assertIn("tests/units/second_test.yml", output)

    @function
    async def verify_chart_uses_chart_source_override(self) -> None:
        """Use the explicit chart source and ignore unrelated YAML under tests/."""
        helm_ci = self._helm_ci(self._non_chart_directory())
        chart = self._fixture_chart().with_new_file("tests/e2e/kind.yaml", "kind: Cluster\n")
        output = await helm_ci.verify_chart(chart_source=chart)

        test_case = TestCase()
        test_case.assertIn("lint:", output)
        test_case.assertIn("template:", output)
        test_case.assertIn("unittest: skipped (no suite files matched configured patterns)", output)

    @function
    async def verify_chart_rejects_invalid_chart_source_override(self) -> None:
        """Verify an invalid override is not replaced by a valid scenario source."""
        helm_ci = self._helm_ci(self._fixture_chart())
        with TestCase().assertRaisesRegex(Exception, "not a Helm chart"):
            await helm_ci.verify_chart(chart_source=self._non_chart_directory())

    @function
    async def verify_library_chart(self) -> None:
        """Verify a library chart skips templating."""
        helm_ci = self._helm_ci(self._fixture_library_chart())
        output = await helm_ci.verify_chart()

        TestCase().assertIn("template: skipped (library chart)", output)

    @function
    async def verify_chart_rejects_non_chart_directory(self) -> None:
        """Verify a directory without Chart.yaml is rejected."""
        helm_ci = self._helm_ci(self._non_chart_directory())
        try:
            await helm_ci.verify_chart()
        except Exception as error:
            TestCase().assertIn("not a Helm chart", str(error))
        else:
            raise AssertionError("Expected non-chart directory validation to fail")

    @function
    async def custom_suite_patterns_replace_defaults(self) -> None:
        """Forward multiple patterns and exclude a failing default suite."""
        chart = (
            self._chart_with_passing_suite("checks/yaml/config_test.yaml")
            .with_new_file("checks/yml/config_test.yml", self._passing_suite("second custom suite"))
            .with_new_file("tests/units/failing_test.yaml", self._failing_suite())
        )
        output = await self._helm_ci(chart).verify_chart(
            unittest_suite_files=["checks/yaml/*_test.yaml", "checks/yml/*_test.yml"]
        )

        test_case = TestCase()
        test_case.assertIn("checks/yaml/config_test.yaml", output)
        test_case.assertIn("checks/yml/config_test.yml", output)
        test_case.assertNotIn("tests/units/failing_test.yaml", output)

    @function
    async def empty_suite_patterns_skip_unittest(self) -> None:
        """Verify an explicit empty suite pattern list skips Helm unittest."""
        chart = self._chart_with_passing_suite("tests/units/config_test.yaml")
        output = await self._helm_ci(chart).verify_chart(unittest_suite_files=[])

        TestCase().assertIn("unittest: skipped (no suite files matched configured patterns)", output)

    @function
    async def selected_failing_suite_fails(self) -> None:
        """Verify failure from a selected suite propagates from verify-chart."""
        chart = self._fixture_chart().with_new_file("checks/failing_test.yaml", self._failing_suite())
        with TestCase().assertRaises(QueryError):
            await self._helm_ci(chart).verify_chart(unittest_suite_files=["checks/*_test.yaml"])

    @function
    async def publish_chart_requires_git_tag_prefix(self) -> None:
        """Verify the unified release entrypoint validates its tag prefix before publishing."""
        with TestCase().assertRaisesRegex(Exception, "git_tag_prefix: must not be empty"):
            await self._helm_ci(self._fixture_chart()).publish_chart(
                oci_url="registry.invalid/charts",
                git_tag_prefix="/",
                git_token=dag.set_secret("helm-ci-test-git-token", "unused"),
            )

    @function
    async def publish_chart_uses_chart_source_override(self) -> None:
        """Verify publish metadata is read from an explicit chart source override."""
        helm_ci = self._helm_ci(self._fixture_chart())
        with TestCase().assertRaises(Exception) as raised:
            await helm_ci.publish_chart(
                oci_url="registry.invalid/charts",
                git_tag_prefix="charts/missing",
                git_token=dag.set_secret("helm-ci-test-override-git-token", "unused"),
                chart_source=self._non_chart_directory(),
            )

        TestCase().assertIn("chart_source: not a Helm chart (missing Chart.yaml)", str(raised.exception))

    @function
    async def gets_chart_release_tag(self) -> None:
        """Verify release tag combines its prefix and Chart.yaml version."""
        tag = await self._helm_ci(self._fixture_chart()).get_chart_release_tag(git_tag_prefix="charts/ns-configurator")

        TestCase().assertEqual("charts/ns-configurator/v1.0.0", tag)

    @function
    async def gets_chart_release_tag_with_version_override(self) -> None:
        """Verify release tag uses the effective overridden package version."""
        tag = await self._helm_ci(self._fixture_chart()).get_chart_release_tag(
            git_tag_prefix="charts/ns-configurator",
            version="2.0.0",
        )

        TestCase().assertEqual("charts/ns-configurator/v2.0.0", tag)

    @function
    async def normalizes_chart_release_tag_prefix(self) -> None:
        """Verify release tag strips surrounding separators from its prefix."""
        tag = await self._helm_ci(self._fixture_chart()).get_chart_release_tag(
            git_tag_prefix="/charts/ns-configurator/"
        )

        TestCase().assertEqual("charts/ns-configurator/v1.0.0", tag)

    @function
    async def publish_chart_requires_registry_credentials_together(self) -> None:
        """Verify registry authentication inputs are supplied as a pair."""
        helm_ci = self._helm_ci(self._fixture_chart())
        with TestCase().assertRaisesRegex(
            Exception,
            "registry_login and registry_password must be supplied together",
        ):
            await helm_ci.publish_chart(
                oci_url="registry.invalid/charts",
                git_tag_prefix="charts/ns-configurator",
                git_token=dag.set_secret("helm-ci-paired-auth-git-token", "unused"),
                registry_login="registry-user",
                with_dependency_update=False,
            )

    @function
    async def publish_chart_skips_existing_release_tag(self) -> None:
        """Use distinct Helm and Git UIDs while checking an existing local-remote release tag."""
        repository = self._repository_with_release_tag()
        helm_ci = self._helm_ci(repository, helm_container_user_id="12345", git_container_user_id="12346")
        output = await helm_ci.publish_chart(
            oci_url="registry.invalid/charts",
            git_tag_prefix="charts/ns-configurator",
            chart_source=self._fixture_chart(),
            with_dependency_update=False,
        )

        test_case = TestCase()
        test_case.assertIn("skipped: release tag already exists", output)
        test_case.assertIn("release tag: charts/ns-configurator/v1.0.0", output)

    @function
    async def gets_oci_registry_host(self) -> None:
        """Verify registry authentication uses the host from the OCI URL."""
        registry_host = await self._helm_ci(self._fixture_chart()).get_oci_registry_host(
            oci_url="oci://ghcr.io/riftonix/libs/"
        )

        TestCase().assertEqual("ghcr.io", registry_host)

    @function
    async def gets_oci_registry_host_with_port(self) -> None:
        """Verify registry host extraction preserves an explicit port."""
        registry_host = await self._helm_ci(self._fixture_chart()).get_oci_registry_host(
            oci_url="registry.example.com:5000/team/charts"
        )

        TestCase().assertEqual("registry.example.com:5000", registry_host)

    def _helm_ci(
        self,
        source: Directory,
        *,
        helm_container_user_id: str | None = None,
        git_container_user_id: str | None = None,
    ):
        return dag.helm_ci(
            source=source,
            helm_image_registry=self.helm_image_registry,
            helm_image_repository=self.helm_image_repository,
            helm_image_tag=self.helm_image_tag,
            helm_container_user_id=self.helm_container_user_id or helm_container_user_id,
            helm_unittest_image_registry=self.helm_unittest_image_registry,
            helm_unittest_image_repository=self.helm_unittest_image_repository,
            helm_unittest_image_tag=self.helm_unittest_image_tag,
            helm_unittest_container_user_id=self.helm_unittest_container_user_id,
            git_image_registry=self.git_image_registry,
            git_image_repository=self.git_image_repository,
            git_image_tag=self.git_image_tag,
            git_container_user_id=self.git_container_user_id or git_container_user_id,
        )

    def _non_chart_directory(self) -> Directory:
        """Return a directory without Chart.yaml."""
        return dag.directory().with_new_file("README.md", "not a chart")

    def _fixture_chart(self) -> Directory:
        """Return the fixture chart directory."""
        return dag.current_module().source().directory("charts/ns-configurator")

    def _repository_with_release_tag(self) -> Directory:
        """Return a Git repository whose bare origin contains the chart release tag."""
        registry = self.git_image_registry or FIXTURE_GIT_IMAGE_REGISTRY
        repository = self.git_image_repository or FIXTURE_GIT_IMAGE_REPOSITORY
        tag = self.git_image_tag or FIXTURE_GIT_IMAGE_TAG
        return (
            dag.container()
            .from_(f"{registry}/{repository}:{tag}")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(["sh", "-c", "printf 'release\n' > README.md && git add README.md && git commit -m release"])
            .with_exec(["git", "tag", "charts/ns-configurator/v1.0.0"])
            .with_exec(["mkdir", "-p", ".remote"])
            .with_exec(["git", "clone", "--bare", ".", ".remote/origin.git"])
            .with_exec(["git", "tag", "-d", "charts/ns-configurator/v1.0.0"])
            .with_exec(["git", "remote", "add", "origin", ".remote/origin.git"])
            .directory("/work/repo")
        )

    def _fixture_library_chart(self) -> Directory:
        """Return a copy of the fixture chart with library type metadata."""
        return (
            dag.current_module()
            .source()
            .directory("charts/ns-configurator")
            .with_new_file(
                "Chart.yaml",
                "apiVersion: v2\nname: ns-configurator\nversion: 0.1.0\ntype: library\n",
            )
        )

    def _chart_with_passing_suite(self, path: str) -> Directory:
        """Return a fixture chart with a passing suite at the requested path."""
        return self._fixture_chart().with_new_file(path, self._passing_suite("selected suite"))

    def _passing_suite(self, name: str) -> str:
        """Return a passing Helm unittest suite."""
        return (
            f"suite: {name}\n"
            "templates:\n"
            "  - templates/limit-range.yaml\n"
            "tests:\n"
            "  - it: renders the configured limit range\n"
            "    asserts:\n"
            "      - equal:\n"
            "          path: metadata.name\n"
            "          value: limit-range\n"
        )

    def _failing_suite(self) -> str:
        """Return a failing Helm unittest suite."""
        return (
            "suite: selected failure\n"
            "templates:\n"
            "  - templates/limit-range.yaml\n"
            "tests:\n"
            "  - it: propagates a selected failure\n"
            "    asserts:\n"
            "      - equal:\n"
            "          path: metadata.name\n"
            "          value: unexpected-name\n"
        )
