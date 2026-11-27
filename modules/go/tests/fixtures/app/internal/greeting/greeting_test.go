package greeting

import "testing"

func TestGreeting(t *testing.T) {
	if Greeting != "hello" {
		t.Fatalf("unexpected greeting: %q", Greeting)
	}
}
