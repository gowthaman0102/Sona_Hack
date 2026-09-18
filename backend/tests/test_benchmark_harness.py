from fastapi.testclient import TestClient

from app.benchmarking.dataset import (
    BENCHMARK_CASES,
)

from app.benchmarking.harness import (
    build_run_result,
    preserve_learning_history,
)


def get_case(
    case_id: str,
):
    return next(
        case
        for case in BENCHMARK_CASES
        if case.case_id == case_id
    )


def make_body(
    *,
    response: str = "Chennai",
    selected_tier: str = "low",
    selected_model: str = "qwen3:1.7b",
    escalated: bool = False,
    initial_tier: str = "low",
    final_tier: str = "low",
):
    return {
        "response": response,
        "routing": {
            "selected_tier": selected_tier,
            "selected_model": selected_model,
        },
        "escalation": {
            "escalated": escalated,
            "initial_tier": initial_tier,
            "final_tier": final_tier,
        },
        "analytics": {
            "attempt_count": 1,
            "total_prompt_tokens": 10,
            "total_output_tokens": 5,
            "total_tokens": 15,
            "total_latency_seconds": 1.25,
            "normalized_compute_cost": 1.25,
            "final_attempt_compute_cost": 1.25,
            "escalation_overhead_compute": 0.0,
        },
    }


def test_build_result_maps_route_metrics():
    case = get_case(
        "low-general-capital"
    )

    result = build_run_result(
        case=case,
        strategy="adaptive",
        body=make_body(),
    )

    assert result.case_id == case.case_id
    assert result.strategy == "adaptive"
    assert result.passed is True
    assert result.quality_score == 1.0

    assert result.selected_tier == "low"
    assert result.selected_model == "qwen3:1.7b"

    assert result.attempt_count == 1
    assert result.total_tokens == 15
    assert result.total_latency_seconds == 1.25
    assert result.normalized_compute_cost == 1.25


def test_build_result_maps_escalation():
    case = get_case(
        "medium-explanation-http"
    )

    body = make_body(
        response=(
            "A client sends requests "
            "to a server."
        ),
        selected_tier="medium",
        selected_model="qwen3:4b",
        escalated=True,
        initial_tier="low",
        final_tier="medium",
    )

    body["analytics"]["attempt_count"] = 2
    body["analytics"][
        "escalation_overhead_compute"
    ] = 0.8

    result = build_run_result(
        case=case,
        strategy="adaptive",
        body=body,
    )

    assert result.escalated is True
    assert result.initial_tier == "low"
    assert result.final_tier == "medium"
    assert result.attempt_count == 2
    assert result.escalation_overhead_compute == 0.8


def test_build_result_scores_failed_quality():
    case = get_case(
        "low-general-capital"
    )

    result = build_run_result(
        case=case,
        strategy="adaptive",
        body=make_body(
            response="Mumbai",
        ),
    )

    assert result.passed is False
    assert result.quality_score == 0.0


def test_always_high_result_keeps_strategy_label():
    case = get_case(
        "low-general-capital"
    )

    result = build_run_result(
        case=case,
        strategy="always_high",
        body=make_body(
            selected_tier="high",
            selected_model="qwen3:8b",
            initial_tier="high",
            final_tier="high",
        ),
    )

    assert result.strategy == "always_high"
    assert result.selected_tier == "high"
    assert result.selected_model == "qwen3:8b"


def test_harness_imports_testclient_contract():
    assert TestClient is not None


def test_preserve_learning_history_restores_existing_file(
    tmp_path,
):
    path = (
        tmp_path
        / "learning_history.json"
    )

    original = (
        b'{"original": true}\n'
    )

    path.write_bytes(
        original
    )

    with preserve_learning_history(
        path
    ):
        path.write_text(
            '{"changed": true}\n',
            encoding="utf-8",
        )

    assert path.read_bytes() == original


def test_preserve_learning_history_removes_new_file(
    tmp_path,
):
    path = (
        tmp_path
        / "learning_history.json"
    )

    assert not path.exists()

    with preserve_learning_history(
        path
    ):
        path.write_text(
            '{"temporary": true}\n',
            encoding="utf-8",
        )

    assert not path.exists()


def test_preserve_learning_history_restores_after_exception(
    tmp_path,
):
    path = (
        tmp_path
        / "learning_history.json"
    )

    original = (
        b'{"safe": true}\n'
    )

    path.write_bytes(
        original
    )

    try:
        with preserve_learning_history(
            path
        ):
            path.write_text(
                '{"unsafe": true}\n',
                encoding="utf-8",
            )

            raise RuntimeError(
                "test failure"
            )

    except RuntimeError:
        pass

    assert path.read_bytes() == original
