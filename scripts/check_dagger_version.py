#!/usr/bin/env python3
"""Check that Dagger engine and CI CLI versions are aligned."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DAGGER_JSON_GLOB = "modules/**/dagger.json"
WORKFLOW_GLOB = ".github/workflows/*.y*ml"
DAGGER_VERSION_PATTERN = re.compile(r"^\s*DAGGER_VERSION:\s*([vV]?[0-9]+(?:\.[0-9]+){2})\s*$")


def normalize_version(version: str) -> str:
    """Return a version without a leading v prefix."""
    return version.removeprefix("v").removeprefix("V")


def dagger_json_files() -> list[Path]:
    """Return checked Dagger module metadata files."""
    return sorted(path for path in REPOSITORY_ROOT.glob(DAGGER_JSON_GLOB) if "sdk" not in path.parts)


def workflow_files() -> list[Path]:
    """Return GitHub Actions workflow files."""
    return sorted(REPOSITORY_ROOT.glob(WORKFLOW_GLOB))


def read_engine_versions() -> dict[Path, str]:
    """Read engineVersion values from Dagger module metadata."""
    versions: dict[Path, str] = {}

    for path in dagger_json_files():
        with path.open(encoding="utf-8") as file:
            data = json.load(file)

        version = data.get("engineVersion")
        if not isinstance(version, str):
            raise ValueError(f"{path.relative_to(REPOSITORY_ROOT)} has no string engineVersion")

        versions[path] = version

    return versions


def read_workflow_versions() -> dict[Path, str]:
    """Read DAGGER_VERSION values from GitHub Actions workflows."""
    versions: dict[Path, str] = {}

    for path in workflow_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            match = DAGGER_VERSION_PATTERN.match(line)
            if match:
                versions[path] = match.group(1)
                break

    return versions


def main() -> int:
    """Validate Dagger versions and print mismatches."""
    engine_versions = read_engine_versions()
    workflow_versions = read_workflow_versions()
    normalized_versions = {
        normalize_version(version) for version in [*engine_versions.values(), *workflow_versions.values()]
    }

    if not engine_versions:
        print("No modules/**/dagger.json files found.", file=sys.stderr)
        return 2

    if not workflow_versions:
        print("No DAGGER_VERSION values found in .github/workflows/*.y*ml.", file=sys.stderr)
        return 2

    if len(normalized_versions) == 1:
        version = normalized_versions.pop()
        print(f"Dagger versions are aligned: {version}")
        return 0

    print("Dagger versions are not aligned:", file=sys.stderr)
    for path, version in [*engine_versions.items(), *workflow_versions.items()]:
        print(f"  {path.relative_to(REPOSITORY_ROOT)}: {version}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
