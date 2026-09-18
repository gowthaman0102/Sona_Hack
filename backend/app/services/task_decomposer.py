import re

from app.models.decomposition import (
    DecomposedTask,
    DecompositionResult,
)
from app.services.query_analyzer import QueryAnalyzer


class TaskDecomposer:
    """
    Deterministic multi-task decomposition baseline for AURA.

    It separates clearly independent action clauses while
    preserving ordinary phrases that merely contain 'and'.
    """

    def __init__(self) -> None:
        self.analyzer = QueryAnalyzer()

        actions = sorted(
            self.analyzer.ACTION_MARKERS,
            key=len,
            reverse=True,
        )

        escaped_actions = [
            re.escape(action)
            for action in actions
        ]

        self.action_pattern = (
            "(?:"
            + "|".join(escaped_actions)
            + ")"
        )

    def decompose(
        self,
        prompt: str,
    ) -> DecompositionResult:

        original = prompt.strip()

        if not original:
            return DecompositionResult(
                original_prompt=prompt,
                is_multi_task=False,
                task_count=0,
                reason="empty_prompt",
                tasks=[],
            )

        candidates = self._split_prompt(
            original
        )

        cleaned = []

        for candidate in candidates:
            task = self._clean_task(
                candidate
            )

            if task:
                cleaned.append(
                    task
                )

        cleaned = self._remove_duplicates(
            cleaned
        )

        if len(cleaned) > 1:
            cleaned[0] = (
                self._trim_leading_context_from_first_task(
                    cleaned[0]
                )
            )

        if len(cleaned) <= 1:
            analysis = self.analyzer.analyze(
                original
            )

            return DecompositionResult(
                original_prompt=original,
                is_multi_task=False,
                task_count=1,
                reason=(
                    "No clearly independent multiple "
                    "action clauses were detected."
                ),
                tasks=[
                    DecomposedTask(
                        index=1,
                        text=original,
                        analysis=analysis,
                    )
                ],
            )

        tasks = []

        for index, text in enumerate(
            cleaned,
            start=1,
        ):
            tasks.append(
                DecomposedTask(
                    index=index,
                    text=text,
                    analysis=(
                        self.analyzer.analyze(
                            text
                        )
                    ),
                )
            )

        return DecompositionResult(
            original_prompt=original,
            is_multi_task=True,
            task_count=len(tasks),
            reason=(
                "Multiple independent action clauses "
                "were detected and separated."
            ),
            tasks=tasks,
        )

    def extract_shared_context(
        self,
        prompt: str,
        tasks: list[DecomposedTask],
    ) -> str:
        """
        Returns background/context from the original request
        while removing the decomposed action instructions.

        This prevents one subtask model from following the
        instructions intended for other subtasks.
        """

        text = prompt.strip()

        if not text:
            return ""

        earliest = None

        for task in tasks:

            position = text.lower().find(
                task.text.lower()
            )

            if (
                position >= 0
                and (
                    earliest is None
                    or position < earliest
                )
            ):
                earliest = position

        if earliest is None:
            return text

        context = text[:earliest].strip(
            " \t\r\n,;."
        )

        return context

    def _trim_leading_context_from_first_task(
        self,
        text: str,
    ) -> str:
        """
        When a multi-task prompt begins with background data,
        the first split candidate may contain both that context
        and the first instruction.

        Example:
        "Customer email is a@b.com. Extract the email"

        becomes:
        "Extract the email"
        """

        match = re.search(
            rf"\b{self.action_pattern}\b",
            text,
            flags=re.IGNORECASE,
        )

        if match is None:
            return text.strip()

        return text[
            match.start():
        ].strip()

    def _split_prompt(
        self,
        text: str,
    ) -> list[str]:

        parts = [
            text
        ]

        separators = [
            r"\n+",
            r";+",
            r"(?m)^\s*\d+[\.\)]\s*",
            r"(?m)^\s*[-*]\s+",
            rf"(?<=[.!?])\s+(?=(?:please\s+)?{self.action_pattern}\b)",
        ]

        for separator in separators:
            next_parts = []

            for part in parts:
                split_parts = re.split(
                    separator,
                    part,
                )

                next_parts.extend(
                    split_parts
                )

            parts = next_parts

        final_parts = []

        for part in parts:
            final_parts.extend(
                self._split_action_clauses(
                    part
                )
            )

        return final_parts

    def _split_action_clauses(
        self,
        text: str,
    ) -> list[str]:

        comma_pattern = (
            rf",\s*(?="
            rf"(?:please\s+)?"
            rf"{self.action_pattern}\b)"
        )

        parts = re.split(
            comma_pattern,
            text,
            flags=re.IGNORECASE,
        )

        final_parts = []

        conjunction_pattern = (
            rf"\s+(?:and|then|also)\s+"
            rf"(?="
            rf"(?:please\s+)?"
            rf"{self.action_pattern}\b)"
        )

        for part in parts:
            final_parts.extend(
                re.split(
                    conjunction_pattern,
                    part,
                    flags=re.IGNORECASE,
                )
            )

        return final_parts

    def _clean_task(
        self,
        text: str,
    ) -> str:

        cleaned = text.strip(
            " \t\r\n,;."
        )

        cleaned = re.sub(
            r"^(and|then|also)\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        return cleaned.strip()

    def _remove_duplicates(
        self,
        tasks: list[str],
    ) -> list[str]:

        seen = set()
        unique = []

        for task in tasks:
            key = task.lower().strip()

            if key in seen:
                continue

            seen.add(
                key
            )

            unique.append(
                task
            )

        return unique
