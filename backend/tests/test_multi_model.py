from unittest.mock import patch

from app.core.model_registry import ModelTier
from app.services.multi_model_service import MultiModelService


def test_generate_low_tier():
    service = MultiModelService()

    fake_result = {
        "model": "qwen3:1.7b",
        "response": "Low tier response",
        "thinking": None,
        "done": True,
        "total_duration": 2_000_000_000,
        "load_duration": 1000,
        "prompt_eval_count": 10,
        "eval_count": 20,
        "eval_duration": 1_000_000_000,
    }

    with patch.object(
        service.ollama,
        "generate",
        return_value=fake_result,
    ) as mocked_generate:

        result = service.generate_for_tier(
            ModelTier.LOW,
            "Test prompt",
        )

    assert result["tier"] == "low"
    assert result["model_name"] == "qwen3:1.7b"
    assert result["compute_score"] == 1
    assert result["latency_seconds"] == 2.0
    assert result["thinking_enabled"] is False
    assert result["tokens_per_second"] == 20.0

    mocked_generate.assert_called_once_with(
        model="qwen3:1.7b",
        prompt="Test prompt",
        system_prompt=None,
        think=False,
    )


def test_generate_high_tier_with_thinking():
    service = MultiModelService()

    fake_result = {
        "model": "qwen3:8b",
        "response": "High tier response",
        "thinking": "internal reasoning",
        "done": True,
        "total_duration": 5_000_000_000,
        "load_duration": 1000,
        "prompt_eval_count": 10,
        "eval_count": 30,
        "eval_duration": 3_000_000_000,
    }

    with patch.object(
        service.ollama,
        "generate",
        return_value=fake_result,
    ) as mocked_generate:

        result = service.generate_for_tier(
            ModelTier.HIGH,
            "Hard test prompt",
            think=True,
        )

    assert result["tier"] == "high"
    assert result["model_name"] == "qwen3:8b"
    assert result["compute_score"] == 4
    assert result["thinking_enabled"] is True
    assert result["tokens_per_second"] == 10.0

    mocked_generate.assert_called_once_with(
        model="qwen3:8b",
        prompt="Hard test prompt",
        system_prompt=None,
        think=True,
    )
