from unittest.mock import patch

from app.services.intelligent_router import IntelligentRouter


def fake_generation(
    model_name: str,
    response: str,
):
    return {
        "tier": "test",
        "model_name": model_name,
        "display_name": model_name,
        "compute_score": 1,
        "thinking_enabled": False,
        "response": response,
        "prompt_tokens": 10,
        "output_tokens": 10,
        "latency_seconds": 1.0,
        "tokens_per_second": 10.0,
    }


def test_high_confidence_low_does_not_escalate():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=fake_generation(
            "qwen3:1.7b",
            "25 September 2026",
        ),
    ) as mocked:

        result = router.route(
            "Extract the date from this sentence."
        )

    assert result.routing.selected_tier == "low"
    assert result.escalation.escalated is False
    assert len(result.escalation.attempts) == 1
    assert result.confidence.should_escalate is False

    assert mocked.call_count == 1


def test_low_escalates_to_medium():
    router = IntelligentRouter()

    responses = [
        fake_generation(
            "qwen3:1.7b",
            "",
        ),
        fake_generation(
            "qwen3:4b",
            (
                "Database normalization organizes relational "
                "data into related tables to reduce duplicate "
                "information and improve consistency."
            ),
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=responses,
    ) as mocked:

        result = router.route(
            "Extract the date from this sentence."
        )

    # Extraction response from LOW fails confidence.
    # MEDIUM response is accepted.
    assert result.routing.selected_tier == "medium"
    assert result.escalation.escalated is True
    assert result.escalation.initial_tier == "low"
    assert result.escalation.final_tier == "medium"
    assert len(result.escalation.attempts) == 2

    assert mocked.call_count == 2


def test_medium_escalates_to_high():
    router = IntelligentRouter()

    responses = [
        fake_generation(
            "qwen3:4b",
            "I don't know.",
        ),
        fake_generation(
            "qwen3:8b",
            (
                "Database normalization organizes data into "
                "related tables to reduce duplication and "
                "maintain consistency. First normal form removes "
                "repeating groups, while later normal forms "
                "separate dependencies into appropriate tables."
            ),
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=responses,
    ) as mocked:

        result = router.route(
            "Explain database normalization."
        )

    assert result.escalation.initial_tier == "medium"
    assert result.escalation.final_tier == "high"
    assert result.escalation.escalated is True

    assert result.routing.selected_tier == "high"

    assert mocked.call_count == 2


def test_low_can_escalate_all_way_to_high():
    router = IntelligentRouter()

    responses = [
        fake_generation(
            "qwen3:1.7b",
            "",
        ),
        fake_generation(
            "qwen3:4b",
            "",
        ),
        fake_generation(
            "qwen3:8b",
            "25 September 2026",
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=responses,
    ) as mocked:

        result = router.route(
            "Extract the date from this sentence."
        )

    assert result.escalation.initial_tier == "low"
    assert result.escalation.final_tier == "high"
    assert result.escalation.escalated is True

    assert len(
        result.escalation.attempts
    ) == 3

    assert mocked.call_count == 3


def test_high_is_escalation_ceiling():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=fake_generation(
            "qwen3:8b",
            "Use caching.",
        ),
    ) as mocked:

        result = router.route(
            (
                "Analyze this backend architecture, identify "
                "the root cause, compare alternatives, and "
                "recommend the best redesign."
            )
        )

    assert result.routing.selected_tier == "high"
    assert result.escalation.final_tier == "high"

    assert mocked.call_count == 1


def test_manual_override_disables_auto_escalation():
    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=fake_generation(
            "qwen3:1.7b",
            "",
        ),
    ) as mocked:

        result = router.route(
            (
                "Analyze this backend architecture, identify "
                "the root cause, compare solutions, and "
                "recommend a redesign."
            ),
            override_tier="low",
        )

    assert result.routing.selected_tier == "low"
    assert result.routing.override_applied is True
    assert result.escalation.escalated is False

    assert mocked.call_count == 1


def test_attempt_history_records_confidence():
    router = IntelligentRouter()

    responses = [
        fake_generation(
            "qwen3:1.7b",
            "",
        ),
        fake_generation(
            "qwen3:4b",
            "25 September 2026",
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=responses,
    ):

        result = router.route(
            "Extract the date from this sentence."
        )

    first = result.escalation.attempts[0]
    second = result.escalation.attempts[1]

    assert first.tier == "low"
    assert first.should_escalate is True

    assert second.tier == "medium"
    assert second.should_escalate is False
