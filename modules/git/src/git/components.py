from __future__ import annotations

from fnmatch import fnmatchcase

import dagger

from .cli import GitCli
from .paths import normalize_path


class Components:
    """Component discovery operations for the Git Dagger facade."""

    def __init__(self, git: GitCli) -> None:
        self.git = git

    async def get_components(self, component_roots: list[str]) -> list[str]:
        normalized_roots = [normalize_path(root) for root in component_roots]
        components: set[str] = set()

        for root in normalized_roots:
            if has_glob_meta(root):
                components.update(await self._get_matching_directories(root))
            elif await self._is_directory(root):
                components.add(root)

        return sorted(components)

    async def get_changed_components(
        self,
        base_ref: str,
        head_ref: str,
        component_roots: list[str],
        shared_paths: list[str] | None,
        single_component: bool | None,
    ) -> list[str]:
        _ = single_component
        components = await self.get_components(component_roots=component_roots)
        if not components:
            return []

        changed_files = await self._get_changed_files(base_ref=base_ref, head_ref=head_ref)
        normalized_shared_paths = [normalize_path(path) for path in shared_paths or []]
        if any(
            path_matches_root(path, shared_path) for path in changed_files for shared_path in normalized_shared_paths
        ):
            return components

        changed_components = {
            component for component in components if any(path_matches_root(path, component) for path in changed_files)
        }
        return sorted(changed_components)

    async def _get_matching_directories(self, pattern: str) -> list[str]:
        output = await self.git.container().with_exec(["git", "ls-files", "-z", "--", pattern]).stdout()
        files = [path for path in output.split("\0") if path]
        return sorted(
            {matching_component_root(path, pattern) for path in files if matching_component_root(path, pattern)}
        )

    async def _is_directory(self, path: str) -> bool:
        if path == ".":
            return True

        cmd = ["sh", "-c", 'test -d "$1"', "is-directory", path]
        try:
            await self.git.container().with_exec(cmd).sync()
            return True
        except dagger.ExecError:
            return False

    async def _get_changed_files(self, base_ref: str, head_ref: str) -> list[str]:
        cmd = [
            "git",
            "diff",
            "--name-only",
            "--find-renames",
            "--find-copies",
            "--find-copies-harder",
            "--diff-filter=ACMRTUXB",
            base_ref,
            head_ref,
        ]
        output = await self.git.container().with_exec(cmd).stdout()
        return [line.strip() for line in output.splitlines() if line.strip()]


def has_glob_meta(pattern: str) -> bool:
    return any(char in pattern for char in "*?[")


def matching_component_root(path: str, pattern: str) -> str | None:
    pattern_parts = normalize_path(pattern).split("/")
    path_parts = normalize_path(path).split("/")

    if len(path_parts) < len(pattern_parts):
        return None

    for pattern_part, path_part in zip(pattern_parts, path_parts, strict=False):
        if has_glob_meta(pattern_part):
            if not fnmatchcase(path_part, pattern_part):
                return None
            continue
        if path_part != pattern_part:
            return None

    return "/".join(path_parts[: len(pattern_parts)])


def path_matches_root(path: str, root: str) -> bool:
    normalized_path = normalize_path(path)
    normalized_root = normalize_path(root)
    return normalized_path == normalized_root or normalized_path.startswith(f"{normalized_root}/")
