from __future__ import annotations

import dagger

from .cli import GitCli


class Auth:
    """Authentication operations for the Git Dagger facade."""

    def __init__(self, git: GitCli) -> None:
        self.git = git

    async def with_ssh_private_key(self, source: dagger.File) -> str:
        container = (
            self.git.container()
            .with_env_variable("SSH_PRIVATE_KEY_PATH", "$HOME/.ssh/id_rsa", expand=True)
            .with_file("$SSH_PRIVATE_KEY_PATH", source=source, owner=self.git.user_id, permissions=600, expand=True)
            .with_exec(["ls", "-lah", "$HOME/.ssh"], expand=True)
        )
        return await container.stdout()
