"""
Tests for POST /api/chat agent dispatch behavior (CHAT-02).

Covers:
- test_chat_financial_agent: agent='financial' → 200 + non-empty reply
- test_chat_default_agent_backward_compat: no agent field → 200 + non-empty reply
- test_chat_unknown_agent_fallback: agent='unknown_xyz' → 200 + non-empty reply (falls back to quant)

All tests mock requests.post to avoid live LLM calls.
GROQ_API_KEY is patched so the Groq branch is exercised.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    import webapp
    webapp.app.config["TESTING"] = True
    with webapp.app.test_client() as c:
        yield c


def _groq_mock():
    """Return a MagicMock that looks like a successful Groq HTTP response."""
    mock = MagicMock()
    mock.json.return_value = {"choices": [{"message": {"content": "mocked reply"}}]}
    mock.raise_for_status = MagicMock()
    return mock


def test_chat_financial_agent(client, monkeypatch):
    """POST /api/chat with agent='financial' returns 200 with a non-empty reply."""
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    with patch("webapp.requests.post", return_value=_groq_mock()) as mock_post:
        response = client.post("/api/chat", json={"message": "hello", "agent": "financial"})

    assert response.status_code == 200
    data = response.get_json()
    assert "reply" in data
    assert data["reply"]  # non-empty


def test_chat_default_agent_backward_compat(client, monkeypatch):
    """POST /api/chat with no agent field defaults to quant and returns 200."""
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    with patch("webapp.requests.post", return_value=_groq_mock()):
        response = client.post("/api/chat", json={"message": "hello"})

    assert response.status_code == 200
    data = response.get_json()
    assert "reply" in data
    assert data["reply"]


def test_chat_unknown_agent_fallback(client, monkeypatch):
    """POST /api/chat with an unknown agent value falls back to quant silently and returns 200."""
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    with patch("webapp.requests.post", return_value=_groq_mock()):
        response = client.post("/api/chat", json={"message": "hello", "agent": "unknown_xyz"})

    assert response.status_code == 200
    data = response.get_json()
    assert "reply" in data
    assert data["reply"]
