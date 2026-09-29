import pytest

from app.models import Role
from tests.factories import auth, make_user


@pytest.fixture
def admin(db):
    return make_user(db, Role.ADMIN)


def _new(**o):
    return {
        "email": "new@test.local",
        "name": "New",
        "password": "longenough",
        "role": "client",
    } | o


def test_admin_creates_user_who_can_then_log_in(client, admin):
    res = client.post("/users", json=_new(), headers=auth(admin))
    assert res.status_code == 201
    assert "password" not in res.text
    login = client.post("/auth/login", json={"email": "new@test.local", "password": "longenough"})
    assert login.status_code == 200


def test_duplicate_email_is_409_case_insensitive(client, admin):
    client.post("/users", json=_new(), headers=auth(admin))
    assert (
        client.post("/users", json=_new(email="NEW@test.local"), headers=auth(admin)).status_code
        == 409
    )


@pytest.mark.parametrize(
    "override", [{"password": "short"}, {"email": "not-an-email"}, {"role": "root"}]
)
def test_invalid_user_payload_is_422(client, admin, override):
    assert client.post("/users", json=_new(**override), headers=auth(admin)).status_code == 422


def test_admin_changes_role_and_deactivates(client, db, admin):
    target = make_user(db, Role.CLIENT)
    res = client.patch(f"/users/{target.id}", json={"role": "operator"}, headers=auth(admin))
    assert res.json()["role"] == "operator"
    res = client.patch(f"/users/{target.id}", json={"is_active": False}, headers=auth(admin))
    assert res.json()["is_active"] is False
    assert client.get("/auth/me", headers=auth(target)).status_code == 401


@pytest.mark.parametrize("change", [{"is_active": False}, {"role": "operator"}])
def test_admin_cannot_lock_themselves_out(client, admin, change):
    assert client.patch(f"/users/{admin.id}", json=change, headers=auth(admin)).status_code == 422


@pytest.mark.parametrize("role", [Role.OPERATOR, Role.CLIENT])
def test_only_admins_manage_users(client, db, role):
    user = make_user(db, role)
    h = auth(user)
    assert client.get("/users", headers=h).status_code == 403
    assert client.post("/users", json=_new(), headers=h).status_code == 403
    assert client.patch(f"/users/{user.id}", json={"role": "admin"}, headers=h).status_code == 403
