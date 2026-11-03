const API_BASE = "http://127.0.0.1:8765";
const defaults = { mode: "BALANCED", ad_blocking_enabled: true, tracker_blocking_enabled: true, paired_token: "", connection_status: "NOT_PAIRED", applied_rule_count: 0 };
const $ = (selector) => document.querySelector(selector);

async function getState() { return { ...defaults, ...(await chrome.storage.local.get(defaults)) }; }
function title(mode) { return mode.toLowerCase().replace(/^./, (letter) => letter.toUpperCase()); }
async function render() {
  const state = await getState();
  $("#mode-title").textContent = title(state.mode);
  $("#connection-status").textContent = state.connection_status === "CONNECTED" ? "Connected to local SOVRIVA Desktop." : state.connection_status === "DESKTOP_UNAVAILABLE" ? "Desktop app unavailable on 127.0.0.1:8765." : "Pair with the local desktop app to sync policy.";
  $("#connection-dot").classList.toggle("connected", state.connection_status === "CONNECTED");
  $("#rule-count").textContent = state.applied_rule_count || 0;
  $("#sync-time").textContent = state.last_sync_at ? new Date(state.last_sync_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—";
  document.querySelectorAll("[data-mode]").forEach((button) => button.classList.toggle("active", button.dataset.mode === state.mode));
  document.querySelectorAll("[data-setting]").forEach((button) => button.classList.toggle("on", Boolean(state[button.dataset.setting])));
}

async function update(patch) { await chrome.storage.local.set(patch); chrome.runtime.sendMessage({ type: "APPLY_POLICY", settings: patch }); await render(); }
document.querySelectorAll("[data-mode]").forEach((button) => button.addEventListener("click", () => update({ mode: button.dataset.mode })));
document.querySelectorAll("[data-setting]").forEach((button) => button.addEventListener("click", async () => { const state = await getState(); update({ [button.dataset.setting]: !state[button.dataset.setting] }); }));
$("#flush-button").addEventListener("click", async () => { await chrome.runtime.sendMessage({ type: "FLUSH" }); await render(); });
$("#pair-button").addEventListener("click", async () => {
  const code = $("#pairing-code").value.trim(); if (!/^\d{6}$/.test(code)) return;
  try {
    const extensionId = chrome.runtime.id;
    const response = await fetch(`${API_BASE}/api/pairing/claim`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ code, extension_id: extensionId }) });
    const payload = await response.json(); if (!response.ok) throw new Error(payload.detail || "Pairing failed");
    await chrome.storage.local.set({ paired_token: payload.token, extension_id: extensionId, connection_status: "CONNECTED" });
    await render();
    chrome.runtime.sendMessage({ type: "APPLY_POLICY", settings: { paired_token: payload.token } }).catch(() => {});
  } catch (error) { $("#connection-status").textContent = error.message; }
});
render();
