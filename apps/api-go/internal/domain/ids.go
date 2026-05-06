package domain

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"strings"
)

func NewID(prefix string) (string, error) {
	cleanedPrefix := strings.TrimSpace(prefix)
	if cleanedPrefix == "" {
		return "", fmt.Errorf("id prefix must not be blank")
	}

	bytes := make([]byte, 16)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return cleanedPrefix + "_" + hex.EncodeToString(bytes), nil
}
