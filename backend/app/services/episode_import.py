"""Idempotent, streaming import of the recording system's episode CSV export.

Design:
- Every row is normalised and validated in pure Python (`parse_row`) and either becomes
  a clean `EpisodeRow` or a `RowError` with a machine-readable reason.
- Valid rows are inserted in batches with `INSERT ... ON CONFLICT (episode_id) DO NOTHING`,
  so re-running the same file (or two imports racing) never creates duplicates. Rows
  that already exist are reported as `already_imported`, never overwritten.
- The file is streamed, so memory stays flat regardless of file size.
"""

import csv
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TextIO

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Episode, Quality, Robot

REQUIRED_COLUMNS = (
    "episode_id",
    "robot_id",
    "task_name",
    "recorded_at",
    "duration_seconds",
    "operator_name",
    "quality",
)
BATCH_SIZE = 1000
MAX_REPORTED_ERRORS = 500

# Accepted timestamp formats, tried in order. Naive values are treated as UTC.
# "DD/MM/YYYY HH:MM" is day-first: the export contains 14/08/2026, which only parses
# day-first, so we assume the recording system uses one convention consistently.
# Episodes can't be recorded in the future; allow a day of clock skew between systems.
FUTURE_TOLERANCE = timedelta(days=1)
_DATE_FORMATS = ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M")
_WS = re.compile(r"\s+")


class SkipReason(str, Enum):
    BLANK_ROW = "blank_row"
    MALFORMED_ROW = "malformed_row"
    MISSING_EPISODE_ID = "missing_episode_id"
    UNKNOWN_ROBOT = "unknown_robot"
    MISSING_TASK_NAME = "missing_task_name"
    INVALID_RECORDED_AT = "invalid_recorded_at"
    RECORDED_IN_FUTURE = "recorded_in_future"
    INVALID_DURATION = "invalid_duration"
    INVALID_QUALITY = "invalid_quality"
    DUPLICATE_IN_FILE = "duplicate_in_file"
    ALREADY_IMPORTED = "already_imported"


@dataclass(frozen=True, slots=True)
class EpisodeRow:
    episode_id: str
    robot_id: str
    task_name: str
    recorded_at: datetime
    duration_seconds: int
    operator_name: str | None
    quality: Quality


@dataclass(frozen=True, slots=True)
class RowError:
    reason: SkipReason
    detail: str
    episode_id: str | None = None


@dataclass
class ImportReport:
    rows_read: int = 0
    imported: int = 0
    skipped: Counter[SkipReason] = field(default_factory=Counter)
    errors: list[dict] = field(default_factory=list)

    def skip(self, line: int, err: RowError) -> None:
        self.skipped[err.reason] += 1
        if len(self.errors) < MAX_REPORTED_ERRORS:
            self.errors.append(
                {
                    "line": line,
                    "episode_id": err.episode_id,
                    "reason": err.reason.value,
                    "detail": err.detail,
                }
            )

    def as_dict(self) -> dict:
        return {
            "rows_read": self.rows_read,
            "imported": self.imported,
            "skipped": sum(self.skipped.values()),
            "skipped_by_reason": {r.value: n for r, n in sorted(self.skipped.items())},
            "errors": self.errors,
            "errors_truncated": sum(self.skipped.values()) > len(self.errors),
        }


class InvalidCsvError(ValueError):
    """The file as a whole is unusable (e.g. missing columns)."""


# --- normalisation helpers (pure, unit-tested) ------------------------------------


def _clean(value: str | None) -> str:
    return _WS.sub(" ", value or "").strip()


def parse_recorded_at(value: str) -> datetime | None:
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        parsed = None
        for fmt in _DATE_FORMATS:
            try:
                parsed = datetime.strptime(value, fmt)  # noqa: DTZ007 (UTC applied below)
                break
            except ValueError:
                continue
    if parsed is None:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def parse_duration(value: str) -> int | None:
    """Whole, positive seconds only. '45.5', '-5', 'N/A' and '' are rejected, not guessed."""
    value = value.strip()
    if not value.isdigit():
        return None
    seconds = int(value)
    return seconds if seconds > 0 else None


def parse_row(
    raw: dict[str | None, str | None],
    known_robots: frozenset[str],
    now: datetime | None = None,
) -> EpisodeRow | RowError:
    # csv.DictReader puts surplus fields under key None and fills missing ones with None.
    if None in raw or any(raw.get(c) is None for c in REQUIRED_COLUMNS):
        return RowError(
            SkipReason.MALFORMED_ROW,
            "wrong number of columns",
            _clean(raw.get("episode_id")) or None,
        )

    episode_id = _clean(raw["episode_id"]).upper()
    if not episode_id:
        return RowError(SkipReason.MISSING_EPISODE_ID, "episode_id is empty")

    robot_id = _clean(raw["robot_id"]).lower()
    if robot_id not in known_robots:
        return RowError(SkipReason.UNKNOWN_ROBOT, f"unknown robot_id {robot_id!r}", episode_id)

    task_name = _clean(raw["task_name"]).lower()
    if not task_name:
        return RowError(SkipReason.MISSING_TASK_NAME, "task_name is empty", episode_id)

    recorded_at = parse_recorded_at(raw["recorded_at"])
    if recorded_at is None:
        return RowError(
            SkipReason.INVALID_RECORDED_AT,
            f"unparseable recorded_at {raw['recorded_at']!r}",
            episode_id,
        )
    if recorded_at > (now or datetime.now(timezone.utc)) + FUTURE_TOLERANCE:
        return RowError(
            SkipReason.RECORDED_IN_FUTURE,
            f"recorded_at {raw['recorded_at']!r} is in the future",
            episode_id,
        )

    duration = parse_duration(raw["duration_seconds"])
    if duration is None:
        return RowError(
            SkipReason.INVALID_DURATION,
            f"duration_seconds must be a positive integer, got {raw['duration_seconds']!r}",
            episode_id,
        )

    quality_raw = _clean(raw["quality"]).lower()
    try:
        quality = Quality(quality_raw)
    except ValueError:
        return RowError(
            SkipReason.INVALID_QUALITY, f"invalid quality {raw['quality']!r}", episode_id
        )

    return EpisodeRow(
        episode_id=episode_id,
        robot_id=robot_id,
        task_name=task_name,
        recorded_at=recorded_at,
        duration_seconds=duration,
        operator_name=_clean(raw["operator_name"]) or None,  # optional: keep the episode
        quality=quality,
    )


# --- orchestration -----------------------------------------------------------------


def _insert_batch(db: Session, batch: list[tuple[int, EpisodeRow]], report: ImportReport) -> None:
    if not batch:
        return
    stmt = (
        insert(Episode)
        .on_conflict_do_nothing(index_elements=["episode_id"])
        .returning(Episode.episode_id)
    )
    params = [
        {
            "episode_id": r.episode_id,
            "robot_id": r.robot_id,
            "task_name": r.task_name,
            "recorded_at": r.recorded_at,
            "duration_seconds": r.duration_seconds,
            "operator_name": r.operator_name,
            "quality": r.quality.value,
        }
        for _, r in batch
    ]
    # executemany + RETURNING: SQLAlchemy batches this into multi-row INSERTs
    # ("insertmanyvalues") without re-compiling a giant statement per batch.
    inserted = set(db.scalars(stmt, params))
    report.imported += len(inserted)
    for line, row in batch:
        if row.episode_id not in inserted:
            report.skip(
                line,
                RowError(SkipReason.ALREADY_IMPORTED, "episode already exists", row.episode_id),
            )
    batch.clear()


def import_episodes(db: Session, stream: TextIO) -> ImportReport:
    """Import a CSV stream. The caller owns the transaction (commit/rollback)."""
    reader = csv.DictReader(stream)
    missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise InvalidCsvError(f"missing required columns: {', '.join(missing)}")

    known_robots = frozenset(db.scalars(select(Robot.id)))
    now = datetime.now(timezone.utc)
    report = ImportReport()
    # episode_id -> hash of its first normalised row (a hash, not the row, keeps memory low).
    first_seen: dict[str, int] = {}
    batch: list[tuple[int, EpisodeRow]] = []

    for raw in _non_empty(reader, report):
        line = reader.line_num
        report.rows_read += 1
        result = parse_row(raw, known_robots, now)
        if isinstance(result, RowError):
            report.skip(line, result)
            continue

        previous = first_seen.get(result.episode_id)
        if previous is not None:
            kind = "identical" if previous == hash(result) else "conflicting"
            report.skip(
                line,
                RowError(
                    SkipReason.DUPLICATE_IN_FILE,
                    f"{kind} duplicate; first occurrence kept",
                    result.episode_id,
                ),
            )
            continue
        first_seen[result.episode_id] = hash(result)

        batch.append((line, result))
        if len(batch) >= BATCH_SIZE:
            _insert_batch(db, batch, report)

    _insert_batch(db, batch, report)
    return report


def _non_empty(reader: csv.DictReader, report: ImportReport) -> Iterable[dict]:
    """Skip rows that are entirely blank or whitespace (reported, not silently dropped)."""
    for raw in reader:
        if (
            all(not (v or "").strip() for v in raw.values() if isinstance(v, str))
            and None not in raw
        ):
            report.rows_read += 1
            report.skip(reader.line_num, RowError(SkipReason.BLANK_ROW, "row is empty"))
            continue
        yield raw
