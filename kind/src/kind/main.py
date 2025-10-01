import dagger
from typing import Annotated
from dagger import Doc, dag, function, object_type


@object_type
class Kind:
    '''
    Dagger-ci helm module
    '''
    image_registry: str
    image_repository: str
    image_tag: str
    user: str
    container_: dagger.Container | None

    @classmethod
    async def create(
        cls,
        image_registry: Annotated[str | None, Doc('Helm image registry')] = 'docker.io',
        image_repository: Annotated[str | None, Doc('Helm image repositroy')] = 'docker',
        image_tag: Annotated[str | None, Doc('Helm image tag')] = '28.5.0-rc.1-dind',
        user: Annotated[str | None, Doc('Helm image user')] = '65532',
    ):
        '''Constructor'''
        return cls(
            image_registry=image_registry,
            image_repository=image_repository,
            image_tag=image_tag,
            user=user,
            container_=None,
        )

    @function
    def container(self) -> dagger.Container:
        '''Creates container with configured kind k8s cluster'''
        if self.container_:
            return self.container_
        self.container_ = (
            dag.container().from_(address=f'{self.image_registry}/{self.image_repository}:{self.image_tag}')
            .with_exec([
                "/bin/sh", "-c",
                "curl -Lo /usr/local/bin/kind https://kind.sigs.k8s.io/dl/v0.30.0/kind-linux-amd64 && chmod +x /usr/local/bin/kind"   # noqa E501
            ])
        )
        return self.container_
