package test

import (
	"net/http"
	"testing"

	"117503445/traefik-zero-downtime-deployment-example/app/internal/server"
)

func TestServer(t *testing.T) {
	go func() {
		server := server.NewServer("1.0.0")
		server.Run()
	}()

	req, err := http.NewRequest("GET", "http://localhost:8080", nil)
	if err != nil {
		t.Fatal(err)
	}

	if resp, err := http.DefaultClient.Do(req); err != nil {
		t.Fatal(err)
	} else {
		if resp.StatusCode != http.StatusOK {
			t.Fatalf("expected status OK; got %v", resp.Status)
		}
	}
}
