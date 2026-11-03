"""User-authorized Google and Meta archive adapters.

The parser deliberately reads archives in memory and never extracts untrusted
paths to disk. It keeps source file names and JSON pointers with every record
so the UI can show exactly why a finding exists.
"""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
import zipfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from io import BytesIO
from typing import Any, Iterable


MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 350 * 1024 * 1024
MAX_FILES = 8_000
MAX_MEMBER_BYTES = 35 * 1024 * 1024
PARSER_VERSION = "sovriva-importers-0.1"

UNSAFE_SUFFIXES = {
    ".exe",
    ".dll",
    ".com",
    ".scr",
    ".bat",
    ".cmd",
    ".ps1",
    ".msi",
    ".vbs",
    ".jar",
}


class ArchiveValidationError(ValueError):
    """An archive is unsafe or exceeds a documented resource limit."""


class ImportParseError(ValueError):
    """The archive is readable but has no supported records."""


@dataclass
class InterestRecord:
    original_label: str
    source_file: str
    source_record_path: str
    source_record: dict[str, Any]
    observed_at: str | None
    evidence_type: str


@dataclass
class ActivityRecord:
    record_type: str
    title: str
    url: str | None
    occurred_at: str | None
    source_file: str
    source_record_path: str
    source_record: dict[str, Any]
    evidence_type: str


@dataclass
class ParsedImport:
    platform: str
    filename: str
    source_sha256: str
    total_files: int
    supported_files: int
    unsupported_files: list[str] = field(default_factory=list)
    interests: list[InterestRecord] = field(default_factory=list)
    activities: list[ActivityRecord] = field(default_factory=list)
    malformed_files: list[str] = field(default_factory=list)
    coverage: dict[str, Any] = field(default_factory=dict)

    @property
    def records_count(self) -> int:
        return len(self.interests) + len(self.activities)


def archive_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_member_name(name: str) -> str:
    if not name or "\x00" in name:
        raise ArchiveValidationError("Archive contains an empty or NUL-containing path")
    normalized = name.replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
        raise ArchiveValidationError(f"Absolute archive path is not allowed: {name}")
    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if ".." in parts:
        raise ArchiveValidationError(f"Path traversal entry is not allowed: {name}")
    suffix = posixpath.splitext(normalized.lower())[1]
    if suffix in UNSAFE_SUFFIXES:
        raise ArchiveValidationError(f"Executable archive member is not allowed: {name}")
    return "/".join(parts)


def validate_archive(data: bytes) -> list[zipfile.ZipInfo]:
    if len(data) > MAX_ARCHIVE_BYTES:
        raise ArchiveValidationError("Archive exceeds the 100 MB compressed size limit")
    try:
        archive = zipfile.ZipFile(BytesIO(data))
        members = archive.infolist()
        if len(members) > MAX_FILES:
            raise ArchiveValidationError("Archive contains too many files")
        total_size = 0
        for member in members:
            _safe_member_name(member.filename)
            if member.file_size > MAX_MEMBER_BYTES:
                raise ArchiveValidationError(f"Archive member is too large: {member.filename}")
            total_size += member.file_size
            if total_size > MAX_UNCOMPRESSED_BYTES:
                raise ArchiveValidationError("Archive exceeds the 350 MB expanded size limit")
        bad_member = archive.testzip()
        if bad_member:
            raise ArchiveValidationError(f"Archive checksum failed for {bad_member}")
        return members
    except zipfile.BadZipFile as exc:
        raise ArchiveValidationError("Uploaded file is not a valid ZIP archive") from exc


def detect_platform(names: Iterable[str], requested: str | None = None) -> str:
    if requested and requested.lower() in {"google", "meta"}:
        return requested.lower()
    joined = " ".join(name.lower() for name in names)
    if any(token in joined for token in ("facebook", "instagram", "meta", "ads_information")):
        return "meta"
    if any(token in joined for token in ("google", "my activity", "chrome", "youtube")):
        return "google"
    raise ImportParseError("Could not detect Google or Meta export format")


def _load_json(archive: zipfile.ZipFile, member: zipfile.ZipInfo) -> Any:
    raw = archive.read(member)
    return json.loads(raw.decode("utf-8-sig"))


def _walk(value: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _objects(value: Any) -> Iterable[tuple[str, dict[str, Any]]]:
    for path, item in _walk(value):
        if isinstance(item, dict):
            yield path, item


def _first_text(record: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _time_value(record: dict[str, Any]) -> str | None:
    value = _first_text(record, ("timestamp", "time", "datetime", "date", "creation_timestamp"))
    if value:
        return value
    for key in ("timestamp", "time", "creation_timestamp"):
        if isinstance(record.get(key), (int, float)):
            return str(record[key])
    return None


def _record_label(record: dict[str, Any]) -> str | None:
    candidate = _first_text(
        record,
        (
            "interest",
            "interest_name",
            "interestName",
            "label",
            "topic",
            "topic_name",
            "advertiser",
            "advertiser_name",
            "name",
            "title",
        ),
    )
    if not candidate:
        return None
    candidate = re.sub(r"\s+", " ", candidate).strip()
    if len(candidate) < 2 or len(candidate) > 180:
        return None
    if candidate.startswith(("http://", "https://", "www.")):
        return None
    if candidate.lower() in {"name", "title", "unknown", "none", "null", "advertiser"}:
        return None
    return candidate


def _record_url(record: dict[str, Any]) -> str | None:
    value = _first_text(record, ("url", "titleUrl", "title_url", "link", "href"))
    return value if value and value.startswith(("http://", "https://")) else None


class _ActivityHTMLParser(HTMLParser):
    """Small safe extractor for legacy exports; it never executes or renders HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            self._href = href if href and href.startswith(("http://", "https://")) else None
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href:
            text = re.sub(r"\s+", " ", " ".join(self._text)).strip()
            if len(text) >= 2:
                self.links.append((text[:240], self._href))
            self._href = None
            self._text = []


def _parse_html_activity(
    archive: zipfile.ZipFile,
    member: zipfile.ZipInfo,
    platform: str,
    activities: list[ActivityRecord],
    coverage: dict[str, Any],
) -> bool:
    name = _safe_member_name(member.filename)
    lower = name.lower()
    if not lower.endswith((".html", ".htm")):
        return False
    if not re.search(r"activity|history|youtube|search|chrome|browser", lower):
        return False
    raw = archive.read(member)
    parser = _ActivityHTMLParser()
    try:
        parser.feed(raw.decode("utf-8", errors="replace"))
    except Exception:
        return False
    if not parser.links:
        return False
    coverage.setdefault("html_files", []).append(name)
    for index, (title, url) in enumerate(parser.links):
        record_type = "YOUTUBE_ACTIVITY" if "youtube" in lower else "BROWSING_ACTIVITY"
        activities.append(
            ActivityRecord(
                record_type=record_type,
                title=title,
                url=url,
                occurred_at=None,
                source_file=name,
                source_record_path=f"html.a[{index}]",
                source_record={"title": title, "url": url, "format": "legacy-html"},
                evidence_type="BROWSER_OBSERVED" if platform == "google" else "PLATFORM_REPORTED",
            )
        )
    return True


def _parse_records(
    archive: zipfile.ZipFile,
    member: zipfile.ZipInfo,
    platform: str,
    interests: list[InterestRecord],
    activities: list[ActivityRecord],
    coverage: dict[str, Any],
) -> bool:
    name = _safe_member_name(member.filename)
    lower = name.lower()
    if not lower.endswith(".json"):
        return False
    try:
        data = _load_json(archive, member)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False

    interest_context = bool(
        re.search(r"interest|advertis|advertiser|(^|[/_ -])ads?([_/ .-]|$)|ad[_ -]?preference|personaliz|topic", lower)
    )
    activity_context = bool(
        re.search(r"activity|history|youtube|search|off[_ -]?meta|browser|location", lower)
    )
    if interest_context:
        coverage.setdefault("interest_files", []).append(name)
    if activity_context:
        coverage.setdefault("activity_files", []).append(name)

    found = False
    for path, record in _objects(data):
        label = _record_label(record)
        if interest_context and label:
            interests.append(
                InterestRecord(
                    original_label=label,
                    source_file=name,
                    source_record_path=path or "$",
                    source_record=dict(record),
                    observed_at=_time_value(record),
                    evidence_type="PLATFORM_REPORTED",
                )
            )
            found = True
        if activity_context:
            title = _first_text(record, ("title", "name", "query", "activity", "text"))
            url = _record_url(record)
            if title and len(title) >= 2 and (url or "history" in lower or "activity" in lower):
                record_type = "SEARCH" if "search" in lower or "query" in record else "BROWSING_ACTIVITY"
                if "youtube" in lower:
                    record_type = "YOUTUBE_ACTIVITY"
                activities.append(
                    ActivityRecord(
                        record_type=record_type,
                        title=title[:240],
                        url=url,
                        occurred_at=_time_value(record),
                        source_file=name,
                        source_record_path=path or "$",
                        source_record=dict(record),
                        evidence_type="BROWSER_OBSERVED" if platform == "google" else "PLATFORM_REPORTED",
                    )
                )
                found = True
    return found


def parse_archive(data: bytes, filename: str, requested_platform: str | None = None) -> ParsedImport:
    members = validate_archive(data)
    names = [_safe_member_name(member.filename) for member in members if not member.is_dir()]
    platform = detect_platform(names, requested_platform)
    interests: list[InterestRecord] = []
    activities: list[ActivityRecord] = []
    unsupported: list[str] = []
    malformed: list[str] = []
    coverage: dict[str, Any] = {"formats": [], "interest_files": [], "activity_files": [], "html_files": []}

    with zipfile.ZipFile(BytesIO(data)) as archive:
        for member in members:
            if member.is_dir():
                continue
            name = _safe_member_name(member.filename)
            if name.lower().endswith(".json"):
                try:
                    supported = _parse_records(
                        archive, member, platform, interests, activities, coverage
                    )
                except (UnicodeDecodeError, json.JSONDecodeError):
                    malformed.append(name)
                    supported = False
                if not supported:
                    unsupported.append(name)
            elif name.lower().endswith((".html", ".htm")):
                supported = _parse_html_activity(archive, member, platform, activities, coverage)
                coverage["formats"].append("legacy-html")
                if not supported:
                    unsupported.append(name)
            elif name.lower().endswith((".csv", ".txt")):
                # These are retained in coverage but are never executed or rendered as HTML.
                unsupported.append(name)
            else:
                unsupported.append(name)

    # Deduplicate records without losing source provenance.
    unique_interests: list[InterestRecord] = []
    seen_interests: set[tuple[str, str, str]] = set()
    for item in interests:
        key = (item.original_label.casefold(), item.source_file, item.source_record_path)
        if key not in seen_interests:
            seen_interests.add(key)
            unique_interests.append(item)
    unique_activities: list[ActivityRecord] = []
    seen_activities: set[tuple[str, str, str]] = set()
    for item in activities:
        key = (item.title.casefold(), item.source_file, item.source_record_path)
        if key not in seen_activities:
            seen_activities.add(key)
            unique_activities.append(item)

    coverage["interest_files"] = sorted(set(coverage["interest_files"]))
    coverage["activity_files"] = sorted(set(coverage["activity_files"]))
    coverage["html_files"] = sorted(set(coverage["html_files"]))
    coverage["explicit_interest_support"] = bool(unique_interests or coverage["interest_files"])
    coverage["malformed_files"] = malformed
    coverage["notes"] = [
        "An export is a user-authorized view of available records, not the platform's complete internal profile.",
        "Missing files are reported as incomplete evidence rather than removals.",
    ]
    if not unique_interests and not unique_activities:
        raise ImportParseError("No supported JSON records were found in the archive")
    return ParsedImport(
        platform=platform,
        filename=filename or "uploaded-export.zip",
        source_sha256=archive_sha256(data),
        total_files=len(names),
        supported_files=len(set(coverage["interest_files"] + coverage["activity_files"])),
        unsupported_files=sorted(set(unsupported)),
        interests=unique_interests,
        activities=unique_activities,
        malformed_files=malformed,
        coverage=coverage,
    )
