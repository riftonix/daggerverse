from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class Opentofu:
    container_image: str
    executor: str
    container_: dagger.Container | None

    @classmethod
    async def create(
        cls,
        container_image: Annotated[str | None, Doc('TF container image')] = ('ghcr.io/opentofu/opentofu:latest'),
        executor: Annotated[str, Doc('Choice of IaC executor')] = 'tofu'
    ):
        '''Constructor'''
        return cls(
            container_image=container_image,
            executor=executor,
            container_=None
        )

    @function
    def container(self) -> dagger.Container:
        '''Returns container'''
        if self.container_:
            return self.container_
        container: dagger.Container = dag.container()
        self.container_ = (
            container.from_(address=self.container_image)
            .with_env_variable('TF_CLI_CONFIG_FILE', '/src/.tf.rc')
        )
        return self.container_

    @function
    async def lint(
        self,
        source: Annotated[dagger.Directory, Doc('IaC project path')]
    ) -> str:
        '''Verify that the manifests is well-formed'''
        container: dagger.Container = (
            self.container()
            .with_directory('/src', source)
            .with_workdir('/src')
        )
        lint_cmd: list[str] = [self.executor, 'fmt', '-recursive', '-check', '-diff', '-no-color']
        init_cmd: list[str] = [self.executor, 'init']
        validate_cmd: list[str] = [self.executor, 'validate', '-no-color']
        return await container.with_exec(lint_cmd).with_exec(init_cmd).with_exec(validate_cmd).stdout()
