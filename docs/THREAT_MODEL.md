# Threat model

| Threat | Impact | Mitigation | Verification |
|---|---|---|---|
| Malicious ZIP / traversal | Arbitrary file access | In-memory archive validation and normalized member paths | `tests/test_security.py` |
| Decompression bomb | Resource exhaustion | compressed, member, total, and file-count limits | archive limit tests |
| Malformed JSON | Import failure | per-file parse isolation and transaction rollback | importer tests |
| Malicious HTML | script execution | HTML unsupported and never rendered | import coverage test |
| Unauthorized loopback request | Observation injection | pairing token for extension ingestion; loopback bind | pairing tests |
| Token theft | Observation injection | hashed revocable token, short-lived pairing code | revoke test |
| Extension message abuse | Policy changes | messages are limited to local policy operations | extension review |
| Database exposure | Sensitive local data | minimal storage, deletion, explicit unencrypted limitation | deletion test |
| CSRF | Local state changes | loopback-only desktop context, no cookie auth, JSON endpoints | manual review |
| Dependency/supply chain | Code execution | minimal dependencies and license audit | release checklist |
| Unauthorized telemetry | Privacy breach | no analytics or remote event endpoint | source review |

This is not a claim of complete security. Installer signing, DPAPI secret protection, and a full dependency scanner remain release work.
