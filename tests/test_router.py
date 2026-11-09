import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.router import choose

client = TestClient(app)  # no API keys set -> only mock models available


def test_simple_prompt_goes_cheap():
    m, _ = choose("hi there", "rules")
    assert m.name == "mock-fast"


def test_code_prompt_goes_smart():
    m, _ = choose("fix this bug: def f(): return 1/0", "rules")
    assert m.name == "mock-smart"


def test_explicit_unknown_model():
    with pytest.raises(ValueError):
        choose("x", "explicit", "nope")


def test_chat_endpoint():
    r = client.post("/chat", json={"prompt": "hello"})
    assert r.status_code == 200
    assert r.json()["model"] == "mock-fast"


def test_fallback(monkeypatch):
    monkeypatch.setenv("MOCK_FAIL", "mock-fast")
    r = client.post("/chat", json={"prompt": "hello"})
    body = r.json()
    assert body["model"] == "mock-smart"
    assert "FAILED" in body["attempts"][0]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}
