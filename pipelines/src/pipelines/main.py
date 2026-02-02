from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class Pipelines:
    async def _helm(
        self,
        source: dagger.Directory,
        image_registry: Annotated[str | None, Doc('Helm image registry')] = 'docker.io',
        image_repository: Annotated[str | None, Doc('Helm image repository')] = 'alpine/helm',
        image_tag: Annotated[str | None, Doc('Helm image tag')] = '3.18.6',
        container_user: Annotated[str | None, Doc('Helm image user')] = '65532',
    ):
        '''Return configured Helm module instance from local ./helm module'''
        return dag.helm(
            source=source,
            image_registry=image_registry,
            image_repository=image_repository,
            image_tag=image_tag,
            container_user=container_user,
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
        return f"lint:\n{lint_stdout}\n\ntemplate:\n{template_stdout}"

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
    async def helm_verify_changed(
        self,
        source: Annotated[dagger.Directory, Doc('Repository root directory')],
        target_branch: Annotated[str, Doc('Target branch or ref to diff against')] = 'master',
        diff_dir: Annotated[str | None, Doc('Subdirectory to scope the diff')] = '.',
        values: Annotated[dagger.File | None, Doc('Optional values.yaml file')] = None,
        release_name: Annotated[str, Doc('Helm release name for templating')] = 'ci-release',
    ) -> list[str]:
        '''Run helm_verify for each directory returned by git.get_changed_dirs'''
        git = dag.git(source=source)
        changed_dirs = await git.get_changed_dirs(
            target_branch=target_branch,
            diff_dir=diff_dir,
        )
        normalized_diff_dir = (diff_dir or '.').rstrip('/')
        outputs: list[str] = []
        for changed_dir in changed_dirs:
            if normalized_diff_dir in ('.', './'):
                chart_dir = changed_dir
            else:
                chart_dir = f"{normalized_diff_dir}/{changed_dir}"
            result = await self.helm_verify(
                source=source.directory(chart_dir),
                values=values,
                release_name=release_name,
            )
            outputs.append(f"{chart_dir}:\n{result}")
        return outputs
