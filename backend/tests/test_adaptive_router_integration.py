from unittest.mock import patch

from app.models.learning import LearningOutcome
from app.services.adaptive_routing_policy import (
    AdaptiveRoutingPolicy,
)
from app.services.intelligent_router import (
    IntelligentRouter,
)
from app.services.multi_task_router import (
    MultiTaskRouter,
)
from app.services.performance_history_store import (
    PerformanceHistoryStore,
)


def generation(
    response,
    latency=1.0,
):

    return {
        "tier": "test",
        "model_name": "mock",
        "display_name": "mock",
        "compute_score": 1,
        "thinking_enabled": False,
        "response": response,
        "prompt_tokens": 10,
        "output_tokens": 5,
        "latency_seconds": latency,
        "tokens_per_second": 5.0,
    }


def record_many(
    store,
    *,
    task_type,
    tier,
    successes,
    failures,
):

    models = {
        "low": "qwen3:1.7b",
        "medium": "qwen3:4b",
        "high": "qwen3:8b",
    }

    for _ in range(successes):

        store.record(
            LearningOutcome(
                task_type=task_type,
                tier=tier,
                model_name=models[tier],
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
                model_name=models[tier],
                success=False,
                confidence_score=0.4,
                latency_seconds=1.0,
                normalized_compute_cost=1.0,
            )
        )


def extraction_upgrade_policy(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
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

    return AdaptiveRoutingPolicy(
        store
    )


def test_default_single_router_has_no_policy():

    router = IntelligentRouter()

    assert router.adaptive_policy is None


def test_default_multi_router_has_no_policy():

    router = MultiTaskRouter()

    assert router.adaptive_policy is None


def test_single_router_adaptively_starts_medium(
    tmp_path,
):

    policy = extraction_upgrade_policy(
        tmp_path
    )

    router = IntelligentRouter(
        adaptive_policy=policy
    )

    called_tiers = []

    def generate(
        *,
        tier,
        prompt,
        system_prompt,
        think,
    ):

        called_tiers.append(
            tier.value
        )

        return generation(
            "alice@example.com"
        )

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=generate,
    ):

        result = router.route(
            "Extract the email alice@example.com"
        )

    assert called_tiers == [
        "medium"
    ]

    assert (
        result.routing.recommended_tier
        == "low"
    )

    assert (
        result.escalation.initial_tier
        == "medium"
    )

    assert (
        result.routing.selected_tier
        == "medium"
    )


def test_manual_override_beats_adaptive_learning(
    tmp_path,
):

    policy = extraction_upgrade_policy(
        tmp_path
    )

    router = IntelligentRouter(
        adaptive_policy=policy
    )

    called_tiers = []

    def generate(
        *,
        tier,
        prompt,
        system_prompt,
        think,
    ):

        called_tiers.append(
            tier.value
        )

        return generation(
            "alice@example.com"
        )

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=generate,
    ):

        result = router.route(
            "Extract the email alice@example.com",
            override_tier="low",
        )

    assert called_tiers == [
        "low"
    ]

    assert result.routing.override_applied is True

    assert (
        result.routing.selected_tier
        == "low"
    )


def test_adaptive_start_still_allows_escalation(
    tmp_path,
):

    policy = extraction_upgrade_policy(
        tmp_path
    )

    router = IntelligentRouter(
        adaptive_policy=policy
    )

    called_tiers = []

    outputs = [
        generation(
            ""
        ),
        generation(
            "alice@example.com"
        ),
    ]

    def generate(
        *,
        tier,
        prompt,
        system_prompt,
        think,
    ):

        called_tiers.append(
            tier.value
        )

        return outputs.pop(0)

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=generate,
    ):

        result = router.route(
            "Extract the email alice@example.com"
        )

    assert called_tiers == [
        "medium",
        "high",
    ]

    assert (
        result.escalation.initial_tier
        == "medium"
    )

    assert (
        result.escalation.final_tier
        == "high"
    )

    assert result.escalation.escalated is True


def test_multi_router_adaptively_upgrades_extraction(
    tmp_path,
):

    policy = extraction_upgrade_policy(
        tmp_path
    )

    router = MultiTaskRouter(
        adaptive_policy=policy
    )

    prompt = (
        "The customer email is alice@example.com. "
        "Checkout becomes slow during peak traffic. "
        "Extract the customer email, "
        "summarize the complaint, "
        "and analyze the root cause."
    )

    called_tiers = []

    responses = [
        "alice@example.com",
        (
            "The customer reports that checkout "
            "becomes slow during peak traffic."
        ),
        (
            "The likely root cause is resource contention "
            "during peak traffic, where database connections "
            "become saturated and synchronous operations "
            "cause requests to queue."
        ),
    ]

    def generate(
        *,
        tier,
        prompt,
        system_prompt,
        think,
    ):

        called_tiers.append(
            tier.value
        )

        return generation(
            responses.pop(0)
        )

    with patch.object(
        router.models,
        "generate_for_tier",
        side_effect=generate,
    ):

        result = router.execute(
            prompt
        )

    assert result.task_count == 3

    first = result.tasks[0]

    assert first.task_type == "extraction"

    # Analyzer baseline remains visible.
    assert first.recommended_tier == "low"

    # Learning changes actual start/selection.
    assert first.escalation.initial_tier == "medium"
    assert first.selected_tier == "medium"

    assert called_tiers[0] == "medium"


def test_learning_does_not_remove_privacy_requirement(
    tmp_path,
):

    policy = extraction_upgrade_policy(
        tmp_path
    )

    router = IntelligentRouter(
        adaptive_policy=policy
    )

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=generation(
            "alice@example.com"
        ),
    ):

        result = router.route(
            "Extract the email alice@example.com"
        )

    assert result.privacy.requires_local is True

    assert (
        result.privacy_policy.external_routing_allowed
        is False
    )

    assert (
        result.privacy_policy.selected_model_is_local
        is True
    )


def test_high_capability_baseline_is_never_downgraded(
    tmp_path,
):

    store = PerformanceHistoryStore(
        tmp_path / "history.json"
    )

    record_many(
        store,
        task_type="analysis",
        tier="medium",
        successes=20,
        failures=0,
    )

    record_many(
        store,
        task_type="analysis",
        tier="high",
        successes=0,
        failures=5,
    )

    policy = AdaptiveRoutingPolicy(
        store
    )

    result = policy.recommend(
        task_type="analysis",
        baseline_tier="high",
    )

    assert result.recommended_tier == "high"
    assert result.learning_applied is False
