/* SOVRIVA dashboard: dependency-light, local-only UI. */

const state = {
  view: "overview",
  dashboard: null,
  imports: [],
  interests: [],
  comparison: null,
  graph: null,
  actions: [],
  pairing: null,
  drift: null,
  selectedEvidence: null,
};
let refreshGeneration = 0;

const titles = {
  overview: ["Overview", "Your local privacy intelligence workspace.", "See what is known, what is inferred, and what is still missing — without sending your data anywhere."],
  dna: ["Advertising Profile DNA", "A source-linked view of your reported interests.", "Only imported platform records appear here. SOVRIVA never invents interests when an export is incomplete."],
  drift: ["Profile Drift Intelligence", "Observe change without confusing absence for deletion.", "Compare real snapshots and inspect the evidence behind each added, retained, or uncertain record."],
  comparison: ["Cross-Platform Comparison", "One taxonomy. Every original label preserved.", "Reconcile Google and Meta records while keeping uncertain matches visible instead of forcing them."],
  misprofiling: ["Misprofiling Detector", "Your interpretation stays separate from platform evidence.", "Classify records as accurate, inaccurate, outdated, or unsure. Your feedback never overwrites imported data."],
  evidence: ["Evidence Provenance", "Every conclusion should have a trail.", "Inspect source files, original record paths, detection method, algorithm version, and uncertainty."],
  actions: ["Privacy Action Verifier", "Measure an observable change after a privacy action.", "Record what you changed, import a later snapshot, and get an evidence-limited outcome."],
  monitor: ["Live Browser Monitor", "Local browser observations, not surveillance.", "The extension sends normalized metadata only. Passwords, cookies, request bodies, and page content never enter SOVRIVA."],
  blocking: ["Ad Blocking Engine", "Network rules you can inspect.", "DNR enforcement is separate from tracker protection. Exact blocked-request telemetry is only shown when Chrome exposes it reliably."],
  tracking: ["Tracker Protection", "Reduce known third-party tracking paths.", "Advertising, analytics, social, essential, and unknown domains remain separate classifications."],
  footprint: ["Digital Footprint", "From a visited site to an evidence record.", "This map is built from stored extension observations. No observation means no edge."],
  "why-ad": ["Why This Ad?", "Local screenshot investigation.", "OCR runs in the browser after the local worker is available. Screenshots are never uploaded to SOVRIVA."],
  experiment: ["Privacy Experiment Lab", "A controlled way to verify browser rules.", "Run the local first-party and third-party fixtures, then compare requests received under each mode."],
  settings: ["Settings", "Control the local workspace.", "Mode changes are persisted locally and are consumed by the paired extension on its next policy sync."],
  sync: ["Automatic Sync", "Transparent connection status.", "Manual imports remain the default. No provider is marked connected without a real authorization flow."],
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
}

function formatNumber(value) { return new Intl.NumberFormat().format(Number(value || 0)); }
function formatDate(value) { if (!value) return "Not available"; const parsed = new Date(value); return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }); }
function label(value) { return String(value || "").replaceAll("_", " ").toLowerCase().replace(/(^|\s)\S/g, (letter) => letter.toUpperCase()); }
function pill(value, kind = "") { return `<span class="pill ${kind ? `pill-${kind}` : ""}">${escapeHtml(label(value))}</span>`; }

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  const content = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof content.detail === "string" ? content.detail : content.detail?.message || `Request failed (${response.status})`);
  return content;
}

function toast(message, error = false) {
  const region = document.querySelector("#toast-region");
  const item = document.createElement("div");
  item.className = `toast${error ? " error" : ""}`;
  item.textContent = message;
  region.appendChild(item);
  window.setTimeout(() => item.remove(), 4300);
}

async function refresh() {
  const generation = ++refreshGeneration;
  try {
    // Paint the main workspace as soon as the two data sources needed for it respond.
    // Larger view-specific lists continue loading in the background.
    const [dashboard, pairing] = await Promise.all([api("/api/dashboard"), api("/api/pairing/status")]);
    if (generation !== refreshGeneration) return;
    state.dashboard = dashboard;
    state.imports = dashboard.imports || [];
    state.interests = dashboard.interests || [];
    state.pairing = { ...(state.pairing || {}), ...pairing };
    render();
    Promise.allSettled([api("/api/imports"), api("/api/interests"), api("/api/privacy-actions"), api("/api/graph")]).then((results) => {
      if (generation !== refreshGeneration) return;
      const [imports, interests, actions, graph] = results;
      if (imports.status === "fulfilled") state.imports = imports.value;
      if (interests.status === "fulfilled") state.interests = interests.value;
      if (actions.status === "fulfilled") state.actions = actions.value;
      if (graph.status === "fulfilled") state.graph = graph.value;
      render();
    });
  } catch (error) { toast(error.message, true); }
}

function pageHead() {
  const [title, subtitle, description] = titles[state.view];
  document.querySelector("#page-breadcrumb").textContent = title;
  return `<div class="page-head"><div class="page-head-copy"><p class="eyebrow">${escapeHtml(subtitle.toUpperCase())}</p><h1>${escapeHtml(title)}</h1><p>${escapeHtml(description)}</p></div><div class="head-actions">${state.view === "overview" ? `<button class="btn" data-action="download-report">Export report</button><button class="btn" data-action="seed-demo">Explore isolated demo</button><button class="btn btn-primary" data-action="import-any">Import archive</button>` : ""}</div></div>`;
}

function metric(labelText, value, foot) { return `<div class="metric-card"><div class="metric-label">${escapeHtml(labelText)}</div><div class="metric-value">${formatNumber(value)}</div><div class="metric-foot">${escapeHtml(foot)}</div></div>`; }

function emptyState(title, body, action = "") { return `<div class="empty-state"><div class="empty-icon">⌁</div><h3>${escapeHtml(title)}</h3><p>${escapeHtml(body)}</p>${action}</div>`; }

function architecturePanel() {
  const settings = state.dashboard?.settings || { mode: "BALANCED" };
  const stages = [
    ["01", "Import", "Supported ZIP", "blue"],
    ["02", "Normalize", "Original labels", "violet"],
    ["03", "Intelligence", "Drift + matching", "blue"],
    ["04", "Evidence", "Source provenance", "green"],
    ["05", "Verify", "Observable outcome", "orange"],
    ["06", "Dashboard", settings.mode + " mode", "navy"],
  ];
  return `<section class="panel architecture-panel"><div class="panel-header"><div><div class="panel-title">Evidence-led architecture</div><div class="panel-subtitle">A local workflow from user-authorized data to an inspectable conclusion.</div></div><span class="pill pill-green">LOCAL-FIRST</span></div><div class="architecture-track">${stages.map(([number, title, detail, tone], index) => `<div class="architecture-stage tone-${tone}"><span>${number}</span><strong>${title}</strong><small>${detail}</small></div>${index < stages.length - 1 ? "<i class=\"architecture-arrow\">→</i>" : ""}`).join("")}</div><div class="architecture-foot"><span><b>FastAPI</b> loopback service</span><span><b>SQLite</b> evidence store</span><span><b>MV3</b> browser companion</span><span class="planned"><b>AI</b> planned, not benchmarked</span></div></section>`;
}

function importSurface() {
  return `<section class="import-surface" id="import-dropzone" tabindex="0" aria-label="Import a supported ZIP archive"><div class="import-orbit"><span></span><span></span><span></span></div><div><div class="import-kicker">LOCAL IMPORT WORKSPACE</div><strong>Bring your evidence. Keep your control.</strong><p>Drop a supported Google or Meta ZIP here, or choose an archive to validate locally.</p></div><button class="btn btn-primary" data-action="import-any">Choose ZIP archive</button></section>`;
}

function overviewView() {
  const dashboard = state.dashboard || { metrics: {}, categories: [], interests: [], observations: [], settings: { mode: "BALANCED" } };
  const metrics = dashboard.metrics || {};
  const categories = dashboard.categories || [];
  const interests = dashboard.interests || [];
  const observations = dashboard.observations || [];
  const maxCategory = Math.max(1, ...categories.map((item) => item.count));
  const bars = Array.from({ length: 8 }, (_, index) => categories[index] || { category: "", count: 0 });
  return `${pageHead()}${importSurface()}
    <div class="metric-grid">
      ${metric("Imported interests", metrics.interests, metrics.interests ? "From stored source records" : "Nothing imported yet")}
      ${metric("Observed requests", metrics.observed_requests, metrics.observed_requests ? "Extension metadata" : "Extension not connected")}
      ${metric("Ad-related observed", metrics.classified_ads, "Classified locally")}
      ${metric("Verified blocked", metrics.verified_blocked, metrics.verified_blocked ? "Reliable telemetry only" : "No verified telemetry")}
    </div>
    <div class="content-grid">
      <section class="panel chart-panel"><div class="panel-header"><div><div class="panel-title">Interest landscape</div><div class="panel-subtitle">Normalized categories from available imports</div></div><button class="panel-link" data-view="dna">Open DNA →</button></div>
        ${categories.length ? `<div class="chart-bars">${bars.map((item) => `<div class="bar-group" title="${escapeHtml(label(item.category))}: ${item.count}"><div class="bar" style="height:${Math.max(3, (item.count / maxCategory) * 92)}%"></div></div>`).join("")}</div><div class="bar-labels">${bars.map((item) => `<span>${escapeHtml((item.category || "—").slice(0, 9))}</span>`).join("")}</div>` : emptyState("No imported profile yet", "Bring a Google Takeout or Meta Accounts Center ZIP into the local workspace. A sample mode is available for a judge walkthrough.", `<button class="btn btn-blue" data-action="import-any">Choose an archive</button>`)}
      </section>
      <section class="signal-card"><div class="panel-header"><div><div class="panel-title">Workspace signal</div><div class="panel-subtitle">Evidence coverage, not a risk score</div></div><span class="pill pill-blue">${escapeHtml(label(dashboard.settings?.mode || "BALANCED"))}</span></div>
        <div class="signal-main"><div class="signal-score">${metrics.interests ? "✓" : "—"}</div><div><strong>${metrics.interests ? "Evidence is ready" : "Waiting for evidence"}</strong><span>${metrics.interests ? `${formatNumber(metrics.interests)} imported records available` : "No personal records stored"}</span></div></div>
        <div class="signal-note">${escapeHtml(dashboard.data_notice || "Local records only. Nothing is estimated.")}</div>
      </section>
    </div>
    ${architecturePanel()}<div class="bottom-grid"><section class="panel"><div class="panel-header"><div><div class="panel-title">Recent profile records</div><div class="panel-subtitle">Platform labels remain unchanged</div></div><button class="panel-link" data-view="dna">View all →</button></div>${interests.length ? interestTable(interests.slice(0, 6)) : emptyState("Your profile starts with your exports", "SOVRIVA will preserve the original label, source file, and record path for every supported interest.")}</section>
      <section class="panel"><div class="panel-header"><div><div class="panel-title">Live activity</div><div class="panel-subtitle">Normalized metadata from the extension</div></div><button class="panel-link" data-view="monitor">Monitor →</button></div>${observations.length ? observationTable(observations.slice(0, 5)) : emptyState("No browser observations", "Pair the extension to see real request metadata. SOVRIVA does not generate activity for an empty workspace.", `<button class="btn" data-view="monitor">Pair extension</button>`)}</section></div>`;
}

function interestTable(records) {
  return `<div class="table-wrap"><table><thead><tr><th>Original label</th><th>Platform</th><th>Category</th><th>Evidence</th><th>Confidence</th></tr></thead><tbody>${records.map((item) => `<tr><td><strong>${escapeHtml(item.original_label)}</strong><small class="muted-cell">${escapeHtml(item.source_file)}</small></td><td>${pill(item.platform, item.platform === "google" ? "blue" : "violet")}</td><td>${escapeHtml(label(item.category))}</td><td>${pill(item.evidence_type, "green")}</td><td>${Math.round((item.confidence || 0) * 100)}%</td></tr>`).join("")}</tbody></table></div>`;
}

function observationTable(records) {
  return `<div class="table-wrap"><table><thead><tr><th>Destination</th><th>Type</th><th>Class</th><th>Decision</th><th>Time</th></tr></thead><tbody>${records.map((item) => `<tr><td><strong>${escapeHtml(item.destination_domain)}</strong><small class="muted-cell">${escapeHtml(item.initiator_domain || "unknown initiator")}</small></td><td>${escapeHtml(item.resource_type)}</td><td>${pill(item.classification, item.classification === "ADVERTISING" ? "orange" : item.classification === "ANALYTICS" || item.classification === "SOCIAL" ? "violet" : "green")}</td><td>${pill(item.decision, item.decision === "VERIFIED_BLOCKED" ? "green" : "")}</td><td>${escapeHtml(formatDate(item.observed_at))}</td></tr>`).join("")}</tbody></table></div>`;
}

function dnaView() {
  return `${pageHead()}<section class="panel"><div class="filters"><input class="input wide-input" id="interest-search" placeholder="Search original or normalized labels"/><select class="select" id="interest-platform"><option value="">All platforms</option><option value="google">Google</option><option value="meta">Meta</option></select><select class="select" id="interest-category"><option value="">All categories</option>${[...new Set(state.interests.map((item) => item.category))].sort().map((item) => `<option value="${escapeHtml(item)}">${escapeHtml(label(item))}</option>`).join("")}</select></div><div id="dna-table">${interestTable(state.interests)}</div></section><section class="panel full-panel"><div class="panel-header"><div><div class="panel-title">Profile relationship view</div><div class="panel-subtitle">Source → platform-reported interest; no unsupported inference added</div></div><button class="panel-link" data-view="evidence">Inspect evidence →</button></div><div class="flow-map">${state.interests.slice(0, 7).map((item) => `<div class="flow-node"><small>${escapeHtml(item.platform.toUpperCase())}</small><strong>${escapeHtml(item.original_label)}</strong></div><div class="flow-arrow">→</div>`).join("") || `<span class="muted-cell">Import records to render the relationship view.</span>`}</div></section>`;
}

function driftView() {
  const options = state.imports.map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.snapshot_label)}${item.is_demo ? " · DEMO" : ""}</option>`).join("");
  const result = state.drift;
  return `${pageHead()}<section class="panel"><div class="panel-header"><div><div class="panel-title">Snapshot comparison</div><div class="panel-subtitle">Choose two actual local imports. Later coverage controls whether absence is removal or uncertainty.</div></div></div><div class="filters"><select class="select" id="drift-before"><option value="">Before snapshot</option>${options}</select><select class="select" id="drift-after"><option value="">After snapshot</option>${options}</select><button class="btn btn-primary" data-action="run-drift">Run comparison</button></div>${result ? driftResult(result) : emptyState("No comparison selected", "Import two snapshots from the same or different platforms, then run the original Profile Drift algorithm.")}</section>`;
}

function driftResult(result) {
  const card = (title, count, color, records) => `<div class="metric-card"><div class="metric-label">${title}</div><div class="metric-value">${count}</div><div class="metric-foot">${records.slice(0, 2).map((item) => escapeHtml(item.original_label || item.after?.original_label || "record")).join(" · ") || "No records"}</div></div>`;
  return `<div class="metric-grid">${card("Newly reported", result.added.length, "blue", result.added)}${card("Retained", result.retained.length, "green", result.retained)}${card("Removed · supported", result.removed.length, "violet", result.removed)}${card("Uncertain absence", result.uncertain_absence.length, "orange", result.uncertain_absence)}</div><div class="section-kicker">Interpretation</div><div class="info-row"><span>${escapeHtml(result.interpretation)}</span><span>${escapeHtml(result.algorithm_version)}</span></div>${result.changed_classifications.length ? `<div class="section-kicker">Changed classifications</div>${result.changed_classifications.map((item) => `<div class="info-row"><span>${escapeHtml(item.before.original_label)}</span><span>${escapeHtml(label(item.before.category))} → ${escapeHtml(label(item.after.category))}</span></div>`).join("")}` : ""}`;
}

function comparisonView() {
  const comparison = state.comparison;
  return `${pageHead()}<section class="panel"><div class="panel-header"><div><div class="panel-title">Canonical reconciliation</div><div class="panel-subtitle">Similarity below the threshold remains unmatched.</div></div><button class="btn" data-action="load-comparison">Refresh comparison</button></div>${comparison ? `<div class="metric-grid">${metric("Compared records", comparison.compared_records, "All imported platforms")}${metric("Supported matches", comparison.matches.length, "Exact or similar")}${metric("Platform-specific", comparison.platform_specific.length, "No forced match")}${metric("Algorithm", "0.1", "Reproducible rules")}</div><div class="table-wrap"><table><thead><tr><th>Google / left</th><th>Meta / right</th><th>Match</th><th>Certainty</th></tr></thead><tbody>${comparison.matches.map((item) => `<tr><td><strong>${escapeHtml(item.left_label)}</strong></td><td>${escapeHtml(item.right_label)}</td><td>${pill(item.match_type, item.match_type === "EXACT_CANONICAL" ? "green" : "orange")}</td><td>${escapeHtml(item.certainty)}</td></tr>`).join("") || `<tr><td colspan="4">No cross-platform match is supported by current evidence.</td></tr>`}</tbody></table></div>` : emptyState("No comparison loaded", "Import Google and Meta records, then refresh to see supported and uncertain relationships.")}</section>`;
}

function misprofilingView() {
  return `${pageHead()}<section class="panel"><div class="panel-header"><div><div class="panel-title">Review imported interests</div><div class="panel-subtitle">Your classification is user-declared evidence, not a platform fact.</div></div></div>${state.interests.length ? `<div class="table-wrap"><table><thead><tr><th>Interest</th><th>Platform evidence</th><th>Your review</th><th>Outcome</th></tr></thead><tbody>${state.interests.map((item) => `<tr><td><strong>${escapeHtml(item.original_label)}</strong><small class="muted-cell">${escapeHtml(item.source_file)}</small></td><td>${pill(item.evidence_type, "blue")}</td><td><div class="radio-list">${["ACCURATE", "INACCURATE", "OUTDATED", "UNSURE"].map((choice) => `<label><input type="radio" name="pref-${item.id}" data-action="preference" data-id="${item.id}" value="${choice}" ${item.preference === choice ? "checked" : ""}/> ${label(choice)}</label>`).join("")}</div></td><td>${pill(item.preference_outcome || "UNVERIFIED", item.preference_outcome === "PREFERENCE_DISCREPANCY" ? "red" : item.preference_outcome === "PREFERENCE_MATCH" ? "green" : "")}</td></tr>`).join("")}</tbody></table></div>` : emptyState("Nothing to review", "Import a supported export first. User feedback will be stored separately from source records.")}</section>`;
}

function evidenceView() {
  const selected = state.selectedEvidence;
  return `${pageHead()}<section class="content-grid"><section class="panel"><div class="panel-header"><div><div class="panel-title">Evidence index</div><div class="panel-subtitle">Select a record to inspect the full provenance trail.</div></div></div>${state.interests.length ? `<div class="info-list">${state.interests.map((item) => `<button class="info-row" data-action="evidence" data-id="${item.id}" style="background:none;border:0;text-align:left;cursor:pointer"><span><strong>${escapeHtml(item.original_label)}</strong><small class="muted-cell">${escapeHtml(item.platform)} · ${escapeHtml(item.source_file)}</small></span><span>${pill(item.evidence_type, "green")}</span></button>`).join("")}</div>` : emptyState("No evidence records", "Every finding will be linked to a platform, file, record path, and algorithm version after import.")}</section><section class="panel">${selected ? `<div class="panel-header"><div><div class="panel-title">Provenance detail</div><div class="panel-subtitle">${escapeHtml(selected.provenance?.conclusion || "")}</div></div>${selected.provenance?.demo_record ? pill("DEMO DATA", "orange") : ""}</div><div class="info-list"><div class="info-row"><span>Source platform</span><span>${escapeHtml(selected.provenance.source_platform)}</span></div><div class="info-row"><span>Source filename</span><span>${escapeHtml(selected.provenance.source_filename)}</span></div><div class="info-row"><span>Record path</span><span>${escapeHtml(selected.provenance.source_record_path)}</span></div><div class="info-row"><span>Evidence category</span><span>${escapeHtml(selected.provenance.evidence_category)}</span></div><div class="info-row"><span>Detection method</span><span>${escapeHtml(selected.provenance.detection_method)}</span></div><div class="info-row"><span>Uncertainty</span><span>${Math.round((selected.provenance.uncertainty || 0) * 100)}%</span></div></div><div class="section-kicker">Original record</div><pre class="code-box">${escapeHtml(JSON.stringify(selected.provenance.source_record, null, 2))}</pre>` : emptyState("Choose a finding", "SOVRIVA makes the underlying source record inspectable before you draw a conclusion.")}</section></section>`;
}

function actionsView() {
  const options = state.interests.map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.original_label)} · ${escapeHtml(item.platform)}</option>`).join("");
  const imports = state.imports.map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.snapshot_label)}</option>`).join("");
  return `${pageHead()}<section class="content-grid"><section class="panel"><div class="panel-header"><div><div class="panel-title">Record a privacy action</div><div class="panel-subtitle">Describe what you did on the official platform settings page.</div></div></div><div class="info-list"><label class="section-kicker">Interest evidence<select class="select" id="action-interest" style="display:block;width:100%;margin-top:8px"><option value="">Select interest</option>${options}</select></label><label class="section-kicker">Original snapshot<select class="select" id="action-before" style="display:block;width:100%;margin-top:8px"><option value="">Select snapshot</option>${imports}</select></label><label class="section-kicker">Action date<input class="input" id="action-date" type="date" style="display:block;width:100%;margin-top:8px" value="${new Date().toISOString().slice(0, 10)}"/></label><label class="section-kicker">Nature of action<input class="input" id="action-nature" placeholder="For example: removed an ad interest" style="display:block;width:100%;margin-top:8px"/></label><label class="section-kicker">Notes<textarea id="action-notes" placeholder="What official setting did you use?"></textarea></label><button class="btn btn-primary" data-action="create-action">Save action record</button></div></section><section class="panel"><div class="panel-header"><div><div class="panel-title">Verification history</div><div class="panel-subtitle">No internal deletion claims — only observable outcomes.</div></div></div>${state.actions.length ? `<div class="info-list">${state.actions.map((item) => `<div class="info-row"><span><strong>${escapeHtml(item.nature)}</strong><small class="muted-cell">${escapeHtml(item.action_date)} · ${escapeHtml(item.verification_status)}</small></span>${item.verification_status === "PENDING" ? `<button class="panel-link" data-action="verify-action" data-id="${item.id}">Verify with later import →</button>` : pill(item.verification_status, item.verification_status === "OBSERVED_CHANGE" ? "green" : item.verification_status === "NO_CHANGE_OBSERVED" ? "red" : "orange")}</div>`).join("")}</div>` : emptyState("No privacy actions recorded", "Save a manual action after reviewing an unwanted interest, then import a later export to verify it.")}</section></section>`;
}

function monitorView() {
  const observations = state.dashboard?.observations || [];
  const paired = state.pairing?.paired_extensions || [];
  return `${pageHead()}<section class="content-grid"><section class="panel"><div class="panel-header"><div><div class="panel-title">Extension connection</div><div class="panel-subtitle">Pairing is short-lived and tokens are revocable.</div></div><button class="btn" data-action="pairing-start">Generate pairing code</button></div>${state.pairing?.code ? `<div class="signal-card" style="min-height:0;margin-bottom:16px"><div class="panel-title">${escapeHtml(state.pairing.code)}</div><div class="panel-subtitle" style="color:#b9c7df;margin-top:8px">Enter this code in the SOVRIVA extension before ${escapeHtml(formatDate(state.pairing.expires_at))}.</div></div>` : ""}<div class="section-kicker">Active connections</div>${paired.length ? `<div class="info-list">${paired.map((item) => `<div class="info-row"><span><strong>${escapeHtml(item.extension_id)}</strong><small class="muted-cell">Last seen: ${escapeHtml(formatDate(item.last_seen_at))}</small></span><button class="panel-link" data-action="revoke-pairing" data-id="${escapeHtml(item.extension_id)}">Revoke</button></div>`).join("")}</div>` : `<p class="muted-cell">No paired extension. Install the unpacked extension and use the code above.</p>`}<div class="section-kicker">Permissions explained</div><p class="muted-cell">SOVRIVA uses declarativeNetRequest for enforcement and webRequest for permitted metadata observation. It does not read passwords, cookies, request bodies, form data, or page text.</p></section><section class="panel"><div class="panel-header"><div><div class="panel-title">Observed request stream</div><div class="panel-subtitle">${formatNumber(observations.length)} records loaded locally</div></div><button class="panel-link" data-action="refresh">Refresh →</button></div>${observations.length ? observationTable(observations) : emptyState("No activity received", "This panel stays empty until a paired extension sends real browser metadata.")}</section></section>`;
}

function protectionView(kind) {
  const settings = state.dashboard?.settings || { mode: "BALANCED", ad_blocking_enabled: true, tracker_blocking_enabled: true };
  const isAd = kind === "blocking";
  return `${pageHead()}<section class="panel"><div class="panel-header"><div><div class="panel-title">${isAd ? "Advertisement rules" : "Tracker rules"}</div><div class="panel-subtitle">${isAd ? "Known advertising domains and cosmetic selectors." : "Advertising, analytics, and social domains classified independently."}</div></div>${pill(isAd ? (settings.ad_blocking_enabled ? "ENABLED" : "DISABLED") : (settings.tracker_blocking_enabled ? "ENABLED" : "DISABLED"), isAd ? "blue" : "violet")}</div><div class="mode-grid">${[["INTEREST", "Interest", "Ad rules off by default; observation stays available."], ["BALANCED", "Balanced", "Selective rules that preserve common essential connections."], ["PRIVACY", "Privacy", "More aggressive supported rules and cosmetic filtering."]].map(([mode, name, text]) => `<button class="mode-card ${settings.mode === mode ? "selected" : ""}" data-action="mode" data-mode="${mode}"><strong><i class="mode-dot"></i>${name}</strong><p>${text}</p></button>`).join("")}</div><div class="section-kicker">Independent controls</div><div class="toggle-row"><div><strong>Advertisement blocking</strong><small>Updates the extension's DNR ad rules on the next sync.</small></div><button class="toggle ${settings.ad_blocking_enabled ? "on" : ""}" data-action="toggle" data-setting="ad_blocking_enabled" aria-label="Toggle advertisement blocking"></button></div><div class="toggle-row"><div><strong>Tracker protection</strong><small>Updates tracker DNR rules without changing ad rules.</small></div><button class="toggle ${settings.tracker_blocking_enabled ? "on" : ""}" data-action="toggle" data-setting="tracker_blocking_enabled" aria-label="Toggle tracker protection"></button></div><div class="section-kicker">Telemetry boundary</div><p class="muted-cell">${escapeHtml(state.dashboard?.data_notice || "SOVRIVA distinguishes observed requests from verified blocked requests.")}</p></section>`;
}

function footprintView() {
  const nodes = state.graph?.nodes || [];
  const display = nodes.slice(0, 10);
  return `${pageHead()}<section class="panel"><div class="panel-header"><div><div class="panel-title">Evidence relationship map</div><div class="panel-subtitle">Interactive records are based on actual imported interests and extension observations.</div></div><span class="pill pill-green">${display.length} nodes</span></div><div class="graph-canvas">${display.length ? display.map((node, index) => `<button class="graph-node ${escapeHtml(node.type)}" style="left:${12 + ((index * 19) % 78)}%;top:${25 + ((index * 37) % 55)}%" title="${escapeHtml(JSON.stringify(node.detail || {}))}"><small>${escapeHtml(label(node.type))}</small>${escapeHtml(node.label)}</button>`).join("") : emptyState("No footprint relationships", "Real nodes will appear after the extension observes requests or imports provide evidence.")}</div><div class="section-kicker">Flow semantics</div><div class="flow-map"><div class="flow-node"><small>WEBSITE</small><strong>Visited origin</strong></div><div class="flow-arrow">→</div><div class="flow-node"><small>OBSERVED</small><strong>Request metadata</strong></div><div class="flow-arrow">→</div><div class="flow-node"><small>POLICY</small><strong>Classification & decision</strong></div><div class="flow-arrow">→</div><div class="flow-node"><small>EVIDENCE</small><strong>Inspect source</strong></div></div></section>`;
}

function whyAdView() {
  return `${pageHead()}<section class="content-grid"><section class="panel"><div class="panel-header"><div><div class="panel-title">Local screenshot OCR</div><div class="panel-subtitle">The image remains in this browser tab.</div></div></div><input class="input" id="ad-screenshot" type="file" accept="image/*"/><div id="ocr-status" class="muted-cell" style="margin-top:14px">Select a screenshot to begin local analysis.</div><div id="ocr-output" style="margin-top:16px"></div></section><section class="panel"><div class="panel-title">Evidence comparison</div><div class="panel-subtitle">OCR text can be compared against actual stored records.</div><div class="section-kicker">Available evidence</div><div class="info-list"><div class="info-row"><span>Imported interests</span><span>${formatNumber(state.interests.length)}</span></div><div class="info-row"><span>Browser observations</span><span>${formatNumber(state.dashboard?.metrics?.observed_requests || 0)}</span></div><div class="info-row"><span>Claim boundary</span><span>Correlation only</span></div></div><p class="muted-cell" style="margin-top:20px">A visible brand or keyword does not prove why an advertisement was selected. SOVRIVA reports supporting and missing evidence separately.</p></section></section>`;
}

function experimentView() {
  return `${pageHead()}<section class="panel"><div class="panel-header"><div><div class="panel-title">Controlled local fixtures</div><div class="panel-subtitle">Use the included local lab server and a Chromium profile with the extension loaded.</div></div><span class="pill pill-orange">REAL REQUESTS REQUIRED</span></div><div class="flow-map"><div class="flow-node"><small>FIRST-PARTY</small><strong>http://127.0.0.1:8780</strong></div><div class="flow-arrow">→</div><div class="flow-node"><small>THIRD-PARTY</small><strong>http://127.0.0.1:8781</strong></div><div class="flow-arrow">→</div><div class="flow-node"><small>REPORT</small><strong>Requests received</strong></div></div><div class="section-kicker">Runbook</div><div class="info-list"><div class="info-row"><span>1. Start fixture</span><span><code>python scripts/lab_server.py</code></span></div><div class="info-row"><span>2. Load extension</span><span>Developer mode · Load unpacked</span></div><div class="info-row"><span>3. Switch mode</span><span>Interest → Balanced → Privacy</span></div><div class="info-row"><span>4. Inspect</span><span>Network + local report endpoint</span></div></div><p class="muted-cell" style="margin-top:18px">This fixture is never counted as personal activity. It is a separate test origin and should be reported as experiment data.</p></section>`;
}

function settingsView() {
  const settings = state.dashboard?.settings || { mode: "BALANCED", ad_blocking_enabled: true, tracker_blocking_enabled: true };
  return `${pageHead()}<section class="content-grid"><section class="panel"><div class="panel-title">Protection mode</div><div class="panel-subtitle">The paired extension consumes this policy from the loopback API.</div><div class="section-kicker">Current mode</div><div class="mode-grid" style="grid-template-columns:1fr">${[["INTEREST", "Interest", "Ad blocking is off by default."], ["BALANCED", "Balanced", "Selective protection."], ["PRIVACY", "Privacy", "Aggressive supported protection."]].map(([mode, name, text]) => `<button class="mode-card ${settings.mode === mode ? "selected" : ""}" data-action="mode" data-mode="${mode}"><strong><i class="mode-dot"></i>${name}</strong><p>${text}</p></button>`).join("")}</div></section><section class="panel"><div class="panel-title">Data controls</div><div class="panel-subtitle">Deletion is explicit and local.</div><div class="section-kicker">Workspace</div><button class="btn btn-danger" data-action="delete-all">Delete every local import, observation, action, and pairing</button><div class="section-kicker">Storage note</div><p class="muted-cell">SQLite is stored under the application data directory in packaged builds. This development run uses <code>data/sovriva.db</code>. The database is not encrypted by this prototype; sensitive secrets are stored hashed and the limitation is documented.</p><div class="section-kicker">Optional sync</div><p class="muted-cell">Google Data Portability remains disabled by default. Manual Takeout import works without credentials, billing, or cloud setup.</p></section></section>`;
}

function syncView() {
  return `${pageHead()}<section class="content-grid"><section class="panel"><div class="panel-title">Google Data Portability</div><div class="panel-subtitle">Optional and disabled by default.</div><div class="section-kicker">Current status</div><div class="info-list"><div class="info-row"><span>Connection</span><span>${pill("MANUAL_IMPORT_REQUIRED", "orange")}</span></div><div class="info-row"><span>Last successful sync</span><span>Not available</span></div><div class="info-row"><span>Consent expiry</span><span>Not available</span></div></div><p class="muted-cell" style="margin-top:18px">Google Data Portability requires provider eligibility, OAuth consent, project verification, and configuration that may require a billing-enabled Cloud project. SOVRIVA never enables billing automatically.</p><button class="btn" data-action="refresh-sync">Refresh status</button></section><section class="panel"><div class="panel-title">Meta synchronization</div><div class="panel-subtitle">Official export workflow only.</div><div class="section-kicker">Current status</div><div class="info-row"><span>Connection</span><span>${pill("MANUAL_IMPORT_REQUIRED", "orange")}</span></div><p class="muted-cell" style="margin-top:18px">SOVRIVA does not scrape consumer accounts or request passwords. Upload a new official Facebook/Instagram Accounts Center archive when you want a new snapshot; duplicate imports are detected locally.</p><button class="btn btn-primary" data-action="import-any">Import updated archive</button></section></section>`;
}

function render() {
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === state.view));
  const view = state.view;
  let html = view === "overview" ? overviewView() : view === "dna" ? dnaView() : view === "drift" ? driftView() : view === "comparison" ? comparisonView() : view === "misprofiling" ? misprofilingView() : view === "evidence" ? evidenceView() : view === "actions" ? actionsView() : view === "sync" ? syncView() : view === "monitor" ? monitorView() : view === "blocking" || view === "tracking" ? protectionView(view) : view === "footprint" ? footprintView() : view === "why-ad" ? whyAdView() : view === "experiment" ? experimentView() : settingsView();
  document.querySelector("#app-content").innerHTML = html;
  bindViewControls();
}

async function importFile(file, platform = null, isDemo = false) {
  if (!file) return;
  const dropzone = document.querySelector("#import-dropzone");
  dropzone?.classList.add("is-loading");
  const button = dropzone?.querySelector("button");
  if (button) { button.disabled = true; button.textContent = "Validating locally…"; }
  const reader = new FileReader();
  reader.onload = async () => {
    try {
      const base64 = String(reader.result).split(",")[1] || "";
      await api("/api/import", { method: "POST", body: JSON.stringify({ filename: file.name, platform, is_demo: isDemo, content_base64: base64 }) });
      toast(`${file.name} imported locally`); await refresh();
    } catch (error) { toast(error.message, true); }
    finally { dropzone?.classList.remove("is-loading"); if (button) { button.disabled = false; button.textContent = "Choose ZIP archive"; } }
  };
  reader.readAsDataURL(file);
}

function triggerFilePicker() {
  const input = document.createElement("input"); input.type = "file"; input.accept = ".zip,application/zip";
  input.onchange = () => importFile(input.files[0]); input.click();
}

async function loadComparison() { try { state.comparison = await api("/api/comparison"); render(); } catch (error) { toast(error.message, true); } }

async function runDrift() {
  const before = document.querySelector("#drift-before")?.value; const after = document.querySelector("#drift-after")?.value;
  if (!before || !after || before === after) return toast("Choose two different snapshots", true);
  try { state.drift = await api(`/api/drift?before=${encodeURIComponent(before)}&after=${encodeURIComponent(after)}`); render(); } catch (error) { toast(error.message, true); }
}

async function runOcr(file) {
  const status = document.querySelector("#ocr-status"); const output = document.querySelector("#ocr-output");
  if (!file) return;
  status.textContent = "Loading the local OCR worker… no image data is sent to SOVRIVA.";
  try {
    if (!window.Tesseract) {
      await new Promise((resolve, reject) => { const script = document.createElement("script"); script.src = "https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js"; script.onload = resolve; script.onerror = () => reject(new Error("Tesseract.js could not be loaded. Offline OCR requires the package to be bundled.")); document.head.appendChild(script); });
    }
    const worker = await window.Tesseract.createWorker("eng");
    const result = await worker.recognize(file);
    await worker.terminate();
    const text = result.data.text.trim();
    const tokens = new Set(text.toLowerCase().match(/[a-z0-9]+/g) || []);
    const related = state.interests.filter((item) => (item.original_label.toLowerCase().match(/[a-z0-9]+/g) || []).some((token) => tokens.has(token)));
    status.textContent = "OCR completed locally. Screenshot bytes were not uploaded.";
    output.innerHTML = `<div class="section-kicker">Extracted text</div><pre class="code-box">${escapeHtml(text || "No readable text detected")}</pre><div class="section-kicker">Related stored evidence</div>${related.length ? interestTable(related) : `<p class="muted-cell">No matching imported label. This is insufficient evidence of ad causation.</p>`}`;
  } catch (error) { status.textContent = error.message; toast(error.message, true); }
}

async function bindAction(action, element) {
  if (action === "refresh") return refresh();
  if (action === "download-report") { window.location.assign("/api/reports/profile.md"); return; }
  if (action === "import-any") return triggerFilePicker();
  if (action === "seed-demo") { try { await api("/api/demo/seed", { method: "POST" }); toast("Isolated demonstration data is ready"); await refresh(); } catch (error) { toast(error.message, true); } return; }
  if (action === "load-comparison") return loadComparison();
  if (action === "refresh-sync") { try { await api("/api/sync/status"); toast("Sync status checked: manual import remains required"); } catch (error) { toast(error.message, true); } return; }
  if (action === "run-drift") return runDrift();
  if (action === "evidence") { try { state.selectedEvidence = await api(`/api/provenance/${encodeURIComponent(element.dataset.id)}`); render(); } catch (error) { toast(error.message, true); } return; }
  if (action === "preference") { try { await api(`/api/interests/${element.dataset.id}/preference`, { method: "PATCH", body: JSON.stringify({ preference: element.value }) }); toast("Your review was saved separately"); await refresh(); } catch (error) { toast(error.message, true); } return; }
  if (action === "mode") {
    const mode = element.dataset.mode;
    try {
      await api("/api/settings", { method: "PATCH", body: JSON.stringify({ mode }) });
      state.dashboard = { ...state.dashboard, settings: { ...state.dashboard.settings, mode } };
      render();
      toast(`Mode set to ${label(mode)}; extension will sync in the background`);
    } catch (error) { toast(error.message, true); }
    return;
  }
  if (action === "toggle") {
    const setting = element.dataset.setting;
    const current = Boolean(state.dashboard?.settings?.[setting]);
    try {
      await api("/api/settings", { method: "PATCH", body: JSON.stringify({ mode: state.dashboard.settings.mode, [setting]: !current }) });
      state.dashboard = { ...state.dashboard, settings: { ...state.dashboard.settings, [setting]: !current } };
      render();
      toast(`${label(setting)} ${!current ? "enabled" : "disabled"}`);
    } catch (error) { toast(error.message, true); }
    return;
  }
  if (action === "pairing-start") { try { state.pairing = { ...(state.pairing || {}), ...(await api("/api/pairing/start", { method: "POST" })) }; toast("Pairing code generated"); render(); } catch (error) { toast(error.message, true); } return; }
  if (action === "revoke-pairing") { try { await api(`/api/pairing/revoke/${encodeURIComponent(element.dataset.id)}`, { method: "POST" }); toast("Extension token revoked"); state.pairing = await api("/api/pairing/status"); render(); } catch (error) { toast(error.message, true); } return; }
  if (action === "delete-all") { if (!window.confirm("Delete all local imports, observations, actions, and pairing tokens? This cannot be undone.")) return; try { await api("/api/data", { method: "DELETE" }); toast("All local data and pairings deleted"); await refresh(); } catch (error) { toast(error.message, true); } return; }
  if (action === "create-action") { const body = { interest_id: document.querySelector("#action-interest")?.value, before_import_id: document.querySelector("#action-before")?.value, action_date: document.querySelector("#action-date")?.value, nature: document.querySelector("#action-nature")?.value, notes: document.querySelector("#action-notes")?.value || "" }; if (!body.interest_id || !body.before_import_id || !body.nature) return toast("Complete the action fields first", true); try { await api("/api/privacy-actions", { method: "POST", body: JSON.stringify(body) }); toast("Privacy action recorded"); await refresh(); } catch (error) { toast(error.message, true); } return; }
  if (action === "verify-action") { const after = state.imports.find((item) => item.id !== state.actions.find((actionItem) => actionItem.id === element.dataset.id)?.before_import_id); if (!after) return toast("Import a later snapshot first", true); try { await api(`/api/privacy-actions/${element.dataset.id}/verify/${after.id}`, { method: "POST" }); toast("Action verified against the selected later import"); await refresh(); } catch (error) { toast(error.message, true); } }
}

function bindViewControls() {
  document.querySelectorAll("[data-view]").forEach((element) => element.addEventListener("click", () => { state.view = element.dataset.view; if (state.view === "comparison") loadComparison(); render(); }));
  document.querySelectorAll("[data-action]").forEach((element) => element.addEventListener("click", () => bindAction(element.dataset.action, element)));
  document.querySelector("#interest-search")?.addEventListener("input", filterDna);
  document.querySelector("#interest-platform")?.addEventListener("change", filterDna);
  document.querySelector("#interest-category")?.addEventListener("change", filterDna);
  document.querySelector("#ad-screenshot")?.addEventListener("change", (event) => runOcr(event.target.files[0]));
  const dropzone = document.querySelector("#import-dropzone");
  if (dropzone) {
    dropzone.addEventListener("dragover", (event) => { event.preventDefault(); dropzone.classList.add("is-dragging"); });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("is-dragging"));
    dropzone.addEventListener("drop", (event) => { event.preventDefault(); dropzone.classList.remove("is-dragging"); importFile(event.dataTransfer.files[0]); });
    dropzone.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); triggerFilePicker(); } });
  }
}

function setPresentationMode(enabled) {
  document.body.classList.toggle("presentation-mode", enabled);
  const button = document.querySelector("#present-button");
  if (button) button.textContent = enabled ? "× Exit presentation" : "▶ Present";
  if (enabled && document.documentElement.requestFullscreen && !document.fullscreenElement) document.documentElement.requestFullscreen().catch(() => {});
  if (!enabled && document.fullscreenElement && document.exitFullscreen) document.exitFullscreen().catch(() => {});
}

function filterDna() {
  const search = (document.querySelector("#interest-search")?.value || "").toLowerCase(); const platform = document.querySelector("#interest-platform")?.value; const category = document.querySelector("#interest-category")?.value;
  const results = state.interests.filter((item) => (!search || `${item.original_label} ${item.normalized_label}`.toLowerCase().includes(search)) && (!platform || item.platform === platform) && (!category || item.category === category));
  document.querySelector("#dna-table").innerHTML = interestTable(results);
}

document.addEventListener("DOMContentLoaded", async () => {
  document.querySelector("#refresh-button").addEventListener("click", refresh);
  document.querySelector("#present-button").addEventListener("click", () => setPresentationMode(!document.body.classList.contains("presentation-mode")));
  document.addEventListener("keydown", (event) => { if (event.key.toLowerCase() === "p" && !/input|textarea|select/i.test(event.target.tagName)) setPresentationMode(!document.body.classList.contains("presentation-mode")); if (event.key === "Escape") setPresentationMode(false); });
  document.addEventListener("fullscreenchange", () => { if (!document.fullscreenElement) setPresentationMode(false); });
  await refresh();
});
