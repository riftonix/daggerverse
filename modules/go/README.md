# Go

Reusable Dagger checks for Go source trees. Pass the source directory before the operation name:

```bash
dagger -m ./modules/go call --source=../my-app validate-package --package=./cmd/my-app
dagger -m ./modules/go call --source=../my-app check-format
dagger -m ./modules/go call --source=../my-app test
dagger -m ./modules/go call --source=../my-app build --package=./cmd/my-app
```

- `validate-package` returns the normalized path of a single `main` package in the root module. Use `.` for a root application.
- `check-format` reports files that need `gofmt` outside `.git` and `vendor`, without changing them.
- `test` runs `go test ./...` from the root module and returns the test output.
- `build` checks that the requested executable compiles without exporting the binary.

## Runtime

The default image is the Renovate-managed [Go image pin](src/go/main.py). Set `--image-registry`,
`--image-repository`, or `--image-tag` to override it. The image needs `go`, `gofmt`, `sh`, and `find`,
plus a C toolchain if the project uses CGO.

Commands run as UID `65532` by default. Use `--container-user-id` to select a different numeric UID.
The module gives that user writable home and temporary directories and separate Go module and build caches.

```bash
dagger -m ./modules/go call --source=../my-app --image-tag=1.26.11 --container-user-id=12345 test
```

Workspace mode and automatic toolchain downloads are disabled. Choose an image that meets the root
`go.mod` minimum. Format checks, tests, and builds leave the caller's source directory unchanged.

## Tests

```bash
make tests module go
```

See the [repository documentation](../../docs/README.md) for Dagger module conventions.
