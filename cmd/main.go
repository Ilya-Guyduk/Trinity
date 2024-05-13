package main

import (
	"log"
	"trinity_go/internal/config"
	"trinity_go/internal/logger"
	"trinity_go/rpcclient"
	"trinity_go/rpcserver"
)

/*
Основная функция точки входа
*/
func main() {
	// Initialize configuration
	config.Init()
	cfg, err := config.InitConfig()
	if err != nil {
		log.Fatalf("[MAIN][main]> Failed to load configuration: %v", err)
	}

	// Initialize logger
	if err := logger.InitLogger(cfg); err != nil {
		log.Fatalf("[MAIN][main]> Failed to initialize logger: %v", err)
	}

	// Start RPC server and client in a separate goroutine
	go rpcserver.StartServer(cfg)
	go rpcclient.StartClient(cfg)

	logger.Info("[MAIN][main]> Application started")

	select {}
}
