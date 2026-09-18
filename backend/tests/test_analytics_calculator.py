from app.services.analytics_calculator import (
    AnalyticsCalculator,
)


calculator = AnalyticsCalculator()


def test_attempt_metrics_calculate_total_tokens():

    result = calculator.build_attempt(
        tier="low",
        model_name="qwen3:1.7b",
        compute_score=1,
        confidence_score=1.0,
        confidence_level="high",
        should_escalate=False,
        prompt_tokens=20,
        output_tokens=10,
        latency_seconds=2.0,
        tokens_per_second=5.0,
    )

    assert result.total_tokens == 30


def test_normalized_compute_uses_score_times_latency():

    result = calculator.build_attempt(
        tier="high",
        model_name="qwen3:8b",
        compute_score=4,
        confidence_score=1.0,
        confidence_level="high",
        should_escalate=False,
        prompt_tokens=20,
        output_tokens=10,
        latency_seconds=2.5,
        tokens_per_second=4.0,
    )

    assert (
        result.normalized_compute_cost
        == 10.0
    )


def test_summary_aggregates_all_attempt_tokens():

    attempts = [
        calculator.build_attempt(
            tier="low",
            model_name="qwen3:1.7b",
            compute_score=1,
            confidence_score=0.0,
            confidence_level="low",
            should_escalate=True,
            prompt_tokens=10,
            output_tokens=2,
            latency_seconds=1.0,
            tokens_per_second=2.0,
        ),
        calculator.build_attempt(
            tier="medium",
            model_name="qwen3:4b",
            compute_score=2,
            confidence_score=1.0,
            confidence_level="high",
            should_escalate=False,
            prompt_tokens=12,
            output_tokens=8,
            latency_seconds=2.0,
            tokens_per_second=4.0,
        ),
    ]

    result = calculator.summarize(
        attempts
    )

    assert result.attempt_count == 2

    assert (
        result.total_prompt_tokens
        == 22
    )

    assert (
        result.total_output_tokens
        == 10
    )

    assert result.total_tokens == 32


def test_summary_aggregates_all_latency():

    attempts = [
        calculator.build_attempt(
            tier="low",
            model_name="qwen3:1.7b",
            compute_score=1,
            confidence_score=0.0,
            confidence_level="low",
            should_escalate=True,
            prompt_tokens=10,
            output_tokens=2,
            latency_seconds=1.25,
            tokens_per_second=2.0,
        ),
        calculator.build_attempt(
            tier="medium",
            model_name="qwen3:4b",
            compute_score=2,
            confidence_score=1.0,
            confidence_level="high",
            should_escalate=False,
            prompt_tokens=12,
            output_tokens=8,
            latency_seconds=2.75,
            tokens_per_second=4.0,
        ),
    ]

    result = calculator.summarize(
        attempts
    )

    assert (
        result.total_latency_seconds
        == 4.0
    )


def test_summary_compute_includes_escalation_overhead():

    attempts = [
        calculator.build_attempt(
            tier="low",
            model_name="qwen3:1.7b",
            compute_score=1,
            confidence_score=0.0,
            confidence_level="low",
            should_escalate=True,
            prompt_tokens=10,
            output_tokens=2,
            latency_seconds=1.0,
            tokens_per_second=2.0,
        ),
        calculator.build_attempt(
            tier="medium",
            model_name="qwen3:4b",
            compute_score=2,
            confidence_score=1.0,
            confidence_level="high",
            should_escalate=False,
            prompt_tokens=12,
            output_tokens=8,
            latency_seconds=2.0,
            tokens_per_second=4.0,
        ),
    ]

    result = calculator.summarize(
        attempts
    )

    # LOW = 1 × 1.0 = 1
    # MEDIUM = 2 × 2.0 = 4

    assert (
        result.normalized_compute_cost
        == 5.0
    )

    assert (
        result.final_attempt_compute_cost
        == 4.0
    )

    assert (
        result.escalation_overhead_compute
        == 1.0
    )


def test_no_escalation_has_zero_overhead():

    attempts = [
        calculator.build_attempt(
            tier="medium",
            model_name="qwen3:4b",
            compute_score=2,
            confidence_score=1.0,
            confidence_level="high",
            should_escalate=False,
            prompt_tokens=10,
            output_tokens=5,
            latency_seconds=2.0,
            tokens_per_second=2.5,
        ),
    ]

    result = calculator.summarize(
        attempts
    )

    assert result.attempt_count == 1

    assert (
        result.escalation_overhead_compute
        == 0.0
    )


def test_empty_analytics_are_zero():

    result = calculator.summarize(
        []
    )

    assert result.attempt_count == 0
    assert result.total_tokens == 0
    assert result.normalized_compute_cost == 0.0
