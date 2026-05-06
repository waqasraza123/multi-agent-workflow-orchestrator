package httpapi

import (
	"log/slog"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/pythonworker"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/storage"
)

type Dependencies struct {
	Logger       *slog.Logger
	Store        *storage.Store
	WorkerClient *pythonworker.Client
}

func NewRouter(dependencies Dependencies) http.Handler {
	router := chi.NewRouter()
	handler := Handler{dependencies: dependencies}

	router.Get("/health", handler.Health)
	router.Get("/ready", handler.Ready)
	router.Post("/runs", handler.CreateRun)
	router.Get("/runs", handler.ListRuns)
	router.Get("/runs/{run_id}", handler.GetRun)
	router.Get("/runs/{run_id}/state", handler.GetRunState)
	router.Post("/runs/{run_id}/plan", handler.GeneratePlan)
	router.Get("/runs/{run_id}/plans/latest", handler.GetLatestPlan)
	router.Post("/runs/{run_id}/turns/advance", handler.AdvanceTurn)

	return router
}
