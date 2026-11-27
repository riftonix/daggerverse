package main

import (
	"os"
	"testing"
)

func TestRuntime(t *testing.T) {
	if uid := os.Getuid(); uid != 65532 {
		t.Fatalf("Go commands use UID %d", uid)
	}
	moduleCache := os.Getenv("GOMODCACHE")
	buildCache := os.Getenv("GOCACHE")
	if moduleCache == buildCache {
		t.Fatal("module and build caches must use separate paths")
	}
	for _, dir := range []string{moduleCache, buildCache, os.Getenv("HOME"), os.Getenv("TMPDIR")} {
		if dir == "" {
			t.Fatal("cache, home, or temporary directory is unset")
		}
		file, err := os.CreateTemp(dir, "go-module-test-")
		if err != nil {
			t.Fatal(err)
		}
		file.Close()
		os.Remove(file.Name())
	}
}
