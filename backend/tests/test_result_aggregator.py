from unittest.mock import patch

from app.services.multi_task_router import MultiTaskRouter
from app.services.result_aggregator import ResultAggregator


def generation(
    response: str,
    prompt_tokens: int = 10,
    output_tokens: int = 5,
    latency: float = 1.0,
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
        "tokens_per_second": 10.0,
    }


def test_aggregated_response_contains_all_subtasks():
    router = MultiTaskRouter()

    outputs = [
        generation(
            "customer@example.com"
        ),
        generation(
            (
                "The customer reports repeated "
                "checkout slowdowns during peak traffic."
            )
        ),
        generation(
            (
                "The likely root cause is synchronous database "
                "access combined with connection contention "
                "under concurrent traffic, which causes request "
                "queues and increased latency."
            )
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            (
                "Extract the customer email address, "
                "summarize the complaint, "
                "and analyze the root cause of the issue."
            )
        )

    assert (
        "customer@example.com"
        in result.aggregated_response
    )

    assert (
        "checkout slowdowns"
        in result.aggregated_response
    )

    assert (
        "synchronous database"
        in result.aggregated_response
    )


def test_aggregation_preserves_task_order():
    router = MultiTaskRouter()

    outputs = [
        generation("FIRST_RESULT"),
        generation(
            (
                "SECOND_RESULT contains enough words "
                "to satisfy summarization confidence."
            )
        ),
        generation(
            (
                "THIRD_RESULT contains a detailed explanation "
                "of the likely root cause with sufficient "
                "context for the complex analysis request."
            )
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            (
                "Extract the date, "
                "summarize the text, "
                "and analyze the root cause."
            )
        )

    first = result.aggregated_response.index(
        "FIRST_RESULT"
    )

    second = result.aggregated_response.index(
        "SECOND_RESULT"
    )

    third = result.aggregated_response.index(
        "THIRD_RESULT"
    )

    assert first < second < third


def test_aggregation_has_task_headers():
    router = MultiTaskRouter()

    outputs = [
        generation("25 September"),
        generation(
            (
                "The text contains enough detail "
                "for this summary response."
            )
        ),
        generation(
            (
                "The analysis explains the underlying cause "
                "with enough detail to satisfy confidence."
            )
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            (
                "Extract the date, "
                "summarize the text, "
                "and analyze the cause."
            )
        )

    assert (
        "Task 1 - Extraction"
        in result.aggregated_response
    )

    assert (
        "Task 2 - Summarization"
        in result.aggregated_response
    )

    assert (
        "Task 3 - Analysis"
        in result.aggregated_response
    )


def test_single_task_aggregation_returns_plain_response():
    aggregator = ResultAggregator()

    router = MultiTaskRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=generation(
            (
                "Database normalization reduces "
                "data duplication across tables."
            )
        ),
    ):

        result = router.execute(
            "Explain database normalization."
        )

    assert result.task_count == 1

    assert result.aggregated_response == (
        "Database normalization reduces "
        "data duplication across tables."
    )


def test_totals_are_calculated():
    router = MultiTaskRouter()

    outputs = [
        generation(
            "customer@example.com",
            prompt_tokens=10,
            output_tokens=2,
            latency=1.0,
        ),
        generation(
            (
                "The complaint describes checkout "
                "slowdowns during peak traffic."
            ),
            prompt_tokens=20,
            output_tokens=10,
            latency=2.0,
        ),
        generation(
            (
                "The likely root cause is synchronous database "
                "access and connection contention under concurrent "
                "load, causing queued requests and increased latency."
            ),
            prompt_tokens=30,
            output_tokens=20,
            latency=3.0,
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            (
                "Extract the customer email address, "
                "summarize the complaint, "
                "and analyze the root cause of the issue."
            )
        )

    assert result.total_prompt_tokens == 60
    assert result.total_output_tokens == 32
    assert result.total_latency_seconds == 6.0

    assert (
        result.total_compute_score
        == 7
    )
