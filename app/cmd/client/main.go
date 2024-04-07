package main

import "net/http"

func main() {
	req, err := http.NewRequest("GET", "http://localhost:8080", nil)
	if err != nil {
		panic(err)
	}

	if resp, err := http.DefaultClient.Do(req); err != nil {
		panic(err)
	} else {
		if resp.StatusCode != http.StatusOK {
			panic("expected status OK")
		}
	}
}
