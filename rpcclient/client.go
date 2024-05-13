package rpcclient

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/rpc"
	"os"
	"time"
	"trinity_go/internal/config"
	"trinity_go/internal/logger"

	"github.com/rs/xid"
)

var (
	cfg *config.Config
)

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

func NodeHandler(filePath string) {
	// Чтение данных из JSON файла
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		logger.Error("[RPC-CLIENT][NodeHandler]> Ошибка чтения файла:", err)
		return
	}

	// Разбор JSON данных в структуру NodeData
	var nodeData NodeData
	err = json.Unmarshal(data, &nodeData)
	if err != nil {
		logger.Error("[RPC-CLIENT][NodeHandler]> Ошибка разбора JSON:", err)
		return
	}

	// Теперь данные хранятся в переменной nodeData
	logger.Debug("[RPC-CLIENT][NodeHandler]> Содержимое JSON файла:", nodeData)

	// Запускаем отдельный поток для каждой ноды в блоке Nodes
	for _, node := range nodeData.Nodes {

		// Проверка, что нода не деактивирована
		if node.Active != "disable" {

			// Инициализация горутины для каждой ноды
			go func(n Node) {

				logger.Info("[RPC-CLIENT][NodeHandler][%s]> Запуск горутины", n.ID)

				// Цикл для отправки удаленной RPC команды Ping раз в секунду
				for {
					// Отправляем удаленную RPC команду
					if n.Active == "active" {

						//Ping
						err := sendPingCommand(n.Host, n.Port)
						if err != nil {
							logger.Error("[RPC-CLIENT][NodeHandler]> Ошибка отправки RPC команды Ping для ноды:", n.Hostname, err)
						}
					} else if n.Active == "unknown" {
						err := sendRegistrateCommand(n.Host, n.Port)
						if err != nil {
							logger.Error("[RPC-CLIENT][NodeHandler]> Ошибка отправки RPC команды Ping для ноды:", n.Hostname, err)
						}
					}
					// Ждем одну секунду перед отправкой следующей команды
					time.Sleep(time.Second)
				}
			}(node)
		} else {
			logger.Debug("[RPC-CLIENT][NodeHandler][%s]> Skeep node, Data - %s", node.ID, node)
		}
	}
}

func sendPingCommand(host string, port int) error {
	// Формируем адрес удаленного сервера
	serverAddress := fmt.Sprintf("%s:%d", host, port)

	// Устанавливаем соединение с удаленным сервером
	client, err := rpc.DialHTTP("tcp", serverAddress)
	if err != nil {
		return err
	}
	defer client.Close()

	var reply string
	// Отправляем удаленной серверу команду Ping
	err = client.Call("TrinityServer.Ping", "", &reply)
	if err != nil {
		return err
	}

	// Выводим ответ от сервера
	logger.Info("[RPC-CLIENT][sendPingCommand]> Ответ от сервера:", reply)

	return nil
}

func sendRegistrateCommand(host string, port int) error {
	logger.Info("[RPC-CLIENT][sendRegistrateCommand]> Send Reg...")

	// Загружаем существующие данные из файла
	items, err := loadItems()
	if err != nil {
		return err
	}
	myData := items.Self[0]
	// Формируем адрес удаленного сервера
	serverAddress := fmt.Sprintf("%s:%d", host, port)

	// Устанавливаем соединение с удаленным сервером
	client, err := rpc.DialHTTP("tcp", serverAddress)
	if err != nil {
		return err
	}
	defer client.Close()

	var reply string
	// Отправляем удаленной серверу команду Ping
	err = client.Call("TrinityServer.RegisterNode", myData, &reply)
	if err != nil {
		return err
	}

	// Выводим ответ от сервера
	logger.Info("[RPC-CLIENT][sendPingCommand]> Ответ от сервера:", reply)

	return nil
}

func StartClient(config *config.Config) {
	cfg = config
	logger.Info("[RPC-CLIENT][StartClient]> Init rpc-client...")

	// Путь к JSON файлу
	filePath, ok := cfg.Get("Server", "json_file")
	if !ok {
		logger.Error("[RPC][StartClient]> Error loading JSON file!")
	}

	// Проверка существования файла
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		logger.Warning("[RPC-CLIENT][StartClient]> No such file %s! Create new!", filePath)
		// Файл не существует - создаем новый
		nodeData := NodeData{
			Self:    []Node{},
			Nodes:   []Node{},
			Cluster: []Node{},
		}

		// Создание идентификатора ноды
		id := xid.New().String()

		// Создание демонстрационных данных для блока "self"
		selfData := []Node{
			{
				ID:       id,
				Hostname: "example-hostname",
				Host:     "example-host",
				Port:     1234,
				Type:     "example-type",
				Active:   "active",
				Cpu:      "example-cpu",
				Memory:   "example-memory",
				Services: []string{"service1", "service2"},
			},
		}

		// Обновление данных в блоке "self"
		nodeData.Self = selfData

		// Преобразование в JSON
		jsonData, err := json.MarshalIndent(nodeData, "", "  ")
		if err != nil {
			logger.Error("[RPC-CLIENT][StartClient]> Ошибка маршалинга JSON:", err)
			return
		}

		// Создание нового файла и запись в него данных
		err = ioutil.WriteFile(filePath, jsonData, 0644)
		if err != nil {
			logger.Error("[RPC-CLIENT][StartClient]> Ошибка записи в файл:", err)
			return
		}

		logger.Info("[RPC-CLIENT][StartClient]> New JSON was created:", filePath)

	}
	NodeHandler(filePath)

}
