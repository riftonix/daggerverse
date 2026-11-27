"""Dagger workflow for verifying one Go application."""

from typing import Annotated, Self

import dagger
from dagger import Doc, dag, function, object_type

DEFAULT_GO_IMAGE_REGISTRY = "docker.io"
DEFAULT_GO_IMAGE_REPOSITORY = "library/golang"
# renovate: datasource=docker depName=library/golang
DEFAULT_GO_IMAGE_TAG = "1.27.4"
DEFAULT_GO_CONTAINER_USER_ID = "65532"


@object_type
class GoCi:
    """Check formatting, run tests, and compile a Go application."""

    source: dagger.Directory
    go_image_registry: str
    go_image_repository: str
    go_image_tag: str
    go_container_user_id: str

    @classmethod
    def create(
        cls,
        source: Annotated[dagger.Directory, Doc("Source directory containing the root go.mod")],
        go_image_registry: Annotated[str, Doc("Go runtime image registry")] = DEFAULT_GO_IMAGE_REGISTRY,
        go_image_repository: Annotated[str, Doc("Go runtime image repository")] = DEFAULT_GO_IMAGE_REPOSITORY,
        go_image_tag: Annotated[str, Doc("Go runtime image tag")] = DEFAULT_GO_IMAGE_TAG,
        go_container_user_id: Annotated[str, Doc("Numeric UID for Go commands")] = DEFAULT_GO_CONTAINER_USER_ID,
    ) -> Self:
        """Select the source, Go runtime image, and execution user."""
        return cls(
            source=source,
            go_image_registry=go_image_registry,
            go_image_repository=go_image_repository,
            go_image_tag=go_image_tag,
            go_container_user_id=go_container_user_id,
        )

    @function
    async def verify_app(
        self,
        package: Annotated[str, Doc("One main package directory relative to the module root")],
    ) -> str:
        """Check formatting, test the root module, and compile an application without exporting it."""
        go = dag.go(
            source=self.source,
            image_registry=self.go_image_registry,
            image_repository=self.go_image_repository,
            image_tag=self.go_image_tag,
            container_user_id=self.go_container_user_id,
        )
        package = await go.validate_package(package=package)
        await go.check_format()
        await go.test()
        await go.build(package=package)

        image = f"{self.go_image_registry}/{self.go_image_repository}:{self.go_image_tag}"
        return f"Verified {package} using {image}: gofmt, go test ./..., go build passed."
