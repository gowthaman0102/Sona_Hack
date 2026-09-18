from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def generation(
    response: str,
    prompt_tokens: int = 10,
    output_tokens: int = 5,
    latency: float = 1.0,
):
    return {
        "tier": "test",
        "model_name": "mock",
        "display_name": "mock",
        "compute_score": 1,
        "thinking_enabled": False,
        "response": response,
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "latency_seconds": latency,
        "tokens_per_second": 10.0,
    }


def test_multi_route_api_returns_three_tasks():

    outputs = [
        generation(
            "customer@example.com"
        ),
        generation(
            (
                "The customer reports persistent "
                "checkout slowdown during peak traffic."
            )
        ),
        generation(
            (
                "The likely root cause is synchronous database "
                "access combined with connection contention "
                "during concurrent traffic, which causes "
                "request queues and increased latency."
            )
        ),
    ]

    with patch(
        "app.api.multi_routing.multi_task_router."
        "models.generate_for_tier",
        side_effect=outputs,
    ):

        response = client.post(
            "/multi-route",
            json={
                "prompt": (
                    "Extract the customer email address, "
                    "summarize the complaint, "
                    "and analyze the root cause of the issue."
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["is_multi_task"] is True
    assert data["task_count"] == 3

    assert (
        data["tasks"][0]["recommended_tier"]
        == "low"
    )

    assert (
        data["tasks"][1]["recommended_tier"]
        == "medium"
    )

    assert (
        data["tasks"][2]["recommended_tier"]
        == "high"
    )


def test_multi_route_api_returns_aggregation():

    outputs = [
        generation(
            "customer@example.com"
        ),
        generation(
            (
                "The customer reports persistent "
                "checkout slowdown during peak traffic."
            )
        ),
        generation(
            (
                "The root cause is synchronous database "
                "processing combined with connection contention "
                "during concurrent load, causing queueing and "
                "higher backend latency."
            )
        ),
    ]

    with patch(
        "app.api.multi_routing.multi_task_router."
        "models.generate_for_tier",
        side_effect=outputs,
    ):

        response = client.post(
            "/multi-route",
            json={
                "prompt": (
                    "Extract the customer email address, "
                    "summarize the complaint, "
                    "and analyze the root cause of the issue."
                )
            },
        )

    data = response.json()

    assert (
        "Task 1 - Extraction"
        in data["aggregated_response"]
    )

    assert (
        "Task 2 - Summarization"
        in data["aggregated_response"]
    )

    assert (
        "Task 3 - Analysis"
        in data["aggregated_response"]
    )


def test_multi_route_api_exposes_task_models():

    outputs = [
        generation(
            "customer@example.com"
        ),
        generation(
            (
                "The customer reports persistent "
                "checkout slowdown during peak traffic."
            )
        ),
        generation(
            (
                "The likely cause is synchronous database "
                "access and connection contention under "
                "concurrent load, increasing latency and "
                "causing request queues."
            )
        ),
    ]

    with patch(
        "app.api.multi_routing.multi_task_router."
        "models.generate_for_tier",
        side_effect=outputs,
    ):

        response = client.post(
            "/multi-route",
            json={
                "prompt": (
                    "Extract the customer email address, "
                    "summarize the complaint, "
                    "and analyze the root cause of the issue."
                )
            },
        )

    data = response.json()

    assert (
        data["tasks"][0]["selected_model"]
        == "qwen3:1.7b"
    )

    assert (
        data["tasks"][1]["selected_model"]
        == "qwen3:4b"
    )

    assert (
        data["tasks"][2]["selected_model"]
        == "qwen3:8b"
    )


def test_multi_route_rejects_empty_prompt():

    response = client.post(
        "/multi-route",
        json={
            "prompt": ""
        },
    )

    assert response.status_code == 422


def test_multi_route_api_can_report_selective_escalation():

    outputs = [
        generation(
            "customer@example.com"
        ),

        generation(
            "I don't know."
        ),

        generation(
            (
                "The customer reports persistent checkout "
                "slowdowns during high traffic and repeated "
                "delays while completing transactions."
            )
        ),

        generation(
            (
                "The likely root cause is synchronous database "
                "access combined with connection contention. "
                "Under concurrent traffic, requests queue while "
                "connections remain occupied, increasing "
                "backend latency."
            )
        ),
    ]

    with patch(
        "app.api.multi_routing.multi_task_router."
        "models.generate_for_tier",
        side_effect=outputs,
    ):

        response = client.post(
            "/multi-route",
            json={
                "prompt": (
                    "Extract the customer email address, "
                    "summarize the complaint, "
                    "and analyze the root cause of the issue."
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["tasks"][0]["escalation"]["escalated"]
        is False
    )

    assert (
        data["tasks"][1]["escalation"]["escalated"]
        is True
    )

    assert (
        data["tasks"][1]["recommended_tier"]
        == "medium"
    )

    assert (
        data["tasks"][1]["selected_tier"]
        == "high"
    )

    assert (
        data["tasks"][2]["escalation"]["escalated"]
        is False
    )
