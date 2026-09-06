from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from packages.schemas.domain import Device, DeviceStatus, Workspace


class IdentityRepository(ABC):
    @abstractmethod
    def save_device(self, device: Device, *, owner_id: str | None = None) -> Device: ...

    @abstractmethod
    def list_devices(self, *, user_id: str | None = None) -> list[Device]: ...

    @abstractmethod
    def save_workspace(self, workspace: Workspace, *, user_id: str | None = None) -> Workspace: ...

    @abstractmethod
    def list_workspaces(self, *, user_id: str | None = None) -> list[Workspace]: ...

    @abstractmethod
    def is_project_member(self, project_id: str, user_id: str) -> bool: ...

    @abstractmethod
    def is_device_owner(self, device_id: str, user_id: str) -> bool: ...


class InMemoryIdentityRepository(IdentityRepository):
    def __init__(self) -> None:
        self.devices: dict[str, Device] = {}
        self.workspaces: dict[str, Workspace] = {}
        self.device_owners: dict[str, str] = {}
        self.workspace_members: dict[tuple[str, str], str] = {}

    def save_device(self, device: Device, *, owner_id: str | None = None) -> Device:
        self.devices[device.device_id] = device.model_copy(deep=True)
        if owner_id:
            self.device_owners[device.device_id] = owner_id
        return device.model_copy(deep=True)

    def list_devices(self, *, user_id: str | None = None) -> list[Device]:
        values = list(self.devices.values())
        if user_id is not None:
            values = [item for item in values if self.device_owners.get(item.device_id) == user_id]
        return [item.model_copy(deep=True) for item in values]

    def save_workspace(self, workspace: Workspace, *, user_id: str | None = None) -> Workspace:
        self.workspaces[workspace.workspace_id] = workspace.model_copy(deep=True)
        if user_id:
            self.workspace_members[(workspace.workspace_id, user_id)] = "owner"
        return workspace.model_copy(deep=True)

    def list_workspaces(self, *, user_id: str | None = None) -> list[Workspace]:
        values = list(self.workspaces.values())
        if user_id is not None:
            allowed = {wid for (wid, uid), _role in self.workspace_members.items() if uid == user_id}
            values = [item for item in values if item.workspace_id in allowed]
        return [item.model_copy(deep=True) for item in values]

    def is_project_member(self, project_id: str, user_id: str) -> bool:
        return any(
            workspace.project_id == project_id
            and (workspace.workspace_id, user_id) in self.workspace_members
            for workspace in self.workspaces.values()
        )

    def is_device_owner(self, device_id: str, user_id: str) -> bool:
        return self.device_owners.get(device_id) == user_id


class PostgresIdentityRepository(IdentityRepository):
    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("DATABASE_URL is required for PostgresIdentityRepository")
        self.dsn = dsn

    def _connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def save_device(self, device: Device, *, owner_id: str | None = None) -> Device:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO devices (device_id,owner_id,name,platform,hostname,status,vs_code_version,bridge_version,last_seen,created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (device_id) DO UPDATE SET
                  owner_id=COALESCE(EXCLUDED.owner_id,devices.owner_id), name=EXCLUDED.name, platform=EXCLUDED.platform,
                  hostname=EXCLUDED.hostname, status=EXCLUDED.status, vs_code_version=EXCLUDED.vs_code_version,
                  bridge_version=EXCLUDED.bridge_version, last_seen=EXCLUDED.last_seen
                RETURNING *
                """,
                (device.device_id, owner_id, device.name, device.platform, device.hostname, device.status.value,
                 device.vs_code_version, device.bridge_version, device.last_seen, device.created_at),
            )
            return _row_to_device(cur.fetchone())

    def list_devices(self, *, user_id: str | None = None) -> list[Device]:
        with self._connect() as conn, conn.cursor() as cur:
            if user_id:
                cur.execute("SELECT * FROM devices WHERE owner_id=%s ORDER BY created_at", (user_id,))
            else:
                cur.execute("SELECT * FROM devices ORDER BY created_at")
            return [_row_to_device(row) for row in cur.fetchall()]

    def save_workspace(self, workspace: Workspace, *, user_id: str | None = None) -> Workspace:
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
            result = _row_to_workspace(cur.fetchone())
            if user_id:
                cur.execute(
                    """
                    INSERT INTO workspace_members (workspace_id,user_id,role)
                    VALUES (%s,%s,'owner')
                    ON CONFLICT (workspace_id,user_id) DO UPDATE SET role='owner'
                    """,
                    (workspace.workspace_id, user_id),
                )
            return result

    def list_workspaces(self, *, user_id: str | None = None) -> list[Workspace]:
        with self._connect() as conn, conn.cursor() as cur:
            if user_id:
                cur.execute(
                    """
                    SELECT w.* FROM workspaces w
                    JOIN workspace_members wm ON wm.workspace_id=w.workspace_id
                    WHERE wm.user_id=%s ORDER BY w.created_at
                    """,
                    (user_id,),
                )
            else:
                cur.execute("SELECT * FROM workspaces ORDER BY created_at")
            return [_row_to_workspace(row) for row in cur.fetchall()]

    def is_project_member(self, project_id: str, user_id: str) -> bool:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS(
                  SELECT 1 FROM projects p WHERE p.project_id=%s AND p.owner_id=%s
                ) OR EXISTS(
                  SELECT 1 FROM workspace_members wm
                  JOIN workspaces w ON w.workspace_id=wm.workspace_id
                  WHERE w.project_id=%s AND wm.user_id=%s
                ) AS allowed
                """,
                (project_id, user_id, project_id, user_id),
            )
            return bool(cur.fetchone()["allowed"])

    def is_device_owner(self, device_id: str, user_id: str) -> bool:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT EXISTS(SELECT 1 FROM devices WHERE device_id=%s AND owner_id=%s) AS allowed", (device_id, user_id))
            return bool(cur.fetchone()["allowed"])


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
