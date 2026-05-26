from __future__ import annotations

from .cli import GitCli


class FilesAtRef:
    """Files-at-ref operations for the Git Dagger facade."""

    def __init__(self, git: GitCli) -> None:
        self.git = git

    async def has_file_at_ref(self, ref: str, path: str) -> bool:
        result = (
            await self.git.container()
            .with_exec(
                [
                    "sh",
                    "-c",
                    'if test "$(git cat-file -t "$1:$2" 2>/dev/null)" = blob; then printf "true\\n"; else printf "false\\n"; fi',
                    "sh",
                    ref,
                    path,
                ]
            )
            .stdout()
        )
        return result.strip() == "true"

    async def get_file_contents_at_ref(self, ref: str, path: str) -> str:
        return (
            await self.git.container()
            .with_exec(
                [
                    "sh",
                    "-c",
                    'git show "$1:$2"',
                    "sh",
                    ref,
                    path,
                ]
            )
            .stdout()
        )
