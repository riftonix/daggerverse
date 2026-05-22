"""Dagger-native tests for the Git module."""

from typing import Annotated
from unittest import TestCase

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type


@object_type
class Tests:
    """Test module entrypoint for Git checks."""

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "git-tests"

    @function
    async def all(
        self,
        source: Annotated[
            dagger.Directory,
            DefaultPath("../../.."),
            Doc("Git repository root directory"),
        ],
    ) -> None:
        """Run all Git module tests."""
        await self.short_commit_sha(source=source)
        await self.fetch_tags()
        await self.get_tags()
        await self.tags_pointing_at()
        await self.compatibility_wrappers()
        await self.merge_base_for_diverged_branches()
        await self.changed_files_between_refs()
        await self.changed_files_path_and_diff_filters()
        await self.changed_dirs_root_scoped()
        await self.changed_dirs_subdirectory_scoped()
        await self.has_changes_for_changed_and_unchanged_paths()

    @function
    async def short_commit_sha(
        self,
        source: Annotated[
            dagger.Directory,
            DefaultPath("../../.."),
            Doc("Git repository root directory"),
        ],
    ) -> None:
        """Call the parent Git module public API and assert short SHA shape."""
        short_sha = await dag.git(source=source).get_short_commit_sha(length=8)

        test_case = TestCase()
        test_case.assertEqual(8, len(short_sha.strip()))
        test_case.assertRegex(short_sha.strip(), r"^[0-9a-f]+$")

    @function
    async def fetch_tags(self) -> None:
        """Fetch tags from a local bare remote into a repository without local tags."""
        git = dag.git(source=self._repo_with_remote_tag())
        test_case = TestCase()

        test_case.assertEqual([], await git.list_tags(pattern="v1.0.0"))
        fetch_output = await git.fetch_tags()
        test_case.assertIn("[new tag]", fetch_output)
        test_case.assertIn("v1.0.0", fetch_output)

    @function
    async def get_tags(self) -> None:
        """Return local tags through the verb-based get_tags function."""
        tags = await dag.git(source=self._repo_with_local_tag()).get_tags(pattern="v1.*")

        test_case = TestCase()
        test_case.assertEqual(["v1.0.0"], tags)

    @function
    async def tags_pointing_at(self) -> None:
        """Fetch remote tags and return tags that point at an explicit ref."""
        tags = await dag.git(source=self._repo_with_remote_tag()).get_tags_pointing_at(ref="HEAD")

        test_case = TestCase()
        test_case.assertEqual(["v1.0.0"], tags)

    @function
    async def compatibility_wrappers(self) -> None:
        """Keep old names working while verb-based names are introduced."""
        git = dag.git(source=self._repo_with_local_tag())
        tags = await git.get_tags(pattern="v1.*")
        legacy_tags = await git.list_tags(pattern="v1.*")

        test_case = TestCase()
        test_case.assertEqual(tags, legacy_tags)

    @function
    async def merge_base_for_diverged_branches(self) -> None:
        """Return the shared commit for diverged base and head branches."""
        repo = self._repo_with_diverged_branches()
        git = dag.git(source=repo.directory("/work/repo"))

        merge_base = await git.get_merge_base(base_ref="main", head_ref="feature")
        expected_merge_base = await repo.with_exec(["git", "merge-base", "main", "feature"]).stdout()
        main_sha = await repo.with_exec(["git", "rev-parse", "main"]).stdout()
        feature_sha = await repo.with_exec(["git", "rev-parse", "feature"]).stdout()

        test_case = TestCase()
        test_case.assertEqual(expected_merge_base.strip(), merge_base)
        test_case.assertNotEqual(main_sha.strip(), merge_base)
        test_case.assertNotEqual(feature_sha.strip(), merge_base)

    @function
    async def changed_files_between_refs(self) -> None:
        """Return added, copied, modified, renamed, and type-changed files between refs."""
        git = dag.git(source=self._repo_with_diff_statuses().directory("/work/repo"))

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

    @function
    async def changed_files_path_and_diff_filters(self) -> None:
        """Scope changed files by path filters and Git diff-filter status letters."""
        git = dag.git(source=self._repo_with_diff_statuses().directory("/work/repo"))

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

    @function
    async def changed_dirs_root_scoped(self) -> None:
        """Return unique changed directories from repository root."""
        git = dag.git(source=self._repo_with_diff_statuses().directory("/work/repo"))

        top_level_dirs = await git.get_changed_dirs(base_ref="main", head_ref="feature")
        second_level_dirs = await git.get_changed_dirs(base_ref="main", head_ref="feature", depth=2)
        copied_dirs = await git.get_changed_dirs(base_ref="main", head_ref="feature", diff_filter="C")

        test_case = TestCase()
        test_case.assertEqual([".", "services"], top_level_dirs)
        test_case.assertEqual([".", "services/api"], second_level_dirs)
        test_case.assertEqual(["."], copied_dirs)

    @function
    async def changed_dirs_subdirectory_scoped(self) -> None:
        """Return changed directories scoped under a path filter."""
        git = dag.git(source=self._repo_with_diff_statuses().directory("/work/repo"))

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

    @function
    async def has_changes_for_changed_and_unchanged_paths(self) -> None:
        """Return whether matching files changed between refs."""
        git = dag.git(source=self._repo_with_diff_statuses().directory("/work/repo"))

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

    def _repo_with_local_tag(self) -> dagger.Directory:
        """Return a git repo with a local tag."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(["sh", "-c", "printf 'initial\\n' > README.md && git add README.md && git commit -m initial"])
            .with_exec(["git", "tag", "v1.0.0"])
            .directory("/work/repo")
        )

    def _repo_with_remote_tag(self) -> dagger.Directory:
        """Return a git repo whose local bare remote contains a tag missing locally."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(["sh", "-c", "printf 'initial\\n' > README.md && git add README.md && git commit -m initial"])
            .with_exec(["git", "tag", "v1.0.0"])
            .with_exec(["mkdir", "-p", ".remote"])
            .with_exec(["git", "clone", "--bare", ".", ".remote/origin.git"])
            .with_exec(["git", "tag", "-d", "v1.0.0"])
            .with_exec(["git", "remote", "add", "origin", ".remote/origin.git"])
            .directory("/work/repo")
        )

    def _repo_with_diverged_branches(self) -> dagger.Container:
        """Return a git repo with base and feature branches diverged from one commit."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(["sh", "-c", "printf 'initial\\n' > README.md && git add README.md && git commit -m initial"])
            .with_exec(["git", "checkout", "-b", "feature"])
            .with_exec(
                ["sh", "-c", "printf 'feature\\n' > feature.txt && git add feature.txt && git commit -m feature"]
            )
            .with_exec(["git", "checkout", "main"])
            .with_exec(["sh", "-c", "printf 'main\\n' > main.txt && git add main.txt && git commit -m main"])
        )

    def _repo_with_diff_statuses(self) -> dagger.Container:
        """Return a git repo with practical diff status coverage."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    (
                        "mkdir -p services/api && "
                        "printf 'copy source\\n' > copy-source.txt && "
                        "printf 'before\\n' > modified.txt && "
                        "printf 'rename me\\n' > renamed-from.txt && "
                        "printf 'regular file\\n' > type-change && "
                        "git add . && git commit -m initial"
                    ),
                ]
            )
            .with_exec(["git", "checkout", "-b", "feature"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    (
                        "printf 'added\\n' > added.txt && "
                        "cp copy-source.txt copied.txt && "
                        "printf 'after\\n' > modified.txt && "
                        "git mv renamed-from.txt renamed.txt && "
                        "rm type-change && ln -s copy-source.txt type-change && "
                        "printf 'handler\\n' > services/api/handler.py && "
                        "mkdir -p services/api/internal/jobs && "
                        "printf 'worker\\n' > services/api/internal/jobs/worker.py && "
                        "git add . && git commit -m feature"
                    ),
                ]
            )
        )
