from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from packages.schemas.domain import Device, DeviceStatus, Workspace

from .repository import IdentityRepository, InMemoryIdentityRepository


@dataclass(slots=True)
class Enrollment:
    code_hash: str
    user_id: str
    expires_at: datetime


class IdentityService:
    """Identity and workstation registry with pluggable persistence."""

    def __init__(self, repository: IdentityRepository | None = None) -> None:
        self.repository = repository or InMemoryIdentityRepository()
        self.devices: dict[str, Device] = {item.device_id: item for item in self.repository.list_devices()}
        self.workspaces: dict[str, Workspace] = {item.workspace_id: item for item in self.repository.list_workspaces()}
        self.enrollments: dict[str, Enrollment] = {}

    def create_enrollment_code(self, user_id: str, ttl_minutes: int = 10) -> str:
        raw = secrets.token_urlsafe(8)
        self.enrollments[self._hash(raw)] = Enrollment(
            code_hash=self._hash(raw),
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes),
        )
        return raw

    def enroll_device(
        self,
        *,
        code: str,
        device_id: str,
        name: str,
        platform: str,
        hostname: str,
        vs_code_version: str | None = None,
        bridge_version: str | None = None,
    ) -> Device:
        key = self._hash(code)
        enrollment = self.enrollments.get(key)
        now = datetime.now(timezone.utc)
        if enrollment is None or enrollment.expires_at <= now:
            raise ValueError("Invalid or expired enrollment code")
        device = Device(
            device_id=device_id,
            name=name,
            platform=platform,
            hostname=hostname,
            status=DeviceStatus.ONLINE,
            vs_code_version=vs_code_version,
            bridge_version=bridge_version,
            last_seen=now,
        )
        persisted = self.repository.save_device(device)
        self.devices[device_id] = persisted
        del self.enrollments[key]
        return persisted.model_copy(deep=True)

    def update_device_status(self, device_id: str, status: DeviceStatus, *, last_seen: datetime | None = None) -> Device:
        device = self.devices.get(device_id)
        if device is None:
            raise ValueError("Device is not registered")
        device.status = status
        device.last_seen = last_seen or datetime.now(timezone.utc)
        persisted = self.repository.save_device(device)
        self.devices[device_id] = persisted
        return persisted.model_copy(deep=True)

    def register_workspace(self, workspace: Workspace) -> Workspace:
        if workspace.device_id not in self.devices:
            raise ValueError("Device is not registered")
        workspace.registered = True
        workspace.updated_at = datetime.now(timezone.utc)
        persisted = self.repository.save_workspace(workspace)
        self.workspaces[workspace.workspace_id] = persisted
        return persisted.model_copy(deep=True)

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
