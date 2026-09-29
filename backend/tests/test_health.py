from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app


class _OkSession:
    def execute(self, *_):
        return None


class _DownSession:
    def execute(self, *_):
        raise OperationalError("SELECT 1", {}, Exception("db down"))


def test_health_ok(client):
    app.dependency_overrides[get_db] = lambda: _OkSession()
    try:
        res = client.get("/health")
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "database": "ok"}
    assert "x-request-id" in res.headers


def test_health_reports_db_down_as_503(client):
    app.dependency_overrides[get_db] = lambda: _DownSession()
    try:
        res = client.get("/health")
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 503
    assert res.json()["database"] == "unavailable"
