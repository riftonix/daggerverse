"""Git helpers for CI and release workflows, independent of the CI provider.

Compare explicit Git refs or commits to find changed files and directories.
Map changes to monorepo components to build a CI or release matrix. Configure
shared paths so changes to common files select all components.

Use an existing checkout with its `.git` directory to fetch refs and tags,
deepen shallow history, or create and push release tags.
Remote operations support both HTTPS token and SSH key authentication.
"""

from .main import Git as Git
