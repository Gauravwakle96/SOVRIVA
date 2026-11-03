# Open-source license and security audit

Repositories were checked through their GitHub metadata and README at 2026-11-03. No source files were copied into SOVRIVA; selected items are architectural references unless noted.

| Repository | Declared license | Use in SOVRIVA | Decision |
|---|---|---|---|
| Blocky | MIT | MV3/DNR/settings concepts | Reference; no filter-list files copied |
| google_takeout_parser | MIT | ZIP/JSON/activity parsing concepts | Independent adapter; no package dependency |
| Interests-network-graph | MIT | Meta schema/graph concepts | Reference; no Gemini dependency |
| WXT | MIT | MV3 framework patterns | Not adopted; extension is dependency-free |
| FP Radar | MIT | observer/fingerprinting boundary | Reference only; no fingerprint spoofing |
| xyflow/xyflow | MIT | graph UI concepts | Not bundled in this dependency-light prototype |
| Tesseract.js | Apache-2.0 | local OCR browser API | Development CDN path; bundle and pin for offline release |
| Chroma-Ad-Blocker | GPL-3.0 | MV3 architecture reference | No source, scriptlets, or rules copied |

Maintenance, dependency advisories, bundled filter-list licensing, and release pinning must be rechecked before a public release. SOVRIVA currently uses a small hand-reviewed domain corpus rather than redistributing EasyList/uBlock/Chroma datasets.
