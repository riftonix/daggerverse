from typing import Annotated

import dagger
import yaml
from dagger import DefaultPath, Doc, dag, function, object_type

DEFAULT_HELM_IMAGE_REGISTRY = "docker.io"
DEFAULT_HELM_IMAGE_REPOSITORY = "alpine/helm"
# renovate: datasource=docker depName=alpine/helm
DEFAULT_HELM_IMAGE_TAG = "3.21.3"
DEFAULT_HELM_CONTAINER_USER_ID = "65532"

DEFAULT_GIT_IMAGE_REGISTRY = "docker.io"
DEFAULT_GIT_IMAGE_REPOSITORY = "alpine/git"
# renovate: datasource=docker depName=alpine/git
DEFAULT_GIT_IMAGE_TAG = "v2.54.0"
DEFAULT_GIT_CONTAINER_USER_ID = "65532"


@object_type
class HelmCi:
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
        helm_image_registry: Annotated[str | None, Doc("Helm image registry")] = DEFAULT_HELM_IMAGE_REGISTRY,
        helm_image_repository: Annotated[str | None, Doc("Helm image repository")] = DEFAULT_HELM_IMAGE_REPOSITORY,
        helm_image_tag: Annotated[str | None, Doc("Helm image tag")] = DEFAULT_HELM_IMAGE_TAG,
        helm_container_user_id: Annotated[str | None, Doc("Helm container user")] = DEFAULT_HELM_CONTAINER_USER_ID,
        git_image_registry: Annotated[
            str | None, Doc("Git image registry for changed-chart detection")
        ] = DEFAULT_GIT_IMAGE_REGISTRY,
        git_image_repository: Annotated[
            str | None, Doc("Git image repository for changed-chart detection")
        ] = DEFAULT_GIT_IMAGE_REPOSITORY,
        git_image_tag: Annotated[str | None, Doc("Git image tag for changed-chart detection")] = DEFAULT_GIT_IMAGE_TAG,
        git_container_user_id: Annotated[
            str | None, Doc("Git container user for changed-chart detection")
        ] = DEFAULT_GIT_CONTAINER_USER_ID,
    ):
        """Constructor exposing Helm and Git runtime image inputs with prefixed names."""
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

    async def _get_changed_chart_paths(
        self,
        source: dagger.Directory,
        target_branch: str,
        diff_paths: list[str] | None,
    ) -> list[str]:
        git = dag.git(
            source=source,
            image_registry=self.git_image_registry,
            image_repository=self.git_image_repository,
            image_tag=self.git_image_tag,
            user_id=self.git_container_user_id,
        )
        changed_paths: list[str] = []
        for diff_path in diff_paths or []:
            changed_paths.extend(
                await git.get_changed_dirs_since_merge_base(
                    base_ref=target_branch,
                    paths=[diff_path],
                )
            )
        return sorted(set(changed_paths))

    def _helm(self, source: dagger.Directory):
        """Return configured Helm module instance from the helm module dependency."""
        return dag.helm(
            source=source,
            image_registry=self.helm_image_registry,
            image_repository=self.helm_image_repository,
            image_tag=self.helm_image_tag,
            container_user_id=self.helm_container_user_id,
        )

    async def _get_chart_metadata(self, source: dagger.Directory, chart_path: str) -> dict:
        chart_yaml = await source.file(f"{chart_path}/Chart.yaml").contents()
        metadata = yaml.safe_load(chart_yaml) or {}
        if not isinstance(metadata, dict):
            return {}
        return metadata

    @function
    async def helm_verify(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Helm chart directory")],
        values: Annotated[dagger.File | None, Doc("Optional values.yaml file")] = None,
        release_name: Annotated[str, Doc("Helm release name for templating")] = "ci-release",
    ) -> str:
        """Run Helm lint and template via local helm module"""
        chart = self._helm(source=source)
        lint_stdout = await chart.lint(strict=True)
        template_stdout = await chart.template(values=values, release_name=release_name)
        return f"lint:\n{lint_stdout}\n\ntemplate:\n{template_stdout}"

    @function
    async def helm_publish(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Helm chart directory")],
        oci_url: Annotated[str, Doc("Destination OCI registry URL without chart name")],
        version: Annotated[str, Doc("Chart semver to publish")],
        app_version: Annotated[str | None, Doc("Optional appVersion override")] = None,
        username: Annotated[str | None, Doc("Registry username for login")] = None,
        password: Annotated[dagger.Secret | None, Doc("Registry password")] = None,
        insecure: Annotated[bool | None, Doc("Allow plain http pushes")] = False,
    ) -> str:
        """Package and push helm chart via local helm module"""
        chart = self._helm(source=source)
        if username and password:
            chart = chart.with_registry_login(username=username, password=password)
        return await chart.push(
            oci_url=oci_url,
            version=version,
            app_version=app_version or "",
            insecure=insecure,
        )

    @function
    async def helm_verify_changed_charts(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Repository root directory")],
        target_branch: Annotated[str, Doc("Target branch or ref to diff against")] = "master",
        charts_path: Annotated[str | None, Doc("Charts directory (relative to repo root)")] = None,
        libs_path: Annotated[str | None, Doc("Libraries directory (relative to repo root)")] = None,
        values: Annotated[dagger.File | None, Doc("Optional values.yaml file")] = None,
        release_name: Annotated[str, Doc("Helm release name for templating")] = "ci-release",
    ) -> list[str]:
        """Verify changed charts/libs and optionally publish feature versions"""
        diff_paths = [path for path in (charts_path, libs_path) if path]
        chart_paths = await self._get_changed_chart_paths(
            source=source,
            target_branch=target_branch,
            diff_paths=diff_paths,
        )
        if not chart_paths:
            return []

        outputs: list[str] = []
        for chart_path in chart_paths:
            chart_dir = source.directory(chart_path)
            metadata = await self._get_chart_metadata(source=source, chart_path=chart_path)
            chart_name = str(metadata.get("name", "")).strip()
            chart_version = str(metadata.get("version", "")).strip()
            if not chart_name or not chart_version:
                outputs.append(f"{chart_path}: skipped (missing name/version in Chart.yaml)")
                continue
            verify_out = await self.helm_verify(
                source=chart_dir,
                values=values,
                release_name=release_name,
            )

            summary_lines = [f"{chart_path}:", verify_out]
            outputs.append("\n".join(summary_lines))
        return outputs
