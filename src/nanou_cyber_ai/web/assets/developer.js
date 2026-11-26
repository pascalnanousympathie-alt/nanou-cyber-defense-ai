"use strict";

let latestDeveloperKey = "";

function clearDeveloperSecrets() {
  latestDeveloperKey = "";
  const input = document.getElementById("developer-key-value");
  const panel = document.getElementById("developer-key-once");
  if (input) {
    input.value = "";
    input.type = "password";
  }
  if (panel) panel.hidden = true;
}

function renderDeveloperKeys(items) {
  const list = document.getElementById("developer-key-list");
  list.replaceChildren();
  for (const item of (Array.isArray(items) ? items : [])) {
    const row = document.createElement("article");
    row.className = "developer-key-row";
    const identity = document.createElement("div");
    identity.className = "developer-key-identity";
    const name = document.createElement("strong");
    name.textContent = item.name;
    const prefix = document.createElement("code");
    prefix.textContent = item.token_prefix + "…";
    const scopes = document.createElement("small");
    scopes.textContent = (item.scopes || []).join(" · ");
    identity.append(name, prefix, scopes);

    const controls = document.createElement("div");
    controls.className = "developer-key-controls";
    const revoked = Boolean(item.revoked_at);
    const expired = new Date(item.expires_at).getTime() <= Date.now();
    const status = document.createElement("span");
    status.className = "developer-key-status " + (revoked ? "revoked" : expired ? "expired" : "active");
    status.textContent = revoked ? "Revoked" : expired ? "Expired" : "Active";
    const expiry = document.createElement("small");
    expiry.textContent = "Lany: " + new Intl.DateTimeFormat("fr-FR", {
      dateStyle: "medium",
      timeZone: "Indian/Antananarivo",
    }).format(new Date(item.expires_at));
    controls.append(status, expiry);
    if (!revoked && !expired) {
      const revoke = document.createElement("button");
      revoke.className = "button button-secondary";
      revoke.type = "button";
      revoke.textContent = "Revoke";
      revoke.addEventListener("click", () => revokeDeveloperKey(item.id, revoke));
      controls.append(revoke);
    }
    row.append(identity, controls);
    list.append(row);
  }
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "loading-line";
    empty.textContent = "Mbola tsy manana API key ianao.";
    list.append(empty);
  }
}

async function loadDeveloperKeys() {
  if (!canAnalyze()) return;
  try {
    const items = await apiRequest("/api/developer/keys");
    renderDeveloperKeys(Array.isArray(items) ? items : []);
  } catch (error) {
    document.getElementById("developer-key-list").textContent =
      error.message || "Tsy afaka namaky ny API keys.";
  }
}

async function createDeveloperKey(event) {
  event.preventDefault();
  if (!canAnalyze()) return;
  const scopes = Array.from(
    document.querySelectorAll('#developer-key-form input[name="scope"]:checked'),
  ).map((input) => input.value);
  if (!scopes.length) {
    setMessage(document.getElementById("developer-message"), "Safidio farafahakeliny scope iray.", "error");
    return;
  }
  const button = document.getElementById("developer-key-create");
  button.disabled = true;
  try {
    const result = await apiRequest("/api/developer/keys", {
      method: "POST",
      body: {
        name: document.getElementById("developer-key-name").value.trim(),
        scopes,
        expires_in_days: Number(document.getElementById("developer-key-expiry").value),
      },
    });
    latestDeveloperKey = result.token;
    document.getElementById("developer-key-value").value = latestDeveloperKey;
    document.getElementById("developer-key-value").type = "password";
    document.getElementById("developer-key-once").hidden = false;
    document.getElementById("developer-key-reveal").textContent = "Asehoy";
    document.getElementById("developer-key-form").reset();
    setMessage(
      document.getElementById("developer-message"),
      "Vita. Tehirizo ao amin'ny secret manager ilay token; tsy azo alaina indray rehefa miala amin'ity pejy ity.",
      "success",
    );
    await loadDeveloperKeys();
  } catch (error) {
    setMessage(
      document.getElementById("developer-message"),
      error.message || "Tsy nahomby ny famoronana API key.",
      "error",
    );
  } finally {
    button.disabled = false;
  }
}

async function copyDeveloperKey() {
  if (!latestDeveloperKey) return;
  try {
    await navigator.clipboard.writeText(latestDeveloperKey);
    setMessage(
      document.getElementById("developer-message"),
      "Voakopy ny token. Tehirizo ao amin'ny secret manager.",
      "success",
    );
  } catch {
    const input = document.getElementById("developer-key-value");
    input.type = "text";
    input.select();
    setMessage(
      document.getElementById("developer-message"),
      "Safidio ary adikao amin'ny tanana ilay token.",
      "error",
    );
  }
}

function revealDeveloperKey() {
  if (!latestDeveloperKey) return;
  const field = document.getElementById("developer-key-value");
  field.type = field.type === "password" ? "text" : "password";
  document.getElementById("developer-key-reveal").textContent =
    field.type === "password" ? "Asehoy" : "Afeno";
}

async function revokeDeveloperKey(keyId, button) {
  if (!window.confirm("Hanafoana tanteraka ity API key ity ve?")) return;
  button.disabled = true;
  try {
    await apiRequest("/api/developer/keys/" + encodeURIComponent(keyId), {
      method: "DELETE",
    });
    setMessage(document.getElementById("developer-message"), "Voasakana ilay API key.", "success");
    await loadDeveloperKeys();
  } catch (error) {
    setMessage(
      document.getElementById("developer-message"),
      error.message || "Tsy afaka nanafoana ilay API key.",
      "error",
    );
  } finally {
    button.disabled = false;
  }
}

function initializeDeveloperCenter() {
  document.getElementById("developer-key-form").addEventListener("submit", createDeveloperKey);
  document.getElementById("developer-key-refresh").addEventListener("click", loadDeveloperKeys);
  document.getElementById("developer-key-copy").addEventListener("click", copyDeveloperKey);
  document.getElementById("developer-key-reveal").addEventListener("click", revealDeveloperKey);
  document.getElementById("logout-button").addEventListener("click", clearDeveloperSecrets, true);
  // The platform's existing loader remains the source of truth for RBAC and the session.
  void (async () => {
    try {
      await loadAuth();
      if (canAnalyze()) await loadDeveloperKeys();
      else clearDeveloperSecrets();
    } catch {
      clearDeveloperSecrets();
    }
  })();
}

initializeDeveloperCenter();
