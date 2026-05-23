from unittest import TestCase

import dagger
from dagger import dag

from .fixtures import SyntheticGitRepos


class RefTests(SyntheticGitRepos):
    """Ref and fetch behavior tests."""

    async def all(self) -> None:
        await self.with_fetched_refs_missing_branch()
        await self.ensure_ref_resolves_existing_ref()
        await self.ensure_ref_fails_for_missing_ref()
        await self.with_unshallow_fetches_full_history()
        await self.with_unshallow_keeps_full_repository_usable()
        await self.merge_base_for_diverged_branches()

    async def with_fetched_refs_missing_branch(self) -> None:
        """Fetch a missing remote branch from a local bare remote."""
        git = dag.git(source=self.repo_with_missing_remote_branch())
        test_case = TestCase()

        try:
            await git.container().with_exec(["git", "rev-parse", "--verify", "origin/feature"]).stdout()
        except dagger.ExecError:
            pass
        else:
            test_case.fail("origin/feature should be missing before with_fetched_refs")

        fetched_git = git.with_fetched_refs(refspecs=["refs/heads/feature:refs/remotes/origin/feature"])
        changed_files = await fetched_git.get_changed_files(base_ref="main", head_ref="origin/feature")
        fetched_ref = (
            await fetched_git.container().with_exec(["git", "rev-parse", "--verify", "origin/feature"]).stdout()
        )

        test_case.assertRegex(fetched_ref.strip(), r"^[0-9a-f]+$")
        test_case.assertEqual(["feature.txt"], changed_files)

    async def ensure_ref_resolves_existing_ref(self) -> None:
        """Return the resolved object SHA for an existing ref."""
        repo = self.repo_with_local_tag()
        git = dag.git(source=repo)

        resolved_ref = await git.ensure_ref(ref="HEAD")
        expected_ref = (
            await dag.git(source=repo).container().with_exec(["git", "rev-parse", "--verify", "HEAD"]).stdout()
        )

        test_case = TestCase()
        test_case.assertEqual(expected_ref.strip(), resolved_ref)

    async def ensure_ref_fails_for_missing_ref(self) -> None:
        """Fail with a clear error when a ref is missing."""
        git = dag.git(source=self.repo_with_local_tag())
        test_case = TestCase()

        try:
            await git.ensure_ref(ref="refs/heads/missing")
        except dagger.ExecError as error:
            test_case.assertIn("Git ref not found: refs/heads/missing", error.stderr)
        else:
            test_case.fail("ensure_ref should fail for a missing ref")

    async def with_unshallow_fetches_full_history(self) -> None:
        """Turn a shallow repository into a full-history repository."""
        git = dag.git(source=self.shallow_repo_with_remote_history())
        test_case = TestCase()

        is_shallow = await git.container().with_exec(["git", "rev-parse", "--is-shallow-repository"]).stdout()
        test_case.assertEqual("true", is_shallow.strip())

        full_git = git.with_unshallow()

        is_shallow = await full_git.container().with_exec(["git", "rev-parse", "--is-shallow-repository"]).stdout()
        commit_count = await full_git.container().with_exec(["git", "rev-list", "--count", "HEAD"]).stdout()

        test_case.assertEqual("false", is_shallow.strip())
        test_case.assertEqual("3", commit_count.strip())

    async def with_unshallow_keeps_full_repository_usable(self) -> None:
        """Leave an already full-history repository usable after with_unshallow."""
        git = dag.git(source=self.repo_with_remote_tag())

        full_git = git.with_unshallow()
        resolved_ref = await full_git.ensure_ref(ref="HEAD")

        test_case = TestCase()
        test_case.assertRegex(resolved_ref, r"^[0-9a-f]+$")

    async def merge_base_for_diverged_branches(self) -> None:
        """Return the shared commit for diverged base and head branches."""
        repo = self.repo_with_diverged_branches()
        git = dag.git(source=repo.directory("/work/repo"))

        merge_base = await git.get_merge_base(base_ref="main", head_ref="feature")
        expected_merge_base = await repo.with_exec(["git", "merge-base", "main", "feature"]).stdout()
        main_sha = await repo.with_exec(["git", "rev-parse", "main"]).stdout()
        feature_sha = await repo.with_exec(["git", "rev-parse", "feature"]).stdout()

        test_case = TestCase()
        test_case.assertEqual(expected_merge_base.strip(), merge_base)
        test_case.assertNotEqual(main_sha.strip(), merge_base)
        test_case.assertNotEqual(feature_sha.strip(), merge_base)
