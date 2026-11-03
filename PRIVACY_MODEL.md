# SOVRIVA privacy model

SOVRIVA is local-first: imports, evidence, observations, settings, and reports remain in local SQLite. The extension sends only normalized browser metadata to the paired loopback API. It does not send complete URLs, cookies, passwords, request bodies, form contents, or page text.

Pairing is explicit, a code expires after five minutes, and the resulting token is revocable. The prototype database is not encrypted at rest; this is disclosed and must be addressed with Windows DPAPI or an equivalent key strategy before a production privacy claim.
