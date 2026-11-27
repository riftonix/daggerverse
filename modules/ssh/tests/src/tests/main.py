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
        """Assert the configured container user can mount a private key in its home."""
        ssh = dag.ssh(container_user_id="12345")
        home = await ssh.container().env_variable("HOME")
        stdout = await ssh.with_private_key(self._fixture_private_key())
        test_case = TestCase()
        test_case.assertEqual("/home/12345", home)
        test_case.assertRegex(stdout, r"(?m)^-rw------- .*\bid_rsa$")

    def _fixture_private_key(self):
        """Return a fixture private key file."""
        return dag.current_module().source().file(FIXTURE_PRIVATE_KEY_PATH)
