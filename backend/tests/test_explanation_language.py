from app.core.model_registry import (
    ModelTier,
    get_model_by_tier,
)
from app.services.query_analyzer import QueryAnalyzer
from app.services.routing_explanation import RoutingExplanationService


analyzer = QueryAnalyzer()
service = RoutingExplanationService()


def build_explanation(
    prompt: str,
    recommended: ModelTier,
    selected: ModelTier,
    override: bool = False,
    thinking: bool = False,
):
    analysis = analyzer.analyze(
        prompt
    )

    return service.explain(
        analysis=analysis,
        recommended_tier=recommended,
        selected_tier=selected,
        selected_profile=get_model_by_tier(
            selected
        ),
        override_applied=override,
        thinking_enabled=thinking,
        thinking_override_applied=False,
    )


def test_extraction_uses_an():
    result = build_explanation(
        "Extract the date from this sentence.",
        ModelTier.LOW,
        ModelTier.LOW,
    )

    assert (
        "classified as an extraction task"
        in result.complexity_reason
    )


def test_analysis_uses_an():
    result = build_explanation(
        "Analyze this backend architecture.",
        ModelTier.HIGH,
        ModelTier.HIGH,
    )

    assert (
        "classified as an analysis task"
        in result.complexity_reason
    )


def test_explanation_uses_an():
    result = build_explanation(
        "Explain normalization.",
        ModelTier.MEDIUM,
        ModelTier.MEDIUM,
    )

    assert (
        "classified as an explanation task"
        in result.complexity_reason
    )


def test_planning_uses_a():
    result = build_explanation(
        "Design a scalable backend architecture.",
        ModelTier.HIGH,
        ModelTier.HIGH,
    )

    assert (
        "classified as a planning task"
        in result.complexity_reason
    )


def test_coding_uses_a():
    result = build_explanation(
        "Write Python code for binary search.",
        ModelTier.MEDIUM,
        ModelTier.MEDIUM,
    )

    assert (
        "classified as a coding task"
        in result.complexity_reason
    )


def test_override_tradeoff_has_correct_spacing():
    result = build_explanation(
        "Extract the date from this sentence.",
        ModelTier.LOW,
        ModelTier.HIGH,
        override=True,
    )

    assert (
        "access to a more capable model"
        in result.compute_quality_tradeoff
    )

    assert (
        "access toa"
        not in result.compute_quality_tradeoff
    )
