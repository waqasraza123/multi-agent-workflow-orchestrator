package requestmeta

import "context"

type contextKey string

const metadataContextKey contextKey = "agent_runway_request_metadata"

type Metadata struct {
	RequestID   string
	Traceparent string
}

func WithMetadata(ctx context.Context, metadata Metadata) context.Context {
	return context.WithValue(ctx, metadataContextKey, metadata)
}

func FromContext(ctx context.Context) (Metadata, bool) {
	metadata, ok := ctx.Value(metadataContextKey).(Metadata)
	return metadata, ok
}
