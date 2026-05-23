from __future__ import annotations

from .cli import GitCli


class Components:
    """Component discovery operations for the Git Dagger facade."""

    def __init__(self, git: GitCli) -> None:
        self.git = git
