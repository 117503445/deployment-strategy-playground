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

	log.Printf("Starting server version: %s, HOSTNAME: %s\n", ver, os.Getenv("HOSTNAME"))

	if buildText, err := os.ReadFile("build.txt"); err == nil {
		log.Printf("Build info: %s", string(buildText))
	}else{
		log.Printf("Failed to read build info: %s", err)
	}

	server := server.NewServer(ver)
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
}
