from __future__ import annotations

import dagger

from .cli import GitCli


class Auth:
    """Authentication operations for the Git Dagger facade."""

    def __init__(self, git: GitCli) -> None:
        self.git = git

    def with_https_token_auth(
        self,
        host: str,
        token: dagger.Secret,
        username: str | None,
    ) -> GitCli:
        normalized_host = normalize_https_host(host)
        auth_username = username or "oauth2"
        askpass_path = "$HOME/.local/bin/git-askpass"
        askpass_script = """#!/bin/sh
case "$1" in
  *Username*) printf '%s\\n' "$GIT_HTTPS_USERNAME" ;;
  *) printf '%s\\n' "$GIT_HTTPS_TOKEN" ;;
esac
"""

        self.git.container_ = (
            self.git.container()
            .with_env_variable("GIT_HTTPS_HOST", normalized_host)
            .with_env_variable("GIT_HTTPS_USERNAME", auth_username)
            .with_secret_variable("GIT_HTTPS_TOKEN", token)
            .with_env_variable("GIT_ASKPASS", askpass_path, expand=True)
            .with_env_variable("GIT_TERMINAL_PROMPT", "0")
            .with_exec(["mkdir", "-p", "$HOME/.local/bin"], expand=True)
            .with_new_file(
                askpass_path,
                contents=askpass_script,
                owner=self.git.user_id,
                permissions=0o700,
                expand=True,
            )
            .with_exec(["git", "config", "--global", f"credential.https://{normalized_host}.username", auth_username])
        )
        return self.git

    def with_ssh_key_auth(
        self,
        private_key: dagger.Secret,
        known_hosts: dagger.Secret,
        host: str | None,
    ) -> GitCli:
        ssh_dir = "$HOME/.ssh"
        key_path = "$HOME/.ssh/id_ed25519"
        known_hosts_path = "$HOME/.ssh/known_hosts"
        ssh_command = (
            "ssh -i $HOME/.ssh/id_ed25519 "
            "-o UserKnownHostsFile=$HOME/.ssh/known_hosts "
            "-o IdentitiesOnly=yes "
            "-o StrictHostKeyChecking=yes"
        )

        container = (
            self.git.container()
            .with_exec(["mkdir", "-p", ssh_dir], expand=True)
            .with_mounted_secret(key_path, private_key, owner=self.git.user_id, mode=0o600, expand=True)
            .with_mounted_secret(known_hosts_path, known_hosts, owner=self.git.user_id, mode=0o644, expand=True)
            .with_env_variable("GIT_SSH_COMMAND", ssh_command, expand=True)
        )

        if host:
            normalized_host = normalize_ssh_host(host)
            config = (
                f"Host {normalized_host}\n"
                f"  HostName {normalized_host}\n"
                "  IdentityFile ~/.ssh/id_ed25519\n"
                "  UserKnownHostsFile ~/.ssh/known_hosts\n"
                "  IdentitiesOnly yes\n"
                "  StrictHostKeyChecking yes\n"
            )
            container = container.with_new_file(
                "$HOME/.ssh/config",
                contents=config,
                owner=self.git.user_id,
                permissions=0o600,
                expand=True,
            )

        self.git.container_ = container
        return self.git


def normalize_https_host(host: str) -> str:
    normalized = host.strip()
    if normalized.startswith("https://"):
        normalized = normalized.removeprefix("https://")
    elif normalized.startswith("http://"):
        normalized = normalized.removeprefix("http://")
    if "@" in normalized:
        normalized = normalized.rsplit("@", maxsplit=1)[-1]
    return normalized.split("/", maxsplit=1)[0].rstrip("/")


def normalize_ssh_host(host: str) -> str:
    normalized = host.strip()
    if normalized.startswith("ssh://"):
        normalized = normalized.removeprefix("ssh://")
    if "@" in normalized:
        normalized = normalized.rsplit("@", maxsplit=1)[-1]
    if ":" in normalized and "/" in normalized and normalized.index(":") < normalized.index("/"):
        normalized = normalized.split(":", maxsplit=1)[0]
    return normalized.split("/", maxsplit=1)[0].rstrip("/")
