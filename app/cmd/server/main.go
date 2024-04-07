package main

import (
	"117503445/traefik-zero-downtime-deployment-example/app/internal/server"
	"os"
)

func main() {

	// read version from env
	ver := os.Getenv("VER")

	server := server.NewServer(ver)
	server.Run()
}
