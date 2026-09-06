from packages.schemas.domain import DeviceStatus, Workspace
from services.identity.repository import InMemoryIdentityRepository
from services.identity.service import IdentityService


def test_device_enrollment_and_workspace_registration() -> None:
    repository = InMemoryIdentityRepository()
    identity = IdentityService(repository)
    code = identity.create_enrollment_code("user-1")

    device = identity.enroll_device(
        code=code,
        device_id="device-1",
        name="Dev PC",
        platform="windows",
        hostname="DEVPC",
    )
    assert device.status == DeviceStatus.ONLINE
    assert repository.list_devices()[0].device_id == "device-1"

    workspace = identity.register_workspace(
        Workspace(
            workspace_id="workspace-1",
            project_id="project-1",
            device_id="device-1",
            name="Project",
            path="C:/Projects/project",
        )
    )
    assert workspace.registered is True
    assert repository.list_workspaces()[0].workspace_id == "workspace-1"

    identity.update_device_status("device-1", DeviceStatus.OFFLINE)
    assert repository.list_devices()[0].status == DeviceStatus.OFFLINE


def test_expired_or_unknown_code_is_rejected() -> None:
    identity = IdentityService()
    try:
        identity.enroll_device(code="bad", device_id="d", name="D", platform="x", hostname="h")
    except ValueError as exc:
        assert "Invalid or expired" in str(exc)
    else:
        raise AssertionError("invalid code was accepted")
