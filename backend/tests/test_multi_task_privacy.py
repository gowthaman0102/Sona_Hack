from unittest.mock import patch

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


def sensitive_prompt():
    return (
        "The customer email is alice@example.com. "
        "The checkout becomes slow during peak traffic. "
        "Extract the customer email, "
        "summarize the complaint, "
        "and analyze the root cause."
    )


def safe_outputs():
    return [
        generation(
            "alice@example.com"
        ),
        generation(
            (
                "The customer reports slow checkout "
                "during peak traffic."
            )
        ),
        generation(
            (
                "The likely cause is resource contention "
                "under concurrent load."
            )
        ),
    ]


def test_multi_task_result_exposes_overall_privacy():

    router = MultiTaskRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=safe_outputs(),
    ):

        result = router.execute(
            sensitive_prompt()
        )

    assert (
        result.privacy.contains_sensitive_data
        is True
    )

    assert (
        "email"
        in result.privacy.categories
    )

    assert result.privacy.requires_local is True


def test_shared_sensitive_context_propagates_to_every_subtask():

    router = MultiTaskRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=safe_outputs(),
    ):

        result = router.execute(
            sensitive_prompt()
        )

    assert result.task_count == 3

    for task in result.tasks:

        assert task.privacy.requires_local is True

        assert (
            "email"
            in task.privacy.categories
        )

        assert (
            task.privacy_policy.privacy_enforced
            is True
        )

        assert (
            task.privacy_policy.execution_scope
            == "local_only"
        )

        assert (
            task.privacy_policy.external_routing_allowed
            is False
        )

        assert (
            task.privacy_policy.selected_model_is_local
            is True
        )


def test_non_sensitive_multi_task_remains_standard():

    router = MultiTaskRouter()

    prompt = (
        "Extract the date, "
        "summarize the paragraph, "
        "and analyze the root cause."
    )

    outputs = [
        generation(
            "25 September"
        ),
        generation(
            (
                "The paragraph provides a clear "
                "summary of the main topic."
            )
        ),
        generation(
            (
                "The likely cause is resource contention "
                "combined with synchronous processing."
            )
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

    assert result.privacy.requires_local is False

    for task in result.tasks:

        assert (
            task.privacy_policy.privacy_enforced
            is False
        )

        assert (
            task.privacy_policy.execution_scope
            == "standard"
        )


def test_sensitive_subtask_does_not_contaminate_unrelated_subtask():
    router = MultiTaskRouter()

    prompt = (
        'Summarize this text: "Project meeting is Monday." '
        'Then identify whether this contains sensitive information: '
        '"My Aadhaar number is 1234 5678 9012."'
    )

    outputs = [
        generation("Project meeting: Monday"),
        generation("contains sensitive information"),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):
        result = router.execute(prompt)

    assert result.privacy.requires_local is True
    assert result.tasks[0].privacy.requires_local is False
    assert result.tasks[0].privacy.risk_level == "none"
    assert result.tasks[0].privacy_policy.execution_scope == "standard"
    assert result.tasks[1].privacy.requires_local is True
    assert result.tasks[1].privacy_policy.execution_scope == "local_only"


def test_high_risk_shared_secret_propagates_high_risk():

    router = MultiTaskRouter()

    prompt = (
        "password=Secret123. "
        "Extract the credential, "
        "summarize the security issue, "
        "and analyze the exposure risk."
    )

    outputs = [
        generation(
            "Secret123"
        ),
        generation(
            (
                "A plaintext password is exposed "
                "inside the request."
            )
        ),
        generation(
            (
                "The exposed credential can be misused "
                "for unauthorized access and should be "
                "rotated immediately."
            )
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

    assert result.privacy.risk_level == "high"

    for task in result.tasks:

        assert (
            task.privacy.risk_level
            == "high"
        )

        assert (
            "password_or_secret"
            in task.privacy.categories
        )


def test_privacy_is_preserved_during_escalation():

    router = MultiTaskRouter()

    outputs = [
        # Task 1 LOW fails
        generation(
            ""
        ),

        # Task 1 MEDIUM succeeds
        generation(
            "alice@example.com"
        ),

        # Task 2 MEDIUM succeeds
        generation(
            (
                "The customer reports slow checkout "
                "during peak traffic."
            )
        ),

        # Task 3 HIGH succeeds
        generation(
            (
                "The likely cause is synchronous processing "
                "combined with resource contention during "
                "concurrent requests."
            )
        ),
    ]

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=outputs,
    ):

        result = router.execute(
            sensitive_prompt()
        )

    first = result.tasks[0]

    assert first.escalation.escalated is True

    assert (
        first.selected_tier
        == "medium"
    )

    assert (
        first.privacy_policy.execution_scope
        == "local_only"
    )

    assert (
        first.privacy_policy.external_routing_allowed
        is False
    )


def test_each_selected_model_is_approved_local_model():

    router = MultiTaskRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=safe_outputs(),
    ):

        result = router.execute(
            sensitive_prompt()
        )

    allowed = {
        "qwen3:1.7b",
        "qwen3:4b",
        "qwen3:8b",
    }

    for task in result.tasks:

        assert (
            task.selected_model
            in allowed
        )
