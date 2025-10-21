# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app, engine, init_db
from sqlmodel import Session, select
from models import sha256_hex

client = TestClient(app)

@pytest.fixture(autouse=True)
def prepare_db(tmp_path, monkeypatch):
    # use a temporary sqlite file for tests
    dbfile = tmp_path / "test.db"
    url = f"sqlite:///{dbfile}"
    from sqlmodel import create_engine
    eng = create_engine(url, connect_args={"check_same_thread": False})
    # monkeypatch engine in main module
    import main
    main.engine = eng
    main.init_db()
    yield
    # cleanup handled by tmp_path

def test_create_and_get_string():
    payload = {"value": "Level"}  # palindrome case-insensitively
    r = client.post("/strings", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["value"] == "Level"
    assert data["properties"]["is_palindrome"] is True
    sha = data["properties"]["sha256_hash"]

    # GET by path (URL-encode if needed)
    r2 = client.get("/strings/Level")
    assert r2.status_code == 200
    assert r2.json()["id"] == sha

def test_conflict_create():
    payload = {"value": "abc"}
    r = client.post("/strings", json=payload)
    assert r.status_code == 201
    r2 = client.post("/strings", json=payload)
    assert r2.status_code == 409

def test_list_filters():
    client.post("/strings", json={"value": "aba"})
    client.post("/strings", json={"value": "hello world"})
    r = client.get("/strings?is_palindrome=true")
    assert r.status_code == 200
    assert r.json()["count"] >= 1

def test_nl_filter():
    client.post("/strings", json={"value": "aba"})
    r = client.get("/strings/filter-by-natural-language", params={"query":"all single word palindromic strings"})
    assert r.status_code == 200
    assert r.json()["count"] >= 1

