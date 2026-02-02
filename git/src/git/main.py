from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class Git:
    source: dagger.Directory
    image_registry: str
    image_repository: str
    image_tag: str
    container_user: str
    container_: dagger.Container | None

    @classmethod
    async def create(
        cls,
        source: Annotated[dagger.Directory, Doc('Git repository directory (must include .git)')],
        image_registry: Annotated[str | None, Doc('Git image registry')] = 'docker.io',
        image_repository: Annotated[str | None, Doc('Git image repositroy')] = 'alpine/git',
        image_tag: Annotated[str | None, Doc('Git image tag')] = '2.52.0',
        container_user: Annotated[str | None, Doc('Git image user')] = '65532',
    ):
        '''Constructor'''
        return cls(
            source=source,
            image_registry=image_registry,
            image_repository=image_repository,
            image_tag=image_tag,
            container_user=container_user,
            container_=None,
        )

    @function
    def container(self) -> dagger.Container:
        '''Creates container with configured git'''
        if self.container_:
            return self.container_
        self.container_ = (
            dag.container()
            .from_(address=f'{self.image_registry}/{self.image_repository}:{self.image_tag}')
            .with_user(self.container_user)
            .with_env_variable('GIT_REPO_PATH', '/tmp/git/repo')
            .with_exec(['mkdir', '-p', '-m', '770', '$GIT_REPO_PATH'], expand=True)
            .with_directory('$GIT_REPO_PATH', self.source, owner=self.container_user, expand=True)
            .with_workdir('$GIT_REPO_PATH', expand=True)
            .with_exec(['git', 'config', '--local', 'safe.directory', '$GIT_REPO_PATH'], expand=True)
        )
        return self.container_

    @function
    async def get_changed_dirs(
        self,
        target_branch: Annotated[str, Doc('Target branch or ref to diff against')] = 'master',
        diff_path: Annotated[str | None, Doc('Path to scope the diff (relative to repo root)')] = '.',
    ) -> list[str]:
        '''Return changed paths inside diff_path between target_branch and HEAD'''
        container = self.container()

        diff_output = await container.with_exec(
            [
                'sh',
                '-c',
                (
                    'git diff --name-only --diff-filter=ACMRTUXB '
                    f'{target_branch} -- "{diff_path}"'
                ),
            ]
        ).stdout()

        untracked_output = await container.with_exec(
            [
                'sh',
                '-c',
                f'git ls-files --others --exclude-standard -- "{diff_path}"',
            ]
        ).stdout()

        raw_paths = [
            line.strip()
            for line in (diff_output + '\n' + untracked_output).splitlines()
            if line.strip()
        ]

        normalized_diff_path = (diff_path or '.').rstrip('/')
        if normalized_diff_path in ('.', './'):
            relative_paths = raw_paths
        else:
            prefix = f'{normalized_diff_path}/'
            relative_paths = [
                path[len(prefix):] if path.startswith(prefix) else path
                for path in raw_paths
            ]

        top_level_dirs = [path.split('/', 1)[0] for path in relative_paths]
        if normalized_diff_path in ('.', './'):
            return sorted(set(top_level_dirs))

        return sorted({f'{normalized_diff_path}/{path}' for path in top_level_dirs})
