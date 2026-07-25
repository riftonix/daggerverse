import json
from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type

DEFAULT_HELM_IMAGE_REGISTRY = "docker.io"
DEFAULT_HELM_IMAGE_REPOSITORY = "alpine/helm"
# renovate: datasource=docker depName=alpine/helm
DEFAULT_HELM_IMAGE_TAG = "4.2.3"
DEFAULT_HELM_CONTAINER_USER_ID = "65532"

DEFAULT_GIT_IMAGE_REGISTRY = "docker.io"
DEFAULT_GIT_IMAGE_REPOSITORY = "alpine/git"
# renovate: datasource=docker depName=alpine/git
DEFAULT_GIT_IMAGE_TAG = "v2.54.0"
DEFAULT_GIT_CONTAINER_USER_ID = "65532"

DEFAULT_HELM_UNITTEST_IMAGE_REGISTRY = "docker.io"
DEFAULT_HELM_UNITTEST_IMAGE_REPOSITORY = "helmunittest/helm-unittest"
# renovate: datasource=docker depName=helmunittest/helm-unittest
DEFAULT_HELM_UNITTEST_IMAGE_TAG = "4.2.0-1.1.0"
DEFAULT_HELM_UNITTEST_CONTAINER_USER_ID = "65532"


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

    helm_unittest_image_registry: str
    helm_unittest_image_repository: str
    helm_unittest_image_tag: str
    helm_unittest_container_user_id: str

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
        helm_unittest_image_registry: Annotated[
            str | None, Doc("Helm unittest image registry")
        ] = DEFAULT_HELM_UNITTEST_IMAGE_REGISTRY,
        helm_unittest_image_repository: Annotated[
            str | None, Doc("Helm unittest image repository")
        ] = DEFAULT_HELM_UNITTEST_IMAGE_REPOSITORY,
        helm_unittest_image_tag: Annotated[
            str | None, Doc("Helm unittest image tag")
        ] = DEFAULT_HELM_UNITTEST_IMAGE_TAG,
        helm_unittest_container_user_id: Annotated[
            str | None, Doc("Helm unittest container user")
        ] = DEFAULT_HELM_UNITTEST_CONTAINER_USER_ID,
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
            helm_unittest_image_registry=helm_unittest_image_registry or DEFAULT_HELM_UNITTEST_IMAGE_REGISTRY,
            helm_unittest_image_repository=helm_unittest_image_repository or DEFAULT_HELM_UNITTEST_IMAGE_REPOSITORY,
            helm_unittest_image_tag=helm_unittest_image_tag or DEFAULT_HELM_UNITTEST_IMAGE_TAG,
            helm_unittest_container_user_id=helm_unittest_container_user_id or DEFAULT_HELM_UNITTEST_CONTAINER_USER_ID,
        )

    async def _get_changed_chart_paths(
        self,
        source: dagger.Directory,
        base_ref: str,
        head_ref: str,
        charts_path: list[str],
    ) -> list[str]:
        if not charts_path:
            msg = "At least one chart path pattern is required"
            raise ValueError(msg)

        git = dag.git(
            source=source,
            image_registry=self.git_image_registry,
            image_repository=self.git_image_repository,
            image_tag=self.git_image_tag,
            user_id=self.git_container_user_id,
        )
        merge_base = await git.get_merge_base(base_ref=base_ref, head_ref=head_ref)
        return await git.get_changed_components(
            base_ref=merge_base,
            head_ref=head_ref,
            component_roots=charts_path,
        )

    def _helm(self, source: dagger.Directory):
        """Return configured Helm module instance from the helm module dependency."""
        return dag.helm(
            source=source,
            image_registry=self.helm_image_registry,
            image_repository=self.helm_image_repository,
            image_tag=self.helm_image_tag,
            container_user_id=self.helm_container_user_id,
        )

    def _helm_unittest(self, source: dagger.Directory):
        """Return configured Helm unittest module instance from the module dependency."""
        return dag.helm_unittest(
            source=source,
            image_registry=self.helm_unittest_image_registry,
            image_repository=self.helm_unittest_image_repository,
            image_tag=self.helm_unittest_image_tag,
            container_user_id=self.helm_unittest_container_user_id,
        )

    async def _has_unittest_suites(self, chart_dir: dagger.Directory) -> bool:
        """Return whether a chart contains Helm unittest suite files."""
        return bool(await chart_dir.glob("tests/**/*.yaml")) or bool(await chart_dir.glob("tests/**/*.yml"))

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

    async def _verify_changed_chart(
        self,
        chart_dir: dagger.Directory,
        chart_path: str,
        values: dagger.File | None,
        release_name: str,
    ) -> str:
        chart = self._helm(source=chart_dir).with_dependency_update()
        metadata = json.loads(await chart.get_chart_metadata_json())
        if not metadata.get("name") or not metadata.get("version"):
            return f"{chart_path}: skipped (missing name/version in Chart.yaml)"

        lint_stdout = await chart.lint(strict=True)
        steps = [f"{chart_path}:", f"lint:\n{lint_stdout}"]

        if metadata.get("chart_type") == "library":
            steps.append("template: skipped (library chart)")
        else:
            template_stdout = await chart.template(values=values, release_name=release_name)
            steps.append(f"template:\n{template_stdout}")

        if await self._has_unittest_suites(chart_dir):
            unittest_stdout = await self._helm_unittest(source=chart_dir).with_dependency_update().test()
            steps.append(f"unittest:\n{unittest_stdout}")
        else:
            steps.append("unittest: skipped (no suite files under tests/)")
        return "\n\n".join(steps)

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
    async def verify_charts(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Repository root directory")],
        base_ref: Annotated[str, Doc("Base ref to compare changed chart components against")],
        head_ref: Annotated[str, Doc("Head ref to compare changed chart components from")] = "HEAD",
        charts_path: Annotated[
            list[str] | None,
            Doc(
                "Glob-like chart component root pattern relative to source, for example charts/*; repeat for multiple roots"
            ),
        ] = None,
        values: Annotated[dagger.File | None, Doc("Optional values.yaml file")] = None,
        release_name: Annotated[str, Doc("Helm release name for templating")] = "ci-release",
    ) -> list[str]:
        """Verify changed chart components discovered from caller-provided chart root patterns."""
        chart_paths = await self._get_changed_chart_paths(
            source=source,
            base_ref=base_ref,
            head_ref=head_ref,
            charts_path=charts_path or [],
        )
        if not chart_paths:
            return ["No changed chart directories found"]

        outputs: list[str] = []
        for chart_path in chart_paths:
            chart_dir = source.directory(chart_path)
            if not await chart_dir.glob("Chart.yaml"):
                outputs.append(f"{chart_path}: skipped (not a Helm chart)")
                continue
            outputs.append(
                await self._verify_changed_chart(
                    chart_dir=chart_dir,
                    chart_path=chart_path,
                    values=values,
                    release_name=release_name,
                )
            )
        return outputs
