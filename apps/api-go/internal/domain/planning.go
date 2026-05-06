package domain

import (
	"fmt"
	"time"
)

type PlannedTask struct {
	TaskID             string   `json:"task_id"`
	Title              string   `json:"title"`
	Description        string   `json:"description"`
	AssignedAgent      string   `json:"assigned_agent"`
	DependencyIDs      []string `json:"dependency_ids"`
	AcceptanceCriteria []string `json:"acceptance_criteria"`
}

type RunPlanReport struct {
	PlanID       string        `json:"plan_id"`
	RunID        string        `json:"run_id"`
	WorkflowType WorkflowType  `json:"workflow_type"`
	CreatedAt    time.Time     `json:"created_at"`
	TemplateName string        `json:"template_name"`
	Summary      string        `json:"summary"`
	Tasks        []PlannedTask `json:"tasks"`
}

type RunPlanResponse struct {
	Item RunPlanReport `json:"item"`
}

func BuildRunPlan(runState RunStateSnapshot) (RunPlanReport, error) {
	switch runState.WorkflowType {
	case WorkflowTypeTechnicalPlan:
		return buildTechnicalPlan(runState)
	case WorkflowTypeDocumentAnalysis:
		return buildDocumentAnalysisPlan(runState)
	case WorkflowTypeResearchReport:
		return buildResearchReportPlan(runState)
	default:
		return buildAssistedActionPlan(runState)
	}
}

func NewRunPlanFromPlannedTasks(
	runState RunStateSnapshot,
	templateName string,
	summary string,
	tasks []PlannedTask,
) (RunPlanReport, error) {
	return newRunPlan(runState, templateName, summary, tasks)
}

func RegisterTasks(runState RunStateSnapshot, plannedTasks []PlannedTask) (RunStateSnapshot, error) {
	if len(plannedTasks) == 0 {
		return RunStateSnapshot{}, fmt.Errorf("at least one task is required")
	}

	taskRecords := make([]TaskRecord, 0, len(plannedTasks))
	for _, task := range plannedTasks {
		taskRecords = append(taskRecords, task.ToTaskRecord())
	}

	existingTaskIDs := map[string]struct{}{}
	for _, task := range runState.Tasks {
		existingTaskIDs[task.TaskID] = struct{}{}
	}
	allKnownTaskIDs := map[string]struct{}{}
	for taskID := range existingTaskIDs {
		allKnownTaskIDs[taskID] = struct{}{}
	}
	for _, task := range taskRecords {
		if _, exists := allKnownTaskIDs[task.TaskID]; exists {
			return RunStateSnapshot{}, fmt.Errorf("task %s already exists", task.TaskID)
		}
		allKnownTaskIDs[task.TaskID] = struct{}{}
	}
	for _, task := range taskRecords {
		for _, dependencyID := range task.DependencyIDs {
			if _, exists := allKnownTaskIDs[dependencyID]; !exists {
				return RunStateSnapshot{}, fmt.Errorf(
					"task %s has unknown dependency %s",
					task.TaskID,
					dependencyID,
				)
			}
		}
	}

	completedTaskIDs := completedTaskIDs(runState.Tasks)
	normalizedTasks := make([]TaskRecord, 0, len(taskRecords))
	for _, task := range taskRecords {
		if dependenciesCompleted(task, completedTaskIDs) {
			task.Status = "ready"
		} else {
			task.Status = "pending"
		}
		normalizedTasks = append(normalizedTasks, task)
	}

	runState.Tasks = append(runState.Tasks, normalizedTasks...)
	runState.Status = RunStatusPlanning
	runState.UpdatedAt = time.Now().UTC()
	return runState, nil
}

func (task PlannedTask) ToTaskRecord() TaskRecord {
	return TaskRecord{
		TaskID:             task.TaskID,
		Title:              task.Title,
		Description:        task.Description,
		AssignedAgent:      task.AssignedAgent,
		Status:             "pending",
		DependencyIDs:      task.DependencyIDs,
		AcceptanceCriteria: task.AcceptanceCriteria,
		RiskLevel:          "medium",
		AttemptCount:       0,
	}
}

func buildTechnicalPlan(runState RunStateSnapshot) (RunPlanReport, error) {
	return newRunPlan(
		runState,
		"technical_plan_default",
		"Default technical planning workflow with scope analysis, dependency review, and delivery planning.",
		[]PlannedTask{
			{
				TaskID:             "plan_scope_review",
				Title:              "Review request scope",
				Description:        "Review the user goal and identify the technical planning scope",
				AssignedAgent:      "planner",
				AcceptanceCriteria: []string{"Scope and assumptions identified"},
			},
			{
				TaskID:             "plan_dependency_analysis",
				Title:              "Analyze dependencies",
				Description:        "Identify dependencies, risks, and technical constraints",
				AssignedAgent:      "researcher",
				DependencyIDs:      []string{"plan_scope_review"},
				AcceptanceCriteria: []string{"Dependencies and risks documented"},
			},
			{
				TaskID:             "plan_delivery_outline",
				Title:              "Draft delivery plan",
				Description:        "Create the execution plan with milestones and validation steps",
				AssignedAgent:      "writer",
				DependencyIDs:      []string{"plan_dependency_analysis"},
				AcceptanceCriteria: []string{"Execution plan drafted"},
			},
		},
	)
}

func buildDocumentAnalysisPlan(runState RunStateSnapshot) (RunPlanReport, error) {
	return newRunPlan(
		runState,
		"document_analysis_default",
		"Default document analysis workflow with intake, findings extraction, and summary preparation.",
		[]PlannedTask{
			{
				TaskID:             "document_intake",
				Title:              "Review documents",
				Description:        "Review the provided documents and identify the analysis targets",
				AssignedAgent:      "researcher",
				AcceptanceCriteria: []string{"Document scope identified"},
			},
			{
				TaskID:             "document_findings",
				Title:              "Extract findings",
				Description:        "Extract key findings, contradictions, and risks from the documents",
				AssignedAgent:      "researcher",
				DependencyIDs:      []string{"document_intake"},
				AcceptanceCriteria: []string{"Findings extracted"},
			},
			{
				TaskID:             "document_summary",
				Title:              "Prepare analysis summary",
				Description:        "Prepare the final summary of the document analysis",
				AssignedAgent:      "writer",
				DependencyIDs:      []string{"document_findings"},
				AcceptanceCriteria: []string{"Summary prepared"},
			},
		},
	)
}

func buildResearchReportPlan(runState RunStateSnapshot) (RunPlanReport, error) {
	return newRunPlan(
		runState,
		"research_report_default",
		"Default research report workflow with scoping, evidence collection, and report drafting.",
		[]PlannedTask{
			{
				TaskID:             "research_scope",
				Title:              "Define research scope",
				Description:        "Define the topic, constraints, and success criteria for the report",
				AssignedAgent:      "planner",
				AcceptanceCriteria: []string{"Research scope defined"},
			},
			{
				TaskID:             "research_collection",
				Title:              "Collect research evidence",
				Description:        "Collect evidence and source material relevant to the report",
				AssignedAgent:      "researcher",
				DependencyIDs:      []string{"research_scope"},
				AcceptanceCriteria: []string{"Evidence collected"},
			},
			{
				TaskID:             "research_report",
				Title:              "Draft research report",
				Description:        "Prepare the final research report with findings and conclusions",
				AssignedAgent:      "writer",
				DependencyIDs:      []string{"research_collection"},
				AcceptanceCriteria: []string{"Report drafted"},
			},
		},
	)
}

func buildAssistedActionPlan(runState RunStateSnapshot) (RunPlanReport, error) {
	return newRunPlan(
		runState,
		"assisted_action_default",
		"Default assisted action workflow with scoping, execution preparation, and outcome review.",
		[]PlannedTask{
			{
				TaskID:             "action_scope",
				Title:              "Define action scope",
				Description:        "Define the requested action and constraints before execution",
				AssignedAgent:      "planner",
				AcceptanceCriteria: []string{"Action scope defined"},
			},
			{
				TaskID:             "action_execution",
				Title:              "Prepare execution",
				Description:        "Prepare the execution path and confirm prerequisites",
				AssignedAgent:      "executor",
				DependencyIDs:      []string{"action_scope"},
				AcceptanceCriteria: []string{"Execution prerequisites confirmed"},
			},
			{
				TaskID:             "action_review",
				Title:              "Review execution outcome",
				Description:        "Review the execution outcome and summarize next steps",
				AssignedAgent:      "writer",
				DependencyIDs:      []string{"action_execution"},
				AcceptanceCriteria: []string{"Execution outcome reviewed"},
			},
		},
	)
}

func newRunPlan(
	runState RunStateSnapshot,
	templateName string,
	summary string,
	tasks []PlannedTask,
) (RunPlanReport, error) {
	planID, err := NewID("plan")
	if err != nil {
		return RunPlanReport{}, err
	}
	return RunPlanReport{
		PlanID:       planID,
		RunID:        runState.RunID,
		WorkflowType: runState.WorkflowType,
		CreatedAt:    time.Now().UTC(),
		TemplateName: templateName,
		Summary:      summary,
		Tasks:        tasks,
	}, nil
}
