from app.services.confidence_evaluator import ConfidenceEvaluator
from app.services.query_analyzer import QueryAnalyzer


analyzer = QueryAnalyzer()
evaluator = ConfidenceEvaluator()


def test_good_extraction_response_has_high_confidence():
    analysis = analyzer.analyze(
        "Extract the date from this sentence."
    )

    result = evaluator.evaluate(
        "25 September 2026",
        analysis,
    )

    assert result.score >= 0.80
    assert result.level == "high"
    assert result.should_escalate is False


def test_good_explanation_has_high_confidence():
    analysis = analyzer.analyze(
        "Explain database normalization."
    )

    response = (
        "Database normalization organizes relational data "
        "into structured tables to reduce duplication and "
        "improve consistency. It separates related entities "
        "and connects them using keys."
    )

    result = evaluator.evaluate(
        response,
        analysis,
    )

    assert result.score >= 0.80
    assert result.should_escalate is False


def test_empty_response_escalates():
    analysis = analyzer.analyze(
        "Explain database normalization."
    )

    result = evaluator.evaluate(
        "",
        analysis,
    )

    assert result.score < 0.65
    assert result.level == "low"
    assert result.should_escalate is True
    assert "empty_response" in result.reasons


def test_short_complex_response_escalates():
    analysis = analyzer.analyze(
        (
            "Analyze this backend architecture, identify "
            "the root cause, compare alternatives, and "
            "recommend the best redesign."
        )
    )

    result = evaluator.evaluate(
        "Use caching.",
        analysis,
    )

    assert result.score < 0.65
    assert result.should_escalate is True

    assert (
        "insufficient_detail_for_complex_task"
        in result.reasons
    )


def test_failure_language_reduces_confidence():
    analysis = analyzer.analyze(
        "Explain database normalization."
    )

    result = evaluator.evaluate(
        "I don't know the answer to this question.",
        analysis,
    )

    assert result.score < 0.65
    assert result.should_escalate is True

    assert (
        "failure_language_detected"
        in result.reasons
    )


def test_uncertainty_reduces_confidence():
    analysis = analyzer.analyze(
        "Explain database normalization."
    )

    result = evaluator.evaluate(
        (
            "I am not sure, but database normalization "
            "probably means organizing data into tables "
            "to reduce repeated information."
        ),
        analysis,
    )

    assert result.score < 1.0

    assert (
        "uncertainty_language_detected"
        in result.reasons
    )


def test_reasoning_leak_reduces_confidence():
    analysis = analyzer.analyze(
        "Explain database normalization."
    )

    result = evaluator.evaluate(
        (
            "<think>Private reasoning</think> "
            "Database normalization reduces duplication "
            "and improves consistency across tables."
        ),
        analysis,
    )

    assert result.score < 0.65
    assert result.should_escalate is True

    assert (
        "reasoning_leak_detected"
        in result.reasons
    )


def test_detailed_analysis_has_high_confidence():
    analysis = analyzer.analyze(
        (
            "Analyze this backend architecture, identify "
            "the root cause, compare alternatives, and "
            "recommend the best redesign."
        )
    )

    response = (
        "The primary bottleneck is synchronous database access "
        "combined with a single application instance. Under "
        "high load, requests queue while database connections "
        "remain occupied. One option is vertical scaling, which "
        "is simple but limited. Another is horizontal scaling "
        "with stateless application instances and connection "
        "pooling. The second approach is preferable because it "
        "improves throughput, resilience, and future scalability."
    )

    result = evaluator.evaluate(
        response,
        analysis,
    )

    assert result.score >= 0.80
    assert result.should_escalate is False
