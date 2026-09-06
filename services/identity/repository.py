from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from packages.schemas.domain import Device, DeviceStatus, Workspace


class IdentityRepository(ABC):
    @abstractmethod
    def save_device(self, device: Device) -> Device: ...

    @abstractmethod
    def list_devices(self) -> list[Device]: ...

    @abstractmethod
    def save_workspace(self, workspace: Workspace) -> Workspace: ...

    @abstractmethod
    def list_workspaces(self) -> list[Workspace]: ...


class InMemoryIdentityRepository(IdentityRepository):
    def __init__(self) -> None:
        self.devices: dict[str, Device] = {}
        self.workspaces: dict[str, Workspace] = {}

    def save_device(self, device: Device) -> Device:
        self.devices[device.device_id] = device.model_copy(deep=True)
        return device.model_copy(deep=True)

    def list_devices(self) -> list[Device]:
        return [item.model_copy(deep=True) for item in self.devices.values()]

    def save_workspace(self, workspace: Workspace) -> Workspace:
        self.workspaces[workspace.workspace_id] = workspace.model_copy(deep=True)
        return workspace.model_copy(deep=True)

    def list_workspaces(self) -> list[Workspace]:
        return [item.model_copy(deep=True) for item in self.workspaces.values()]


class PostgresIdentityRepository(IdentityRepository):
    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("DATABASE_URL is required for PostgresIdentityRepository")
        self.dsn = dsn

    def _connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def save_device(self, device: Device) -> Device:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO devices (device_id,name,platform,hostname,status,vs_code_version,bridge_version,last_seen,created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (device_id) DO UPDATE SET
                  name=EXCLUDED.name, platform=EXCLUDED.platform, hostname=EXCLUDED.hostname,
                  status=EXCLUDED.status, vs_code_version=EXCLUDED.vs_code_version,
                  bridge_version=EXCLUDED.bridge_version, last_seen=EXCLUDED.last_seen
                RETURNING *
                """,
                (device.device_id, device.name, device.platform, device.hostname, device.status.value,
                 device.vs_code_version, device.bridge_version, device.last_seen, device.created_at),
            )
            return _row_to_device(cur.fetchone())

    def list_devices(self) -> list[Device]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM devices ORDER BY created_at")
            return [_row_to_device(row) for row in cur.fetchall()]

    def save_workspace(self, workspace: Workspace) -> Workspace:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO workspaces (workspace_id,project_id,device_id,name,path,registered,created_at,updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (workspace_id) DO UPDATE SET
                  project_id=EXCLUDED.project_id, device_id=EXCLUDED.device_id, name=EXCLUDED.name,
                  path=EXCLUDED.path, registered=EXCLUDED.registered, updated_at=EXCLUDED.updated_at
                RETURNING *
                """,
                (workspace.workspace_id, workspace.project_id, workspace.device_id, workspace.name,
                 workspace.path, workspace.registered, workspace.created_at, workspace.updated_at),
            )
            return _row_to_workspace(cur.fetchone())

    def list_workspaces(self) -> list[Workspace]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM workspaces ORDER BY created_at")
            return [_row_to_workspace(row) for row in cur.fetchall()]


def _row_to_device(row: dict[str, Any]) -> Device:
    return Device(
        device_id=row["device_id"], name=row["name"], platform=row["platform"], hostname=row["hostname"],
        status=DeviceStatus(row["status"]), vs_code_version=row["vs_code_version"],
        bridge_version=row["bridge_version"], last_seen=row["last_seen"], created_at=row["created_at"],
    )


def _row_to_workspace(row: dict[str, Any]) -> Workspace:
    return Workspace(
        workspace_id=row["workspace_id"], project_id=row["project_id"], device_id=row["device_id"],
        name=row["name"], path=row["path"], registered=row["registered"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )
