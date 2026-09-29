from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import DbSession, StaffUser
from app.core.errors import BusinessRuleError
from app.schemas.analytics import AnalyticsOut
from app.services.analytics import build_report

router = APIRouter(prefix="/analytics", tags=["analytics"])

MAX_RANGE_DAYS = 366


@router.get("", response_model=AnalyticsOut)
def analytics(
    db: DbSession,
    _: StaffUser,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
) -> AnalyticsOut:
    """Defaults to the last 30 days. Both dates are inclusive (UTC days)."""
    date_to = date_to or date.today()
    date_from = date_from or date_to - timedelta(days=29)
    if date_from > date_to:
        raise BusinessRuleError("'from' must be on or before 'to'")
    if (date_to - date_from).days + 1 > MAX_RANGE_DAYS:
        raise BusinessRuleError(f"Date range is limited to {MAX_RANGE_DAYS} days")
    return build_report(db, date_from, date_to)
