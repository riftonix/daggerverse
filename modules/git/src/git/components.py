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
