import io
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.models import Episode, Quality, Role
from app.services.episode_import import (
    EpisodeRow,
    InvalidCsvError,
    RowError,
    SkipReason,
    import_episodes,
    parse_row,
)
from tests.factories import auth, make_user

SEED_CSV = Path(__file__).resolve().parents[2] / "seed" / "episodes.csv"
ROBOTS = frozenset({"arm-01", "arm-02", "arm-03", "mobile-01", "humanoid-01"})
HEADER = "episode_id,robot_id,task_name,recorded_at,duration_seconds,operator_name,quality\n"


def _row(**overrides):
    base = {
        "episode_id": "EP-1",
        "robot_id": "arm-01",
        "task_name": "pick cup",
        "recorded_at": "2026-08-01T10:00:00",
        "duration_seconds": "30",
        "operator_name": "Eric",
        "quality": "good",
    }
    return base | overrides


# --- row normalisation ---------------------------------------------------------


def test_clean_row_is_normalised():
    result = parse_row(
        _row(episode_id=" ep-1 ", robot_id=" ARM-01", task_name="  Pick   Cup ", quality="USABLE"),
        ROBOTS,
    )
    assert result == EpisodeRow(
        episode_id="EP-1",
        robot_id="arm-01",
        task_name="pick cup",
        recorded_at=datetime(2026, 8, 1, 10, tzinfo=timezone.utc),
        duration_seconds=30,
        operator_name="Eric",
        quality=Quality.USABLE,
    )


@pytest.mark.parametrize(
    "value, expected",
    [
        ("2026-08-14T09:20:00Z", datetime(2026, 8, 14, 9, 20, tzinfo=timezone.utc)),
        ("2026-08-14 09:12:00", datetime(2026, 8, 14, 9, 12, tzinfo=timezone.utc)),
        ("14/08/2026 09:15", datetime(2026, 8, 14, 9, 15, tzinfo=timezone.utc)),  # day-first
    ],
)
def test_accepted_date_formats(value, expected):
    assert parse_row(_row(recorded_at=value), ROBOTS).recorded_at == expected


@pytest.mark.parametrize(
    "overrides, reason",
    [
        ({"episode_id": "  "}, SkipReason.MISSING_EPISODE_ID),
        ({"robot_id": "arm-99"}, SkipReason.UNKNOWN_ROBOT),
        ({"robot_id": ""}, SkipReason.UNKNOWN_ROBOT),
        ({"task_name": " "}, SkipReason.MISSING_TASK_NAME),
        ({"recorded_at": "not a date"}, SkipReason.INVALID_RECORDED_AT),
        ({"duration_seconds": "45.5"}, SkipReason.INVALID_DURATION),
        ({"duration_seconds": "-5"}, SkipReason.INVALID_DURATION),
        ({"duration_seconds": "0"}, SkipReason.INVALID_DURATION),
        ({"duration_seconds": "N/A"}, SkipReason.INVALID_DURATION),
        ({"duration_seconds": ""}, SkipReason.INVALID_DURATION),
        ({"quality": "excellent"}, SkipReason.INVALID_QUALITY),
        ({"quality": ""}, SkipReason.INVALID_QUALITY),
        ({"quality": None}, SkipReason.MALFORMED_ROW),  # short row from DictReader
    ],
)
def test_invalid_rows_are_rejected_with_a_reason(overrides, reason):
    result = parse_row(_row(**overrides), ROBOTS)
    assert isinstance(result, RowError)
    assert result.reason is reason


def test_missing_operator_name_is_allowed():
    assert parse_row(_row(operator_name=" "), ROBOTS).operator_name is None


# --- import against the database -----------------------------------------------


def _count(db) -> int:
    return db.scalar(select(func.count()).select_from(Episode))


def test_seed_file_import_report(db):
    with SEED_CSV.open(encoding="utf-8-sig", newline="") as fh:
        report = import_episodes(db, fh).as_dict()
    assert report["rows_read"] == report["imported"] + report["skipped"]
    assert report["imported"] == _count(db) == 174
    assert report["skipped_by_reason"]["duplicate_in_file"] == 4
    assert report["skipped_by_reason"]["unknown_robot"] == 2
    assert all(e["reason"] and e["line"] > 1 for e in report["errors"])


def test_import_is_idempotent(db):
    for _ in range(2):
        with SEED_CSV.open(encoding="utf-8-sig", newline="") as fh:
            report = import_episodes(db, fh).as_dict()
    assert report["imported"] == 0
    assert report["skipped_by_reason"]["already_imported"] == 174
    assert _count(db) == 174


def test_conflicting_duplicate_keeps_first_occurrence(db):
    csv_text = (
        HEADER
        + "EP-7,arm-01,pick cup,2026-08-01T10:00:00,30,Eric,bad\n"
        + "ep-7,arm-01,pick cup,2026-08-01T10:00:00,30,Eric,good\n"
    )
    report = import_episodes(db, io.StringIO(csv_text)).as_dict()
    assert report["imported"] == 1
    assert "conflicting" in report["errors"][0]["detail"]
    assert db.scalar(select(Episode.quality).where(Episode.episode_id == "EP-7")) is Quality.BAD


def test_missing_columns_rejects_whole_file(db):
    with pytest.raises(InvalidCsvError):
        import_episodes(db, io.StringIO("episode_id,robot_id\nEP-1,arm-01\n"))


# --- HTTP endpoint -------------------------------------------------------------


def _upload(client, user, content: bytes):
    return client.post(
        "/episodes/import",
        files={"file": ("episodes.csv", content, "text/csv")},
        headers=auth(user),
    )


def test_operator_can_import_via_api(client, db):
    op = make_user(db, Role.OPERATOR)
    res = _upload(client, op, SEED_CSV.read_bytes())
    assert res.status_code == 200
    assert res.json()["imported"] == 174


def test_client_cannot_import(client, db):
    res = _upload(client, make_user(db, Role.CLIENT), SEED_CSV.read_bytes())
    assert res.status_code == 403
    assert _count(db) == 0


def test_import_requires_authentication(client):
    res = client.post("/episodes/import", files={"file": ("e.csv", b"x", "text/csv")})
    assert res.status_code == 401


def test_bad_header_returns_422(client, db):
    res = _upload(client, make_user(db, Role.ADMIN), b"foo,bar\n1,2\n")
    assert res.status_code == 422
