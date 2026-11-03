const cosmeticState = { enabled: false };

function applyCosmeticRules(enabled) {
  let style = document.getElementById("sovriva-cosmetic-style");
  if (!enabled) { style?.remove(); return; }
  if (!style) {
    style = document.createElement("style"); style.id = "sovriva-cosmetic-style";
    style.textContent = ".sovriva-ad-slot,[data-ad-slot],[aria-label=\"Advertisement\"]{display:none!important} iframe[src*='doubleclick.net']{display:none!important}";
    (document.head || document.documentElement).appendChild(style);
  }
}

chrome.storage.local.get({ cosmetic_filtering: false }).then((settings) => { cosmeticState.enabled = settings.cosmetic_filtering; applyCosmeticRules(settings.cosmetic_filtering); });
chrome.storage.onChanged.addListener((changes) => { if (changes.cosmetic_filtering) applyCosmeticRules(changes.cosmetic_filtering.newValue); });
