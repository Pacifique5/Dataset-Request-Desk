from datetime import date, datetime, timedelta, timezone

import pytest

from app.models import Quality, RequestStatus, RequestStatusEvent, Role
from tests.factories import auth, make_episode, make_request, make_user

S = RequestStatus


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture
def staff(db):
    return make_user(db, Role.OPERATOR)


def _get(client, user, qs="from=2026-08-01&to=2026-08-02"):
    return client.get(f"/analytics?{qs}", headers=auth(user))


def test_episodes_per_day_per_robot_respects_inclusive_utc_range(client, db, staff):
    make_episode(db, robot_id="arm-01", recorded_at=utc(2026, 7, 31, 23, 59))  # before range
    make_episode(db, robot_id="arm-01", recorded_at=utc(2026, 8, 1, 0, 0))
    make_episode(db, robot_id="arm-01", recorded_at=utc(2026, 8, 1, 18, 0))
    make_episode(db, robot_id="arm-02", recorded_at=utc(2026, 8, 1, 9, 0))
    make_episode(db, robot_id="arm-01", recorded_at=utc(2026, 8, 2, 23, 59))  # last minute
    make_episode(db, robot_id="arm-01", recorded_at=utc(2026, 8, 3, 0, 0))  # after range

    rows = _get(client, staff).json()["episodes_per_day_per_robot"]
    assert rows == [
        {"day": "2026-08-01", "robot_id": "arm-01", "episodes": 2},
        {"day": "2026-08-01", "robot_id": "arm-02", "episodes": 1},
        {"day": "2026-08-02", "robot_id": "arm-01", "episodes": 1},
    ]


def test_top_tasks_counts_only_good_episodes_top_five(client, db, staff):
    when = utc(2026, 8, 1, 12)
    counts = {"a": 6, "b": 5, "c": 4, "d": 3, "e": 2, "f": 1}
    for task, n in counts.items():
        for _ in range(n):
            make_episode(db, Quality.GOOD, task_name=task, recorded_at=when)
    for _ in range(10):  # lots of usable 'f' must not count
        make_episode(db, Quality.USABLE, task_name="f", recorded_at=when)

    top = _get(client, staff).json()["top_tasks_by_good_episodes"]
    assert [(t["task_name"], t["good_episodes"]) for t in top] == [
        ("a", 6),
        ("b", 5),
        ("c", 4),
        ("d", 3),
        ("e", 2),
    ]


def _event(db, req, frm, to, at, by):
    db.add(
        RequestStatusEvent(
            request_id=req.id, from_status=frm, to_status=to, changed_at=at, changed_by_id=by.id
        )
    )
    db.flush()


def test_fulfilment_counts_and_median_uses_first_delivery(client, db, staff):
    cli = make_user(db, Role.CLIENT)
    created = utc(2026, 8, 1, 10)
    hours = [2, 4, 10]  # median = 4h
    for h in hours:
        req = make_request(db, cli, status=S.ACCEPTED, created_at=created)
        _event(db, req, S.IN_PROGRESS, S.DELIVERED, created + timedelta(hours=h), staff)
    # Rework: rejected then delivered again much later; only the FIRST delivery counts.
    rework = make_request(db, cli, status=S.DELIVERED, created_at=created)
    _event(db, rework, S.IN_PROGRESS, S.DELIVERED, created + timedelta(hours=4), staff)
    _event(db, rework, S.IN_PROGRESS, S.DELIVERED, created + timedelta(days=5), staff)
    make_request(db, cli, status=S.SUBMITTED, created_at=created)  # never delivered
    make_request(db, cli, status=S.SUBMITTED, created_at=utc(2026, 9, 1))  # outside range

    f = _get(client, staff).json()["fulfilment"]
    assert f["requests_by_status"] == {
        "submitted": 1,
        "in_progress": 0,
        "delivered": 1,
        "accepted": 3,
        "rejected": 0,
    }
    assert f["delivered_sample_size"] == 4
    assert f["median_submitted_to_delivered_seconds"] == 4 * 3600


def test_empty_range_returns_zeros_not_errors(client, staff):
    body = _get(client, staff, "from=2020-01-01&to=2020-01-31").json()
    assert body["episodes_per_day_per_robot"] == []
    assert body["top_tasks_by_good_episodes"] == []
    assert body["fulfilment"]["median_submitted_to_delivered_seconds"] is None


def test_default_range_is_last_30_days(client, staff):
    body = client.get("/analytics", headers=auth(staff)).json()
    assert body["date_to"] == str(date.today())
    assert body["date_from"] == str(date.today() - timedelta(days=29))


@pytest.mark.parametrize("qs", ["from=2026-08-10&to=2026-08-01", "from=2020-01-01&to=2026-01-01"])
def test_invalid_ranges_are_422(client, staff, qs):
    assert _get(client, staff, qs).status_code == 422


def test_clients_cannot_see_analytics(client, db):
    assert _get(client, make_user(db, Role.CLIENT)).status_code == 403
