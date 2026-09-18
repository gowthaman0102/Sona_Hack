from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Difficulty = Literal[
    "low",
    "medium",
    "high",
]

EvaluatorType = Literal[
    "exact",
    "contains_all",
    "contains_any",
]


@dataclass(
    frozen=True,
    slots=True,
)
class BenchmarkCase:
    case_id: str
    task_type: str
    difficulty: Difficulty
    prompt: str
    evaluator: EvaluatorType
    expected: tuple[str, ...]
    description: str


BENCHMARK_CASES: tuple[
    BenchmarkCase,
    ...,
] = (
    BenchmarkCase(
        case_id="low-extraction-email",
        task_type="extraction",
        difficulty="low",
        prompt=(
            "Extract only the email address from this text: "
            "Contact Priya at priya@example.com for details."
        ),
        evaluator="contains_all",
        expected=(
            "priya@example.com",
        ),
        description=(
            "Simple structured extraction."
        ),
    ),
    BenchmarkCase(
        case_id="low-extraction-phone",
        task_type="extraction",
        difficulty="low",
        prompt=(
            "Extract only the phone number from this text: "
            "Call Arun on 9876543210 tomorrow."
        ),
        evaluator="contains_all",
        expected=(
            "9876543210",
        ),
        description=(
            "Simple numeric extraction."
        ),
    ),
    BenchmarkCase(
        case_id="low-classification-positive",
        task_type="classification",
        difficulty="low",
        prompt=(
            "Classify this review as positive, negative, "
            "or neutral. Reply with only the label: "
            "\"The product works perfectly and I love it.\""
        ),
        evaluator="exact",
        expected=(
            "positive",
        ),
        description=(
            "Simple sentiment classification."
        ),
    ),
    BenchmarkCase(
        case_id="low-classification-negative",
        task_type="classification",
        difficulty="low",
        prompt=(
            "Classify this review as positive, negative, "
            "or neutral. Reply with only the label: "
            "\"The app crashes every time I open it.\""
        ),
        evaluator="exact",
        expected=(
            "negative",
        ),
        description=(
            "Simple negative sentiment classification."
        ),
    ),
    BenchmarkCase(
        case_id="low-transformation-uppercase",
        task_type="transformation",
        difficulty="low",
        prompt=(
            "Convert this text to uppercase and return only "
            "the converted text: adaptive routing"
        ),
        evaluator="exact",
        expected=(
            "ADAPTIVE ROUTING",
        ),
        description=(
            "Deterministic text transformation."
        ),
    ),
    BenchmarkCase(
        case_id="low-general-capital",
        task_type="general",
        difficulty="low",
        prompt=(
            "What is the capital of Tamil Nadu? "
            "Reply with only the city name."
        ),
        evaluator="exact",
        expected=(
            "chennai",
        ),
        description=(
            "Short factual response."
        ),
    ),
    BenchmarkCase(
        case_id="medium-explanation-http",
        task_type="explanation",
        difficulty="medium",
        prompt=(
            "Explain in two short sentences what HTTP is "
            "and mention both client and server."
        ),
        evaluator="contains_all",
        expected=(
            "client",
            "server",
        ),
        description=(
            "Concise technical explanation."
        ),
    ),
    BenchmarkCase(
        case_id="medium-explanation-database-index",
        task_type="explanation",
        difficulty="medium",
        prompt=(
            "Explain why a database index can improve query "
            "performance. Mention lookup and storage overhead."
        ),
        evaluator="contains_all",
        expected=(
            "lookup",
            "storage",
        ),
        description=(
            "Trade-off explanation."
        ),
    ),
    BenchmarkCase(
        case_id="medium-summarization-routing",
        task_type="summarization",
        difficulty="medium",
        prompt=(
            "Summarize this in one sentence: "
            "AURA analyzes each prompt, estimates its complexity, "
            "selects an appropriate local language model, checks "
            "the response confidence, and can escalate to a more "
            "capable model when needed."
        ),
        evaluator="contains_any",
        expected=(
            "route",
            "routing",
            "model",
            "complexity",
        ),
        description=(
            "Short controlled summarization."
        ),
    ),
    BenchmarkCase(
        case_id="medium-coding-python-even",
        task_type="coding",
        difficulty="medium",
        prompt=(
            "Write a Python function named is_even that accepts "
            "an integer n and returns True when n is even and "
            "False otherwise. Return only the code."
        ),
        evaluator="contains_all",
        expected=(
            "def is_even",
            "% 2",
        ),
        description=(
            "Small deterministic coding task."
        ),
    ),
    BenchmarkCase(
        case_id="medium-coding-sql-filter",
        task_type="coding",
        difficulty="medium",
        prompt=(
            "Write a SQL query that selects all columns from "
            "employees where salary is greater than 50000. "
            "Return only the SQL query."
        ),
        evaluator="contains_all",
        expected=(
            "select",
            "employees",
            "salary",
            "50000",
        ),
        description=(
            "Small deterministic SQL generation task."
        ),
    ),
    BenchmarkCase(
        case_id="medium-general-arithmetic",
        task_type="general",
        difficulty="medium",
        prompt=(
            "A server handles 120 requests per minute. "
            "How many requests does it handle in 15 minutes? "
            "Reply with only the number."
        ),
        evaluator="exact",
        expected=(
            "1800",
        ),
        description=(
            "Single-step arithmetic."
        ),
    ),
    BenchmarkCase(
        case_id="high-analysis-cache",
        task_type="analysis",
        difficulty="high",
        prompt=(
            "Analyze this system design problem: an API receives "
            "frequent repeated read requests, the database is "
            "becoming the bottleneck, and data changes only every "
            "few minutes. Recommend an approach and explicitly "
            "mention caching, invalidation, and database load."
        ),
        evaluator="contains_all",
        expected=(
            "cach",
            "invalidat",
            "database",
        ),
        description=(
            "Multi-factor architecture analysis."
        ),
    ),
    BenchmarkCase(
        case_id="high-analysis-replication",
        task_type="analysis",
        difficulty="high",
        prompt=(
            "Analyze a database architecture where reads greatly "
            "outnumber writes and users are distributed globally. "
            "Discuss read replicas, replication lag, and consistency."
        ),
        evaluator="contains_all",
        expected=(
            "replica",
            "lag",
            "consisten",
        ),
        description=(
            "Distributed database trade-off analysis."
        ),
    ),
    BenchmarkCase(
        case_id="high-planning-migration",
        task_type="planning",
        difficulty="high",
        prompt=(
            "Create a concise migration plan for moving a small "
            "web application from a single server to containers. "
            "Include testing, rollback, monitoring, and deployment "
            "order."
        ),
        evaluator="contains_all",
        expected=(
            "test",
            "rollback",
            "monitor",
            "deploy",
        ),
        description=(
            "Multi-requirement implementation planning."
        ),
    ),
    BenchmarkCase(
        case_id="high-planning-backup",
        task_type="planning",
        difficulty="high",
        prompt=(
            "Plan a database backup strategy for a production "
            "application. Include full backups, incremental or "
            "continuous backups, restore testing, and retention."
        ),
        evaluator="contains_all",
        expected=(
            "full",
            "restore",
            "retention",
        ),
        description=(
            "Operational resilience planning."
        ),
    ),
    BenchmarkCase(
        case_id="high-coding-deduplicate",
        task_type="coding",
        difficulty="high",
        prompt=(
            "Write a Python function named deduplicate_preserve_order "
            "that removes duplicate integers from a list while "
            "preserving the first occurrence order. Explain the "
            "time complexity in one short comment."
        ),
        evaluator="contains_all",
        expected=(
            "deduplicate_preserve_order",
            "set",
        ),
        description=(
            "Implementation plus complexity requirement."
        ),
    ),
    BenchmarkCase(
        case_id="high-analysis-routing",
        task_type="analysis",
        difficulty="high",
        prompt=(
            "Compare always using a large language model with "
            "adaptive model routing. Analyze latency, compute use, "
            "quality, and escalation trade-offs, and explain when "
            "adaptive routing is useful."
        ),
        evaluator="contains_all",
        expected=(
            "latency",
            "compute",
            "quality",
            "escalat",
        ),
        description=(
            "Benchmark-domain reasoning task."
        ),
    ),
)


def get_benchmark_cases() -> tuple[
    BenchmarkCase,
    ...,
]:
    return BENCHMARK_CASES


def get_cases_by_difficulty(
    difficulty: Difficulty,
) -> tuple[
    BenchmarkCase,
    ...,
]:
    return tuple(
        case
        for case in BENCHMARK_CASES
        if case.difficulty == difficulty
    )


def get_cases_by_task_type(
    task_type: str,
) -> tuple[
    BenchmarkCase,
    ...,
]:
    return tuple(
        case
        for case in BENCHMARK_CASES
        if case.task_type == task_type
    )
