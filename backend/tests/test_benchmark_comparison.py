import pytest

from app.benchmarking.comparison import (
    compare_payloads,
    percent_change,
)


def make_payload(
    *,
    strategy: str,
    pass_rate: float,
    mean_quality: float,
    latency: float,
    tokens: int,
    compute: float,
    results: list[dict],
):
    return {
        "strategy": strategy,
        "summary": {
            "case_count": len(results),
            "passed_count": sum(
                1
                for result in results
                if result["passed"]
            ),
            "pass_rate": pass_rate,
            "mean_quality_score": mean_quality,
            "total_latency_seconds": latency,
            "mean_latency_seconds": (
                latency / len(results)
            ),
            "total_tokens": tokens,
            "total_normalized_compute_cost": compute,
            "total_escalation_overhead_compute": 0.0,
            "escalated_count": 0,
            "tier_usage": {},
            "model_usage": {},
        },
        "results": results,
    }


def make_result(
    *,
    case_id: str,
    passed: bool,
    quality: float,
    compute: float,
    latency: float = 1.0,
    tokens: int = 10,
    tier: str = "low",
):
    return {
        "case_id": case_id,
        "passed": passed,
        "quality_score": quality,
        "normalized_compute_cost": compute,
        "total_latency_seconds": latency,
        "total_tokens": tokens,
        "final_tier": tier,
    }


def test_percent_change():
    assert percent_change(
        value=150.0,
        baseline=100.0,
    ) == 50.0


def test_percent_change_handles_zero_baseline():
    assert (
        percent_change(
            value=10.0,
            baseline=0.0,
        )
        is None
    )


def test_compare_payloads_identifies_quality_and_compute():
    adaptive = make_payload(
        strategy="adaptive",
        pass_rate=0.5,
        mean_quality=0.75,
        latency=4.0,
        tokens=60,
        compute=7.0,
        results=[
            make_result(
                case_id="a",
                passed=True,
                quality=1.0,
                compute=1.0,
            ),
            make_result(
                case_id="b",
                passed=False,
                quality=0.5,
                compute=6.0,
            ),
        ],
    )

    high = make_payload(
        strategy="always_high",
        pass_rate=1.0,
        mean_quality=1.0,
        latency=5.0,
        tokens=80,
        compute=9.0,
        results=[
            make_result(
                case_id="a",
                passed=True,
                quality=1.0,
                compute=4.0,
                tier="high",
            ),
            make_result(
                case_id="b",
                passed=True,
                quality=1.0,
                compute=5.0,
                tier="high",
            ),
        ],
    )

    result = compare_payloads(
        adaptive=adaptive,
        always_high=high,
    )

    assert (
        result[
            "quality_comparison"
        ]["adaptive_losses"]
        == 1
    )

    assert (
        result[
            "quality_comparison"
        ]["ties"]
        == 1
    )

    assert (
        result[
            "compute_comparison"
        ]["adaptive_lower_compute"]
        == 1
    )

    assert (
        result[
            "compute_comparison"
        ]["adaptive_higher_compute"]
        == 1
    )

    assert result[
        "high_fixed_adaptive_failures"
    ] == ["b"]

    assert result[
        "adaptive_quality_match_lower_compute"
    ] == ["a"]


def test_compare_payloads_rejects_mismatched_cases():
    adaptive = make_payload(
        strategy="adaptive",
        pass_rate=1.0,
        mean_quality=1.0,
        latency=1.0,
        tokens=10,
        compute=1.0,
        results=[
            make_result(
                case_id="a",
                passed=True,
                quality=1.0,
                compute=1.0,
            ),
        ],
    )

    high = make_payload(
        strategy="always_high",
        pass_rate=1.0,
        mean_quality=1.0,
        latency=1.0,
        tokens=10,
        compute=1.0,
        results=[
            make_result(
                case_id="b",
                passed=True,
                quality=1.0,
                compute=1.0,
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="same case IDs",
    ):
        compare_payloads(
            adaptive=adaptive,
            always_high=high,
        )
