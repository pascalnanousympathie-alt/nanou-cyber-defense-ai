"use strict";

const byId = (id) => document.getElementById(id);
let csrfToken = "";
let currentUser = null;
let configuredMalwareModel = null;
let adminUsersCache = [];
let adminAuditCache = [];
let currentCategory = "home";
const loadedCategories = new Set();
let googleCredentialAction = "signin";

const canAnalyze = () => Boolean(currentUser && ["admin", "analyst"].includes(currentUser.role));

const ROLE_WORKSPACES = {
  admin: {
    title: "Administrator control room",
    summary: "Fitantanana ny kaonty, fanaraha-maso ny asa ary fidirana amin'ny fitaovana fiarovana.",
    badge: "ADMIN",
    guidance: "Ny fanovana andraikitra sy ny fankatoavana mpampiasa dia hita ao amin'ny Kaonty sy fidirana. Voarakitra ao amin'ny audit log ny hetsika mifandraika amin'izany.",
    permissions: [
      ["Governance", "Manaiky na manafoana kaonty, manendry rôles ary mijery ny audit log."],
      ["Threat intelligence", "Mikaroka CVE ao amin'ny NVD sy mijery ny CISA KEV."],
      ["Malware laboratory", "Manampy metadata ary mampiasa feature analysis rehefa misy modely voamarina."]
    ],
  },
  analyst: {
    title: "Analyst operations",
    summary: "Fikarohana threat intelligence sy fanomanana angona ho an'ny fanadihadiana.",
    badge: "ANALYST",
    guidance: "Afaka manomana CSV feature voafetra sy mampiditra metadata ianao. Tsy afaka mitantana kaonty na mijery ny audit log Admin.",
    permissions: [
      ["Threat intelligence", "Mikaroka CVE sy mandinika ny lisitra CISA KEV."],
      ["Feature analysis", "Manamarina CSV feature iray (1 MiB max) ary manao inference raha misy modely voamarina."],
      ["Malware metadata", "Manampy SHA-256, label ary loharano; tsy mandray APK na executable."]
    ],
  },
  viewer: {
    title: "Read-only security workspace",
    summary: "Fijerena vaovao sy metadata amin'ny fomba read-only.",
    badge: "VIEWER",
    guidance: "Read-only ny fidiranao. Tsy misy fanovana metadata, inference, fitantanana kaonty na fidirana amin'ny audit log.",
    permissions: [
      ["Threat intelligence", "Mijery CVE/NVD sy ny CISA KEV."],
      ["Malware metadata", "Mijery ny hashes sy labels efa voatahiry."],
      ["Restricted actions", "Tsy afaka mampiditra metadata, manomana features na mitantana kaonty."]
    ],
  },
};

function updateRoleVisibility() {
  const activeRoles = currentUser ? [currentUser.role, "authenticated"] : ["public"];
  document.querySelectorAll("[data-role-visibility]").forEach((element) => {
    const allowedRoles = element.dataset.roleVisibility.split(",").map((role) => role.trim());
    const allowed = allowedRoles.some((role) => activeRoles.includes(role));
    element.dataset.roleAllowed = String(allowed);
    element.hidden = !allowed;
  });
  document.querySelectorAll(".nav-group").forEach((group) => {
    const links = Array.from(group.querySelectorAll(".nav-link"));
    if (links.length) group.hidden = !links.some((link) => !link.hidden);
  });
  if (currentUser) showCategory(currentCategory);
}

const CATEGORY_TITLES = {
  home: "Accueil",
  threat: "Threat Intelligence",
  malware: "AI & Malware Analysis",
  assistant: "Assistant & Tools",
  operations: "Operations & Developer",
  account: "Kaonty & Gouvernance",
};

function showCategory(category) {
  if (!currentUser) return;
  if (!Object.hasOwn(CATEGORY_TITLES, category)) category = "home";
  if (category === "operations" && !canAnalyze()) category = "home";
  currentCategory = category;
  const home = byId("category-home");
  home.hidden = category !== "home";
  const backbar = byId("category-backbar");
  backbar.hidden = category === "home";
  byId("category-current-title").textContent = CATEGORY_TITLES[category] || "";

  document.querySelectorAll("[data-category-view]").forEach((element) => {
    const roleAllowed = element.dataset.roleAllowed !== "false";
    element.hidden = element.dataset.categoryView !== category || !roleAllowed;
  });
  document.querySelectorAll("[data-category-target]").forEach((link) => {
    const active = link.dataset.categoryTarget === category;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  window.dispatchEvent(new CustomEvent("nanou:category-changed", {
    detail: { category },
  }));
  loadCategoryData(category);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function loadCategoryData(category) {
  if (loadedCategories.has(category)) return;
  loadedCategories.add(category);
  if (category === "home") {
    await loadHealth();
  } else if (category === "threat") {
    await Promise.all([loadHealth(), loadKev()]);
  } else if (category === "malware") {
    await Promise.all([loadMalwareModelStatus(), loadMetadata()]);
  } else if (category === "assistant") {
    await loadTools();
  } else if (category === "account" && currentUser?.role === "admin") {
    await loadAdminConsole();
  }
}

function openRegistrationDetails(event) {
  event.preventDefault();
  byId("login-form").hidden = true;
  byId("register-form").hidden = false;
  byId("google-auth-block").hidden = true;
  byId("register-open-link").hidden = true;
  byId("auth-message").textContent = "Fenoy eto ny fisoratana anarana amin'ny antsipiriany. Viewer no andraikitra voalohany ary mila fankatoavan'ny Admin.";
}

function closeRegistrationDetails(event) {
  event.preventDefault();
  byId("register-form").hidden = true;
  byId("login-form").hidden = false;
  byId("google-auth-block").hidden = false;
  byId("register-open-link").hidden = false;
}

async function handleGoogleCredential(response) {
  const credential = response?.credential;
  if (typeof credential !== "string" || credential.length < 20 || credential.length > 16384) {
    byId("google-auth-status").textContent = "Tsy voaray ny Google credential. Avereno ny fidirana.";
    return;
  }
  const linking = googleCredentialAction === "link";
  const status = linking ? byId("google-link-status") : byId("google-auth-status");
  setMessage(status, linking ? "Mampifandray ny Google account…" : "Manamarina ny kaonty Google…");
  try {
    const result = await apiRequest(linking ? "/api/auth/google/link" : "/api/auth/google", {
      method: "POST",
      body: { credential },
    });
    if (linking) {
      googleCredentialAction = "signin";
      byId("google-link-status").textContent = "Google account tafifandray soa aman-tsara.";
      await loadGoogleLinkStatus();
      return;
    }
    if (result.pending_approval) {
      byId("auth-message").textContent = result.message || "Voaray ny kaonty Google. Miandry fankatoavan'ny Administrator.";
      byId("google-auth-status").textContent = "Fangatahana voaray; mbola tsy afaka miditra raha tsy ankatoavin'ny Admin.";
      return;
    }
    await loadAuth();
  } catch (error) {
    googleCredentialAction = "signin";
    const status = linking ? byId("google-link-status") : byId("google-auth-status");
    status.textContent = error.message || "Tsy nahomby ny fanamarinana Google.";
  }
}

async function loadGoogleLinkStatus() {
  if (!currentUser) return;
  const slot = byId("google-link-button-slot");
  try {
    const status = await apiRequest("/api/auth/google/status");
    if (!status.available) {
      slot.hidden = true;
      byId("google-link-status").textContent = "Mbola tsy napetraka ny Google identity migration ao amin'ny database.";
      return;
    }
    if (status.linked) {
      slot.hidden = true;
      byId("google-link-status").textContent = "Google account efa tafifandray.";
      return;
    }
    slot.hidden = false;
    if (window.google?.accounts?.id && slot.dataset.rendered !== "true") {
      window.google.accounts.id.renderButton(slot, {
        type: "standard",
        theme: "filled_black",
        size: "large",
        text: "continue_with",
        shape: "rectangular",
        width: 250,
        click_listener: () => { googleCredentialAction = "link"; },
      });
      slot.dataset.rendered = "true";
    }
    byId("google-link-status").textContent = "Ampifandraiso ny Google mitovy amin'ny email an'ity kaonty ity.";
  } catch (error) {
    byId("google-link-status").textContent = error.message || "Tsy azo hamarinina ny Google link.";
  }
}

async function loadAuthProviders() {
  const slot = byId("google-button-slot");
  try {
    const providers = await apiRequest("/api/auth/providers");
    const google = providers?.google;
    if (!google?.enabled || typeof google.client_id !== "string") {
      byId("google-auth-status").textContent = google?.reason === "identity_storage_migration_required"
        ? "Google Sign-In miandry ny database migration; mbola miasa ny fidirana amin'ny email sy tenimiafina."
        : "Google Sign-In mbola tsy voa-configurer: mila OAuth Web Client ID sy authorized origin ao amin'ny Google Cloud.";
      if (currentUser) loadGoogleLinkStatus();
      return;
    }
    const renderGoogleButton = () => {
      if (!window.google?.accounts?.id) {
        byId("google-auth-status").textContent = "Tsy tafiditra ny Google Identity Services.";
        return;
      }
      window.google.accounts.id.initialize({
        client_id: google.client_id,
        callback: handleGoogleCredential,
        auto_select: false,
        cancel_on_tap_outside: true,
      });
      googleCredentialAction = "signin";
      window.google.accounts.id.renderButton(slot, {
        type: "standard",
        theme: "filled_black",
        size: "large",
        text: "continue_with",
        shape: "rectangular",
        width: 290,
        click_listener: () => { googleCredentialAction = "signin"; },
      });
      byId("google-auth-status").textContent = "Misorata anarana na midira amin'ny kaonty Google voamarina.";
      if (currentUser) loadGoogleLinkStatus();
    };
    if (window.google?.accounts?.id) {
      renderGoogleButton();
      return;
    }
    let script = document.querySelector('script[data-google-identity="true"]');
    if (!script) {
      script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.dataset.googleIdentity = "true";
      script.onload = renderGoogleButton;
      script.onerror = () => {
        byId("google-auth-status").textContent = "Tsy afaka nampiditra Google Identity Services.";
      };
      document.head.append(script);
    } else {
      script.addEventListener("load", renderGoogleButton, { once: true });
    }
  } catch (error) {
    slot.replaceChildren();
    byId("google-auth-status").textContent = error.message || "Tsy azo nohamarinina ny Google provider.";
  }
}

function renderRoleWorkspace() {
  const workspace = byId("role-workspace");
  if (!currentUser) {
    workspace.hidden = true;
    return;
  }
  const config = ROLE_WORKSPACES[currentUser.role];
  if (!config) {
    workspace.hidden = true;
    return;
  }
  workspace.hidden = false;
  byId("role-workspace-title").textContent = config.title;
  byId("role-workspace-summary").textContent = config.summary;
  byId("role-workspace-badge").textContent = config.badge;
  byId("role-workspace-guidance").textContent = config.guidance;
  const permissions = byId("role-workspace-permissions");
  permissions.replaceChildren();
  for (const [title, description] of config.permissions) {
    const card = document.createElement("article");
    card.className = "role-permission";
    const heading = document.createElement("strong");
    heading.textContent = title;
    const detail = document.createElement("p");
    detail.textContent = description;
    card.append(heading, detail);
    permissions.append(card);
  }
}

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

async function ensureCsrf() {
  const response = await fetch("/api/auth/csrf", {
    method: "GET",
    credentials: "same-origin",
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok || typeof payload?.csrf_token !== "string") {
    throw new Error("Tsy afaka nanokatra CSRF session.");
  }
  csrfToken = payload.csrf_token;
  return csrfToken;
}

async function apiRequest(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = {
    Accept: "application/json",
    ...(options.contentType ? { "Content-Type": options.contentType } : {}),
    ...(options.body !== undefined && !options.contentType
      ? { "Content-Type": "application/json" }
      : {}),
  };
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    if (!csrfToken) await ensureCsrf();
    headers["X-CSRF-Token"] = csrfToken;
  }
  const body = options.rawBody !== undefined
    ? options.rawBody
    : options.body !== undefined
      ? JSON.stringify(options.body)
      : undefined;
  const response = await fetch(path, {
    method,
    headers,
    body,
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
    if (response.status === 403 && payload?.detail?.startsWith("CSRF") && method !== "GET") {
      await ensureCsrf();
    }
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

function setAuthPanels(mode) {
  document.body.dataset.authState = currentUser ? "authenticated" : mode === "bootstrap" ? "bootstrap" : "anonymous";
  byId("bootstrap-panel").hidden = mode !== "bootstrap";
  byId("login-panel").hidden = mode !== "login";
  byId("register-form").hidden = true;
  byId("login-form").hidden = false;
  byId("google-auth-block").hidden = false;
  byId("register-open-link").hidden = false;
  byId("account-panel").hidden = mode !== "account";
  byId("admin-panel").hidden = mode !== "account" || currentUser?.role !== "admin";
  const badge = byId("user-badge");
  badge.hidden = !currentUser;
  badge.textContent = currentUser ? `${currentUser.display_name} · ${currentUser.role}` : "";
  byId("auth-state-pill").textContent = currentUser ? "Voamarina" : mode === "bootstrap" ? "Setup voalohany" : "Tsy tafiditra";
  byId("metadata-workspace").hidden = !currentUser;
  updateRoleVisibility();
  renderRoleWorkspace();
  byId("metadata-auth-status").textContent = currentUser
    ? `Miditra amin'ny metadata amin'ny andraikitra ${currentUser.role}.`
    : "Midira amin'ny kaonty voa-approve raha hijery na hitahiry metadata.";
  const canWriteMetadata = canAnalyze();
  byId("metadata-create-form").hidden = !canWriteMetadata;
  byId("metadata-write-access").textContent = canWriteMetadata
    ? "Fahazoan-dalana: Admin / Analyst — afaka manampy SHA-256 metadata."
    : "Read-only: afaka mijery metadata ianao fa tsy afaka manampy na manova azy.";
  updateInferenceAccess();
  window.dispatchEvent(new CustomEvent("nanou:auth-changed", {
    detail: { role: currentUser?.role || null },
  }));
}

async function loadAuth() {
  try {
    const status = await apiRequest("/api/auth/me");
    currentUser = status.user || null;
    currentCategory = "home";
    loadedCategories.clear();
    if (currentUser) {
      setAuthPanels("account");
      byId("account-name").textContent = currentUser.display_name;
      byId("account-email").textContent = currentUser.email;
      byId("account-role").textContent = currentUser.role.toUpperCase();
      byId("auth-message").textContent = "Voaaro amin'ny session manokana ny fidirana. Mikatona ho azy rehefa lany daty.";
    } else if (status.bootstrap_required) {
      setAuthPanels("bootstrap");
      updateRoleVisibility();
      byId("auth-message").textContent = "Tsy mbola misy Administrator. Ny kaonty voalohany ihany no mahazo andraikitra Admin.";
    } else {
      setAuthPanels("login");
      updateRoleVisibility();
      byId("auth-message").textContent = "Mila miditra amin'ny kaonty voa-approve ianao. Ny fisoratana anarana vaovao dia mila fankatoavan'ny Admin.";
      byId("metadata-list").replaceChildren();
      byId("metadata-total").textContent = "0";
    }
  } catch (error) {
    currentUser = null;
    setAuthPanels("login");
    updateRoleVisibility();
    byId("auth-message").textContent = error.message || "Tsy afaka nanamarina ny kaonty. Zahao ny database connection.";
  }
}

async function submitBootstrap(event) {
  event.preventDefault();
  const submit = byId("bootstrap-form").querySelector("button[type=submit]");
  submit.disabled = true;
  try {
    await apiRequest("/api/auth/bootstrap", {
      method: "POST",
      body: {
        display_name: byId("bootstrap-name").value.trim(),
        email: byId("bootstrap-email").value.trim(),
        password: byId("bootstrap-password").value,
        bootstrap_token: byId("bootstrap-token").value,
      },
    });
    byId("bootstrap-form").reset();
    await loadAuth();
  } catch (error) {
    byId("auth-message").textContent = error.message || "Tsy nahomby ny fametrahana Admin.";
  } finally {
    submit.disabled = false;
  }
}

async function submitLogin(event) {
  event.preventDefault();
  const submit = byId("login-form").querySelector("button[type=submit]");
  submit.disabled = true;
  try {
    await apiRequest("/api/auth/login", {
      method: "POST",
      body: {
        email: byId("login-email").value.trim(),
        password: byId("login-password").value,
      },
    });
    byId("login-form").reset();
    await loadAuth();
  } catch (error) {
    byId("auth-message").textContent = error.message || "Tsy nahomby ny fidirana.";
  } finally {
    submit.disabled = false;
  }
}

async function submitRegistration(event) {
  event.preventDefault();
  const submit = byId("register-form").querySelector("button[type=submit]");
  submit.disabled = true;
  try {
    const result = await apiRequest("/api/auth/register", {
      method: "POST",
      body: {
        display_name: byId("register-name").value.trim(),
        email: byId("register-email").value.trim(),
        password: byId("register-password").value,
      },
    });
    byId("register-form").reset();
    byId("auth-message").textContent = result.message || "Voaray ny fangatahana. Miandry fankatoavan'ny Admin.";
  } catch (error) {
    byId("auth-message").textContent = error.message || "Tsy voaray ny fisoratana anarana.";
  } finally {
    submit.disabled = false;
  }
}

async function submitPasswordChange(event) {
  event.preventDefault();
  const form = byId("password-change-form");
  const submit = form.querySelector("button[type=submit]");
  const currentPassword = byId("current-password").value;
  const newPassword = byId("new-password").value;
  if (newPassword !== byId("confirm-password").value) {
    byId("password-change-status").textContent = "Tsy mitovy ny fanamafisana ny tenimiafina vaovao.";
    return;
  }
  if (currentPassword === newPassword) {
    byId("password-change-status").textContent = "Mila tenimiafina vaovao tsy mitovy amin'ny taloha.";
    return;
  }
  submit.disabled = true;
  byId("password-change-status").textContent = "Manavao ny tenimiafina…";
  try {
    await apiRequest("/api/auth/password", {
      method: "POST",
      body: {
        current_password: currentPassword,
        new_password: newPassword,
      },
    });
    form.reset();
    byId("password-change-status").textContent = "Voavao ny tenimiafina. Nesorina ny session taloha rehetra.";
    await loadAuth();
  } catch (error) {
    byId("password-change-status").textContent = error.message || "Tsy nahomby ny fanovana tenimiafina.";
  } finally {
    submit.disabled = false;
  }
}

async function logoutAccount() {
  try {
    await apiRequest("/api/auth/logout", { method: "POST" });
  } catch (error) {
    byId("auth-message").textContent = error.message || "Tsy nahomby ny logout.";
    return;
  }
  currentUser = null;
  byId("metadata-create-form").reset();
  byId("metadata-list").replaceChildren();
  byId("metadata-total").textContent = "0";
  byId("inference-features").value = "";
  byId("inference-result").replaceChildren();
  await loadAuth();
}

function adminUserState(item) {
  if (!item.is_approved) return "pending";
  return item.is_active ? "active" : "disabled";
}

function renderAdminUsers(items) {
  const list = byId("admin-users");
  list.replaceChildren();
  const users = Array.isArray(items) ? items : [];
  const counts = {
    active: users.filter((item) => adminUserState(item) === "active").length,
    pending: users.filter((item) => adminUserState(item) === "pending").length,
    disabled: users.filter((item) => adminUserState(item) === "disabled").length,
  };
  byId("admin-total-users").textContent = String(users.length);
  byId("admin-active-users").textContent = String(counts.active);
  byId("admin-pending-users").textContent = String(counts.pending);
  byId("admin-disabled-users").textContent = String(counts.disabled);

  const query = byId("admin-user-search").value.trim().toLocaleLowerCase();
  const stateFilter = byId("admin-user-filter").value;
  const filtered = users.filter((item) => {
    const state = adminUserState(item);
    const matchesState = stateFilter === "all" || state === stateFilter;
    const searchable = [item.display_name, item.email, item.role, state].join(" ").toLocaleLowerCase();
    return matchesState && (!query || searchable.includes(query));
  });
  byId("admin-user-result-count").textContent = `${filtered.length} / ${users.length} kaonty aseho`;

  for (const item of filtered) {
    const row = document.createElement("article");
    row.className = "admin-user-row";
    const identity = document.createElement("div");
    identity.className = "admin-user-identity";
    const name = document.createElement("strong");
    name.textContent = item.display_name;
    const email = document.createElement("span");
    email.textContent = item.email;
    const state = adminUserState(item);
    const status = document.createElement("small");
    status.className = `admin-user-status status-${state}`;
    status.textContent = state === "pending"
      ? "Miandry fankatoavana"
      : state === "active" ? "Mavitrika" : "Voasakana / tsy mavitrika";
    identity.append(name, email, status);

    const controls = document.createElement("div");
    controls.className = "admin-user-controls";
    const role = document.createElement("select");
    role.setAttribute("aria-label", `Andraikitry ny ${item.email}`);
    for (const value of ["viewer", "analyst", "admin"]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value.toUpperCase();
      option.selected = item.role === value;
      role.append(option);
    }
    const activeLabel = document.createElement("label");
    activeLabel.className = "active-toggle";
    const active = document.createElement("input");
    active.type = "checkbox";
    active.checked = item.is_active && item.is_approved;
    activeLabel.append(active, document.createTextNode(" Mankatoaka / mampavitrika"));
    const save = document.createElement("button");
    save.className = "button button-secondary";
    save.type = "button";
    save.textContent = "Tehirizo";
    const isSelf = item.id === currentUser?.id;
    if (isSelf) {
      role.disabled = true;
      active.disabled = true;
      save.disabled = true;
      save.title = "Tsy azo ovaina eto ny kaontinao manokana.";
    }
    save.addEventListener("click", async () => {
      save.disabled = true;
      try {
        await apiRequest(`/api/admin/users/${encodeURIComponent(item.id)}`, {
          method: "PATCH",
          body: { role: role.value, is_active: active.checked },
        });
        await loadAdminConsole();
      } catch (error) {
        byId("auth-message").textContent = error.message || "Tsy voatahiry ny fanovana.";
      } finally {
        save.disabled = isSelf;
      }
    });
    controls.append(role, activeLabel, save);
    row.append(identity, controls);
    list.append(row);
  }
  if (!filtered.length) {
    const empty = document.createElement("p");
    empty.className = "loading-line";
    empty.textContent = users.length
      ? "Tsy misy kaonty mifanaraka amin'ny fikarohana na sivana."
      : "Tsy mbola misy kaonty voasoratra.";
    list.append(empty);
  }
}

function formatAuditDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value || "Daty tsy fantatra";
  try {
    return new Intl.DateTimeFormat("fr-FR", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Indian/Antananarivo",
    }).format(date);
  } catch {
    return date.toLocaleString();
  }
}

function auditOutcomeLabel(value) {
  const labels = {
    success: "Tafita",
    pending: "Miandry",
    failed: "Tsy tafita",
    blocked: "Voasakana",
    invalid_bootstrap_token: "Token diso",
    pending_or_disabled: "Kaonty tsy mavitrika",
  };
  return labels[value] || value || "Tsy fantatra";
}

function renderAudit(items) {
  const list = byId("audit-list");
  list.replaceChildren();
  const events = Array.isArray(items) ? items : [];
  const query = byId("audit-search").value.trim().toLocaleLowerCase();
  const outcomeFilter = byId("audit-outcome-filter").value;
  const filtered = events.filter((item) => {
    const outcome = item.outcome || "unknown";
    const searchable = [item.action, outcome, item.target_type, item.target_id, item.request_id]
      .filter(Boolean).join(" ").toLocaleLowerCase();
    return (outcomeFilter === "all" || outcome === outcomeFilter)
      && (!query || searchable.includes(query));
  });

  for (const item of filtered) {
    const row = document.createElement("article");
    row.className = "audit-row";
    const main = document.createElement("div");
    main.className = "audit-row-main";
    const action = document.createElement("strong");
    action.textContent = item.action || "Hetsika tsy fantatra";
    const outcome = item.outcome || "unknown";
    const badge = document.createElement("span");
    const outcomeClass = outcome.toLowerCase().replace(/[^a-z0-9_-]/g, "");
    badge.className = `audit-outcome outcome-${outcomeClass}`;
    badge.textContent = auditOutcomeLabel(outcome);
    main.append(action, badge);

    const detail = document.createElement("span");
    detail.className = "audit-row-detail";
    const target = item.target_type ? `Target: ${item.target_type}` : "";
    const request = item.request_id ? `Ref: ${item.request_id.slice(0, 14)}` : "";
    detail.textContent = [target, request].filter(Boolean).join(" · ") || "Tsy misy antsipiriany fanampiny";

    const timestamp = document.createElement("time");
    timestamp.dateTime = item.created_at || "";
    timestamp.textContent = formatAuditDate(item.created_at);
    row.append(main, detail, timestamp);
    list.append(row);
  }
  if (!filtered.length) {
    const empty = document.createElement("p");
    empty.className = "loading-line";
    empty.textContent = events.length
      ? "Tsy misy hetsika mifanaraka amin'ny fikarohana na sivana."
      : "Mbola tsy misy audit event voarakitra.";
    list.append(empty);
  }
}

async function createAdminPairing() {
  const button = byId("admin-bridge-create");
  const status = byId("admin-bridge-status");
  button.disabled = true;
  byId("admin-bridge-code-wrap").hidden = true;
  byId("admin-bridge-code").textContent = "";
  setMessage(status, "Mamorona pairing code voafetra…");
  try {
    const result = await apiRequest("/api/auth/pairing", { method: "POST" });
    byId("admin-bridge-code").textContent = result.pairing_code;
    byId("admin-bridge-code-wrap").hidden = false;
    setMessage(
      status,
      "Vita. Adikao ary ampidiro ao amin'ny Termux ao anatin'ny " +
        result.expires_in_seconds +
        " segondra. Read-only mandritra ny 15 minitra ny bridge.",
      "success",
    );
    window.clearTimeout(window.nanouAdminPairingExpiry);
    window.nanouAdminPairingExpiry = window.setTimeout(() => {
      byId("admin-bridge-code").textContent = "";
      byId("admin-bridge-code-wrap").hidden = true;
      setMessage(status, "Lany daty ny code. Mamoròna pairing code vaovao raha ilaina.");
    }, result.expires_in_seconds * 1000);
  } catch (error) {
    setMessage(status, error.message || "Tsy afaka namorona pairing code.", "error");
  } finally {
    button.disabled = false;
  }
}

async function copyAdminPairingCode() {
  const code = byId("admin-bridge-code").textContent;
  if (!code) return;
  try {
    await navigator.clipboard.writeText(code);
    setMessage(byId("admin-bridge-status"), "Voadika. Apetaho ao amin'ny Termux rehefa angatahina.", "success");
  } catch (_error) {
    setMessage(byId("admin-bridge-status"), "Tsy nahazo clipboard. Safidio ary adikao ilay code hita eo ambony.", "error");
  }
}

async function loadAdminConsole() {
  if (currentUser?.role !== "admin") return;
  try {
    const [users, audit] = await Promise.all([
      apiRequest("/api/admin/users"),
      apiRequest("/api/admin/audit?limit=100"),
    ]);
    adminUsersCache = Array.isArray(users) ? users : [];
    adminAuditCache = Array.isArray(audit) ? audit : [];
    renderAdminUsers(adminUsersCache);
    renderAudit(adminAuditCache);
  } catch (error) {
    byId("admin-users").textContent = error.message || "Tsy afaka namaky ny admin workspace.";
  }
}

function renderCvePlaceholder() {
  const result = byId("cve-result");
  if (!result.childElementCount) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    const icon = document.createElement("span");
    icon.textContent = "⌕";
    const message = document.createElement("p");
    message.textContent = "Ampidiro ny ID CVE hahitana ny antsipiriany sy ny isa CVSS.";
    empty.append(icon, message);
    result.append(empty);
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
  if (!currentUser) return;
  try {
    const items = await apiRequest("/api/malware/metadata?limit=100");
    renderMetadata(Array.isArray(items) ? items : []);
  } catch (error) {
    setMessage(byId("metadata-auth-status"), error.message || "Tsy afaka namaky metadata.", "error");
  }
}

async function createMetadata(event) {
  event.preventDefault();
  if (!canAnalyze()) {
    setMessage(byId("metadata-auth-status"), "Admin na Analyst ihany no afaka manampy metadata.", "error");
    return;
  }
  const payload = {
    sha256: byId("sample-hash").value.trim(),
    label: byId("sample-label").value,
    source: byId("sample-source").value.trim(),
    family: byId("sample-family").value.trim() || null,
  };
  try {
    await apiRequest("/api/malware/metadata", { method: "POST", body: payload });
    byId("metadata-create-form").reset();
    setMessage(byId("metadata-auth-status"), "Voatahiry ny metadata.", "success");
    await loadMetadata();
  } catch (error) {
    setMessage(byId("metadata-auth-status"), error.message || "Tsy voatahiry ny metadata.", "error");
  }
}

function updateInferenceAccess() {
  const ready = Boolean(configuredMalwareModel?.available);
  const authenticated = canAnalyze();
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
    : "Midira amin'ny kaonty Analyst na Admin mba hampiasa inference.";
}

async function loadMalwareModelStatus() {
  try {
    configuredMalwareModel = await apiRequest("/api/malware/inference/status");
  } catch {
    configuredMalwareModel = { available: false, reason: "Tsy azo nohamarinina ny toetry ny modely." };
  }
  updateInferenceAccess();
}


async function readFileAsText(file) {
  if (typeof file.text === "function") return file.text();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("Tsy afaka namaky ny CSV."));
    reader.readAsText(file, "UTF-8");
  });
}

async function prepareFeatureCsv() {
  if (!canAnalyze()) {
    setMessage(byId("feature-prepare-status"), "Admin na Analyst ihany no afaka manomana features.", "error");
    return;
  }
  const file = byId("feature-csv").files?.[0];
  if (!file) {
    setMessage(byId("feature-prepare-status"), "Safidio aloha ny CSV feature.", "error");
    return;
  }
  if (!file.name.toLowerCase().endsWith(".csv") || file.size > 1_048_576) {
    setMessage(byId("feature-prepare-status"), "CSV ihany no azo atao ary 1 MiB no fetra.", "error");
    return;
  }
  const datasetId = byId("inference-dataset").value;
  const button = byId("prepare-features");
  button.disabled = true;
  setMessage(byId("feature-prepare-status"), "Manamarina ny schema sy ny feature values…");
  try {
    const csvText = await readFileAsText(file);
    const prepared = await apiRequest(`/api/malware/features/prepare/${encodeURIComponent(datasetId)}`, {
      method: "POST",
      contentType: "text/csv",
      rawBody: csvText,
    });
    byId("inference-features").value = JSON.stringify(prepared.features);
    setMessage(
      byId("feature-prepare-status"),
      `PASS · ${prepared.feature_count} features · CSV SHA-256: ${prepared.source_content_sha256}`,
      "success",
    );
  } catch (error) {
    byId("inference-features").value = "";
    setMessage(byId("feature-prepare-status"), error.message || "Tsy nety ny feature CSV.", "error");
  } finally {
    button.disabled = false;
  }
}

async function runMalwareInference(event) {
  event.preventDefault();
  if (!canAnalyze() || !configuredMalwareModel?.available) {
    setError(byId("inference-result"), "Mila modely voamarina sy kaonty Analyst/Admin aloha.");
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
byId("bootstrap-form").addEventListener("submit", submitBootstrap);
byId("login-form").addEventListener("submit", submitLogin);
byId("register-form").addEventListener("submit", submitRegistration);
byId("logout-button").addEventListener("click", logoutAccount);
byId("password-change-form").addEventListener("submit", submitPasswordChange);
byId("refresh-admin").addEventListener("click", loadAdminConsole);
byId("admin-bridge-create").addEventListener("click", createAdminPairing);
byId("admin-bridge-copy").addEventListener("click", copyAdminPairingCode);
byId("admin-user-search").addEventListener("input", () => renderAdminUsers(adminUsersCache));
byId("admin-user-filter").addEventListener("change", () => renderAdminUsers(adminUsersCache));
byId("audit-search").addEventListener("input", () => renderAudit(adminAuditCache));
byId("audit-outcome-filter").addEventListener("change", () => renderAudit(adminAuditCache));
byId("metadata-create-form").addEventListener("submit", createMetadata);
byId("prepare-features").addEventListener("click", prepareFeatureCsv);
byId("inference-dataset").addEventListener("change", () => {
  byId("feature-csv").value = "";
  byId("inference-features").value = "";
  setMessage(byId("feature-prepare-status"), "Miova ny dataset; safidio indray ny CSV mifanaraka.");
});
byId("malware-inference-form").addEventListener("submit", runMalwareInference);
byId("register-open-link").addEventListener("click", openRegistrationDetails);
byId("register-back-link").addEventListener("click", closeRegistrationDetails);
byId("category-back-button").addEventListener("click", () => showCategory("home"));
document.querySelectorAll("[data-category-target]").forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    showCategory(link.dataset.categoryTarget);
  });
});
document.querySelectorAll("[data-open-category]").forEach((button) => {
  button.addEventListener("click", () => showCategory(button.dataset.openCategory));
});

async function initializePlatform() {
  renderCvePlaceholder();
  try {
    await ensureCsrf();
  } catch (error) {
    byId("auth-message").textContent = error.message || "Tsy azo namboarina ny CSRF session.";
  }
  await loadAuth();
  await loadAuthProviders();
}

initializePlatform();
