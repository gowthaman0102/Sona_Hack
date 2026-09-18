from unittest.mock import patch

from app.services.intelligent_router import IntelligentRouter


def generation(
    *,
    response,
    prompt_tokens,
    output_tokens,
    latency,
):
    return {
        "tier": "test",
        "model_name": "mock",
        "display_name": "mock",
        "compute_score": 1,
        "thinking_enabled": False,
        "response": response,
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "latency_seconds": latency,
        "tokens_per_second": (
            round(
                output_tokens / latency,
                2,
            )
            if latency
            else None
        ),
    }


def test_single_attempt_route_analytics():

    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=generation(
            response="alice@example.com",
            prompt_tokens=10,
            output_tokens=2,
            latency=1.5,
        ),
    ):

        result = router.route(
            (
                "Extract the email from "
                "alice@example.com"
            )
        )

    assert result.analytics.attempt_count == 1

    assert (
        result.analytics.total_prompt_tokens
        == 10
    )

    assert (
        result.analytics.total_output_tokens
        == 2
    )

    assert (
        result.analytics.total_tokens
        == 12
    )

    assert (
        result.analytics.total_latency_seconds
        == 1.5
    )

    assert (
        result.analytics.escalation_overhead_compute
        == 0.0
    )


def test_escalation_analytics_include_failed_attempt():

    router = IntelligentRouter()

    outputs = [
        generation(
            response="",
            prompt_tokens=10,
            output_tokens=0,
            latency=1.0,
        ),
        generation(
            response="25 September 2026",
            prompt_tokens=12,
            output_tokens=4,
            latency=2.0,
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.route(
            "Extract the date: 25 September 2026."
        )

    assert result.escalation.escalated is True

    assert result.analytics.attempt_count == 2

    assert (
        result.analytics.total_prompt_tokens
        == 22
    )

    assert (
        result.analytics.total_output_tokens
        == 4
    )

    assert (
        result.analytics.total_latency_seconds
        == 3.0
    )

    # LOW: 1 × 1 = 1
    # MEDIUM: 2 × 2 = 4

    assert (
        result.analytics.normalized_compute_cost
        == 5.0
    )

    assert (
        result.analytics.final_attempt_compute_cost
        == 4.0
    )

    assert (
        result.analytics.escalation_overhead_compute
        == 1.0
    )


def test_route_preserves_existing_final_metrics():

    router = IntelligentRouter()

    outputs = [
        generation(
            response="",
            prompt_tokens=10,
            output_tokens=0,
            latency=1.0,
        ),
        generation(
            response="25 September 2026",
            prompt_tokens=12,
            output_tokens=4,
            latency=2.0,
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.route(
            "Extract the date: 25 September 2026."
        )

    # Legacy fields intentionally remain final-attempt values.

    assert result.prompt_tokens == 12
    assert result.output_tokens == 4
    assert result.latency_seconds == 2.0

    # Accurate totals now live in analytics.

    assert (
        result.analytics.total_prompt_tokens
        == 22
    )

    assert (
        result.analytics.total_latency_seconds
        == 3.0
    )
