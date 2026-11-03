"""SQLite persistence with explicit, versioned schema and rollback-friendly writes."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parent.parent
_default_data_dir = ROOT / "data"
if os.name == "nt" and (getattr(sys, "frozen", False) or os.getenv("SOVRIVA_PACKAGED") == "1"):
    _default_data_dir = Path(os.getenv("LOCALAPPDATA", ROOT)) / "SOVRIVA"
DATA_DIR = Path(os.getenv("SOVRIVA_DATA_DIR", _default_data_dir))
DB_PATH = DATA_DIR / "sovriva.db"
SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def json_value(value: str | None, default: Any = None) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    return connection


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    connection = connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    with transaction() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS imports (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                filename TEXT NOT NULL,
                source_sha256 TEXT NOT NULL UNIQUE,
                imported_at TEXT NOT NULL,
                status TEXT NOT NULL,
                snapshot_label TEXT NOT NULL,
                total_files INTEGER NOT NULL,
                supported_files INTEGER NOT NULL,
                unsupported_files TEXT NOT NULL,
                records_count INTEGER NOT NULL,
                coverage TEXT NOT NULL,
                parser_version TEXT NOT NULL
                ,is_demo INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS interests (
                id TEXT PRIMARY KEY,
                import_id TEXT NOT NULL REFERENCES imports(id) ON DELETE CASCADE,
                platform TEXT NOT NULL,
                original_label TEXT NOT NULL,
                normalized_label TEXT NOT NULL,
                category TEXT NOT NULL,
                source_file TEXT NOT NULL,
                source_record_path TEXT NOT NULL,
                source_record TEXT NOT NULL,
                observed_at TEXT,
                imported_at TEXT NOT NULL,
                evidence_type TEXT NOT NULL,
                preference TEXT NOT NULL DEFAULT 'UNREVIEWED',
                classification_status TEXT NOT NULL,
                confidence REAL NOT NULL,
                classifier_explanation TEXT NOT NULL,
                UNIQUE(import_id, normalized_label, source_file, source_record_path)
            );

            CREATE TABLE IF NOT EXISTS activity_records (
                id TEXT PRIMARY KEY,
                import_id TEXT NOT NULL REFERENCES imports(id) ON DELETE CASCADE,
                platform TEXT NOT NULL,
                record_type TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                occurred_at TEXT,
                source_file TEXT NOT NULL,
                source_record_path TEXT NOT NULL,
                source_record TEXT NOT NULL,
                evidence_type TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS observations (
                id TEXT PRIMARY KEY,
                observed_at TEXT NOT NULL,
                tab_id INTEGER,
                initiator_domain TEXT,
                destination_domain TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                third_party INTEGER NOT NULL,
                classification TEXT NOT NULL,
                decision TEXT NOT NULL,
                mode TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'extension'
            );

            CREATE TABLE IF NOT EXISTS privacy_actions (
                id TEXT PRIMARY KEY,
                interest_id TEXT NOT NULL REFERENCES interests(id) ON DELETE CASCADE,
                before_import_id TEXT NOT NULL REFERENCES imports(id) ON DELETE CASCADE,
                action_date TEXT NOT NULL,
                nature TEXT NOT NULL,
                notes TEXT NOT NULL,
                created_at TEXT NOT NULL,
                verification_status TEXT NOT NULL DEFAULT 'PENDING',
                after_import_id TEXT REFERENCES imports(id) ON DELETE SET NULL,
                verification_report TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_feedback (
                interest_id TEXT PRIMARY KEY REFERENCES interests(id) ON DELETE CASCADE,
                classification TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pairing_codes (
                id TEXT PRIMARY KEY,
                code_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                consumed INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS extension_tokens (
                id TEXT PRIMARY KEY,
                token_hash TEXT NOT NULL UNIQUE,
                extension_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_seen_at TEXT,
                revoked INTEGER NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_interests_import ON interests(import_id);
            CREATE INDEX IF NOT EXISTS idx_interests_normalized ON interests(normalized_label);
            CREATE INDEX IF NOT EXISTS idx_activity_import ON activity_records(import_id);
            CREATE INDEX IF NOT EXISTS idx_pairing_expiry ON pairing_codes(expires_at);
            CREATE INDEX IF NOT EXISTS idx_observations_time ON observations(observed_at);
            """
        )
        db.execute(
            "INSERT OR REPLACE INTO schema_meta(key, value) VALUES ('version', ?)",
            (str(SCHEMA_VERSION),),
        )
        db.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES ('privacy_mode', 'BALANCED')"
        )
        db.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES ('ad_blocking_enabled', 'true')"
        )
        db.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES ('tracker_blocking_enabled', 'true')"
        )
        columns = {row["name"] for row in db.execute("PRAGMA table_info(imports)").fetchall()}
        if "is_demo" not in columns:
            db.execute("ALTER TABLE imports ADD COLUMN is_demo INTEGER NOT NULL DEFAULT 0")


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def rows_to_dict(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]
