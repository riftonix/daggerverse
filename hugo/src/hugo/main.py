from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type, DefaultPath


@object_type
class Hugo:
    source: dagger.Directory
    image_registry: str
    image_repository: str
    image_tag: str
    container_user: str
    container_: dagger.Container | None

    @classmethod
    async def create(
        cls,
        source: Annotated[
            dagger.Directory,
            DefaultPath('./'),
            Doc('Hugo site directory'),
        ],
        image_registry: Annotated[str | None, Doc('Hugo image registry')] = 'docker.io',
        image_repository: Annotated[str | None, Doc('Hugo image repository')] = 'hugomods/hugo',
        image_tag: Annotated[str | None, Doc('Hugo image tag')] = 'exts-0.154.2',
        container_user: Annotated[str | None, Doc('Hugo image user')] = '65532',
    ):
        '''Constructor'''
        return cls(
            source=source,
            image_registry=image_registry,
            image_repository=image_repository,
            image_tag=image_tag,
            container_user=container_user,
            container_=None,
        )

    @function
    def container(self) -> dagger.Container:
        '''Creates container with configured Hugo'''
        if self.container_:
            return self.container_
        self.container_ = (
            dag.container()
            .from_(address=f'{self.image_registry}/{self.image_repository}:{self.image_tag}')
            .with_user(self.container_user)
            .with_env_variable('NPM_CONFIG_CACHE', '/tmp/npm-cache')
            .with_env_variable('NPM_CONFIG_USERCONFIG', '/tmp/.npmrc')
            .with_exec(['mkdir', '-p', '-m', '770', '/tmp/hugo/site'])
            .with_directory('/tmp/hugo/site', self.source, owner=self.container_user)
            .with_workdir('/tmp/hugo/site')
            .with_exposed_port(1313)
        )
        return self.container_

    @function
    async def build(
        self,
        hugo_theme_url: Annotated[str, Doc('Hugo theme module URL')],   # github.com/google/docsy@v0.13.0
        site_base_url: Annotated[str, Doc('Site base URL for Hugo')],   # example.com
        npm_registry_url: Annotated[str, Doc('NPM registry URL')] = 'https://registry.npmjs.org/',
    ) -> dagger.Directory:
        '''Build Hugo site and return the public directory'''
        container = (
            self.container()
            .with_env_variable('SITE_THEME_URL', hugo_theme_url)
            .with_env_variable('SITE_BASE_URL', site_base_url)
            .with_env_variable('NPM_REGISTRY_URL', npm_registry_url)
            .with_exec(['hugo', 'version'])
            .with_exec(['hugo', 'mod', 'get', '-u', '$SITE_THEME_URL'], expand=True)
            .with_exec(['npm', 'config', 'set', 'registry', '$NPM_REGISTRY_URL'], expand=True)
            .with_exec(['npm', 'install', 'autoprefixer'])
            .with_exec([
                'hugo',
                '--minify',
                '--destination',
                'public',
                '--baseURL',
                '$SITE_BASE_URL',
                '--forceSyncStatic',
                '--cleanDestinationDir',
            ], expand=True)
        )
        public_dir = container.directory('public')
        return public_dir
