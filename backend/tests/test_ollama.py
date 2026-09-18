from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ollama_health_available():
    with patch(
        "app.api.ollama.ollama_service.health_check",
        return_value=True,
    ):
        response = client.get("/ollama/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "available"
    assert data["ollama_available"] is True


def test_ollama_models():
    fake_models = [
        {
            "name": "qwen2.5:7b",
            "model": "qwen2.5:7b",
            "size": 4700000000,
            "modified_at": "2026-09-10T00:00:00Z",
            "details": {},
        }
    ]

    with patch(
        "app.api.ollama.ollama_service.list_models",
        return_value=fake_models,
    ):
        response = client.get("/ollama/models")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 1
    assert data["models"][0]["name"] == "qwen2.5:7b"
