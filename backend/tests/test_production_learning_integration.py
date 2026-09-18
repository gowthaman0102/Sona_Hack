from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.routing import intelligent_router
from app.api.multi_routing import multi_task_router
from app.main import app
from app.services.adaptive_routing_policy import (
    AdaptiveRoutingPolicy,
)
from app.services.learning_outcome_recorder import (
    LearningOutcomeRecorder,
)
from app.services.performance_history_store import (
    PerformanceHistoryStore,
)


client = TestClient(app)


def generation(
    response,
    *,
    prompt_tokens=10,
    output_tokens=5,
    latency=1.0,
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


def isolated_learning(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    recorder = LearningOutcomeRecorder(
        store
    )

    policy = AdaptiveRoutingPolicy(
        store
    )

    return (
        store,
        recorder,
        policy,
    )


def test_route_api_records_history(
    tmp_path,
):

    store, recorder, policy = (
        isolated_learning(
            tmp_path
        )
    )

    old_recorder = (
        intelligent_router.learning_recorder
    )

    old_policy = (
        intelligent_router.adaptive_policy
    )

    intelligent_router.learning_recorder = (
        recorder
    )

    intelligent_router.adaptive_policy = (
        policy
    )

    try:

        with patch.object(
            intelligent_router.models,
            "generate_for_tier",
            return_value=generation(
                "alice@example.com",
            ),
        ):

            response = client.post(
                "/route",
                json={
                    "prompt": (
                        "Extract the email "
                        "alice@example.com"
                    )
                },
            )

        assert response.status_code == 200

        data = response.json()

        task_type = (
            data["routing"]["analysis"][
                "task_type"
            ]
        )

        tier = (
            data["routing"][
                "selected_tier"
            ]
        )

        stats = store.get_stats(
            task_type=task_type,
            tier=tier,
        )

        assert stats.attempts == 1
        assert stats.successes == 1

    finally:

        intelligent_router.learning_recorder = (
            old_recorder
        )

        intelligent_router.adaptive_policy = (
            old_policy
        )


def test_route_api_can_use_learned_upgrade(
    tmp_path,
):

    store, recorder, policy = (
        isolated_learning(
            tmp_path
        )
    )

    from app.models.learning import (
        LearningOutcome,
    )

    for index in range(5):

        store.record(
            LearningOutcome(
                task_type="extraction",
                tier="low",
                model_name="qwen3:1.7b",
                success=(
                    index == 0
                ),
                confidence_score=(
                    0.9
                    if index == 0
                    else 0.4
                ),
                latency_seconds=1.0,
                normalized_compute_cost=1.0,
            )
        )

    for _ in range(5):

        store.record(
            LearningOutcome(
                task_type="extraction",
                tier="medium",
                model_name="qwen3:4b",
                success=True,
                confidence_score=0.9,
                latency_seconds=1.0,
                normalized_compute_cost=2.0,
            )
        )


    old_recorder = (
        intelligent_router.learning_recorder
    )

    old_policy = (
        intelligent_router.adaptive_policy
    )

    intelligent_router.learning_recorder = (
        recorder
    )

    intelligent_router.adaptive_policy = (
        policy
    )


    called = []


    def generate(
        *,
        tier,
        prompt,
        system_prompt,
        think,
    ):

        called.append(
            tier.value
        )

        return generation(
            "alice@example.com"
        )


    try:

        with patch.object(
            intelligent_router.models,
            "generate_for_tier",
            side_effect=generate,
        ):

            response = client.post(
                "/route",
                json={
                    "prompt": (
                        "Extract the email "
                        "alice@example.com"
                    )
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert (
            data["routing"][
                "recommended_tier"
            ]
            == "low"
        )

        assert (
            data["routing"][
                "selected_tier"
            ]
            == "medium"
        )

        assert called == [
            "medium"
        ]

    finally:

        intelligent_router.learning_recorder = (
            old_recorder
        )

        intelligent_router.adaptive_policy = (
            old_policy
        )


def test_route_and_multi_route_share_production_store():

    assert (
        intelligent_router.learning_recorder
        is multi_task_router.learning_recorder
    )

    assert (
        intelligent_router.adaptive_policy
        is multi_task_router.adaptive_policy
    )

    assert (
        intelligent_router.learning_recorder.store
        is multi_task_router.learning_recorder.store
    )
