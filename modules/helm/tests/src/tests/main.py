"""Dagger-native tests for the Helm module."""

import json
from typing import Annotated
from unittest import TestCase

import yaml
from dagger import Directory, Doc, Service, dag, function, object_type

FIXTURE_CHART_PATH = "charts/ns-configurator"
FIXTURE_CHART_NAME = "ns-configurator"
FIXTURE_CHART_VERSION = "1.0.0"
FIXTURE_CHART_TYPE = "application"
FIXTURE_CHART_ANNOTATIONS = ["category=application", "owner=platform"]
LIBRARY_CHART_PATH = "charts/library-chart"
LIBRARY_CHART_NAME = "library-chart"
LIBRARY_CHART_VERSION = "0.1.0"
LIBRARY_CHART_TYPE = "library"
LIBRARY_CHART_ANNOTATIONS = ["category=library", "owner=platform"]
LOCAL_REGISTRY_HOST = "registry"
LOCAL_REGISTRY_PORT = 5000
LOCAL_REGISTRY_NAMESPACE = "charts"
DEFAULT_REGISTRY_IMAGE_REGISTRY = "docker.io"
DEFAULT_REGISTRY_IMAGE_REPOSITORY = "registry"
# renovate: datasource=docker depName=registry
DEFAULT_REGISTRY_IMAGE_TAG = "3"


@object_type
class Tests:
    """Test module entrypoint for Helm checks."""

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "helm-tests"

    @function
    async def all(self) -> None:
        """Run all Helm module tests."""
        await self.lint()
        await self.chart_metadata()
        await self.template()
        await self.library_chart_template()
        await self.package()
        await self.push()

    @function
    async def lint(self) -> str:
        """Run Helm lint against the fixture chart."""
        return await dag.helm(source=self._fixture_chart()).with_dependency_update().lint(strict=True, errors_only=True)

    @function
    async def template(self) -> None:
        """Run Helm template against the fixture chart."""
        rendered_template = await dag.helm(source=self._fixture_chart()).with_dependency_update().template()
        manifests = [manifest for manifest in yaml.safe_load_all(rendered_template) if manifest]
        test_case = TestCase()
        test_case.assertEqual(1, len(manifests))

        limit_range = manifests[0]
        test_case.assertEqual("v1", limit_range["apiVersion"])
        test_case.assertEqual("LimitRange", limit_range["kind"])
        test_case.assertEqual("limit-range", limit_range["metadata"]["name"])
        test_case.assertEqual(
            [
                {
                    "type": "Container",
                    "default": {"cpu": "250m", "memory": "512Mi"},
                    "defaultRequest": {"cpu": "25m", "memory": "64Mi"},
                    "max": {"cpu": "16000m", "memory": "32Gi"},
                    "min": {"cpu": "5m", "memory": "16Mi"},
                },
                {
                    "type": "Pod",
                    "max": {"cpu": "16000m", "memory": "32Gi"},
                },
            ],
            limit_range["spec"]["limits"],
        )

    @function
    async def chart_metadata(self) -> None:
        """Assert structured chart metadata for application and library charts."""
        app_metadata = json.loads(await dag.helm(source=self._fixture_chart()).get_chart_metadata_json())
        library_metadata = json.loads(await dag.helm(source=self._library_chart()).get_chart_metadata_json())

        test_case = TestCase()
        test_case.assertEqual(FIXTURE_CHART_NAME, app_metadata["name"])
        test_case.assertEqual(FIXTURE_CHART_VERSION, app_metadata["version"])
        test_case.assertEqual(FIXTURE_CHART_TYPE, app_metadata["chart_type"])
        test_case.assertEqual(FIXTURE_CHART_ANNOTATIONS, app_metadata["annotations"])
        test_case.assertNotEqual("library", app_metadata["chart_type"])

        test_case.assertEqual(LIBRARY_CHART_NAME, library_metadata["name"])
        test_case.assertEqual(LIBRARY_CHART_VERSION, library_metadata["version"])
        test_case.assertEqual(LIBRARY_CHART_TYPE, library_metadata["chart_type"])
        test_case.assertEqual(LIBRARY_CHART_ANNOTATIONS, library_metadata["annotations"])
        test_case.assertEqual("library", library_metadata["chart_type"])

    @function
    async def library_chart_template(self) -> None:
        """Assert Helm template is skipped for library charts."""
        rendered_template = await dag.helm(source=self._library_chart()).template()
        test_case = TestCase()
        test_case.assertEqual("", rendered_template)

    @function
    async def package(self) -> None:
        """Package the fixture chart and assert the output archive."""
        chart_archive = await dag.helm(source=self._fixture_chart()).with_dependency_update().package()
        test_case = TestCase()
        test_case.assertEqual("ns-configurator-1.0.0.tgz", await chart_archive.name())
        test_case.assertGreater(await chart_archive.size(), 0)

    @function
    async def push(
        self,
        registry_image_registry: Annotated[str, Doc("Registry image registry")] = DEFAULT_REGISTRY_IMAGE_REGISTRY,
        registry_image_repository: Annotated[str, Doc("Registry image repository")] = DEFAULT_REGISTRY_IMAGE_REPOSITORY,
        registry_image_tag: Annotated[str, Doc("Registry image tag")] = DEFAULT_REGISTRY_IMAGE_TAG,
    ) -> None:
        """Package and push the fixture chart to a local OCI registry service."""
        registry_service = self._local_registry(
            image_registry=registry_image_registry,
            image_repository=registry_image_repository,
            image_tag=registry_image_tag,
        )
        helm = dag.helm(source=self._fixture_chart()).with_dependency_update()
        helm_with_registry = helm.with_container(self._with_local_registry(helm.container(), registry_service))
        pushed = await helm_with_registry.push(
            oci_url=self._registry_namespace_url(),
            insecure=True,
        )
        published = await helm_with_registry.is_already_published(
            oci_chart_url=f"{self._registry_namespace_url()}/{FIXTURE_CHART_NAME}",
            version=FIXTURE_CHART_VERSION,
            insecure=True,
        )

        test_case = TestCase()
        test_case.assertEqual("ns-configurator-1.0.0.tgz", pushed)
        test_case.assertTrue(published)

    def _fixture_chart(self) -> Directory:
        """Return the fixture chart directory."""
        return dag.current_module().source().directory(FIXTURE_CHART_PATH)

    def _library_chart(self) -> Directory:
        """Return the fixture library chart directory."""
        return dag.current_module().source().directory(LIBRARY_CHART_PATH)

    def _local_registry(
        self,
        image_registry: str,
        image_repository: str,
        image_tag: str,
    ) -> Service:
        """Return an ephemeral local OCI registry service."""
        image = f"{image_registry}/{image_repository}:{image_tag}"
        return dag.container().from_(image).with_exposed_port(LOCAL_REGISTRY_PORT).as_service(use_entrypoint=True)

    def _with_local_registry(self, container, registry_service: Service):
        """Bind the local registry service to a Helm container."""
        for env_name in (
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "FTP_PROXY",
            "ALL_PROXY",
            "http_proxy",
            "https_proxy",
            "ftp_proxy",
            "all_proxy",
        ):
            container = container.with_env_variable(env_name, "")
        return (
            container.with_service_binding(LOCAL_REGISTRY_HOST, registry_service)
            .with_env_variable("NO_PROXY", f"{LOCAL_REGISTRY_HOST},{LOCAL_REGISTRY_HOST}:{LOCAL_REGISTRY_PORT}")
            .with_env_variable("no_proxy", f"{LOCAL_REGISTRY_HOST},{LOCAL_REGISTRY_HOST}:{LOCAL_REGISTRY_PORT}")
        )

    def _registry_namespace_url(self) -> str:
        """Return local registry namespace URL without chart name."""
        return f"{LOCAL_REGISTRY_HOST}:{LOCAL_REGISTRY_PORT}/{LOCAL_REGISTRY_NAMESPACE}"
