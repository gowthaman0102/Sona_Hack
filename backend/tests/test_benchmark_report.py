import json

from app.benchmarking.report import (
    generate_benchmark_report,
)


def write_fixture(
    path,
    payload,
):
    path.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )


def test_generate_benchmark_report(
    tmp_path,
):
    adaptive_path = (
        tmp_path
        / "adaptive.json"
    )

    high_path = (
        tmp_path
        / "always_high.json"
    )

    comparison_path = (
        tmp_path
        / "comparison.json"
    )

    adaptive = {
        "summary": {
            "pass_rate": 0.5,
            "mean_quality_score": 0.75,
            "total_latency_seconds": 10.0,
            "mean_latency_seconds": 5.0,
            "total_tokens": 100,
            "total_normalized_compute_cost": 20.0,
            "escalated_count": 0,
            "tier_usage": {
                "low": 1,
                "medium": 1,
            },
        },
    }

    high = {
        "summary": {
            "pass_rate": 1.0,
            "mean_quality_score": 1.0,
            "total_latency_seconds": 8.0,
            "mean_latency_seconds": 4.0,
            "total_tokens": 80,
            "total_normalized_compute_cost": 24.0,
            "escalated_count": 0,
            "tier_usage": {
                "high": 2,
            },
        },
    }

    comparison = {
        "deltas": {
            "pass_rate_percentage_points": -50.0,
            "mean_quality_score": -0.25,
            "latency_percent": 25.0,
            "tokens_percent": 25.0,
            "normalized_compute_percent": -16.67,
        },
        "quality_comparison": {
            "adaptive_wins": 0,
            "adaptive_losses": 1,
            "ties": 1,
        },
        "compute_comparison": {
            "adaptive_lower_compute": 1,
            "adaptive_higher_compute": 1,
            "ties": 0,
        },
        "high_fixed_adaptive_failures": [
            "case-b",
        ],
        "adaptive_quality_match_lower_compute": [
            "case-a",
        ],
    }

    write_fixture(
        adaptive_path,
        adaptive,
    )

    write_fixture(
        high_path,
        high,
    )

    write_fixture(
        comparison_path,
        comparison,
    )

    report = generate_benchmark_report(
        adaptive_path=adaptive_path,
        always_high_path=high_path,
        comparison_path=comparison_path,
    )

    assert (
        "# AURA Phase 12 Benchmark Report"
        in report
    )

    assert (
        "50.00%"
        in report
    )

    assert (
        "100.00%"
        in report
    )

    assert (
        "`case-b`"
        in report
    )

    assert (
        "`case-a`"
        in report
    )

    assert (
        "actual API monetary spend is ?0"
        in report
    )

    assert (
        "single saved run"
        in report
    )
