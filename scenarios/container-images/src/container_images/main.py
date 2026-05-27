from dagger import function, object_type


@object_type
class ContainerImages:
    """Container image scenario entrypoint."""

    @function
    def module(self) -> str:
        """Return the scenario name."""
        return "container-images"
