from fastapi.testclient import TestClient

from services.control_plane.auth import issue_dev_token
from services.control_plane.main import app

client = TestClient(app)


def auth_headers() -> dict[str, str]:
    """Return a valid development bearer token for authenticated API tests."""
    return {"Authorization": f"Bearer {issue_dev_token()}"}


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_protected_routes_reject_missing_credentials() -> None:
    assert client.get("/api/agents").status_code == 401
    assert client.get("/api/tasks?project_id=demo").status_code == 401


def test_agent_registry() -> None:
    response = client.get("/api/agents", headers=auth_headers())
    assert response.status_code == 200
    assert {agent["id"] for agent in response.json()} == {
        "ruata",
        "kimi",
        "manasseh",
        "john",
        "moses",
        "ian",
    }


def test_create_task() -> None:
    headers = auth_headers() | {"Idempotency-Key": "test-task-1"}
    payload = {
        "project_id": "demo",
        "title": "Scaffold task",
        "description": "Create the initial task",
        "risk_level": "low",
    }
    response = client.post("/api/tasks", headers=headers, json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["task_id"].startswith("TASK-")
    assert body["status"] == "backlog"

    retry = client.post("/api/tasks", headers=headers, json=payload)
    assert retry.status_code == 200
    assert retry.json()["task_id"] == body["task_id"]


def test_invalid_development_token_is_rejected() -> None:
    response = client.get(
        "/api/agents",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401


def test_idempotency_key_cannot_be_reused_for_a_different_task_request() -> None:
    headers = auth_headers() | {"Idempotency-Key": "test-task-payload-conflict"}
    first_payload = {
        "project_id": "demo",
        "title": "First request",
        "description": "Create the initial task",
        "risk_level": "low",
    }
    first = client.post("/api/tasks", headers=headers, json=first_payload)
    assert first.status_code == 200

    conflicting = client.post(
        "/api/tasks",
        headers=headers,
        json={**first_payload, "title": "Different request"},
    )
    assert conflicting.status_code == 409

