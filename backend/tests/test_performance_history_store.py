import json

from app.models.learning import LearningOutcome
from app.services.performance_history_store import (
    PerformanceHistoryStore,
)


def outcome(
    *,
    task_type="summarization",
    tier="low",
    model_name="qwen3:1.7b",
    success=True,
    confidence=0.9,
    latency=1.5,
    compute=1.5,
):

    return LearningOutcome(
        task_type=task_type,
        tier=tier,
        model_name=model_name,
        success=success,
        confidence_score=confidence,
        latency_seconds=latency,
        normalized_compute_cost=compute,
    )


def test_record_creates_persistent_file(
    tmp_path,
):

    path = (
        tmp_path
        / "history.json"
    )

    store = PerformanceHistoryStore(
        path
    )

    store.record(
        outcome()
    )

    assert path.exists()

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        "summarization::low"
        in data
    )


def test_record_aggregates_history(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    store.record(
        outcome(
            success=True,
            confidence=0.9,
            latency=1.0,
            compute=1.0,
        )
    )

    result = store.record(
        outcome(
            success=False,
            confidence=0.5,
            latency=3.0,
            compute=3.0,
        )
    )

    assert result.attempts == 2
    assert result.successes == 1
    assert result.failures == 1

    assert (
        result.average_confidence
        == 0.7
    )

    assert (
        result.average_latency_seconds
        == 2.0
    )

    assert (
        result.average_normalized_compute_cost
        == 2.0
    )

    assert (
        result.reliability_score
        == 0.5
    )


def test_history_survives_new_store_instance(
    tmp_path,
):

    path = (
        tmp_path
        / "history.json"
    )

    first = PerformanceHistoryStore(
        path
    )

    first.record(
        outcome()
    )

    second = PerformanceHistoryStore(
        path
    )

    stats = second.get_stats(
        task_type="summarization",
        tier="low",
    )

    assert stats.attempts == 1
    assert stats.successes == 1

    assert (
        stats.reliability_score
        == 0.667
    )


def test_missing_history_is_neutral(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    stats = store.get_stats(
        task_type="analysis",
        tier="high",
    )

    assert stats.attempts == 0
    assert stats.successes == 0
    assert stats.failures == 0

    assert (
        stats.reliability_score
        == 0.5
    )


def test_tiers_are_kept_separate(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    store.record(
        outcome(
            tier="low",
        )
    )

    store.record(
        outcome(
            tier="medium",
            model_name="qwen3:4b",
        )
    )

    stats = store.get_task_stats(
        "summarization"
    )

    assert len(stats) == 2

    assert [
        item.tier
        for item in stats
    ] == [
        "low",
        "medium",
    ]


def test_task_types_are_kept_separate(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    store.record(
        outcome(
            task_type="summarization",
        )
    )

    store.record(
        outcome(
            task_type="analysis",
            tier="high",
            model_name="qwen3:8b",
        )
    )

    summary = store.get_stats(
        task_type="summarization",
        tier="low",
    )

    analysis = store.get_stats(
        task_type="analysis",
        tier="high",
    )

    assert summary.attempts == 1
    assert analysis.attempts == 1


def test_snapshot_returns_all_buckets(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    store.record(
        outcome(
            tier="low",
        )
    )

    store.record(
        outcome(
            tier="medium",
            model_name="qwen3:4b",
        )
    )

    snapshot = store.snapshot()

    assert len(snapshot) == 2

    assert (
        "summarization::low"
        in snapshot
    )

    assert (
        "summarization::medium"
        in snapshot
    )
