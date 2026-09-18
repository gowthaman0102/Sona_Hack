import pytest

from app.benchmarking.dataset import (
    BenchmarkCase,
)

from app.benchmarking.evaluator import (
    evaluate_response,
    normalize_response,
)


def make_case(
    *,
    evaluator: str,
    expected: tuple[str, ...],
) -> BenchmarkCase:
    return BenchmarkCase(
        case_id="test-case",
        task_type="general",
        difficulty="low",
        prompt="test",
        evaluator=evaluator,
        expected=expected,
        description="test",
    )


def test_normalize_response_is_case_insensitive():
    assert (
        normalize_response(
            "  Hello   WORLD  "
        )
        == "hello world"
    )


def test_normalize_response_removes_code_fences():
    assert (
        normalize_response(
            "```python\nprint('hi')\n```"
        )
        == "print('hi')"
    )


def test_exact_evaluator_passes_normalized_value():
    case = make_case(
        evaluator="exact",
        expected=("chennai",),
    )

    result = evaluate_response(
        case,
        "Chennai.",
    )

    assert result.passed is True
    assert result.score == 1.0


def test_exact_evaluator_fails_different_value():
    case = make_case(
        evaluator="exact",
        expected=("1800",),
    )

    result = evaluate_response(
        case,
        "1700",
    )

    assert result.passed is False
    assert result.score == 0.0


def test_contains_all_passes_when_every_term_exists():
    case = make_case(
        evaluator="contains_all",
        expected=(
            "client",
            "server",
        ),
    )

    result = evaluate_response(
        case,
        "The client sends a request to the server.",
    )

    assert result.passed is True
    assert result.score == 1.0
    assert result.missing_expectations == ()


def test_contains_all_returns_partial_score():
    case = make_case(
        evaluator="contains_all",
        expected=(
            "cache",
            "database",
        ),
    )

    result = evaluate_response(
        case,
        "Use a cache for repeated requests.",
    )

    assert result.passed is False
    assert result.score == 0.5
    assert result.missing_expectations == (
        "database",
    )


def test_contains_any_passes_with_one_match():
    case = make_case(
        evaluator="contains_any",
        expected=(
            "routing",
            "model",
            "complexity",
        ),
    )

    result = evaluate_response(
        case,
        "The system selects a model dynamically.",
    )

    assert result.passed is True
    assert result.score == 1.0


def test_contains_any_fails_without_match():
    case = make_case(
        evaluator="contains_any",
        expected=(
            "routing",
            "model",
        ),
    )

    result = evaluate_response(
        case,
        "This sentence contains neither concept.",
    )

    assert result.passed is False
    assert result.score == 0.0


def test_empty_response_fails():
    case = make_case(
        evaluator="contains_all",
        expected=("answer",),
    )

    result = evaluate_response(
        case,
        "   ",
    )

    assert result.passed is False
    assert result.score == 0.0
    assert result.reason == "empty response"


def test_unsupported_evaluator_raises():
    case = BenchmarkCase(
        case_id="bad-case",
        task_type="general",
        difficulty="low",
        prompt="test",
        evaluator="unsupported",  # type: ignore[arg-type]
        expected=("x",),
        description="test",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported evaluator",
    ):
        evaluate_response(
            case,
            "x",
        )
