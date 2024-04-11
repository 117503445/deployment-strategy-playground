package server

import (
	"context"
	"log"
	"net/http"
	"time"

	"fmt"
	"os"

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
	r := gin.New()
	r.Use(gin.LoggerWithFormatter(func(param gin.LogFormatterParams) string {
		// your custom format
		return fmt.Sprintf("[GIN] %s \"%s %s %s %d %s %s\"\n",
			param.TimeStamp.Format("2006-01-02 15:04:05.000000"),
			param.Method,
			param.Path,
			param.Request.Proto,
			param.StatusCode,
			param.Latency,
			param.ErrorMessage,
		)
	}))
	r.Use(gin.Recovery())

	r.GET("/", func(c *gin.Context) {
		time.Sleep(500 * time.Millisecond)
		c.JSON(http.StatusOK, gin.H{
			"msg":      "Hello World",
			"version":  s.version,
			"hostname": os.Getenv("HOSTNAME"),
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
