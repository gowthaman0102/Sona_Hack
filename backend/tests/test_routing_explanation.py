from app.core.model_registry import (
    ModelTier,
    get_model_by_tier,
)
from app.services.query_analyzer import QueryAnalyzer
from app.services.routing_explanation import RoutingExplanationService


analyzer = QueryAnalyzer()
service = RoutingExplanationService()


def explain(
    prompt: str,
    recommended: ModelTier,
    selected: ModelTier,
    override: bool = False,
    thinking: bool = False,
    thinking_override: bool = False,
):
    analysis = analyzer.analyze(prompt)

    return service.explain(
        analysis=analysis,
        recommended_tier=recommended,
        selected_tier=selected,
        selected_profile=get_model_by_tier(
            selected
        ),
        override_applied=override,
        thinking_enabled=thinking,
        thinking_override_applied=thinking_override,
    )


def test_low_tier_explanation():
    result = explain(
        "Extract the date from this sentence.",
        ModelTier.LOW,
        ModelTier.LOW,
    )

    assert "LOW" in result.summary
    assert "speed" in result.compute_quality_tradeoff.lower()


def test_medium_tier_explanation():
    result = explain(
        "Explain normalization with an example.",
        ModelTier.MEDIUM,
        ModelTier.MEDIUM,
    )

    assert "MEDIUM" in result.summary
    assert "balances" in result.compute_quality_tradeoff.lower()


def test_high_tier_explanation():
    result = explain(
        (
            "Analyze this Python backend, identify "
            "the root cause, compare two solutions, "
            "and recommend the best architecture."
        ),
        ModelTier.HIGH,
        ModelTier.HIGH,
        thinking=True,
    )

    assert "HIGH" in result.summary

    assert (
        "higher latency"
        in result.compute_quality_tradeoff.lower()
    )

    assert (
        "thinking mode was enabled"
        in result.reasoning_reason.lower()
    )


def test_complexity_grammar_extraction():
    result = explain(
        "Extract the date from this sentence.",
        ModelTier.LOW,
        ModelTier.LOW,
    )

    assert (
        "classified as an extraction task"
        in result.complexity_reason
    )


def test_complexity_grammar_analysis():
    result = explain(
        "Analyze this backend.",
        ModelTier.HIGH,
        ModelTier.HIGH,
    )

    assert (
        "classified as an analysis task"
        in result.complexity_reason
    )


def test_low_to_high_override_tradeoff():
    result = explain(
        "Extract the date from this sentence.",
        ModelTier.LOW,
        ModelTier.HIGH,
        override=True,
    )

    assert (
        "increases compute usage"
        in result.compute_quality_tradeoff
    )

    assert (
        "LOW to HIGH"
        in result.override_reason
    )


def test_high_to_low_override_tradeoff():
    result = explain(
        (
            "Analyze this backend architecture, "
            "identify the root cause, compare solutions, "
            "and recommend a redesign."
        ),
        ModelTier.HIGH,
        ModelTier.LOW,
        override=True,
    )

    assert (
        "reduces compute usage"
        in result.compute_quality_tradeoff
    )

    assert (
        "may reduce response quality"
        in result.compute_quality_tradeoff
    )


def test_same_tier_override():
    result = explain(
        "Explain normalization.",
        ModelTier.MEDIUM,
        ModelTier.MEDIUM,
        override=True,
    )

    assert (
        "trade-off is unchanged"
        in result.compute_quality_tradeoff
    )

    assert (
        "matches AURA's recommendation"
        in result.override_reason
    )


def test_detected_signals():
    result = explain(
        (
            "Analyze this Python API, identify the "
            "root cause, compare two solutions, "
            "and recommend the best redesign."
        ),
        ModelTier.HIGH,
        ModelTier.HIGH,
        thinking=True,
    )

    assert (
        "technical_or_code_content"
        in result.signals
    )

    assert (
        "reasoning_markers_detected"
        in result.signals
    )

    assert (
        "multiple_requirements"
        in result.signals
    )
