"""Push the upstream fixture charts to a registry and keep its storage.

The registry runs only inside this exec, so the service that later serves the storage is
stateless and survives restarts between Dagger calls. Charts are read from
/tmp/upstream/<version>/<name> and pushed as <name>:<version>.
"""

import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.request

FIXTURE = pathlib.Path(__file__).parent
CHARTS = pathlib.Path("/tmp/upstream")
PACKAGES = pathlib.Path("/tmp/packages")
DIGESTS = pathlib.Path("/tmp/digests.json")
REGISTRY_BINARY = "/tmp/registry-bin/registry"
REGISTRY = "127.0.0.1:5000"
# This package also gets a cosign-style signature tag, which tag selection must ignore.
SIGNED = "nuc-demo:1.0.4"


def wait_for_registry() -> None:
    for _ in range(300):
        try:
            with urllib.request.urlopen(f"http://{REGISTRY}/v2/", timeout=1):
                return
        except OSError:
            time.sleep(0.1)
    sys.exit("fixture registry did not start")


def push(chart: pathlib.Path) -> str:
    """Package a chart as the version named by its parent directory, push it, and return its digest."""
    version = chart.parent.name
    destination = PACKAGES / version / chart.name
    subprocess.run(
        ["helm", "package", str(chart), "--version", version, "--destination", str(destination)],
        check=True,
    )
    archive = next(destination.glob("*.tgz"))
    pushed = subprocess.run(
        ["helm", "push", str(archive), f"oci://{REGISTRY}/nuc", "--plain-http"],
        check=True,
        capture_output=True,
        text=True,
    )
    return re.search(r"Digest:\s*(sha256:[0-9a-f]{64})", pushed.stdout + pushed.stderr)[1]


def sign(name: str, digest: str) -> None:
    """Tag a copy of the package manifest as <digest>.sig, as cosign does."""
    base_url = f"http://{REGISTRY}/v2/nuc/{name}/manifests"
    request = urllib.request.Request(
        f"{base_url}/{digest}",
        headers={"Accept": "application/vnd.oci.image.manifest.v1+json"},
    )
    with urllib.request.urlopen(request) as response:
        manifest, media_type = response.read(), response.headers["Content-Type"]
    signature = urllib.request.Request(
        f"{base_url}/{digest.replace(':', '-')}.sig",
        data=manifest,
        method="PUT",
        headers={"Content-Type": media_type},
    )
    with urllib.request.urlopen(signature):
        pass


def main() -> None:
    registry = subprocess.Popen([REGISTRY_BINARY, "serve", str(FIXTURE / "config.yml")])
    try:
        wait_for_registry()
        digests = {f"{chart.name}:{chart.parent.name}": push(chart) for chart in sorted(CHARTS.glob("*/*"))}
        sign(SIGNED.split(":")[0], digests[SIGNED])
        DIGESTS.write_text(json.dumps(digests, sort_keys=True))
    finally:
        registry.terminate()
        registry.wait()


if __name__ == "__main__":
    main()
