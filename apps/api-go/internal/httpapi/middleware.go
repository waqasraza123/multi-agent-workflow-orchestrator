package httpapi

import (
	"crypto/rand"
	"encoding/hex"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/waqasraza123/agent-runway/apps/api-go/internal/requestmeta"
)

const (
	requestIDHeader   = "X-Request-ID"
	traceparentHeader = "traceparent"
)

type statusCapturingResponseWriter struct {
	http.ResponseWriter
	statusCode int
	bytes      int
}

func (writer *statusCapturingResponseWriter) WriteHeader(statusCode int) {
	if writer.statusCode != 0 {
		return
	}
	writer.statusCode = statusCode
	writer.ResponseWriter.WriteHeader(statusCode)
}

func (writer *statusCapturingResponseWriter) Write(body []byte) (int, error) {
	if writer.statusCode == 0 {
		writer.statusCode = http.StatusOK
	}
	written, err := writer.ResponseWriter.Write(body)
	writer.bytes += written
	return written, err
}

func (handler Handler) requestMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(response http.ResponseWriter, request *http.Request) {
		startedAt := time.Now()
		requestID := normalizeHeaderValue(request.Header.Get(requestIDHeader))
		if requestID == "" {
			requestID = newRequestID()
		}
		traceparent := normalizeHeaderValue(request.Header.Get(traceparentHeader))
		if traceparent == "" {
			traceparent = newTraceparent()
		}

		response.Header().Set(requestIDHeader, requestID)
		response.Header().Set(traceparentHeader, traceparent)

		metadata := requestmeta.Metadata{
			RequestID:   requestID,
			Traceparent: traceparent,
		}
		requestWithMetadata := request.WithContext(
			requestmeta.WithMetadata(request.Context(), metadata),
		)
		capturingWriter := &statusCapturingResponseWriter{ResponseWriter: response}

		next.ServeHTTP(capturingWriter, requestWithMetadata)

		statusCode := capturingWriter.statusCode
		if statusCode == 0 {
			statusCode = http.StatusOK
		}
		if handler.dependencies.Logger != nil {
			handler.dependencies.Logger.Info(
				"http_request",
				"request_id", requestID,
				"traceparent", traceparent,
				"method", request.Method,
				"path", request.URL.Path,
				"status", statusCode,
				"bytes", capturingWriter.bytes,
				"duration_ms", time.Since(startedAt).Milliseconds(),
				"remote_addr", request.RemoteAddr,
				"user_agent", request.UserAgent(),
			)
		}
	})
}

func normalizeHeaderValue(value string) string {
	return strings.TrimSpace(value)
}

func newRequestID() string {
	return "req_" + randomHex(16)
}

func newTraceparent() string {
	return "00-" + randomHex(16) + "-" + randomHex(8) + "-01"
}

func randomHex(byteCount int) string {
	buffer := make([]byte, byteCount)
	if _, err := rand.Read(buffer); err != nil {
		return strconv.FormatInt(time.Now().UnixNano(), 16)
	}
	return hex.EncodeToString(buffer)
}
