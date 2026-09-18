import pytest

from app.services.learning_context import (
    performance_history_store,
)


@pytest.fixture(autouse=True)
def isolate_production_learning_history(
    tmp_path,
):
    """
    Prevent all tests from writing to AURA's real runtime
    learning-history location.

    The shared production store remains the same object,
    but its path is redirected to a fresh temporary file
    for each test.
    """

    original_path = (
        performance_history_store.path
    )

    test_path = (
        tmp_path
        / "learning_history.json"
    )

    performance_history_store.path = (
        test_path
    )

    try:
        yield

    finally:

        performance_history_store.path = (
            original_path
        )

        if test_path.exists():
            test_path.unlink()
