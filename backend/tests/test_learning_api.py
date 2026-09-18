from fastapi.testclient import TestClient

from app.main import app
from app.models.learning import LearningOutcome
from app.services.learning_context import (
    performance_history_store,
)


client = TestClient(app)


def record(
    *,
    task_type,
    tier,
    success,
):

    models = {
        "low": "qwen3:1.7b",
        "medium": "qwen3:4b",
        "high": "qwen3:8b",
    }

    performance_history_store.record(
        LearningOutcome(
            task_type=task_type,
            tier=tier,
            model_name=models[tier],
            success=success,
            confidence_score=(
                0.9
                if success
                else 0.4
            ),
            latency_seconds=1.0,
            normalized_compute_cost=1.0,
        )
    )


def test_empty_learning_history():

    response = client.get(
        "/learning/history"
    )

    assert response.status_code == 200

    assert response.json() == {}


def test_learning_history_exposes_aggregate_stats():

    record(
        task_type="extraction",
        tier="low",
        success=True,
    )

    response = client.get(
        "/learning/history"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        "extraction::low"
        in data
    )

    stats = data[
        "extraction::low"
    ]

    assert stats["attempts"] == 1
    assert stats["successes"] == 1
    assert stats["failures"] == 0

    assert (
        stats["reliability_score"]
        == 0.667
    )


def test_task_history_returns_only_requested_task():

    record(
        task_type="extraction",
        tier="low",
        success=True,
    )

    record(
        task_type="analysis",
        tier="high",
        success=True,
    )

    response = client.get(
        "/learning/history/extraction"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert (
        data[0]["task_type"]
        == "extraction"
    )

    assert (
        data[0]["tier"]
        == "low"
    )


def test_task_history_missing_task_returns_empty_list():

    response = client.get(
        "/learning/history/nonexistent"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_recommendation_preserves_baseline_without_history():

    response = client.get(
        "/learning/recommendation/extraction",
        params={
            "baseline_tier": "low"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["baseline_tier"] == "low"
    assert data["recommended_tier"] == "low"

    assert (
        data["learning_applied"]
        is False
    )


def test_recommendation_exposes_learned_upgrade():

    # LOW:
    # 1 success + 4 failures.
    record(
        task_type="extraction",
        tier="low",
        success=True,
    )

    for _ in range(4):
        record(
            task_type="extraction",
            tier="low",
            success=False,
        )

    # MEDIUM:
    # 5 successes.
    for _ in range(5):
        record(
            task_type="extraction",
            tier="medium",
            success=True,
        )

    response = client.get(
        "/learning/recommendation/extraction",
        params={
            "baseline_tier": "low"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["baseline_tier"] == "low"

    assert (
        data["recommended_tier"]
        == "medium"
    )

    assert (
        data["learning_applied"]
        is True
    )


def test_invalid_baseline_tier_is_rejected():

    response = client.get(
        "/learning/recommendation/extraction",
        params={
            "baseline_tier": "ultra"
        },
    )

    assert response.status_code == 422


def test_history_does_not_expose_prompt_or_response():

    record(
        task_type="extraction",
        tier="low",
        success=True,
    )

    response = client.get(
        "/learning/history"
    )

    text = response.text.lower()

    assert "prompt" not in text
    assert "response" not in text
