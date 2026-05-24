from unittest import TestCase

from dagger import dag

from .fixtures import SyntheticGitRepos


class ComponentTests(SyntheticGitRepos):
    """Component discovery behavior tests."""

    async def all(self) -> None:
        await self.components_from_explicit_roots()
        await self.components_from_glob_like_roots()

    async def components_from_explicit_roots(self) -> None:
        """Return existing explicit component roots in stable sorted order."""
        git = dag.git(source=self.repo_with_components().directory("/work/repo"))

        components = await git.get_components(
            component_roots=[
                "services/web",
                "services/missing",
                "services/api",
                "./packages/shared/",
                "services/api",
            ]
        )

        test_case = TestCase()
        test_case.assertEqual(["packages/shared", "services/api", "services/web"], components)

    async def components_from_glob_like_roots(self) -> None:
        """Return component roots discovered from glob-like patterns."""
        git = dag.git(source=self.repo_with_components().directory("/work/repo"))

        components = await git.get_components(component_roots=["services/*", "packages/*", "deploy/*"])
        nested_components = await git.get_components(component_roots=["environments/*/apps/*"])

        test_case = TestCase()
        test_case.assertEqual(["packages/shared", "services/api", "services/web"], components)
        test_case.assertEqual(["environments/dev/apps/api", "environments/prod/apps/api"], nested_components)
