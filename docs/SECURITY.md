# Security model summary

- The API binds to `127.0.0.1` through `run.py`.
- ZIP members are checked for traversal, absolute paths, unsafe executable suffixes, CRC errors, file count, member size, and expanded-size limits.
- SQL uses parameterized statements; import writes occur in transactions.
- Pairing codes expire after five minutes, are one-time, and are stored as hashes. Extension tokens are stored as hashes and can be revoked.
- Imported HTML is never executed. Unsupported formats are reported instead.
- The extension sends domains and request metadata only and never sends the full URL.
- SQLite is not encrypted at rest in this prototype. This limitation is explicit; packaged production builds should add a Windows DPAPI-protected key strategy before claiming encrypted sensitive storage.

See `THREAT_MODEL.md` for attack scenarios and verification coverage.
