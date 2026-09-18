from unittest.mock import patch

from app.services.multi_task_router import MultiTaskRouter


def generation(
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


def prompt():
    return (
        "The customer email is alice@example.com. "
        "Checkout is slow during peak traffic. "
        "Extract the customer email, "
        "summarize the complaint, "
        "and analyze the root cause."
    )


def test_each_subtask_exposes_analytics():

    router = MultiTaskRouter()

    outputs = [
        generation(
            "alice@example.com",
            10,
            2,
            1.0,
        ),
        generation(
            "Checkout is slow during peak traffic.",
            20,
            8,
            2.0,
        ),
        generation(
            (
                "The likely cause is resource contention "
                "during peak traffic."
            ),
            30,
            10,
            3.0,
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            prompt()
        )

    assert result.task_count == 3

    assert all(
        task.analytics is not None
        for task in result.tasks
    )

    assert all(
        task.analytics.attempt_count == 1
        for task in result.tasks
    )


def test_multi_task_totals_include_every_task():

    router = MultiTaskRouter()

    outputs = [
        generation(
            "alice@example.com",
            10,
            2,
            1.0,
        ),
        generation(
            "Checkout is slow during peak traffic.",
            20,
            8,
            2.0,
        ),
        generation(
            (
                "The likely cause is resource contention "
                "during peak traffic."
            ),
            30,
            10,
            3.0,
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            prompt()
        )

    analytics = result.analytics

    assert analytics.task_count == 3
    assert analytics.total_attempt_count == 3

    assert analytics.total_prompt_tokens == 60
    assert analytics.total_output_tokens == 20
    assert analytics.total_tokens == 80
    assert analytics.total_latency_seconds == 6.0


def test_multi_task_normalized_compute_uses_each_selected_tier():

    router = MultiTaskRouter()

    outputs = [
        generation(
            "alice@example.com",
            10,
            2,
            1.0,
        ),
        generation(
            "Checkout is slow during peak traffic.",
            20,
            8,
            2.0,
        ),
        generation(
            (
                "The likely cause is resource contention "
                "during peak traffic."
            ),
            30,
            10,
            3.0,
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            prompt()
        )

    # LOW:    1 × 1.0 = 1
    # MEDIUM: 2 × 2.0 = 4
    # HIGH:   4 × 3.0 = 12
    # TOTAL:             17

    assert (
        result.analytics.normalized_compute_cost
        == 17.0
    )

    assert (
        result.analytics.final_attempt_compute_cost
        == 17.0
    )

    assert (
        result.analytics.escalation_overhead_compute
        == 0.0
    )


def test_subtask_escalation_is_counted_in_request_totals():

    router = MultiTaskRouter()

    outputs = [
        # Task 1 LOW fails
        generation(
            "",
            10,
            0,
            1.0,
        ),

        # Task 1 MEDIUM succeeds
        generation(
            "alice@example.com",
            12,
            2,
            2.0,
        ),

        # Task 2 MEDIUM
        generation(
            "Checkout is slow during peak traffic.",
            20,
            8,
            2.0,
        ),

        # Task 3 HIGH
        generation(
            (
                "The likely cause is resource contention "
                "during peak traffic."
            ),
            30,
            10,
            3.0,
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            prompt()
        )

    first = result.tasks[0]

    assert first.escalation.escalated is True
    assert first.analytics.attempt_count == 2

    assert (
        first.analytics.total_prompt_tokens
        == 22
    )

    assert (
        first.analytics.total_latency_seconds
        == 3.0
    )

    # Task 1:
    # LOW    1 × 1 = 1
    # MEDIUM 2 × 2 = 4
    #
    # Task 2:
    # MEDIUM 2 × 2 = 4
    #
    # Task 3:
    # HIGH   4 × 3 = 12
    #
    # Total = 21

    assert (
        result.analytics.normalized_compute_cost
        == 21.0
    )

    assert (
        result.analytics.escalation_overhead_compute
        == 1.0
    )

    assert (
        result.analytics.total_attempt_count
        == 4
    )


def test_legacy_multi_task_totals_remain_final_attempt_only():

    router = MultiTaskRouter()

    outputs = [
        generation(
            "",
            10,
            0,
            1.0,
        ),
        generation(
            "alice@example.com",
            12,
            2,
            2.0,
        ),
        generation(
            "Checkout is slow during peak traffic.",
            20,
            8,
            2.0,
        ),
        generation(
            (
                "The likely cause is resource contention "
                "during peak traffic."
            ),
            30,
            10,
            3.0,
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            prompt()
        )

    # Legacy values remain accepted/final attempts only.
    assert result.total_prompt_tokens == 62
    assert result.total_output_tokens == 20
    assert result.total_latency_seconds == 7.0

    # Analytics contains the failed LOW attempt too.
    assert (
        result.analytics.total_prompt_tokens
        == 72
    )

    assert (
        result.analytics.total_output_tokens
        == 20
    )

    assert (
        result.analytics.total_latency_seconds
        == 8.0
    )
