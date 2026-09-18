import json

from app.benchmarking.harness import (
    BenchmarkRunResult,
)

from app.benchmarking.runner import (
    summarize_results,
    write_results_json,
)


def make_result(
    *,
    case_id: str,
    passed: bool,
    quality_score: float,
    final_tier: str,
    selected_model: str,
    latency: float,
    total_tokens: int,
    compute: float,
    escalated: bool = False,
    escalation_overhead: float = 0.0,
) -> BenchmarkRunResult:
    return BenchmarkRunResult(
        case_id=case_id,
        strategy="adaptive",
        task_type="general",
        difficulty="low",
        passed=passed,
        quality_score=quality_score,
        selected_tier=final_tier,
        selected_model=selected_model,
        initial_tier=final_tier,
        final_tier=final_tier,
        escalated=escalated,
        attempt_count=2 if escalated else 1,
        prompt_tokens=10,
        output_tokens=5,
        total_tokens=total_tokens,
        total_latency_seconds=latency,
        normalized_compute_cost=compute,
        final_attempt_compute_cost=compute,
        escalation_overhead_compute=escalation_overhead,
        response="test",
        evaluation_reason="test",
    )


def test_summarize_results_aggregates_metrics():
    results = [
        make_result(
            case_id="a",
            passed=True,
            quality_score=1.0,
            final_tier="low",
            selected_model="qwen3:1.7b",
            latency=1.0,
            total_tokens=20,
            compute=1.0,
        ),
        make_result(
            case_id="b",
            passed=False,
            quality_score=0.5,
            final_tier="medium",
            selected_model="qwen3:4b",
            latency=3.0,
            total_tokens=40,
            compute=6.0,
            escalated=True,
            escalation_overhead=1.0,
        ),
    ]

    summary = summarize_results(
        results
    )

    assert summary["case_count"] == 2
    assert summary["passed_count"] == 1
    assert summary["pass_rate"] == 0.5
    assert summary["mean_quality_score"] == 0.75
    assert summary["total_latency_seconds"] == 4.0
    assert summary["mean_latency_seconds"] == 2.0
    assert summary["total_tokens"] == 60
    assert summary["total_normalized_compute_cost"] == 7.0
    assert summary["total_escalation_overhead_compute"] == 1.0
    assert summary["escalated_count"] == 1

    assert summary["tier_usage"] == {
        "low": 1,
        "medium": 1,
    }


def test_summarize_results_handles_empty_input():
    summary = summarize_results(
        []
    )

    assert summary["case_count"] == 0
    assert summary["pass_rate"] == 0.0
    assert summary["mean_quality_score"] == 0.0


def test_write_results_json(tmp_path):
    path = (
        tmp_path
        / "results.json"
    )

    results = [
        make_result(
            case_id="a",
            passed=True,
            quality_score=1.0,
            final_tier="low",
            selected_model="qwen3:1.7b",
            latency=1.0,
            total_tokens=20,
            compute=1.0,
        ),
    ]

    write_results_json(
        path=path,
        strategy="adaptive",
        results=results,
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert payload["strategy"] == "adaptive"
    assert payload["summary"]["case_count"] == 1
    assert payload["results"][0]["case_id"] == "a"
