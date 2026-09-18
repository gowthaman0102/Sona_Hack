from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def _load_json(
    path: Path,
) -> dict[str, Any]:
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def _percent(
    value: float,
) -> str:
    return f"{value * 100:.2f}%"


def _signed_percent(
    value: float | None,
) -> str:
    if value is None:
        return "N/A"

    return f"{value:+.2f}%"


def generate_benchmark_report(
    *,
    adaptive_path: Path,
    always_high_path: Path,
    comparison_path: Path,
) -> str:
    adaptive_payload = _load_json(
        adaptive_path
    )

    high_payload = _load_json(
        always_high_path
    )

    comparison = _load_json(
        comparison_path
    )

    adaptive = adaptive_payload[
        "summary"
    ]

    high = high_payload[
        "summary"
    ]

    deltas = comparison[
        "deltas"
    ]

    quality = comparison[
        "quality_comparison"
    ]

    compute = comparison[
        "compute_comparison"
    ]

    fixed_failures = comparison[
        "high_fixed_adaptive_failures"
    ]

    efficient_matches = comparison[
        "adaptive_quality_match_lower_compute"
    ]

    lines = [
        "# AURA Phase 12 Benchmark Report",
        "",
        "## Benchmark Objective",
        "",
        (
            "Evaluate adaptive AURA routing against an "
            "Always-HIGH baseline using the same 18 prompts."
        ),
        "",
        (
            "The Always-HIGH baseline forces every request "
            "to the HIGH tier (`qwen3:8b`)."
        ),
        "",
        (
            "All models run locally through Ollama, so actual "
            "API monetary spend is ?0. The benchmark therefore "
            "uses normalized compute cost rather than currency."
        ),
        "",
        "## Methodology",
        "",
        "- 18 benchmark prompts.",
        "- 6 labelled low difficulty.",
        "- 6 labelled medium difficulty.",
        "- 6 labelled high difficulty.",
        (
            "- Task categories include extraction, classification, "
            "transformation, general, explanation, summarization, "
            "coding, analysis, and planning."
        ),
        (
            "- Both strategies execute the same prompt set through "
            "the existing `/route` pipeline."
        ),
        (
            "- Quality is evaluated deterministically using exact, "
            "contains-all, or contains-any checks."
        ),
        (
            "- Production learning history is preserved around "
            "every benchmark request so benchmark execution cannot "
            "train or contaminate the adaptive router."
        ),
        (
            "- Dataset difficulty labels are benchmark metadata and "
            "are distinct from AURA's runtime analyzer tier."
        ),
        "",
        "## Aggregate Results",
        "",
        (
            "| Metric | Adaptive AURA | Always-HIGH | "
            "Adaptive Delta |"
        ),
        "|---|---:|---:|---:|",
        (
            f"| Pass rate | "
            f"{_percent(float(adaptive['pass_rate']))} | "
            f"{_percent(float(high['pass_rate']))} | "
            f"{float(deltas['pass_rate_percentage_points']):+.2f} pp |"
        ),
        (
            f"| Mean quality | "
            f"{float(adaptive['mean_quality_score']):.4f} | "
            f"{float(high['mean_quality_score']):.4f} | "
            f"{float(deltas['mean_quality_score']):+.4f} |"
        ),
        (
            f"| Total latency | "
            f"{float(adaptive['total_latency_seconds']):.3f} s | "
            f"{float(high['total_latency_seconds']):.3f} s | "
            f"{_signed_percent(deltas['latency_percent'])} |"
        ),
        (
            f"| Mean latency | "
            f"{float(adaptive['mean_latency_seconds']):.3f} s | "
            f"{float(high['mean_latency_seconds']):.3f} s | "
            f"? |"
        ),
        (
            f"| Total tokens | "
            f"{int(adaptive['total_tokens'])} | "
            f"{int(high['total_tokens'])} | "
            f"{_signed_percent(deltas['tokens_percent'])} |"
        ),
        (
            f"| Normalized compute | "
            f"{float(adaptive['total_normalized_compute_cost']):.3f} | "
            f"{float(high['total_normalized_compute_cost']):.3f} | "
            f"{_signed_percent(deltas['normalized_compute_percent'])} |"
        ),
        (
            f"| Escalations | "
            f"{int(adaptive['escalated_count'])} | "
            f"{int(high['escalated_count'])} | "
            f"? |"
        ),
        "",
        "## Routing Distribution",
        "",
        "Adaptive AURA final-tier usage:",
        "",
    ]

    for tier in (
        "low",
        "medium",
        "high",
    ):
        count = adaptive[
            "tier_usage"
        ].get(
            tier,
            0,
        )

        lines.append(
            f"- {tier.upper()}: {count}"
        )

    lines.extend(
        [
            "",
            (
                "Always-HIGH final-tier usage: "
                f"HIGH = {high['tier_usage'].get('high', 0)}."
            ),
            "",
            "## Quality Comparison",
            "",
            (
                f"- Adaptive quality wins: "
                f"{quality['adaptive_wins']}."
            ),
            (
                f"- Adaptive quality losses: "
                f"{quality['adaptive_losses']}."
            ),
            (
                f"- Quality ties: "
                f"{quality['ties']}."
            ),
            "",
            (
                "Always-HIGH corrected these adaptive "
                "quality failures:"
            ),
            "",
        ]
    )

    if fixed_failures:
        for case_id in fixed_failures:
            lines.append(
                f"- `{case_id}`"
            )
    else:
        lines.append(
            "- None."
        )

    lines.extend(
        [
            "",
            "## Compute Comparison",
            "",
            (
                f"- Adaptive used lower normalized compute "
                f"on {compute['adaptive_lower_compute']} cases."
            ),
            (
                f"- Adaptive used higher normalized compute "
                f"on {compute['adaptive_higher_compute']} cases."
            ),
            (
                f"- Compute ties: "
                f"{compute['ties']}."
            ),
            "",
            (
                "Adaptive AURA matched Always-HIGH quality "
                "while using lower normalized compute on:"
            ),
            "",
        ]
    )

    if efficient_matches:
        for case_id in efficient_matches:
            lines.append(
                f"- `{case_id}`"
            )
    else:
        lines.append(
            "- None."
        )

    lines.extend(
        [
            "",
            "## Observations",
            "",
            (
                "1. Always-HIGH achieved the highest deterministic "
                "quality in this benchmark run."
            ),
            (
                "2. Adaptive AURA did not reduce aggregate latency, "
                "token generation, or normalized compute in this run."
            ),
            (
                "3. Smaller models sometimes generated substantially "
                "longer responses, offsetting their lower per-second "
                "compute score."
            ),
            (
                "4. The two adaptive quality failures were both "
                "classification tasks routed to the LOW model."
            ),
            (
                "5. Adaptive routing still demonstrated per-case "
                "efficiency opportunities: several prompts matched "
                "Always-HIGH quality with lower normalized compute."
            ),
            (
                "6. No confidence-based escalation occurred in either "
                "saved benchmark run."
            ),
            "",
            "## Interpretation",
            "",
            (
                "The benchmark does not support a claim that the "
                "current adaptive policy is globally more efficient "
                "than Always-HIGH on this hardware and prompt set."
            ),
            "",
            (
                "Instead, the results identify where the router needs "
                "further optimization: stronger classification routing, "
                "better output-length control, and routing decisions "
                "that account for observed generation efficiency rather "
                "than model size alone."
            ),
            "",
            "## Limitations",
            "",
            (
                "- This is a single saved run of 18 prompts, not a "
                "large statistical performance study."
            ),
            (
                "- Local inference latency varies with model warm state, "
                "system load, and generated response length."
            ),
            (
                "- The deterministic evaluator checks required answer "
                "properties but is not a complete semantic quality judge."
            ),
            (
                "- Normalized compute cost is an internal resource metric, "
                "not monetary API cost."
            ),
            (
                "- Actual monetary API spend remains ?0 because all "
                "benchmark models execute locally."
            ),
            "",
            "## Phase 12 Conclusion",
            "",
            (
                "Phase 12 establishes a reproducible benchmarking "
                "framework for AURA and provides a measured baseline "
                "for future routing improvements."
            ),
            "",
            (
                "The current results favor Always-HIGH at the aggregate "
                "level, while also revealing specific cases where "
                "adaptive routing preserves quality at lower compute."
            ),
            "",
            (
                "These findings should be carried into final integration "
                "and future policy tuning without altering the saved "
                "benchmark evidence."
            ),
            "",
        ]
    )

    return "\n".join(
        lines
    )


def write_benchmark_report(
    *,
    adaptive_path: Path,
    always_high_path: Path,
    comparison_path: Path,
    output_path: Path,
) -> str:
    report = generate_benchmark_report(
        adaptive_path=adaptive_path,
        always_high_path=always_high_path,
        comparison_path=comparison_path,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        report,
        encoding="utf-8",
    )

    return report
