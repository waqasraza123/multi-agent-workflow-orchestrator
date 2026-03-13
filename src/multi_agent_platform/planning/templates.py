from multi_agent_platform.contracts.run_plans import PlannedTask, RunPlanReport
from multi_agent_platform.contracts.runs import RunStateSnapshot, WorkflowType


def build_run_plan(run_state: RunStateSnapshot) -> RunPlanReport:
    if run_state.workflow_type is WorkflowType.TECHNICAL_PLAN:
        return build_technical_plan(run_state)
    if run_state.workflow_type is WorkflowType.DOCUMENT_ANALYSIS:
        return build_document_analysis_plan(run_state)
    if run_state.workflow_type is WorkflowType.RESEARCH_REPORT:
        return build_research_report_plan(run_state)
    return build_assisted_action_plan(run_state)


def build_technical_plan(run_state: RunStateSnapshot) -> RunPlanReport:
    tasks = [
        PlannedTask(
            task_id="plan_scope_review",
            title="Review request scope",
            description="Review the user goal and identify the technical planning scope",
            assigned_agent="planner",
            acceptance_criteria=["Scope and assumptions identified"],
        ),
        PlannedTask(
            task_id="plan_dependency_analysis",
            title="Analyze dependencies",
            description="Identify dependencies, risks, and technical constraints",
            assigned_agent="researcher",
            dependency_ids=["plan_scope_review"],
            acceptance_criteria=["Dependencies and risks documented"],
        ),
        PlannedTask(
            task_id="plan_delivery_outline",
            title="Draft delivery plan",
            description="Create the execution plan with milestones and validation steps",
            assigned_agent="writer",
            dependency_ids=["plan_dependency_analysis"],
            acceptance_criteria=["Execution plan drafted"],
        ),
    ]
    return RunPlanReport(
        run_id=run_state.run_id,
        workflow_type=run_state.workflow_type,
        template_name="technical_plan_default",
        summary=(
            "Default technical planning workflow with scope analysis, "
            "dependency review, and delivery planning."
        ),
        tasks=tasks,
    )


def build_document_analysis_plan(run_state: RunStateSnapshot) -> RunPlanReport:
    tasks = [
        PlannedTask(
            task_id="document_intake",
            title="Review documents",
            description="Review the provided documents and identify the analysis targets",
            assigned_agent="researcher",
            acceptance_criteria=["Document scope identified"],
        ),
        PlannedTask(
            task_id="document_findings",
            title="Extract findings",
            description="Extract key findings, contradictions, and risks from the documents",
            assigned_agent="researcher",
            dependency_ids=["document_intake"],
            acceptance_criteria=["Findings extracted"],
        ),
        PlannedTask(
            task_id="document_summary",
            title="Prepare analysis summary",
            description="Prepare the final summary of the document analysis",
            assigned_agent="writer",
            dependency_ids=["document_findings"],
            acceptance_criteria=["Summary prepared"],
        ),
    ]
    return RunPlanReport(
        run_id=run_state.run_id,
        workflow_type=run_state.workflow_type,
        template_name="document_analysis_default",
        summary=(
            "Default document analysis workflow with intake, findings extraction, "
            "and summary preparation."
        ),
        tasks=tasks,
    )


def build_research_report_plan(run_state: RunStateSnapshot) -> RunPlanReport:
    tasks = [
        PlannedTask(
            task_id="research_scope",
            title="Define research scope",
            description="Define the topic, constraints, and success criteria for the report",
            assigned_agent="planner",
            acceptance_criteria=["Research scope defined"],
        ),
        PlannedTask(
            task_id="research_collection",
            title="Collect research evidence",
            description="Collect evidence and source material relevant to the report",
            assigned_agent="researcher",
            dependency_ids=["research_scope"],
            acceptance_criteria=["Evidence collected"],
        ),
        PlannedTask(
            task_id="research_report",
            title="Draft research report",
            description="Prepare the final research report with findings and conclusions",
            assigned_agent="writer",
            dependency_ids=["research_collection"],
            acceptance_criteria=["Report drafted"],
        ),
    ]
    return RunPlanReport(
        run_id=run_state.run_id,
        workflow_type=run_state.workflow_type,
        template_name="research_report_default",
        summary=(
            "Default research report workflow with scoping, evidence collection, "
            "and report drafting."
        ),
        tasks=tasks,
    )


def build_assisted_action_plan(run_state: RunStateSnapshot) -> RunPlanReport:
    tasks = [
        PlannedTask(
            task_id="action_scope",
            title="Define action scope",
            description="Define the requested action and constraints before execution",
            assigned_agent="planner",
            acceptance_criteria=["Action scope defined"],
        ),
        PlannedTask(
            task_id="action_execution",
            title="Prepare execution",
            description="Prepare the execution path and confirm prerequisites",
            assigned_agent="executor",
            dependency_ids=["action_scope"],
            acceptance_criteria=["Execution prerequisites confirmed"],
        ),
        PlannedTask(
            task_id="action_review",
            title="Review execution outcome",
            description="Review the execution outcome and summarize next steps",
            assigned_agent="writer",
            dependency_ids=["action_execution"],
            acceptance_criteria=["Execution outcome reviewed"],
        ),
    ]
    return RunPlanReport(
        run_id=run_state.run_id,
        workflow_type=run_state.workflow_type,
        template_name="assisted_action_default",
        summary=(
            "Default assisted action workflow with scoping, execution preparation, "
            "and outcome review."
        ),
        tasks=tasks,
    )
