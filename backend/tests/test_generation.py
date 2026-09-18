from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_generate_text():
    fake_result = {
        "model": "qwen2.5:7b",
        "response": "Hello from AURA.",
        "done": True,
        "total_duration": 1000000,
        "load_duration": 1000,
        "prompt_eval_count": 5,
        "eval_count": 4,
        "eval_duration": 500000,
    }

    with patch(
        "app.api.ollama.ollama_service.generate",
        return_value=fake_result,
    ):
        response = client.post(
            "/ollama/generate",
            json={
                "model": "qwen2.5:7b",
                "prompt": "Say hello.",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["model"] == "qwen2.5:7b"
    assert data["response"] == "Hello from AURA."
    assert data["done"] is True
