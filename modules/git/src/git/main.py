from typing import Annotated, Self

import dagger
from dagger import DefaultPath, Doc, function, object_type

from .auth import Auth
from .cli import GitCli
from .components import Components
from .diffs import Diffs
from .files_at_ref import FilesAtRef
from .metadata import Metadata
from .refs import Refs
from .tags import Tags


@object_type
class Git:
    source: dagger.Directory
    image_registry: str
    image_repository: str
    image_tag: str
    user_id: str
    container_: dagger.Container | None

    def _git(self) -> GitCli:
        return GitCli(
            source=self.source,
            image_registry=self.image_registry,
            image_repository=self.image_repository,
            image_tag=self.image_tag,
            user_id=self.user_id,
            container_=self.container_,
        )

    @classmethod
    async def create(
        cls,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Git repository directory (must include .git)")],
        image_registry: Annotated[str | None, Doc("Git image registry")] = "docker.io",
        image_repository: Annotated[str | None, Doc("Git image repositroy")] = "alpine/git",
        image_tag: Annotated[str | None, Doc("Git image tag")] = "2.52.0",
        user_id: Annotated[str | None, Doc("Git image user")] = "65532",
    ):
        """Constructor"""
        return cls(
            source=source,
            image_registry=image_registry,
            image_repository=image_repository,
            image_tag=image_tag,
            user_id=user_id,
            container_=None,
        )

    @function
    def container(self) -> dagger.Container:
        """Creates container with configured git"""
        git = self._git()
        container = git.container()
        self.container_ = git.container_
        return container

    @function
    async def with_https_token_auth(
        self,
        host: Annotated[str, Doc("HTTPS Git host to authenticate against")],
        token: Annotated[dagger.Secret, Doc("HTTPS token secret")],
        username: Annotated[str | None, Doc("Optional HTTPS username")] = None,
    ) -> Self:
        """Configure HTTPS token authentication for Git operations."""
        self.container_ = (
            Auth(self._git())
            .with_https_token_auth(
                host=host,
                token=token,
                username=username,
            )
            .container_
        )
        return self

    @function
    async def with_ssh_key_auth(
        self,
        private_key: Annotated[dagger.Secret, Doc("SSH private key secret")],
        known_hosts: Annotated[dagger.Secret, Doc("SSH known_hosts secret")],
        host: Annotated[str | None, Doc("Optional SSH Git host to configure")] = None,
    ) -> Self:
        """Configure SSH key authentication for Git operations."""
        self.container_ = (
            Auth(self._git())
            .with_ssh_key_auth(
                private_key=private_key,
                known_hosts=known_hosts,
                host=host,
            )
            .container_
        )
        return self

    @function
    async def get_changed_paths(
        self,
        target_branch: Annotated[str, Doc("Target branch or ref to diff against")] = "master",
        diff_path: Annotated[str | None, Doc("Path to scope the diff (relative to repo root)")] = ".",
    ) -> list[str]:
        """Return changed paths inside diff_path between target_branch and HEAD"""
        return await Diffs(self._git()).get_changed_paths(target_branch=target_branch, diff_path=diff_path)

    @function
    async def get_merge_base(
        self,
        base_ref: Annotated[str, Doc("Base Git ref or SHA")],
        head_ref: Annotated[str, Doc("Head Git ref or SHA")],
    ) -> str:
        """Return the merge-base commit shared by two refs."""
        return await Refs(self._git()).get_merge_base(base_ref=base_ref, head_ref=head_ref)

    @function
    async def get_changed_files(
        self,
        base_ref: Annotated[str, Doc("Base Git ref or SHA")],
        head_ref: Annotated[str, Doc("Head Git ref or SHA")],
        paths: Annotated[list[str] | None, Doc("Optional path filters relative to the repository root")] = None,
        diff_filter: Annotated[str, Doc("Git diff-filter status letters")] = "ACMRTUXB",
    ) -> list[str]:
        """Return changed file paths between two refs."""
        return await Diffs(self._git()).get_changed_files(
            base_ref=base_ref,
            head_ref=head_ref,
            paths=paths,
            diff_filter=diff_filter,
        )

    @function
    async def get_changed_files_since_merge_base(
        self,
        base_ref: Annotated[str, Doc("Base Git ref or SHA")],
        head_ref: Annotated[str, Doc("Head Git ref or SHA")] = "HEAD",
        paths: Annotated[list[str] | None, Doc("Optional path filters relative to the repository root")] = None,
        diff_filter: Annotated[str, Doc("Git diff-filter status letters")] = "ACMRTUXB",
    ) -> list[str]:
        """Return changed file paths from the merge base of base_ref and head_ref to head_ref."""
        return await Diffs(self._git()).get_changed_files_since_merge_base(
            base_ref=base_ref,
            head_ref=head_ref,
            paths=paths,
            diff_filter=diff_filter,
        )

    @function
    async def get_changed_dirs(
        self,
        base_ref: Annotated[str, Doc("Base Git ref or SHA")],
        head_ref: Annotated[str, Doc("Head Git ref or SHA")],
        paths: Annotated[list[str] | None, Doc("Optional path filters relative to the repository root")] = None,
        depth: Annotated[int, Doc("Directory depth to return")] = 1,
        diff_filter: Annotated[str, Doc("Git diff-filter status letters")] = "ACMRTUXB",
    ) -> list[str]:
        """Return unique changed directories between two refs."""
        return await Diffs(self._git()).get_changed_dirs(
            base_ref=base_ref,
            head_ref=head_ref,
            paths=paths,
            depth=depth,
            diff_filter=diff_filter,
        )

    @function
    async def get_changed_dirs_since_merge_base(
        self,
        base_ref: Annotated[str, Doc("Base Git ref or SHA")],
        head_ref: Annotated[str, Doc("Head Git ref or SHA")] = "HEAD",
        paths: Annotated[list[str] | None, Doc("Optional path filters relative to the repository root")] = None,
        depth: Annotated[int, Doc("Directory depth to return")] = 1,
        diff_filter: Annotated[str, Doc("Git diff-filter status letters")] = "ACMRTUXB",
    ) -> list[str]:
        """Return unique changed directories from the merge base of base_ref and head_ref to head_ref."""
        return await Diffs(self._git()).get_changed_dirs_since_merge_base(
            base_ref=base_ref,
            head_ref=head_ref,
            paths=paths,
            depth=depth,
            diff_filter=diff_filter,
        )

    @function
    async def has_changes(
        self,
        base_ref: Annotated[str, Doc("Base Git ref or SHA")],
        head_ref: Annotated[str, Doc("Head Git ref or SHA")],
        paths: Annotated[list[str] | None, Doc("Optional path filters relative to the repository root")] = None,
        diff_filter: Annotated[str, Doc("Git diff-filter status letters")] = "ACMRTUXB",
    ) -> bool:
        """Return whether any files changed between two refs."""
        return await Diffs(self._git()).has_changes(
            base_ref=base_ref,
            head_ref=head_ref,
            paths=paths,
            diff_filter=diff_filter,
        )

    @function
    async def get_components(
        self,
        component_roots: Annotated[list[str], Doc("Component root directories or glob-like patterns")],
    ) -> list[str]:
        """Return discovered component roots in stable sorted order."""
        return await Components(self._git()).get_components(component_roots=component_roots)

    @function
    async def get_changed_components(
        self,
        base_ref: Annotated[str, Doc("Base Git ref or SHA")],
        head_ref: Annotated[str, Doc("Head Git ref or SHA")],
        component_roots: Annotated[list[str], Doc("Component root directories or glob-like patterns")],
        shared_paths: Annotated[list[str] | None, Doc("Paths that affect all components")] = None,
        single_component: Annotated[bool | None, Doc("Treat repository as one component")] = False,
    ) -> list[str]:
        """Return discovered components whose files changed between two refs."""
        return await Components(self._git()).get_changed_components(
            base_ref=base_ref,
            head_ref=head_ref,
            component_roots=component_roots,
            shared_paths=shared_paths,
            single_component=single_component,
        )

    @function
    async def with_fetched_tags(
        self,
        remote: Annotated[str, Doc("Remote name to fetch tags from")] = "origin",
        prune: Annotated[bool | None, Doc("Prune deleted tags")] = False,
    ) -> Self:
        """Fetch tags from remote."""
        self.container_ = Tags(self._git()).with_fetched_tags(remote=remote, prune=prune).container_
        return self

    @function
    async def with_fetched_refs(
        self,
        remote: Annotated[str, Doc("Remote name to fetch refs from")] = "origin",
        refspecs: Annotated[list[str] | None, Doc("Optional refspecs to fetch")] = None,
        depth: Annotated[int | None, Doc("Optional shallow fetch depth")] = None,
        prune: Annotated[bool | None, Doc("Prune deleted remote-tracking refs")] = False,
    ) -> Self:
        """Fetch refs from remote and keep them available for later Git calls."""
        self.container_ = (
            Refs(self._git())
            .with_fetched_refs(
                remote=remote,
                refspecs=refspecs,
                depth=depth,
                prune=prune,
            )
            .container_
        )
        return self

    @function
    async def with_unshallow(
        self,
        remote: Annotated[str, Doc("Remote name to fetch full history from")] = "origin",
    ) -> Self:
        """Ensure a shallow repository has full history for later Git calls."""
        self.container_ = Refs(self._git()).with_unshallow(remote=remote).container_
        return self

    @function
    async def ensure_ref(
        self,
        ref: Annotated[str, Doc("Git ref or SHA to resolve")],
    ) -> str:
        """Resolve a ref or fail with a clear missing-ref error."""
        return await Refs(self._git()).ensure_ref(ref=ref)

    @function
    async def get_tags(
        self,
        pattern: Annotated[str, Doc("Optional tag filter pattern (glob)")] = "*",
        sort: Annotated[str, Doc("Tag sort key: version, refname, or any git tag sort key")] = "version",
    ) -> list[str]:
        """Return tags in the repository, optionally filtered by glob pattern."""
        return await Tags(self._git()).get_tags(pattern=pattern, sort=sort)

    @function
    async def has_tag(
        self,
        tag: Annotated[str, Doc("Tag name to check")],
    ) -> bool:
        """Return whether a tag exists in the repository."""
        return await Tags(self._git()).has_tag(tag=tag)

    @function
    async def get_latest_tag(
        self,
        pattern: Annotated[str, Doc("Optional tag filter pattern (glob)")] = "*",
        semver: Annotated[bool | None, Doc("Only consider semantic version tags")] = True,
    ) -> str:
        """Return the latest matching tag, or an empty string when none match."""
        return await Tags(self._git()).get_latest_tag(pattern=pattern, semver=semver)

    @function
    async def get_short_commit_sha(
        self,
        length: Annotated[int | None, Doc("Length of the short SHA")] = 8,
    ) -> str:
        """Return short commit SHA for HEAD"""
        return await Metadata(self._git()).get_short_commit_sha(length=length)

    @function
    async def get_head_sha(self) -> str:
        """Return full commit SHA for HEAD."""
        return await Metadata(self._git()).get_head_sha()

    @function
    async def get_current_branch(self) -> str:
        """Return the current branch name, or an empty string for detached HEAD."""
        return await Metadata(self._git()).get_current_branch()

    @function
    async def get_current_ref(self) -> str:
        """Return the current symbolic ref, or the full HEAD SHA for detached HEAD."""
        return await Metadata(self._git()).get_current_ref()

    @function
    async def get_remote_url(
        self,
        remote: Annotated[str, Doc("Remote name")] = "origin",
    ) -> str:
        """Return the configured URL for a remote."""
        return await Metadata(self._git()).get_remote_url(remote=remote)

    @function
    async def get_default_branch(
        self,
        remote: Annotated[str, Doc("Remote name")] = "origin",
    ) -> str:
        """Return the remote default branch name."""
        return await Metadata(self._git()).get_default_branch(remote=remote)

    @function
    async def get_status_porcelain(self) -> str:
        """Return git status in porcelain format."""
        return await Metadata(self._git()).get_status_porcelain()

    @function
    async def has_clean_worktree(self) -> bool:
        """Return whether the repository worktree has no pending changes."""
        return await Metadata(self._git()).has_clean_worktree()

    @function
    async def has_file_at_ref(
        self,
        ref: Annotated[str, Doc("Git ref or SHA to inspect")],
        path: Annotated[str, Doc("File path relative to the repository root")],
    ) -> bool:
        """Return whether a file exists at a Git ref."""
        return await FilesAtRef(self._git()).has_file_at_ref(ref=ref, path=path)

    @function
    async def get_file_contents_at_ref(
        self,
        ref: Annotated[str, Doc("Git ref or SHA to read from")],
        path: Annotated[str, Doc("File path relative to the repository root")],
    ) -> str:
        """Return file contents from a Git ref."""
        return await FilesAtRef(self._git()).get_file_contents_at_ref(ref=ref, path=path)

    @function
    async def get_tags_pointing_at(
        self,
        ref: Annotated[str, Doc("Git ref to inspect")] = "HEAD",
    ) -> list[str]:
        """Return tags that point at a ref."""
        return await Tags(self._git()).get_tags_pointing_at(ref=ref)

    @function
    async def create_tag(
        self,
        tag: Annotated[str, Doc("Tag name to create")],
        message: Annotated[str | None, Doc("Optional annotated tag message")] = None,
        user_name: Annotated[str, Doc("Tagger name for annotated tags")] = "dagger-ci",
        user_email: Annotated[str, Doc("Tagger email for annotated tags")] = "dagger-ci@example.local",
    ) -> Self:
        """Create a local lightweight or annotated tag."""
        self.container_ = (
            Tags(self._git())
            .create_tag(
                tag=tag,
                message=message,
                user_name=user_name,
                user_email=user_email,
            )
            .container_
        )
        return self

    @function
    async def push_tag(
        self,
        tag: Annotated[str, Doc("Tag name to push")],
        remote: Annotated[str, Doc("Remote name to push the tag to")] = "origin",
    ) -> Self:
        """Push a local tag to a remote."""
        self.container_ = Tags(self._git()).push_tag(tag=tag, remote=remote).container_
        return self
