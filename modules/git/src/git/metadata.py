from __future__ import annotations

from .cli import GitCli


class Metadata:
    """Repository metadata operations for the Git Dagger facade."""

    def __init__(self, git: GitCli) -> None:
        self.git = git

    async def get_head_sha(self) -> str:
        return await self.git.container().with_exec(["git", "rev-parse", "HEAD"]).stdout()

    async def get_short_commit_sha(self, length: int | None) -> str:
        return await self.git.container().with_exec(["git", "rev-parse", f"--short={length}", "HEAD"]).stdout()

    async def get_current_branch(self) -> str:
        return await self.git.container().with_exec(["git", "branch", "--show-current"]).stdout()

    async def get_current_ref(self) -> str:
        return (
            await self.git.container()
            .with_exec(["sh", "-c", "git symbolic-ref --quiet HEAD || git rev-parse HEAD"])
            .stdout()
        )

    async def get_remote_url(self, remote: str) -> str:
        return await self.git.container().with_exec(["git", "remote", "get-url", remote]).stdout()

    async def get_default_branch(self, remote: str) -> str:
        return (
            await self.git.container()
            .with_exec(
                [
                    "sh",
                    "-c",
                    'git ls-remote --symref "$1" HEAD | awk \'/^ref:/ { sub("^refs/heads/", "", $2); print $2; exit }\'',
                    "sh",
                    remote,
                ]
            )
            .stdout()
        )

    async def get_status_porcelain(self) -> str:
        return await self.git.container().with_exec(["git", "status", "--porcelain"]).stdout()

    async def has_clean_worktree(self) -> bool:
        status = await self.get_status_porcelain()
        return status.strip() == ""
