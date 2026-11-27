from typing import Annotated

import dagger
from dagger import Container, Doc, dag, function, object_type

DEFAULT_IMAGE_REGISTRY = "docker.io"
DEFAULT_IMAGE_REPOSITORY = "kroniak/ssh-client"
# renovate: datasource=docker depName=kroniak/ssh-client
DEFAULT_IMAGE_TAG = "3.23"
DEFAULT_CONTAINER_USER_ID = "65532"


@object_type
class Ssh:
    """SSH dagger module"""

    image_registry: str
    image_repository: str
    image_tag: str
    container_user_id: str
    container_: dagger.Container | None

    @classmethod
    async def create(
        cls,
        image_registry: Annotated[str | None, Doc("SSH image registry")] = DEFAULT_IMAGE_REGISTRY,
        image_repository: Annotated[str | None, Doc("SSH image repository")] = DEFAULT_IMAGE_REPOSITORY,
        image_tag: Annotated[str | None, Doc("SSH image tag")] = DEFAULT_IMAGE_TAG,
        container_user_id: Annotated[str | None, Doc("SSH container user ID")] = DEFAULT_CONTAINER_USER_ID,
    ):
        """Constructor"""
        return cls(
            image_registry=image_registry,
            image_repository=image_repository,
            image_tag=image_tag,
            container_user_id=container_user_id or DEFAULT_CONTAINER_USER_ID,
            container_=None,
        )

    @function
    def container(self) -> Container:
        """
        Get the base container for the SSH module.
        """
        if self.container_:
            return self.container_
        home = f"/home/{self.container_user_id}"
        self.container_ = (
            dag.container()
            .from_(address=f"{self.image_registry}/{self.image_repository}:{self.image_tag}")
            .with_exec(["apk", "add", "--no-cache", "sshpass"])
            .with_exec(["adduser", "-D", "-u", self.container_user_id, "-h", home, self.container_user_id])
            .with_user(self.container_user_id)
            .with_env_variable("HOME", home)
            .with_new_file(
                path="$HOME/.ssh/config",
                contents='"Host *\n\tStrictHostKeyChecking no\n\n"',
                owner=self.container_user_id,
                permissions=0o600,
                expand=True,
            )
            .with_workdir("$HOME/.ssh", expand=True)
        )
        return self.container_

    @function
    async def with_private_key(self, source: Annotated[dagger.File, Doc("Private key file")]) -> str:
        """Add private key to container"""

        container: dagger.Container = self.container()
        container = (
            container.with_env_variable("SSH_PRIVATE_KEY_PATH", "$HOME/.ssh/id_rsa", expand=True)
            .with_file(
                "$SSH_PRIVATE_KEY_PATH", source=source, owner=self.container_user_id, permissions=0o600, expand=True
            )
            .with_exec(["ls", "-lah", "$HOME/.ssh"], expand=True)
        )
        return await container.stdout()

    @function
    async def exec(
        self,
        destination: Annotated[str, Doc("Address to connect for ssh client")],
        ssh_port: Annotated[int, Doc("Destination port")] = 22,
        ssh_user: Annotated[str, Doc("Ssh user")] = "root",
        insecure_ssh_password: Annotated[str, Doc("Ssh password, that can be visible in the logs")] = "",
        ssh_cmd: Annotated[str, Doc("Command for remote exec")] = "uname -a",
    ) -> str:
        """Functions for helm chart linting"""
        container: dagger.Container = self.container()
        cmd: list[str] = []
        if insecure_ssh_password:
            cmd.extend(["sshpass", "-p", insecure_ssh_password])
        cmd.extend(["ssh", "-v", "-p", str(ssh_port), "-o", "StrictHostKeyChecking=no", f"{ssh_user}@{destination}"])
        cmd.append(ssh_cmd)
        return await container.with_exec(cmd, use_entrypoint=True).stdout()
