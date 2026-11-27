package main

import (
	"os"
	"runtime"
	"testing"
)

func TestContainerUser(t *testing.T) {
	if uid := os.Getuid(); uid != 65532 {
		t.Fatalf("verification uses UID %d", uid)
	}
}

func TestToolchain(t *testing.T) {
	const expectedVersion = ""
	if expectedVersion != "" && runtime.Version() != expectedVersion {
		t.Fatalf("verification uses %s, want %s", runtime.Version(), expectedVersion)
	}
}
