from packages.schemas.domain import DeviceStatus, Workspace
from services.identity.repository import InMemoryIdentityRepository
from services.identity.service import IdentityService


def test_device_enrollment_and_workspace_registration() -> None:
    repository = InMemoryIdentityRepository()
    identity = IdentityService(repository)
    code = identity.create_enrollment_code("user-1")

    device = identity.enroll_device(
        code=code,
        user_id="user-1",
        device_id="device-1",
        name="Dev PC",
        platform="windows",
        hostname="DEVPC",
    )
    assert device.status == DeviceStatus.ONLINE
    assert repository.list_devices(user_id="user-1")[0].device_id == "device-1"
    assert not repository.list_devices(user_id="user-2")

    workspace = identity.register_workspace(
        Workspace(
            workspace_id="workspace-1",
            project_id="project-1",
            device_id="device-1",
            name="Project",
            path="C:/Projects/project",
        ),
        user_id="user-1",
    )
    assert workspace.registered is True
    assert repository.list_workspaces(user_id="user-1")[0].workspace_id == "workspace-1"
    assert identity.can_access_project("project-1", "user-1") is True
    assert identity.can_access_project("project-1", "user-2") is False

    identity.update_device_status("device-1", DeviceStatus.OFFLINE)
    assert repository.list_devices(user_id="user-1")[0].status == DeviceStatus.OFFLINE


def test_wrong_user_cannot_enroll_or_register_workspace() -> None:
    identity = IdentityService(InMemoryIdentityRepository())
    code = identity.create_enrollment_code("user-1")
    try:
        identity.enroll_device(
            code=code,
            user_id="user-2",
            device_id="device-1",
            name="Dev PC",
            platform="windows",
            hostname="DEVPC",
        )
    except ValueError as exc:
        assert "Invalid or expired" in str(exc)
    else:
        raise AssertionError("wrong user enrolled device")


def test_expired_or_unknown_code_is_rejected() -> None:
    identity = IdentityService()
    try:
        identity.enroll_device(code="bad", user_id="user-1", device_id="d", name="D", platform="x", hostname="h")
    except ValueError as exc:
        assert "Invalid or expired" in str(exc)
    else:
        raise AssertionError("invalid code was accepted")
