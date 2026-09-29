"""In-process fan-out of request events to Server-Sent Events subscribers.

One background task per API process holds a single LISTEN connection and copies each
notification into the queue of every connected SSE client. Clients never hold a
database connection of their own.
"""

import asyncio
import contextlib
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import psycopg
from sqlalchemy.engine import make_url

from app.models import Role
from app.services.events import CHANNEL

logger = logging.getLogger("app.realtime")

Event = dict[str, Any]
HEARTBEAT_SECONDS = 15.0
QUEUE_SIZE = 100


def visible_to(event: Event, user_id: int, role: Role) -> bool:
    """Staff see every request's events; clients only their own."""
    return role is not Role.CLIENT or event.get("client_id") == user_id


class Broadcaster:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[Event]] = set()
        self._task: asyncio.Task[None] | None = None

    # --- producer side -----------------------------------------------------------

    def publish(self, event: Event) -> None:
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # A stalled client must not block everyone else; it will refetch
                # on its next event anyway.
                logger.warning("realtime.subscriber_queue_full")

    async def _listen(self, dsn: str) -> None:
        while True:
            try:
                async with await psycopg.AsyncConnection.connect(dsn, autocommit=True) as conn:
                    await conn.execute(f"LISTEN {CHANNEL}")
                    logger.info("realtime.listening", extra={"channel": CHANNEL})
                    async for note in conn.notifies():
                        self.publish(json.loads(note.payload))
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("realtime.listener_failed; reconnecting in 2s")
                await asyncio.sleep(2)

    def start(self, database_url: str) -> None:
        dsn = (
            make_url(database_url)
            .set(drivername="postgresql")
            .render_as_string(hide_password=False)
        )
        self._task = asyncio.create_task(self._listen(dsn))

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    # --- consumer side -----------------------------------------------------------

    @contextlib.contextmanager
    def subscribe(self):
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=QUEUE_SIZE)
        self._subscribers.add(queue)
        try:
            yield queue
        finally:
            self._subscribers.discard(queue)


broadcaster = Broadcaster()


async def event_stream(
    source: Broadcaster,
    user_id: int,
    role: Role,
    is_disconnected: Callable[[], Awaitable[bool]],
    heartbeat: float = HEARTBEAT_SECONDS,
) -> AsyncIterator[str]:
    """SSE wire format: `data: <json>\\n\\n` per event, `: ping` comments to keep proxies open."""
    with source.subscribe() as queue:
        yield "retry: 3000\n\n"
        while not await is_disconnected():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=heartbeat)
            except asyncio.TimeoutError:  # builtin TimeoutError only from 3.11
                yield ": ping\n\n"
                continue
            if visible_to(event, user_id, role):
                yield f"data: {json.dumps(event)}\n\n"
