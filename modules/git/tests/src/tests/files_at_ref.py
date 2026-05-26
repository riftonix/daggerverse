from unittest import TestCase

from dagger import dag

from .fixtures import SyntheticGitRepos


class FilesAtRefTests(SyntheticGitRepos):
    """Files-at-ref behavior tests."""

    async def all(self) -> None:
        await self.has_file_at_ref_for_existing_and_missing_files()
        await self.get_file_contents_at_ref_for_non_head_ref()

    async def has_file_at_ref_for_existing_and_missing_files(self) -> None:
        """Return whether files exist at a ref."""
        git = dag.git(source=self.repo_on_main_branch())

        has_readme = await git.has_file_at_ref(ref="HEAD", path="README.md")
        has_missing_file = await git.has_file_at_ref(ref="HEAD", path="missing.txt")
        has_missing_nested_file = await git.has_file_at_ref(ref="HEAD", path="docs/missing.md")

        test_case = TestCase()
        test_case.assertTrue(has_readme)
        test_case.assertFalse(has_missing_file)
        test_case.assertFalse(has_missing_nested_file)

    async def get_file_contents_at_ref_for_non_head_ref(self) -> None:
        """Read file contents from a non-HEAD ref."""
        git = dag.git(source=self.repo_with_file_versions_at_refs())

        old_contents = await git.get_file_contents_at_ref(ref="old-version", path="version.txt")
        head_contents = await git.get_file_contents_at_ref(ref="HEAD", path="version.txt")

        test_case = TestCase()
        test_case.assertEqual("old contents\n", old_contents)
        test_case.assertEqual("head contents\n", head_contents)
