from unittest import TestCase

from dagger import dag

from .fixtures import SyntheticGitRepos


class ComponentTests(SyntheticGitRepos):
    """Component discovery behavior tests."""

    async def all(self) -> None:
        await self.components_from_explicit_roots()
        await self.components_from_glob_like_roots()
        await self.changed_components_from_component_roots()
        await self.shared_path_change_returns_all_components()

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

    async def changed_components_from_component_roots(self) -> None:
        """Return discovered components whose files changed between refs."""
        git = dag.git(source=self.repo_with_changed_components().directory("/work/repo"))

        explicit_components = await git.get_changed_components(
            base_ref="main",
            head_ref="feature",
            component_roots=["services/api", "services/web", "packages/shared"],
        )
        glob_components = await git.get_changed_components(
            base_ref="main",
            head_ref="feature",
            component_roots=["services/*", "packages/*"],
        )
        unchanged_components = await git.get_changed_components(
            base_ref="main",
            head_ref="feature",
            component_roots=["services/web"],
        )

        test_case = TestCase()
        test_case.assertEqual(["packages/shared", "services/api"], explicit_components)
        test_case.assertEqual(["packages/shared", "services/api"], glob_components)
        test_case.assertEqual([], unchanged_components)

    async def shared_path_change_returns_all_components(self) -> None:
        """Return all discovered components when a shared path changes."""
        git = dag.git(source=self.repo_with_shared_path_change().directory("/work/repo"))

        components = await git.get_changed_components(
            base_ref="main",
            head_ref="feature",
            component_roots=["services/*", "packages/*"],
            shared_paths=["shared"],
        )
        file_components = await git.get_changed_components(
            base_ref="main",
            head_ref="feature",
            component_roots=["services/api", "services/web", "packages/shared"],
            shared_paths=["shared/config.yaml"],
        )

        test_case = TestCase()
        test_case.assertEqual(["packages/shared", "services/api", "services/web"], components)
        test_case.assertEqual(["packages/shared", "services/api", "services/web"], file_components)
