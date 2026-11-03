# Local API

Base URL: `http://127.0.0.1:8765`

Important endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | readiness check |
| `POST /api/import` | base64 ZIP import with validation |
| `GET /api/dashboard` | local metrics and recent records |
| `GET /api/interests` | source-linked profile records |
| `GET /api/drift?before=&after=` | Profile Drift result |
| `GET /api/comparison` | cross-platform reconciliation |
| `GET /api/provenance/{id}` | inspect evidence |
| `POST /api/observations` | paired extension batch ingestion |
| `PATCH /api/settings` | mode and independent switches |
| `POST /api/pairing/start` | five-minute code |
| `POST /api/pairing/claim` | one-time extension token |
| `GET /api/reports/profile.md` | downloadable local Markdown report |
| `DELETE /api/data` | complete local record deletion |

Extension-only endpoints require `X-SOVRIVA-TOKEN`. The dashboard is intentionally loopback-local and has no user account system.
