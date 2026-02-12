from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type, DefaultPath


@object_type
class Git:
    source: dagger.Directory
    image_registry: str
    image_repository: str
    image_tag: str
    user_id: str
    container_: dagger.Container | None

    @classmethod
    async def create(
        cls,
        source: Annotated[dagger.Directory, DefaultPath('.'), Doc('Git repository directory (must include .git)')],
        image_registry: Annotated[str | None, Doc('Git image registry')] = 'docker.io',
        image_repository: Annotated[str | None, Doc('Git image repositroy')] = 'alpine/git',
        image_tag: Annotated[str | None, Doc('Git image tag')] = '2.52.0',
        user_id: Annotated[str | None, Doc('Git image user')] = '65532',
    ):
        '''Constructor'''
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
        '''Creates container with configured git'''
        if self.container_:
            return self.container_
        self.container_ = (
            dag.container()
            .from_(address=f'{self.image_registry}/{self.image_repository}:{self.image_tag}')
            .with_env_variable('USER_ID', self.user_id)
            .with_env_variable('USER_NAME', 'git')
            .with_user('0')
            .with_exec(
                [
                    'sh',
                    '-c',
                    (
                        'getent passwd "$USER_ID" >/dev/null 2>&1 || '
                        'printf "$USER_NAME:x:%s:%s:$USER_NAME:/home/$USER_NAME:/sbin/nologin\\n" '   # noqa E501
                        '"$USER_ID" "$USER_ID" >> /etc/passwd; '
                        'getent group "$USER_ID" >/dev/null 2>&1 || '
                        'echo "$USER_NAME:x:$USER_ID:" >> /etc/group; '
                        'install -d -m 700 -o "$USER_ID" -g "$USER_ID" '
                        '"/home/$USER_NAME"'
                    ),
                ], expand=True
            )
            .with_user(self.user_id)
            .with_env_variable('HOME', '/home/git')
            .with_env_variable('GIT_REPO_PATH', '/tmp/git/repo')
            .with_exec(['mkdir', '-p', '-m', '770', '$GIT_REPO_PATH'], expand=True)
            .with_directory('$GIT_REPO_PATH', self.source, owner=self.user_id, expand=True)
            .with_workdir('$GIT_REPO_PATH', expand=True)
            .with_exec([
                'sh',
                '-c',
                'git status --porcelain >/dev/null 2>&1 || (echo "Path $GIT_REPO_PATH is not a git repo" >&2; exit 1)',
            ], expand=True)
            .with_exec(['git', 'config', '--local', 'safe.directory', '$GIT_REPO_PATH'], expand=True)
        )
        return self.container_

    @function
    async def with_ssh_private_key(
        self,
        source: Annotated[dagger.File, Doc('Private key file')]
    ) -> str:
        '''Add ssh private key to container'''

        container: dagger.Container = self.container()
        container = (
            container.with_env_variable('SSH_PRIVATE_KEY_PATH', '$HOME/.ssh/id_rsa', expand=True)
            .with_file('$SSH_PRIVATE_KEY_PATH', source=source, owner=self.user_id, permissions=600, expand=True)
            .with_exec(['ls', '-lah', '$HOME/.ssh'], expand=True)
        )
        return await container.stdout()

    @function
    async def get_changed_paths(
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

    # @function
    # async def fetch_tags(
    #     self,
    #     remote: Annotated[str, Doc('Remote name to fetch tags from')] = 'origin',
    #     prune: Annotated[bool | None, Doc('Prune deleted tags')] = False,
    # ) -> str:
    #     '''Fetch tags from remote'''
    #     container = self.container()
    #     cmd = ['git', 'fetch', '--tags', remote]
    #     if prune:
    #         cmd.insert(2, '--prune')
    #     return await container.with_exec(cmd).stdout()

    @function
    async def list_tags(
        self,
        pattern: Annotated[str, Doc('Optional tag filter pattern (glob)')] = '*',
    ) -> list[str]:
        '''List tags in the repository (optionally filtered)'''
        container = self.container()
        output = await container.with_exec(
            ['git', 'tag', '--list', pattern, '--sort=version:refname']
        ).stdout()
        return [line.strip() for line in output.splitlines() if line.strip()]

    @function
    async def get_short_commit_sha(
        self,
        length: Annotated[int | None, Doc('Length of the short SHA')] = 8,
    ) -> str:
        '''Return short commit SHA for HEAD'''
        container = self.container()
        return await container.with_exec(
            ['git', 'rev-parse', f'--short={length}', 'HEAD']
        ).stdout()

    # @function
    # async def create_and_push_tag(
    #     self,
    #     tag: Annotated[str, Doc('Tag name to create')],
    #     message: Annotated[str | None, Doc('Annotated tag message (optional)')] = None,
    #     remote: Annotated[str, Doc('Remote name to push the tag to')] = 'origin',
    #     user_name: Annotated[str, Doc('Git user.name for annotated tags')] = 'dagger-ci',
    #     user_email: Annotated[str, Doc('Git user.email for annotated tags')] = 'dagger-ci@example.local',
    # ) -> str:
    #     '''Create a tag and push it to the remote'''
    #     container = self.container()
    #     if message:
    #         container = container.with_exec(
    #             [
    #                 'git',
    #                 '-c',
    #                 f'user.name={user_name}',
    #                 '-c',
    #                 f'user.email={user_email}',
    #                 'tag',
    #                 '-a',
    #                 tag,
    #                 '-m',
    #                 message,
    #             ]
    #         )
    #     else:
    #         container = container.with_exec(['git', 'tag', tag])

    #     return await container.with_exec(['git', 'push', remote, tag]).stdout()

    @function
    async def get_tags_pointing_at_head(
        self,
        remote: Annotated[str, Doc('Remote name to fetch tags from')] = 'origin',
    ) -> list[str]:
        '''Return all tags that point to HEAD'''
        container = self.container()
        await self.fetch_tags(remote=remote)
        output = await container.with_exec(['git', 'tag', '--points-at', 'HEAD']).stdout()
        return [line.strip() for line in output.splitlines() if line.strip()]
