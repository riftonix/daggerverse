import dagger
from dagger import dag


class SyntheticGitRepos:
    """Synthetic Git repository fixtures shared by Git module tests."""

    def repo_with_local_tag(self) -> dagger.Directory:
        """Return a git repo with a local tag."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(["sh", "-c", "printf 'initial\\n' > README.md && git add README.md && git commit -m initial"])
            .with_exec(["git", "tag", "v1.0.0"])
            .directory("/work/repo")
        )

    def repo_with_remote_tag(self) -> dagger.Directory:
        """Return a git repo whose local bare remote contains a tag missing locally."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(["sh", "-c", "printf 'initial\\n' > README.md && git add README.md && git commit -m initial"])
            .with_exec(["git", "tag", "v1.0.0"])
            .with_exec(["mkdir", "-p", ".remote"])
            .with_exec(["git", "clone", "--bare", ".", ".remote/origin.git"])
            .with_exec(["git", "tag", "-d", "v1.0.0"])
            .with_exec(["git", "remote", "add", "origin", ".remote/origin.git"])
            .directory("/work/repo")
        )

    def repo_with_missing_remote_branch(self) -> dagger.Directory:
        """Return a git repo whose local bare remote contains a missing branch."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(["sh", "-c", "printf 'initial\\n' > README.md && git add README.md && git commit -m initial"])
            .with_exec(["git", "checkout", "-b", "feature"])
            .with_exec(
                ["sh", "-c", "printf 'feature\\n' > feature.txt && git add feature.txt && git commit -m feature"]
            )
            .with_exec(["mkdir", "-p", ".remote"])
            .with_exec(["git", "clone", "--bare", ".", ".remote/origin.git"])
            .with_exec(["git", "checkout", "main"])
            .with_exec(["git", "branch", "-D", "feature"])
            .with_exec(["git", "remote", "add", "origin", ".remote/origin.git"])
            .directory("/work/repo")
        )

    def shallow_repo_with_remote_history(self) -> dagger.Directory:
        """Return a shallow clone with a local bare remote that has full history."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/source")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(["sh", "-c", "printf 'one\\n' > history.txt && git add . && git commit -m one"])
            .with_exec(["sh", "-c", "printf 'two\\n' > history.txt && git add . && git commit -m two"])
            .with_exec(["sh", "-c", "printf 'three\\n' > history.txt && git add . && git commit -m three"])
            .with_workdir("/work")
            .with_exec(["git", "clone", "--bare", "/work/source", "/work/origin.git"])
            .with_exec(["git", "clone", "--depth", "1", "file:///work/origin.git", "/work/repo"])
            .with_exec(["mkdir", "-p", "/work/repo/.remote"])
            .with_exec(["cp", "-a", "/work/origin.git", "/work/repo/.remote/origin.git"])
            .with_workdir("/work/repo")
            .with_exec(["git", "remote", "set-url", "origin", ".remote/origin.git"])
            .directory("/work/repo")
        )

    def repo_with_diverged_branches(self) -> dagger.Container:
        """Return a git repo with base and feature branches diverged from one commit."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(["sh", "-c", "printf 'initial\\n' > README.md && git add README.md && git commit -m initial"])
            .with_exec(["git", "checkout", "-b", "feature"])
            .with_exec(
                ["sh", "-c", "printf 'feature\\n' > feature.txt && git add feature.txt && git commit -m feature"]
            )
            .with_exec(["git", "checkout", "main"])
            .with_exec(["sh", "-c", "printf 'main\\n' > main.txt && git add main.txt && git commit -m main"])
        )

    def repo_with_diff_statuses(self) -> dagger.Container:
        """Return a git repo with practical diff status coverage."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    (
                        "mkdir -p services/api && "
                        "printf 'copy source\\n' > copy-source.txt && "
                        "printf 'before\\n' > modified.txt && "
                        "printf 'rename me\\n' > renamed-from.txt && "
                        "printf 'regular file\\n' > type-change && "
                        "git add . && git commit -m initial"
                    ),
                ]
            )
            .with_exec(["git", "checkout", "-b", "feature"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    (
                        "printf 'added\\n' > added.txt && "
                        "cp copy-source.txt copied.txt && "
                        "printf 'after\\n' > modified.txt && "
                        "git mv renamed-from.txt renamed.txt && "
                        "rm type-change && ln -s copy-source.txt type-change && "
                        "printf 'handler\\n' > services/api/handler.py && "
                        "mkdir -p services/api/internal/jobs && "
                        "printf 'worker\\n' > services/api/internal/jobs/worker.py && "
                        "git add . && git commit -m feature"
                    ),
                ]
            )
        )

    def repo_with_pull_request_branch(self) -> dagger.Container:
        """Return a git repo shaped like a pull request branch from an older base."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    (
                        "mkdir -p services/api docs && "
                        "printf 'base\\n' > services/api/app.py && "
                        "printf 'base\\n' > docs/guide.md && "
                        "git add . && git commit -m base"
                    ),
                ]
            )
            .with_exec(["git", "checkout", "-b", "feature"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    (
                        "printf 'feature\\n' > services/api/app.py && "
                        "printf 'feature\\n' > services/api/feature.py && "
                        "git add . && git commit -m feature"
                    ),
                ]
            )
            .with_exec(["git", "checkout", "main"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    "printf 'main\\n' > docs/main-only.md && git add . && git commit -m main",
                ]
            )
            .with_exec(["git", "checkout", "feature"])
        )

    def repo_with_monorepo_pull_request_branch(self) -> dagger.Container:
        """Return a monorepo-shaped pull request branch with base branch drift."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    (
                        "mkdir -p services/api services/web packages/shared docs && "
                        "printf 'base\\n' > services/api/app.py && "
                        "printf 'base\\n' > services/web/app.py && "
                        "printf 'base\\n' > packages/shared/lib.py && "
                        "printf 'base\\n' > docs/guide.md && "
                        "git add . && git commit -m base"
                    ),
                ]
            )
            .with_exec(["git", "checkout", "-b", "feature"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    (
                        "printf 'feature\\n' > services/api/app.py && "
                        "mkdir -p services/api/internal/jobs && "
                        "printf 'feature\\n' > services/api/internal/jobs/worker.py && "
                        "printf 'feature\\n' > services/web/ui.py && "
                        "printf 'feature\\n' > packages/shared/new.py && "
                        "git add . && git commit -m feature"
                    ),
                ]
            )
            .with_exec(["git", "checkout", "main"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    "printf 'main\\n' > docs/main-only.md && git add . && git commit -m main",
                ]
            )
            .with_exec(["git", "checkout", "feature"])
        )

    def repo_with_components(self) -> dagger.Container:
        """Return a monorepo with explicit and pattern-discovered components."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    (
                        "mkdir -p services/api services/web packages/shared docs "
                        "environments/dev/apps/api environments/prod/apps/api && "
                        "printf 'api\\n' > services/api/app.py && "
                        "printf 'web\\n' > services/web/app.py && "
                        "printf 'shared\\n' > packages/shared/lib.py && "
                        "printf 'docs\\n' > docs/readme.md && "
                        "printf 'dev\\n' > environments/dev/apps/api/config.yaml && "
                        "printf 'prod\\n' > environments/prod/apps/api/config.yaml && "
                        "git add . && git commit -m components"
                    ),
                ]
            )
        )

    def repo_with_changed_components(self) -> dagger.Container:
        """Return a monorepo with changed and unchanged component roots."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    (
                        "mkdir -p services/api services/web packages/shared docs && "
                        "printf 'api\\n' > services/api/app.py && "
                        "printf 'web\\n' > services/web/app.py && "
                        "printf 'shared\\n' > packages/shared/lib.py && "
                        "printf 'docs\\n' > docs/readme.md && "
                        "git add . && git commit -m base"
                    ),
                ]
            )
            .with_exec(["git", "checkout", "-b", "feature"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    (
                        "printf 'api feature\\n' > services/api/app.py && "
                        "printf 'shared feature\\n' > packages/shared/lib.py && "
                        "printf 'docs feature\\n' > docs/readme.md && "
                        "git add . && git commit -m feature"
                    ),
                ]
            )
        )

    def repo_with_shared_path_change(self) -> dagger.Container:
        """Return a monorepo where only a shared path changed."""
        return (
            dag.container()
            .from_("docker.io/alpine/git:2.52.0")
            .with_workdir("/work/repo")
            .with_exec(["git", "init", "--initial-branch", "main", "."])
            .with_exec(["git", "config", "user.name", "Dagger Test"])
            .with_exec(["git", "config", "user.email", "dagger-test@example.local"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    (
                        "mkdir -p services/api services/web packages/shared shared && "
                        "printf 'api\\n' > services/api/app.py && "
                        "printf 'web\\n' > services/web/app.py && "
                        "printf 'shared package\\n' > packages/shared/lib.py && "
                        "printf 'shared config\\n' > shared/config.yaml && "
                        "git add . && git commit -m base"
                    ),
                ]
            )
            .with_exec(["git", "checkout", "-b", "feature"])
            .with_exec(
                [
                    "sh",
                    "-c",
                    "printf 'shared config feature\\n' > shared/config.yaml && git add . && git commit -m feature",
                ]
            )
        )
