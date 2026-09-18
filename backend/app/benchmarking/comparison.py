from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def percent_change(
    *,
    value: float,
    baseline: float,
) -> float | None:
    if baseline == 0:
        return None

    return (
        (value - baseline)
        / baseline
        * 100.0
    )


def compare_payloads(
    *,
    adaptive: dict[str, Any],
    always_high: dict[str, Any],
) -> dict[str, Any]:
    adaptive_summary = adaptive["summary"]
    high_summary = always_high["summary"]

    adaptive_results = {
        result["case_id"]: result
        for result in adaptive["results"]
    }

    high_results = {
        result["case_id"]: result
        for result in always_high["results"]
    }

    if (
        set(adaptive_results)
        != set(high_results)
    ):
        raise ValueError(
            "Benchmark result sets do not contain "
            "the same case IDs."
        )

    quality_wins = []
    quality_losses = []
    quality_ties = []

    compute_wins = []
    compute_losses = []
    compute_ties = []

    high_fixed_adaptive_failures = []

    adaptive_quality_match_lower_compute = []

    per_case = []

    for case_id in sorted(
        adaptive_results
    ):
        adaptive_result = (
            adaptive_results[case_id]
        )

        high_result = (
            high_results[case_id]
        )

        adaptive_quality = float(
            adaptive_result[
                "quality_score"
            ]
        )

        high_quality = float(
            high_result[
                "quality_score"
            ]
        )

        adaptive_compute = float(
            adaptive_result[
                "normalized_compute_cost"
            ]
        )

        high_compute = float(
            high_result[
                "normalized_compute_cost"
            ]
        )

        if adaptive_quality > high_quality:
            quality_wins.append(
                case_id
            )

        elif adaptive_quality < high_quality:
            quality_losses.append(
                case_id
            )

        else:
            quality_ties.append(
                case_id
            )

        if adaptive_compute < high_compute:
            compute_wins.append(
                case_id
            )

        elif adaptive_compute > high_compute:
            compute_losses.append(
                case_id
            )

        else:
            compute_ties.append(
                case_id
            )

        if (
            not adaptive_result["passed"]
            and high_result["passed"]
        ):
            high_fixed_adaptive_failures.append(
                case_id
            )

        if (
            adaptive_quality == high_quality
            and adaptive_compute < high_compute
        ):
            adaptive_quality_match_lower_compute.append(
                case_id
            )

        per_case.append(
            {
                "case_id": case_id,
                "adaptive_quality": (
                    adaptive_quality
                ),
                "always_high_quality": (
                    high_quality
                ),
                "quality_delta": (
                    adaptive_quality
                    - high_quality
                ),
                "adaptive_compute": (
                    adaptive_compute
                ),
                "always_high_compute": (
                    high_compute
                ),
                "compute_delta": (
                    adaptive_compute
                    - high_compute
                ),
                "compute_delta_percent": (
                    percent_change(
                        value=adaptive_compute,
                        baseline=high_compute,
                    )
                ),
                "adaptive_latency_seconds": (
                    float(
                        adaptive_result[
                            "total_latency_seconds"
                        ]
                    )
                ),
                "always_high_latency_seconds": (
                    float(
                        high_result[
                            "total_latency_seconds"
                        ]
                    )
                ),
                "adaptive_tokens": int(
                    adaptive_result[
                        "total_tokens"
                    ]
                ),
                "always_high_tokens": int(
                    high_result[
                        "total_tokens"
                    ]
                ),
                "adaptive_final_tier": (
                    adaptive_result[
                        "final_tier"
                    ]
                ),
                "always_high_final_tier": (
                    high_result[
                        "final_tier"
                    ]
                ),
            }
        )

    return {
        "case_count": (
            adaptive_summary[
                "case_count"
            ]
        ),
        "adaptive": adaptive_summary,
        "always_high": high_summary,
        "deltas": {
            "pass_rate_percentage_points": (
                float(
                    adaptive_summary[
                        "pass_rate"
                    ]
                )
                - float(
                    high_summary[
                        "pass_rate"
                    ]
                )
            )
            * 100.0,
            "mean_quality_score": (
                float(
                    adaptive_summary[
                        "mean_quality_score"
                    ]
                )
                - float(
                    high_summary[
                        "mean_quality_score"
                    ]
                )
            ),
            "latency_percent": (
                percent_change(
                    value=float(
                        adaptive_summary[
                            "total_latency_seconds"
                        ]
                    ),
                    baseline=float(
                        high_summary[
                            "total_latency_seconds"
                        ]
                    ),
                )
            ),
            "tokens_percent": (
                percent_change(
                    value=float(
                        adaptive_summary[
                            "total_tokens"
                        ]
                    ),
                    baseline=float(
                        high_summary[
                            "total_tokens"
                        ]
                    ),
                )
            ),
            "normalized_compute_percent": (
                percent_change(
                    value=float(
                        adaptive_summary[
                            "total_normalized_compute_cost"
                        ]
                    ),
                    baseline=float(
                        high_summary[
                            "total_normalized_compute_cost"
                        ]
                    ),
                )
            ),
        },
        "quality_comparison": {
            "adaptive_wins": len(
                quality_wins
            ),
            "adaptive_losses": len(
                quality_losses
            ),
            "ties": len(
                quality_ties
            ),
            "win_cases": quality_wins,
            "loss_cases": quality_losses,
            "tie_cases": quality_ties,
        },
        "compute_comparison": {
            "adaptive_lower_compute": len(
                compute_wins
            ),
            "adaptive_higher_compute": len(
                compute_losses
            ),
            "ties": len(
                compute_ties
            ),
            "lower_compute_cases": compute_wins,
            "higher_compute_cases": compute_losses,
            "tie_cases": compute_ties,
        },
        "high_fixed_adaptive_failures": (
            high_fixed_adaptive_failures
        ),
        "adaptive_quality_match_lower_compute": (
            adaptive_quality_match_lower_compute
        ),
        "per_case": per_case,
    }


def load_json(
    path: Path,
) -> dict[str, Any]:
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def write_comparison_json(
    *,
    adaptive_path: Path,
    always_high_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    adaptive = load_json(
        adaptive_path
    )

    always_high = load_json(
        always_high_path
    )

    comparison = compare_payloads(
        adaptive=adaptive,
        always_high=always_high,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            comparison,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return comparison
