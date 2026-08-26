from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_auth_header() -> dict[str, str]:
    login_resp = client.post(
        "/api/auth/login",
        json={"username": "evaluator@example.test", "password": "test-only-password"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "callscope-api"


def test_auth_login_success():
    response = client.post(
        "/api/auth/login",
        json={"username": "evaluator@example.test", "password": "test-only-password"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["username"] == "evaluator@example.test"


def test_auth_login_failure():
    response = client.post(
        "/api/auth/login",
        json={"username": "evaluator@example.test", "password": "WrongPassword"},
    )
    assert response.status_code == 401


def test_create_batch_unauthenticated_rejected():
    response = client.post(
        "/api/batches",
        files={"file": ("test.mp3", b"dummy audio", "audio/mp3")},
    )
    assert response.status_code == 401


def test_create_batch_audio_file_success_with_auth():
    headers = get_auth_header()
    response = client.post(
        "/api/batches",
        headers=headers,
        files={"file": ("test.mp3", b"dummy audio", "audio/mp3")},
    )
    assert response.status_code == 200
    assert "batch_id" in response.json()


def test_create_batch_unsupported_format_rejected():
    headers = get_auth_header()
    response = client.post(
        "/api/batches",
        headers=headers,
        files={"file": ("test.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_demo_backdoor_credentials_are_rejected():
    response = client.post("/api/auth/login", json={"username":"admin","password":"admin123"})
    assert response.status_code == 401
