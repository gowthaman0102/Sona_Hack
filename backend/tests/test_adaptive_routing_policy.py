from app.models.learning import LearningOutcome
from app.services.adaptive_routing_policy import (
    AdaptiveRoutingPolicy,
)
from app.services.performance_history_store import (
    PerformanceHistoryStore,
)


def record_many(
    store,
    *,
    task_type,
    tier,
    successes,
    failures,
):

    model_names = {
        "low": "qwen3:1.7b",
        "medium": "qwen3:4b",
        "high": "qwen3:8b",
    }

    for _ in range(successes):

        store.record(
            LearningOutcome(
                task_type=task_type,
                tier=tier,
                model_name=model_names[tier],
                success=True,
                confidence_score=0.9,
                latency_seconds=1.0,
                normalized_compute_cost=1.0,
            )
        )

    for _ in range(failures):

        store.record(
            LearningOutcome(
                task_type=task_type,
                tier=tier,
                model_name=model_names[tier],
                success=False,
                confidence_score=0.4,
                latency_seconds=1.0,
                normalized_compute_cost=1.0,
            )
        )


def build_policy(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    policy = AdaptiveRoutingPolicy(
        store
    )

    return store, policy


def test_no_history_preserves_baseline(
    tmp_path,
):

    _, policy = build_policy(
        tmp_path
    )

    result = policy.recommend(
        task_type="extraction",
        baseline_tier="low",
    )

    assert result.recommended_tier == "low"
    assert result.learning_applied is False


def test_small_sample_does_not_change_routing(
    tmp_path,
):

    store, policy = build_policy(
        tmp_path
    )

    record_many(
        store,
        task_type="extraction",
        tier="low",
        successes=0,
        failures=2,
    )

    record_many(
        store,
        task_type="extraction",
        tier="medium",
        successes=2,
        failures=0,
    )

    result = policy.recommend(
        task_type="extraction",
        baseline_tier="low",
    )

    assert result.recommended_tier == "low"
    assert result.learning_applied is False


def test_reliable_baseline_is_preserved(
    tmp_path,
):

    store, policy = build_policy(
        tmp_path
    )

    record_many(
        store,
        task_type="summarization",
        tier="low",
        successes=5,
        failures=0,
    )

    record_many(
        store,
        task_type="summarization",
        tier="medium",
        successes=10,
        failures=0,
    )

    result = policy.recommend(
        task_type="summarization",
        baseline_tier="low",
    )

    assert result.recommended_tier == "low"
    assert result.learning_applied is False


def test_poor_low_can_upgrade_to_medium(
    tmp_path,
):

    store, policy = build_policy(
        tmp_path
    )

    record_many(
        store,
        task_type="extraction",
        tier="low",
        successes=1,
        failures=4,
    )

    record_many(
        store,
        task_type="extraction",
        tier="medium",
        successes=5,
        failures=0,
    )

    result = policy.recommend(
        task_type="extraction",
        baseline_tier="low",
    )

    assert result.learning_applied is True

    assert (
        result.recommended_tier
        == "medium"
    )


def test_nearest_strong_upgrade_is_preferred(
    tmp_path,
):

    store, policy = build_policy(
        tmp_path
    )

    record_many(
        store,
        task_type="extraction",
        tier="low",
        successes=0,
        failures=5,
    )

    record_many(
        store,
        task_type="extraction",
        tier="medium",
        successes=5,
        failures=0,
    )

    record_many(
        store,
        task_type="extraction",
        tier="high",
        successes=10,
        failures=0,
    )

    result = policy.recommend(
        task_type="extraction",
        baseline_tier="low",
    )

    assert (
        result.recommended_tier
        == "medium"
    )


def test_poor_medium_can_upgrade_to_high(
    tmp_path,
):

    store, policy = build_policy(
        tmp_path
    )

    record_many(
        store,
        task_type="summarization",
        tier="medium",
        successes=1,
        failures=4,
    )

    record_many(
        store,
        task_type="summarization",
        tier="high",
        successes=5,
        failures=0,
    )

    result = policy.recommend(
        task_type="summarization",
        baseline_tier="medium",
    )

    assert result.learning_applied is True
    assert result.recommended_tier == "high"


def test_high_baseline_is_never_downgraded(
    tmp_path,
):

    store, policy = build_policy(
        tmp_path
    )

    record_many(
        store,
        task_type="analysis",
        tier="high",
        successes=0,
        failures=5,
    )

    record_many(
        store,
        task_type="analysis",
        tier="medium",
        successes=20,
        failures=0,
    )

    result = policy.recommend(
        task_type="analysis",
        baseline_tier="high",
    )

    assert result.recommended_tier == "high"
    assert result.learning_applied is False


def test_stronger_tier_needs_enough_history(
    tmp_path,
):

    store, policy = build_policy(
        tmp_path
    )

    record_many(
        store,
        task_type="extraction",
        tier="low",
        successes=0,
        failures=5,
    )

    record_many(
        store,
        task_type="extraction",
        tier="medium",
        successes=2,
        failures=0,
    )

    result = policy.recommend(
        task_type="extraction",
        baseline_tier="low",
    )

    assert result.recommended_tier == "low"
    assert result.learning_applied is False


def test_candidates_include_all_tiers(
    tmp_path,
):

    _, policy = build_policy(
        tmp_path
    )

    result = policy.recommend(
        task_type="general",
        baseline_tier="low",
    )

    assert [
        item.tier
        for item in result.candidates
    ] == [
        "low",
        "medium",
        "high",
    ]


def test_invalid_baseline_is_rejected(
    tmp_path,
):

    import pytest

    _, policy = build_policy(
        tmp_path
    )

    with pytest.raises(
        ValueError,
    ):
        policy.recommend(
            task_type="general",
            baseline_tier="ultra",
        )
