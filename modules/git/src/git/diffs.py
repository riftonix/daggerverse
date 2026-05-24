from __future__ import annotations

from .cli import GitCli
from .paths import changed_dir_for_file, normalize_path


class Diffs:
    """Diff operations for the Git Dagger facade."""

    def __init__(self, git: GitCli) -> None:
        self.git = git

    async def get_changed_paths(self, target_branch: str, diff_path: str | None) -> list[str]:
        diff_path = diff_path or "."
        diff_output = (
            await self.git.container()
            .with_exec(
                [
                    "sh",
                    "-c",
                    f'git diff --name-only --diff-filter=ACMRTUXB {target_branch} -- "{diff_path}"',
                ]
            )
            .stdout()
        )

        untracked_output = (
            await self.git.container()
            .with_exec(
                [
                    "sh",
                    "-c",
                    f'git ls-files --others --exclude-standard -- "{diff_path}"',
                ]
            )
            .stdout()
        )

        raw_paths = [line.strip() for line in (diff_output + "\n" + untracked_output).splitlines() if line.strip()]

        normalized_diff_path = diff_path.rstrip("/")
        if normalized_diff_path in (".", "./"):
            relative_paths = raw_paths
        else:
            prefix = f"{normalized_diff_path}/"
            relative_paths = [path[len(prefix) :] if path.startswith(prefix) else path for path in raw_paths]

        top_level_dirs = [path.split("/", 1)[0] for path in relative_paths]
        if normalized_diff_path in (".", "./"):
            return sorted(set(top_level_dirs))

        return sorted({f"{normalized_diff_path}/{path}" for path in top_level_dirs})

    async def get_changed_files(
        self,
        base_ref: str,
        head_ref: str,
        paths: list[str] | None,
        diff_filter: str,
    ) -> list[str]:
        cmd = [
            "git",
            "diff",
            "--name-only",
            "--find-renames",
            "--find-copies",
            "--find-copies-harder",
            f"--diff-filter={diff_filter}",
            base_ref,
            head_ref,
        ]
        if paths:
            cmd.append("--")
            cmd.extend(paths)

        output = await self.git.container().with_exec(cmd).stdout()
        return [line.strip() for line in output.splitlines() if line.strip()]

    async def get_changed_files_since_merge_base(
        self,
        base_ref: str,
        head_ref: str,
        paths: list[str] | None,
        diff_filter: str,
    ) -> list[str]:
        merge_base = (await self.git.container().with_exec(["git", "merge-base", base_ref, head_ref]).stdout()).strip()

        return await self.get_changed_files(
            base_ref=merge_base,
            head_ref=head_ref,
            paths=paths,
            diff_filter=diff_filter,
        )

    async def get_changed_dirs(
        self,
        base_ref: str,
        head_ref: str,
        paths: list[str] | None,
        depth: int,
        diff_filter: str,
    ) -> list[str]:
        changed_files = await self.get_changed_files(
            base_ref=base_ref,
            head_ref=head_ref,
            paths=paths,
            diff_filter=diff_filter,
        )
        scopes = [normalize_path(path) for path in paths or [] if normalize_path(path) != "."]

        return sorted({changed_dir_for_file(path, scopes=scopes, depth=depth) for path in changed_files})

    async def get_changed_dirs_since_merge_base(
        self,
        base_ref: str,
        head_ref: str,
        paths: list[str] | None,
        depth: int,
        diff_filter: str,
    ) -> list[str]:
        changed_files = await self.get_changed_files_since_merge_base(
            base_ref=base_ref,
            head_ref=head_ref,
            paths=paths,
            diff_filter=diff_filter,
        )
        scopes = [normalize_path(path) for path in paths or [] if normalize_path(path) != "."]

        return sorted({changed_dir_for_file(path, scopes=scopes, depth=depth) for path in changed_files})

    async def has_changes(
        self,
        base_ref: str,
        head_ref: str,
        paths: list[str] | None,
        diff_filter: str,
    ) -> bool:
        changed_files = await self.get_changed_files(
            base_ref=base_ref,
            head_ref=head_ref,
            paths=paths,
            diff_filter=diff_filter,
        )
        return bool(changed_files)
