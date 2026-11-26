package greeting

import "testing"

func TestGreeting(t *testing.T) {
	if Hello != "hello" {
		t.Fatalf("unexpected greeting: %q", Hello)
	}
}
