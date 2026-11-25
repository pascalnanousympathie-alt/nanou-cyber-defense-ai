"use strict";

function simulationElement(id) {
  return document.getElementById(id);
}

let simulationConfigLoaded = false;
let simulationConfigLoading = false;

function setSimulationStatus(message, state = "") {
  const status = simulationElement("simulation-status");
  if (!status) return;
  status.textContent = message;
  status.dataset.state = state;
}

function fillSimulationSelect(select, options, placeholder) {
  select.replaceChildren();
  const first = document.createElement("option");
  first.value = "";
  first.textContent = placeholder;
  first.disabled = true;
  first.selected = true;
  select.append(first);
  for (const option of options) {
    const item = document.createElement("option");
    item.value = option.id;
    item.textContent = option.label;
    select.append(item);
  }
}

async function loadSimulationConfiguration() {
  if (simulationConfigLoaded || simulationConfigLoading) return;
  const section = simulationElement("attack-simulation");
  if (!section || section.hidden) return;
  simulationConfigLoading = true;
  setSimulationStatus("Maka ny configuration sy ny allowlist…");
  try {
    const config = await apiRequest("/api/simulations/config");
    const target = simulationElement("simulation-target");
    fillSimulationSelect(target, config.targets || [], "Safidio ny lab target");
    fillSimulationSelect(
      simulationElement("simulation-profile"),
      config.profiles || [],
      "Safidio ny profil",
    );
    fillSimulationSelect(
      simulationElement("simulation-intensity"),
      config.intensities || [],
      "Safidio ny intensity",
    );

    const controls = config.controls || {};
    const mode = simulationElement("simulation-mode");
    mode.textContent = config.mode === "offline_synthetic_only"
      ? "OFFLINE · SYNTHETIC"
      : "DISABLED";
    const runButton = simulationElement("simulation-run");
    runButton.disabled = !config.targets?.length || !controls.authorization_required;
    if (!config.targets?.length) {
      setSimulationStatus(
        "Tsy mbola misy target ID ao amin'ny allowlist. Ampidiro amin'ny server environment ny NANOU_SIMULATION_ALLOWED_TARGETS.",
        "error",
      );
    } else {
      setSimulationStatus(
        "Vonona ny simulation offline. Admin/Analyst ihany; 10 runs isan'ora no fetra.",
      );
    }
    simulationConfigLoaded = true;
  } catch (error) {
    setSimulationStatus(error.message || "Tsy afaka naka ny simulation configuration.", "error");
  } finally {
    simulationConfigLoading = false;
  }
}

function renderSimulationResult(result) {
  const container = simulationElement("simulation-result");
  container.replaceChildren();
  container.hidden = false;

  const header = document.createElement("div");
  header.className = "simulation-result-header";
  const title = document.createElement("strong");
  title.textContent = "Simulation report · " + result.status;
  header.append(title);

  const badges = document.createElement("div");
  badges.className = "simulation-result-badges";
  for (const value of [
    result.profile_label,
    "Intensity: " + result.intensity,
    (result.events_generated || 0) + " synthetic signals",
    "No network activity",
  ]) {
    const badge = document.createElement("span");
    badge.textContent = value;
    badges.append(badge);
  }
  header.append(badges);
  container.append(header);

  const summary = document.createElement("p");
  summary.className = "simulation-status";
  summary.textContent =
    "Target ID: " + result.target_id +
    " · Reference: " + result.authorization_reference +
    " · Run ID: " + result.simulation_id;
  container.append(summary);

  const events = document.createElement("div");
  events.className = "simulation-events";
  for (const event of result.events || []) {
    const article = document.createElement("article");
    article.className = "simulation-event";
    const top = document.createElement("div");
    top.className = "simulation-event-top";
    const name = document.createElement("strong");
    name.textContent = event.technique || "Synthetic signal";
    const id = document.createElement("span");
    id.textContent = event.technique_id || "MITRE";
    top.append(name, id);

    const signal = document.createElement("p");
    signal.textContent = event.signal || "";
    const detection = document.createElement("small");
    detection.textContent = "Detection: " + (event.detection_logic || "");
    const recommendation = document.createElement("small");
    recommendation.className = "simulation-recommendation";
    recommendation.textContent = "Action: " + (event.recommended_action || "");
    article.append(top, signal, detection, recommendation);
    events.append(article);
  }
  container.append(events);

  const note = document.createElement("p");
  note.className = "data-note";
  note.textContent =
    "Fiofanana ihany ity valiny ity. Tsy nisy target tena nifandraisana na vulnerability tena nosedraina.";
  container.append(note);
}

async function runAttackSimulation(event) {
  event.preventDefault();
  const form = simulationElement("simulation-form");
  const runButton = simulationElement("simulation-run");
  const payload = {
    target_id: simulationElement("simulation-target").value,
    profile: simulationElement("simulation-profile").value,
    intensity: simulationElement("simulation-intensity").value,
    authorization_reference: simulationElement("simulation-authorization-reference").value.trim(),
    authorization_acknowledged: simulationElement("simulation-authorization-ack").checked,
  };

  if (!payload.target_id || !payload.profile || !payload.intensity) {
    setSimulationStatus("Fenoy aloha ny target, profile ary intensity.", "error");
    return;
  }
  if (!payload.authorization_acknowledged) {
    setSimulationStatus("Ilaina ny fanamafisana mazava fa manana alalana ianao.", "error");
    return;
  }
  if (!payload.authorization_reference) {
    setSimulationStatus("Ampidiro ny reference de validation na ticket.", "error");
    return;
  }

  runButton.disabled = true;
  setSimulationStatus("Mamokatra synthetic telemetry offline…");
  try {
    const result = await apiRequest("/api/simulations/run", {
      method: "POST",
      body: payload,
    });
    renderSimulationResult(result);
    setSimulationStatus(
      "Vita ny simulation offline. Audit event voarakitra; tsy nisy fifandraisana tamin'ny target.",
      "success",
    );
  } catch (error) {
    setSimulationStatus(error.message || "Tsy tanteraka ny simulation.", "error");
  } finally {
    runButton.disabled = false;
  }
}

function initializeSimulationManager() {
  const section = simulationElement("attack-simulation");
  const form = simulationElement("simulation-form");
  if (!section || !form || form.dataset.initialized === "true") return;
  form.dataset.initialized = "true";
  form.addEventListener("submit", runAttackSimulation);

  simulationElement("simulation-refresh").addEventListener("click", () => {
    simulationConfigLoaded = false;
    loadSimulationConfiguration();
  });

  const observer = new MutationObserver(() => {
    if (!section.hidden) loadSimulationConfiguration();
  });
  observer.observe(section, { attributes: true, attributeFilter: ["hidden"] });
  if (!section.hidden) loadSimulationConfiguration();
}

initializeSimulationManager();
