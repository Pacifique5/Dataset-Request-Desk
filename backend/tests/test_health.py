from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app


def test_health_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "database": "ok"}
    assert "x-request-id" in res.headers


def test_health_reports_db_down_as_503(client):
    class DownSession:
        def execute(self, *_):
            raise OperationalError("SELECT 1", {}, Exception("db down"))

    app.dependency_overrides[get_db] = lambda: DownSession()
    res = client.get("/health")
    assert res.status_code == 503
    assert res.json()["database"] == "unavailable"
