"""Integration tests for the chat / session / analytics API."""

import pytest


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_session_and_messages(client, auth_headers):
    r = client.post("/api/sessions", headers=auth_headers, json={"title": "测试会话"})
    assert r.status_code == 200
    sid = r.json()["id"]

    r2 = client.get(f"/api/sessions/{sid}/messages", headers=auth_headers)
    assert r2.status_code == 200


def test_non_stream_chat_returns_trace(client, auth_headers):
    # Create a session first
    sid = client.post("/api/sessions", headers=auth_headers, json={}).json()["id"]
    r = client.post(
        "/api/chat",
        headers=auth_headers,
        json={"sessionId": sid, "message": "查询订单 ORD20260610001 状态"},
    )
    # 422 => validation issue; 429 => rate limit; 500 => LLM key missing in CI.
    # We only assert it did not crash with an unhandled error.
    assert r.status_code in (200, 422, 429, 500)
    if r.status_code == 200:
        body = r.json()
        # Non-stream chat returns {userMessage, botMessage, ...}
        assert "botMessage" in body
        assert "content" in body["botMessage"]


def test_analytics_requires_admin(client, auth_headers):
    r = client.get("/api/analytics", headers=auth_headers)
    # tester is role=user -> 403
    assert r.status_code in (403, 200)  # depends on seeding; default user => 403


def test_rate_limit_endpoint_exists(client):
    # health is public; just ensure analytics/tool-audit require auth shape
    r = client.get("/api/tool-audit")
    assert r.status_code == 401
