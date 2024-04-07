package server

import (
	"context"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
)

// https://gin-gonic.com/docs/examples/graceful-restart-or-stop/

type Server struct {
	version string
	srv     *http.Server
}

func NewServer(version string) *Server {
	return &Server{version: version}
}

func (s *Server) Run() {
	r := gin.Default()
	r.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"msg":     "Hello World",
			"version": s.version,
		})
	})
	s.srv = &http.Server{
		Addr:    ":8080",
		Handler: r,
	}
	if err := s.srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("listen: %s\n", err)
	}
}

func (s *Server) Stop(ctx context.Context) {
	if err := s.srv.Shutdown(ctx); err != nil {
		log.Fatalf("Server Shutdown Failed:%+v", err)
	}
	log.Println("Server Exited Properly")
}
