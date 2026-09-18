from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Iterable
import json

from fastapi.testclient import TestClient

from app.benchmarking.dataset import (
    BenchmarkCase,
)

from app.benchmarking.harness import (
    BenchmarkRunResult,
    BenchmarkStrategy,
    run_benchmark_case,
)


def run_benchmark_suite(
    *,
    client: TestClient,
    cases: Iterable[BenchmarkCase],
    strategy: BenchmarkStrategy,
) -> list[BenchmarkRunResult]:
    results: list[BenchmarkRunResult] = []

    for case in cases:
        result = run_benchmark_case(
            client=client,
            case=case,
            strategy=strategy,
        )

        results.append(
            result
        )

    return results


def summarize_results(
    results: list[BenchmarkRunResult],
) -> dict:
    if not results:
        return {
            "case_count": 0,
            "passed_count": 0,
            "pass_rate": 0.0,
            "mean_quality_score": 0.0,
            "total_latency_seconds": 0.0,
            "mean_latency_seconds": 0.0,
            "total_tokens": 0,
            "total_normalized_compute_cost": 0.0,
            "total_escalation_overhead_compute": 0.0,
            "escalated_count": 0,
            "tier_usage": {},
            "model_usage": {},
        }

    return {
        "case_count": len(results),
        "passed_count": sum(
            1
            for result in results
            if result.passed
        ),
        "pass_rate": (
            sum(
                1
                for result in results
                if result.passed
            )
            / len(results)
        ),
        "mean_quality_score": mean(
            result.quality_score
            for result in results
        ),
        "total_latency_seconds": sum(
            result.total_latency_seconds
            for result in results
        ),
        "mean_latency_seconds": mean(
            result.total_latency_seconds
            for result in results
        ),
        "total_tokens": sum(
            result.total_tokens
            for result in results
        ),
        "total_normalized_compute_cost": sum(
            result.normalized_compute_cost
            for result in results
        ),
        "total_escalation_overhead_compute": sum(
            result.escalation_overhead_compute
            for result in results
        ),
        "escalated_count": sum(
            1
            for result in results
            if result.escalated
        ),
        "tier_usage": dict(
            Counter(
                result.final_tier
                for result in results
            )
        ),
        "model_usage": dict(
            Counter(
                result.selected_model
                for result in results
            )
        ),
    }


def write_results_json(
    *,
    path: Path,
    strategy: BenchmarkStrategy,
    results: list[BenchmarkRunResult],
) -> None:
    payload = {
        "strategy": strategy,
        "summary": summarize_results(
            results
        ),
        "results": [
            asdict(
                result
            )
            for result in results
        ],
    }

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
