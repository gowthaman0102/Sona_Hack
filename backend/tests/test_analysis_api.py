from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_analysis_api_medium_query():
    response = client.post(
        "/analysis",
        json={
            "prompt": (
                "Explain database normalization "
                "with an example."
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["task_type"] == "explanation"
    assert data["recommended_tier"] == "medium"
    assert data["reasoning_required"] is False

    assert "features" in data
    assert data["features"]["word_count"] > 0


def test_analysis_api_complex_query():
    response = client.post(
        "/analysis",
        json={
            "prompt": (
                "Analyze this Python API, identify "
                "the root cause of high latency, "
                "compare possible solutions, and "
                "recommend the best architecture."
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["task_type"] == "analysis"
    assert data["recommended_tier"] == "high"
    assert data["reasoning_required"] is True
    assert (
        data["features"]["has_multiple_requirements"]
        is True
    )


def test_analysis_api_rejects_empty_prompt():
    response = client.post(
        "/analysis",
        json={
            "prompt": ""
        },
    )

    assert response.status_code == 422
