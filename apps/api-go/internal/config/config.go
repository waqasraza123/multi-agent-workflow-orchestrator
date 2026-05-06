package config

import (
	"os"
	"strconv"
	"strings"
)

type Settings struct {
	Host                     string
	Port                     string
	DatabaseURL              string
	AgentWorkerURL           string
	AgentWorkerToken         string
	ExecutionBackend         string
	LLMProviderName          string
	LLMModelName             string
	LLMTemperature           *float64
	LLMMaxOutputTokens       *int
	LLMTimeoutSeconds        *float64
	LLMMaxRetries            int
	ExecutionFallbackEnabled bool
	PlanningBackend          string
	PlanningProviderName     string
	PlanningModelName        string
	PlanningTemperature      *float64
	PlanningMaxOutputTokens  *int
	PlanningTimeoutSeconds   *float64
	PlanningMaxRetries       int
	PlanningFallbackEnabled  bool
	AuthMode                 string
	AuthViewerTokens         []string
	AuthOperatorTokens       []string
	AuthAdminTokens          []string
}

func Load() Settings {
	return Settings{
		Host:                     readEnv("HOST", "0.0.0.0"),
		Port:                     readEnv("PORT", "8080"),
		DatabaseURL:              os.Getenv("DATABASE_URL"),
		AgentWorkerURL:           readEnv("AGENT_WORKER_URL", "http://127.0.0.1:8090"),
		AgentWorkerToken:         os.Getenv("AGENT_WORKER_TOKEN"),
		ExecutionBackend:         strings.ToLower(readEnv("EXECUTION_BACKEND", "deterministic")),
		LLMProviderName:          readEnv("LLM_PROVIDER_NAME", "fake"),
		LLMModelName:             readEnv("LLM_MODEL_NAME", "fake-model"),
		LLMTemperature:           readOptionalFloat("LLM_TEMPERATURE"),
		LLMMaxOutputTokens:       readOptionalInt("LLM_MAX_OUTPUT_TOKENS"),
		LLMTimeoutSeconds:        readOptionalFloat("LLM_TIMEOUT_SECONDS"),
		LLMMaxRetries:            readInt("LLM_MAX_RETRIES", 0),
		ExecutionFallbackEnabled: readBool("EXECUTION_FALLBACK_ENABLED", true),
		PlanningBackend:          strings.ToLower(readEnv("PLANNING_BACKEND", "deterministic")),
		PlanningProviderName:     readEnv("PLANNING_PROVIDER_NAME", readEnv("LLM_PROVIDER_NAME", "fake")),
		PlanningModelName:        readEnv("PLANNING_MODEL_NAME", readEnv("LLM_MODEL_NAME", "fake-model")),
		PlanningTemperature:      readOptionalFloat("PLANNING_TEMPERATURE"),
		PlanningMaxOutputTokens:  readOptionalInt("PLANNING_MAX_OUTPUT_TOKENS"),
		PlanningTimeoutSeconds:   readOptionalFloat("PLANNING_TIMEOUT_SECONDS"),
		PlanningMaxRetries:       readInt("PLANNING_MAX_RETRIES", readInt("LLM_MAX_RETRIES", 0)),
		PlanningFallbackEnabled:  readBool("PLANNING_FALLBACK_ENABLED", true),
		AuthMode:                 strings.ToLower(readEnv("AUTH_MODE", "disabled")),
		AuthViewerTokens:         readCSV("AUTH_VIEWER_TOKENS"),
		AuthOperatorTokens:       readCSV("AUTH_OPERATOR_TOKENS"),
		AuthAdminTokens:          readCSV("AUTH_ADMIN_TOKENS"),
	}
}

func (settings Settings) HTTPAddress() string {
	return settings.Host + ":" + settings.Port
}

func (settings Settings) AuthEnabled() bool {
	return settings.AuthMode != "" && settings.AuthMode != "disabled"
}

func (settings Settings) HasAuthTokens() bool {
	return len(settings.AuthViewerTokens) > 0 ||
		len(settings.AuthOperatorTokens) > 0 ||
		len(settings.AuthAdminTokens) > 0
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

func readBool(name string, fallback bool) bool {
	value := strings.ToLower(strings.TrimSpace(os.Getenv(name)))
	if value == "" {
		return fallback
	}
	switch value {
	case "1", "true", "yes", "on":
		return true
	case "0", "false", "no", "off":
		return false
	default:
		return fallback
	}
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

func readCSV(name string) []string {
	value := os.Getenv(name)
	if value == "" {
		return []string{}
	}
	parts := strings.Split(value, ",")
	items := make([]string, 0, len(parts))
	for _, part := range parts {
		item := strings.TrimSpace(part)
		if item != "" {
			items = append(items, item)
		}
	}
	return items
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
