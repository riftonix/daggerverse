from __future__ import annotations

from .cli import GitCli


class FilesAtRef:
    """Files-at-ref operations for the Git Dagger facade."""

    def __init__(self, git: GitCli) -> None:
        self.git = git
