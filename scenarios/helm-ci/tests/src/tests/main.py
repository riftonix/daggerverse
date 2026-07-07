"""Dagger-native tests for the Helm CI scenario."""

from typing import Annotated
from unittest import TestCase

from dagger import Directory, Doc, dag, function, object_type

DEFAULT_HELM_IMAGE_REGISTRY = "docker.io"
DEFAULT_HELM_IMAGE_REPOSITORY = "alpine/helm"
DEFAULT_HELM_IMAGE_TAG = "3.18.6"
DEFAULT_HELM_CONTAINER_USER_ID = "65532"

DEFAULT_GIT_IMAGE_REGISTRY = "docker.io"
DEFAULT_GIT_IMAGE_REPOSITORY = "alpine/git"
DEFAULT_GIT_IMAGE_TAG = "2.52.0"
DEFAULT_GIT_CONTAINER_USER_ID = "65532"

FIXTURE_GIT_IMAGE_REGISTRY = "docker.io"
FIXTURE_GIT_IMAGE_REPOSITORY = "alpine/git"
FIXTURE_GIT_IMAGE_TAG = "2.52.0"


@object_type
class Tests:
    """Test module entrypoint for Helm CI scenario checks."""

    helm_image_registry: str
    helm_image_repository: str
    helm_image_tag: str
    helm_container_user_id: str

    git_image_registry: str
    git_image_repository: str
    git_image_tag: str
    git_container_user_id: str

    @classmethod
    async def create(
        cls,
        helm_image_registry: Annotated[
            str | None,
            Doc("Helm image registry override for offline or mirrored-registry runs"),
        ] = DEFAULT_HELM_IMAGE_REGISTRY,
        helm_image_repository: Annotated[
            str | None,
            Doc("Helm image repository override for offline or mirrored-registry runs"),
        ] = DEFAULT_HELM_IMAGE_REPOSITORY,
        helm_image_tag: Annotated[
            str | None,
            Doc("Helm image tag override for offline or mirrored-registry runs"),
        ] = DEFAULT_HELM_IMAGE_TAG,
        helm_container_user_id: Annotated[
            str | None,
            Doc("Helm container user id override for offline or mirrored-registry runs"),
        ] = DEFAULT_HELM_CONTAINER_USER_ID,
        git_image_registry: Annotated[
            str | None,
            Doc("Git image registry override for offline or mirrored-registry runs"),
        ] = DEFAULT_GIT_IMAGE_REGISTRY,
        git_image_repository: Annotated[
            str | None,
            Doc("Git image repository override for offline or mirrored-registry runs"),
        ] = DEFAULT_GIT_IMAGE_REPOSITORY,
        git_image_tag: Annotated[
            str | None,
            Doc("Git image tag override for offline or mirrored-registry runs"),
        ] = DEFAULT_GIT_IMAGE_TAG,
        git_container_user_id: Annotated[
            str | None,
            Doc("Git container user id override for offline or mirrored-registry runs"),
        ] = DEFAULT_GIT_CONTAINER_USER_ID,
    ):
        """Constructor exposing optional Helm and Git runtime image overrides for offline runs."""
        return cls(
            helm_image_registry=helm_image_registry or DEFAULT_HELM_IMAGE_REGISTRY,
            helm_image_repository=helm_image_repository or DEFAULT_HELM_IMAGE_REPOSITORY,
            helm_image_tag=helm_image_tag or DEFAULT_HELM_IMAGE_TAG,
            helm_container_user_id=helm_container_user_id or DEFAULT_HELM_CONTAINER_USER_ID,
            git_image_registry=git_image_registry or DEFAULT_GIT_IMAGE_REGISTRY,
            git_image_repository=git_image_repository or DEFAULT_GIT_IMAGE_REPOSITORY,
            git_image_tag=git_image_tag or DEFAULT_GIT_IMAGE_TAG,
            git_container_user_id=git_container_user_id or DEFAULT_GIT_CONTAINER_USER_ID,
        )

    def _helm_image_inputs(self) -> dict[str, str]:
        """Return the configured Helm runtime image inputs as keyword arguments."""
        return {
            "helm_image_registry": self.helm_image_registry,
            "helm_image_repository": self.helm_image_repository,
            "helm_image_tag": self.helm_image_tag,
            "helm_container_user_id": self.helm_container_user_id,
        }

    def _git_image_inputs(self) -> dict[str, str]:
        """Return the configured Git runtime image inputs as keyword arguments."""
        return {
            "git_image_registry": self.git_image_registry,
            "git_image_repository": self.git_image_repository,
            "git_image_tag": self.git_image_tag,
            "git_container_user_id": self.git_container_user_id,
        }

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "helm-ci-tests"

    @function
    async def all(self) -> None:
        """Run all Helm CI scenario tests."""
        await self.helm_verify_changed_charts_uses_merge_base()

    @function
    async def helm_verify_changed_charts_uses_merge_base(self) -> None:
        """Verify only feature-branch chart changes, not base-branch drift."""
        helm_ci = dag.helm_ci(**self._helm_image_inputs(), **self._git_image_inputs())
        outputs = await helm_ci.helm_verify_changed_charts(
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
            .from_(f"{FIXTURE_GIT_IMAGE_REGISTRY}/{FIXTURE_GIT_IMAGE_REPOSITORY}:{FIXTURE_GIT_IMAGE_TAG}")
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
