const form = document.querySelector("#workflowForm");
const runButton = document.querySelector("#runButton");
const runBadge = document.querySelector("#runBadge");
const taskList = document.querySelector("#taskList");
const turnTimeline = document.querySelector("#turnTimeline");
const evidenceList = document.querySelector("#evidenceList");
const outputCard = document.querySelector("#outputCard");

const stageOrder = ["intake", "plan", "analysis", "evidence", "approval", "verification"];

const statusNodes = {
  intake: document.querySelector("#intakeStatus"),
  plan: document.querySelector("#planStatus"),
  analysis: document.querySelector("#analysisStatus"),
  evidence: document.querySelector("#evidenceStatus"),
  approval: document.querySelector("#approvalStatus"),
  verification: document.querySelector("#verificationStatus"),
};

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function titleCase(value) {
  return String(value)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }

  return response.json();
}

function setActiveArea(area) {
  document.querySelectorAll("[data-area]").forEach((node) => {
    node.classList.toggle("active", node.dataset.area === area);
  });

  stageOrder.forEach((stage) => {
    const stageNode = document.querySelector(`.stage-card[data-area="${stage}"]`);
    if (!stageNode) {
      return;
    }
    const stageIndex = stageOrder.indexOf(stage);
    const activeIndex = stageOrder.indexOf(area);
    stageNode.classList.toggle("done", activeIndex > stageIndex);
    stageNode.classList.remove("error");
  });
}

function markError() {
  document.querySelectorAll(".stage-card.active").forEach((node) => {
    node.classList.add("error");
  });
}

function showToast(message) {
  const existingToast = document.querySelector(".toast");
  if (existingToast) {
    existingToast.remove();
  }

  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  document.body.appendChild(toast);
}

function resetDashboard() {
  setActiveArea("intake");
  runBadge.textContent = "Starting";
  statusNodes.intake.textContent = "Request received.";
  statusNodes.plan.textContent = "Waiting for scope and task breakdown.";
  statusNodes.analysis.textContent = "Agents have not started.";
  statusNodes.evidence.textContent = "No evidence recorded.";
  statusNodes.approval.textContent = "No review checkpoint yet.";
  statusNodes.verification.textContent = "Completion checks pending.";
  taskList.innerHTML = "";
  turnTimeline.innerHTML = "";
  evidenceList.innerHTML = "";
  outputCard.innerHTML = '<p class="muted">No final output yet.</p>';
}

function renderTasks(tasks) {
  taskList.innerHTML = tasks
    .map(
      (task) => `
        <div class="task-row ${escapeHtml(task.status)}">
          <div class="task-title">${escapeHtml(task.title)}</div>
          <div>${escapeHtml(task.description)}</div>
          <div class="meta">${escapeHtml(task.assigned_agent)} / ${escapeHtml(titleCase(task.status))}</div>
        </div>
      `,
    )
    .join("");
}

function appendTurn(turn) {
  const row = document.createElement("div");
  row.className = "timeline-row active";
  row.innerHTML = `
    <div class="timeline-title">${escapeHtml(titleCase(turn.agent_name))}</div>
    <div>${escapeHtml(turn.summary)}</div>
    <div class="meta">${escapeHtml(turn.task_id)} / ${escapeHtml(turn.resulting_run_status)}</div>
  `;
  turnTimeline.prepend(row);

  window.setTimeout(() => {
    row.classList.remove("active");
  }, 700);
}

function renderEvidence(evidence) {
  evidenceList.innerHTML = evidence
    .map(
      (item) => `
        <div class="evidence-row">
          <div class="evidence-title">${escapeHtml(titleCase(item.collected_by_agent))}</div>
          <div>${escapeHtml(item.summary)}</div>
          <div class="meta">${escapeHtml(item.source_type)} / ${Math.round(item.confidence * 100)}% confidence</div>
        </div>
      `,
    )
    .join("");
}

function renderOutput(output) {
  outputCard.innerHTML = `
    <p class="output-title">${escapeHtml(output.title)}</p>
    <div class="summary-box">${escapeHtml(output.summary)}</div>
    ${output.key_findings
      .map(
        (finding) => `
          <div class="finding-row">
            <div>${escapeHtml(finding)}</div>
          </div>
        `,
      )
      .join("")}
  `;
}

async function runWorkflow(event) {
  event.preventDefault();
  resetDashboard();
  runButton.disabled = true;
  runButton.textContent = "Running";

  const formData = new FormData(form);
  const goal = formData.get("goal");
  const workflowType = formData.get("workflowType");
  const approvalMode = formData.get("approvalMode");

  try {
    const runResponse = await api("/runs", {
      method: "POST",
      body: JSON.stringify({
        user_goal: goal,
        workflow_type: workflowType,
        approval_policy: {
          mode: approvalMode,
          require_human_approval_for_high_risk_tools: approvalMode !== "never",
          minimum_verification_confidence: 0.8,
        },
      }),
    });

    const run = runResponse.item;
    runBadge.textContent = run.run_id;
    statusNodes.intake.textContent = "Business request captured as a tracked run.";
    await sleep(450);

    setActiveArea("plan");
    const planResponse = await api(`/runs/${run.run_id}/plan`, { method: "POST" });
    renderTasks(planResponse.item.tasks.map((task) => ({ ...task, status: "ready" })));
    statusNodes.plan.textContent = `${planResponse.item.tasks.length} tasks created for ${titleCase(workflowType)}.`;
    await sleep(700);

    let latestState = null;
    let approvalCreated = false;

    for (let index = 0; index < planResponse.item.tasks.length; index += 1) {
      setActiveArea("analysis");
      const turnResponse = await api(`/runs/${run.run_id}/turns/advance`, {
        method: "POST",
      });

      latestState = turnResponse.run_state;
      appendTurn(turnResponse.turn);
      renderTasks(latestState.tasks);
      statusNodes.analysis.textContent = `${index + 1} of ${planResponse.item.tasks.length} agent turns completed.`;
      await sleep(600);

      setActiveArea("evidence");
      renderEvidence(latestState.evidence);
      statusNodes.evidence.textContent = `${latestState.evidence.length} evidence items captured from tool execution.`;
      await sleep(500);

      if (!approvalCreated && approvalMode !== "never" && latestState.evidence.length > 0) {
        setActiveArea("approval");
        const approvalResponse = await api(`/runs/${run.run_id}/approvals`, {
          method: "POST",
          body: JSON.stringify({
            requested_action: "Use AI-generated findings in the client report",
            reason: "The workflow reached a review checkpoint before final delivery.",
            risk_summary: "Business recommendations should be approved before release.",
            proposed_next_step: "Approve findings and continue verification.",
            supporting_evidence_refs: latestState.evidence.map((item) => item.evidence_id),
          }),
        });

        await sleep(450);
        await api(`/runs/${run.run_id}/approvals/${approvalResponse.item.approval_id}/decide`, {
          method: "POST",
          body: JSON.stringify({
            decision: "approve",
            reviewer_id: "demo_reviewer",
            reviewer_note: "Approved for workflow continuation.",
          }),
        });

        approvalCreated = true;
        statusNodes.approval.textContent = "Human review checkpoint approved.";
        await sleep(500);
      }
    }

    setActiveArea("verification");
    const verificationResponse = await api(`/runs/${run.run_id}/verify`, {
      method: "POST",
    });
    statusNodes.verification.textContent = `${titleCase(verificationResponse.item.verdict)} with ${Math.round(
      verificationResponse.item.confidence * 100,
    )}% confidence.`;
    await sleep(550);

    const outputResponse = await api(`/runs/${run.run_id}/finalize`, {
      method: "POST",
    });
    setActiveArea("output");
    renderOutput(outputResponse.item);
    runBadge.textContent = "Completed";
    runButton.textContent = "Run another workflow";
  } catch (error) {
    markError();
    showToast(error.message);
    runBadge.textContent = "Needs attention";
    runButton.textContent = "Retry workflow";
  } finally {
    runButton.disabled = false;
  }
}

form.addEventListener("submit", runWorkflow);
