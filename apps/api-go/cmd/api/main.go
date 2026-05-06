package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/waqasraza123/agent-runway/apps/api-go/internal/authjwt"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/config"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/httpapi"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/observability"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/pythonworker"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/storage"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	settings := config.Load()

	rootContext, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	var store *storage.Store
	if settings.DatabaseURL != "" {
		openedStore, err := storage.Open(rootContext, settings.DatabaseURL)
		if err != nil {
			logger.Error("failed to connect to database", "error", err)
			os.Exit(1)
		}
		defer openedStore.Close()
		store = openedStore
	}

	traceExporter := observability.NewSpanExporter(observability.SpanExporterOptions{
		Endpoint:           settings.OTLPTracesEndpoint,
		Headers:            settings.OTLPHeaders,
		Timeout:            time.Duration(settings.OTLPTimeoutSeconds * float64(time.Second)),
		QueueSize:          settings.OTLPQueueSize,
		ServiceName:        settings.ServiceName,
		ServiceEnvironment: settings.ServiceEnvironment,
		Logger:             logger,
	})
	if traceExporter != nil {
		defer func() {
			shutdownContext, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			defer cancel()
			if err := traceExporter.Close(shutdownContext); err != nil {
				logger.Warn("trace exporter shutdown failed", "error", err)
			}
		}()
	}

	workerClient := pythonworker.NewClient(settings.AgentWorkerURL, settings.AgentWorkerToken)
	var jwtValidator *authjwt.Validator
	if settings.AuthMode == "jwt" {
		jwtValidator = authjwt.NewValidator(settings)
	}
	router := httpapi.NewRouter(httpapi.Dependencies{
		Logger:        logger,
		Store:         store,
		WorkerClient:  workerClient,
		TraceExporter: traceExporter,
		JWTValidator:  jwtValidator,
		Settings:      settings,
	})

	server := &http.Server{
		Addr:              settings.HTTPAddress(),
		Handler:           router,
		ReadHeaderTimeout: 5 * time.Second,
	}

	go func() {
		logger.Info("starting Go control plane", "address", server.Addr)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error("server failed", "error", err)
			os.Exit(1)
		}
	}()

	<-rootContext.Done()

	shutdownContext, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := server.Shutdown(shutdownContext); err != nil {
		logger.Error("server shutdown failed", "error", err)
		os.Exit(1)
	}
}
