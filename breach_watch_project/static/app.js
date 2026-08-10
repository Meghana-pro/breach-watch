const listElement = document.getElementById("incidentList");
const messageElement = document.getElementById("message");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  })[char]);
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body.detail) detail = Array.isArray(body.detail) ? body.detail.map(x => x.msg).join(", ") : body.detail;
    } catch (_) {}
    throw new Error(detail);
  }
  return response.json();
}

function showMessage(text, isError = false) {
  messageElement.textContent = text;
  messageElement.className = isError ? "message error" : "message";
}

async function loadSummary() {
  const summary = await api("/api/summary");
  document.getElementById("totalCount").textContent = summary.total_incidents;
  document.getElementById("highCount").textContent = summary.high_risk;
  document.getElementById("mediumCount").textContent = summary.medium_risk;
  document.getElementById("lowCount").textContent = summary.low_risk;
}

function renderIncident(item) {
  const types = item.data_types.map(type => `<span class="pill">${escapeHtml(type.replaceAll("_", " "))}</span>`).join("");
  const reasons = item.risk_reasons.map(reason => `<li>${escapeHtml(reason)}</li>`).join("");
  const action = item.action_completed
    ? `<span class="completed">✓ Follow-up completed</span><button class="secondary action-btn" data-id="${item.id}" data-completed="false">Reopen action</button>`
    : `<button class="primary action-btn" data-id="${item.id}" data-completed="true">Mark follow-up complete</button>`;
  const source = item.source_url
    ? `<a href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>`
    : `<span class="muted">No external source link</span>`;
  return `
    <article class="incident">
      <div class="incident-top">
        <div><h3>${escapeHtml(item.title)}</h3><p class="org">${escapeHtml(item.organization)} · ${escapeHtml(item.incident_date)} · ${escapeHtml(item.source_name)}</p></div>
        <span class="risk ${escapeHtml(item.risk_level)}">${escapeHtml(item.risk_level)} risk</span>
      </div>
      <p class="description">${escapeHtml(item.description)}</p>
      <div class="pills">${types}</div>
      <div class="incident-bottom">
        <span class="score">Risk score: <strong>${item.risk_score}/100</strong> · ${source}</span>
        <div>${action}</div>
      </div>
      <details><summary>Why this risk score?</summary><ul class="reasons">${reasons}</ul></details>
    </article>`;
}

async function loadIncidents() {
  try {
    const incidents = await api("/api/incidents");
    listElement.innerHTML = incidents.length
      ? incidents.map(renderIncident).join("")
      : "<p>No incidents yet. Add a record below.</p>";
    await loadSummary();
  } catch (error) {
    listElement.innerHTML = `<p class="muted">Could not load incidents: ${escapeHtml(error.message)}. Is the FastAPI server running?</p>`;
  }
}

listElement.addEventListener("click", async (event) => {
  const button = event.target.closest(".action-btn");
  if (!button) return;
  button.disabled = true;
  try {
    await api(`/api/incidents/${button.dataset.id}/action`, {
      method: "PATCH",
      body: JSON.stringify({ completed: button.dataset.completed === "true" })
    });
    showMessage("Follow-up status updated.");
    await loadIncidents();
  } catch (error) {
    showMessage(error.message, true);
    button.disabled = false;
  }
});

document.getElementById("refreshBtn").addEventListener("click", loadIncidents);

document.getElementById("incidentForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const payload = {
    organization: data.get("organization").trim(),
    title: data.get("title").trim(),
    source_name: data.get("source_name").trim(),
    source_url: data.get("source_url").trim(),
    incident_date: data.get("incident_date"),
    description: data.get("description").trim(),
    data_types: data.getAll("data_types")
  };
  try {
    await api("/api/incidents", { method: "POST", body: JSON.stringify(payload) });
    form.reset();
    form.elements.source_name.value = "Manual demo entry";
    form.elements.incident_date.value = new Date().toISOString().slice(0, 10);
    showMessage("Incident analyzed and saved.");
    await loadIncidents();
  } catch (error) {
    showMessage(`Could not save incident: ${error.message}`, true);
  }
});

document.querySelector('input[name="incident_date"]').value = new Date().toISOString().slice(0, 10);
loadIncidents();
