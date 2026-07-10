"""Dagger-native tests for the SSH module."""

from unittest import TestCase

from dagger import dag, function, object_type

FIXTURE_PRIVATE_KEY_PATH = "fixtures/id_rsa"


@object_type
class Tests:
    """Test module entrypoint for SSH module checks."""

    @function
    def module(self) -> str:
        """Return the test module name."""
        return "ssh-tests"

    @function
    async def all(self) -> None:
        """Run all SSH module tests."""
        await self.container_has_sshpass()
        await self.private_key_is_mounted()

    @function
    async def container_has_sshpass(self) -> None:
        """Assert the default SSH container has sshpass installed."""
        stdout = await dag.ssh().container().with_exec(["which", "sshpass"]).stdout()
        TestCase().assertEqual("/usr/bin/sshpass", stdout.strip())

    @function
    async def private_key_is_mounted(self) -> None:
        """Assert with_private_key mounts the provided key file."""
        stdout = await dag.ssh().with_private_key(self._fixture_private_key())
        TestCase().assertIn("id_rsa", stdout)

    def _fixture_private_key(self):
        """Return a fixture private key file."""
        return dag.current_module().source().file(FIXTURE_PRIVATE_KEY_PATH)
