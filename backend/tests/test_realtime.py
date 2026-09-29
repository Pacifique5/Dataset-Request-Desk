"""Real-time events: NOTIFY is transactional, and the SSE stream filters per user."""

import asyncio
import json

import psycopg
import pytest
from sqlalchemy import delete
from sqlalchemy.engine import make_url

from app.db.session import SessionLocal
from app.models import DatasetRequest, RequestStatusEvent, Role, User
from app.realtime import Broadcaster, event_stream, visible_to
from app.schemas.request import RequestCreate
from app.services.events import CHANNEL
from app.services.requests import create_request
from tests.conftest import TEST_DATABASE_URL
from tests.factories import make_user

DSN = make_url(TEST_DATABASE_URL).set(drivername="postgresql").render_as_string(False)


def test_visibility_rules():
    event = {"client_id": 7}
    assert visible_to(event, 7, Role.CLIENT)
    assert not visible_to(event, 8, Role.CLIENT)
    assert visible_to(event, 99, Role.OPERATOR)
    assert visible_to(event, 99, Role.ADMIN)


def test_stream_formats_events_and_filters_other_clients():
    async def scenario() -> list[str]:
        source = Broadcaster()
        stream = event_stream(source, user_id=1, role=Role.CLIENT, is_disconnected=_never)
        chunks = [await stream.__anext__()]  # retry hint; subscribes the queue
        source.publish({"request_id": 10, "client_id": 2})  # someone else's
        source.publish({"request_id": 11, "client_id": 1})  # mine
        chunks.append(await stream.__anext__())
        await stream.aclose()
        return chunks

    retry, data = asyncio.run(scenario())
    assert retry.startswith("retry:")
    assert json.loads(data.removeprefix("data: "))["request_id"] == 11


def test_stream_sends_heartbeats_when_idle():
    async def scenario() -> str:
        stream = event_stream(Broadcaster(), 1, Role.OPERATOR, _never, heartbeat=0.01)
        await stream.__anext__()
        chunk = await stream.__anext__()
        await stream.aclose()
        return chunk

    assert asyncio.run(scenario()) == ": ping\n\n"


async def _never() -> bool:
    return False


@pytest.fixture
def listener():
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute(f"LISTEN {CHANNEL}")
        yield conn


def _drain(conn) -> list[dict]:
    return [json.loads(n.payload) for n in conn.notifies(timeout=0.5, stop_after=5)]


def test_notification_is_delivered_only_after_commit(listener):
    with SessionLocal() as s:
        client = make_user(s, Role.CLIENT)
        body = RequestCreate(task_name="pick cup", episodes_requested=1, deadline="2099-01-01")
        req = create_request(s, client, body)
        assert _drain(listener) == []  # not visible before commit
        s.commit()
        req_id, client_id = req.id, client.id

    events = _drain(listener)
    try:
        assert [(e["kind"], e["request_id"], e["client_id"], e["actor_id"]) for e in events] == [
            ("created", req_id, client_id, client_id)
        ]
    finally:
        with SessionLocal.begin() as s:
            s.execute(delete(RequestStatusEvent).where(RequestStatusEvent.request_id == req_id))
            s.execute(delete(DatasetRequest).where(DatasetRequest.id == req_id))
            s.execute(delete(User).where(User.id == client_id))


def test_rolled_back_change_emits_nothing(listener):
    with SessionLocal() as s:
        client = make_user(s, Role.CLIENT)
        body = RequestCreate(task_name="pick cup", episodes_requested=1, deadline="2099-01-01")
        create_request(s, client, body)
        s.rollback()
    assert _drain(listener) == []


def test_events_endpoint_requires_authentication(client):
    assert client.get("/events").status_code == 401
