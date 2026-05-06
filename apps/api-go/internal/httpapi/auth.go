package httpapi

import (
	"context"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/hex"
	"net/http"
	"strings"
	"time"

	"github.com/waqasraza123/agent-runway/apps/api-go/internal/domain"
)

type accessRole int

const (
	roleViewer accessRole = iota + 1
	roleOperator
	roleAdmin
)

type authIdentityContextKey struct{}

func (handler Handler) requireRole(
	requiredRole accessRole,
	next http.HandlerFunc,
) http.HandlerFunc {
	return func(response http.ResponseWriter, request *http.Request) {
		if !handler.dependencies.Settings.AuthEnabled() {
			next(response, request)
			return
		}
		if !handler.dependencies.Settings.HasAuthTokens() {
			writeError(response, http.StatusServiceUnavailable, "authentication is enabled but no tokens are configured")
			return
		}

		token, ok := extractAccessToken(request)
		if !ok {
			response.Header().Set("WWW-Authenticate", `Bearer realm="agent-runway"`)
			writeError(response, http.StatusUnauthorized, "authentication token is required")
			return
		}

		role, ok := handler.roleForToken(token)
		if !ok {
			response.Header().Set("WWW-Authenticate", `Bearer realm="agent-runway"`)
			writeError(response, http.StatusUnauthorized, "authentication token is invalid")
			return
		}
		if role < requiredRole {
			writeError(response, http.StatusForbidden, "authentication token does not have access to this endpoint")
			return
		}

		identity := handler.identityForToken(token, role)
		if err := identity.Validate(); err != nil {
			writeError(response, http.StatusServiceUnavailable, "authentication token identity is not configured")
			return
		}
		if handler.dependencies.Store != nil {
			if err := handler.dependencies.Store.EnsureAuthIdentity(request.Context(), identity); err != nil {
				handler.logError("persist auth identity failed", err)
				writeError(response, http.StatusInternalServerError, "Failed to persist authentication identity")
				return
			}
		}

		next(response, request.WithContext(withAuthIdentity(request.Context(), identity)))
	}
}

func extractAccessToken(request *http.Request) (string, bool) {
	authorization := strings.TrimSpace(request.Header.Get("Authorization"))
	if authorization != "" {
		parts := strings.Fields(authorization)
		if len(parts) == 2 && strings.EqualFold(parts[0], "Bearer") {
			token := strings.TrimSpace(parts[1])
			return token, token != ""
		}
	}

	token := strings.TrimSpace(request.Header.Get("X-API-Key"))
	return token, token != ""
}

func (handler Handler) roleForToken(token string) (accessRole, bool) {
	if tokenMatchesAny(token, handler.dependencies.Settings.AuthAdminTokens) {
		return roleAdmin, true
	}
	if tokenMatchesAny(token, handler.dependencies.Settings.AuthOperatorTokens) {
		return roleOperator, true
	}
	if tokenMatchesAny(token, handler.dependencies.Settings.AuthViewerTokens) {
		return roleViewer, true
	}
	return 0, false
}

func (handler Handler) identityForToken(token string, role accessRole) domain.AuthIdentity {
	fingerprint := tokenFingerprint(token)
	for _, principal := range handler.dependencies.Settings.AuthTokenPrincipals {
		if constantTimeStringEqual(token, principal.Token) {
			subject := principal.Subject
			if subject == "" {
				subject = "static-token:" + fingerprint
			}
			return domain.AuthIdentity{
				TenantID:         principal.TenantID,
				UserID:           principal.UserID,
				Subject:          subject,
				DisplayName:      principal.DisplayName,
				Role:             role.String(),
				TokenFingerprint: fingerprint,
				AuthenticatedAt:  time.Now().UTC(),
			}
		}
	}

	tenantID := strings.TrimSpace(handler.dependencies.Settings.AuthDefaultTenantID)
	if tenantID == "" {
		tenantID = "tenant_default"
	}
	return domain.AuthIdentity{
		TenantID:         tenantID,
		UserID:           "user_" + fingerprint[:32],
		Subject:          "static-token:" + fingerprint,
		DisplayName:      role.String() + " token " + fingerprint[:12],
		Role:             role.String(),
		TokenFingerprint: fingerprint,
		AuthenticatedAt:  time.Now().UTC(),
	}
}

func currentAuthIdentity(request *http.Request) (domain.AuthIdentity, bool) {
	identity, ok := request.Context().Value(authIdentityContextKey{}).(domain.AuthIdentity)
	return identity, ok
}

func withAuthIdentity(ctx context.Context, identity domain.AuthIdentity) context.Context {
	return context.WithValue(ctx, authIdentityContextKey{}, identity)
}

func (role accessRole) String() string {
	switch role {
	case roleAdmin:
		return "admin"
	case roleOperator:
		return "operator"
	case roleViewer:
		return "viewer"
	default:
		return "unknown"
	}
}

func tokenFingerprint(token string) string {
	sum := sha256.Sum256([]byte(token))
	return hex.EncodeToString(sum[:])
}

func tokenMatchesAny(token string, candidates []string) bool {
	for _, candidate := range candidates {
		if constantTimeStringEqual(token, candidate) {
			return true
		}
	}
	return false
}

func constantTimeStringEqual(left string, right string) bool {
	if len(left) != len(right) {
		return false
	}
	return subtle.ConstantTimeCompare([]byte(left), []byte(right)) == 1
}
