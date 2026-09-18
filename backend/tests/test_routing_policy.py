from unittest.mock import patch

from app.services.intelligent_router import IntelligentRouter


def _fake_result(
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
        "output_tokens": 5,
        "latency_seconds": 1.0,
        "tokens_per_second": 10.0,
    }


def test_high_score_enables_thinking():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=_fake_result(
            "high",
            "qwen3:8b",
            4,
            True,
        ),
    ) as mocked:

        result = router.route(
            (
                "Analyze this Python backend, identify the root "
                "cause, compare two solutions, and recommend "
                "the best architecture."
            )
        )

    assert result.routing.selected_tier == "high"
    assert result.routing.thinking_enabled is True

    assert (
        mocked.call_args.kwargs["think"]
        is True
    )


def test_high_tier_override_does_not_force_thinking():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=_fake_result(
            "high",
            "qwen3:8b",
            4,
            False,
        ),
    ) as mocked:

        result = router.route(
            "Extract the date from this sentence.",
            override_tier="high",
        )

    assert result.routing.recommended_tier == "low"
    assert result.routing.selected_tier == "high"
    assert result.routing.thinking_enabled is False

    assert (
        mocked.call_args.kwargs["think"]
        is False
    )


def test_manual_thinking_can_be_enabled():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=_fake_result(
            "medium",
            "qwen3:4b",
            2,
            True,
        ),
    ) as mocked:

        result = router.route(
            "Explain normalization with an example.",
            override_thinking=True,
        )

    assert result.routing.selected_tier == "medium"

    assert (
        result.routing.thinking_override_applied
        is True
    )

    assert result.routing.thinking_enabled is True

    assert (
        mocked.call_args.kwargs["think"]
        is True
    )


def test_low_override_preserves_original_recommendation():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=_fake_result(
            "low",
            "qwen3:1.7b",
            1,
            False,
        ),
    ):

        result = router.route(
            (
                "Analyze this backend architecture, identify "
                "the root cause, compare alternatives, and "
                "recommend a scalable redesign."
            ),
            override_tier="low",
        )

    assert result.routing.recommended_tier == "high"
    assert result.routing.selected_tier == "low"
    assert result.routing.compute_score == 1
    assert result.routing.override_applied is True


def test_no_override_keeps_recommendation_and_selection_equal():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=_fake_result(
            "medium",
            "qwen3:4b",
            2,
            False,
        ),
    ):

        result = router.route(
            "Explain database normalization."
        )

    assert (
        result.routing.recommended_tier
        == result.routing.selected_tier
    )

    assert result.routing.override_applied is False
