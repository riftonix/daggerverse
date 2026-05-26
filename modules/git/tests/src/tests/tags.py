from unittest import TestCase

from dagger import dag

from .fixtures import SyntheticGitRepos


class TagTests(SyntheticGitRepos):
    """Tag behavior tests."""

    async def all(self) -> None:
        await self.with_fetched_tags()
        await self.get_tags()
        await self.get_tags_with_sort()
        await self.has_tag()
        await self.get_latest_tag()
        await self.tags_pointing_at()
        await self.create_lightweight_tag()
        await self.create_annotated_tag()
        await self.push_tag_to_local_bare_remote()

    async def with_fetched_tags(self) -> None:
        """Fetch tags from a local bare remote into a repository without local tags."""
        git = dag.git(source=self.repo_with_remote_tag())
        test_case = TestCase()

        test_case.assertEqual([], await git.get_tags(pattern="v1.0.0"))

        fetched_git = git.with_fetched_tags()

        test_case.assertEqual(["v1.0.0"], await fetched_git.get_tags(pattern="v1.0.0"))

    async def get_tags(self) -> None:
        """Return local tags through the verb-based get_tags function."""
        tags = await dag.git(source=self.repo_with_version_tags()).get_tags(pattern="v1.*")

        test_case = TestCase()
        test_case.assertEqual(["v1.0.0", "v1.2.0", "v1.10.0"], tags)

    async def get_tags_with_sort(self) -> None:
        """Return local tags with an explicit git tag sort order."""
        git = dag.git(source=self.repo_with_version_tags())

        refname_tags = await git.get_tags(pattern="v1.*", sort="refname")
        descending_version_tags = await git.get_tags(pattern="v1.*", sort="-version")
        service_tags = await git.get_tags(pattern="service/*")

        test_case = TestCase()
        test_case.assertEqual(["v1.0.0", "v1.10.0", "v1.2.0"], refname_tags)
        test_case.assertEqual(["v1.10.0", "v1.2.0", "v1.0.0"], descending_version_tags)
        test_case.assertEqual(["service/v2.0.0"], service_tags)

    async def has_tag(self) -> None:
        """Return whether an exact local tag exists."""
        git = dag.git(source=self.repo_with_version_tags())

        test_case = TestCase()
        test_case.assertTrue(await git.has_tag(tag="v1.2.0"))
        test_case.assertTrue(await git.has_tag(tag="service/v2.0.0"))
        test_case.assertFalse(await git.has_tag(tag="v1.3.0"))
        test_case.assertFalse(await git.has_tag(tag="v1.*"))

    async def get_latest_tag(self) -> None:
        """Return the latest matching tag for semver and non-semver tag sets."""
        git = dag.git(source=self.repo_with_version_tags())

        latest_semver = await git.get_latest_tag(pattern="v*")
        latest_v1 = await git.get_latest_tag(pattern="v1.*")
        latest_plain_semver = await git.get_latest_tag(pattern="[0-9]*")
        latest_module = await git.get_latest_tag(pattern="modules/helm/*")
        latest_module_v1 = await git.get_latest_tag(pattern="modules/helm/v1.*")
        latest_plain_module = await git.get_latest_tag(pattern="modules/plain/*")
        latest_non_semver = await git.get_latest_tag(pattern="release-*", semver=False)
        no_semver_match = await git.get_latest_tag(pattern="release-*")
        no_match = await git.get_latest_tag(pattern="missing-*", semver=False)

        test_case = TestCase()
        test_case.assertEqual("v2.0.0", latest_semver)
        test_case.assertEqual("v1.10.0", latest_v1)
        test_case.assertEqual("3.0.0", latest_plain_semver)
        test_case.assertEqual("modules/helm/v2.0.0", latest_module)
        test_case.assertEqual("modules/helm/v1.10.0", latest_module_v1)
        test_case.assertEqual("modules/plain/1.10.0", latest_plain_module)
        test_case.assertEqual("release-2024.10", latest_non_semver)
        test_case.assertEqual("", no_semver_match)
        test_case.assertEqual("", no_match)

    async def tags_pointing_at(self) -> None:
        """Return tags that point at HEAD and non-HEAD refs."""
        git = dag.git(source=self.repo_with_tags_on_multiple_refs())

        head_tags = await git.get_tags_pointing_at()
        first_commit_tags = await git.get_tags_pointing_at(ref="HEAD~1")

        test_case = TestCase()
        test_case.assertEqual(["head", "v2.0.0"], head_tags)
        test_case.assertEqual(["first", "v1.0.0"], first_commit_tags)

    async def create_lightweight_tag(self) -> None:
        """Create a lightweight tag on HEAD."""
        git = dag.git(source=self.repo_with_local_tag()).create_tag(tag="v1.1.0")

        tag_type = await git.container().with_exec(["git", "cat-file", "-t", "v1.1.0"]).stdout()
        pointed_sha = await git.container().with_exec(["git", "rev-parse", "v1.1.0"]).stdout()
        head_sha = await git.container().with_exec(["git", "rev-parse", "HEAD"]).stdout()

        test_case = TestCase()
        test_case.assertTrue(await git.has_tag(tag="v1.1.0"))
        test_case.assertEqual("commit", tag_type.strip())
        test_case.assertEqual(head_sha.strip(), pointed_sha.strip())

    async def create_annotated_tag(self) -> None:
        """Create an annotated tag on HEAD with tagger metadata."""
        git = dag.git(source=self.repo_with_local_tag()).create_tag(
            tag="v1.1.0",
            message="Release v1.1.0",
            user_name="Release Bot",
            user_email="release@example.local",
        )

        tag_type = await git.container().with_exec(["git", "cat-file", "-t", "v1.1.0"]).stdout()
        tag_metadata = (
            await git.container()
            .with_exec(
                [
                    "git",
                    "for-each-ref",
                    "refs/tags/v1.1.0",
                    "--format=%(taggername)|%(taggeremail)|%(contents:subject)",
                ]
            )
            .stdout()
        )

        test_case = TestCase()
        test_case.assertTrue(await git.has_tag(tag="v1.1.0"))
        test_case.assertEqual("tag", tag_type.strip())
        test_case.assertEqual("Release Bot|<release@example.local>|Release v1.1.0", tag_metadata.strip())

    async def push_tag_to_local_bare_remote(self) -> None:
        """Push a local tag to a local bare remote."""
        git = dag.git(source=self.repo_with_remote_tag())

        before_push = (
            await git.container().with_exec(["git", "ls-remote", "--tags", "origin", "refs/tags/v1.1.0"]).stdout()
        )

        pushed_git = git.create_tag(tag="v1.1.0").push_tag(tag="v1.1.0")
        after_push = (
            await pushed_git.container()
            .with_exec(["git", "ls-remote", "--tags", "origin", "refs/tags/v1.1.0"])
            .stdout()
        )
        local_sha = await pushed_git.container().with_exec(["git", "rev-parse", "v1.1.0"]).stdout()

        test_case = TestCase()
        test_case.assertEqual("", before_push.strip())
        test_case.assertIn(local_sha.strip(), after_push)
        test_case.assertIn("refs/tags/v1.1.0", after_push)
