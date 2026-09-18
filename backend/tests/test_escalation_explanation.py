from unittest.mock import patch

from app.services.intelligent_router import IntelligentRouter


def fake_generation(
    response: str,
):
    return {
        "tier": "test",
        "model_name": "mock",
        "display_name": "mock",
        "compute_score": 1,
        "thinking_enabled": False,
        "response": response,
        "prompt_tokens": 10,
        "output_tokens": 10,
        "latency_seconds": 1.0,
        "tokens_per_second": 10.0,
    }


def test_no_escalation_reason():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=fake_generation(
            "25 September 2026"
        ),
    ):

        result = router.route(
            "Extract the date from this sentence."
        )

    assert result.escalation.escalated is False

    assert (
        "no escalation was required"
        in result.escalation.reason.lower()
    )


def test_escalation_reason_contains_risk():
    router = IntelligentRouter()

    responses = [
        fake_generation(""),
        fake_generation("25 September 2026"),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=responses,
    ):

        result = router.route(
            "Extract the date from this sentence."
        )

    assert result.escalation.escalated is True

    assert (
        "empty_response"
        in result.escalation.reason
    )

    assert (
        "LOW to MEDIUM"
        in result.escalation.reason
    )


def test_override_explains_no_auto_escalation():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=fake_generation(""),
    ):

        result = router.route(
            "Extract the date from this sentence.",
            override_tier="low",
        )

    assert result.escalation.escalated is False

    assert (
        "user explicitly overrode"
        in result.escalation.reason.lower()
    )


def test_high_ceiling_explanation():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=fake_generation(
            "Use caching."
        ),
    ):

        result = router.route(
            (
                "Analyze this backend architecture, "
                "identify the root cause, compare "
                "alternatives, and recommend a redesign."
            )
        )

    assert result.routing.selected_tier == "high"

    assert (
        "no further escalation is available"
        in result.escalation.reason.lower()
    )
