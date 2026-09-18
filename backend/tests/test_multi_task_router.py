from unittest.mock import patch

from app.core.model_registry import ModelTier
from app.services.multi_task_router import MultiTaskRouter


def generation(
    response: str,
):
    return {
        "tier": "test",
        "model_name": "mock",
        "display_name": "mock",
        "compute_score": 1,
        "thinking_enabled": False,
        "response": response,
        "prompt_tokens": 10,
        "output_tokens": 10,
        "latency_seconds": 1.0,
        "tokens_per_second": 10.0,
    }


def mixed_prompt():
    return (
        "Extract the customer email address, "
        "summarize the complaint, "
        "and analyze the root cause of the issue."
    )


def test_required_multi_task_prompts_decompose_into_independent_tasks():
    router = MultiTaskRouter()

    scenarios = [
        (
            'Extract the email from "Contact alice@example.com". '
            'Then convert "hello aura" to uppercase.',
            [
                "Extract the email from \"Contact alice@example.com\"",
                'convert "hello aura" to uppercase',
            ],
        ),
        (
            'Extract the phone number from "Call me at 9876543210". '
            'Then explain in simple terms how binary search works. '
            'Then create a short migration plan for moving a small REST API '
            'from SQLite to PostgreSQL.',
            [
                'Extract the phone number from "Call me at 9876543210"',
                "explain in simple terms how binary search works",
                "create a short migration plan for moving a small REST API "
                "from SQLite to PostgreSQL",
            ],
        ),
        (
            "Calculate 2+2. Then calculate 7*6.",
            [
                "Calculate 2+2",
                "calculate 7*6",
            ],
        ),
        (
            'Summarize this text: "Project meeting is Monday." '
            'Then identify whether this contains sensitive information: '
            '"My Aadhaar number is 1234 5678 9012."',
            [
                'Summarize this text: "Project meeting is Monday."',
                'identify whether this contains sensitive information: '
                '"My Aadhaar number is 1234 5678 9012."',
            ],
        ),
    ]

    for prompt, expected_tasks in scenarios:
        result = router.decomposer.decompose(prompt)

        assert result.is_multi_task is True
        assert result.task_count == len(expected_tasks)
        assert [task.text for task in result.tasks] == expected_tasks


def test_three_subtasks_execute_independently_without_escalation():
    router = MultiTaskRouter()

    outputs = [
        generation(
            "customer@example.com"
        ),
        generation(
            (
                "The customer reports persistent "
                "performance problems during checkout "
                "when traffic is unusually high."
            )
        ),
        generation(
            (
                "The likely root cause is synchronous database "
                "access combined with connection contention "
                "under concurrent load. Requests queue while "
                "database connections remain occupied, causing "
                "latency across the checkout workflow."
            )
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ) as mocked:

        result = router.execute(
            mixed_prompt()
        )

    assert result.task_count == 3
    assert mocked.call_count == 3

    assert (
        result.tasks[0]
        .escalation.escalated
        is False
    )

    assert (
        result.tasks[1]
        .escalation.escalated
        is False
    )

    assert (
        result.tasks[2]
        .escalation.escalated
        is False
    )


def test_each_subtask_starts_at_correct_tier():
    router = MultiTaskRouter()

    outputs = [
        generation(
            "customer@example.com"
        ),
        generation(
            (
                "The customer reports persistent "
                "performance problems during checkout."
            )
        ),
        generation(
            (
                "The likely root cause is synchronous database "
                "access combined with contention under load. "
                "This creates request queues and increases "
                "latency during concurrent operations."
            )
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ) as mocked:

        router.execute(
            mixed_prompt()
        )

    calls = mocked.call_args_list

    assert (
        calls[0].kwargs["tier"]
        == ModelTier.LOW
    )

    assert (
        calls[1].kwargs["tier"]
        == ModelTier.MEDIUM
    )

    assert (
        calls[2].kwargs["tier"]
        == ModelTier.HIGH
    )


def test_low_subtask_can_escalate_to_medium():
    router = MultiTaskRouter()

    outputs = [
        generation(
            ""
        ),
        generation(
            "customer@example.com"
        ),
        generation(
            (
                "The complaint describes persistent "
                "checkout performance degradation."
            )
        ),
        generation(
            (
                "The root cause is synchronous database access "
                "combined with resource contention during "
                "concurrent requests, producing queueing and "
                "increased latency throughout the backend."
            )
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ) as mocked:

        result = router.execute(
            mixed_prompt()
        )

    first = result.tasks[0]

    assert (
        first.recommended_tier
        == "low"
    )

    assert (
        first.selected_tier
        == "medium"
    )

    assert (
        first.selected_model
        == "qwen3:4b"
    )

    assert (
        first.escalation.escalated
        is True
    )

    assert (
        len(
            first.escalation.attempts
        )
        == 2
    )

    assert mocked.call_count == 4


def test_medium_subtask_can_escalate_to_high():
    router = MultiTaskRouter()

    outputs = [
        generation(
            "customer@example.com"
        ),
        generation(
            "I don't know."
        ),
        generation(
            (
                "The complaint describes repeated checkout "
                "slowdowns during busy periods and indicates "
                "that customers experience delayed responses "
                "while completing transactions."
            )
        ),
        generation(
            (
                "The root cause is synchronous database access "
                "and contention under concurrent traffic. "
                "Connections remain occupied while requests "
                "queue, increasing end-to-end latency."
            )
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            mixed_prompt()
        )

    second = result.tasks[1]

    assert (
        second.recommended_tier
        == "medium"
    )

    assert (
        second.selected_tier
        == "high"
    )

    assert (
        second.selected_model
        == "qwen3:8b"
    )

    assert (
        second.escalation.escalated
        is True
    )


def test_high_subtask_is_escalation_ceiling():
    router = MultiTaskRouter()

    outputs = [
        generation(
            "customer@example.com"
        ),
        generation(
            (
                "The customer reports persistent "
                "checkout performance problems."
            )
        ),
        generation(
            "Use caching."
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ) as mocked:

        result = router.execute(
            mixed_prompt()
        )

    third = result.tasks[2]

    assert (
        third.selected_tier
        == "high"
    )

    assert (
        third.confidence.should_escalate
        is True
    )

    assert (
        third.escalation.escalated
        is False
    )

    assert (
        "no stronger configured model"
        in third.escalation.reason.lower()
    )

    assert mocked.call_count == 3


def test_escalation_is_independent_per_subtask():
    router = MultiTaskRouter()

    outputs = [
        generation(
            "customer@example.com"
        ),
        generation(
            "I don't know."
        ),
        generation(
            (
                "The complaint describes severe checkout "
                "slowdowns during high traffic and repeated "
                "delays while customers complete transactions."
            )
        ),
        generation(
            (
                "The likely cause is synchronous database "
                "processing combined with connection contention. "
                "Under concurrency, database connections remain "
                "occupied and requests accumulate in queues."
            )
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            mixed_prompt()
        )

    assert (
        result.tasks[0]
        .escalation.escalated
        is False
    )

    assert (
        result.tasks[1]
        .escalation.escalated
        is True
    )

    assert (
        result.tasks[2]
        .escalation.escalated
        is False
    )


def test_original_context_is_preserved_during_escalation():
    router = MultiTaskRouter()

    prompt = mixed_prompt()

    outputs = [
        generation(""),
        generation(
            "customer@example.com"
        ),
        generation(
            (
                "The complaint describes a persistent "
                "checkout performance issue."
            )
        ),
        generation(
            (
                "The likely cause is database contention "
                "and synchronous request processing under "
                "concurrent load."
            )
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ) as mocked:

        router.execute(
            prompt
        )

    for call in mocked.call_args_list:

        focused_prompt = (
            call.kwargs["prompt"]
        )

        assert (
            "Background context:"
            in focused_prompt
        )

        assert (
            "Assigned subtask:"
            in focused_prompt
        )


def test_high_complexity_high_task_uses_thinking():
    router = MultiTaskRouter()

    prompt = (
        "Extract the date, "
        "summarize the paragraph, "
        "and analyze why this Python backend becomes "
        "slow under heavy traffic because database "
        "access is synchronous and resource contention "
        "increases during concurrent requests."
    )

    outputs = [
        generation(
            "25 September"
        ),
        generation(
            (
                "The paragraph provides a sufficiently "
                "detailed summary of the main information."
            )
        ),
        generation(
            (
                "The backend slows because synchronous database "
                "access blocks request processing under concurrent "
                "traffic. Resource contention increases as active "
                "requests compete for limited connections, causing "
                "queues and progressively higher latency."
            )
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ) as mocked:

        router.execute(
            prompt
        )

    calls = mocked.call_args_list

    assert (
        calls[0].kwargs["think"]
        is False
    )

    assert (
        calls[1].kwargs["think"]
        is False
    )

    assert (
        calls[2].kwargs["think"]
        is True
    )
