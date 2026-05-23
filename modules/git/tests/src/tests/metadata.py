from unittest import TestCase

import dagger
from dagger import dag


class MetadataTests:
    """Repository metadata tests."""

    async def all(self, source: dagger.Directory) -> None:
        await self.short_commit_sha(source=source)

    async def short_commit_sha(self, source: dagger.Directory) -> None:
        """Call the parent Git module public API and assert short SHA shape."""
        short_sha = await dag.git(source=source).get_short_commit_sha(length=8)

        test_case = TestCase()
        test_case.assertEqual(8, len(short_sha.strip()))
        test_case.assertRegex(short_sha.strip(), r"^[0-9a-f]+$")
