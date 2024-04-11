package main

import (
	"117503445/traefik-zero-downtime-deployment-example/app/internal/server"
	"os"

	"context"
	"log"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	// read version from env
	ver := os.Getenv("VER")

	if buildText, err := os.ReadFile("build.txt"); err == nil {
		log.Printf("Build info: %s", string(buildText))
	} else {
		log.Printf("Failed to read build info: %s", err)
	}

	isGraceENV := os.Getenv("GRACE")
	isGrace := isGraceENV == "true"

	log.Printf("Starting server version: %s, HOSTNAME: %s, isGrace: %v\n", ver, os.Getenv("HOSTNAME"), isGrace)
	server := server.NewServer(ver)

	if isGrace {
		go func() {
			server.Run()
		}()

		quit := make(chan os.Signal, 1)
		signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
		<-quit
		log.Println("Shutting down server...")

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		server.Stop(ctx)

		log.Println("Server exiting")
	} else {
		server.Run()
	}
}
