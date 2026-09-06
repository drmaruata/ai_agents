from services.identity.service import IdentityService
from packages.schemas.domain import DeviceStatus, Workspace


def test_device_enrollment_and_workspace_registration():
    identity = IdentityService()
    code = identity.create_enrollment_code("user-1")
    device = identity.enroll_device(
        code=code,
        device_id="device-1",
        name="Dev PC",
        platform="windows",
        hostname="DEVPC",
    )
    assert device.status == DeviceStatus.ONLINE

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


def test_expired_or_unknown_code_is_rejected():
    identity = IdentityService()
    try:
        identity.enroll_device(code="bad", device_id="d", name="D", platform="x", hostname="h")
    except ValueError as exc:
        assert "Invalid or expired" in str(exc)
    else:
        raise AssertionError("invalid code was accepted")
