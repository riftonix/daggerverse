"""Dagger-native tests for the Git module."""

from dagger import function, object_type

from .auth import AuthTests
from .components import ComponentTests
from .diffs import DiffTests
from .files_at_ref import FilesAtRefTests
from .metadata import MetadataTests
from .refs import RefTests
from .tags import TagTests


@object_type
class Tests:
    """Test module entrypoint for Git checks."""

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "git-tests"

    @function
    async def all(self) -> None:
        """Run all Git module tests."""
        await MetadataTests().all()
        await TagTests().all()
        await AuthTests().all()
        await RefTests().all()
        await DiffTests().all()
        await ComponentTests().all()
        await FilesAtRefTests().all()
