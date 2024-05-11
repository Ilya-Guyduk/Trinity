package node

type Node struct {
	ID       string `json:"id"`
	Hostname string `json:"hostname"`
	Host     string `json:"host"`
	Port     int    `json:"port"`
	State    string `json:"state"`
	Role     string `json:"role"`
	CPU      string `json:"cpu"`
	Memory   string `json:"memory"`
	Services string `json:"services"`
}
