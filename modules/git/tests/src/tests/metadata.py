from unittest import TestCase

import dagger
from dagger import dag

from .fixtures import SyntheticGitRepos


class MetadataTests(SyntheticGitRepos):
    """Repository metadata tests."""

    async def all(self, source: dagger.Directory) -> None:
        await self.head_sha(source=source)
        await self.short_commit_sha(source=source)
        await self.current_ref_for_branch()
        await self.current_ref_for_detached_head()
        await self.remote_url_and_default_branch()
        await self.status_porcelain_for_clean_worktree()
        await self.status_porcelain_for_dirty_worktree()

    async def head_sha(self, source: dagger.Directory) -> None:
        """Call the parent Git module public API and assert full SHA shape."""
        head_sha = await dag.git(source=source).get_head_sha()

        test_case = TestCase()
        test_case.assertEqual(40, len(head_sha.strip()))
        test_case.assertRegex(head_sha.strip(), r"^[0-9a-f]+$")

    async def short_commit_sha(self, source: dagger.Directory) -> None:
        """Call the parent Git module public API and assert short SHA shape."""
        short_sha = await dag.git(source=source).get_short_commit_sha(length=8)

        test_case = TestCase()
        test_case.assertEqual(8, len(short_sha.strip()))
        test_case.assertRegex(short_sha.strip(), r"^[0-9a-f]+$")

    async def current_ref_for_branch(self) -> None:
        """Return branch metadata when HEAD is attached to a branch."""
        git = dag.git(source=self.repo_on_main_branch())

        current_branch = await git.get_current_branch()
        current_ref = await git.get_current_ref()

        test_case = TestCase()
        test_case.assertEqual("main", current_branch.strip())
        test_case.assertEqual("refs/heads/main", current_ref.strip())

    async def current_ref_for_detached_head(self) -> None:
        """Return detached HEAD metadata without reporting a branch."""
        git = dag.git(source=self.repo_with_detached_head())

        current_branch = await git.get_current_branch()
        current_ref = await git.get_current_ref()
        head_sha = await git.get_head_sha()

        test_case = TestCase()
        test_case.assertEqual("", current_branch.strip())
        test_case.assertEqual(head_sha.strip(), current_ref.strip())
        test_case.assertRegex(current_ref.strip(), r"^[0-9a-f]{40}$")

    async def remote_url_and_default_branch(self) -> None:
        """Return remote metadata from a local bare remote."""
        git = dag.git(source=self.repo_with_default_branch_remote())

        remote_url = await git.get_remote_url()
        default_branch = await git.get_default_branch()

        test_case = TestCase()
        test_case.assertEqual(".remote/origin.git", remote_url.strip())
        test_case.assertEqual("main", default_branch.strip())

    async def status_porcelain_for_clean_worktree(self) -> None:
        """Return empty porcelain status and clean flag for a clean worktree."""
        git = dag.git(source=self.repo_on_main_branch())

        status = await git.get_status_porcelain()
        is_clean = await git.has_clean_worktree()

        test_case = TestCase()
        test_case.assertEqual("", status.strip())
        test_case.assertTrue(is_clean)

    async def status_porcelain_for_dirty_worktree(self) -> None:
        """Return porcelain status and dirty flag for pending changes."""
        git = dag.git(source=self.repo_with_dirty_worktree())

        status = await git.get_status_porcelain()
        is_clean = await git.has_clean_worktree()

        test_case = TestCase()
        test_case.assertIn(" M README.md", status)
        test_case.assertIn("?? untracked.txt", status)
        test_case.assertFalse(is_clean)
