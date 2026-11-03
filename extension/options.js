document.title = "SOVRIVA Extension Settings";
const defaults = { allowlist: [], custom_block_domains: [] };
const lines = (value) => value.split(/\r?\n/).map((item) => item.trim().toLowerCase()).filter(Boolean);

async function load() {
  const state = await chrome.storage.local.get(defaults);
  document.querySelector("#allowlist").value = (state.allowlist || []).join("\n");
  document.querySelector("#custom-block").value = (state.custom_block_domains || []).join("\n");
}

document.querySelector("#save").addEventListener("click", async () => {
  await chrome.storage.local.set({ allowlist: lines(document.querySelector("#allowlist").value), custom_block_domains: lines(document.querySelector("#custom-block").value) });
  document.querySelector("#status").textContent = "Saved locally";
  window.setTimeout(() => { document.querySelector("#status").textContent = ""; }, 2500);
});
load();
