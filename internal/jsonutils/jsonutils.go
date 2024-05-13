package jsonutils

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"trinity_go/internal/config"
)

// Node represents a node in the cluster
type Node struct {
	ID       string   `json:"id"`
	Hostname string   `json:"hostname"`
	Host     string   `json:"host"`
	Port     int      `json:"port"`
	Type     string   `json:"type"`
	Active   string   `json:"active"`
	CPU      string   `json:"cpu"`
	Memory   string   `json:"memory"`
	Services []string `json:"services"`
}

// Cluster represents the cluster information
type Cluster struct {
	Self    []Node `json:"self"`
	Nodes   []Node `json:"nodes"`
	Cluster []Node `json:"cluster"`
}

// LoadCluster loads cluster information from a JSON file
func LoadCluster(cfg *config.Config) (*Cluster, error) {

	filename, err := cfg.Get("Server", "json_file")

	data, err := ioutil.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	var cluster Cluster
	err = json.Unmarshal(data, &cluster)
	if err != nil {
		return nil, err
	}

	return &cluster, nil
}

// SaveCluster saves cluster information to a JSON file
func SaveCluster(cluster *Cluster, filename string) error {
	data, err := json.MarshalIndent(cluster, "", "    ")
	if err != nil {
		return err
	}

	err = ioutil.WriteFile(filename, data, 0644)
	if err != nil {
		return err
	}

	return nil
}

// AddNode adds a node to the cluster
func AddNode(cluster *Cluster, node Node) {
	cluster.Nodes = append(cluster.Nodes, node)
}

// RemoveNode removes a node from the cluster
func RemoveNode(cluster *Cluster, nodeID string) {
	for i, node := range cluster.Nodes {
		if node.ID == nodeID {
			cluster.Nodes = append(cluster.Nodes[:i], cluster.Nodes[i+1:]...)
			return
		}
	}
}

// PrintCluster prints cluster information
func PrintCluster(cluster *Cluster) {
	fmt.Println("Self:")
	for _, node := range cluster.Self {
		fmt.Printf("%+v\n", node)
	}

	fmt.Println("Nodes:")
	for _, node := range cluster.Nodes {
		fmt.Printf("%+v\n", node)
	}

	fmt.Println("Cluster:")
	for _, node := range cluster.Cluster {
		fmt.Printf("%+v\n", node)
	}
}
