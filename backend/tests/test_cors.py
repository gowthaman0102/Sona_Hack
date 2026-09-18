from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_vite_localhost_origin_is_allowed():

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "access-control-allow-origin"
        ]
        == "http://localhost:5173"
    )


def test_vite_loopback_origin_is_allowed():

    response = client.options(
        "/models",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "access-control-allow-origin"
        ]
        == "http://127.0.0.1:5173"
    )


def test_unknown_origin_is_not_allowed():

    response = client.options(
        "/health",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert (
        response.headers.get(
            "access-control-allow-origin"
        )
        is None
    )


def test_normal_get_includes_cors_header_for_frontend():

    response = client.get(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "access-control-allow-origin"
        ]
        == "http://localhost:5173"
    )
