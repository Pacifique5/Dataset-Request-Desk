"""Two operators race to assign the same episode to different requests.

Unlike the other tests this one commits for real (each thread needs its own
connection), so it cleans up after itself.
"""

import threading

import pytest
from sqlalchemy import delete, func, select

from app.core.errors import ConflictError
from app.db.session import SessionLocal
from app.models import Assignment, DatasetRequest, Episode, RequestStatus, Role, User
from app.services.assignments import assign_episodes
from tests.factories import make_episode, make_request, make_user


@pytest.fixture
def committed():
    with SessionLocal.begin() as s:
        op1, op2 = make_user(s, Role.OPERATOR), make_user(s, Role.OPERATOR)
        cli = make_user(s, Role.CLIENT)
        r1 = make_request(s, cli, status=RequestStatus.IN_PROGRESS)
        r2 = make_request(s, cli, status=RequestStatus.IN_PROGRESS)
        ep = make_episode(s)
        ids = {
            "ops": [op1.id, op2.id],
            "reqs": [r1.id, r2.id],
            "client": cli.id,
            "episode": ep.episode_id,
            "episode_pk": ep.id,
        }
    yield ids
    with SessionLocal.begin() as s:
        s.execute(delete(Assignment).where(Assignment.request_id.in_(ids["reqs"])))
        s.execute(delete(DatasetRequest).where(DatasetRequest.id.in_(ids["reqs"])))
        s.execute(delete(Episode).where(Episode.id == ids["episode_pk"]))
        s.execute(delete(User).where(User.id.in_([*ids["ops"], ids["client"]])))


def test_concurrent_assignment_of_same_episode_has_exactly_one_winner(committed):
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def worker(op_id: int, req_id: int) -> None:
        with SessionLocal() as s:
            user = s.get(User, op_id)
            barrier.wait()
            try:
                assign_episodes(s, user, req_id, [committed["episode"]])
                s.commit()
                outcomes.append("ok")
            except ConflictError:
                s.rollback()
                outcomes.append("conflict")

    threads = [
        threading.Thread(target=worker, args=(op, req))
        for op, req in zip(committed["ops"], committed["reqs"], strict=True)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert sorted(outcomes) == ["conflict", "ok"]
    with SessionLocal() as s:
        n = s.scalar(select(func.count()).where(Assignment.episode_id == committed["episode_pk"]))
    assert n == 1
