from unittest import TestCase

from dagger import dag

from .fixtures import SyntheticGitRepos


class AuthTests(SyntheticGitRepos):
    """Authentication behavior tests."""

    async def all(self) -> None:
        await self.with_https_token_auth_configures_git_without_exposing_token()
        await self.with_ssh_key_auth_configures_git_without_exposing_key_material()

    async def with_https_token_auth_configures_git_without_exposing_token(self) -> None:
        """Configure HTTPS token auth without writing the token to git config."""
        token_text = "sensitive-token-value"
        git = dag.git(source=self.repo_with_local_tag()).with_https_token_auth(
            host="https://git.example.local/org/repo.git",
            token=dag.set_secret("GIT_TEST_TOKEN", token_text),
            username="ci-user",
        )

        askpass_path = await git.container().with_exec(["sh", "-c", "printf '%s' \"$GIT_ASKPASS\""]).stdout()
        askpass_username = (
            await git.container()
            .with_exec(["sh", "-c", '"$GIT_ASKPASS" "Username for \'https://git.example.local\':"'])
            .stdout()
        )
        askpass_permissions = await git.container().with_exec(["stat", "-c", "%a", askpass_path]).stdout()
        configured_username = (
            await git.container()
            .with_exec(["git", "config", "--global", "--get", "credential.https://git.example.local.username"])
            .stdout()
        )
        config = await git.container().with_exec(["git", "config", "--global", "--list"]).stdout()

        test_case = TestCase()
        test_case.assertEqual("/home/git/.local/bin/git-askpass", askpass_path)
        test_case.assertEqual("ci-user", askpass_username.strip())
        test_case.assertEqual("700", askpass_permissions.strip())
        test_case.assertEqual("ci-user", configured_username.strip())
        test_case.assertNotIn(token_text, config)

    async def with_ssh_key_auth_configures_git_without_exposing_key_material(self) -> None:
        """Configure SSH key auth with strict permissions and no key material in output."""
        private_key_text = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest-private-key\n-----END OPENSSH PRIVATE KEY-----"
        known_hosts_text = "git.example.local ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKnownHost"
        git = dag.git(source=self.repo_with_local_tag()).with_ssh_key_auth(
            private_key=dag.set_secret("GIT_TEST_SSH_KEY", private_key_text),
            known_hosts=dag.set_secret("GIT_TEST_KNOWN_HOSTS", known_hosts_text),
            host="git@git.example.local:org/repo.git",
        )

        key_permissions = await git.container().with_exec(["stat", "-c", "%a", "/home/git/.ssh/id_ed25519"]).stdout()
        known_hosts_permissions = (
            await git.container().with_exec(["stat", "-c", "%a", "/home/git/.ssh/known_hosts"]).stdout()
        )
        config_permissions = await git.container().with_exec(["stat", "-c", "%a", "/home/git/.ssh/config"]).stdout()
        ssh_command = await git.container().with_exec(["sh", "-c", "printf '%s' \"$GIT_SSH_COMMAND\""]).stdout()
        config = await git.container().with_exec(["cat", "/home/git/.ssh/config"]).stdout()

        combined_output = "\n".join([ssh_command, config])

        test_case = TestCase()
        test_case.assertEqual("600", key_permissions.strip())
        test_case.assertEqual("644", known_hosts_permissions.strip())
        test_case.assertEqual("600", config_permissions.strip())
        test_case.assertIn("UserKnownHostsFile=/home/git/.ssh/known_hosts", ssh_command)
        test_case.assertIn("Host git.example.local", config)
        test_case.assertNotIn(private_key_text, combined_output)
        test_case.assertNotIn(known_hosts_text, combined_output)
