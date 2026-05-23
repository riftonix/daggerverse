from unittest import TestCase

from dagger import dag

from .fixtures import SyntheticGitRepos


class TagTests(SyntheticGitRepos):
    """Tag behavior tests."""

    async def all(self) -> None:
        await self.with_fetched_tags()
        await self.get_tags()
        await self.tags_pointing_at()

    async def with_fetched_tags(self) -> None:
        """Fetch tags from a local bare remote into a repository without local tags."""
        git = dag.git(source=self.repo_with_remote_tag())
        test_case = TestCase()

        test_case.assertEqual([], await git.get_tags(pattern="v1.0.0"))

        fetched_git = git.with_fetched_tags()

        test_case.assertEqual(["v1.0.0"], await fetched_git.get_tags(pattern="v1.0.0"))

    async def get_tags(self) -> None:
        """Return local tags through the verb-based get_tags function."""
        tags = await dag.git(source=self.repo_with_local_tag()).get_tags(pattern="v1.*")

        test_case = TestCase()
        test_case.assertEqual(["v1.0.0"], tags)

    async def tags_pointing_at(self) -> None:
        """Fetch remote tags and return tags that point at an explicit ref."""
        tags = await dag.git(source=self.repo_with_remote_tag()).get_tags_pointing_at(ref="HEAD")

        test_case = TestCase()
        test_case.assertEqual(["v1.0.0"], tags)
