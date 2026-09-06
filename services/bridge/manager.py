from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from fastapi import WebSocket


@dataclass(slots=True)
class PendingRequest:
    future: asyncio.Future[dict[str, Any]]


class BridgeConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[str, WebSocket] = {}
        self.pending: dict[str, PendingRequest] = {}

    async def register(self, device_id: str, websocket: WebSocket) -> None:
        previous = self.connections.get(device_id)
        if previous is not None and previous is not websocket:
            try:
                await previous.close(code=1012, reason="replaced")
            except Exception:
                pass
        self.connections[device_id] = websocket

    def unregister(self, device_id: str, websocket: WebSocket) -> None:
        if self.connections.get(device_id) is websocket:
            self.connections.pop(device_id, None)

    def connected_devices(self) -> list[str]:
        return sorted(self.connections)

    async def send_tool_request(self, device_id: str, tool: str, args: dict[str, Any], timeout: float = 120.0) -> dict[str, Any]:
        websocket = self.connections.get(device_id)
        if websocket is None:
            raise ConnectionError(f"Device is not connected: {device_id}")
        request_id = f"REQ-{uuid4().hex[:12].upper()}"
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self.pending[request_id] = PendingRequest(future=future)
        await websocket.send_text(json.dumps({"version": "1", "type": "tool.request", "request_id": request_id, "tool": tool, "args": args}))
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            self.pending.pop(request_id, None)

    def resolve_response(self, message: dict[str, Any]) -> bool:
        request_id = str(message.get("request_id", ""))
        pending = self.pending.get(request_id)
        if pending is None or pending.future.done():
            return False
        pending.future.set_result(message)
        return True
