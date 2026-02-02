# SSH Dagger Module

Containerized SSH client for Dagger pipelines. This module provisions a container with `ssh` and `sshpass`, configures a non-root user, and exposes helpers to add a private key and execute remote commands.

## Features
- Base image `kroniak/ssh-client` with `ssh` tools
- Installs `sshpass` for password-based auth (optional)
- Non-root user support with HOME configured
- Preconfigured SSH client disabling strict host key checking
- Add a private key to the container
- Execute remote SSH commands

## Defaults
- image_registry: `docker.io`
- image_repository: `kroniak/ssh-client`
- image_tag: `3.21`
- container_user: `65532`
- HOME: `/home/65532`
- SSH config: `$HOME/.ssh/config` with `StrictHostKeyChecking no`

## API

- create(image_registry, image_repository, image_tag, container_user)
  - Returns a configured Ssh module instance.

- container() -> dagger.Container
  - Returns the cached base container with the SSH client.

- with_private_key(source: File) -> str
  - Mounts a private key to `$HOME/.ssh/id_rsa` with `600` permissions and lists `$HOME/.ssh`.
  - Returns stdout from the listing.

- exec(destination: str, ssh_port: int = 22, ssh_user: str = 'root', insecure_ssh_password: str = 'P@ssw0rd', ssh_cmd: str = 'uname -a') -> str
  - Builds and runs an ssh command. If `insecure_ssh_password` is provided, uses `sshpass -p`.
  - Adds `-o StrictHostKeyChecking=no` to suppress host key prompts.
  - Returns stdout from the remote command.

## Usage (Python SDK)

```python
import asyncio
import dagger
from dagger import dag
from ssh import Ssh

async def main():
    async with dagger.Connection(dag) as client:
        ssh_mod = await Ssh.create()

        # Optionally add a private key
        # key_file = client.host().file("~/.ssh/id_rsa")
        # out = await ssh_mod.with_private_key(source=key_file)
        # print(out)

        # Execute a remote command (password auth example)
        res = await ssh_mod.exec(
            destination="example.com",
            ssh_port=22,
            ssh_user="root",
            insecure_ssh_password="hunter2",
            ssh_cmd="uname -a"
        )
        print(res)

asyncio.run(main())
```

## Usage (CLI)

Run a remote command (password auth):

```bash
dagger -m ./ssh call exec \
  --destination=example.com \
  --ssh-user=root \
  --ssh-port=22 \
  --insecure-ssh-password=hunter2 \
  --ssh-cmd="uname -a"
```

Add a private key:

```bash
dagger -m ./ssh call with-private-key --source=./id_rsa
```

Security notes:
- Avoid logging real passwords. Prefer Dagger secrets or key-based auth where possible.
- The module disables strict host key checking; consider overriding if you require stronger host verification.

## License
See the repository root LICENSE file.
