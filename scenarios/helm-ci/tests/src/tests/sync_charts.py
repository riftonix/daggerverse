"""Chart sync tests for the Helm CI scenario."""

from unittest import TestCase

import yaml
from dagger import dag, function, object_type

from .fixtures import (
    FAKE_DIGEST,
    assert_fails_with,
    demo_chart,
    demo_values,
    failure_output,
    fixtures,
    fork,
    pin,
    read_config,
    registry,
    scenario,
    snapshot,
    with_config,
    with_nomatch,
)


@object_type
class SyncChartsTests:
    """Chart sync checks, run as `dagger call sync-charts <test>`."""

    @function
    async def all(self) -> None:
        """Run all chart sync tests."""
        await self.reports_all_configuration_errors()
        await self.reports_missing_configuration()
        await self.rejects_unknown_component()
        await self.rejects_invalid_inputs()
        await self.renders_local_and_pull_request_manifests()
        await self.default_runtime_container()
        await self.runtime_user_input()
        await self.replaced_runtime_container()
        await self.previews_update()
        await self.merges_upstream_update()
        await self.skips_up_to_date_components()
        await self.components_are_independent()
        await self.reports_component_failures()

    @function
    async def reports_all_configuration_errors(self) -> None:
        """Report every configuration and pin problem in one error before any pipeline runs."""
        config = await read_config(fork()) | {
            "upstream": {"registry": "http://bad", "versionfilter": ">=1.0.0"},
            "rewrite": [{"from": "SHARED"}],
            "components": {
                "demo": None,
                "bad": {"path": "../escape"},
                "Upper": None,
                "filt": {"versionfilter": "~1.0"},
            },
        }
        source = (
            with_config(fork(), config)
            .without_file("updatecli/pins/demo.json")
            .with_symlink("other.json", "updatecli/pins/demo.json")
        )
        helm_ci = scenario(source)
        for call in (helm_ci.sync_charts_manifest, helm_ci.sync_charts_diff):
            output = await failure_output(call())
            for expected in (
                "upstream.registry: 'http://bad' must be oci://<host>[/<project>]",
                "rewrite[0]: to is missing",
                "components.bad: path '../escape' must be charts/<name> or libs/<name>",
                "components.Upper: ID must match [a-z0-9][a-z0-9-]*",
                "components.filt: unsupported versionfilter '~1.0'",
                "components.filt: path libs/filt must be a directory inside source",
                "components.filt: pin updatecli/pins/filt.json is missing",
                "components.demo: pin updatecli/pins/demo.json must not be a symbolic link",
            ):
                TestCase().assertIn(expected, output)

    @function
    async def reports_missing_configuration(self) -> None:
        """Name every missing required configuration value."""
        output = await failure_output(scenario(with_config(fork(), {"foo": 1})).sync_charts_manifest())
        for expected in (
            "upstream.registry: missing",
            "upstream.versionfilter: missing",
            "home: missing",
            "components: missing",
        ):
            TestCase().assertIn(expected, output)

    @function
    async def rejects_unknown_component(self) -> None:
        """Reject a selected component that the configuration does not declare."""
        await assert_fails_with(
            scenario(fork()).sync_charts_manifest(components=["demo", "ghost"]),
            "components input: unknown component IDs ghost",
        )

    @function
    async def rejects_invalid_inputs(self) -> None:
        """Validate the configuration path and the GitHub repository and branch inputs."""
        helm_ci = scenario(fork())
        await assert_fails_with(
            helm_ci.sync_charts_manifest(config_path="../values.yaml"), "must be a relative path inside source"
        )
        await assert_fails_with(
            helm_ci.sync_charts_manifest(repository="example/helm-fork"),
            "repository and branch must be supplied together",
        )
        await assert_fails_with(
            helm_ci.sync_charts_manifest(repository="bad", branch="master"), "repository: 'bad' must be owner/name"
        )
        await assert_fails_with(
            helm_ci.sync_charts_update(
                github_token=dag.set_secret("helm-ci-sync-charts-token", "unused"),
                repository="bad",
                branch="master",
            ),
            "repository: 'bad' must be owner/name",
        )

    @function
    async def renders_local_and_pull_request_manifests(self) -> None:
        """Render all local pipelines or a selected GitHub pipeline with a PR action and no token."""
        test = TestCase()
        helm_ci = scenario(fork())
        local = list(yaml.safe_load_all(await helm_ci.sync_charts_manifest()))
        test.assertEqual(["upstream-demo", "upstream-other"], [document["pipelineid"] for document in local])
        for document in local:
            test.assertNotIn("scms", document)
            test.assertNotIn("actions", document)
            test.assertNotIn("scmid", document["targets"]["component"])
        test.assertEqual(
            "python3 -I /opt/chart-sync/chart_sync.py sync --config updatecli/values.yaml --component demo",
            local[0]["targets"]["component"]["spec"]["command"],
        )

        text = await helm_ci.sync_charts_manifest(components=["demo"], repository="example/helm-fork", branch="master")
        github = list(yaml.safe_load_all(text))
        test.assertEqual(["upstream-demo"], [document["pipelineid"] for document in github])
        test.assertNotIn("token", text)
        demo = github[0]
        test.assertEqual(
            {
                "owner": "example",
                "repository": "helm-fork",
                "branch": "master",
                "commitusingapi": True,
                "submodules": False,
            },
            demo["scms"]["fork"]["spec"],
        )
        test.assertEqual("github", demo["scms"]["fork"]["kind"])
        test.assertEqual("fork", demo["targets"]["component"]["scmid"])
        action = demo["actions"]["pullrequest"]
        test.assertEqual("github/pullrequest", action["kind"])
        test.assertEqual("fork", action["scmid"])
        test.assertEqual("chore(deps): update demo from upstream", action["title"])
        test.assertIn("`libs/demo`", action["spec"]["description"])

    @function
    async def default_runtime_container(self) -> None:
        """Run chart sync as the unprivileged user with every tool and source mounted at /work."""
        test = TestCase()
        source = dag.directory().with_new_file("marker.txt", "marker\n")
        container = dag.helm_ci(source=source).updatecli_container()
        test.assertEqual("65532", (await container.with_exec(["id", "-u"]).stdout()).strip())
        await container.with_exec(
            ["sh", "-c", "python3 -I -c 'import yaml' && helm version && git --version && updatecli version"]
        ).sync()
        test.assertEqual("/work", await container.workdir())
        test.assertEqual(["marker.txt"], await container.directory("/work").entries())

    @function
    async def runtime_user_input(self) -> None:
        """Apply the Updatecli container user input to the chart sync runtime."""
        container = dag.helm_ci(source=dag.directory(), updatecli_container_user_id="1000").updatecli_container()
        TestCase().assertEqual("1000", await container.user())

    @function
    async def replaced_runtime_container(self) -> None:
        """Use a caller-provided runtime container for chart sync."""
        helm_ci = dag.helm_ci(source=dag.directory())
        replaced = helm_ci.with_updatecli_container(
            helm_ci.updatecli_container().with_env_variable("CHART_SYNC_RUNTIME_MARKER", "replaced")
        )
        TestCase().assertEqual(
            "replaced", await replaced.updatecli_container().env_variable("CHART_SYNC_RUNTIME_MARKER")
        )

    @function
    async def previews_update(self) -> None:
        """Preview the newest stable version inside the filter and skip up-to-date components."""
        test = TestCase()
        registry_service, digests = await registry()
        output = await scenario(fork(digests), registry_service).sync_charts_diff()
        test.assertIn("Preview demo: 1.0.4 -> 1.0.5", output)
        test.assertNotIn("Preview other", output)

    @function
    async def merges_upstream_update(self) -> None:
        """Merge upstream changes into the fork, keep fork edits, and update only the component and its pin."""
        registry_service, digests = await registry()
        source = fork(digests)
        updated = await scenario(source, registry_service).sync_charts()

        upstream = fixtures().directory("upstream/update/nuc-demo")
        expected = source.without_files(["libs/demo/templates/old.yaml", "libs/demo/templates/gone.yaml"])
        expected = expected.with_new_file("updatecli/pins/demo.json", pin("1.0.5", digests["nuc-demo:1.0.5"]))
        expected = expected.with_new_file("libs/demo/Chart.yaml", demo_chart("1.0.5"))
        expected = expected.with_new_file("libs/demo/values.yaml", demo_values("upstream-new"))
        for path in ("templates/renamed.yaml", "templates/new.yaml", "LICENSE.txt", "files/blob.bin"):
            expected = expected.with_file(f"libs/demo/{path}", upstream.file(path))
        TestCase().assertEqual(await snapshot(expected), await snapshot(updated))

    @function
    async def skips_up_to_date_components(self) -> None:
        """Leave components unchanged when the pin is current or newer than every matching tag."""
        test = TestCase()
        registry_service, digests = await registry()
        source = (
            fork(digests)
            .with_new_file("updatecli/pins/demo.json", pin("1.0.5", digests["nuc-demo:1.0.5"]))
            .with_new_file("updatecli/pins/other.json", pin("1.2.0", FAKE_DIGEST))
        )
        helm_ci = scenario(source, registry_service)
        test.assertNotIn("Preview", await helm_ci.sync_charts_diff())
        test.assertEqual(await snapshot(source), await snapshot(await helm_ci.sync_charts()))

    @function
    async def components_are_independent(self) -> None:
        """Process every selected component even when one of them fails."""
        registry_service, digests = await registry()
        helm_ci = scenario(await with_nomatch(fork(digests), digests), registry_service)
        output = await failure_output(helm_ci.sync_charts_diff(components=["demo", "nomatch"]))
        test = TestCase()
        test.assertIn("Preview demo: 1.0.4 -> 1.0.5", output)
        test.assertIn("no tag of oci://registry:5000/nuc/nuc-other matches '>=3.0.0'", output)

    @function
    async def reports_component_failures(self) -> None:
        """Fail a component on upstream, pin, merge, and fork content problems with a diagnostic for each."""
        registry_service, digests = await registry()
        source = fork(digests)
        config = await read_config(source)
        unreachable = config | {
            "upstream": config["upstream"] | {"registry": "oci://unreachable.invalid/nuc", "plainhttp": False}
        }
        unsafe = "symbolic links or .git metadata"
        # Each case: name, source, component, whether to apply instead of preview, expected output.
        cases = (
            (
                "no matching version",
                await with_nomatch(source, digests),
                "nomatch",
                True,
                "no tag of oci://registry:5000/nuc/nuc-other matches '>=3.0.0'",
            ),
            (
                "unreachable registry",
                with_config(source, unreachable),
                "other",
                False,
                "tag listing https://unreachable.invalid/v2/nuc/nuc-other/tags/list failed",
            ),
            (
                "digest mismatch",
                source.with_new_file("updatecli/pins/demo.json", pin("1.0.4", FAKE_DIGEST)),
                "demo",
                False,
                "does not match the pinned digest",
            ),
            (
                "merge conflict",
                source.with_new_file("libs/demo/values.yaml", demo_values("fork-first")),
                "demo",
                True,
                "Merge conflict in values.yaml",
            ),
            (
                "version collision",
                source.with_new_file("libs/demo/Chart.yaml", demo_chart("1.0.5")),
                "demo",
                False,
                "version collision",
            ),
            (
                "symbolic link",
                source.with_symlink("old.yaml", "libs/demo/templates/link.yaml"),
                "demo",
                False,
                unsafe,
            ),
            ("git metadata", source.with_new_file("libs/demo/.git/config", "[core]\n"), "demo", False, unsafe),
        )
        for name, case_source, component, apply, expected in cases:
            helm_ci = scenario(case_source, registry_service)
            if apply:
                call = helm_ci.sync_charts(components=[component]).sync()
            else:
                call = helm_ci.sync_charts_diff(components=[component])
            await assert_fails_with(call, expected, name)
