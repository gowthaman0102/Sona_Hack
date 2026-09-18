from unittest.mock import patch

from app.services.multi_task_router import MultiTaskRouter
from app.services.task_decomposer import TaskDecomposer


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


def test_shared_context_excludes_other_task_instructions():

    prompt = (
        "The customer email address is alice@example.com. "
        "The checkout becomes slow during peak traffic. "
        "Extract the customer email address, "
        "summarize the complaint, "
        "and analyze the root cause."
    )

    decomposer = TaskDecomposer()

    result = decomposer.decompose(
        prompt
    )

    context = (
        decomposer.extract_shared_context(
            prompt,
            result.tasks,
        )
    )

    assert (
        "alice@example.com"
        in context
    )

    assert (
        "checkout becomes slow"
        in context
    )

    assert (
        "Extract the customer email address"
        not in context
    )

    assert (
        "summarize the complaint"
        not in context
    )

    assert (
        "analyze the root cause"
        not in context
    )


def test_each_focused_prompt_has_only_its_assigned_instruction():

    prompt = (
        "The customer email address is alice@example.com. "
        "The checkout becomes slow during peak traffic. "
        "Extract the customer email address, "
        "summarize the complaint, "
        "and analyze the root cause."
    )

    router = MultiTaskRouter()

    outputs = [
        generation(
            "alice@example.com"
        ),
        generation(
            (
                "The customer reports slow "
                "checkout during peak traffic."
            )
        ),
        generation(
            (
                "The root cause is synchronous processing "
                "and resource contention during peak load."
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

    prompts = [
        call.kwargs["prompt"]
        for call in mocked.call_args_list
    ]

    assert (
        "Assigned subtask:\n"
        "Extract the customer email address"
        in prompts[0]
    )

    assert (
        "summarize the complaint"
        not in prompts[0].lower()
    )

    assert (
        "analyze the root cause"
        not in prompts[0].lower()
    )

    assert (
        "Assigned subtask:\n"
        "summarize the complaint"
        in prompts[1]
    )

    assert (
        "Extract the customer email address"
        not in prompts[1]
    )

    assert (
        "analyze the root cause"
        not in prompts[1].lower()
    )


def test_background_context_remains_available_to_all_tasks():

    prompt = (
        "Customer alice@example.com reports checkout "
        "slowdowns during peak traffic. "
        "Extract the customer email address, "
        "summarize the complaint, "
        "and analyze the root cause."
    )

    router = MultiTaskRouter()

    outputs = [
        generation(
            "alice@example.com"
        ),
        generation(
            (
                "Checkout becomes slow "
                "during peak traffic."
            )
        ),
        generation(
            (
                "The likely cause is backend resource "
                "contention during peak traffic."
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

        focused = call.kwargs["prompt"]

        assert (
            "alice@example.com"
            in focused
        )

        assert (
            "peak traffic"
            in focused
        )
