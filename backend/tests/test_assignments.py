import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Assignment, Quality, RequestStatus, Role
from tests.factories import assign, auth, make_episode, make_request, make_user

S = RequestStatus


@pytest.fixture
def ctx(db):
    client_user = make_user(db, Role.CLIENT)
    operator = make_user(db, Role.OPERATOR)
    return {
        "client": client_user,
        "other_client": make_user(db, Role.CLIENT),
        "operator": operator,
        "req": make_request(db, client_user, status=S.IN_PROGRESS, episodes_requested=2),
    }


def _assign(client, ctx, ids, user=None):
    return client.post(
        f"/requests/{ctx['req'].id}/assignments",
        json={"episode_ids": ids},
        headers=auth(user or ctx["operator"]),
    )


def test_operator_assigns_good_and_usable_episodes(client, db, ctx):
    good = make_episode(db, Quality.GOOD)
    usable = make_episode(db, Quality.USABLE)
    res = _assign(client, ctx, [good.episode_id, usable.episode_id.lower()])  # ids normalised
    assert res.status_code == 200
    body = res.json()
    assert body["episodes_assigned"] == 2
    assert {a["episode"]["episode_id"] for a in body["items"]} == {
        good.episode_id,
        usable.episode_id,
    }


def test_bad_quality_episode_cannot_be_assigned(client, db, ctx):
    bad = make_episode(db, Quality.BAD)
    good = make_episode(db, Quality.GOOD)
    res = _assign(client, ctx, [good.episode_id, bad.episode_id])
    assert res.status_code == 422
    assert bad.episode_id in res.json()["detail"]
    # All-or-nothing: the good one was not assigned either.
    assert db.query(Assignment).count() == 0


def test_episode_cannot_belong_to_two_requests(client, db, ctx):
    ep = make_episode(db)
    other = make_request(db, ctx["other_client"], status=S.IN_PROGRESS)
    assign(db, other, ep, ctx["operator"])
    res = _assign(client, ctx, [ep.episode_id])
    assert res.status_code == 409
    assert ep.episode_id in res.json()["detail"]


def test_database_enforces_one_request_per_episode(db, ctx):
    """Even if the service check were bypassed (e.g. a race), the UNIQUE constraint holds."""
    ep = make_episode(db)
    other = make_request(db, ctx["other_client"], status=S.IN_PROGRESS)
    assign(db, ctx["req"], ep, ctx["operator"])
    with pytest.raises(IntegrityError):
        assign(db, other, ep, ctx["operator"])


def test_reassigning_to_same_request_is_idempotent(client, db, ctx):
    ep = make_episode(db)
    assert _assign(client, ctx, [ep.episode_id]).json()["episodes_assigned"] == 1
    assert _assign(client, ctx, [ep.episode_id]).json()["episodes_assigned"] == 1


def test_unknown_episode_is_404(client, ctx):
    assert _assign(client, ctx, ["EP-NOPE"]).status_code == 404


@pytest.mark.parametrize("status", [S.SUBMITTED, S.DELIVERED, S.ACCEPTED, S.REJECTED])
def test_assignments_are_frozen_outside_in_progress(client, db, ctx, status):
    ctx["req"].status = status
    db.flush()
    assert _assign(client, ctx, [make_episode(db).episode_id]).status_code == 409


def test_clients_cannot_assign(client, db, ctx):
    res = _assign(client, ctx, [make_episode(db).episode_id], user=ctx["client"])
    assert res.status_code == 403


def test_unassign_frees_the_episode(client, db, ctx):
    ep = make_episode(db)
    assign(db, ctx["req"], ep, ctx["operator"])
    url = f"/requests/{ctx['req'].id}/assignments/{ep.episode_id}"
    assert client.delete(url, headers=auth(ctx["operator"])).status_code == 204
    assert client.delete(url, headers=auth(ctx["operator"])).status_code == 404
    other = make_request(db, ctx["other_client"], status=S.IN_PROGRESS)
    assign(db, other, ep, ctx["operator"])  # now free for another request


def test_owner_can_view_assignments_but_other_clients_cannot(client, db, ctx):
    assign(db, ctx["req"], make_episode(db), ctx["operator"])
    url = f"/requests/{ctx['req'].id}/assignments"
    assert client.get(url, headers=auth(ctx["client"])).json()["episodes_assigned"] == 1
    assert client.get(url, headers=auth(ctx["other_client"])).status_code == 404


def test_episode_list_filters(client, db, ctx):
    make_episode(db, Quality.GOOD, task_name="pick cup")
    make_episode(db, Quality.BAD, task_name="pick cup")
    make_episode(db, Quality.GOOD, task_name="fold towel")
    taken = make_episode(db, Quality.USABLE, task_name="pick cup")
    assign(db, ctx["req"], taken, ctx["operator"])
    h = auth(ctx["operator"])

    def ids(qs):
        return client.get(f"/episodes?{qs}", headers=h).json()["total"]

    assert ids("task_name=Pick%20Cup") == 3
    assert ids("task_name=pick%20cup&quality=good") == 1
    assert ids("task_name=pick%20cup&available=true") == 1  # excludes bad + already assigned


def test_clients_cannot_browse_episodes(client, ctx):
    assert client.get("/episodes", headers=auth(ctx["client"])).status_code == 403
