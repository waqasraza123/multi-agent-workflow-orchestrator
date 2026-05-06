package observability

import (
	"bytes"
	"context"
	"encoding/json"
	"log/slog"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"
)

type SpanExporter struct {
	endpoint           string
	headers            map[string]string
	serviceName        string
	serviceEnvironment string
	client             *http.Client
	logger             *slog.Logger
	queue              chan Span
	done               chan struct{}
	wg                 sync.WaitGroup
}

type SpanExporterOptions struct {
	Endpoint           string
	Headers            map[string]string
	Timeout            time.Duration
	QueueSize          int
	ServiceName        string
	ServiceEnvironment string
	Logger             *slog.Logger
}

type Span struct {
	Name         string
	TraceID      string
	SpanID       string
	ParentSpanID string
	StartTime    time.Time
	EndTime      time.Time
	Attributes   map[string]any
	StatusCode   int
	StatusMessage string
}

func NewSpanExporter(options SpanExporterOptions) *SpanExporter {
	endpoint := strings.TrimSpace(options.Endpoint)
	if endpoint == "" {
		return nil
	}
	timeout := options.Timeout
	if timeout <= 0 {
		timeout = 2 * time.Second
	}
	queueSize := options.QueueSize
	if queueSize <= 0 {
		queueSize = 256
	}
	serviceName := strings.TrimSpace(options.ServiceName)
	if serviceName == "" {
		serviceName = "agent-runway-api-go"
	}
	serviceEnvironment := strings.TrimSpace(options.ServiceEnvironment)
	if serviceEnvironment == "" {
		serviceEnvironment = "local"
	}

	exporter := &SpanExporter{
		endpoint:           endpoint,
		headers:            options.Headers,
		serviceName:        serviceName,
		serviceEnvironment: serviceEnvironment,
		client:             &http.Client{Timeout: timeout},
		logger:             options.Logger,
		queue:              make(chan Span, queueSize),
		done:               make(chan struct{}),
	}
	exporter.wg.Add(1)
	go exporter.run()
	return exporter
}

func (exporter *SpanExporter) Export(span Span) {
	if exporter == nil {
		return
	}
	select {
	case exporter.queue <- span:
	default:
		if exporter.logger != nil {
			exporter.logger.Warn(
				"otel_span_dropped",
				"span_name", span.Name,
				"trace_id", span.TraceID,
				"reason", "queue_full",
			)
		}
	}
}

func (exporter *SpanExporter) Close(ctx context.Context) error {
	if exporter == nil {
		return nil
	}
	close(exporter.done)
	completed := make(chan struct{})
	go func() {
		exporter.wg.Wait()
		close(completed)
	}()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-completed:
		return nil
	}
}

func (exporter *SpanExporter) run() {
	defer exporter.wg.Done()
	for {
		select {
		case span := <-exporter.queue:
			exporter.exportSpan(span)
		case <-exporter.done:
			for {
				select {
				case span := <-exporter.queue:
					exporter.exportSpan(span)
				default:
					return
				}
			}
		}
	}
}

func (exporter *SpanExporter) exportSpan(span Span) {
	payload, err := json.Marshal(exporter.buildPayload(span))
	if err != nil {
		if exporter.logger != nil {
			exporter.logger.Error("otel_span_encode_failed", "error", err)
		}
		return
	}
	request, err := http.NewRequest(http.MethodPost, exporter.endpoint, bytes.NewReader(payload))
	if err != nil {
		if exporter.logger != nil {
			exporter.logger.Error("otel_span_request_failed", "error", err)
		}
		return
	}
	request.Header.Set("Content-Type", "application/json")
	for key, value := range exporter.headers {
		request.Header.Set(key, value)
	}

	response, err := exporter.client.Do(request)
	if err != nil {
		if exporter.logger != nil {
			exporter.logger.Warn("otel_span_export_failed", "error", err, "trace_id", span.TraceID)
		}
		return
	}
	defer response.Body.Close()
	if response.StatusCode < 200 || response.StatusCode >= 300 {
		if exporter.logger != nil {
			exporter.logger.Warn(
				"otel_span_export_rejected",
				"status", response.StatusCode,
				"trace_id", span.TraceID,
			)
		}
	}
}

func (exporter *SpanExporter) buildPayload(span Span) map[string]any {
	return map[string]any{
		"resourceSpans": []any{
			map[string]any{
				"resource": map[string]any{
					"attributes": []any{
						stringAttribute("service.name", exporter.serviceName),
						stringAttribute("deployment.environment", exporter.serviceEnvironment),
					},
				},
				"scopeSpans": []any{
					map[string]any{
						"scope": map[string]any{
							"name":    "agent-runway-go-api",
							"version": "0.1.0",
						},
						"spans": []any{span.toOTLP()},
					},
				},
			},
		},
	}
}

func (span Span) toOTLP() map[string]any {
	statusCode := 1
	if span.StatusCode >= http.StatusInternalServerError {
		statusCode = 2
	}
	attributes := make([]any, 0, len(span.Attributes))
	for key, value := range span.Attributes {
		attributes = append(attributes, attribute(key, value))
	}
	item := map[string]any{
		"traceId":           span.TraceID,
		"spanId":            span.SpanID,
		"name":              span.Name,
		"kind":              2,
		"startTimeUnixNano": strconv.FormatInt(span.StartTime.UnixNano(), 10),
		"endTimeUnixNano":   strconv.FormatInt(span.EndTime.UnixNano(), 10),
		"attributes":        attributes,
		"status": map[string]any{
			"code":    statusCode,
			"message": span.StatusMessage,
		},
	}
	if span.ParentSpanID != "" {
		item["parentSpanId"] = span.ParentSpanID
	}
	return item
}

func attribute(key string, value any) map[string]any {
	switch typedValue := value.(type) {
	case int:
		return intAttribute(key, typedValue)
	case int64:
		return int64Attribute(key, typedValue)
	case bool:
		return boolAttribute(key, typedValue)
	case string:
		return stringAttribute(key, typedValue)
	default:
		return stringAttribute(key, "")
	}
}

func stringAttribute(key string, value string) map[string]any {
	return map[string]any{"key": key, "value": map[string]any{"stringValue": value}}
}

func intAttribute(key string, value int) map[string]any {
	return int64Attribute(key, int64(value))
}

func int64Attribute(key string, value int64) map[string]any {
	return map[string]any{
		"key":   key,
		"value": map[string]any{"intValue": strconv.FormatInt(value, 10)},
	}
}

func boolAttribute(key string, value bool) map[string]any {
	return map[string]any{"key": key, "value": map[string]any{"boolValue": value}}
}

func ParseTraceparent(traceparent string) (string, string, bool) {
	parts := strings.Split(strings.TrimSpace(traceparent), "-")
	if len(parts) != 4 {
		return "", "", false
	}
	traceID := strings.ToLower(parts[1])
	parentSpanID := strings.ToLower(parts[2])
	if len(traceID) != 32 || len(parentSpanID) != 16 {
		return "", "", false
	}
	if !isLowerHex(traceID) || !isLowerHex(parentSpanID) {
		return "", "", false
	}
	if traceID == "00000000000000000000000000000000" ||
		parentSpanID == "0000000000000000" {
		return "", "", false
	}
	return traceID, parentSpanID, true
}

func FormatTraceparent(traceID string, spanID string) string {
	return "00-" + traceID + "-" + spanID + "-01"
}

func isLowerHex(value string) bool {
	for _, char := range value {
		if (char < '0' || char > '9') && (char < 'a' || char > 'f') {
			return false
		}
	}
	return true
}
