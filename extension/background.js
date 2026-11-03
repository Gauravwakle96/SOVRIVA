const API_BASE = "http://127.0.0.1:8765";
const STORAGE_DEFAULTS = {
  mode: "BALANCED",
  ad_blocking_enabled: true,
  tracker_blocking_enabled: true,
  allowlist: [],
  custom_block_domains: [],
  paired_token: "",
  extension_id: ""
};

const AD_DOMAINS = [
  "doubleclick.net", "googlesyndication.com", "googleadservices.com", "adnxs.com",
  "adsrvr.org", "taboola.com", "outbrain.com", "advertising.com", "criteo.com"
];
const TRACKER_DOMAINS = [
  "google-analytics.com", "analytics.google.com", "segment.io", "mixpanel.com",
  "connect.facebook.net", "facebook.com", "tiktok.com", "linkedin.com", "hotjar.com"
];
const PRIVACY_AD_DOMAINS = [...AD_DOMAINS, "amazon-adsystem.com", "rubiconproject.com", "pubmatic.com"];
const PRIVACY_TRACKER_DOMAINS = [...TRACKER_DOMAINS, "scorecardresearch.com", "quantserve.com", "mathtag.com"];
let eventQueue = [];
let activeMode = "BALANCED";
let lastPolicyKey = "";
let policySyncTimer = null;

function settings() { return chrome.storage.local.get(STORAGE_DEFAULTS); }

function hostname(url) {
  try { return new URL(url).hostname.toLowerCase().replace(/^www\./, ""); } catch { return ""; }
}

function registrable(domain) {
  const parts = domain.split(".");
  return parts.length > 2 ? parts.slice(-2).join(".") : domain;
}

function isThirdParty(initiator, destination) {
  if (!initiator || !destination) return false;
  return registrable(hostname(initiator)) !== registrable(destination);
}

function matchesDomain(domain, root) { return domain === root || domain.endsWith(`.${root}`); }
function normalizeUserDomain(value) {
  const domain = String(value || "").trim().toLowerCase().replace(/^https?:\/\//, "").split("/")[0].replace(/^www\./, "");
  return /^[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?$/.test(domain) && domain.includes(".") ? domain : null;
}
function classify(domain, thirdParty) {
  if (!thirdParty) return "FIRST_PARTY";
  if (AD_DOMAINS.some((root) => matchesDomain(domain, root))) return "ADVERTISING";
  if (TRACKER_DOMAINS.some((root) => matchesDomain(domain, root))) return "ANALYTICS";
  return "UNKNOWN";
}

function filterDomainRule(domain, id, priority, excludedInitiatorDomains = []) {
  return {
    id, priority, action: { type: "block" },
    condition: {
      urlFilter: `||${domain}^`,
      resourceTypes: ["main_frame", "sub_frame", "script", "image", "xmlhttprequest", "media", "ping"],
      excludedInitiatorDomains
    }
  };
}

async function applyPolicy(next) {
  const mode = next.mode || "BALANCED";
  const allowlist = (next.allowlist || []).map(normalizeUserDomain).filter(Boolean);
  const shouldAds = Boolean(next.ad_blocking_enabled) && mode !== "INTEREST";
  const shouldTrackers = Boolean(next.tracker_blocking_enabled);
  const ads = mode === "PRIVACY" ? PRIVACY_AD_DOMAINS : AD_DOMAINS;
  const trackers = mode === "PRIVACY" ? PRIVACY_TRACKER_DOMAINS : TRACKER_DOMAINS;
  const domains = [
    ...(shouldAds ? ads.map((domain, index) => filterDomainRule(domain, 1000 + index, 100, allowlist)) : []),
    ...(shouldTrackers ? trackers.map((domain, index) => filterDomainRule(domain, 2000 + index, 90, allowlist)) : []),
    ...(next.custom_block_domains || []).map(normalizeUserDomain).filter(Boolean).map((domain, index) => filterDomainRule(domain, 3000 + index, 80, allowlist))
  ];
  const policyKey = JSON.stringify({ mode, ad: shouldAds, trackers: shouldTrackers, allowlist, domains: domains.map((rule) => rule.condition.urlFilter) });
  if (policyKey === lastPolicyKey) return;
  try {
    const existing = await chrome.declarativeNetRequest.getDynamicRules();
    await chrome.declarativeNetRequest.updateDynamicRules({
      removeRuleIds: existing.map((rule) => rule.id),
      addRules: domains.slice(0, 450)
    });
    activeMode = mode;
    lastPolicyKey = policyKey;
    await chrome.storage.local.set({ mode, ad_blocking_enabled: Boolean(next.ad_blocking_enabled), tracker_blocking_enabled: Boolean(next.tracker_blocking_enabled), applied_rule_count: Math.min(domains.length, 450), cosmetic_filtering: mode === "PRIVACY" });
  } catch (error) {
    await chrome.storage.local.set({ last_policy_error: String(error), applied_rule_count: 0 });
  }
}

function schedulePolicySync() {
  clearTimeout(policySyncTimer);
  policySyncTimer = setTimeout(() => { policySyncTimer = null; syncDesktopPolicy(); }, 80);
}

async function syncDesktopPolicy() {
  const current = await settings();
  if (!current.paired_token) return applyPolicy(current);
  try {
    const response = await fetch(`${API_BASE}/api/extension/config`, { headers: { "X-SOVRIVA-TOKEN": current.paired_token } });
    if (response.ok) {
      const remote = await response.json();
      return applyPolicy({ ...current, ...remote });
    }
    if (response.status === 401) await chrome.storage.local.set({ paired_token: "", connection_status: "REAUTH_REQUIRED" });
  } catch { await chrome.storage.local.set({ connection_status: "DESKTOP_UNAVAILABLE" }); }
  return applyPolicy(current);
}

async function flushEvents() {
  const current = await settings();
  if (!current.paired_token || !eventQueue.length) return;
  const batch = eventQueue.splice(0, 50);
  try {
    const response = await fetch(`${API_BASE}/api/observations`, {
      method: "POST", headers: { "Content-Type": "application/json", "X-SOVRIVA-TOKEN": current.paired_token },
      body: JSON.stringify({ observations: batch })
    });
    if (!response.ok) eventQueue.unshift(...batch);
    else await chrome.storage.local.set({ connection_status: "CONNECTED", last_sync_at: new Date().toISOString() });
  } catch { eventQueue.unshift(...batch); await chrome.storage.local.set({ connection_status: "DESKTOP_UNAVAILABLE" }); }
}

function observe(details) {
  if (!details.url || details.url.startsWith("chrome-extension://")) return;
  const destination = hostname(details.url);
  if (!destination) return;
  // Do not turn SOVRIVA's own loopback sync traffic into user observations.
  if (destination === "127.0.0.1" || destination === "localhost") return;
  const initiator = hostname(details.initiator || details.documentUrl || "");
  const thirdParty = isThirdParty(initiator, destination);
  eventQueue.push({
    observed_at: new Date().toISOString(), tab_id: details.tabId >= 0 ? details.tabId : null,
    initiator_domain: initiator || null, destination_domain: destination,
    resource_type: details.type || "other", third_party: thirdParty,
    classification: classify(destination, thirdParty), decision: "OBSERVED", mode: activeMode, source: "extension"
  });
  if (eventQueue.length >= 50) flushEvents();
}

chrome.runtime.onInstalled.addListener(async () => { const current = await settings(); await chrome.storage.local.set({ ...STORAGE_DEFAULTS, ...current, connection_status: "NOT_PAIRED" }); await applyPolicy({ ...STORAGE_DEFAULTS, ...current }); });
chrome.runtime.onStartup.addListener(syncDesktopPolicy);
chrome.webRequest.onBeforeRequest.addListener(observe, { urls: ["<all_urls>"] });
chrome.alarms.create("sovriva-sync", { periodInMinutes: 0.25 });
chrome.alarms.onAlarm.addListener((alarm) => { if (alarm.name === "sovriva-sync") { syncDesktopPolicy(); flushEvents(); } });
chrome.storage.onChanged.addListener((changes) => {
  if (["mode", "ad_blocking_enabled", "tracker_blocking_enabled", "allowlist", "custom_block_domains", "paired_token"].some((key) => changes[key])) schedulePolicySync();
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    if (message.type === "GET_STATE") return sendResponse(await settings());
    if (message.type === "APPLY_POLICY") { await applyPolicy({ ...(await settings()), ...message.settings }); return sendResponse({ ok: true }); }
    if (message.type === "FLUSH") { await flushEvents(); return sendResponse({ ok: true }); }
    return sendResponse({ ok: false });
  })();
  return true;
});
