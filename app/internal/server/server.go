package server

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

type Server struct {
	version string
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
	r.Run() // listen and serve on 0.0.0.0:8080 (for windows "localhost:8080")
}
