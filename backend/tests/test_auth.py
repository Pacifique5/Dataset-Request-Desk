from app.models import Role
from tests.factories import auth, make_user


def test_login_sets_httponly_cookie_and_me_works(client, db):
    make_user(db, Role.OPERATOR, email="op@test.local")
    res = client.post("/auth/login", json={"email": "OP@test.local ", "password": "password"})
    assert res.status_code == 200
    assert res.json()["role"] == "operator"
    cookie = res.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert "password_hash" not in res.json()

    me = client.get("/auth/me")  # TestClient re-sends the cookie
    assert me.status_code == 200
    assert me.json()["email"] == "op@test.local"


def test_wrong_password_and_unknown_email_give_same_401(client, db):
    make_user(db, email="c@test.local")
    wrong = client.post("/auth/login", json={"email": "c@test.local", "password": "nope"})
    unknown = client.post("/auth/login", json={"email": "who@test.local", "password": "nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_deactivated_user_cannot_login_or_use_existing_token(client, db):
    user = make_user(db, email="gone@test.local")
    headers = auth(user)
    user.is_active = False
    db.flush()
    assert (
        client.post(
            "/auth/login", json={"email": "gone@test.local", "password": "password"}
        ).status_code
        == 401
    )
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_me_requires_authentication(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_logout_clears_cookie(client, db):
    make_user(db, email="x@test.local")
    client.post("/auth/login", json={"email": "x@test.local", "password": "password"})
    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401


def test_repeated_failures_are_throttled_even_with_the_right_password(client, db):
    make_user(db, email="victim@test.local")
    bad = {"email": "victim@test.local", "password": "wrong"}
    for _ in range(5):
        assert client.post("/auth/login", json=bad).status_code == 401
    res = client.post("/auth/login", json={"email": "victim@test.local", "password": "password"})
    assert res.status_code == 429
    assert int(res.headers["retry-after"]) > 0
    # Other accounts are unaffected.
    make_user(db, email="other@test.local")
    ok = client.post("/auth/login", json={"email": "other@test.local", "password": "password"})
    assert ok.status_code == 200


def test_successful_login_resets_the_failure_count(client, db):
    make_user(db, email="typo@test.local")
    for _ in range(4):
        client.post("/auth/login", json={"email": "typo@test.local", "password": "wrong"})
    good = {"email": "typo@test.local", "password": "password"}
    assert client.post("/auth/login", json=good).status_code == 200
    for _ in range(4):
        client.post("/auth/login", json={"email": "typo@test.local", "password": "wrong"})
    assert client.post("/auth/login", json=good).status_code == 200
