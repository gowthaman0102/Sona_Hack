from app.models.decomposition import SubtaskExecutionResult


class ResultAggregator:
    """
    Combines independently routed subtask responses into
    one deterministic user-facing result.

    No extra LLM call is used, avoiding unnecessary compute.
    """

    def aggregate(
        self,
        tasks: list[SubtaskExecutionResult],
    ) -> str:

        if not tasks:
            return ""

        if len(tasks) == 1:
            return tasks[0].response.strip()

        sections: list[str] = []

        for task in tasks:

            title = self._title_for(
                task
            )

            response = (
                task.response.strip()
            )

            section = (
                f"{title}\n"
                f"{response}"
            )

            sections.append(
                section
            )

        return "\n\n".join(
            sections
        )

    def _title_for(
        self,
        task: SubtaskExecutionResult,
    ) -> str:

        readable_type = (
            task.task_type
            .replace("_", " ")
            .title()
        )

        return (
            f"Task {task.index} - "
            f"{readable_type}"
        )
