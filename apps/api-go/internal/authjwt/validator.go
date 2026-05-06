package authjwt

import (
	"context"
	"crypto"
	"crypto/hmac"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"math/big"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/waqasraza123/agent-runway/apps/api-go/internal/config"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/domain"
)

type Validator struct {
	settings     config.Settings
	httpClient   *http.Client
	cachedKeys   map[string]*rsa.PublicKey
	cacheExpires time.Time
	mu           sync.Mutex
}

type jwtHeader struct {
	Algorithm string `json:"alg"`
	KeyID     string `json:"kid"`
	Type      string `json:"typ"`
}

type jwksResponse struct {
	Keys []jwkKey `json:"keys"`
}

type jwkKey struct {
	KeyType   string `json:"kty"`
	KeyID     string `json:"kid"`
	Algorithm string `json:"alg"`
	Use       string `json:"use"`
	Modulus   string `json:"n"`
	Exponent  string `json:"e"`
}

func NewValidator(settings config.Settings) *Validator {
	return &Validator{
		settings:   settings,
		httpClient: &http.Client{Timeout: 5 * time.Second},
		cachedKeys: map[string]*rsa.PublicKey{},
	}
}

func (validator *Validator) Validate(ctx context.Context, token string) (domain.AuthIdentity, error) {
	header, claims, signingInput, signature, err := parseJWT(token)
	if err != nil {
		return domain.AuthIdentity{}, err
	}
	if !validator.algorithmAllowed(header.Algorithm) {
		return domain.AuthIdentity{}, fmt.Errorf("jwt algorithm is not allowed")
	}
	if err := validator.verifySignature(ctx, header, signingInput, signature); err != nil {
		return domain.AuthIdentity{}, err
	}
	if err := validator.validateRegisteredClaims(claims); err != nil {
		return domain.AuthIdentity{}, err
	}
	identity, err := validator.identityFromClaims(claims, token)
	if err != nil {
		return domain.AuthIdentity{}, err
	}
	if err := identity.Validate(); err != nil {
		return domain.AuthIdentity{}, err
	}
	return identity, nil
}

func parseJWT(token string) (jwtHeader, map[string]any, string, []byte, error) {
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return jwtHeader{}, nil, "", nil, fmt.Errorf("jwt must contain three segments")
	}
	headerBytes, err := base64.RawURLEncoding.DecodeString(parts[0])
	if err != nil {
		return jwtHeader{}, nil, "", nil, fmt.Errorf("decode jwt header: %w", err)
	}
	claimsBytes, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return jwtHeader{}, nil, "", nil, fmt.Errorf("decode jwt claims: %w", err)
	}
	signature, err := base64.RawURLEncoding.DecodeString(parts[2])
	if err != nil {
		return jwtHeader{}, nil, "", nil, fmt.Errorf("decode jwt signature: %w", err)
	}

	var header jwtHeader
	if err := json.Unmarshal(headerBytes, &header); err != nil {
		return jwtHeader{}, nil, "", nil, fmt.Errorf("parse jwt header: %w", err)
	}
	var claims map[string]any
	if err := json.Unmarshal(claimsBytes, &claims); err != nil {
		return jwtHeader{}, nil, "", nil, fmt.Errorf("parse jwt claims: %w", err)
	}
	if header.Algorithm == "" || strings.EqualFold(header.Algorithm, "none") {
		return jwtHeader{}, nil, "", nil, fmt.Errorf("jwt algorithm is required")
	}
	return header, claims, parts[0] + "." + parts[1], signature, nil
}

func (validator *Validator) algorithmAllowed(algorithm string) bool {
	for _, allowed := range validator.settings.AuthJWTAlgorithms {
		if strings.EqualFold(strings.TrimSpace(allowed), algorithm) {
			return true
		}
	}
	return false
}

func (validator *Validator) verifySignature(
	ctx context.Context,
	header jwtHeader,
	signingInput string,
	signature []byte,
) error {
	switch header.Algorithm {
	case "HS256":
		if validator.settings.AuthJWTSigningSecret == "" {
			return fmt.Errorf("jwt signing secret is not configured")
		}
		mac := hmac.New(sha256.New, []byte(validator.settings.AuthJWTSigningSecret))
		_, _ = mac.Write([]byte(signingInput))
		if !hmac.Equal(signature, mac.Sum(nil)) {
			return fmt.Errorf("jwt signature is invalid")
		}
		return nil
	case "RS256":
		publicKey, err := validator.rsaPublicKey(ctx, header.KeyID)
		if err != nil {
			return err
		}
		digest := sha256.Sum256([]byte(signingInput))
		if err := rsa.VerifyPKCS1v15(publicKey, crypto.SHA256, digest[:], signature); err != nil {
			return fmt.Errorf("jwt signature is invalid")
		}
		return nil
	default:
		return fmt.Errorf("jwt algorithm is not supported")
	}
}

func (validator *Validator) rsaPublicKey(ctx context.Context, keyID string) (*rsa.PublicKey, error) {
	if validator.settings.AuthJWTPublicKeyPEM != "" {
		return parseRSAPublicKeyPEM(validator.settings.AuthJWTPublicKeyPEM)
	}
	if validator.settings.AuthJWKSURL == "" {
		return nil, fmt.Errorf("jwt public key or jwks url is not configured")
	}
	keys, err := validator.jwksKeys(ctx)
	if err != nil {
		return nil, err
	}
	if keyID != "" {
		key, ok := keys[keyID]
		if !ok {
			return nil, fmt.Errorf("jwt key id is not trusted")
		}
		return key, nil
	}
	if len(keys) == 1 {
		for _, key := range keys {
			return key, nil
		}
	}
	return nil, fmt.Errorf("jwt key id is required")
}

func parseRSAPublicKeyPEM(value string) (*rsa.PublicKey, error) {
	block, _ := pem.Decode([]byte(value))
	if block == nil {
		return nil, fmt.Errorf("parse jwt public key pem: no pem block found")
	}
	parsed, err := x509.ParsePKIXPublicKey(block.Bytes)
	if err == nil {
		if key, ok := parsed.(*rsa.PublicKey); ok {
			return key, nil
		}
		return nil, fmt.Errorf("jwt public key is not rsa")
	}
	key, err := x509.ParsePKCS1PublicKey(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("parse jwt rsa public key: %w", err)
	}
	return key, nil
}

func (validator *Validator) jwksKeys(ctx context.Context) (map[string]*rsa.PublicKey, error) {
	validator.mu.Lock()
	if time.Now().Before(validator.cacheExpires) && len(validator.cachedKeys) > 0 {
		keys := cloneKeyMap(validator.cachedKeys)
		validator.mu.Unlock()
		return keys, nil
	}
	validator.mu.Unlock()

	request, err := http.NewRequestWithContext(ctx, http.MethodGet, validator.settings.AuthJWKSURL, nil)
	if err != nil {
		return nil, fmt.Errorf("build jwks request: %w", err)
	}
	response, err := validator.httpClient.Do(request)
	if err != nil {
		return nil, fmt.Errorf("fetch jwks: %w", err)
	}
	defer response.Body.Close()
	if response.StatusCode < 200 || response.StatusCode >= 300 {
		return nil, fmt.Errorf("fetch jwks returned status %d", response.StatusCode)
	}
	var jwks jwksResponse
	if err := json.NewDecoder(response.Body).Decode(&jwks); err != nil {
		return nil, fmt.Errorf("decode jwks: %w", err)
	}
	keys := map[string]*rsa.PublicKey{}
	for _, item := range jwks.Keys {
		key, err := item.rsaPublicKey()
		if err != nil {
			continue
		}
		if item.KeyID != "" {
			keys[item.KeyID] = key
		}
	}
	if len(keys) == 0 {
		return nil, fmt.Errorf("jwks did not contain usable rsa keys")
	}

	validator.mu.Lock()
	validator.cachedKeys = cloneKeyMap(keys)
	validator.cacheExpires = time.Now().Add(time.Duration(validator.settings.AuthJWKSCacheSeconds) * time.Second)
	validator.mu.Unlock()
	return keys, nil
}

func (key jwkKey) rsaPublicKey() (*rsa.PublicKey, error) {
	if key.KeyType != "RSA" || key.Modulus == "" || key.Exponent == "" {
		return nil, errors.New("jwk is not rsa")
	}
	modulusBytes, err := base64.RawURLEncoding.DecodeString(key.Modulus)
	if err != nil {
		return nil, err
	}
	exponentBytes, err := base64.RawURLEncoding.DecodeString(key.Exponent)
	if err != nil {
		return nil, err
	}
	exponent := 0
	for _, item := range exponentBytes {
		exponent = exponent<<8 + int(item)
	}
	if exponent == 0 {
		return nil, errors.New("jwk exponent is invalid")
	}
	return &rsa.PublicKey{
		N: new(big.Int).SetBytes(modulusBytes),
		E: exponent,
	}, nil
}

func cloneKeyMap(source map[string]*rsa.PublicKey) map[string]*rsa.PublicKey {
	cloned := make(map[string]*rsa.PublicKey, len(source))
	for key, value := range source {
		cloned[key] = value
	}
	return cloned
}

func (validator *Validator) validateRegisteredClaims(claims map[string]any) error {
	now := time.Now().UTC()
	if issuer := validator.settings.AuthJWTIssuer; issuer != "" {
		if claimString(claims, "iss") != issuer {
			return fmt.Errorf("jwt issuer is invalid")
		}
	}
	if audience := validator.settings.AuthJWTAudience; audience != "" {
		if !claimAudienceContains(claims["aud"], audience) {
			return fmt.Errorf("jwt audience is invalid")
		}
	}
	if expiresAt, ok := claimUnixTime(claims, "exp"); ok && !now.Before(expiresAt) {
		return fmt.Errorf("jwt is expired")
	}
	if notBefore, ok := claimUnixTime(claims, "nbf"); ok && now.Before(notBefore) {
		return fmt.Errorf("jwt is not active yet")
	}
	if issuedAt, ok := claimUnixTime(claims, "iat"); ok && now.Add(2*time.Minute).Before(issuedAt) {
		return fmt.Errorf("jwt issued-at is in the future")
	}
	return nil
}

func (validator *Validator) identityFromClaims(
	claims map[string]any,
	token string,
) (domain.AuthIdentity, error) {
	subject := claimString(claims, validator.settings.AuthJWTSubjectClaim)
	if subject == "" {
		return domain.AuthIdentity{}, fmt.Errorf("jwt subject claim is required")
	}
	tenantID := claimString(claims, validator.settings.AuthJWTTenantClaim)
	if tenantID == "" {
		tenantID = validator.settings.AuthDefaultTenantID
	}
	role := normalizeRole(claimRole(claims, validator.settings.AuthJWTRoleClaim))
	if role == "" {
		return domain.AuthIdentity{}, fmt.Errorf("jwt role claim is required")
	}
	displayName := claimString(claims, validator.settings.AuthJWTDisplayNameClaim)
	if displayName == "" {
		displayName = claimString(claims, validator.settings.AuthJWTEmailClaim)
	}
	if displayName == "" {
		displayName = subject
	}
	return domain.AuthIdentity{
		TenantID:         tenantID,
		UserID:           stableUserID(subject),
		Subject:          subject,
		DisplayName:      displayName,
		Role:             role,
		TokenFingerprint: tokenFingerprint(token),
		AuthenticatedAt:  time.Now().UTC(),
	}, nil
}

func stableUserID(subject string) string {
	sum := sha256.Sum256([]byte(subject))
	return "user_" + fmt.Sprintf("%x", sum[:])[:32]
}

func tokenFingerprint(token string) string {
	sum := sha256.Sum256([]byte(token))
	return fmt.Sprintf("%x", sum[:])
}

func normalizeRole(role string) string {
	switch strings.ToLower(strings.TrimSpace(role)) {
	case "admin", "administrator":
		return "admin"
	case "operator", "editor", "writer":
		return "operator"
	case "viewer", "reader", "read":
		return "viewer"
	default:
		return ""
	}
}

func claimString(claims map[string]any, name string) string {
	if name == "" {
		return ""
	}
	value, ok := claims[name]
	if !ok {
		return ""
	}
	switch typedValue := value.(type) {
	case string:
		return strings.TrimSpace(typedValue)
	default:
		return ""
	}
}

func claimRole(claims map[string]any, name string) string {
	value, ok := claims[name]
	if !ok {
		return ""
	}
	switch typedValue := value.(type) {
	case string:
		return typedValue
	case []any:
		best := ""
		for _, item := range typedValue {
			role, ok := item.(string)
			if !ok {
				continue
			}
			normalized := normalizeRole(role)
			if normalized == "admin" {
				return normalized
			}
			if normalized == "operator" {
				best = normalized
			}
			if normalized == "viewer" && best == "" {
				best = normalized
			}
		}
		return best
	default:
		return ""
	}
}

func claimAudienceContains(value any, audience string) bool {
	switch typedValue := value.(type) {
	case string:
		return typedValue == audience
	case []any:
		for _, item := range typedValue {
			if itemValue, ok := item.(string); ok && itemValue == audience {
				return true
			}
		}
	}
	return false
}

func claimUnixTime(claims map[string]any, name string) (time.Time, bool) {
	value, ok := claims[name]
	if !ok {
		return time.Time{}, false
	}
	switch typedValue := value.(type) {
	case float64:
		return time.Unix(int64(typedValue), 0).UTC(), true
	case json.Number:
		parsed, err := typedValue.Int64()
		if err != nil {
			return time.Time{}, false
		}
		return time.Unix(parsed, 0).UTC(), true
	default:
		return time.Time{}, false
	}
}
