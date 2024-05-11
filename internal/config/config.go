package config

import (
	"bufio"
	"os"
	"strings"
)

var (
	configFileName string
)

// Config структура представляет файл конфигурации INI
type Config struct {
	data map[string]map[string]string
}

func Init() {
	configFileName = "/home/admin/Trinity_go/configs/trinity.ini"
}

// NewConfig создает новый экземпляр Config из файла
func InitConfig() (*Config, error) {
	file, err := os.Open(configFileName)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	cfg := &Config{
		data: make(map[string]map[string]string),
	}

	var currentSection string
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())

		// Пропускаем комментарии и пустые строки
		if line == "" || strings.HasPrefix(line, ";") || strings.HasPrefix(line, "#") {
			continue
		}

		// Обработка секций
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			currentSection = strings.TrimSpace(strings.TrimSuffix(strings.TrimPrefix(line, "["), "]"))
			cfg.data[currentSection] = make(map[string]string)
			continue
		}

		// Обработка параметров
		parts := strings.SplitN(line, "=", 2)
		if len(parts) == 2 {
			key := strings.TrimSpace(parts[0])
			value := strings.TrimSpace(parts[1])
			cfg.data[currentSection][key] = value
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, err
	}

	return cfg, nil
}

// Get возвращает значение параметра из определенной секции
func (c *Config) Get(section, key string) (string, bool) {
	if val, ok := c.data[section]; ok {
		if v, ok := val[key]; ok {
			return v, true
		}
	}
	return "", false
}
