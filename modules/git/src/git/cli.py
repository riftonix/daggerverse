from __future__ import annotations

import dagger
from dagger import dag


class GitCli:
    """Internal Git CLI container state."""

    def __init__(
        self,
        source: dagger.Directory,
        image_registry: str,
        image_repository: str,
        image_tag: str,
        user_id: str,
        container_: dagger.Container | None = None,
    ) -> None:
        self.source = source
        self.image_registry = image_registry
        self.image_repository = image_repository
        self.image_tag = image_tag
        self.user_id = user_id
        self.container_ = container_

    def container(self) -> dagger.Container:
        """Create the configured Git container for a repository source."""
        if self.container_:
            return self.container_

        self.container_ = (
            dag.container()
            .from_(address=f"{self.image_registry}/{self.image_repository}:{self.image_tag}")
            .with_env_variable("USER_ID", self.user_id)
            .with_env_variable("USER_NAME", "git")
            .with_user("0")
            .with_exec(
                [
                    "sh",
                    "-c",
                    (
                        'getent passwd "$USER_ID" >/dev/null 2>&1 || '
                        'printf "$USER_NAME:x:%s:%s:$USER_NAME:/home/$USER_NAME:/sbin/nologin\\n" '
                        '"$USER_ID" "$USER_ID" >> /etc/passwd; '
                        'getent group "$USER_ID" >/dev/null 2>&1 || '
                        'echo "$USER_NAME:x:$USER_ID:" >> /etc/group; '
                        'install -d -m 700 -o "$USER_ID" -g "$USER_ID" '
                        '"/home/$USER_NAME"'
                    ),
                ],
                expand=True,
            )
            .with_user(self.user_id)
            .with_env_variable("HOME", "/home/git")
            .with_env_variable("GIT_REPO_PATH", "/tmp/git/repo")
            .with_exec(["mkdir", "-p", "-m", "770", "$GIT_REPO_PATH"], expand=True)
            .with_directory("$GIT_REPO_PATH", self.source, owner=self.user_id, expand=True)
            .with_workdir("$GIT_REPO_PATH", expand=True)
            .with_exec(
                [
                    "sh",
                    "-c",
                    'git status --porcelain >/dev/null 2>&1 || (echo "Path $GIT_REPO_PATH is not a git repo" >&2; exit 1)',
                ],
                expand=True,
            )
            .with_exec(["git", "config", "--local", "safe.directory", "$GIT_REPO_PATH"], expand=True)
        )
        return self.container_
