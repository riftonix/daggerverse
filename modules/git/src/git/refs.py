from __future__ import annotations

from .cli import GitCli


class Refs:
    """Ref and fetch operations for the Git Dagger facade."""

    def __init__(self, git: GitCli) -> None:
        self.git = git

    async def get_merge_base(self, base_ref: str, head_ref: str) -> str:
        output = await self.git.container().with_exec(["git", "merge-base", base_ref, head_ref]).stdout()
        return output.strip()

    async def ensure_ref(self, ref: str) -> str:
        cmd = [
            "sh",
            "-c",
            'git rev-parse --verify --quiet "$1" || { printf "Git ref not found: %s\\n" "$1" >&2; exit 1; }',
            "ensure-ref",
            ref,
        ]
        output = await self.git.container().with_exec(cmd).stdout()
        return output.strip()

    def with_fetched_refs(
        self,
        remote: str,
        refspecs: list[str] | None,
        depth: int | None,
        prune: bool | None,
    ) -> GitCli:
        cmd = ["git", "fetch"]
        if prune:
            cmd.append("--prune")
        if depth is not None:
            cmd.extend(["--depth", str(depth)])
        cmd.append(remote)
        if refspecs:
            cmd.extend(refspecs)

        self.git.container_ = self.git.container().with_exec(cmd)
        return self.git

    def with_unshallow(self, remote: str) -> GitCli:
        cmd = [
            "sh",
            "-c",
            (
                'if [ "$(git rev-parse --is-shallow-repository)" = "true" ]; then '
                'git fetch --unshallow "$1"; '
                "else "
                'git fetch "$1"; '
                "fi"
            ),
            "with-unshallow",
            remote,
        ]
        self.git.container_ = self.git.container().with_exec(cmd)
        return self.git
