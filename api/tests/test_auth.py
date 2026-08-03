from app.main import app
from fastapi.testclient import TestClient
import time

client = TestClient(app)
PASSWORD = "secret123"

def _register():
    email = f"fit{int(time.time()*1000)}-{_register.n}@example.com"
    _register.n += 1
    r = client.post("/api/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return r.json(), email
_register.n = 0

def test_register_login_flow():
    data, email = _register()
    assert data["email"] == email
    assert data["token"]
    r2 = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert r2.status_code == 200
    assert r2.json()["token"]

def test_login_wrong_password():
    _, email = _register()
    r = client.post("/api/auth/login", json={"email": email, "password": "wrongpass"})
    assert r.status_code == 401

def test_duplicate_register():
    data, email = _register()
    r = client.post("/api/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 409

def test_me_requires_token():
    r = client.get("/api/auth/me")
    assert r.status_code == 401

def test_me_with_token():
    data, email = _register()
    h = {"Authorization": f"Bearer {data['token']}"}
    r = client.get("/api/auth/me", headers=h)
    assert r.status_code == 200
    assert r.json()["email"] == email
    assert r.json()["profile"] is None

def test_profile_save_and_read():
    data, _ = _register()
    h = {"Authorization": f"Bearer {data['token']}"}
    profile = {
        "sex": "female", "age": 27, "height_cm": 165, "weight_kg": 55,
        "body_fat": 22, "activity_level": "moderate", "goal": "cut",
        "allergies": ["花生"], "preferred_cuisines": ["西式", "日式"],
    }
    r = client.put("/api/me/profile", json=profile, headers=h)
    assert r.status_code == 200
    me = client.get("/api/auth/me", headers=h).json()
    assert me["profile"]["goal"] == "cut"
    assert me["profile"]["allergies"] == ["花生"]

def test_favorites_sync():
    data, _ = _register()
    h = {"Authorization": f"Bearer {data['token']}"}
    client.put("/api/me/favorites", json={"ids": ["a", "b"]}, headers=h)
    assert client.get("/api/me/favorites", headers=h).json()["ids"] == ["a", "b"]
    client.put("/api/me/favorites", json={"ids": ["b"]}, headers=h)
    assert client.get("/api/me/favorites", headers=h).json()["ids"] == ["b"]

def test_diary_sync():
    data, _ = _register()
    h = {"Authorization": f"Bearer {data['token']}"}
    client.put("/api/me/diary", json={"date": "2026-08-04", "items": [{"name": "鸡蛋", "kcal": 139}]}, headers=h)
    d = client.get("/api/me/diary", headers=h).json()
    assert d["2026-08-04"][0]["name"] == "鸡蛋"

def test_logout_invalidates_token():
    data, _ = _register()
    h = {"Authorization": f"Bearer {data['token']}"}
    client.post("/api/auth/logout", headers=h)
    assert client.get("/api/auth/me", headers=h).status_code == 401
