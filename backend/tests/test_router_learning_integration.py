from unittest.mock import patch

from app.services.intelligent_router import (
    IntelligentRouter,
)
from app.services.learning_outcome_recorder import (
    LearningOutcomeRecorder,
)
from app.services.multi_task_router import (
    MultiTaskRouter,
)
from app.services.performance_history_store import (
    PerformanceHistoryStore,
)


def generation(
    *,
    response,
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


def build_recorder(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    recorder = LearningOutcomeRecorder(
        store
    )

    return store, recorder


def test_router_without_recorder_has_no_learning_side_effect():

    router = IntelligentRouter()

    assert router.learning_recorder is None


def test_single_route_records_success(
    tmp_path,
):

    store, recorder = build_recorder(
        tmp_path
    )

    router = IntelligentRouter(
        learning_recorder=recorder
    )

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=generation(
            response="alice@example.com",
        ),
    ):

        result = router.route(
            "Extract the email alice@example.com"
        )

    stats = store.get_stats(
        task_type=(
            result.routing.analysis.task_type
        ),
        tier=(
            result.routing.selected_tier
        ),
    )

    assert stats.attempts == 1
    assert stats.successes == 1
    assert stats.failures == 0


def test_single_route_records_escalation_failure_and_success(
    tmp_path,
):

    store, recorder = build_recorder(
        tmp_path
    )

    router = IntelligentRouter(
        learning_recorder=recorder
    )

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=[
            generation(
                response="",
                output_tokens=0,
            ),
            generation(
                response="alice@example.com",
            ),
        ],
    ):

        result = router.route(
            "Extract the email alice@example.com"
        )

    task_type = (
        result.routing.analysis.task_type
    )

    low = store.get_stats(
        task_type=task_type,
        tier="low",
    )

    medium = store.get_stats(
        task_type=task_type,
        tier="medium",
    )

    assert low.attempts == 1
    assert low.failures == 1

    assert medium.attempts == 1
    assert medium.successes == 1


def test_multi_task_router_records_each_task(
    tmp_path,
):

    store, recorder = build_recorder(
        tmp_path
    )

    router = MultiTaskRouter(
        learning_recorder=recorder
    )

    prompt = (
        "The customer email is alice@example.com. "
        "Checkout is slow during peak traffic. "
        "Extract the customer email, "
        "summarize the complaint, "
        "and analyze the root cause."
    )

    outputs = [
        generation(
            response="alice@example.com",
            latency=1.0,
        ),
        generation(
            response=(
                "The customer reports checkout becomes "
                "slow during peak traffic."
            ),
            latency=2.0,
        ),
        generation(
            response=(
                "The likely root cause is resource "
                "contention during peak traffic, where "
                "database connections become saturated "
                "and requests queue behind synchronous "
                "operations."
            ),
            latency=3.0,
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            prompt
        )

    assert result.task_count == 3

    for task in result.tasks:

        stats = store.get_stats(
            task_type=task.task_type,
            tier=task.selected_tier,
        )

        assert stats.attempts == 1
        assert stats.successes == 1


def test_multi_task_escalation_records_extra_attempt(
    tmp_path,
):

    store, recorder = build_recorder(
        tmp_path
    )

    router = MultiTaskRouter(
        learning_recorder=recorder
    )

    prompt = (
        "The customer email is alice@example.com. "
        "Checkout is slow during peak traffic. "
        "Extract the customer email, "
        "summarize the complaint, "
        "and analyze the root cause."
    )

    outputs = [
        # Task 1 LOW fails.
        generation(
            response="",
            output_tokens=0,
            latency=1.0,
        ),

        # Task 1 MEDIUM succeeds.
        generation(
            response="alice@example.com",
            latency=2.0,
        ),

        # Task 2 MEDIUM.
        generation(
            response=(
                "The customer reports checkout becomes "
                "slow during peak traffic."
            ),
            latency=2.0,
        ),

        # Task 3 HIGH.
        generation(
            response=(
                "The likely root cause is resource "
                "contention during peak traffic, where "
                "database connections become saturated "
                "and requests queue behind synchronous "
                "operations."
            ),
            latency=3.0,
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            prompt
        )

    first = result.tasks[0]

    low = store.get_stats(
        task_type=first.task_type,
        tier="low",
    )

    medium = store.get_stats(
        task_type=first.task_type,
        tier="medium",
    )

    assert low.attempts == 1
    assert low.failures == 1

    assert medium.attempts == 1
    assert medium.successes == 1

    snapshot = store.snapshot()

    total_attempts = sum(
        stats.attempts
        for stats in snapshot.values()
    )

    assert total_attempts == 4
