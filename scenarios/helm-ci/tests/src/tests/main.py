"""Dagger-native tests for the Helm CI scenario."""

from unittest import TestCase

from dagger import Directory, dag, function, object_type

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
        await self.verify_charts_discovers_changed_chart_components()

    @function
    async def verify_charts_discovers_changed_chart_components(self) -> None:
        """Verify changed chart components from caller-provided root patterns."""
        helm_ci = dag.helm_ci()
        outputs = await helm_ci.verify_charts(
            source=self._repo_with_pull_request_chart_changes(),
            base_ref="main",
            head_ref="feature",
            charts_path=["charts/*", "libs/*"],
        )

        output = "\n".join(outputs)
        test_case = TestCase()
        test_case.assertEqual(2, len(outputs))
        test_case.assertIn("charts/changed:", output)
        test_case.assertIn("libs/common:", output)
        test_case.assertNotIn("charts/base-only:", output)

    def _repo_with_pull_request_chart_changes(self) -> Directory:
        """Return a repo where main and feature both changed charts after the merge base."""
        return (
            dag.container()
            .from_(f"{FIXTURE_GIT_IMAGE_REGISTRY}/{FIXTURE_GIT_IMAGE_REPOSITORY}:{FIXTURE_GIT_IMAGE_TAG}")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_directory("/work/repo/charts/changed", self._fixture_chart())
            .with_directory("/work/repo/charts/base-only", self._fixture_chart())
            .with_directory("/work/repo/libs/common", self._fixture_chart())
            .with_exec(["git", "add", "."])
            .with_exec(["git", "commit", "-m", "base"])
            .with_exec(["git", "checkout", "-b", "feature"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    "printf '\nfeature: true\n' >> charts/changed/values.yaml && "
                    "printf '\nfeature: true\n' >> libs/common/values.yaml && "
                    "git add . && git commit -m feature",
                ]
            )
            .with_exec(["git", "checkout", "main"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    "printf '\nbaseOnly: true\n' >> charts/base-only/values.yaml && git add . && git commit -m main",
                ]
            )
            .directory("/work/repo")
        )

    def _fixture_chart(self) -> Directory:
        """Return the fixture chart directory."""
        return dag.current_module().source().directory("charts/ns-configurator")
