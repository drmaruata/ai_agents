from fastapi.testclient import TestClient

from services.control_plane.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_agent_registry() -> None:
    response = client.get("/api/agents")
    assert response.status_code == 200
    assert {agent["id"] for agent in response.json()} == {
        "ruata",
        "kimi",
        "manasseh",
        "john",
        "ian",
    }


def test_create_task() -> None:
    response = client.post(
        "/api/tasks",
        headers={"Idempotency-Key": "test-task-1"},
        json={
            "project_id": "demo",
            "title": "Scaffold task",
            "description": "Create the initial task",
            "risk_level": "low",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["task_id"].startswith("TASK-")
    assert body["status"] == "backlog"

    retry = client.post(
        "/api/tasks",
        headers={"Idempotency-Key": "test-task-1"},
        json={
            "project_id": "demo",
            "title": "Scaffold task",
            "description": "Create the initial task",
            "risk_level": "low",
        },
    )
    assert retry.status_code == 200
    assert retry.json()["task_id"] == body["task_id"]
