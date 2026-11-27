"use strict";

let attackRole = null;
let attackScopes = [];
let attackReports = [];
let attackCategoryActive = false;

const attackById = (id) => document.getElementById(id);

function attackStatus(id, message, kind = "") {
  const node = attackById(id);
  node.textContent = message;
  node.dataset.state = kind;
}

function attackEmpty(container, message) {
  container.replaceChildren();
  const line = document.createElement("p");
  line.className = "attack-empty";
  line.textContent = message;
  container.append(line);
}

function attackDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

function renderAttackScopes() {
  const list = attackById("attack-scope-list");
  const select = attackById("attack-scope-select");
  list.replaceChildren();
  select.replaceChildren();

  const eligible = attackScopes.filter((scope) => scope.is_authorization_current);
  const option = document.createElement("option");
  option.value = "";
  option.textContent = eligible.length ? "Safidio ny scope…" : "Tsy misy scope manan-kery";
  select.append(option);

  for (const scope of eligible) {
    const item = document.createElement("option");
    item.value = scope.id;
    item.textContent = scope.name + " · " + scope.target;
    select.append(item);
  }
  attackById("attack-run-submit").disabled = eligible.length === 0;

  if (!attackScopes.length) {
    attackEmpty(list, "Mbola tsy misy target allowlist.");
    return;
  }

  for (const scope of attackScopes) {
    const card = document.createElement("article");
    card.className = "attack-scope-item";
    const heading = document.createElement("div");
    heading.className = "attack-scope-item-heading";
    const name = document.createElement("strong");
    name.textContent = scope.name;
    const badge = document.createElement("span");
    badge.className = "attack-scope-state " + (scope.is_authorization_current ? "active" : "inactive");
    badge.textContent = scope.is_authorization_current ? "AUTHORIZED" : scope.is_active ? "EXPIRED" : "REVOKED";
    heading.append(name, badge);

    const target = document.createElement("code");
    target.textContent = scope.target;
    const meta = document.createElement("small");
    meta.textContent = "Basis: " + scope.authorization_basis.replace(/_/g, " ") +
      " · Expires: " + attackDate(scope.authorization_expires_at);
    card.append(heading, target, meta);

    if (attackRole === "admin" && scope.is_active) {
      const revoke = document.createElement("button");
      revoke.type = "button";
      revoke.className = "text-button attack-revoke";
      revoke.textContent = "Revoke scope";
      revoke.addEventListener("click", () => revokeAttackScope(scope.id, revoke));
      card.append(revoke);
    }
    list.append(card);
  }
}

function renderAttackReports() {
  const list = attackById("attack-report-list");
  list.replaceChildren();
  attackById("attack-run-count").textContent = String(attackReports.length);
  if (!attackReports.length) {
    attackEmpty(list, "Tsy mbola nisy simulation voatahiry.");
    return;
  }

  for (const report of attackReports) {
    const details = document.createElement("details");
    details.className = "attack-report-item";
    const summary = document.createElement("summary");
    const title = document.createElement("strong");
    title.textContent = report.profile_label || report.profile;
    const sub = document.createElement("small");
    sub.textContent = (report.scope?.name || "Scope") + " · " + attackDate(report.created_at);
    summary.append(title, sub);
    details.append(summary);

    const stats = document.createElement("p");
    stats.className = "attack-report-stats";
    stats.textContent = (report.summary?.checks_prepared || 0) + " checks · " +
      (report.intensity || "passive") + " · 0 network requests · simulation only";
    details.append(stats);

    const checks = document.createElement("div");
    checks.className = "attack-check-list";
    for (const check of (report.checks || [])) {
      const row = document.createElement("article");
      row.className = "attack-check-item";
      const label = document.createElement("strong");
      label.textContent = check.id + " · " + check.title;
      const state = document.createElement("span");
      state.textContent = check.priority.toUpperCase() + " · " + check.status.replace(/_/g, " ");
      const validation = document.createElement("p");
      validation.textContent = "Validation: " + check.validation;
      const remediation = document.createElement("small");
      remediation.textContent = "Remediation: " + check.remediation;
      row.append(label, state, validation, remediation);
      checks.append(row);
    }
    details.append(checks);

    const attackMap = document.createElement("p");
    attackMap.className = "attack-report-mapping";
    attackMap.textContent = "MITRE ATT&CK: " + (report.attack_mapping || [])
      .map((item) => item.id + " " + item.technique).join(" · ");
    details.append(attackMap);

    const detectionTitle = document.createElement("strong");
    detectionTitle.className = "attack-detection-title";
    detectionTitle.textContent = "SOC detection recommendations";
    details.append(detectionTitle);
    const detections = document.createElement("div");
    detections.className = "attack-detection-list";
    for (const detection of (report.detection_recommendations || [])) {
      const row = document.createElement("article");
      row.className = "attack-detection-item";
      const label = document.createElement("strong");
      label.textContent = detection.rule_id + " · " + detection.name;
      const severity = document.createElement("span");
      severity.textContent = detection.severity.toUpperCase();
      const sources = document.createElement("small");
      sources.textContent = "Log sources: " + detection.log_sources;
      const when = document.createElement("p");
      when.textContent = "Alert when: " + detection.alert_when;
      const triage = document.createElement("small");
      triage.textContent = "SOC triage: " + detection.triage;
      row.append(label, severity, sources, when, triage);
      detections.append(row);
    }
    details.append(detections);

    const download = document.createElement("button");
    download.type = "button";
    download.className = "text-button attack-export";
    download.textContent = "Export JSON";
    download.addEventListener("click", () => exportAttackReport(report));
    details.append(download);
    list.append(details);
  }
}

function exportAttackReport(report) {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "nanou-attack-simulation-" + report.id + ".json";
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function loadAttackWorkspace() {
  if (!["admin", "analyst"].includes(attackRole)) return;
  attackStatus("attack-run-status", "Manamarina ny scopes sy ny tatitra…");
  try {
    const [scopes, reports] = await Promise.all([
      apiRequest("/api/attack/scopes"),
      apiRequest("/api/attack/simulations?limit=30"),
    ]);
    attackScopes = Array.isArray(scopes) ? scopes : [];
    attackReports = Array.isArray(reports) ? reports : [];
    renderAttackScopes();
    renderAttackReports();
    attackStatus(
      "attack-run-status",
      attackScopes.some((scope) => scope.is_authorization_current)
        ? "Vonona · scope manan-kery ihany no azo ampiasaina."
        : "Tsy mbola misy scope nahazoana alalana mbola manan-kery.",
    );
  } catch (error) {
    attackStatus("attack-run-status", error.message || "Tsy azo nohamarinina ny Attack Manager.", "error");
    attackEmpty(attackById("attack-scope-list"), "Tsy azo vakina ny allowlist.");
    attackEmpty(attackById("attack-report-list"), "Tsy azo vakina ny tatitra.");
  }
}

async function createAttackScope(event) {
  event.preventDefault();
  if (attackRole !== "admin") return;
  const button = attackById("attack-scope-submit");
  button.disabled = true;
  attackStatus("attack-scope-status", "Mitahiry ny scope sy authorization metadata…");
  try {
    await apiRequest("/api/attack/scopes", {
      method: "POST",
      body: {
        name: attackById("attack-scope-name").value.trim(),
        target: attackById("attack-scope-target").value.trim(),
        authorization_basis: attackById("attack-scope-basis").value,
        authorization_expires_on: attackById("attack-scope-expiry").value,
        authorization_confirmed: attackById("attack-scope-confirm").checked,
      },
    });
    attackById("attack-scope-form").reset();
    attackById("attack-scope-expiry").min = new Date(Date.now() + 86400000).toISOString().slice(0, 10);
    attackById("attack-scope-expiry").value = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
    attackStatus("attack-scope-status", "PASS · voatahiry ny scope. Tsy nisy fifandraisana tamin'ny target.", "success");
    await loadAttackWorkspace();
  } catch (error) {
    attackStatus("attack-scope-status", error.message || "Tsy voatahiry ny scope.", "error");
  } finally {
    button.disabled = false;
  }
}

async function runAttackSimulation(event) {
  event.preventDefault();
  if (!["admin", "analyst"].includes(attackRole)) return;
  const button = attackById("attack-run-submit");
  if (!attackById("attack-run-confirm").checked) {
    attackStatus("attack-run-status", "Ilaina ny fanamarinana authorization.", "error");
    return;
  }
  button.disabled = true;
  attackStatus("attack-run-status", "Mamorona tabletop report eo an-toerana…");
  try {
    const report = await apiRequest("/api/attack/simulations", {
      method: "POST",
      body: {
        scope_id: attackById("attack-scope-select").value,
        profile: attackById("attack-profile").value,
        intensity: attackById("attack-intensity").value,
        duration_minutes: Number(attackById("attack-duration").value),
        authorization_confirmed: attackById("attack-run-confirm").checked,
      },
    });
    attackReports = [report, ...attackReports].slice(0, 30);
    renderAttackReports();
    attackById("attack-run-confirm").checked = false;
    attackStatus(
      "attack-run-status",
      "PASS · " + report.summary.checks_prepared +
        " checks · 0 network requests · tsy nisy exploit na fanovana natao.",
      "success",
    );
  } catch (error) {
    attackStatus("attack-run-status", error.message || "Tsy nahomby ny simulation.", "error");
  } finally {
    button.disabled = !attackScopes.some((scope) => scope.is_authorization_current);
  }
}

async function revokeAttackScope(scopeId, button) {
  if (attackRole !== "admin" || button.disabled) return;
  button.disabled = true;
  try {
    await apiRequest("/api/attack/scopes/" + encodeURIComponent(scopeId) + "/revoke", {
      method: "POST",
      body: {},
    });
    await loadAttackWorkspace();
  } catch (error) {
    button.textContent = error.message || "Revoke failed";
    button.disabled = false;
  }
}

function initializeAttackSimulation() {
  const scopeForm = attackById("attack-scope-form");
  const runForm = attackById("attack-run-form");
  if (!scopeForm || scopeForm.dataset.initialized === "true") return;
  scopeForm.dataset.initialized = "true";
  runForm.addEventListener("submit", runAttackSimulation);
  scopeForm.addEventListener("submit", createAttackScope);
  attackById("attack-refresh").addEventListener("click", loadAttackWorkspace);
  attackById("attack-scope-expiry").min = new Date(Date.now() + 86400000).toISOString().slice(0, 10);
  attackById("attack-scope-expiry").value = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);

  window.addEventListener("nanou:auth-changed", (event) => {
    attackRole = event.detail?.role || null;
    attackById("attack-scope-form").hidden = attackRole !== "admin";
    attackById("attack-manager-panel").hidden = !["admin", "analyst"].includes(attackRole);
    if (!["admin", "analyst"].includes(attackRole)) {
      attackCategoryActive = false;
      attackScopes = [];
      attackReports = [];
      attackById("attack-scope-list").replaceChildren();
      attackById("attack-report-list").replaceChildren();
      attackById("attack-scope-select").replaceChildren();
      attackById("attack-run-submit").disabled = true;
    } else if (attackCategoryActive) {
      loadAttackWorkspace();
    }
  });
  window.addEventListener("nanou:category-changed", (event) => {
    attackCategoryActive = event.detail?.category === "operations";
    if (attackCategoryActive && ["admin", "analyst"].includes(attackRole)) {
      loadAttackWorkspace();
    }
  });
}

initializeAttackSimulation();
