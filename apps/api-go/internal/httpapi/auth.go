package httpapi

import (
	"crypto/subtle"
	"net/http"
	"strings"
)

type accessRole int

const (
	roleViewer accessRole = iota + 1
	roleOperator
	roleAdmin
)

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

		next(response, request)
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
