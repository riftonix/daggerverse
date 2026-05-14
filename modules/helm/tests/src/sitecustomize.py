"""Python startup customization for the Helm test module."""

import os

os.environ.setdefault("OTEL_SDK_DISABLED", "true")
