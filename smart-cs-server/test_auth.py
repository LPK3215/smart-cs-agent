"""Tests for JWT auth + password hashing."""

import pytest
from fastapi import HTTPException

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_password_hash_and_verify():
    h = hash_password("secret123")
    assert h != "secret123"
    assert verify_password("secret123", h) is True
    assert verify_password("wrong", h) is False


def test_jwt_roundtrip():
    token = create_access_token("user-1", "user")
    payload = decode_access_token(token)
    assert payload["user_id"] == "user-1"
    assert payload["role"] == "user"


def test_jwt_rejects_garbage():
    with pytest.raises(HTTPException):
        decode_access_token("not-a-real-token")


def test_register_login_flow(client):
    r = client.post("/api/auth/register", json={
        "username": "alice", "password": "Passw0rd!", "displayName": "Alice"
    })
    assert r.status_code == 200
    assert "accessToken" in r.json()


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={
        "username": "bob", "password": "Passw0rd!", "displayName": "Bob"
    })
    # password "wrongwrong" (<6) would be a 422; use valid-length wrong password to get 401
    r = client.post("/api/auth/login", json={"username": "bob", "password": "WrongPass123"})
    assert r.status_code == 401


def test_protected_route_requires_token(client):
    r = client.get("/api/sessions")
    assert r.status_code == 401


def test_me_returns_user(client, auth_headers):
    r = client.get("/api/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["username"] == "tester"
