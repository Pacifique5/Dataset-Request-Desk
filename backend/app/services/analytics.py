"""Reporting queries. All aggregation happens in PostgreSQL; Python only shapes rows.

Date range semantics: [date_from 00:00 UTC, date_to + 1 day 00:00 UTC), i.e. both
dates inclusive, days bucketed in UTC.

- Episodes per day per robot: range scan on ix_episodes_recorded_at_robot.
- Top tasks by good episodes: range scan on the partial index
  ix_episodes_good_recorded_task (only quality='good' rows are in it).
- Fulfilment: requests *created* in the range. Time-to-deliver uses each request's
  FIRST delivery event, so rework after a rejection doesn't inflate the median.
"""

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import Date, cast, desc, func, select
from sqlalchemy.orm import Session

from app.models import DatasetRequest, Episode, Quality, RequestStatus, RequestStatusEvent
from app.schemas.analytics import AnalyticsOut, Fulfilment, RobotDayCount, TaskCount

TOP_N_TASKS = 5


def _bounds(date_from: date, date_to: date) -> tuple[datetime, datetime]:
    start = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
    end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return start, end


def episodes_per_day_per_robot(db: Session, start: datetime, end: datetime) -> list[RobotDayCount]:
    day = cast(func.timezone("UTC", Episode.recorded_at), Date).label("day")
    rows = db.execute(
        select(day, Episode.robot_id, func.count().label("n"))
        .where(Episode.recorded_at >= start, Episode.recorded_at < end)
        .group_by(day, Episode.robot_id)
        .order_by(day, Episode.robot_id)
    ).all()
    return [RobotDayCount(day=d, robot_id=r, episodes=n) for d, r, n in rows]


def fulfilment(db: Session, start: datetime, end: datetime) -> Fulfilment:
    in_range = (DatasetRequest.created_at >= start) & (DatasetRequest.created_at < end)

    by_status = dict(
        db.execute(
            select(DatasetRequest.status, func.count())
            .where(in_range)
            .group_by(DatasetRequest.status)
        ).all()
    )

    first_delivery = (
        select(
            RequestStatusEvent.request_id,
            func.min(RequestStatusEvent.changed_at).label("delivered_at"),
        )
        .where(RequestStatusEvent.to_status == RequestStatus.DELIVERED)
        .group_by(RequestStatusEvent.request_id)
        .subquery()
    )
    seconds = func.extract("epoch", first_delivery.c.delivered_at - DatasetRequest.created_at)
    sample, median = db.execute(
        select(func.count(), func.percentile_cont(0.5).within_group(seconds))
        .select_from(DatasetRequest)
        .join(first_delivery, first_delivery.c.request_id == DatasetRequest.id)
        .where(in_range)
    ).one()

    return Fulfilment(
        requests_by_status={s: by_status.get(s, 0) for s in RequestStatus},
        delivered_sample_size=sample,
        median_submitted_to_delivered_seconds=float(median) if median is not None else None,
    )


def top_tasks_by_good_episodes(db: Session, start: datetime, end: datetime) -> list[TaskCount]:
    n = func.count().label("n")
    rows = db.execute(
        select(Episode.task_name, n)
        .where(
            Episode.quality == Quality.GOOD,
            Episode.recorded_at >= start,
            Episode.recorded_at < end,
        )
        .group_by(Episode.task_name)
        .order_by(desc(n), Episode.task_name)  # deterministic tie-break
        .limit(TOP_N_TASKS)
    ).all()
    return [TaskCount(task_name=t, good_episodes=c) for t, c in rows]


def build_report(db: Session, date_from: date, date_to: date) -> AnalyticsOut:
    start, end = _bounds(date_from, date_to)
    return AnalyticsOut(
        date_from=date_from,
        date_to=date_to,
        episodes_per_day_per_robot=episodes_per_day_per_robot(db, start, end),
        fulfilment=fulfilment(db, start, end),
        top_tasks_by_good_episodes=top_tasks_by_good_episodes(db, start, end),
    )
