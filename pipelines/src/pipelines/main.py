from typing import Annotated

import yaml

import dagger
from dagger import Doc, dag, function, object_type, DefaultPath


@object_type
class Pipelines:
    async def _get_changed_paths(
        self,
        source: dagger.Directory,
        target_branch: str,
        diff_paths: list[str] | None,
    ) -> list[str]:
        git = dag.git(source=source)
        changed_paths: list[str] = []
        for diff_path in diff_paths or []:
            changed_paths.extend(
                await git.get_changed_paths(
                    target_branch=target_branch,
                    diff_path=diff_path,
                )
            )
        return sorted(set(changed_paths))

    async def _helm(
        self,
        source: Annotated[dagger.Directory, DefaultPath('.'), Doc('Helm chart host path')],
        image_registry: Annotated[str | None, Doc('Helm image registry')] = 'docker.io',
        image_repository: Annotated[str | None, Doc('Helm image repository')] = 'alpine/helm',
        image_tag: Annotated[str | None, Doc('Helm image tag')] = '3.18.6',
        user_id: Annotated[str | None, Doc('Helm image user')] = '65532',
    ):
        '''Return configured Helm module instance from local ./helm module'''
        return dag.helm(
            source=source,
            image_registry=image_registry,
            image_repository=image_repository,
            image_tag=image_tag,
            user_id=user_id,
        )

    @function
    async def helm_verify(
        self,
        source: Annotated[dagger.Directory, Doc('Helm chart directory')],
        values: Annotated[dagger.File | None, Doc('Optional values.yaml file')] = None,
        release_name: Annotated[str, Doc('Helm release name for templating')] = 'ci-release',
    ) -> str:
        '''Run Helm lint and template via local helm module'''
        chart = await self._helm(source=source)
        lint_stdout = await chart.lint(strict=True)
        template_stdout = await chart.template(values=values, release_name=release_name)
        return f'lint:\n{lint_stdout}\n\ntemplate:\n{template_stdout}'

    @function
    async def helm_publish(
        self,
        source: Annotated[dagger.Directory, Doc('Helm chart directory')],
        oci_url: Annotated[str, Doc('Destination OCI registry URL without chart name')],
        version: Annotated[str, Doc('Chart semver to publish')],
        app_version: Annotated[str | None, Doc('Optional appVersion override')] = None,
        username: Annotated[str | None, Doc('Registry username for login')] = None,
        password: Annotated[dagger.Secret | None, Doc('Registry password')] = None,
        insecure: Annotated[bool | None, Doc('Allow plain http pushes')] = False,
    ) -> str:
        '''Package and push helm chart via local helm module'''
        chart = await self._helm(source=source)
        if username and password:
            chart = chart.with_registry_login(username=username, password=password)
        return await chart.push(
            oci_url=oci_url,
            version=version,
            app_version=app_version or '',
            insecure=insecure,
        )

    @function
    async def helm_verify_changed_charts(
        self,
        source: Annotated[dagger.Directory, Doc('Repository root directory')],
        target_branch: Annotated[str, Doc('Target branch or ref to diff against')] = 'master',
        charts_path: Annotated[str | None, Doc('Charts directory (relative to repo root)')] = None,
        libs_path: Annotated[str | None, Doc('Libraries directory (relative to repo root)')] = None,
        values: Annotated[dagger.File | None, Doc('Optional values.yaml file')] = None,
        release_name: Annotated[str, Doc('Helm release name for templating')] = 'ci-release',
    ) -> list[str]:
        '''Verify changed charts/libs and optionally publish feature versions'''
        diff_paths = [path for path in (charts_path, libs_path) if path]
        chart_paths = await self._get_changed_paths(
            source=source,
            target_branch=target_branch,
            diff_paths=diff_paths,
        )
        if not chart_paths:
            return []

        outputs: list[str] = []
        for chart_path in chart_paths:
            chart_dir = source.directory(chart_path)
            chart = await self._helm(source=chart_dir)
            metadata = yaml.safe_load(await chart.get_chart_info()) or {}
            chart_name = str(metadata.get('name', '')).strip()
            chart_version = str(metadata.get('version', '')).strip()
            if not chart_name or not chart_version:
                outputs.append(
                    f"{chart_path}: skipped (missing name/version in Chart.yaml)"
                )
                continue
            verify_out = await self.helm_verify(
                source=chart_dir,
                values=values,
                release_name=release_name,
            )

            summary_lines = [f'{chart_path}:', verify_out]
            outputs.append('\n'.join(summary_lines))
        return outputs
