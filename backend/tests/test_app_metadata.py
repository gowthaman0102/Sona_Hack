from app.main import app


def test_final_application_title():
    assert app.title == "AURA API"


def test_final_application_version():
    assert app.version == "1.0.0"


def test_final_application_description():
    assert app.description == (
        "Adaptive Unified Routing Architecture "
        "for Cost-Efficient and Reliable Multi-LLM Systems"
    )
