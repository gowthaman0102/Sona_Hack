from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Literal

from fastapi.testclient import TestClient

from app.benchmarking.dataset import (
    BenchmarkCase,
)

from app.benchmarking.evaluator import (
    BenchmarkEvaluation,
    evaluate_response,
)


BenchmarkStrategy = Literal[
    "adaptive",
    "always_high",
]


LEARNING_HISTORY_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "data"
    / "learning_history.json"
)


@contextmanager
def preserve_learning_history(
    path: Path = LEARNING_HISTORY_PATH,
) -> Iterator[None]:
    existed = path.exists()

    original_bytes = (
        path.read_bytes()
        if existed
        else None
    )

    try:
        yield

    finally:
        if existed:
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            path.write_bytes(
                original_bytes
                if original_bytes is not None
                else b""
            )

        elif path.exists():
            path.unlink()


@dataclass(
    frozen=True,
    slots=True,
)
class BenchmarkRunResult:
    case_id: str
    strategy: BenchmarkStrategy
    task_type: str
    difficulty: str

    passed: bool
    quality_score: float

    selected_tier: str
    selected_model: str

    initial_tier: str
    final_tier: str
    escalated: bool

    attempt_count: int

    prompt_tokens: int
    output_tokens: int
    total_tokens: int

    total_latency_seconds: float
    normalized_compute_cost: float
    final_attempt_compute_cost: float
    escalation_overhead_compute: float

    response: str
    evaluation_reason: str


def run_benchmark_case(
    *,
    client: TestClient,
    case: BenchmarkCase,
    strategy: BenchmarkStrategy,
) -> BenchmarkRunResult:
    payload: dict[str, Any] = {
        "prompt": case.prompt,
    }

    if strategy == "always_high":
        payload["override_tier"] = "high"

    with preserve_learning_history():

        response = client.post(
            "/route",
            json=payload,
        )

        response.raise_for_status()

        body = response.json()

    return build_run_result(
        case=case,
        strategy=strategy,
        body=body,
    )


def build_run_result(
    *,
    case: BenchmarkCase,
    strategy: BenchmarkStrategy,
    body: dict[str, Any],
) -> BenchmarkRunResult:
    model_response = str(
        body["response"]
    )

    evaluation = evaluate_response(
        case,
        model_response,
    )

    routing = body["routing"]
    escalation = body["escalation"]
    analytics = body["analytics"]

    if escalation is None:
        initial_tier = str(
            routing["selected_tier"]
        )

        final_tier = str(
            routing["selected_tier"]
        )

        escalated = False
    else:
        initial_tier = str(
            escalation["initial_tier"]
        )

        final_tier = str(
            escalation["final_tier"]
        )

        escalated = bool(
            escalation["escalated"]
        )

    return BenchmarkRunResult(
        case_id=case.case_id,
        strategy=strategy,
        task_type=case.task_type,
        difficulty=case.difficulty,
        passed=evaluation.passed,
        quality_score=evaluation.score,
        selected_tier=str(
            routing["selected_tier"]
        ),
        selected_model=str(
            routing["selected_model"]
        ),
        initial_tier=initial_tier,
        final_tier=final_tier,
        escalated=escalated,
        attempt_count=int(
            analytics["attempt_count"]
        ),
        prompt_tokens=int(
            analytics["total_prompt_tokens"]
        ),
        output_tokens=int(
            analytics["total_output_tokens"]
        ),
        total_tokens=int(
            analytics["total_tokens"]
        ),
        total_latency_seconds=float(
            analytics["total_latency_seconds"]
        ),
        normalized_compute_cost=float(
            analytics["normalized_compute_cost"]
        ),
        final_attempt_compute_cost=float(
            analytics[
                "final_attempt_compute_cost"
            ]
        ),
        escalation_overhead_compute=float(
            analytics[
                "escalation_overhead_compute"
            ]
        ),
        response=model_response,
        evaluation_reason=evaluation.reason,
    )


def evaluation_from_result(
    result: BenchmarkRunResult,
) -> BenchmarkEvaluation:
    return BenchmarkEvaluation(
        passed=result.passed,
        score=result.quality_score,
        matched_expectations=(),
        missing_expectations=(),
        normalized_response=result.response,
        reason=result.evaluation_reason,
    )
