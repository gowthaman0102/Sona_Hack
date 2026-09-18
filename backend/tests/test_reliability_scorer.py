import pytest

from app.services.reliability_scorer import (
    ReliabilityScorer,
)


scorer = ReliabilityScorer()


def test_no_history_has_neutral_reliability():

    result = scorer.calculate_reliability(
        attempts=0,
        successes=0,
    )

    assert result == 0.5


def test_perfect_small_sample_is_smoothed():

    result = scorer.calculate_reliability(
        attempts=1,
        successes=1,
    )

    assert result == 0.667


def test_reliability_improves_with_success_history():

    small = scorer.calculate_reliability(
        attempts=1,
        successes=1,
    )

    mature = scorer.calculate_reliability(
        attempts=10,
        successes=10,
    )

    assert mature > small
    assert mature == 0.917


def test_failure_history_reduces_reliability():

    result = scorer.calculate_reliability(
        attempts=10,
        successes=2,
    )

    assert result == 0.25


def test_balanced_history_is_neutral():

    result = scorer.calculate_reliability(
        attempts=10,
        successes=5,
    )

    assert result == 0.5


def test_build_stats_calculates_averages():

    result = scorer.build_stats(
        task_type="summarization",
        tier="medium",
        attempts=4,
        successes=3,
        total_confidence=3.2,
        total_latency_seconds=8.0,
        total_normalized_compute_cost=16.0,
    )

    assert result.task_type == "summarization"
    assert result.tier == "medium"

    assert result.attempts == 4
    assert result.successes == 3
    assert result.failures == 1

    assert result.average_confidence == 0.8
    assert result.average_latency_seconds == 2.0

    assert (
        result.average_normalized_compute_cost
        == 4.0
    )

    assert result.reliability_score == 0.667


def test_empty_stats_are_neutral():

    result = scorer.build_stats(
        task_type="analysis",
        tier="high",
        attempts=0,
        successes=0,
        total_confidence=0.0,
        total_latency_seconds=0.0,
        total_normalized_compute_cost=0.0,
    )

    assert result.attempts == 0
    assert result.failures == 0
    assert result.reliability_score == 0.5
    assert result.average_confidence == 0.0
    assert result.average_latency_seconds == 0.0


def test_negative_attempts_are_rejected():

    with pytest.raises(
        ValueError,
    ):
        scorer.calculate_reliability(
            attempts=-1,
            successes=0,
        )


def test_successes_cannot_exceed_attempts():

    with pytest.raises(
        ValueError,
    ):
        scorer.calculate_reliability(
            attempts=2,
            successes=3,
        )
