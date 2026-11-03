"""Local-only FastAPI service for SOVRIVA.

The API binds to loopback by default, accepts only JSON/base64 archive uploads,
and stores source-linked records in SQLite. It intentionally has no account
system, telemetry, or remote inference dependency.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import sqlite3
import sys
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from .db import connect, init_db, json_text, json_value, new_id, rows_to_dict, transaction, utc_now
from .imports import ArchiveValidationError, ImportParseError, ParsedImport, parse_archive
from .intelligence import (
    classify_domain,
    compare_platforms,
    drift_compare,
    evidence_graph,
    normalize_interest,
    preference_outcome,
)


ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
STATIC_DIR = ROOT / "frontend"

app = FastAPI(title="SOVRIVA Local API", version="0.1.0", docs_url="/api/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8765", "http://localhost:8765", "chrome-extension://*"],
    allow_origin_regex=r"chrome-extension://[a-z]{32}",
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-SOVRIVA-Client", "X-SOVRIVA-TOKEN", "X-Filename", "X-Platform"],
)


class ImportRequest(BaseModel):
    filename: str = Field(default="uploaded-export.zip", max_length=240)
    platform: str | None = Field(default=None, max_length=20)
    content_base64: str = Field(min_length=4)
    is_demo: bool = False


class PreferenceRequest(BaseModel):
    preference: str = Field(pattern="^(ACCURATE|INACCURATE|OUTDATED|UNSURE|UNREVIEWED)$")


class ModeRequest(BaseModel):
    mode: str = Field(pattern="^(INTEREST|BALANCED|PRIVACY)$")
    ad_blocking_enabled: bool | None = None
    tracker_blocking_enabled: bool | None = None


class Observation(BaseModel):
    observed_at: str | None = None
    tab_id: int | None = None
    initiator_domain: str | None = Field(default=None, max_length=253)
    destination_domain: str = Field(max_length=253)
    resource_type: str = Field(default="other", max_length=40)
    third_party: bool = False
    classification: str | None = None
    decision: str = Field(default="OBSERVED", max_length=40)
    mode: str = Field(default="BALANCED", pattern="^(INTEREST|BALANCED|PRIVACY)$")
    source: str = Field(default="extension", max_length=40)


class ObservationBatch(BaseModel):
    observations: list[Observation] = Field(max_length=500)


class PrivacyActionRequest(BaseModel):
    interest_id: str
    before_import_id: str
    action_date: str
    nature: str = Field(min_length=3, max_length=160)
    notes: str = Field(default="", max_length=2_000)


class PairingClaimRequest(BaseModel):
    code: str = Field(min_length=6, max_length=12)
    extension_id: str = Field(min_length=3, max_length=180)


def _setting(db: sqlite3.Connection, key: str, default: str) -> str:
    row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def _settings(db: sqlite3.Connection) -> dict[str, Any]:
    mode = _setting(db, "privacy_mode", "BALANCED")
    return {
        "mode": mode,
        "ad_blocking_enabled": _setting(db, "ad_blocking_enabled", "true") == "true",
        "tracker_blocking_enabled": _setting(db, "tracker_blocking_enabled", "true") == "true",
    }


def _hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _extension_token(request: Request) -> str | None:
    return request.headers.get("X-SOVRIVA-TOKEN")


def _require_extension_token(request: Request) -> dict[str, Any]:
    token = _extension_token(request)
    if not token or len(token) < 32:
        raise HTTPException(status_code=401, detail="Extension pairing is required")
    with transaction() as db:
        row = db.execute(
            "SELECT * FROM extension_tokens WHERE token_hash = ? AND revoked = 0",
            (_hash_secret(token),),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Extension token is invalid or revoked")
        db.execute("UPDATE extension_tokens SET last_seen_at = ? WHERE id = ?", (utc_now(), row["id"]))
    return dict(row)


def _serialize_import(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["unsupported_files"] = json_value(result.get("unsupported_files"), [])
    result["coverage"] = json_value(result.get("coverage"), {})
    result["is_demo"] = bool(result.get("is_demo", 0))
    return result


def _serialize_interest(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["source_record"] = json_value(result.get("source_record"), {})
    result["preference_outcome"] = preference_outcome(result["preference"], result["evidence_type"])
    return result


def _insert_parsed(parsed: ParsedImport, is_demo: bool = False) -> dict[str, Any]:
    imported_at = utc_now()
    import_id = new_id("imp")
    with transaction() as db:
        duplicate = db.execute(
            "SELECT id FROM imports WHERE source_sha256 = ?", (parsed.source_sha256,)
        ).fetchone()
        if duplicate:
            raise HTTPException(
                status_code=409,
                detail={"message": "This archive was already imported", "import_id": duplicate["id"]},
            )
        snapshot_label = f"{parsed.platform.title()} · {imported_at[:10]}"
        db.execute(
            """INSERT INTO imports(
                id, platform, filename, source_sha256, imported_at, status,
                snapshot_label, total_files, supported_files, unsupported_files,
                records_count, coverage, parser_version, is_demo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                import_id,
                parsed.platform,
                parsed.filename,
                parsed.source_sha256,
                imported_at,
                "DEMO" if is_demo else "IMPORTED",
                snapshot_label,
                parsed.total_files,
                parsed.supported_files,
                json_text(parsed.unsupported_files),
                parsed.records_count,
                json_text(parsed.coverage),
                "sovriva-importers-0.1",
                int(is_demo),
            ),
        )
        interest_count = 0
        for item in parsed.interests:
            normalized, category, confidence, explanation = normalize_interest(item.original_label)
            interest_id = new_id("int")
            cursor = db.execute(
                """INSERT OR IGNORE INTO interests(
                    id, import_id, platform, original_label, normalized_label, category,
                    source_file, source_record_path, source_record, observed_at, imported_at,
                    evidence_type, preference, classification_status, confidence, classifier_explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'UNREVIEWED', ?, ?, ?)""",
                (
                    interest_id,
                    import_id,
                    parsed.platform,
                    item.original_label,
                    normalized,
                    category,
                    item.source_file,
                    item.source_record_path,
                    json_text(item.source_record),
                    item.observed_at,
                    imported_at,
                    item.evidence_type,
                    "UNCERTAIN" if confidence < 0.6 else "CLASSIFIED",
                    confidence,
                    explanation,
                ),
            )
            interest_count += cursor.rowcount
        for item in parsed.activities:
            db.execute(
                """INSERT INTO activity_records(
                    id, import_id, platform, record_type, title, url, occurred_at,
                    source_file, source_record_path, source_record, evidence_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_id("act"),
                    import_id,
                    parsed.platform,
                    item.record_type,
                    item.title,
                    item.url,
                    item.occurred_at,
                    item.source_file,
                    item.source_record_path,
                    json_text(item.source_record),
                    item.evidence_type,
                    imported_at,
                ),
            )
        saved = db.execute("SELECT * FROM imports WHERE id = ?", (import_id,)).fetchone()
        result = _serialize_import(saved)
        result["interest_records_saved"] = interest_count
        result["activity_records_saved"] = len(parsed.activities)
        return result


def _parse_base64(value: str) -> bytes:
    # Reject oversized encoded input before allocating the decoded archive.
    if len(value) > (100 * 1024 * 1024 * 4 // 3) + 8192:
        raise HTTPException(status_code=413, detail="Encoded archive exceeds the 100 MB limit")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="content_base64 is invalid") from exc
    if not decoded:
        raise HTTPException(status_code=400, detail="Archive content is empty")
    return decoded


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, Any]:
    init_db()
    return {"status": "ok", "service": "sovriva-local", "version": "0.1.0", "database": "sqlite"}


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    init_db()
    with connect() as db:
        imports = rows_to_dict(db.execute("SELECT * FROM imports ORDER BY imported_at DESC").fetchall())
        for item in imports:
            item["unsupported_files"] = json_value(item["unsupported_files"], [])
            item["coverage"] = json_value(item["coverage"], {})
            item["is_demo"] = bool(item.get("is_demo", 0))
        interest_rows = db.execute("SELECT * FROM interests ORDER BY imported_at DESC").fetchall()
        observation_rows = db.execute(
            "SELECT * FROM observations ORDER BY observed_at DESC LIMIT 100"
        ).fetchall()
        category_rows = db.execute(
            "SELECT category, COUNT(*) AS count FROM interests GROUP BY category ORDER BY count DESC"
        ).fetchall()
        platform_rows = db.execute(
            "SELECT platform, COUNT(*) AS count FROM interests GROUP BY platform ORDER BY count DESC"
        ).fetchall()
        settings = _settings(db)
        metrics = {
            "imports": len(imports),
            "interests": len(interest_rows),
            "observed_requests": db.execute("SELECT COUNT(*) AS count FROM observations").fetchone()["count"],
            "classified_ads": db.execute(
                "SELECT COUNT(*) AS count FROM observations WHERE classification = 'ADVERTISING'"
            ).fetchone()["count"],
            "classified_trackers": db.execute(
                "SELECT COUNT(*) AS count FROM observations WHERE classification IN ('ADVERTISING', 'ANALYTICS', 'SOCIAL')"
            ).fetchone()["count"],
            "verified_blocked": db.execute(
                "SELECT COUNT(*) AS count FROM observations WHERE decision = 'VERIFIED_BLOCKED'"
            ).fetchone()["count"],
        }
        return {
            "metrics": metrics,
            "settings": settings,
            "imports": imports,
            "interests": [_serialize_interest(row) for row in interest_rows[:12]],
            "categories": rows_to_dict(category_rows),
            "platforms": rows_to_dict(platform_rows),
            "observations": rows_to_dict(observation_rows),
            "data_notice": "Metrics are derived from locally stored records; unavailable telemetry is not estimated.",
        }


@app.post("/api/import")
def import_archive(payload: ImportRequest) -> dict[str, Any]:
    raw = _parse_base64(payload.content_base64)
    try:
        parsed = parse_archive(raw, payload.filename, payload.platform)
        return {"import": _insert_parsed(parsed, payload.is_demo), "status": "imported"}
    except HTTPException:
        raise
    except (ArchiveValidationError, ImportParseError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/imports")
def list_imports() -> list[dict[str, Any]]:
    with connect() as db:
        return [_serialize_import(row) for row in db.execute("SELECT * FROM imports ORDER BY imported_at DESC")]


@app.delete("/api/imports/{import_id}")
def delete_import(import_id: str) -> dict[str, Any]:
    with transaction() as db:
        row = db.execute("SELECT id FROM imports WHERE id = ?", (import_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Import not found")
        db.execute("DELETE FROM imports WHERE id = ?", (import_id,))
    return {"status": "deleted", "import_id": import_id}


@app.delete("/api/data")
def delete_all_data() -> dict[str, Any]:
    with transaction() as db:
        for table in ("user_feedback", "privacy_actions", "activity_records", "interests", "imports", "observations", "extension_tokens", "pairing_codes"):
            db.execute(f"DELETE FROM {table}")
    return {"status": "deleted", "scope": "all local records and pairing tokens"}


@app.get("/api/interests")
def list_interests(
    platform: str | None = None,
    category: str | None = None,
    preference: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if platform:
        clauses.append("platform = ?")
        params.append(platform.lower())
    if category:
        clauses.append("category = ?")
        params.append(category.lower())
    if preference:
        clauses.append("preference = ?")
        params.append(preference.upper())
    if search:
        clauses.append("(original_label LIKE ? OR normalized_label LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect() as db:
        return [_serialize_interest(row) for row in db.execute(
            f"SELECT * FROM interests {where} ORDER BY imported_at DESC", params
        )]


@app.patch("/api/interests/{interest_id}/preference")
def update_preference(interest_id: str, payload: PreferenceRequest) -> dict[str, Any]:
    with transaction() as db:
        row = db.execute("SELECT id FROM interests WHERE id = ?", (interest_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Interest not found")
        db.execute("UPDATE interests SET preference = ? WHERE id = ?", (payload.preference, interest_id))
        db.execute(
            "INSERT OR REPLACE INTO user_feedback(interest_id, classification, updated_at) VALUES (?, ?, ?)",
            (interest_id, payload.preference, utc_now()),
        )
        updated = db.execute("SELECT * FROM interests WHERE id = ?", (interest_id,)).fetchone()
    return _serialize_interest(updated)


@app.get("/api/drift")
def profile_drift(before: str, after: str) -> dict[str, Any]:
    with connect() as db:
        before_import = db.execute("SELECT * FROM imports WHERE id = ?", (before,)).fetchone()
        after_import = db.execute("SELECT * FROM imports WHERE id = ?", (after,)).fetchone()
        if not before_import or not after_import:
            raise HTTPException(status_code=404, detail="Both snapshots are required")
        before_rows = rows_to_dict(db.execute("SELECT * FROM interests WHERE import_id = ?", (before,)).fetchall())
        after_rows = rows_to_dict(db.execute("SELECT * FROM interests WHERE import_id = ?", (after,)).fetchall())
        result = drift_compare(
            before_rows,
            after_rows,
            json_value(before_import["coverage"], {}),
            json_value(after_import["coverage"], {}),
        )
        result.update({"before_import": _serialize_import(before_import), "after_import": _serialize_import(after_import)})
        return result


@app.get("/api/comparison")
def cross_platform_comparison() -> dict[str, Any]:
    with connect() as db:
        rows = rows_to_dict(db.execute("SELECT * FROM interests ORDER BY imported_at DESC").fetchall())
    return compare_platforms(rows)


@app.get("/api/provenance/{interest_id}")
def provenance(interest_id: str) -> dict[str, Any]:
    with connect() as db:
        row = db.execute(
            """SELECT interests.*, imports.filename, imports.source_sha256, imports.snapshot_label,
                      imports.imported_at AS snapshot_imported_at, imports.is_demo
               FROM interests JOIN imports ON imports.id = interests.import_id
               WHERE interests.id = ?""",
            (interest_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Evidence record not found")
    result = _serialize_interest(row)
    result["provenance"] = {
        "conclusion": f"{row['original_label']} is reported under {row['platform']} export evidence.",
        "source_platform": row["platform"],
        "source_filename": row["filename"],
        "source_record_path": row["source_record_path"],
        "source_record": json_value(row["source_record"], {}),
        "timestamp": row["observed_at"] or row["snapshot_imported_at"],
        "evidence_category": row["evidence_type"],
        "detection_method": "Deterministic taxonomy normalization",
        "algorithm_version": "sovriva-importers-0.1 / taxonomy-0.1",
        "uncertainty": round(1 - row["confidence"], 3),
        "demo_record": bool(row["is_demo"]),
    }
    return result


@app.get("/api/graph")
def graph() -> dict[str, Any]:
    with connect() as db:
        interests = rows_to_dict(db.execute("SELECT * FROM interests ORDER BY imported_at DESC LIMIT 80").fetchall())
        observations = rows_to_dict(db.execute("SELECT * FROM observations ORDER BY observed_at DESC LIMIT 80").fetchall())
    return evidence_graph(interests, observations)


@app.post("/api/observations")
def add_observations(request: Request, payload: ObservationBatch) -> dict[str, Any]:
    token = _require_extension_token(request)
    saved = 0
    with transaction() as db:
        for item in payload.observations:
            domain = item.destination_domain.casefold().strip().strip(".")
            classification = item.classification or classify_domain(domain)
            db.execute(
                """INSERT INTO observations(
                    id, observed_at, tab_id, initiator_domain, destination_domain, resource_type,
                    third_party, classification, decision, mode, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_id("obs"),
                    item.observed_at or utc_now(),
                    item.tab_id,
                    item.initiator_domain,
                    domain,
                    item.resource_type,
                    int(item.third_party),
                    classification,
                    item.decision,
                    item.mode,
                    f"{item.source}:{token['extension_id']}",
                ),
            )
            saved += 1
    return {"saved": saved, "telemetry": "observed metadata only", "extension_id": token["extension_id"]}


@app.get("/api/observations")
def list_observations(limit: int = 100) -> list[dict[str, Any]]:
    safe_limit = min(max(limit, 1), 500)
    with connect() as db:
        return rows_to_dict(db.execute(
            "SELECT * FROM observations ORDER BY observed_at DESC LIMIT ?", (safe_limit,)
        ).fetchall())


@app.get("/api/settings")
def get_settings(request: Request) -> dict[str, Any]:
    # The dashboard is loopback-only; the extension uses the pairing token.
    if _extension_token(request):
        _require_extension_token(request)
    with connect() as db:
        return _settings(db)


@app.get("/api/sync/status")
def sync_status() -> dict[str, Any]:
    enabled = os.getenv("GOOGLE_DATA_PORTABILITY_ENABLED", "false").lower() == "true"
    return {
        "google": {
            "status": "AUTHORIZATION_REQUIRED" if enabled else "MANUAL_IMPORT_REQUIRED",
            "enabled": enabled,
            "last_successful_sync": None,
            "consent_expires_at": None,
            "note": "Automatic Google sync is disabled until credentials, eligibility, consent, and project approval are configured.",
        },
        "meta": {
            "status": "MANUAL_IMPORT_REQUIRED",
            "enabled": False,
            "last_successful_sync": None,
            "consent_expires_at": None,
            "note": "Consumer advertising-profile synchronization is not claimed; upload an official Accounts Center export.",
        },
    }


@app.patch("/api/settings")
def update_settings(payload: ModeRequest, request: Request) -> dict[str, Any]:
    if _extension_token(request):
        _require_extension_token(request)
    with transaction() as db:
        values = {"privacy_mode": payload.mode}
        if payload.ad_blocking_enabled is not None:
            values["ad_blocking_enabled"] = "true" if payload.ad_blocking_enabled else "false"
        if payload.tracker_blocking_enabled is not None:
            values["tracker_blocking_enabled"] = "true" if payload.tracker_blocking_enabled else "false"
        for key, value in values.items():
            db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", (key, value))
    return _settings(db)


@app.get("/api/extension/config")
def extension_config(request: Request) -> dict[str, Any]:
    _require_extension_token(request)
    with connect() as db:
        settings = _settings(db)
    settings["policy_version"] = "sovriva-policy-0.1"
    settings["host"] = "127.0.0.1"
    return settings


@app.post("/api/pairing/start")
def start_pairing() -> dict[str, Any]:
    # A code is only usable for five minutes and is stored hashed.
    code = f"{secrets.randbelow(1_000_000):06d}"
    created = utc_now()
    from datetime import datetime, timedelta, timezone

    expires = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    with transaction() as db:
        db.execute("UPDATE pairing_codes SET consumed = 1 WHERE consumed = 0")
        db.execute(
            "INSERT INTO pairing_codes(id, code_hash, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (new_id("pair"), _hash_secret(code), created, expires),
        )
    return {"code": code, "created_at": created, "expires_at": expires, "warning": "Keep this code private."}


@app.post("/api/pairing/claim")
def claim_pairing(payload: PairingClaimRequest) -> dict[str, Any]:
    from datetime import datetime, timezone

    with transaction() as db:
        row = db.execute(
            "SELECT * FROM pairing_codes WHERE consumed = 0 ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="Pairing code is invalid, expired, or already used")
        if row["attempts"] >= 5:
            db.execute("UPDATE pairing_codes SET consumed = 1 WHERE id = ?", (row["id"],))
            raise HTTPException(status_code=429, detail="Pairing code is locked after too many attempts")
        if not secrets.compare_digest(row["code_hash"], _hash_secret(payload.code.strip())):
            attempts = row["attempts"] + 1
            db.execute(
                "UPDATE pairing_codes SET attempts = ?, consumed = CASE WHEN ? >= 5 THEN 1 ELSE consumed END WHERE id = ?",
                (attempts, attempts, row["id"]),
            )
            raise HTTPException(status_code=400, detail="Pairing code is invalid, expired, or already used")
        try:
            expires = datetime.fromisoformat(row["expires_at"])
        except ValueError:
            expires = datetime.min.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Pairing code has expired")
        token = secrets.token_urlsafe(32)
        db.execute("UPDATE pairing_codes SET consumed = 1 WHERE id = ?", (row["id"],))
        token_id = new_id("ext")
        db.execute(
            "INSERT INTO extension_tokens(id, token_hash, extension_id, created_at, last_seen_at) VALUES (?, ?, ?, ?, ?)",
            (token_id, _hash_secret(token), payload.extension_id, utc_now(), utc_now()),
        )
    return {"token": token, "extension_id": payload.extension_id, "status": "paired"}


@app.get("/api/pairing/status")
def pairing_status() -> dict[str, Any]:
    with connect() as db:
        rows = db.execute(
            "SELECT extension_id, created_at, last_seen_at FROM extension_tokens WHERE revoked = 0 ORDER BY created_at DESC"
        ).fetchall()
    return {"paired_extensions": rows_to_dict(rows)}


@app.post("/api/pairing/revoke/{extension_id}")
def revoke_pairing(extension_id: str) -> dict[str, Any]:
    with transaction() as db:
        cursor = db.execute("UPDATE extension_tokens SET revoked = 1 WHERE extension_id = ?", (extension_id,))
    return {"revoked": cursor.rowcount, "extension_id": extension_id}


@app.post("/api/privacy-actions")
def create_privacy_action(payload: PrivacyActionRequest) -> dict[str, Any]:
    try:
        date.fromisoformat(payload.action_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="action_date must be YYYY-MM-DD") from exc
    with transaction() as db:
        interest = db.execute("SELECT id FROM interests WHERE id = ?", (payload.interest_id,)).fetchone()
        snapshot = db.execute("SELECT id FROM imports WHERE id = ?", (payload.before_import_id,)).fetchone()
        if not interest or not snapshot:
            raise HTTPException(status_code=404, detail="Interest and before snapshot are required")
        action_id = new_id("actn")
        db.execute(
            """INSERT INTO privacy_actions(id, interest_id, before_import_id, action_date, nature, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (action_id, payload.interest_id, payload.before_import_id, payload.action_date, payload.nature, payload.notes, utc_now()),
        )
        row = db.execute("SELECT * FROM privacy_actions WHERE id = ?", (action_id,)).fetchone()
    return dict(row)


@app.get("/api/privacy-actions")
def list_privacy_actions() -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute("SELECT * FROM privacy_actions ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]


@app.get("/api/reports/profile.md")
def profile_report(before: str | None = None, after: str | None = None) -> Response:
    """Download a Markdown report composed only from locally stored evidence."""
    with connect() as db:
        imports = [_serialize_import(row) for row in db.execute(
            "SELECT * FROM imports ORDER BY imported_at ASC"
        ).fetchall()]
        interests = [_serialize_interest(row) for row in db.execute(
            "SELECT * FROM interests ORDER BY platform, original_label"
        ).fetchall()]
        observations = rows_to_dict(db.execute(
            "SELECT * FROM observations ORDER BY observed_at DESC LIMIT 200"
        ).fetchall())
    lines = [
        "# SOVRIVA privacy intelligence report",
        "",
        f"Generated locally: {utc_now()}",
        "",
        "> This report contains locally stored records only. It does not claim access to a platform's complete internal profile.",
        "",
        "## Imports",
        "",
        "| Snapshot | Platform | Records | Coverage | Demo |",
        "|---|---|---:|---|---|",
    ]
    for item in imports:
        coverage = item.get("coverage", {})
        coverage_label = "explicit interest data" if coverage.get("explicit_interest_support") else "activity/incomplete profile data"
        lines.append(
            f"| {item['snapshot_label']} | {item['platform']} | {item['records_count']} | {coverage_label} | {'yes' if item['is_demo'] else 'no'} |"
        )
    lines.extend(["", "## Advertising-profile evidence", "", "| Original label | Platform | Category | Evidence | Source |", "|---|---|---|---|---|"])
    for item in interests:
        original_label = item["original_label"].replace("|", "\\|")
        lines.append(
            f"| {original_label} | {item['platform']} | {item['category']} | {item['evidence_type']} | `{item['source_file']}#{item['source_record_path']}` |"
        )
    lines.extend(["", "## Browser observations", "", "| Time | Initiator | Destination | Classification | Decision |", "|---|---|---|---|---|"])
    for item in observations:
        lines.append(
            f"| {item['observed_at']} | {item.get('initiator_domain') or 'unknown'} | {item['destination_domain']} | {item['classification']} | {item['decision']} |"
        )
    if before and after:
        try:
            drift = profile_drift(before, after)
            lines.extend([
                "", "## Profile Drift", "",
                f"- Algorithm: `{drift['algorithm_version']}`",
                f"- Newly reported: {len(drift['added'])}",
                f"- Retained: {len(drift['retained'])}",
                f"- Supported removals: {len(drift['removed'])}",
                f"- Uncertain absence: {len(drift['uncertain_absence'])}",
                "",
                drift["interpretation"],
            ])
        except HTTPException:
            lines.extend(["", "## Profile Drift", "", "The requested snapshots were not available locally."])
    lines.extend(["", "## Limitations", "", "- Observed requests and configured rules are not the same as verified blocked requests.", "- Missing export categories are not evidence of platform deletion.", "- Inferred classifications remain distinct from platform-reported evidence.", ""])
    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename= SOVRIVA_profile_report.md".replace("= ", "=")},
    )


@app.post("/api/privacy-actions/{action_id}/verify/{after_import_id}")
def verify_privacy_action(action_id: str, after_import_id: str) -> dict[str, Any]:
    with transaction() as db:
        action = db.execute("SELECT * FROM privacy_actions WHERE id = ?", (action_id,)).fetchone()
        after = db.execute("SELECT * FROM imports WHERE id = ?", (after_import_id,)).fetchone()
        if not action or not after:
            raise HTTPException(status_code=404, detail="Action or after snapshot not found")
        before_interest = db.execute("SELECT * FROM interests WHERE id = ?", (action["interest_id"],)).fetchone()
        if not before_interest:
            raise HTTPException(status_code=404, detail="Original evidence not found")
        later = db.execute(
            "SELECT * FROM interests WHERE import_id = ? AND normalized_label = ?",
            (after_import_id, before_interest["normalized_label"]),
        ).fetchone()
        if later:
            status = "NO_CHANGE_OBSERVED"
            explanation = "The same normalized label remains in the subsequent export."
        elif json_value(after["coverage"], {}).get("explicit_interest_support"):
            status = "OBSERVED_CHANGE"
            explanation = "The subsequent export explicitly supports interest data and does not contain the prior label."
        else:
            status = "NOT_VERIFIABLE"
            explanation = "The subsequent export does not provide enough interest coverage to assess absence."
        report = {"status": status, "explanation": explanation, "evidence_ids": [action["interest_id"], after_import_id]}
        db.execute(
            "UPDATE privacy_actions SET after_import_id = ?, verification_status = ?, verification_report = ? WHERE id = ?",
            (after_import_id, status, json_text(report), action_id),
        )
        updated = db.execute("SELECT * FROM privacy_actions WHERE id = ?", (action_id,)).fetchone()
    result = dict(updated)
    result["verification_report"] = json_value(result["verification_report"], {})
    return result


def _demo_zip(platform: str) -> bytes:
    payload: dict[str, Any]
    if platform == "meta":
        payload = {
            "advertisers_using_your_activity_or_information": [
                {"name": "Trail running", "category": "sports", "source": "sample"},
                {"name": "Sustainable travel", "category": "travel", "source": "sample"},
                {"name": "Independent coffee", "category": "food", "source": "sample"},
            ]
        }
        filename = "sample_meta_ads_information.json"
    else:
        payload = {
            "items": [
                {"title": "Search: trail running shoes", "url": "https://example.test/search", "timestamp": "2026-09-02T10:00:00Z"},
                {"title": "Search: privacy-first analytics", "url": "https://example.test/search", "timestamp": "2026-09-10T11:30:00Z"},
                {"title": "YouTube: sustainable travel guide", "url": "https://youtube.com/watch?v=sample", "timestamp": "2026-09-15T09:20:00Z"},
            ]
        }
        filename = "sample_google_my_activity.json"
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(filename, json.dumps(payload))
    return output.getvalue()


@app.post("/api/demo/seed")
def seed_demo() -> dict[str, Any]:
    """Insert clearly labelled isolated data, never mixed with personal imports."""
    results = []
    for platform in ("google", "meta"):
        raw = _demo_zip(platform)
        try:
            parsed = parse_archive(raw, f"[DEMO] {platform.title()} sample.zip", platform)
            results.append(_insert_parsed(parsed, is_demo=True))
        except HTTPException as exc:
            if exc.status_code != 409:
                raise
    return {"status": "demo_ready", "imports": results, "notice": "ISOLATED DEMONSTRATION DATA — not personal activity"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/assets/{filename}")
def assets(filename: str) -> FileResponse:
    safe = Path(filename).name
    path = STATIC_DIR / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(path)


@app.exception_handler(Exception)
async def safe_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(status_code=500, content={"detail": "Local SOVRIVA operation failed safely"})
