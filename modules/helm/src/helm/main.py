from typing import Annotated, Self

import yaml
import dagger
from dagger import Doc, dag, function, object_type


@object_type
class Helm:
    '''
    Dagger-ci helm module
    '''
    source: dagger.Directory
    image_registry: str
    image_repository: str
    image_tag: str
    user_id: str
    container_: dagger.Container | None

    @classmethod
    async def create(
        cls,
        source: Annotated[dagger.Directory, Doc('Helm chart host path')],
        image_registry: Annotated[str | None, Doc('Helm image registry')] = 'docker.io',
        image_repository: Annotated[str | None, Doc('Helm image repositroy')] = 'alpine/helm',
        image_tag: Annotated[str | None, Doc('Helm image tag')] = '3.18.6',
        user_id: Annotated[str | None, Doc('Helm image user')] = '65532',
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
        '''Creates container with configured helm'''
        if self.container_:
            return self.container_
        self.container_ = (
            dag.container().from_(address=f'{self.image_registry}/{self.image_repository}:{self.image_tag}')
            .with_user(self.user_id)
            .with_exec(['mkdir', '-p', '-m', '770', '/tmp/helm/registry'])
            .with_env_variable(
                'HELM_REGISTRY_CONFIG',
                '/tmp/helm/registry/config.json',
            )
            .with_env_variable(
                'HELM_CACHE_HOME',
                '/tmp/helm/registry',
            )
            .with_new_file(
                '$HELM_REGISTRY_CONFIG',
                contents='{}',
                owner=self.user_id,
                permissions=0o600,
                expand=True,
            )
            .with_env_variable('HELM_CHART_PATH', '/tmp/helm/chart')
            .with_directory('$HELM_CHART_PATH', self.source, owner=self.user_id, expand=True)
            .with_workdir('$HELM_CHART_PATH', expand=True)
            .with_entrypoint(['/usr/bin/helm'])
        )
        return self.container_

    @function
    def with_registry_login(
        self,
        username: Annotated[str, Doc('Registry username')],
        password: Annotated[dagger.Secret, Doc('Registry password')],
        address: Annotated[str | None, Doc('Registry host')] = 'docker.io',
    ) -> Self:
        '''Function for helm registry authentication'''
        container: dagger.Container = self.container()
        cmd = [
            'sh',
            '-c',
            (
                f'helm registry login {address}'
                f' --username {username}'
                ' --password ${REGISTRY_PASSWORD}'
            ),
        ]
        self.container_ = container.with_secret_variable(
            'REGISTRY_PASSWORD', password
        ).with_exec(cmd, use_entrypoint=False)
        return self

    @function
    def with_dependency_update(
        self,
    ) -> Self:
        '''Functions which runs helm dependency update'''
        container: dagger.Container = self.container()
        cmd: list[str] = ['dependency', 'update', '.']
        self.container_ = container.with_exec(cmd, use_entrypoint=True)
        return self

    @function
    async def lint(
        self,
        strict: Annotated[bool | None, Doc('Fail on lint warnings')] = False,
        errors_only: Annotated[bool | None, Doc('Print only warnings and errors')] = False,
    ) -> str:
        '''Functions for helm chart linting'''
        container: dagger.Container = self.container()
        cmd: list[str] = ['lint', '.']
        if strict:
            cmd.extend(['--strict'])
        if errors_only:
            cmd.extend(['--quiet'])
        return (
            await container
            .with_exec(cmd, use_entrypoint=True)
            .stdout()
        )

    @function
    async def template(
        self,
        values: Annotated[dagger.File | None, Doc('Values.yaml file')] = None,
        release_name: Annotated[str, Doc('Release name')] = 'ci-release',
    ) -> str:
        '''Templates helm chart'''
        await self.lint(strict=True)
        chart_yaml = await self.source.file('Chart.yaml').contents()
        if yaml.safe_load(chart_yaml).get('type') == 'library':
            print('Warning: helm template is not acceptable for library charts (type: library)')
            return ''
        container: dagger.Container = self.container()
        cmd: list[str] = ['template', release_name, '.']
        if values:
            container = container.with_file('values.yaml', values)
            cmd.extend(['-f values.yaml'])
        return await container.with_exec(cmd, use_entrypoint=True).stdout()

    @function
    async def package(
        self,
        app_version: Annotated[
            str | None, Doc('Set the appVersion on the chart to this version')
        ] = '',
        version: Annotated[
            str | None, Doc('Set the version on the chart to this semver version')
        ] = '',
    ) -> dagger.File:
        '''Packages a chart into a versioned chart archive file'''
        await self.template()
        container: dagger.Container = self.container()
        container = container.with_env_variable('HELM_CHART_DEST_PATH', '/tmp/helm/')
        cmd = ['package', '.', '--destination', '$HELM_CHART_DEST_PATH']
        if app_version:
            cmd.extend(['--app-version', app_version])
        if version:
            cmd.extend(['--version', version])

        dest_dir: dagger.Directory = await container.with_exec(
            cmd, use_entrypoint=True, expand=True
        ).directory('$HELM_CHART_DEST_PATH', expand=True)
        dest_files: list[str] = await dest_dir.glob('*.tgz')

        return dest_dir.file(dest_files[0])

    @function
    async def push(
        self,
        oci_url: Annotated[str, Doc('Oci package address without package name and url')],
        version: Annotated[
            str | None, Doc('Set the version on the chart to this semver version')
        ] = '',
        insecure: Annotated[
            bool | None, Doc('Use insecure HTTP connections for the chart upload')
        ] = False,
        app_version: Annotated[
            str | None, Doc('Set the appVersion on the chart to this version')
        ] = '',
    ) -> str:
        '''Function for helm chart publishing'''
        chart: dagger.File = await self.package(
            app_version=app_version,
            version=version,
        )
        cmd = ['push', '$HELM_CHART', f'oci://{oci_url}']
        if insecure:
            cmd.extend(['--plain-http'])
        container: dagger.Container = self.container()
        container = (
            container.with_env_variable('HELM_CHART', '/tmp/chart.tgz')
            .with_file('$HELM_CHART', chart, owner=self.user_id, expand=True)
            .with_exec(cmd, use_entrypoint=True, expand=True)
        )

        return await container.stdout()

    @function
    async def get_chart_version(self) -> str:
        '''Return chart metadata from `helm show chart` as YAML string'''
        container: dagger.Container = self.container()
        cmd = ['show', 'chart', '.']
        chart_yaml = await container.with_exec(cmd, use_entrypoint=True).stdout()
        metadata = yaml.safe_load(chart_yaml) or {}
        chart_version = str(metadata.get('version', '')).strip()
        return chart_version

    @function
    async def is_already_published(
        self,
        oci_chart_url: Annotated[str, Doc('Oci package address with chart name')],
        version: Annotated[str, Doc('Chart version to check')],
        insecure: Annotated[
            bool | None, Doc('Use insecure HTTP connections for the registry')
        ] = False,
    ) -> bool:
        '''Check if chart version exists in OCI registry'''
        cmd = ['show', 'chart', f'oci://{oci_chart_url}', '--version', version]
        if insecure:
            cmd.extend(['--plain-http'])
        container: dagger.Container = self.container()
        try:
            await container.with_exec(cmd, use_entrypoint=True).stdout()
            return True
        except dagger.ExecError:
            return False
