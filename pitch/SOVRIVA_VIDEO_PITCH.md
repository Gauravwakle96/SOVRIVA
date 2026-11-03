# SOVRIVA 2–3 Minute Video Pitch

## Production direction

This is a hybrid pitch: short PPT-style visual cards establish the story, while the working SOVRIVA dashboard and Chrome/Edge extension provide proof. The product footage should occupy most of the video. Do not show private user data; use the isolated demo records.

- Target duration: 2:40–2:55
- Narration: the founder's own recorded voice
- Delivery: calm, confident, conversational, and slightly energetic
- Editing: clean cuts, short zooms, readable captions, no distracting effects
- Audio: voice clearly above music; music should be optional and very quiet
- Claims: show only behavior that is visible in the current prototype

## Timeline and visuals

| Time | Narration purpose | Visual direction |
|---|---|---|
| 00:00–00:18 | Hook and problem | PPT-style opening card: fragmented export files, then cut to the live dashboard. |
| 00:18–00:35 | Users and solution | Solution card with the SOVRIVA tagline, followed by the local dashboard at `127.0.0.1:8765`. |
| 00:35–01:12 | Import and intelligence | Record a supported demo import, then show Profile Drift, cross-platform comparison, and an evidence detail. |
| 01:12–01:32 | Privacy-action verification | Show an action record and a later-snapshot outcome. Keep the outcome honest and evidence-limited. |
| 01:32–01:58 | Browser protection | Show extension pairing, the popup, mode changes, independent switches, and an observation arriving in the dashboard. |
| 01:58–02:18 | Technology and responsible AI | PPT-style technology card, then a brief local API/dashboard view. Do not show code for more than two seconds. |
| 02:18–02:38 | Market, business, and impact | PPT-style card with target users, proposed model, and future scope. Use three or four short phrases only. |
| 02:38–02:55 | Closing | Dashboard and extension side-by-side, followed by the SOVRIVA logo and tagline. |

## Final narration script

Every search, video, and website visit can contribute to how digital platforms understand us.

But when people download their account data, it is fragmented, difficult to compare, and difficult to interpret.

When a record disappears from a later export, that does not automatically mean it was deleted. People need evidence, not assumptions.

Meet SOVRIVA: Your Digital Identity. Your Control.

SOVRIVA is a local-first privacy intelligence platform for individuals, educators, and researchers.

Users import supported Google or Meta exports, and the analysis stays on their computer. The local engine validates the archive, detects duplicate imports, and preserves the original evidence.

Profile Drift compares real snapshots and separates new, retained, removed with supporting evidence, and uncertain records. Cross-platform comparison avoids weak matches, and every finding can be traced to its platform, source file, and record path.

Users can record a privacy action, such as changing an advertising preference, and compare it with a later export. SOVRIVA reports an observed change, no change observed, or not verifiable.

It does not claim to see a platform’s complete internal profile, and it never treats incomplete data as proof of deletion.

The companion Chrome and Edge extension adds a live protection layer. It observes only normalized request metadata and applies supported advertising and tracker rules through Manifest V3.

Advertising blocking and tracker protection remain independent across Interest, Balanced, and Privacy modes. Passwords, cookies, request bodies, and page text never enter SOVRIVA.

The system is built with FastAPI, SQLite, and a browser extension. Its current classifier is deterministic and explainable, so its results are reproducible.

Our next step is to evaluate an optional local language model on labelled data using precision, recall, and macro-F1, while keeping human review when confidence is low.

AI should clarify evidence, not invent it.

SOVRIVA can support individuals, universities, educators, researchers, and future institutional privacy-audit programs.

The proposed model combines a free local core with paid advanced reporting and institutional deployment, without selling personal data.

Our working prototype already includes imports, provenance, Profile Drift, privacy-action verification, browser protection, and secure pairing.

SOVRIVA does not claim to reveal everything a platform knows. It helps people understand the evidence they can access, compare what changes, and control what happens next.

SOVRIVA. Your Digital Identity. Your Control.

## On-screen text cards

Use these as brief visual cards, not full slide narration:

1. **THE PROBLEM** — Fragmented data. Unclear changes. No reliable evidence.
2. **THE SOLUTION** — Local-first privacy intelligence.
3. **THE DIFFERENCE** — Evidence preserved. Uncertainty visible. Weak matches rejected.
4. **THE TECHNOLOGY** — FastAPI · SQLite · MV3 · Explainable local classification.
5. **THE IMPACT** — Understand more. Verify change. Control what happens next.

## Accuracy guardrails

- Say “supported exports,” not “all Google or Meta data.”
- Say “removed with supporting evidence” or “uncertain,” not “deleted” without coverage.
- Say “configured rules” or “experimentally verified blocking” where appropriate.
- Say “proposed business model,” because paid deployment is future scope.
- Do not display pairing tokens, private records, or personal browser history.
