package config

import (
	"os"
	"strconv"
)

type Settings struct {
	Host               string
	Port               string
	DatabaseURL        string
	AgentWorkerURL     string
	AgentWorkerToken   string
	ExecutionBackend   string
	LLMProviderName    string
	LLMModelName       string
	LLMTemperature     *float64
	LLMMaxOutputTokens *int
	LLMTimeoutSeconds  *float64
	LLMMaxRetries      int
}

func Load() Settings {
	return Settings{
		Host:               readEnv("HOST", "0.0.0.0"),
		Port:               readEnv("PORT", "8080"),
		DatabaseURL:        os.Getenv("DATABASE_URL"),
		AgentWorkerURL:     readEnv("AGENT_WORKER_URL", "http://127.0.0.1:8090"),
		AgentWorkerToken:   os.Getenv("AGENT_WORKER_TOKEN"),
		ExecutionBackend:   readEnv("EXECUTION_BACKEND", "deterministic"),
		LLMProviderName:    readEnv("LLM_PROVIDER_NAME", "fake"),
		LLMModelName:       readEnv("LLM_MODEL_NAME", "fake-model"),
		LLMTemperature:     readOptionalFloat("LLM_TEMPERATURE"),
		LLMMaxOutputTokens: readOptionalInt("LLM_MAX_OUTPUT_TOKENS"),
		LLMTimeoutSeconds:  readOptionalFloat("LLM_TIMEOUT_SECONDS"),
		LLMMaxRetries:      readInt("LLM_MAX_RETRIES", 0),
	}
}

func (settings Settings) HTTPAddress() string {
	return settings.Host + ":" + settings.Port
}

func readEnv(name string, fallback string) string {
	value := os.Getenv(name)
	if value == "" {
		return fallback
	}
	return value
}

func readInt(name string, fallback int) int {
	value := os.Getenv(name)
	if value == "" {
		return fallback
	}
	parsed, err := strconv.Atoi(value)
	if err != nil {
		return fallback
	}
	return parsed
}

func readOptionalInt(name string) *int {
	value := os.Getenv(name)
	if value == "" {
		return nil
	}
	parsed, err := strconv.Atoi(value)
	if err != nil {
		return nil
	}
	return &parsed
}

func readOptionalFloat(name string) *float64 {
	value := os.Getenv(name)
	if value == "" {
		return nil
	}
	parsed, err := strconv.ParseFloat(value, 64)
	if err != nil {
		return nil
	}
	return &parsed
}
