# Database schema

SQLite schema version `1` is created by `sovriva/db.py`.

- `imports`: SHA-256, platform, coverage, source filename, parser version, demo marker.
- `interests`: canonical label/category plus original record, source file/path, evidence type, confidence, and user preference.
- `activity_records`: imported browsing/search/video records with source provenance.
- `observations`: normalized extension request metadata and policy decision.
- `privacy_actions`: user-recorded actions and later evidence-limited verification.
- `user_feedback`: separate preference classifications.
- `pairing_codes` / `extension_tokens`: hashed pairing secrets and revocation state.
- `settings`: mode and independent protection switches.

Foreign keys cascade imported evidence deletion. Import insertion is transactional and duplicate source hashes are rejected.
