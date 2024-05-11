package node

type Config struct {
	Self    []Node   `json:"self"`
	Nodes   []Node   `json:"nodes"`
	Cluster []string `json:"cluster"`
}
