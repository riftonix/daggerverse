from typing import Annotated
import dagger
from dagger import dag, function, object_type, Doc, Container


@object_type
class Ssh:
    '''SSH dagger module'''
    image_registry: str
    image_repository: str
    image_tag: str
    container_user: str
    container_: dagger.Container | None

    @classmethod
    async def create(
        cls,
        image_registry: Annotated[str | None, Doc('Helm image registry')] = 'docker.io',
        image_repository: Annotated[str | None, Doc('Helm image repositroy')] = 'kroniak/ssh-client',
        image_tag: Annotated[str | None, Doc('Helm image tag')] = '3.21',
        container_user: Annotated[str | None, Doc('Helm image user')] = '65532',
    ):
        '''Constructor'''
        return cls(
            image_registry=image_registry,
            image_repository=image_repository,
            image_tag=image_tag,
            container_user=container_user,
            container_=None,
        )

    @function
    def container(self) -> Container:
        '''
        Get the base container for the SSH module.
        '''
        if self.container_:
            return self.container_
        self.container_ = (
            dag.container().from_(address=f'{self.image_registry}/{self.image_repository}:{self.image_tag}')
            .with_exec(['apk', 'add', '--no-cache', 'sshpass'])
            .with_exec([
                'adduser', '-D', '-u', self.container_user,
                '-h', f'/home/{self.container_user}',
                self.container_user
            ])
            .with_user(self.container_user)
            .with_env_variable('HOME', f'/home/{self.container_user}')
            .with_new_file(
                path='$HOME/.ssh/config',
                contents='"Host *\n\tStrictHostKeyChecking no\n\n"',
                owner=self.container_user,
                permissions=600,
                expand=True
            )
            .with_workdir('$HOME/.ssh', expand=True)
        )
        return self.container_

    @function
    async def with_private_key(
        self,
        source: Annotated[dagger.File, Doc('Private key file')]
    ) -> str:
        '''Add private key to container'''

        container: dagger.Container = self.container()
        container = (
            container.with_env_variable('SSH_PRIVATE_KEY_PATH', '$HOME/.ssh/id_rsa', expand=True)
            .with_file('$SSH_PRIVATE_KEY_PATH', source=source, owner=self.container_user, permissions=600, expand=True)
            .with_exec(['ls', '-lah', '$HOME/.ssh'], expand=True)
        )
        return await container.stdout()

    @function
    async def exec(
        self,
        destination: Annotated[str, Doc('Address to connect for ssh client')],
        ssh_port: Annotated[int, Doc('Destination port')] = 22,
        ssh_user: Annotated[str, Doc('Ssh user')] = 'root',
        insecure_ssh_password: Annotated[str, Doc('Ssh password, that can be visible in the logs')] = '',
        ssh_cmd: Annotated[str, Doc('Command for remote exec')] = 'uname -a',
    ) -> str:
        '''Functions for helm chart linting'''
        container: dagger.Container = self.container()
        cmd: list[str] = []
        if insecure_ssh_password:
            cmd.extend(['sshpass', '-p', insecure_ssh_password])
        cmd.extend(['ssh', '-v', '-p', str(ssh_port), '-o', 'StrictHostKeyChecking=no', f'{ssh_user}@{destination}'])
        cmd.append(ssh_cmd)
        return (
            await container
            .with_exec(cmd, use_entrypoint=True)
            .stdout()
        )
