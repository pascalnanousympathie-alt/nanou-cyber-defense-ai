"use strict";

let assistantHistory = [];
let assistantBusy = false;

function assistantElement(id) {
  return document.getElementById(id);
}

function appendAssistantMessage(role, content, data = null, status = "") {
  const log = assistantElement("assistant-chat-log");
  const message = document.createElement("article");
  message.className = "assistant-message " + (role === "user" ? "user" : "assistant");

  const label = document.createElement("span");
  label.className = "assistant-message-label";
  label.textContent = role === "user" ? "Ianao" : "Nanou Assistant";

  const paragraph = document.createElement("p");
  paragraph.textContent = content;

  message.append(label, paragraph);

  if (status) {
    const meta = document.createElement("small");
    meta.className = "assistant-message-status";
    meta.textContent = status;
    message.append(meta);
  }

  if (data !== null && data !== undefined) {
    const details = document.createElement("details");
    details.className = "assistant-result-details";
    const summary = document.createElement("summary");
    summary.textContent = "Jereo ny valiny voarafitra";
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(data, null, 2);
    details.append(summary, pre);
    message.append(details);
  }

  log.append(message);
  log.scrollTop = log.scrollHeight;
  return message;
}

function setAssistantMode(mode) {
  const pill = assistantElement("assistant-mode");
  const labels = {
    ai: "AI provider connected",
    local: "Local command mode · tsy misy sarany API",
    local_fallback: "Local fallback · AI provider tsy tratra",
  };
  pill.textContent = labels[mode] || "Command mode";
  pill.dataset.mode = mode || "unknown";
}

function setAssistantBusy(busy) {
  assistantBusy = busy;
  assistantElement("assistant-chat-send").disabled = busy;
  assistantElement("assistant-chat-input").disabled = busy;
  assistantElement("assistant-chat-send").textContent = busy ? "Miasa…" : "Alefaso →";
  if (busy) assistantElement("assistant-status").textContent = "Manatanteraka ny baiko…";
}

async function sendAssistantCommand(message) {
  const clean = String(message || "").trim();
  if (!clean || assistantBusy) return;
  if (clean.length > 1000) {
    assistantElement("assistant-status").textContent = "1000 caractères no fetra.";
    return;
  }

  const previousHistory = assistantHistory.slice(-8);
  appendAssistantMessage("user", clean);
  assistantHistory.push({ role: "user", content: clean });
  assistantElement("assistant-chat-input").value = "";
  setAssistantBusy(true);

  try {
    const result = await apiRequest("/api/chat/command", {
      method: "POST",
      body: {
        message: clean,
        history: previousHistory,
      },
    });
    const reply = result.reply || "Tsy nisy valiny azo aseho.";
    const status = result.executed
      ? "Vita avy hatrany · " + (result.action || "defensive tool") + " · " + (result.mode || "local")
      : "Valiny fanazavana · " + (result.mode || "local");
    appendAssistantMessage("assistant", reply, result.data, status);
    assistantHistory.push({ role: "assistant", content: reply });
    if (result.provider_notice) {
      assistantElement("assistant-status").textContent = result.provider_notice;
    } else {
      assistantElement("assistant-status").textContent = result.executed
        ? "Vita ny asa. Tsy nisy fanovana rafitra natao."
        : "Vonona handray baiko hafa.";
    }
    setAssistantMode(result.mode);
  } catch (error) {
    const messageText = error.message || "Tsy afaka nanatanteraka ilay baiko.";
    appendAssistantMessage("assistant", messageText, null, "Tsy vita");
    assistantHistory.push({ role: "assistant", content: messageText });
    assistantElement("assistant-status").textContent = messageText;
  } finally {
    setAssistantBusy(false);
    assistantElement("assistant-chat-input").focus();
  }
}

function initializeAssistantChat() {
  const form = assistantElement("assistant-chat-form");
  if (!form || form.dataset.initialized === "true") return;
  form.dataset.initialized = "true";

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendAssistantCommand(assistantElement("assistant-chat-input").value);
  });

  document.querySelectorAll("[data-assistant-command]").forEach((button) => {
    button.addEventListener("click", () => {
      sendAssistantCommand(button.dataset.assistantCommand);
    });
  });

  assistantElement("assistant-clear").addEventListener("click", () => {
    assistantHistory = [];
    const log = assistantElement("assistant-chat-log");
    log.replaceChildren();
    appendAssistantMessage(
      "assistant",
      "Voafafa ny resaka teo amin'ity navigateur ity. Inona ny baiko manaraka?",
    );
    assistantElement("assistant-status").textContent = "Vonona handray baiko.";
  });

  assistantElement("logout-button").addEventListener("click", () => {
    assistantHistory = [];
  });

  setAssistantMode("local");
}

initializeAssistantChat();
