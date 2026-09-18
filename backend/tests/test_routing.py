from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.intelligent_router import IntelligentRouter


client = TestClient(app)


def fake_result(
    tier: str,
    model_name: str,
    compute_score: int,
    thinking: bool,
):
    return {
        "tier": tier,
        "model_name": model_name,
        "display_name": model_name,
        "compute_score": compute_score,
        "thinking_enabled": thinking,
        "response": "Test response",
        "prompt_tokens": 10,
        "output_tokens": 10,
        "latency_seconds": 1.0,
        "tokens_per_second": 10.0,
    }


def test_automatic_low_route():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=fake_result(
            "low",
            "qwen3:1.7b",
            1,
            False,
        ),
    ):
        result = router.route(
            "Extract the date from this sentence."
        )

    assert (
        result.routing.recommended_tier
        == "low"
    )

    assert (
        result.routing.selected_tier
        == "low"
    )

    assert (
        result.routing.override_applied
        is False
    )


def test_automatic_medium_route():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=fake_result(
            "medium",
            "qwen3:4b",
            2,
            False,
        ),
    ):
        result = router.route(
            "Explain normalization with an example."
        )

    assert (
        result.routing.recommended_tier
        == "medium"
    )

    assert (
        result.routing.selected_tier
        == "medium"
    )


def test_automatic_high_route():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=fake_result(
            "high",
            "qwen3:8b",
            4,
            True,
        ),
    ):
        result = router.route(
            (
                "Analyze this Python API, identify "
                "the root cause, compare two solutions, "
                "and recommend the best architecture."
            )
        )

    assert (
        result.routing.recommended_tier
        == "high"
    )

    assert (
        result.routing.selected_tier
        == "high"
    )

    assert (
        result.routing.thinking_enabled
        is True
    )


def test_override_low_to_high():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=fake_result(
            "high",
            "qwen3:8b",
            4,
            False,
        ),
    ) as mocked_generate:

        result = router.route(
            "Extract the date from this sentence.",
            override_tier="high",
        )

    assert (
        result.routing.recommended_tier
        == "low"
    )

    assert (
        result.routing.selected_tier
        == "high"
    )

    assert (
        result.routing.selected_model
        == "qwen3:8b"
    )

    assert (
        result.routing.override_applied
        is True
    )

    mocked_generate.assert_called_once()


def test_override_high_to_low():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=fake_result(
            "low",
            "qwen3:1.7b",
            1,
            False,
        ),
    ):

        result = router.route(
            (
                "Analyze this backend architecture "
                "and identify its root cause."
            ),
            override_tier="low",
        )

    assert (
        result.routing.recommended_tier
        == "high"
    )

    assert (
        result.routing.selected_tier
        == "low"
    )

    assert (
        result.routing.override_applied
        is True
    )


def test_thinking_override():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=fake_result(
            "high",
            "qwen3:8b",
            4,
            False,
        ),
    ) as mocked_generate:

        result = router.route(
            (
                "Analyze this backend architecture, "
                "identify the root cause, compare "
                "solutions, and recommend a redesign."
            ),
            override_thinking=False,
        )

    assert (
        result.routing.selected_tier
        == "high"
    )

    assert (
        result.routing.thinking_override_applied
        is True
    )

    assert (
        result.routing.thinking_enabled
        is False
    )

    call = mocked_generate.call_args.kwargs

    assert call["think"] is False


def test_route_api_override():
    fake_response = {
        "prompt": "Extract the date.",
        "routing": {
            "recommended_tier": "low",
            "selected_tier": "high",
            "selected_model": "qwen3:8b",
            "compute_score": 4,
            "override_applied": True,
            "thinking_override_applied": False,
            "thinking_enabled": False,
            "analysis": {
                "task_type": "extraction",
                "complexity_score": 1,
                "reasoning_required": False,
                "recommended_tier": "low",
                "explanation": (
                    "extraction task baseline"
                ),
                "features": {
                    "word_count": 3,
                    "has_code": False,
                    "has_reasoning_markers": False,
                    "has_multiple_requirements": False,
                },
            },
            "explanation": {
                "summary": (
                    "AURA selected the HIGH tier "
                    "using Qwen3 8B."
                ),
                "selection_reason": (
                    "AURA recommended LOW, but the user "
                    "explicitly selected HIGH."
                ),
                "complexity_reason": (
                    "The query received a complexity score "
                    "of 1/10 and was classified as an "
                    "extraction task."
                ),
                "reasoning_reason": (
                    "Thinking mode was not required "
                    "for this query."
                ),
                "compute_quality_tradeoff": (
                    "HIGH prioritizes reasoning quality "
                    "and capability for difficult tasks, "
                    "accepting higher latency and compute usage."
                ),
                "override_reason": (
                    "User override changed the route "
                    "from LOW to HIGH."
                ),
                "signals": [
                    "task_type=extraction",
                    "complexity=1/10",
                ],
            },
        },
        "response": "25 September",
        "prompt_tokens": 10,
        "output_tokens": 3,
        "latency_seconds": 1.0,
        "tokens_per_second": 20.0,
    }

    with patch(
        "app.api.routing.intelligent_router.route",
        return_value=fake_response,
    ) as mocked_route:

        response = client.post(
            "/route",
            json={
                "prompt": "Extract the date.",
                "override_tier": "high",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["routing"]["recommended_tier"]
        == "low"
    )

    assert (
        data["routing"]["selected_tier"]
        == "high"
    )

    assert (
        data["routing"]["override_applied"]
        is True
    )

    mocked_route.assert_called_once_with(
        prompt="Extract the date.",
        override_tier="high",
        override_thinking=None,
    )


def test_invalid_override_rejected_by_api():
    response = client.post(
        "/route",
        json={
            "prompt": "Hello.",
            "override_tier": "ultra",
        },
    )

    assert response.status_code == 422
