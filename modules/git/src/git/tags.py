from __future__ import annotations

import re

import dagger

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

    async def get_tags(self, pattern: str, sort: str) -> list[str]:
        output = (
            await self.git.container().with_exec(["git", "tag", "--list", pattern, f"--sort={tag_sort(sort)}"]).stdout()
        )
        return [line.strip() for line in output.splitlines() if line.strip()]

    async def has_tag(self, tag: str) -> bool:
        try:
            await self.git.container().with_exec(["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"]).sync()
            return True
        except dagger.ExecError:
            return False

    async def get_latest_tag(self, pattern: str, semver: bool | None) -> str:
        tags = await self.get_tags(pattern=pattern, sort="version")
        if not tags:
            return ""
        if not semver:
            return tags[-1]

        semver_tags = [(tag, version) for tag in tags if (version := parse_semver_tag(tag))]
        if not semver_tags:
            return ""
        return max(semver_tags, key=lambda item: item[1])[0]

    async def get_tags_pointing_at(self, ref: str) -> list[str]:
        output = (
            await self.git.container().with_exec(["git", "tag", "--points-at", ref, "--sort=version:refname"]).stdout()
        )
        return [line.strip() for line in output.splitlines() if line.strip()]

    async def ensure_pushed_tag(self, tag: str, remote: str) -> str:
        self.with_fetched_tags(remote=remote, prune=False)
        if await self.has_tag(tag=tag):
            return tag

        self.create_tag(
            tag=tag,
            message=None,
            user_name="dagger-ci",
            user_email="dagger-ci@example.local",
        )
        self.push_tag(tag=tag, remote=remote)
        await (
            self.git.container()
            .with_exec(["git", "ls-remote", "--exit-code", "--tags", remote, f"refs/tags/{tag}"])
            .sync()
        )
        return tag

    def create_tag(self, tag: str, message: str | None, user_name: str, user_email: str) -> GitCli:
        cmd = ["git", "tag", tag]
        if message is not None:
            cmd = [
                "git",
                "-c",
                f"user.name={user_name}",
                "-c",
                f"user.email={user_email}",
                "tag",
                "-a",
                tag,
                "-m",
                message,
            ]

        self.git.container_ = self.git.container().with_exec(cmd)
        return self.git

    def push_tag(self, tag: str, remote: str) -> GitCli:
        self.git.container_ = self.git.container().with_exec(["git", "push", remote, tag])
        return self.git


def tag_sort(sort: str) -> str:
    sort_key = sort.strip() or "version"
    descending = sort_key.startswith("-")
    if descending:
        sort_key = sort_key[1:]

    aliases = {
        "version": "version:refname",
        "name": "refname",
        "refname": "refname",
    }
    git_sort = aliases.get(sort_key, sort_key)
    if descending:
        return f"-{git_sort}"
    return git_sort


SEMVER_TAG_PATTERN = re.compile(
    r"^v?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$"
)


def parse_semver_tag(tag: str) -> tuple[int, int, int, tuple[int | str, ...]] | None:
    version_text = tag.rsplit("/", maxsplit=1)[-1]
    match = SEMVER_TAG_PATTERN.fullmatch(version_text)
    if not match:
        return None

    prerelease = match.group("prerelease")
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        prerelease_key(prerelease),
    )


def prerelease_key(prerelease: str | None) -> tuple[int | str, ...]:
    if prerelease is None:
        return (1,)

    parts: list[int | str] = [0]
    for part in prerelease.split("."):
        if part.isdigit():
            parts.extend((0, int(part)))
        else:
            parts.extend((1, part))
    return tuple(parts)
