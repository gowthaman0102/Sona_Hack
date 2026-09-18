from app.benchmarking.dataset import (
    BENCHMARK_CASES,
    get_cases_by_difficulty,
    get_cases_by_task_type,
)


def test_benchmark_dataset_has_expected_size():
    assert len(BENCHMARK_CASES) == 18


def test_benchmark_case_ids_are_unique():
    case_ids = [
        case.case_id
        for case in BENCHMARK_CASES
    ]

    assert len(case_ids) == len(
        set(case_ids)
    )


def test_benchmark_dataset_is_balanced_by_difficulty():
    assert len(
        get_cases_by_difficulty("low")
    ) == 6

    assert len(
        get_cases_by_difficulty("medium")
    ) == 6

    assert len(
        get_cases_by_difficulty("high")
    ) == 6


def test_benchmark_cases_have_valid_evaluators():
    allowed = {
        "exact",
        "contains_all",
        "contains_any",
    }

    assert all(
        case.evaluator in allowed
        for case in BENCHMARK_CASES
    )


def test_benchmark_cases_have_expected_answers():
    assert all(
        case.expected
        for case in BENCHMARK_CASES
    )


def test_benchmark_cases_have_non_empty_prompts():
    assert all(
        case.prompt.strip()
        for case in BENCHMARK_CASES
    )


def test_benchmark_dataset_covers_core_task_types():
    expected_task_types = {
        "extraction",
        "classification",
        "transformation",
        "general",
        "explanation",
        "summarization",
        "coding",
        "analysis",
        "planning",
    }

    actual_task_types = {
        case.task_type
        for case in BENCHMARK_CASES
    }

    assert (
        expected_task_types
        <= actual_task_types
    )


def test_task_type_filter_returns_only_requested_type():
    coding_cases = (
        get_cases_by_task_type(
            "coding"
        )
    )

    assert coding_cases

    assert all(
        case.task_type == "coding"
        for case in coding_cases
    )
