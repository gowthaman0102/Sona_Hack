from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.model_registry import (
    ModelTier,
    get_all_models,
    get_model_by_tier,
)
from app.main import app


client = TestClient(app)


def test_registry_contains_three_models():
    models = get_all_models()

    assert len(models) == 3


def test_low_tier_model():
    model = get_model_by_tier(ModelTier.LOW)

    assert model.model_name == "qwen3:1.7b"
    assert model.compute_score == 1


def test_medium_tier_model():
    model = get_model_by_tier(ModelTier.MEDIUM)

    assert model.model_name == "qwen3:4b"
    assert model.compute_score == 2


def test_high_tier_model():
    model = get_model_by_tier(ModelTier.HIGH)

    assert model.model_name == "qwen3:8b"
    assert model.compute_score == 4


def test_model_registry_api():
    installed = [
        {"name": "qwen3:1.7b"},
        {"name": "qwen3:4b"},
        {"name": "qwen3:8b"},
    ]

    with patch(
        "app.api.models.ollama_service.list_models",
        return_value=installed,
    ):
        response = client.get("/models")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 3

    assert data["models"][0]["tier"] == "low"
    assert data["models"][1]["tier"] == "medium"
    assert data["models"][2]["tier"] == "high"

    assert all(
        model["installed"]
        for model in data["models"]
    )
