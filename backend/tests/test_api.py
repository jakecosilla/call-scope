from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "callscope-api"


def test_auth_login_success():
    response = client.post(
        "/api/auth/login",
        json={"username": "evaluator@callscope.ai", "password": "CallScope2026!EvalSecret"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["username"] == "evaluator@callscope.ai"


def test_auth_login_failure():
    response = client.post(
        "/api/auth/login",
        json={"username": "evaluator@callscope.ai", "password": "WrongPassword"},
    )
    assert response.status_code == 401


def test_create_batch_non_zip_rejected():
    response = client.post(
        "/api/batches",
        files={"file": ("test.mp3", b"dummy audio", "audio/mp3")},
    )
    assert response.status_code == 400
    assert "File must be a .zip archive" in response.json()["detail"]
