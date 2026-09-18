from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def generation(
    response,
    prompt_tokens,
    output_tokens,
    latency,
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
        "tokens_per_second": (
            round(
                output_tokens / latency,
                2,
            )
            if latency
            else None
        ),
    }


def test_route_api_exposes_analytics():

    with patch(
        "app.api.routing."
        "intelligent_router."
        "models.generate_for_tier",
        return_value=generation(
            "alice@example.com",
            10,
            2,
            1.5,
        ),
    ):

        response = client.post(
            "/route",
            json={
                "prompt": (
                    "Extract the email from "
                    "alice@example.com"
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    analytics = data["analytics"]

    assert analytics["attempt_count"] == 1
    assert analytics["total_prompt_tokens"] == 10
    assert analytics["total_output_tokens"] == 2
    assert analytics["total_tokens"] == 12
    assert analytics["total_latency_seconds"] == 1.5

    assert (
        analytics["escalation_overhead_compute"]
        == 0.0
    )


def test_route_api_exposes_escalation_overhead():

    with patch(
        "app.api.routing."
        "intelligent_router."
        "models.generate_for_tier",
        side_effect=[
            generation(
                "",
                10,
                0,
                1.0,
            ),
            generation(
                "25 September 2026",
                12,
                4,
                2.0,
            ),
        ],
    ):

        response = client.post(
            "/route",
            json={
                "prompt": (
                    "Extract the date: "
                    "25 September 2026."
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    analytics = data["analytics"]

    assert analytics["attempt_count"] == 2
    assert analytics["total_prompt_tokens"] == 22
    assert analytics["total_output_tokens"] == 4
    assert analytics["total_tokens"] == 26
    assert analytics["total_latency_seconds"] == 3.0

    assert (
        analytics["normalized_compute_cost"]
        == 5.0
    )

    assert (
        analytics["final_attempt_compute_cost"]
        == 4.0
    )

    assert (
        analytics["escalation_overhead_compute"]
        == 1.0
    )


def test_multi_route_api_exposes_whole_request_analytics():

    outputs = [
        generation(
            "alice@example.com",
            10,
            2,
            1.0,
        ),
        generation(
            "Checkout is slow.",
            20,
            5,
            2.0,
        ),
        generation(
            (
                "The likely cause is resource "
                "contention during peak traffic."
            ),
            30,
            10,
            3.0,
        ),
    ]

    with patch(
        "app.api.multi_routing."
        "multi_task_router."
        "models.generate_for_tier",
        side_effect=outputs,
    ):

        response = client.post(
            "/multi-route",
            json={
                "prompt": (
                    "Customer alice@example.com reports "
                    "slow checkout during peak traffic. "
                    "Extract the customer email, "
                    "summarize the complaint, "
                    "and analyze the root cause."
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    analytics = data["analytics"]

    assert analytics["task_count"] == 3
    assert analytics["total_attempt_count"] == 3

    assert analytics["total_prompt_tokens"] == 60
    assert analytics["total_output_tokens"] == 17
    assert analytics["total_tokens"] == 77
    assert analytics["total_latency_seconds"] == 6.0

    # LOW    = 1 × 1 = 1
    # MEDIUM = 2 × 2 = 4
    # HIGH   = 4 × 3 = 12

    assert (
        analytics["normalized_compute_cost"]
        == 17.0
    )

    assert (
        analytics["escalation_overhead_compute"]
        == 0.0
    )

    for task in data["tasks"]:
        assert task["analytics"] is not None
        assert (
            task["analytics"]["attempt_count"]
            == 1
        )


def test_api_version_is_current():

    assert app.version == "1.0.0"

    response = client.get(
        "/"
    )

    assert response.status_code == 200

    assert (
        response.json()["version"]
        == "1.0.0"
    )
