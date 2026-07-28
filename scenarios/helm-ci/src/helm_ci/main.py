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
    source: dagger.Directory
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
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Repository root directory")],
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
            source=source,
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

    async def _git_with_optional_auth(
        self,
        git_token: dagger.Secret | None,
        git_host: str,
        git_username: str,
    ):
        """Return the repository Git module with optional HTTPS authentication."""
        git = dag.git(
            source=self.source,
            image_registry=self.git_image_registry,
            image_repository=self.git_image_repository,
            image_tag=self.git_image_tag,
            user_id=self.git_container_user_id,
        )
        if git_token:
            git = await git.with_https_token_auth(
                host=git_host,
                username=git_username,
                token=git_token,
            )
        return git

    @function
    async def verify_chart(
        self,
        values: Annotated[dagger.File | None, Doc("Optional values.yaml file")] = None,
        release_name: Annotated[str, Doc("Helm release name for templating")] = "ci-release",
        chart_source: Annotated[
            dagger.Directory | None,
            Doc("Optional Helm chart directory; defaults to the scenario source"),
        ] = None,
        unittest_suite_files: Annotated[
            list[str] | None,
            Doc("Optional Helm unittest suite file glob patterns"),
        ] = None,
    ) -> str:
        """Verify the Helm chart supplied as the scenario source."""
        chart_source = chart_source or self.source
        if not await chart_source.glob("Chart.yaml"):
            raise ValueError("source: not a Helm chart")

        chart = self._helm(source=chart_source).with_dependency_update()
        metadata = json.loads(await chart.get_chart_metadata_json())
        if not metadata.get("name") or not metadata.get("version"):
            return "skipped (missing name/version in Chart.yaml)"

        lint_stdout = await chart.lint(strict=True)
        steps = [f"lint:\n{lint_stdout}"]

        if metadata.get("chart_type") == "library":
            steps.append("template: skipped (library chart)")
        else:
            template_stdout = await chart.template(values=values, release_name=release_name)
            steps.append(f"template:\n{template_stdout}")

        unittest = self._helm_unittest(source=chart_source)
        if await unittest.has_suites(suite_files=unittest_suite_files):
            unittest_stdout = await unittest.with_dependency_update().test(suite_files=unittest_suite_files)
            steps.append(f"unittest:\n{unittest_stdout}")
        else:
            steps.append("unittest: skipped (no suite files matched configured patterns)")
        return "\n\n".join(steps)

    @function
    async def get_chart_release_tag(
        self,
        git_tag_prefix: Annotated[str, Doc("Git release tag prefix for the chart")],
        chart_source: Annotated[
            dagger.Directory | None,
            Doc("Optional Helm chart directory; defaults to the scenario source"),
        ] = None,
        version: Annotated[str | None, Doc("Optional chart version override")] = None,
    ) -> str:
        """Return the chart-scoped Git release tag."""
        normalized_git_tag_prefix = git_tag_prefix.strip("/")
        if not normalized_git_tag_prefix:
            raise ValueError("git_tag_prefix: must not be empty")

        chart_source = chart_source or self.source
        if not await chart_source.glob("Chart.yaml"):
            raise ValueError("chart_source: not a Helm chart (missing Chart.yaml)")

        chart_version = await self._helm(source=chart_source).get_chart_version()
        if not chart_version:
            raise ValueError("chart_source: missing version in Chart.yaml")
        return f"{normalized_git_tag_prefix}/v{version or chart_version}"

    @function
    def get_chart_oci_url(
        self,
        oci_base_url: Annotated[str, Doc("Base OCI registry URL without chart namespace")],
        git_tag_prefix: Annotated[str, Doc("Git release tag prefix for the chart")],
    ) -> str:
        """Return the chart OCI namespace URL derived from its Git tag prefix."""
        normalized_oci_base_url = oci_base_url.removeprefix("oci://").rstrip("/")
        if not normalized_oci_base_url:
            raise ValueError("oci_base_url: must not be empty")

        normalized_git_tag_prefix = git_tag_prefix.strip("/")
        if not normalized_git_tag_prefix:
            raise ValueError("git_tag_prefix: must not be empty")
        return f"{normalized_oci_base_url}/{normalized_git_tag_prefix}"

    @function
    async def publish_chart(
        self,
        oci_base_url: Annotated[str, Doc("Base OCI registry URL without chart namespace")],
        git_tag_prefix: Annotated[str, Doc("Git release tag prefix for the chart")],
        git_token: Annotated[dagger.Secret | None, Doc("Optional HTTPS token used to push the release Git tag")] = None,
        chart_source: Annotated[
            dagger.Directory | None,
            Doc("Optional Helm chart directory; defaults to the scenario source"),
        ] = None,
        version: Annotated[str | None, Doc("Optional chart version override")] = None,
        app_version: Annotated[str | None, Doc("Optional appVersion override")] = None,
        with_dependency_update: Annotated[
            bool,
            Doc("Run Helm dependency update before publishing"),
        ] = True,
        username: Annotated[str | None, Doc("Registry username for login")] = None,
        password: Annotated[dagger.Secret | None, Doc("Registry password")] = None,
        insecure: Annotated[bool | None, Doc("Allow plain http pushes")] = False,
        git_host: Annotated[str, Doc("HTTPS Git host used for release tag authentication")] = "github.com",
        git_username: Annotated[str, Doc("HTTPS Git username used for release tag authentication")] = "x-access-token",
        git_remote: Annotated[str, Doc("Git remote that receives the release tag")] = "origin",
    ) -> str:
        """Publish one Helm chart and push its Git release tag."""
        chart_source = chart_source or self.source
        oci_url = self.get_chart_oci_url(
            oci_base_url=oci_base_url,
            git_tag_prefix=git_tag_prefix,
        )
        release_tag = await self.get_chart_release_tag(
            git_tag_prefix=git_tag_prefix,
            chart_source=chart_source,
            version=version,
        )
        if bool(username) != bool(password):
            raise ValueError("username and password must be supplied together")

        git = await self._git_with_optional_auth(
            git_token=git_token,
            git_host=git_host,
            git_username=git_username,
        )
        git = git.with_fetched_tags(remote=git_remote)
        if await git.has_tag(tag=release_tag):
            return f"skipped: release tag already exists\nrelease tag: {release_tag}"

        chart = self._helm(source=chart_source)
        if with_dependency_update:
            chart = chart.with_dependency_update()

        if username and password:
            chart = chart.with_registry_login(username=username, password=password)
        package_name = await chart.push(
            oci_url=oci_url,
            version=version or "",
            app_version=app_version or "",
            insecure=insecure,
        )

        await git.create_tag(tag=release_tag).push_tag(tag=release_tag, remote=git_remote).container().sync()
        return f"published: {package_name}\nrelease tag: {release_tag}"
