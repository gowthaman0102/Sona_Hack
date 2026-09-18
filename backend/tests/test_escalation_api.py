from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def generation(
    model_name: str,
    response: str,
):
    return {
        "tier": "test",
        "model_name": model_name,
        "display_name": model_name,
        "compute_score": 1,
        "thinking_enabled": False,
        "response": response,
        "prompt_tokens": 10,
        "output_tokens": 10,
        "latency_seconds": 1.0,
        "tokens_per_second": 10.0,
    }


def test_route_api_returns_escalation_history():

    outputs = [
        generation(
            "qwen3:1.7b",
            "",
        ),
        generation(
            "qwen3:4b",
            "I don't know.",
        ),
        generation(
            "qwen3:8b",
            "25 September 2026",
        ),
    ]

    with patch(
        "app.api.routing.intelligent_router.models.generate_for_tier",
        side_effect=outputs,
    ):

        response = client.post(
            "/route",
            json={
                "prompt": (
                    "Extract the date from "
                    "this sentence."
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["escalation"]["escalated"]
        is True
    )

    assert (
        data["escalation"]["initial_tier"]
        == "low"
    )

    assert (
        data["escalation"]["final_tier"]
        == "high"
    )

    assert (
        len(
            data["escalation"]["attempts"]
        )
        == 3
    )

    assert (
        data["routing"]["selected_model"]
        == "qwen3:8b"
    )

    assert (
        data["confidence"]["score"]
        >= 0.65
    )
