from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def generation(
    response: str,
):
    return {
        "tier": "test",
        "model_name": "mock",
        "display_name": "mock",
        "compute_score": 1,
        "thinking_enabled": False,
        "response": response,
        "prompt_tokens": 10,
        "output_tokens": 5,
        "latency_seconds": 1.0,
        "tokens_per_second": 5.0,
    }


def test_route_api_exposes_privacy_assessment():

    with patch(
        "app.api.routing.intelligent_router."
        "models.generate_for_tier",
        return_value=generation(
            "alice@example.com"
        ),
    ):

        response = client.post(
            "/route",
            json={
                "prompt": (
                    "Extract the email address "
                    "alice@example.com"
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["privacy"][
            "contains_sensitive_data"
        ]
        is True
    )

    assert (
        "email"
        in data["privacy"]["categories"]
    )

    assert (
        data["privacy"]["requires_local"]
        is True
    )


def test_route_api_exposes_local_only_policy():

    with patch(
        "app.api.routing.intelligent_router."
        "models.generate_for_tier",
        return_value=generation(
            "alice@example.com"
        ),
    ):

        response = client.post(
            "/route",
            json={
                "prompt": (
                    "Extract the email address "
                    "alice@example.com"
                )
            },
        )

    data = response.json()

    assert (
        data["privacy_policy"][
            "privacy_enforced"
        ]
        is True
    )

    assert (
        data["privacy_policy"][
            "execution_scope"
        ]
        == "local_only"
    )

    assert (
        data["privacy_policy"][
            "external_routing_allowed"
        ]
        is False
    )

    assert (
        data["privacy_policy"][
            "selected_model_is_local"
        ]
        is True
    )


def test_safe_route_api_reports_standard_scope():

    with patch(
        "app.api.routing.intelligent_router."
        "models.generate_for_tier",
        return_value=generation(
            (
                "Normalization reduces "
                "data duplication."
            )
        ),
    ):

        response = client.post(
            "/route",
            json={
                "prompt": (
                    "Explain database normalization."
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["privacy"]["risk_level"]
        == "none"
    )

    assert (
        data["privacy_policy"][
            "privacy_enforced"
        ]
        is False
    )

    assert (
        data["privacy_policy"][
            "execution_scope"
        ]
        == "standard"
    )


def test_multi_route_api_exposes_overall_privacy():

    outputs = [
        generation(
            "alice@example.com"
        ),
        generation(
            (
                "The customer reports "
                "slow checkout."
            )
        ),
        generation(
            (
                "The likely cause is resource "
                "contention during concurrent load."
            )
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

    assert (
        data["privacy"]["requires_local"]
        is True
    )

    assert (
        "email"
        in data["privacy"]["categories"]
    )


def test_multi_route_api_propagates_privacy_to_every_task():

    outputs = [
        generation(
            "alice@example.com"
        ),
        generation(
            (
                "The customer reports "
                "slow checkout."
            )
        ),
        generation(
            (
                "The likely cause is resource "
                "contention during concurrent load."
            )
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

    data = response.json()

    assert len(data["tasks"]) == 3

    for task in data["tasks"]:

        assert (
            task["privacy"]["requires_local"]
            is True
        )

        assert (
            task["privacy_policy"][
                "privacy_enforced"
            ]
            is True
        )

        assert (
            task["privacy_policy"][
                "execution_scope"
            ]
            == "local_only"
        )

        assert (
            task["privacy_policy"][
                "external_routing_allowed"
            ]
            is False
        )

        assert (
            task["privacy_policy"][
                "selected_model_is_local"
            ]
            is True
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
