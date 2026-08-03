"""Pytest fixtures — isolated temp DB + FastAPI TestClient."""

import os
import tempfile
import pytest
import pytest_asyncio


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Point DATABASE_PATH to a fresh temp file and reset the shared connection."""
    import asyncio
    import app.database as db_mod
    import app.config as cfg

    db_path = os.path.join(tmp_path, "test_smart_cs.db")
    # database.py imports DATABASE_PATH at module level, so patch it there too.
    monkeypatch.setattr(cfg, "DATABASE_PATH", db_path)
    monkeypatch.setattr(db_mod, "DATABASE_PATH", db_path)
    monkeypatch.setattr(db_mod, "_db", None)
    asyncio.run(db_mod.init_db())
    yield
    asyncio.run(db_mod.close_db())


@pytest.fixture
def client(isolated_db):
    """FastAPI TestClient with a clean DB."""
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Register + login a test user, return Authorization headers.

    Real endpoints: POST /api/auth/register, POST /api/auth/login
    Both return {"accessToken": "...", "tokenType": "bearer"}.
    """
    client.post("/api/auth/register", json={
        "username": "tester", "password": "Str0ng!Pass", "display_name": "Tester"
    })
    resp = client.post("/api/auth/login", json={
        "username": "tester", "password": "Str0ng!Pass"
    })
    token = resp.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}
