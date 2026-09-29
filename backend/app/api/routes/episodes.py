import codecs
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, UploadFile, status

from app.api.deps import DbSession, StaffUser
from app.models import Quality
from app.schemas.episode import EpisodeOut, EpisodePage, ImportReportOut
from app.services.assignments import EpisodeFilters, list_episodes
from app.services.episode_import import InvalidCsvError, import_episodes

router = APIRouter(prefix="/episodes", tags=["episodes"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@router.post("/import", response_model=ImportReportOut)
def import_csv(file: UploadFile, db: DbSession, _: StaffUser) -> ImportReportOut:
    """Import an episode CSV export. Safe to re-run: existing episodes are skipped."""
    if file.size is not None and file.size > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")

    # Stream-decode the upload; utf-8-sig tolerates a BOM from spreadsheet exports.
    stream = codecs.getreader("utf-8-sig")(file.file)
    try:
        report = import_episodes(db, stream)
    except InvalidCsvError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except UnicodeDecodeError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "File is not UTF-8 text") from exc
    db.commit()
    return ImportReportOut.model_validate(report.as_dict())


@router.get("", response_model=EpisodePage)
def list_(
    db: DbSession,
    _: StaffUser,
    task_name: str | None = None,
    quality: Quality | None = None,
    robot_id: str | None = None,
    available: bool = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EpisodePage:
    """Browse episodes. `available=true` = assignable (good/usable) and not yet assigned."""
    rows, total = list_episodes(
        db,
        EpisodeFilters(task_name, quality, robot_id, available_only=available),
        limit=limit,
        offset=offset,
    )
    return EpisodePage(
        items=[
            EpisodeOut.model_validate(ep).model_copy(update={"assigned_request_id": rid})
            for ep, rid in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
