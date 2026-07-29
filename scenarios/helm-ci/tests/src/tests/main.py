"""Dagger-native tests for the Helm CI scenario."""

from unittest import TestCase

from dagger import Directory, QueryError, dag, function, object_type

FIXTURE_GIT_IMAGE_REGISTRY = "docker.io"
FIXTURE_GIT_IMAGE_REPOSITORY = "alpine/git"
# renovate: datasource=docker depName=alpine/git
FIXTURE_GIT_IMAGE_TAG = "v2.54.0"


@object_type
class Tests:
    """Test module entrypoint for Helm CI scenario checks."""

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
        await self.unrelated_yaml_skips_unittest()
        await self.default_yaml_suite_runs()
        await self.default_yml_suite_runs()
        await self.custom_suite_patterns_replace_defaults()
        await self.multiple_custom_suite_patterns_run()
        await self.empty_suite_patterns_skip_unittest()
        await self.unmatched_suite_patterns_skip_unittest()
        await self.selected_failing_suite_fails()
        await self.publish_chart_requires_git_tag_prefix()
        await self.publish_chart_uses_chart_source_override()
        await self.release_chart_uses_chart_yaml_version()
        await self.release_chart_accepts_version_override()
        await self.gets_chart_release_tag()
        await self.gets_chart_release_tag_with_version_override()
        await self.normalizes_chart_release_tag_prefix()
        await self.publish_chart_requires_registry_credentials_together()
        await self.publish_chart_skips_existing_release_tag()
        await self.gets_chart_oci_url()
        await self.gets_library_oci_url()
        await self.gets_nested_library_oci_url()

    @function
    async def verify_chart(self) -> None:
        """Verify chart source falls back to the scenario source."""
        helm_ci = dag.helm_ci(source=self._fixture_chart())
        output = await helm_ci.verify_chart()

        TestCase().assertIn("lint:", output)
        TestCase().assertIn("template:", output)

    @function
    async def verify_chart_uses_chart_source_override(self) -> None:
        """Verify an explicit chart source overrides the repository source."""
        helm_ci = dag.helm_ci(source=self._non_chart_directory())
        output = await helm_ci.verify_chart(chart_source=self._fixture_chart())

        test_case = TestCase()
        test_case.assertIn("lint:", output)
        test_case.assertIn("template:", output)

    @function
    async def verify_chart_rejects_invalid_chart_source_override(self) -> None:
        """Verify an invalid override is not replaced by a valid scenario source."""
        helm_ci = dag.helm_ci(source=self._fixture_chart())
        with TestCase().assertRaisesRegex(Exception, "not a Helm chart"):
            await helm_ci.verify_chart(chart_source=self._non_chart_directory())

    @function
    async def verify_library_chart(self) -> None:
        """Verify a library chart skips templating."""
        helm_ci = dag.helm_ci(source=self._fixture_library_chart())
        output = await helm_ci.verify_chart()

        TestCase().assertIn("template: skipped (library chart)", output)

    @function
    async def verify_chart_rejects_non_chart_directory(self) -> None:
        """Verify a directory without Chart.yaml is rejected."""
        helm_ci = dag.helm_ci(source=self._non_chart_directory())
        try:
            await helm_ci.verify_chart()
        except Exception as error:
            TestCase().assertIn("not a Helm chart", str(error))
        else:
            raise AssertionError("Expected non-chart directory validation to fail")

    @function
    async def unrelated_yaml_skips_unittest(self) -> None:
        """Verify unrelated YAML under tests does not enable Helm unittest."""
        chart = self._fixture_chart().with_new_file("tests/e2e/kind.yaml", "kind: Cluster\n")
        output = await dag.helm_ci(source=chart).verify_chart()

        TestCase().assertIn("unittest: skipped (no suite files matched configured patterns)", output)

    @function
    async def default_yaml_suite_runs(self) -> None:
        """Verify the default YAML suite pattern enables Helm unittest."""
        output = await dag.helm_ci(source=self._chart_with_passing_suite("tests/units/config_test.yaml")).verify_chart()

        TestCase().assertIn("unittest:\n", output)
        TestCase().assertIn("PASS", output)

    @function
    async def default_yml_suite_runs(self) -> None:
        """Verify the default YML suite pattern enables Helm unittest."""
        output = await dag.helm_ci(source=self._chart_with_passing_suite("tests/units/config_test.yml")).verify_chart()

        TestCase().assertIn("unittest:\n", output)
        TestCase().assertIn("PASS", output)

    @function
    async def custom_suite_patterns_replace_defaults(self) -> None:
        """Verify custom suite patterns replace defaults and exclude a default suite."""
        chart = self._chart_with_passing_suite("checks/selected_test.yaml").with_new_file(
            "tests/units/failing_test.yaml",
            self._failing_suite(),
        )
        output = await dag.helm_ci(source=chart).verify_chart(unittest_suite_files=["checks/*_test.yaml"])

        TestCase().assertIn("PASS", output)

    @function
    async def multiple_custom_suite_patterns_run(self) -> None:
        """Verify multiple custom suite patterns select suites."""
        chart = self._chart_with_passing_suite("checks/yaml/config_test.yaml").with_new_file(
            "checks/yml/config_test.yml",
            self._passing_suite("second custom suite"),
        )
        output = await dag.helm_ci(source=chart).verify_chart(
            unittest_suite_files=["checks/yaml/*_test.yaml", "checks/yml/*_test.yml"]
        )

        test_case = TestCase()
        test_case.assertIn("checks/yaml/config_test.yaml", output)
        test_case.assertIn("checks/yml/config_test.yml", output)

    @function
    async def empty_suite_patterns_skip_unittest(self) -> None:
        """Verify an explicit empty suite pattern list skips Helm unittest."""
        chart = self._chart_with_passing_suite("tests/units/config_test.yaml")
        output = await dag.helm_ci(source=chart).verify_chart(unittest_suite_files=[])

        TestCase().assertIn("unittest: skipped (no suite files matched configured patterns)", output)

    @function
    async def unmatched_suite_patterns_skip_unittest(self) -> None:
        """Verify unmatched custom suite patterns skip Helm unittest."""
        chart = self._chart_with_passing_suite("tests/units/config_test.yaml")
        output = await dag.helm_ci(source=chart).verify_chart(unittest_suite_files=["checks/*_test.yaml"])

        TestCase().assertIn("unittest: skipped (no suite files matched configured patterns)", output)

    @function
    async def selected_failing_suite_fails(self) -> None:
        """Verify failure from a selected suite propagates from verify-chart."""
        chart = self._fixture_chart().with_new_file("checks/failing_test.yaml", self._failing_suite())
        with TestCase().assertRaises(QueryError):
            await dag.helm_ci(source=chart).verify_chart(unittest_suite_files=["checks/*_test.yaml"])

    @function
    async def publish_chart_requires_git_tag_prefix(self) -> None:
        """Verify the unified release entrypoint validates its tag prefix before publishing."""
        with TestCase().assertRaisesRegex(Exception, "git_tag_prefix: must not be empty"):
            await dag.helm_ci(source=self._fixture_chart()).publish_chart(
                oci_base_url="registry.invalid",
                git_tag_prefix="/",
                git_token=dag.set_secret("helm-ci-test-git-token", "unused"),
            )

    @function
    async def publish_chart_uses_chart_source_override(self) -> None:
        """Verify publish metadata is read from an explicit chart source override."""
        helm_ci = dag.helm_ci(source=self._fixture_chart())
        with TestCase().assertRaises(Exception) as raised:
            await helm_ci.publish_chart(
                oci_base_url="registry.invalid",
                git_tag_prefix="charts/missing",
                git_token=dag.set_secret("helm-ci-test-override-git-token", "unused"),
                chart_source=self._non_chart_directory(),
            )

        TestCase().assertIn("chart_source: not a Helm chart (missing Chart.yaml)", str(raised.exception))

    @function
    async def release_chart_uses_chart_yaml_version(self) -> None:
        """Verify release publication resolves the version declared in Chart.yaml."""
        tag = await dag.helm_ci(source=self._fixture_chart()).get_chart_release_tag(
            git_tag_prefix="charts/ns-configurator"
        )

        TestCase().assertEqual("charts/ns-configurator/v1.0.0", tag)

    @function
    async def release_chart_accepts_version_override(self) -> None:
        """Verify release publication accepts an explicit version override."""
        tag = await dag.helm_ci(source=self._fixture_chart()).get_chart_release_tag(
            git_tag_prefix="charts/ns-configurator",
            version="2.0.0",
        )

        TestCase().assertEqual("charts/ns-configurator/v2.0.0", tag)

    @function
    async def gets_chart_release_tag(self) -> None:
        """Verify release tag combines its prefix and Chart.yaml version."""
        tag = await dag.helm_ci(source=self._fixture_chart()).get_chart_release_tag(
            git_tag_prefix="charts/ns-configurator"
        )

        TestCase().assertEqual("charts/ns-configurator/v1.0.0", tag)

    @function
    async def gets_chart_release_tag_with_version_override(self) -> None:
        """Verify release tag uses the effective overridden package version."""
        tag = await dag.helm_ci(source=self._fixture_chart()).get_chart_release_tag(
            git_tag_prefix="charts/ns-configurator",
            version="2.0.0",
        )

        TestCase().assertEqual("charts/ns-configurator/v2.0.0", tag)

    @function
    async def normalizes_chart_release_tag_prefix(self) -> None:
        """Verify release tag strips surrounding separators from its prefix."""
        tag = await dag.helm_ci(source=self._fixture_chart()).get_chart_release_tag(
            git_tag_prefix="/charts/ns-configurator/"
        )

        TestCase().assertEqual("charts/ns-configurator/v1.0.0", tag)

    @function
    async def publish_chart_requires_registry_credentials_together(self) -> None:
        """Verify registry authentication inputs are supplied as a pair."""
        helm_ci = dag.helm_ci(source=self._fixture_chart())
        with TestCase().assertRaisesRegex(Exception, "username and password must be supplied together"):
            await helm_ci.publish_chart(
                oci_base_url="registry.invalid",
                git_tag_prefix="charts/ns-configurator",
                git_token=dag.set_secret("helm-ci-paired-auth-git-token", "unused"),
                username="registry-user",
                with_dependency_update=False,
            )

    @function
    async def publish_chart_skips_existing_release_tag(self) -> None:
        """Verify an existing remote release tag skips publication before registry access."""
        repository = self._repository_with_release_tag()
        output = await dag.helm_ci(source=repository).publish_chart(
            oci_base_url="registry.invalid",
            git_tag_prefix="charts/ns-configurator",
            chart_source=self._fixture_chart(),
            with_dependency_update=False,
        )

        test_case = TestCase()
        test_case.assertIn("skipped: release tag already exists", output)
        test_case.assertIn("release tag: charts/ns-configurator/v1.0.0", output)

    @function
    async def gets_chart_oci_url(self) -> None:
        """Verify chart prefixes are preserved as OCI repository paths."""
        oci_url = await dag.helm_ci(source=self._fixture_chart()).get_chart_oci_url(
            oci_base_url="ghcr.io/riftonix/",
            git_tag_prefix="charts/appchart",
        )

        TestCase().assertEqual("ghcr.io/riftonix/charts", oci_url)

    @function
    async def gets_library_oci_url(self) -> None:
        """Verify library prefixes are preserved as OCI repository paths."""
        oci_url = await dag.helm_ci(source=self._fixture_chart()).get_chart_oci_url(
            oci_base_url="oci://ghcr.io/riftonix",
            git_tag_prefix="libs/common",
        )

        TestCase().assertEqual("ghcr.io/riftonix/libs", oci_url)

    @function
    async def gets_nested_library_oci_url(self) -> None:
        """Verify nested library prefixes retain every path segment."""
        oci_url = await dag.helm_ci(source=self._fixture_chart()).get_chart_oci_url(
            oci_base_url="ghcr.io/riftonix",
            git_tag_prefix="/libs/test/common/",
        )

        TestCase().assertEqual("ghcr.io/riftonix/libs/test", oci_url)

    @function
    async def gets_nested_library_oci_url_with_chart_name(self) -> None:
        """Verify only the final chart name is removed from a nested prefix."""
        oci_url = await dag.helm_ci(source=self._fixture_chart()).get_chart_oci_url(
            oci_base_url="ghcr.io/riftonix",
            git_tag_prefix="libs/test/common-lib",
        )

        TestCase().assertEqual("ghcr.io/riftonix/libs/test", oci_url)

    @function
    async def gets_oci_registry_host(self) -> None:
        """Verify registry authentication uses the host from the OCI URL."""
        registry_host = await dag.helm_ci(source=self._fixture_chart()).get_oci_registry_host(
            oci_base_url="oci://ghcr.io/riftonix/"
        )

        TestCase().assertEqual("ghcr.io", registry_host)

    def _non_chart_directory(self) -> Directory:
        """Return a directory without Chart.yaml."""
        return (
            dag.container()
            .from_(f"{FIXTURE_GIT_IMAGE_REGISTRY}/{FIXTURE_GIT_IMAGE_REPOSITORY}:{FIXTURE_GIT_IMAGE_TAG}")
            .with_new_file("/work/chart/README.md", "not a chart")
            .directory("/work/chart")
        )

    def _fixture_chart(self) -> Directory:
        """Return the fixture chart directory."""
        return dag.current_module().source().directory("charts/ns-configurator")

    def _repository_with_release_tag(self) -> Directory:
        """Return a Git repository whose bare origin contains the chart release tag."""
        return (
            dag.container()
            .from_(f"{FIXTURE_GIT_IMAGE_REGISTRY}/{FIXTURE_GIT_IMAGE_REPOSITORY}:{FIXTURE_GIT_IMAGE_TAG}")
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
