from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser
from app.realtime import broadcaster, event_stream

router = APIRouter(tags=["events"])


@router.get("/events")
async def events(request: Request, user: CurrentUser) -> StreamingResponse:
    """Server-Sent Events: request created / status changed / assignments changed.

    Authenticated like any other endpoint (the cookie is sent by EventSource). Clients
    only receive events for their own requests.
    """
    return StreamingResponse(
        event_stream(broadcaster, user.id, user.role, request.is_disconnected),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
