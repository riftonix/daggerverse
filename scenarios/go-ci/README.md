# Go CI

`verify-app` checks one Go executable package in a source directory with a root
`go.mod`. It checks formatting with `gofmt -l`, runs `go test ./...` from the
module root, and builds the selected application. The formatting scan skips
`.git` and `vendor`. Tests and compilation still receive the full source tree,
including vendored dependencies and files used by `go:embed`.

Pass the source directory as `--source` and the package directory as `--package`.
Use `.` if the application is at the module root. The package must be a single
`main` package in the root module. On success, the call returns a text summary.
On failure, it reports the failed check and its diagnostics. The call does not
rewrite source files or export the binary. It works without Git metadata or
publication credentials.

Tests and compilation use the selected Go image's normal CGO and linker
settings. The scenario does not add strip flags.

## Verify Kelm and Kafgres

From the Daggerverse root with both repositories checked out next to it:

```bash
dagger -m ./scenarios/go-ci call --source=../kelm verify-app --package=./cmd/kelm
dagger -m ./scenarios/go-ci call --source=../kafgres verify-app --package=./cmd/kafgres
```

## Override the Go runtime

The scenario delegates the Go checks to the local [Go module](../../modules/go/README.md).
The default is the public `docker.io/library/golang` image [pinned in the scenario](src/go_ci/main.py)
and managed by Renovate. Set `--go-image-registry`, `--go-image-repository`, or `--go-image-tag` before
`verify-app` to override the corresponding part of the image reference. The
image needs `go`, `gofmt`, `sh`, and `find`; provide a C toolchain if the project
uses CGO.

Go commands run as UID `65532` by default. Set `--go-container-user-id` to select
a different numeric UID. The module configures writable caches and temporary paths
for that UID.

```bash
dagger -m ./scenarios/go-ci call --source=../kelm --go-image-tag=1.26.11 verify-app --package=./cmd/kelm
dagger -m ./scenarios/go-ci call --source=../kelm --go-container-user-id=12345 verify-app --package=./cmd/kelm
```

The selected image supplies the toolchain for every check. With `GOTOOLCHAIN=local`,
Go does not download another toolchain: the root `go.mod`'s `go` directive must be
compatible with the image, while a newer `toolchain` recommendation does not set
an additional minimum. `GOWORK=off` keeps verification in root-module mode even
when the source contains `go.work`.

## Scenario tests

```bash
make tests scenario go-ci
```

See the [Daggerverse authoring guide](../../docs/how-to/write-dagger-ci-modules-and-tests.md)
for the test module conventions.
