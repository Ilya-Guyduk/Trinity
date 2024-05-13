package rpcserver

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"net/rpc"
	"trinity_go/internal/config"
	"trinity_go/internal/logger"

	"github.com/rs/xid"
)

var (
	cfg *config.Config
)

type Item struct {
	Name  string `json:"name"`
	Price int    `json:"price"`
}

type NodeData struct {
	Self    []Node `json:"self"`
	Nodes   []Node `json:"nodes"`
	Cluster []Node `json:"cluster"`
}

type Node struct {
	ID       string   `json:"id"`
	Hostname string   `json:"hostname"`
	Host     string   `json:"host"`
	Port     int      `json:"port"`
	Type     string   `json:"type"`
	Active   string   `json:"active"`
	Cpu      string   `json:"cpu"`
	Memory   string   `json:"memory"`
	Services []string `json:"services"`
}

type TrinityServer struct{}

// Метод RegisterNode для TrinityServer
func (t *TrinityServer) RegisterNode(nodeData Node, reply *Node) error {

	// Создание идентификатора события
	event_id := xid.New().String()
	logger.Info("[*TrinityServer][RegisterNode][%s]> call registration!", event_id)

	// Загружаем существующие данные из файла
	items, err := loadItems()
	if err != nil {
		return err
	}

	// Добавляем новую ноду в блок self
	items.Nodes = append(items.Nodes, nodeData)

	// Сохраняем обновленные данные в файл
	err = saveItems(items)
	if err != nil {
		return err
	}

	// Возвращаем обновленные данные в ответе
	*reply = items.Self[0]

	return nil
}

func (t *TrinityServer) Ping(request string, reply *string) error {
	// Создание идентификатора события
	event_id := xid.New().String()
	logger.Info("[*TrinityServer][Ping][%s]> call ping", event_id)
	*reply = "pong"
	return nil
}

func (t *TrinityServer) AddItem(item Node, reply *string) error {

	// Создание идентификатора события
	event_id := xid.New().String()
	logger.Info("[*TrinityServer][AddItem][%s]> AddItem...", event_id)

	// Load existing items from trinity.json
	items, err := loadItems()
	if err != nil {
		return err
	}

	// Add new node
	items.Nodes = append(items.Nodes, item)

	// Save updated items to trinity.json
	err = saveItems(items)
	if err != nil {
		return err
	}

	*reply = "Item added successfully"
	return nil
}

func (t *TrinityServer) RemoveItem(ID string, reply *string) error {
	// Load existing items from trinity.json
	items, err := loadItems()
	if err != nil {
		return err
	}

	// Find and remove item by name
	for i, item := range items.Nodes {
		if item.ID == ID {
			items.Self = append(items.Self[:i], items.Self[i+1:]...)
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

func loadItems() (NodeData, error) {
	filePath, ok := cfg.Get("Server", "json_file")
	if !ok {
		return NodeData{}, nil
	}

	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		return NodeData{}, err
	}

	// Разбор JSON данных в структуру NodeData
	var nodeData NodeData
	err = json.Unmarshal(data, &nodeData)
	if err != nil {
		return NodeData{}, err
	}

	return nodeData, nil
}

func saveItems(items NodeData) error {
	filePath, ok := cfg.Get("Server", "json_file")
	if !ok {
		return nil
	}

	data, err := json.MarshalIndent(items, "", "  ")
	if err != nil {
		return err
	}

	err = ioutil.WriteFile(filePath, data, 0644)
	if err != nil {
		return err
	}

	return nil
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		logger.Info("Received request from %s for %s", r.RemoteAddr, r.URL.Path)
		next.ServeHTTP(w, r)
	})
}

func StartServer(config *config.Config) {
	cfg = config
	logger.Info("[RPC-SERVER][StartServer]> Init server...")
	// Create RPC server
	trinityServer := new(TrinityServer)
	rpc.Register(trinityServer)
	http.Handle("/", loggingMiddleware(rpc.DefaultServer))

	// Get server configuration
	host, ok := cfg.Get("Server", "Host")
	if !ok {
		log.Fatalf("[RPC][StartServer]> Host not found in configuration")
	}

	port, ok := cfg.Get("Server", "Port")
	if !ok {
		log.Fatalf("[RPC][StartServer]> Port not found in configuration")
	}

	// Form server address
	serverAddr := net.JoinHostPort(host, port)

	logger.Dev("[RPC][StartServer]> Init_srv_set: serverAddr[%s]", serverAddr)

	// Start RPC server
	l, err := net.Listen("tcp", serverAddr)
	if err != nil {
		log.Fatalf("[RPC][StartServer]> Failed to listen: %v", err)
	}
	defer l.Close()

	err = http.Serve(l, nil)
	if err != nil {
		log.Fatalf("[RPC][StartServer]> Failed to serve: %v", err)
	}
	logger.Info("[RPC][StartServer]> RPC server listening on %s", serverAddr)
}
