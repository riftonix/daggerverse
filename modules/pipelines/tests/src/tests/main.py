"""Dagger-native tests for the transitional Pipelines module."""

from unittest import TestCase

from dagger import Directory, dag, function, object_type


@object_type
class Tests:
    """Test module entrypoint for transitional pipeline checks."""

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "pipelines-tests"

    @function
    async def all(self) -> None:
        """Run all Pipelines module tests."""
        await self.helm_verify_changed_charts_uses_merge_base()

    @function
    async def helm_verify_changed_charts_uses_merge_base(self) -> None:
        """Verify only feature-branch chart changes, not base-branch drift."""
        outputs = await dag.pipelines().helm_verify_changed_charts(
            source=self._repo_with_pull_request_chart_changes(),
            target_branch="main",
            charts_path="charts",
        )

        output = "\n".join(outputs)
        test_case = TestCase()
        test_case.assertEqual(1, len(outputs))
        test_case.assertIn("charts/changed:", output)
        test_case.assertNotIn("charts/base-only:", output)

    def _repo_with_pull_request_chart_changes(self) -> Directory:
        """Return a repo where main and feature both changed charts after the merge base."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_directory("/work/repo/charts/changed", self._fixture_chart())
            .with_directory("/work/repo/charts/base-only", self._fixture_chart())
            .with_exec(["git", "add", "."])
            .with_exec(["git", "commit", "-m", "base"])
            .with_exec(["git", "checkout", "-b", "feature"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    "printf '\\nfeature: true\\n' >> charts/changed/values.yaml && git add . && git commit -m feature",
                ]
            )
            .with_exec(["git", "checkout", "main"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    "printf '\\nbaseOnly: true\\n' >> charts/base-only/values.yaml && git add . && git commit -m main",
                ]
            )
            .with_exec(["git", "checkout", "feature"])
            .directory("/work/repo")
        )

    def _fixture_chart(self) -> Directory:
        """Return the fixture chart directory."""
        return dag.current_module().source().directory("charts/ns-configurator")
