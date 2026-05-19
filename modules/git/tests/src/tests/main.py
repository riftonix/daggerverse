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
