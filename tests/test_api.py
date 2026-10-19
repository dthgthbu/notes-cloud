import os
import tempfile


_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DB_PATH"] = _tmp.name
os.environ["SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


import pytest

@pytest.fixture(autouse=True)
def _clean_cookies():
    client.cookies.clear()
    yield
    client.cookies.clear()

def test_register_ok():
    r = client.post("/api/register", json={"username": "alice", "password": "123456"})
    assert r.status_code == 200
    assert r.json()["username"] == "alice"


def test_register_short_password():
    r = client.post("/api/register", json={"username": "bob", "password": "12"})
    assert r.status_code == 400


def test_register_duplicate():
    client.post("/api/register", json={"username": "carl", "password": "123456"})
    r = client.post("/api/register", json={"username": "carl", "password": "654321"})
    assert r.status_code == 400


def test_login_wrong_password():
    client.post("/api/register", json={"username": "dan", "password": "123456"})
    client.post("/api/logout")
    r = client.post("/api/login", json={"username": "dan", "password": "wrong"})
    assert r.status_code == 401


def test_login_ok():
    client.post("/api/register", json={"username": "eve", "password": "123456"})
    client.post("/api/logout")
    r = client.post("/api/login", json={"username": "eve", "password": "123456"})
    assert r.status_code == 200


def test_me_requires_auth():
    r = client.get("/api/me")
    assert r.status_code == 401



def test_notes_require_auth():
    assert client.get("/api/notes").status_code == 401
    assert client.post("/api/notes", json={"title": "a", "body": "b"}).status_code == 401
    assert client.delete("/api/notes/1").status_code == 401


def test_create_and_list_notes():
    client.post("/api/register", json={"username": "frank", "password": "123456"})
    r = client.post("/api/notes", json={"title": "Привет", "body": "мир"})
    assert r.status_code == 200
    notes = client.get("/api/notes").json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Привет"


def test_delete_note():
    client.post("/api/register", json={"username": "gina", "password": "123456"})
    client.post("/api/notes", json={"title": "t", "body": "b"})
    nid = client.get("/api/notes").json()[0]["id"]
    assert client.delete(f"/api/notes/{nid}").status_code == 200
    assert client.get("/api/notes").json() == []


def test_isolation_between_users():
    r = client.post("/api/register", json={"username": "user1", "password": "123456"})
    print("DEBUG register:", r.status_code, r.json())
    r = client.post("/api/notes", json={"title": "secret", "body": "top"})
    print("DEBUG create:", r.status_code, r.json())
    r = client.get("/api/notes")
    print("DEBUG get:", r.status_code, r.json())
    note_id = r.json()[0]["id"]
    client.post("/api/logout")

    client.post("/api/register", json={"username": "user2", "password": "123456"})
    assert client.get("/api/notes").json() == []
    client.delete(f"/api/notes/{note_id}")
    client.post("/api/logout")

    client.post("/api/login", json={"username": "user1", "password": "123456"})
    assert len(client.get("/api/notes").json()) == 1


def test_contract_me_shape():
    client.post("/api/register", json={"username": "shape", "password": "123456"})
    body = client.get("/api/me").json()
    assert set(body.keys()) == {"id", "username"}


def test_contract_note_shape():
    client.post("/api/register", json={"username": "shape2", "password": "123456"})
    client.post("/api/notes", json={"title": "t", "body": "b"})
    note = client.get("/api/notes").json()[0]
    assert set(note.keys()) == {"id", "title", "body", "created_at"}


def test_contract_error_shape():
    r = client.post("/api/register", json={"username": "x", "password": "123456"})
    assert r.status_code == 400
    assert set(r.json().keys()) == {"detail"}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}



def test_count_requires_auth():
    r = client.get("/api/notes/count")
    assert r.status_code == 401


def test_count_empty():
    client.post("/api/register", json={"username": "count1", "password": "123456"})
    r = client.get("/api/notes/count")
    assert r.status_code == 200
    assert r.json() == {"count": 0}


def test_count_with_notes():
    client.post("/api/register", json={"username": "count2", "password": "123456"})
    client.post("/api/notes", json={"title": "a", "body": "b"})
    client.post("/api/notes", json={"title": "c", "body": "d"})
    r = client.get("/api/notes/count")
    assert r.status_code == 200
    assert r.json() == {"count": 2}
