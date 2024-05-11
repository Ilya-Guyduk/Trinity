package main

import (
	"log"
	"os"
)

const (
	LogLevelDev     = iota // Режим разработки
	LogLevelDebug          // Отладочная информация
	LogLevelInfo           // Информационные сообщения
	LogLevelWarning        // Предупреждения
	LogLevelError          // Ошибки
)

func LogDev(format string, args ...interface{}) {
	log.Printf("[DEV]"+format, args...)
}

func LogDebug(format string, args ...interface{}) {
	log.Printf("[DEBUG]"+format, args...)
}

func LogInfo(format string, args ...interface{}) {
	log.Printf("[INFO] "+format, args...)
}

func LogWarning(format string, args ...interface{}) {
	log.Printf("[WARNING]"+format, args...)
}

func LogError(format string, args ...interface{}) {
	log.Printf("[ERROR]"+format, args...)
}

func InitLogger(logFile string) {
	f, err := os.OpenFile(logFile, os.O_RDWR|os.O_CREATE|os.O_APPEND, 0666)
	if err != nil {
		log.Fatalf("Failed to open log file: %v", err)
	}
	log.SetOutput(f)
}
