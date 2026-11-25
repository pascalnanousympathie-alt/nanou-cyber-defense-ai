"use strict";

const byId = (id) => document.getElementById(id);
let activeMetadataToken = "";
let configuredMalwareModel = null;

function setMessage(element, message, kind = "") {
  element.textContent = message;
  element.className = kind ? `form-message ${kind}` : "form-message";
}

function setLoading(element, message) {
  element.replaceChildren();
  const node = document.createElement("div");
  node.className = "loading-line";
  node.textContent = message;
  element.append(node);
}

function setError(element, message) {
  element.replaceChildren();
  const node = document.createElement("div");
  node.className = "error-line";
  node.textContent = message;
  element.append(node);
}

async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    method: options.method || "GET",
    headers: {
      Accept: "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
      ...(options.body ? { "Content-Type": "application/json" } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
    credentials: "same-origin",
    cache: "no-store",
    redirect: "error",
  });
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    const detail = typeof payload?.detail === "string" ? payload.detail : `HTTP ${response.status}`;
    throw new Error(detail);
  }
  return payload;
}

function safeExternalUrl(value) {
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

function setApiState(state, message) {
  const status = byId("api-status");
  status.dataset.state = state;
  byId("api-status-text").textContent = message;
  byId("metric-api").textContent = state === "ok" ? "Online" : state === "error" ? "Offline" : "…";
  byId("metric-api-detail").textContent = state === "ok" ? "Service mamaly" : state === "error" ? "Tsy tratra ny service" : "Miandry fanamarinana";
}

async function loadHealth() {
  try {
    const data = await apiRequest("/health");
    if (data?.status !== "ok") throw new Error("Valin'ny health tsy fantatra.");
    setApiState("ok", "API opérationnel");
  } catch (error) {
    setApiState("error", "API tsy tratra");
    setError(byId("cve-result"), error.message || "Tsy afaka nifandray tamin'ny API.");
  }
}

function selectCvss(cve) {
  const metrics = cve?.metrics || {};
  for (const key of ["cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]) {
    if (Array.isArray(metrics[key]) && metrics[key].length) {
      const item = metrics[key][0];
      return {
        score: item?.cvssData?.baseScore,
        severity: item?.cvssData?.baseSeverity || item?.baseSeverity || "Tsy voafaritra",
      };
    }
  }
  return null;
}

function renderCve(payload) {
  const result = byId("cve-result");
  result.replaceChildren();
  const cve = payload?.vulnerabilities?.[0]?.cve;
  if (!cve) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    const msg = document.createElement("p");
    msg.textContent = "Tsy nahitana CVE mifanaraka amin'io ID io.";
    empty.append(msg);
    result.append(empty);
    return;
  }

  const header = document.createElement("div");
  header.className = "result-header";
  const id = document.createElement("strong");
  id.textContent = cve.id || "CVE tsy fantatra";
  header.append(id);
  const cvss = selectCvss(cve);
  if (cvss && Number.isFinite(Number(cvss.score))) {
    const pill = document.createElement("span");
    pill.className = `score-pill${Number(cvss.score) >= 7 ? " high" : ""}`;
    pill.textContent = `CVSS ${cvss.score} · ${cvss.severity}`;
    header.append(pill);
  }
  result.append(header);

  const description = Array.isArray(cve.descriptions)
    ? cve.descriptions.find((item) => item.lang === "en")?.value || cve.descriptions[0]?.value
    : "";
  const paragraph = document.createElement("p");
  paragraph.className = "result-description";
  paragraph.textContent = description || "Tsy misy famaritana.";
  result.append(paragraph);

  const meta = document.createElement("div");
  meta.className = "result-meta";
  const published = document.createElement("span");
  published.textContent = `Published: ${cve.published || "—"}`;
  const modified = document.createElement("span");
  modified.textContent = `Modified: ${cve.lastModified || "—"}`;
  meta.append(published, modified);
  result.append(meta);

  const links = document.createElement("div");
  links.className = "result-links";
  for (const reference of (cve.references || []).slice(0, 4)) {
    const href = safeExternalUrl(reference.url);
    if (!href) continue;
    const link = document.createElement("a");
    link.href = href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "Reference ↗";
    links.append(link);
  }
  if (links.childElementCount) result.append(links);
}

async function searchCve(event) {
  event.preventDefault();
  const id = byId("cve-id").value.trim().toUpperCase();
  if (!/^CVE-[0-9]{4}-[0-9]{4,}$/.test(id)) {
    setError(byId("cve-result"), "Ampidiro amin'ny endrika CVE-YYYY-NNNN ny ID.");
    return;
  }
  setLoading(byId("cve-result"), "Mitady ao amin'ny NVD…");
  try {
    const payload = await apiRequest(`/api/cve/${encodeURIComponent(id)}`);
    renderCve(payload);
  } catch (error) {
    setError(byId("cve-result"), error.message || "Tsy nahomby ny fikarohana CVE.");
  }
}

function renderKev(data) {
  const vulnerabilities = Array.isArray(data?.vulnerabilities) ? data.vulnerabilities : [];
  byId("kev-count").textContent = vulnerabilities.length.toLocaleString();
  byId("metric-kev").textContent = vulnerabilities.length.toLocaleString();
  const list = byId("kev-list");
  list.replaceChildren();
  for (const item of vulnerabilities.slice(0, 8)) {
    const row = document.createElement("article");
    row.className = "kev-item";
    const id = document.createElement("span");
    id.textContent = item.cveID || "CVE";
    const title = document.createElement("strong");
    title.textContent = item.vulnerabilityName || item.product || "Vulnerability";
    const detail = document.createElement("p");
    detail.textContent = [item.vendorProject, item.product, item.dateAdded ? `Added ${item.dateAdded}` : ""].filter(Boolean).join(" · ");
    row.append(id, title, detail);
    list.append(row);
  }
  if (!vulnerabilities.length) setError(list, "Tsy misy firaketana azo aseho amin'izao fotoana izao.");
}

async function loadKev() {
  setLoading(byId("kev-list"), "Maka ny CISA KEV feed…");
  try {
    const data = await apiRequest("/api/kev");
    renderKev(data);
  } catch (error) {
    byId("kev-count").textContent = "—";
    byId("metric-kev").textContent = "—";
    setError(byId("kev-list"), error.message || "Tsy hita ny CISA KEV feed.");
  }
}

async function loadTools() {
  const list = byId("tools-list");
  setLoading(list, "Maka ny lisitry ny tools…");
  try {
    const tools = await apiRequest("/api/mcp/tools");
    byId("metric-tools").textContent = Array.isArray(tools) ? tools.length : "—";
    byId("tools-count").textContent = Array.isArray(tools) ? String(tools.length) : "—";
    list.replaceChildren();
    for (const item of (Array.isArray(tools) ? tools : [])) {
      const card = document.createElement("article");
      card.className = "tool-item";
      const name = document.createElement("strong");
      name.textContent = item.name || "Tool";
      const description = document.createElement("p");
      description.textContent = item.description || "Tsy misy famaritana.";
      const meta = document.createElement("div");
      meta.className = "tool-meta";
      for (const value of [item.access, item.required_scope].filter(Boolean)) {
        const chip = document.createElement("span");
        chip.textContent = value;
        meta.append(chip);
      }
      card.append(name, description, meta);
      list.append(card);
    }
  } catch (error) {
    setError(list, error.message || "Tsy nahazo ny lisitry ny MCP tools.");
  }
}

function renderMetadata(items) {
  const list = byId("metadata-list");
  list.replaceChildren();
  byId("metadata-total").textContent = String(items.length);
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "metadata-row";
    const hash = document.createElement("strong");
    hash.textContent = item.sha256 || "Hash tsy fantatra";
    const label = document.createElement("span");
    label.className = `label-${["benign", "malicious", "unknown"].includes(item.label) ? item.label : "unknown"}`;
    label.textContent = item.label || "unknown";
    row.append(hash, label);
    list.append(row);
  }
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "loading-line";
    empty.textContent = "Mbola tsy misy metadata voatahiry.";
    list.append(empty);
  }
}

async function loadMetadata() {
  try {
    const items = await apiRequest("/api/malware/metadata?limit=100", { token: activeMetadataToken });
    renderMetadata(Array.isArray(items) ? items : []);
    byId("metadata-workspace").hidden = false;
    setMessage(byId("metadata-auth-status"), "Voamarina ny token. Azo ampiasaina ny metadata.", "success");
    updateInferenceAccess();
  } catch (error) {
    activeMetadataToken = "";
    byId("api-token").value = "";
    byId("metadata-workspace").hidden = true;
    updateInferenceAccess();
    setMessage(byId("metadata-auth-status"), error.message || "Tsy nahomby ny fanamarinana.", "error");
  }
}

async function authenticateMetadata(event) {
  event.preventDefault();
  const token = byId("api-token").value.trim();
  if (!token) return;
  activeMetadataToken = token;
  byId("api-token").value = "";
  setMessage(byId("metadata-auth-status"), "Manamarina token…");
  await loadMetadata();
}

async function createMetadata(event) {
  event.preventDefault();
  if (!activeMetadataToken) {
    setMessage(byId("metadata-auth-status"), "Lany ny fidirana; ampidiro indray ny token.", "error");
    return;
  }
  const payload = {
    sha256: byId("sample-hash").value.trim(),
    label: byId("sample-label").value,
    source: byId("sample-source").value.trim(),
    family: byId("sample-family").value.trim() || null,
  };
  try {
    await apiRequest("/api/malware/metadata", {
      method: "POST",
      token: activeMetadataToken,
      body: payload,
    });
    byId("metadata-create-form").reset();
    setMessage(byId("metadata-auth-status"), "Voatahiry ny metadata.", "success");
    await loadMetadata();
  } catch (error) {
    setMessage(byId("metadata-auth-status"), error.message || "Tsy voatahiry ny metadata.", "error");
  }
}

function logoutMetadata() {
  activeMetadataToken = "";
  byId("api-token").value = "";
  byId("metadata-workspace").hidden = true;
  byId("metadata-list").replaceChildren();
  byId("metadata-total").textContent = "0";
  updateInferenceAccess();
  byId("inference-result").replaceChildren();
  setMessage(byId("metadata-auth-status"), "Nakatona ny fidirana. Tsy nisy token notehirizina.");
}



function updateInferenceAccess() {
  const ready = Boolean(configuredMalwareModel?.available);
  const authenticated = Boolean(activeMetadataToken);
  byId("inference-fields").disabled = !(ready && authenticated);
  const status = byId("model-status");
  if (!ready) {
    status.dataset.state = "error";
    status.textContent = configuredMalwareModel?.reason || "Tsy mbola misy modely voamarina napetraka ao amin'ny server.";
    return;
  }
  status.dataset.state = "ready";
  const selected = configuredMalwareModel.dataset_id;
  byId("inference-dataset").value = selected;
  const datasetName = selected === "ember2024-apk" ? "EMBER2024" : "LAMDA";
  status.textContent = authenticated
    ? `Modely ${datasetName} voamarina · ${configuredMalwareModel.feature_count} features · afaka manao inference.`
    : `Modely ${datasetName} voamarina. Ampidiro ny bearer token ao amin'ny fizarana Metadata mba hampiasana azy.`;
}

async function loadMalwareModelStatus() {
  try {
    configuredMalwareModel = await apiRequest("/api/malware/inference/status");
  } catch {
    configuredMalwareModel = { available: false, reason: "Tsy azo nohamarinina ny toetry ny modely." };
  }
  updateInferenceAccess();
}

async function runMalwareInference(event) {
  event.preventDefault();
  if (!activeMetadataToken || !configuredMalwareModel?.available) {
    setError(byId("inference-result"), "Mila modely voamarina sy bearer token aloha.");
    return;
  }
  let features;
  try {
    features = JSON.parse(byId("inference-features").value);
  } catch {
    setError(byId("inference-result"), "Tsy JSON array marina ilay feature vector.");
    return;
  }
  if (!Array.isArray(features) || features.some((value) => typeof value !== "number" || !Number.isFinite(value))) {
    setError(byId("inference-result"), "Ny feature vector dia tsy maintsy array misy isa finite ihany.");
    return;
  }
  const datasetId = byId("inference-dataset").value;
  const expected = datasetId === "ember2024-apk" ? 2568 : 4561;
  if (features.length !== expected) {
    setError(byId("inference-result"), `Ity schema ity dia mitaky ${expected} features marina.`);
    return;
  }
  if (datasetId === "lamda-apk-2022-train-2023-test" &&
      features.some((value) => !Number.isInteger(value) || value < -128 || value > 127)) {
    setError(byId("inference-result"), "Ny LAMDA dia mitaky sanda integer signed int8 (-128 hatramin'ny 127).");
    return;
  }

  setLoading(byId("inference-result"), "Manao inference amin'ny modely voamarina…");
  try {
    const result = await apiRequest("/api/malware/inference", {
      method: "POST",
      token: activeMetadataToken,
      body: { dataset_id: datasetId, schema_version: 1, features },
    });
    const area = byId("inference-result");
    area.replaceChildren();
    const wrapper = document.createElement("div");
    wrapper.className = "inference-result";
    const label = document.createElement("strong");
    label.textContent = result.classification === "malicious" ? "MALICIOUS — mila fanadihadiana" : "BENIGN — tsy nahitana famantarana araka ny modely";
    const probability = document.createElement("span");
    probability.className = "probability";
    probability.textContent = `${(result.malicious_probability * 100).toFixed(2)}% probability`;
    const note = document.createElement("p");
    note.textContent = `Dataset: ${result.dataset_id} · Features: ${result.feature_count} · Threshold: ${result.decision_threshold} · SHA-256 model: ${result.model_sha256.slice(0, 12)}…`;
    wrapper.append(label, probability, note);
    area.append(wrapper);
  } catch (error) {
    setError(byId("inference-result"), error.message || "Tsy nahomby ny inference.");
  }
}

byId("cve-form").addEventListener("submit", searchCve);
byId("refresh-kev").addEventListener("click", loadKev);
byId("metadata-auth-form").addEventListener("submit", authenticateMetadata);
byId("metadata-create-form").addEventListener("submit", createMetadata);
byId("metadata-logout").addEventListener("click", logoutMetadata);
byId("malware-inference-form").addEventListener("submit", runMalwareInference);

loadHealth();
loadKev();
loadTools();
loadMalwareModelStatus();
