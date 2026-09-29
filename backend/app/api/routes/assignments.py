from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession, StaffUser
from app.models import User
from app.schemas.episode import AssignIn, AssignmentList, AssignmentOut, EpisodeOut
from app.services import assignments as svc

router = APIRouter(prefix="/requests/{request_id}/assignments", tags=["assignments"])


def _list(db: DbSession, user: User, request_id: int) -> AssignmentList:
    req, rows = svc.list_assignments(db, user, request_id)
    return AssignmentList(
        request_id=req.id,
        episodes_requested=req.episodes_requested,
        episodes_assigned=len(rows),
        items=[
            AssignmentOut(
                episode=EpisodeOut.model_validate(ep).model_copy(
                    update={"assigned_request_id": req.id}
                ),
                assigned_at=a.assigned_at,
                assigned_by_id=a.assigned_by_id,
            )
            for a, ep in rows
        ],
    )


@router.get("", response_model=AssignmentList)
def list_(request_id: int, db: DbSession, user: CurrentUser) -> AssignmentList:
    """Staff, and the owning client (to review the delivery), can see assignments."""
    return _list(db, user, request_id)


@router.post("", response_model=AssignmentList)
def assign(request_id: int, body: AssignIn, db: DbSession, user: StaffUser) -> AssignmentList:
    svc.assign_episodes(db, user, request_id, body.episode_ids)
    db.commit()
    return _list(db, user, request_id)


@router.delete("/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign(request_id: int, episode_id: str, db: DbSession, user: StaffUser) -> None:
    svc.unassign_episode(db, user, request_id, episode_id)
    db.commit()
