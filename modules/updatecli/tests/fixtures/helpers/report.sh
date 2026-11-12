#!/bin/sh
set -eu
printf '%s\n' 'helper-stderr-marker' >&2
printf '%s:%s\n' "${UPDATECLI_TEST_PLAIN:?}" "${UPDATECLI_TEST_SECRET:?}"
