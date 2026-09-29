from datetime import date, timedelta
from itertools import product

import pytest

from app.core.errors import InvalidTransitionError, PermissionDeniedError
from app.models import DatasetRequest, RequestStatus, Role
from app.services.requests import change_status
from app.services.workflow import TRANSITIONS
from tests.factories import assign, auth, make_episode, make_request, make_user

S = RequestStatus


@pytest.fixture
def people(db):
    return {
        "client": make_user(db, Role.CLIENT),
        "other_client": make_user(db, Role.CLIENT),
        "operator": make_user(db, Role.OPERATOR),
        "admin": make_user(db, Role.ADMIN),
    }


def _new_request_body(**overrides):
    body = {
        "task_name": "  Pick   CUP ",
        "episodes_requested": 2,
        "deadline": str(date.today() + timedelta(days=14)),
        "notes": "cups only",
    }
    return body | overrides


# --- creation & visibility -----------------------------------------------------


def test_client_creates_request_and_history_starts(client, people):
    res = client.post("/requests", json=_new_request_body(), headers=auth(people["client"]))
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "submitted"
    assert body["task_name"] == "pick cup"  # normalised like imported episodes
    assert body["client"]["id"] == people["client"].id
    assert [(e["from_status"], e["to_status"]) for e in body["events"]] == [(None, "submitted")]
    assert body["events"][0]["changed_by"]["id"] == people["client"].id


@pytest.mark.parametrize("role", ["operator", "admin"])
def test_staff_cannot_create_requests(client, people, role):
    res = client.post("/requests", json=_new_request_body(), headers=auth(people[role]))
    assert res.status_code == 403


@pytest.mark.parametrize(
    "overrides",
    [
        {"deadline": str(date.today() - timedelta(days=1))},
        {"episodes_requested": 0},
        {"task_name": "   "},
        {"notes": "x" * 2001},
    ],
)
def test_invalid_request_is_rejected(client, people, overrides):
    res = client.post(
        "/requests", json=_new_request_body(**overrides), headers=auth(people["client"])
    )
    assert res.status_code == 422


def test_clients_only_see_their_own_requests(client, db, people):
    mine = make_request(db, people["client"])
    theirs = make_request(db, people["other_client"])

    listed = client.get("/requests", headers=auth(people["client"])).json()
    assert [r["id"] for r in listed["items"]] == [mine.id]
    assert listed["total"] == 1
    # Someone else's request looks exactly like a missing one.
    assert client.get(f"/requests/{theirs.id}", headers=auth(people["client"])).status_code == 404


def test_staff_see_all_requests_and_can_filter_by_status(client, db, people):
    make_request(db, people["client"])
    make_request(db, people["other_client"], status=S.IN_PROGRESS)
    headers = auth(people["operator"])
    assert client.get("/requests", headers=headers).json()["total"] == 2
    filtered = client.get("/requests?status=in_progress", headers=headers).json()
    assert [r["status"] for r in filtered["items"]] == ["in_progress"]


def test_client_cannot_transition_someone_elses_request(client, db, people):
    req = make_request(db, people["other_client"], status=S.DELIVERED)
    res = client.post(
        f"/requests/{req.id}/transitions",
        json={"to_status": "accepted"},
        headers=auth(people["client"]),
    )
    assert res.status_code == 404
    db.refresh(req)
    assert req.status is S.DELIVERED


# --- the state machine, exhaustively --------------------------------------------


@pytest.mark.parametrize(
    "current, target, role", list(product(S, S, ["client", "operator", "admin"]))
)
def test_every_transition_matches_the_table(db, people, current, target, role):
    """All 75 (from, to, role) combinations: allowed iff listed in TRANSITIONS."""
    req = make_request(db, people["client"], status=current, episodes_requested=1)
    assign(db, req, make_episode(db), people["operator"])  # satisfy the delivery rule
    actor = people[role]
    allowed_roles = TRANSITIONS.get((current, target))

    if allowed_roles is None:
        with pytest.raises(InvalidTransitionError):
            change_status(db, actor, req.id, target)
    elif actor.role not in allowed_roles:
        with pytest.raises(PermissionDeniedError):
            change_status(db, actor, req.id, target)
    else:
        assert change_status(db, actor, req.id, target).status is target


def test_cannot_deliver_until_enough_episodes_are_assigned(client, db, people):
    req = make_request(db, people["client"], status=S.IN_PROGRESS, episodes_requested=2)
    assign(db, req, make_episode(db), people["operator"])
    headers = auth(people["operator"])

    res = client.post(
        f"/requests/{req.id}/transitions", json={"to_status": "delivered"}, headers=headers
    )
    assert res.status_code == 422
    assert "1 of 2" in res.json()["detail"]

    assign(db, req, make_episode(db), people["operator"])
    res = client.post(
        f"/requests/{req.id}/transitions", json={"to_status": "delivered"}, headers=headers
    )
    assert res.status_code == 200


def test_full_lifecycle_with_rework_records_every_step(client, db, people):
    cli, op = auth(people["client"]), auth(people["operator"])
    req_id = client.post(
        "/requests", json=_new_request_body(episodes_requested=1), headers=cli
    ).json()["id"]
    req = db.get(DatasetRequest, req_id)
    assign(db, req, make_episode(db), people["operator"])

    def move(to, headers, note=None):
        r = client.post(
            f"/requests/{req_id}/transitions", json={"to_status": to, "note": note}, headers=headers
        )
        assert r.status_code == 200, r.json()
        return r.json()

    move("in_progress", op)
    assert move("delivered", op)["allowed_transitions"] == []  # operator has nothing to do now
    assert set(client.get(f"/requests/{req_id}", headers=cli).json()["allowed_transitions"]) == {
        "accepted",
        "rejected",
    }
    move("rejected", cli, note="blurry footage")
    move("in_progress", op)
    move("delivered", op)
    final = move("accepted", cli)

    steps = [(e["from_status"], e["to_status"], e["changed_by"]["id"]) for e in final["events"]]
    c, o = people["client"].id, people["operator"].id
    assert steps == [
        (None, "submitted", c),
        ("submitted", "in_progress", o),
        ("in_progress", "delivered", o),
        ("delivered", "rejected", c),
        ("rejected", "in_progress", o),
        ("in_progress", "delivered", o),
        ("delivered", "accepted", c),
    ]
    assert final["events"][3]["note"] == "blurry footage"
    assert all(e["changed_at"] for e in final["events"])


def test_error_body_is_consistent(client, db, people):
    req = make_request(db, people["client"])
    res = client.post(
        f"/requests/{req.id}/transitions",
        json={"to_status": "accepted"},
        headers=auth(people["client"]),
    )
    assert res.status_code == 409
    assert res.json() == {
        "detail": "Cannot move a request from submitted to accepted",
        "code": "invalid_transition",
    }
