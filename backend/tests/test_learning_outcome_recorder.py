from app.models.analytics import (
    AttemptMetrics,
    RouteAnalytics,
)
from app.services.learning_outcome_recorder import (
    LearningOutcomeRecorder,
)
from app.services.performance_history_store import (
    PerformanceHistoryStore,
)


def attempt(
    *,
    tier,
    model_name,
    compute_score,
    confidence,
    should_escalate,
    latency,
):

    return AttemptMetrics(
        tier=tier,
        model_name=model_name,
        compute_score=compute_score,
        confidence_score=confidence,
        confidence_level=(
            "high"
            if confidence >= 0.8
            else "low"
        ),
        should_escalate=should_escalate,
        prompt_tokens=10,
        output_tokens=5,
        total_tokens=15,
        latency_seconds=latency,
        tokens_per_second=5.0,
        normalized_compute_cost=round(
            compute_score * latency,
            3,
        ),
    )


def analytics(
    attempts,
):

    total_prompt = sum(
        item.prompt_tokens
        for item in attempts
    )

    total_output = sum(
        item.output_tokens
        for item in attempts
    )

    total_latency = round(
        sum(
            item.latency_seconds
            for item in attempts
        ),
        3,
    )

    total_compute = round(
        sum(
            item.normalized_compute_cost
            for item in attempts
        ),
        3,
    )

    final_compute = (
        attempts[-1].normalized_compute_cost
        if attempts
        else 0.0
    )

    return RouteAnalytics(
        attempt_count=len(attempts),
        total_prompt_tokens=total_prompt,
        total_output_tokens=total_output,
        total_tokens=(
            total_prompt
            + total_output
        ),
        total_latency_seconds=(
            total_latency
        ),
        normalized_compute_cost=(
            total_compute
        ),
        final_attempt_compute_cost=(
            final_compute
        ),
        escalation_overhead_compute=round(
            total_compute
            - final_compute,
            3,
        ),
        attempts=attempts,
    )


def test_single_successful_attempt_is_recorded(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    recorder = LearningOutcomeRecorder(
        store
    )

    route = analytics(
        [
            attempt(
                tier="low",
                model_name="qwen3:1.7b",
                compute_score=1,
                confidence=0.9,
                should_escalate=False,
                latency=1.0,
            )
        ]
    )

    result = recorder.record_route(
        task_type="extraction",
        analytics=route,
    )

    assert len(result) == 1

    stats = store.get_stats(
        task_type="extraction",
        tier="low",
    )

    assert stats.attempts == 1
    assert stats.successes == 1
    assert stats.failures == 0

    assert (
        stats.reliability_score
        == 0.667
    )


def test_escalation_records_failure_then_success(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    recorder = LearningOutcomeRecorder(
        store
    )

    route = analytics(
        [
            attempt(
                tier="low",
                model_name="qwen3:1.7b",
                compute_score=1,
                confidence=0.4,
                should_escalate=True,
                latency=1.0,
            ),
            attempt(
                tier="medium",
                model_name="qwen3:4b",
                compute_score=2,
                confidence=0.9,
                should_escalate=False,
                latency=2.0,
            ),
        ]
    )

    recorder.record_route(
        task_type="extraction",
        analytics=route,
    )

    low = store.get_stats(
        task_type="extraction",
        tier="low",
    )

    medium = store.get_stats(
        task_type="extraction",
        tier="medium",
    )

    assert low.attempts == 1
    assert low.successes == 0
    assert low.failures == 1

    assert (
        low.reliability_score
        == 0.333
    )

    assert medium.attempts == 1
    assert medium.successes == 1
    assert medium.failures == 0

    assert (
        medium.reliability_score
        == 0.667
    )


def test_all_attempt_metrics_are_persisted(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    recorder = LearningOutcomeRecorder(
        store
    )

    route = analytics(
        [
            attempt(
                tier="high",
                model_name="qwen3:8b",
                compute_score=4,
                confidence=0.9,
                should_escalate=False,
                latency=3.0,
            )
        ]
    )

    recorder.record_route(
        task_type="analysis",
        analytics=route,
    )

    stats = store.get_stats(
        task_type="analysis",
        tier="high",
    )

    assert (
        stats.average_confidence
        == 0.9
    )

    assert (
        stats.average_latency_seconds
        == 3.0
    )

    assert (
        stats.average_normalized_compute_cost
        == 12.0
    )


def test_repeated_routes_accumulate_history(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    recorder = LearningOutcomeRecorder(
        store
    )

    successful = analytics(
        [
            attempt(
                tier="low",
                model_name="qwen3:1.7b",
                compute_score=1,
                confidence=0.9,
                should_escalate=False,
                latency=1.0,
            )
        ]
    )

    recorder.record_route(
        task_type="extraction",
        analytics=successful,
    )

    recorder.record_route(
        task_type="extraction",
        analytics=successful,
    )

    stats = store.get_stats(
        task_type="extraction",
        tier="low",
    )

    assert stats.attempts == 2
    assert stats.successes == 2

    assert (
        stats.reliability_score
        == 0.75
    )


def test_empty_route_records_nothing(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    recorder = LearningOutcomeRecorder(
        store
    )

    route = analytics(
        []
    )

    result = recorder.record_route(
        task_type="general",
        analytics=route,
    )

    assert result == []

    assert store.snapshot() == {}
