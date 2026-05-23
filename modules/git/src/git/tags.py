from __future__ import annotations

from .cli import GitCli


class Tags:
    """Tag operations for the Git Dagger facade."""

    def __init__(self, git: GitCli) -> None:
        self.git = git

    def with_fetched_tags(self, remote: str, prune: bool | None) -> GitCli:
        cmd = ["git", "fetch", "--tags", remote]
        if prune:
            cmd.insert(2, "--prune")
        self.git.container_ = self.git.container().with_exec(cmd)
        return self.git

    async def get_tags(self, pattern: str) -> list[str]:
        output = (
            await self.git.container().with_exec(["git", "tag", "--list", pattern, "--sort=version:refname"]).stdout()
        )
        return [line.strip() for line in output.splitlines() if line.strip()]

    async def get_tags_pointing_at(self, ref: str, remote: str) -> list[str]:
        self.with_fetched_tags(remote=remote, prune=False)
        output = await self.git.container().with_exec(["git", "tag", "--points-at", ref]).stdout()
        return [line.strip() for line in output.splitlines() if line.strip()]
