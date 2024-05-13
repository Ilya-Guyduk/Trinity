package logger

import (
	"io"
	"log"
	"os"
	"trinity_go/internal/config"
)

// logLevel содержит текущий уровень логирования.
var (
	Logger *log.Logger
	level  int
)

// InitLogger инициализирует логгер на основе конфигурации.
func InitLogger(cfg *config.Config) error {
	// Получение имени файла лога из конфигурации.
	filename, ok := cfg.Get("Logging", "Log_file")
	if !ok {
		log.Fatalf("Failed to read logfile configuration")
	}

	// Открытие файла лога для записи.
	file, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		// Если файл не существует, создаем новый.
		if os.IsNotExist(err) {
			file, err = os.Create(filename)
			if err != nil {
				return err
			}
		} else {
			return err
		}
	}

	// Определение места вывода лога (файл и/или консоль).
	var output io.Writer = file
	var ScreenOut bool
	if val, ok := cfg.Get("Logging", "ScreenOut"); ok && val == "True" {
		output = io.MultiWriter(file, os.Stdout)
		ScreenOut = true
	}

	// Получение уровня логирования из конфигурации.
	logLevel, ok := cfg.Get("Logging", "Log_level")
	if !ok {
		log.Fatalf("Failed to read log level configuration")
	}

	// Определение флагов для форматирования лога в зависимости от уровня логирования.
	var flag int
	switch logLevel {
	case "dev":
		flag = log.Ldate | log.Ltime | log.Lshortfile
		level = 0
	case "debug":
		flag = log.Ldate | log.Ltime | log.Lshortfile
		level = 1
	case "info":
		flag = log.Ldate | log.Ltime
		level = 2
	case "warning":
		flag = log.Ldate | log.Ltime
		level = 3
	case "error":
		flag = log.Ldate | log.Ltime | log.Lshortfile
		level = 4
	default:
		level = 2
		flag = log.Ldate | log.Ltime
		log.Printf("Unknown log level: '%s'. Using 'info'!", logLevel)
	}

	// Создание нового логгера с указанным местом вывода и флагами форматирования.
	Logger = log.New(output, "", flag)
	Logger.Printf("[INIT]  [LOGGER][init]> Logger initialized successfully with setting:log_level[%s], ScreenOut[%t]", logLevel, ScreenOut)
	return nil
}

// Dev записывает логи уровня DEV.
func Dev(format string, args ...interface{}) {
	if level == 0 {
		Logger.Printf("[DEV]  "+format, args...)
	}
}

// Debug записывает логи уровня DEBUG.
func Debug(format string, args ...interface{}) {
	if level <= 1 {
		Logger.Printf("[DEBUG]  "+format, args...)
	}
}

// Info записывает логи уровня INFO.
func Info(format string, args ...interface{}) {
	if level <= 2 {
		Logger.Printf("[INFO]  "+format, args...)
	}
}

// Warning записывает логи уровня WARNING.
func Warning(format string, args ...interface{}) {
	if level <= 3 {
		Logger.Printf("[WARNING]  "+format, args...)
	}
}

// Error записывает логи уровня ERROR.
func Error(format string, args ...interface{}) {
	if level <= 4 {
		Logger.Printf("[ERROR]  "+format, args...)
	}
}
