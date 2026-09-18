from pathlib import Path
from threading import RLock
import json
import os

from app.models.learning import (
    LearningOutcome,
    PerformanceStats,
)
from app.services.reliability_scorer import (
    ReliabilityScorer,
)


class PerformanceHistoryStore:
    """
    JSON-backed aggregate performance history for AURA.

    Records are grouped by:

        task_type + tier

    Only aggregate operational metrics are persisted.
    User prompts and model responses are not stored.
    """

    def __init__(
        self,
        path: str | Path | None = None,
    ) -> None:

        if path is None:
            path = (
                Path(__file__)
                .resolve()
                .parents[2]
                / "data"
                / "learning_history.json"
            )

        self.path = Path(path)

        self.scorer = ReliabilityScorer()

        self._lock = RLock()

    def record(
        self,
        outcome: LearningOutcome,
    ) -> PerformanceStats:

        with self._lock:

            data = self._load()

            key = self._key(
                task_type=outcome.task_type,
                tier=outcome.tier,
            )

            record = data.get(
                key,
                self._empty_record(
                    task_type=outcome.task_type,
                    tier=outcome.tier,
                ),
            )

            record["attempts"] += 1

            if outcome.success:
                record["successes"] += 1

            record["total_confidence"] += (
                outcome.confidence_score
            )

            record["total_latency_seconds"] += (
                outcome.latency_seconds
            )

            record[
                "total_normalized_compute_cost"
            ] += (
                outcome.normalized_compute_cost
            )

            record["model_names"] = list(
                dict.fromkeys(
                    record.get(
                        "model_names",
                        [],
                    )
                    + [
                        outcome.model_name
                    ]
                )
            )

            data[key] = record

            self._save(
                data
            )

            return self._to_stats(
                record
            )

    def get_stats(
        self,
        *,
        task_type: str,
        tier: str,
    ) -> PerformanceStats:

        with self._lock:

            data = self._load()

            key = self._key(
                task_type=task_type,
                tier=tier,
            )

            record = data.get(
                key
            )

            if record is None:

                return self.scorer.build_stats(
                    task_type=task_type,
                    tier=tier,
                    attempts=0,
                    successes=0,
                    total_confidence=0.0,
                    total_latency_seconds=0.0,
                    total_normalized_compute_cost=0.0,
                )

            return self._to_stats(
                record
            )

    def get_task_stats(
        self,
        task_type: str,
    ) -> list[PerformanceStats]:

        with self._lock:

            data = self._load()

            stats = []

            for record in data.values():

                if (
                    record["task_type"]
                    != task_type
                ):
                    continue

                stats.append(
                    self._to_stats(
                        record
                    )
                )

            tier_order = {
                "low": 0,
                "medium": 1,
                "high": 2,
            }

            return sorted(
                stats,
                key=lambda item: (
                    tier_order.get(
                        item.tier,
                        99,
                    )
                ),
            )

    def snapshot(
        self,
    ) -> dict[str, PerformanceStats]:

        with self._lock:

            data = self._load()

            return {
                key: self._to_stats(
                    record
                )
                for key, record
                in data.items()
            }

    def _to_stats(
        self,
        record: dict,
    ) -> PerformanceStats:

        return self.scorer.build_stats(
            task_type=(
                record["task_type"]
            ),
            tier=(
                record["tier"]
            ),
            attempts=(
                record["attempts"]
            ),
            successes=(
                record["successes"]
            ),
            total_confidence=(
                record["total_confidence"]
            ),
            total_latency_seconds=(
                record["total_latency_seconds"]
            ),
            total_normalized_compute_cost=(
                record[
                    "total_normalized_compute_cost"
                ]
            ),
        )

    def _load(
        self,
    ) -> dict:

        if not self.path.exists():
            return {}

        text = self.path.read_text(
            encoding="utf-8"
        ).strip()

        if not text:
            return {}

        data = json.loads(
            text
        )

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "Learning history must contain a JSON object."
            )

        return data

    def _save(
        self,
        data: dict,
    ) -> None:

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path = (
            self.path.parent
            / (
                self.path.name
                + ".tmp"
            )
        )

        temp_path.write_text(
            json.dumps(
                data,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        os.replace(
            temp_path,
            self.path,
        )

    @staticmethod
    def _key(
        *,
        task_type: str,
        tier: str,
    ) -> str:

        return (
            f"{task_type.strip().lower()}"
            f"::{tier.strip().lower()}"
        )

    @staticmethod
    def _empty_record(
        *,
        task_type: str,
        tier: str,
    ) -> dict:

        return {
            "task_type": (
                task_type.strip().lower()
            ),
            "tier": (
                tier.strip().lower()
            ),
            "attempts": 0,
            "successes": 0,
            "total_confidence": 0.0,
            "total_latency_seconds": 0.0,
            "total_normalized_compute_cost": 0.0,
            "model_names": [],
        }
