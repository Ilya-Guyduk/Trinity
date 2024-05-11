package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"net/rpc"
	"trinity_go/internal/config"
	"trinity_go/internal/logger"
)

var (
	cfg        *config.Config
	host       string
	port       string
	serverAddr string
)

type Item struct {
	Name  string `json:"name"`
	Price int    `json:"price"`
}

type TrinityServer struct{}

func (t *TrinityServer) AddItem(item Item, reply *string) error {
	// Load existing items from trinity.json
	items, err := loadItems()
	if err != nil {
		return err
	}

	// Add new item
	items = append(items, item)

	// Save updated items to trinity.json
	err = saveItems(items)
	if err != nil {
		return err
	}

	*reply = "Item added successfully"
	return nil
}

func (t *TrinityServer) RemoveItem(name string, reply *string) error {
	// Load existing items from trinity.json
	items, err := loadItems()
	if err != nil {
		return err
	}

	// Find and remove item by name
	for i, item := range items {
		if item.Name == name {
			items = append(items[:i], items[i+1:]...)
			// Save updated items to trinity.json
			err = saveItems(items)
			if err != nil {
				return err
			}
			*reply = "Item removed successfully"
			return nil
		}
	}

	*reply = "Item not found"
	return nil
}

func loadItems() ([]Item, error) {
	file, err := ioutil.ReadFile("../configs/trinity.json")
	if err != nil {
		return nil, err
	}

	var items []Item
	err = json.Unmarshal(file, &items)
	if err != nil {
		return nil, err
	}

	return items, nil
}

func saveItems(items []Item) error {
	data, err := json.MarshalIndent(items, "", "  ")
	if err != nil {
		return err
	}

	err = ioutil.WriteFile("../configs/trinity.json", data, 0644)
	if err != nil {
		return err
	}

	return nil
}

func init() {
	config.Init()
	// Initialize configuration
	var err error
	cfg, err = config.InitConfig()
	if err != nil {
		log.Fatalf("[MAIN][init]> Failed to load configuration: %v", err)
	}

	if err := logger.InitLogger(cfg); err != nil {
		log.Fatalf("[MAIN][init]> Failed to initialize logger: %v", err)
	}

	var ok bool
	// Get server configuration
	host, ok = cfg.Get("Server", "Host")
	if !ok {
		log.Fatalf("[MAIN][init]> Host not found in configuration")
	}

	port, ok = cfg.Get("Server", "Port")
	if !ok {
		log.Fatalf("[MAIN][init]> Port not found in configuration")
	}

	// Формирование адреса сервера
	serverAddr = fmt.Sprintf("%s:%s", host, port)
	logger.Dev("[MAIN][init]> Init server setting: host:[%s]", serverAddr)
}

func main() {
	logger.Info("[MAIN][main]> Starting on %s", serverAddr)

	// Create RPC server
	trinityServer := new(TrinityServer)
	rpc.Register(trinityServer)
	rpc.HandleHTTP()

	// Start RPC server
	l, err := net.Listen("tcp", serverAddr)
	if err != nil {
		log.Fatalf("[MAIN][main]> Failed to listen: %v", err)
	}
	defer l.Close()

	logger.Info("[MAIN][main]> RPC server listening ")
	err = http.Serve(l, nil)
	if err != nil {
		log.Fatalf("[MAIN][main]> Failed to serve: %v", err)
	}
}
