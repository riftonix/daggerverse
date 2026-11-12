#!/bin/sh
set -eu
if [ "$DRY_RUN" = true ]; then
  echo preview-only-marker
else
  echo apply-only-marker
fi
