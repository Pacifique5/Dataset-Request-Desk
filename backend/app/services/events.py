"""Publishing request events for real-time clients.

Events go through PostgreSQL NOTIFY inside the *same transaction* as the change, so
they are delivered only if the change commits (a rolled-back change never produces a
phantom event), and every API process that LISTENs receives them — this works with
several replicas without extra infrastructure.
"""

import json
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DatasetRequest

CHANNEL = "request_events"
EventKind = Literal["created", "status_changed", "assignments_changed"]


def publish_request_event(db: Session, req: DatasetRequest, kind: EventKind, actor_id: int) -> None:
    payload = json.dumps(
        {
            "kind": kind,
            "actor_id": actor_id,  # lets the UI skip notifying you about your own change
            "request_id": req.id,
            "client_id": req.client_id,
            "status": req.status.value,
            "task_name": req.task_name,
        }
    )
    db.execute(select(func.pg_notify(CHANNEL, payload)))
