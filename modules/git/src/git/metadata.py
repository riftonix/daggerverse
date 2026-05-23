from __future__ import annotations

from .cli import GitCli


class Metadata:
    """Repository metadata operations for the Git Dagger facade."""

    def __init__(self, git: GitCli) -> None:
        self.git = git

    async def get_short_commit_sha(self, length: int | None) -> str:
        return await self.git.container().with_exec(["git", "rev-parse", f"--short={length}", "HEAD"]).stdout()
