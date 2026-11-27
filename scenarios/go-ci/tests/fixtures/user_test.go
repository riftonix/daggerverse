package main

import (
	"os"
	"testing"
)

func TestContainerUser(t *testing.T) {
	if uid := os.Getuid(); uid != 65532 {
		t.Fatalf("verification uses UID %d", uid)
	}
}
