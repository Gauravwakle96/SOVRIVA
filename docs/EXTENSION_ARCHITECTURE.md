# Extension architecture

`extension/background.js` owns policy and synchronization. `webRequest.onBeforeRequest` records normalized domains, request type, initiator, third-party state, classification, mode, and an `OBSERVED` decision. It does not inspect bodies, cookies, forms, or query parameters.

`declarativeNetRequest.updateDynamicRules` enforces separate ad and tracker domain corpora. Interest, Balanced, and Privacy mode change which rules are active. `content.js` only hides explicitly marked ad slots, advertisement-labeled elements, and DoubleClick iframes when Privacy mode enables cosmetic filtering.

`popup.html` provides pairing, mode switching, independent controls, and sync status. The extension is compatible with Chrome/Edge MV3 but requires Developer Mode for the unpacked build.
