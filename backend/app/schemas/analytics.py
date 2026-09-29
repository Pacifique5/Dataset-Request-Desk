from datetime import date

from pydantic import BaseModel

from app.models import RequestStatus


class RobotDayCount(BaseModel):
    day: date
    robot_id: str
    episodes: int


class Fulfilment(BaseModel):
    requests_by_status: dict[RequestStatus, int]
    delivered_sample_size: int
    median_submitted_to_delivered_seconds: float | None


class TaskCount(BaseModel):
    task_name: str
    good_episodes: int


class AnalyticsOut(BaseModel):
    date_from: date
    date_to: date
    episodes_per_day_per_robot: list[RobotDayCount]
    fulfilment: Fulfilment
    top_tasks_by_good_episodes: list[TaskCount]
