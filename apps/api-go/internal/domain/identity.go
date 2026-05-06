package domain

import (
	"fmt"
	"strings"
	"time"
)

type AuthIdentity struct {
	TenantID         string    `json:"tenant_id"`
	UserID           string    `json:"user_id"`
	Subject          string    `json:"subject"`
	DisplayName      string    `json:"display_name,omitempty"`
	Role             string    `json:"role"`
	TokenFingerprint string    `json:"token_fingerprint,omitempty"`
	AuthenticatedAt  time.Time `json:"authenticated_at"`
}

func (identity AuthIdentity) Validate() error {
	if strings.TrimSpace(identity.TenantID) == "" {
		return fmt.Errorf("tenant_id is required")
	}
	if len(identity.TenantID) > 64 {
		return fmt.Errorf("tenant_id must be at most 64 characters")
	}
	if strings.TrimSpace(identity.UserID) == "" {
		return fmt.Errorf("user_id is required")
	}
	if len(identity.UserID) > 64 {
		return fmt.Errorf("user_id must be at most 64 characters")
	}
	if strings.TrimSpace(identity.Subject) == "" {
		return fmt.Errorf("subject is required")
	}
	if len(identity.Subject) > 256 {
		return fmt.Errorf("subject must be at most 256 characters")
	}
	if strings.TrimSpace(identity.Role) == "" {
		return fmt.Errorf("role is required")
	}
	switch identity.Role {
	case "viewer", "operator", "admin":
	default:
		return fmt.Errorf("role is not supported")
	}
	return nil
}

func LocalAuthIdentity(tenantID string) AuthIdentity {
	now := time.Now().UTC()
	if strings.TrimSpace(tenantID) == "" {
		tenantID = "tenant_default"
	}
	return AuthIdentity{
		TenantID:        strings.TrimSpace(tenantID),
		UserID:          "user_local",
		Subject:         "local-development",
		DisplayName:     "Local Development",
		Role:            "admin",
		AuthenticatedAt: now,
	}
}

func (snapshot *RunStateSnapshot) ApplyOwnership(identity AuthIdentity) {
	snapshot.TenantID = identity.TenantID
	snapshot.OwnerUserID = identity.UserID
	snapshot.CreatedByUserID = identity.UserID
}
