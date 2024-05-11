package node

import (
	"encoding/json"
	"errors"
	"io/ioutil"
)

// NodeRepository определяет интерфейс для работы с узлами.
type NodeRepository interface {
	AddNode(node Node) error
	RemoveNode(id string) error
	UpdateNode(node Node) error
	GetNodeByID(id string) (Node, error)
}

// FileNodeRepository реализует интерфейс NodeRepository и предоставляет методы для работы с узлами, сохраненными в файле.
type FileNodeRepository struct {
	FilePath string // FilePath - путь к файлу, в котором хранятся данные об узлах
}

// AddNode добавляет новый узел в файл с данными об узлах.
func (repo *FileNodeRepository) AddNode(node Node) error {
	// Читаем данные об узлах из файла
	nodes, err := repo.readNodesFromFile()
	if err != nil {
		return err
	}
	// Добавляем новый узел в список
	nodes = append(nodes, node)
	// Записываем обновленные данные об узлах в файл
	return repo.writeNodesToFile(nodes)
}

// RemoveNode удаляет узел из файла по его идентификатору.
func (repo *FileNodeRepository) RemoveNode(id string) error {
	// Читаем данные об узлах из файла
	nodes, err := repo.readNodesFromFile()
	if err != nil {
		return err
	}
	// Ищем узел по его идентификатору и удаляем его из списка
	index := -1
	for i, node := range nodes {
		if node.ID == id {
			index = i
			break
		}
	}
	if index == -1 {
		return errors.New("node not found")
	}
	nodes = append(nodes[:index], nodes[index+1:]...)
	// Записываем обновленные данные об узлах в файл
	return repo.writeNodesToFile(nodes)
}

// UpdateNode обновляет информацию об узле в файле.
func (repo *FileNodeRepository) UpdateNode(node Node) error {
	// Читаем данные об узлах из файла
	nodes, err := repo.readNodesFromFile()
	if err != nil {
		return err
	}
	// Ищем узел по его идентификатору и обновляем информацию
	index := -1
	for i, n := range nodes {
		if n.ID == node.ID {
			index = i
			break
		}
	}
	if index == -1 {
		return errors.New("node not found")
	}
	nodes[index] = node
	// Записываем обновленные данные об узлах в файл
	return repo.writeNodesToFile(nodes)
}

// GetNodeByID получает узел из файла по его идентификатору.
func (repo *FileNodeRepository) GetNodeByID(id string) (Node, error) {
	// Читаем данные об узлах из файла
	nodes, err := repo.readNodesFromFile()
	if err != nil {
		return Node{}, err
	}
	// Ищем узел по его идентификатору
	for _, node := range nodes {
		if node.ID == id {
			return node, nil
		}
	}
	return Node{}, errors.New("node not found")
}

// readNodesFromFile читает содержимое файла JSON и возвращает список узлов.
func (repo *FileNodeRepository) readNodesFromFile() ([]Node, error) {
	// Читаем содержимое файла
	fileContent, err := ioutil.ReadFile(repo.FilePath)
	if err != nil {
		return nil, err
	}
	// Декодируем содержимое файла в структуру данных
	var data map[string][]Node
	if err := json.Unmarshal(fileContent, &data); err != nil {
		return nil, err
	}
	return data["nodes"], nil
}

// writeNodesToFile сериализует список узлов в формат JSON и записывает его в файл.
func (repo *FileNodeRepository) writeNodesToFile(nodes []Node) error {
	// Сериализуем данные в формат JSON
	data := map[string][]Node{"nodes": nodes}
	fileContent, err := json.MarshalIndent(data, "", "    ")
	if err != nil {
		return err
	}
	// Записываем данные в файл
	return ioutil.WriteFile(repo.FilePath, fileContent, 0644)
}
