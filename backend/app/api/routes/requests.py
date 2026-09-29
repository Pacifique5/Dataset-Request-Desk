from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import ClientUser, CurrentUser, DbSession
from app.models import DatasetRequest, RequestStatus, User
from app.schemas.request import (
    RequestCreate,
    RequestDetail,
    RequestOut,
    RequestPage,
    StatusEventOut,
    TransitionIn,
    UserBrief,
)
from app.services import requests as svc
from app.services.workflow import next_statuses

router = APIRouter(prefix="/requests", tags=["requests"])


def _out(req: DatasetRequest, assigned: int, user: User) -> RequestOut:
    return RequestOut(
        id=req.id,
        client=UserBrief.model_validate(req.client),
        task_name=req.task_name,
        episodes_requested=req.episodes_requested,
        episodes_assigned=assigned,
        deadline=req.deadline,
        notes=req.notes,
        status=req.status,
        created_at=req.created_at,
        updated_at=req.updated_at,
        allowed_transitions=next_statuses(req.status, user.role),
    )


def _detail(db: DbSession, req: DatasetRequest, user: User) -> RequestDetail:
    db.refresh(req, ["events"])
    base = _out(req, svc.count_assigned(db, req.id), user)
    return RequestDetail(
        **base.model_dump(),
        events=[StatusEventOut.model_validate(e) for e in req.events],
    )


@router.post("", response_model=RequestDetail, status_code=status.HTTP_201_CREATED)
def create(body: RequestCreate, db: DbSession, client: ClientUser) -> RequestDetail:
    req = svc.create_request(db, client, body)
    db.commit()
    return _detail(db, req, client)


@router.get("", response_model=RequestPage)
def list_(
    db: DbSession,
    user: CurrentUser,
    status_: Annotated[RequestStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> RequestPage:
    rows, total = svc.list_requests(db, user, status=status_, limit=limit, offset=offset)
    return RequestPage(
        items=[_out(r.request, r.episodes_assigned, user) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{request_id}", response_model=RequestDetail)
def get(request_id: int, db: DbSession, user: CurrentUser) -> RequestDetail:
    return _detail(db, svc.get_request(db, user, request_id), user)


@router.post("/{request_id}/transitions", response_model=RequestDetail)
def transition(
    request_id: int, body: TransitionIn, db: DbSession, user: CurrentUser
) -> RequestDetail:
    req = svc.change_status(db, user, request_id, body.to_status, body.note)
    db.commit()
    return _detail(db, req, user)
