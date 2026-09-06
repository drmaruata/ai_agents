from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    RUATA = "ruata"
    KIMI = "kimi"
    MANASSEH = "manasseh"
    JOHN = "john"
    IAN = "ian"


class TaskStatus(str, Enum):
    BACKLOG = "backlog"
    ANALYZING = "analyzing"
    PLANNED = "planned"
    IMPLEMENTING = "implementing"
    VALIDATING = "validating"
    REPAIR = "repair"
    REVIEW = "review"
    HUMAN_APPROVAL = "human_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskCreate(BaseModel):
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    risk_level: str = "low"


class Task(TaskCreate):
    task_id: str
    status: TaskStatus = TaskStatus.BACKLOG
    assigned_agent: AgentRole | None = None


app = FastAPI(title="Ruata Control Plane", version="0.1.0")
tasks: dict[str, Task] = {}
connections: set[WebSocket] = set()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "control-plane"}


@app.get("/api/agents")
def agents() -> list[dict[str, Any]]:
    return [
        {"id": "ruata", "name": "Ruata", "role": "orchestrator", "status": "idle"},
        {"id": "kimi", "name": "Kimi", "role": "research_architecture", "status": "idle"},
        {"id": "manasseh", "name": "Manasseh", "role": "frontend", "status": "idle"},
        {"id": "john", "name": "John", "role": "backend_data", "status": "idle"},
        {"id": "ian", "name": "Ian", "role": "qa_security_reliability", "status": "idle"},
    ]


@app.post("/api/tasks", response_model=Task)
async def create_task(payload: TaskCreate) -> Task:
    task = Task(task_id=f"TASK-{uuid4().hex[:8].upper()}", **payload.model_dump())
    tasks[task.task_id] = task
    await broadcast({"event": "task.created", "task": task.model_dump(mode="json")})
    return task


@app.get("/api/tasks", response_model=list[Task])
def list_tasks() -> list[Task]:
    return list(tasks.values())


@app.websocket("/ws/events")
async def events(websocket: WebSocket) -> None:
    await websocket.accept()
    connections.add(websocket)
    try:
        await websocket.send_json({"event": "connection.ready"})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections.discard(websocket)


async def broadcast(message: dict[str, Any]) -> None:
    stale: list[WebSocket] = []
    for connection in connections:
        try:
            await connection.send_json(message)
        except Exception:
            stale.append(connection)
    for connection in stale:
        connections.discard(connection)
