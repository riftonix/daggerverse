"""Dagger-native tests for the Git module."""

from typing import Annotated, Self

import dagger
from dagger import Doc, dag, function, object_type

from .auth import AuthTests
from .components import ComponentTests
from .diffs import DiffTests
from .files_at_ref import FilesAtRefTests
from .fixtures import DEFAULT_FIXTURE_IMAGE_TAG
from .metadata import MetadataTests
from .refs import RefTests
from .tags import TagTests


@object_type
class Tests:
    """Test module entrypoint for Git checks."""

    image_registry: str | None
    image_repository: str | None
    image_tag: str | None
    container_user_id: str | None

    @classmethod
    async def create(
        cls,
        image_registry: Annotated[str | None, Doc("Git image registry override")] = None,
        image_repository: Annotated[str | None, Doc("Git image repository override")] = None,
        image_tag: Annotated[str | None, Doc("Git image tag override")] = None,
        container_user_id: Annotated[str | None, Doc("Git container user ID override")] = None,
    ) -> Self:
        """Allow Git and its local repository fixtures to run with a mirrored image."""
        return cls(
            image_registry=image_registry,
            image_repository=image_repository,
            image_tag=image_tag,
            container_user_id=container_user_id,
        )

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "git-tests"

    @function
    async def all(self) -> None:
        """Run all Git module tests."""
        registry = self.image_registry or "docker.io"
        repository = self.image_repository or "alpine/git"
        tag = self.image_tag or DEFAULT_FIXTURE_IMAGE_TAG
        fixture_image = f"{registry}/{repository}:{tag}"
        await MetadataTests(self._git, fixture_image).all()
        await TagTests(self._git, fixture_image).all()
        await AuthTests(self._git, fixture_image).all(self.container_user_id or "12345")
        await RefTests(self._git, fixture_image).all()
        await DiffTests(self._git, fixture_image).all()
        await ComponentTests(self._git, fixture_image).all()
        await FilesAtRefTests(self._git, fixture_image).all()

    def _git(self, source: dagger.Directory, container_user_id: str | None = None) -> dagger.Git:
        return dag.git(
            source=source,
            image_registry=self.image_registry,
            image_repository=self.image_repository,
            image_tag=self.image_tag,
            container_user_id=container_user_id or self.container_user_id,
        )
