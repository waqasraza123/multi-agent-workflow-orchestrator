package httpapi

import (
	"log/slog"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/config"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/pythonworker"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/storage"
)

type Dependencies struct {
	Logger       *slog.Logger
	Store        *storage.Store
	WorkerClient *pythonworker.Client
	Settings     config.Settings
}

func NewRouter(dependencies Dependencies) http.Handler {
	router := chi.NewRouter()
	handler := Handler{dependencies: dependencies}

	router.Get("/health", handler.Health)
	router.Get("/ready", handler.Ready)
	router.Post("/runs", handler.requireRole(roleOperator, handler.CreateRun))
	router.Get("/runs", handler.requireRole(roleViewer, handler.ListRuns))
	router.Get("/runs/{run_id}", handler.requireRole(roleViewer, handler.GetRun))
	router.Get("/runs/{run_id}/state", handler.requireRole(roleViewer, handler.GetRunState))
	router.Post("/runs/{run_id}/plan", handler.requireRole(roleOperator, handler.GeneratePlan))
	router.Get("/runs/{run_id}/plans/latest", handler.requireRole(roleViewer, handler.GetLatestPlan))
	router.Post("/runs/{run_id}/turns/advance", handler.requireRole(roleOperator, handler.AdvanceTurn))
	router.Post("/runs/{run_id}/verify", handler.requireRole(roleOperator, handler.VerifyRun))
	router.Get("/runs/{run_id}/verifications/latest", handler.requireRole(roleViewer, handler.GetLatestVerification))
	router.Post("/runs/{run_id}/finalize", handler.requireRole(roleOperator, handler.FinalizeRun))
	router.Get("/runs/{run_id}/outputs/latest", handler.requireRole(roleViewer, handler.GetLatestOutput))
	router.Get("/runs/{run_id}/approvals", handler.requireRole(roleViewer, handler.ListRunApprovals))
	router.Post("/runs/{run_id}/approvals", handler.requireRole(roleOperator, handler.CreateRunApproval))
	router.Post("/runs/{run_id}/approvals/{approval_id}/decide", handler.requireRole(roleOperator, handler.DecideRunApproval))
	router.Get("/runs/{run_id}/events", handler.requireRole(roleViewer, handler.ListRunEvents))
	router.Get("/runs/{run_id}/turns", handler.requireRole(roleViewer, handler.ListRunTurns))
	router.Get("/runs/{run_id}/tool-calls", handler.requireRole(roleViewer, handler.ListRunToolCalls))
	router.Get("/runs/{run_id}/llm-calls", handler.requireRole(roleViewer, handler.ListRunLLMCalls))

	return router
}
