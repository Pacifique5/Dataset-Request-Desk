import codecs

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.deps import DbSession, StaffUser
from app.schemas.episode import ImportReportOut
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
