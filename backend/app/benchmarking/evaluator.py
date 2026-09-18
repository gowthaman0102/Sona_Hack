from __future__ import annotations

import re
from dataclasses import dataclass

from app.benchmarking.dataset import (
    BenchmarkCase,
)


@dataclass(
    frozen=True,
    slots=True,
)
class BenchmarkEvaluation:
    passed: bool
    score: float
    matched_expectations: tuple[str, ...]
    missing_expectations: tuple[str, ...]
    normalized_response: str
    reason: str


def normalize_response(
    response: str,
) -> str:
    text = response.strip().lower()

    text = re.sub(
        r"```(?:\w+)?",
        "",
        text,
    )

    text = text.replace(
        "```",
        "",
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _normalize_exact_value(
    value: str,
) -> str:
    text = normalize_response(
        value
    )

    text = text.strip(
        " \t\r\n"
        "\"'"
        "`"
        ".,;:!?"
    )

    return text


def evaluate_response(
    case: BenchmarkCase,
    response: str,
) -> BenchmarkEvaluation:
    normalized = normalize_response(
        response
    )

    if not normalized:
        return BenchmarkEvaluation(
            passed=False,
            score=0.0,
            matched_expectations=(),
            missing_expectations=case.expected,
            normalized_response=normalized,
            reason="empty response",
        )

    if case.evaluator == "exact":
        return _evaluate_exact(
            case=case,
            normalized_response=normalized,
        )

    if case.evaluator == "contains_all":
        return _evaluate_contains_all(
            case=case,
            normalized_response=normalized,
        )

    if case.evaluator == "contains_any":
        return _evaluate_contains_any(
            case=case,
            normalized_response=normalized,
        )

    raise ValueError(
        f"Unsupported evaluator: {case.evaluator}"
    )


def _evaluate_exact(
    case: BenchmarkCase,
    normalized_response: str,
) -> BenchmarkEvaluation:
    normalized_actual = (
        _normalize_exact_value(
            normalized_response
        )
    )

    expected_values = tuple(
        _normalize_exact_value(
            value
        )
        for value in case.expected
    )

    matched = tuple(
        value
        for value in expected_values
        if normalized_actual == value
    )

    passed = bool(
        matched
    )

    return BenchmarkEvaluation(
        passed=passed,
        score=1.0 if passed else 0.0,
        matched_expectations=matched,
        missing_expectations=(
            ()
            if passed
            else expected_values
        ),
        normalized_response=normalized_response,
        reason=(
            "exact match"
            if passed
            else "exact match failed"
        ),
    )


def _evaluate_contains_all(
    case: BenchmarkCase,
    normalized_response: str,
) -> BenchmarkEvaluation:
    expected_values = tuple(
        normalize_response(
            value
        )
        for value in case.expected
    )

    matched = tuple(
        value
        for value in expected_values
        if value in normalized_response
    )

    missing = tuple(
        value
        for value in expected_values
        if value not in normalized_response
    )

    total = len(
        expected_values
    )

    score = (
        len(matched) / total
        if total
        else 1.0
    )

    passed = (
        len(missing) == 0
    )

    return BenchmarkEvaluation(
        passed=passed,
        score=score,
        matched_expectations=matched,
        missing_expectations=missing,
        normalized_response=normalized_response,
        reason=(
            "all required expectations matched"
            if passed
            else "one or more required expectations missing"
        ),
    )


def _evaluate_contains_any(
    case: BenchmarkCase,
    normalized_response: str,
) -> BenchmarkEvaluation:
    expected_values = tuple(
        normalize_response(
            value
        )
        for value in case.expected
    )

    matched = tuple(
        value
        for value in expected_values
        if value in normalized_response
    )

    missing = tuple(
        value
        for value in expected_values
        if value not in normalized_response
    )

    passed = bool(
        matched
    )

    score = (
        1.0
        if passed
        else 0.0
    )

    return BenchmarkEvaluation(
        passed=passed,
        score=score,
        matched_expectations=matched,
        missing_expectations=missing,
        normalized_response=normalized_response,
        reason=(
            "at least one expected concept matched"
            if passed
            else "no expected concept matched"
        ),
    )
