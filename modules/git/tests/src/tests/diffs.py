from unittest import TestCase

from dagger import dag

from .fixtures import SyntheticGitRepos


class DiffTests(SyntheticGitRepos):
    """Diff behavior tests."""

    async def all(self) -> None:
        await self.changed_files_between_refs()
        await self.changed_files_path_and_diff_filters()
        await self.changed_dirs_root_scoped()
        await self.changed_dirs_subdirectory_scoped()
        await self.has_changes_for_changed_and_unchanged_paths()

    async def changed_files_between_refs(self) -> None:
        """Return added, copied, modified, renamed, and type-changed files between refs."""
        git = dag.git(source=self.repo_with_diff_statuses().directory("/work/repo"))

        changed_files = await git.get_changed_files(base_ref="main", head_ref="feature")

        test_case = TestCase()
        test_case.assertEqual(
            [
                "added.txt",
                "copied.txt",
                "modified.txt",
                "renamed.txt",
                "services/api/handler.py",
                "services/api/internal/jobs/worker.py",
                "type-change",
            ],
            sorted(changed_files),
        )

    async def changed_files_path_and_diff_filters(self) -> None:
        """Scope changed files by path filters and Git diff-filter status letters."""
        git = dag.git(source=self.repo_with_diff_statuses().directory("/work/repo"))

        modified_files = await git.get_changed_files(base_ref="main", head_ref="feature", diff_filter="M")
        copied_files = await git.get_changed_files(base_ref="main", head_ref="feature", diff_filter="C")
        renamed_files = await git.get_changed_files(base_ref="main", head_ref="feature", diff_filter="R")
        scoped_files = await git.get_changed_files(base_ref="main", head_ref="feature", paths=["services/api"])
        type_changed_files = await git.get_changed_files(base_ref="main", head_ref="feature", diff_filter="T")

        test_case = TestCase()
        test_case.assertEqual(["modified.txt"], modified_files)
        test_case.assertEqual(["copied.txt"], copied_files)
        test_case.assertEqual(["renamed.txt"], renamed_files)
        test_case.assertEqual(["services/api/handler.py", "services/api/internal/jobs/worker.py"], scoped_files)
        test_case.assertEqual(["type-change"], type_changed_files)

    async def changed_dirs_root_scoped(self) -> None:
        """Return unique changed directories from repository root."""
        git = dag.git(source=self.repo_with_diff_statuses().directory("/work/repo"))

        top_level_dirs = await git.get_changed_dirs(base_ref="main", head_ref="feature")
        second_level_dirs = await git.get_changed_dirs(base_ref="main", head_ref="feature", depth=2)
        copied_dirs = await git.get_changed_dirs(base_ref="main", head_ref="feature", diff_filter="C")

        test_case = TestCase()
        test_case.assertEqual([".", "services"], top_level_dirs)
        test_case.assertEqual([".", "services/api"], second_level_dirs)
        test_case.assertEqual(["."], copied_dirs)

    async def changed_dirs_subdirectory_scoped(self) -> None:
        """Return changed directories scoped under a path filter."""
        git = dag.git(source=self.repo_with_diff_statuses().directory("/work/repo"))

        scoped_dirs = await git.get_changed_dirs(base_ref="main", head_ref="feature", paths=["services/api"])
        deeper_scoped_dirs = await git.get_changed_dirs(
            base_ref="main",
            head_ref="feature",
            paths=["services/api"],
            depth=2,
        )

        test_case = TestCase()
        test_case.assertEqual(["services/api", "services/api/internal"], scoped_dirs)
        test_case.assertEqual(["services/api", "services/api/internal/jobs"], deeper_scoped_dirs)

    async def has_changes_for_changed_and_unchanged_paths(self) -> None:
        """Return whether matching files changed between refs."""
        git = dag.git(source=self.repo_with_diff_statuses().directory("/work/repo"))

        has_any_changes = await git.has_changes(base_ref="main", head_ref="feature")
        has_scoped_changes = await git.has_changes(base_ref="main", head_ref="feature", paths=["services/api"])
        has_unchanged_path_changes = await git.has_changes(
            base_ref="main",
            head_ref="feature",
            paths=["copy-source.txt"],
        )
        has_matching_status_changes = await git.has_changes(base_ref="main", head_ref="feature", diff_filter="T")
        has_non_matching_status_changes = await git.has_changes(
            base_ref="main",
            head_ref="feature",
            paths=["services/api"],
            diff_filter="T",
        )

        test_case = TestCase()
        test_case.assertTrue(has_any_changes)
        test_case.assertTrue(has_scoped_changes)
        test_case.assertFalse(has_unchanged_path_changes)
        test_case.assertTrue(has_matching_status_changes)
        test_case.assertFalse(has_non_matching_status_changes)
