from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSession

router = APIRouter(tags=["health"])


@router.get("/health")
def health(response: Response, db: DbSession) -> dict[str, str]:
    """Liveness + readiness: returns 503 if the database is unreachable."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "degraded", "database": "unavailable"}
    return {"status": "ok", "database": "ok"}
