import pytest
from fastapi import HTTPException

from services.control_plane import main as control_plane


class Membership:
    def __init__(self, allowed: bool):
        self.allowed = allowed

    def can_access_project(self, project_id: str, user_id: str) -> bool:
        return self.allowed


@pytest.mark.parametrize("allowed", [False, True])
def test_supabase_project_access_is_membership_gated(monkeypatch, allowed: bool) -> None:
    monkeypatch.setattr(control_plane, "supabase_auth_enabled", lambda: True)
    monkeypatch.setattr(control_plane, "identity", type("IdentityStub", (), {"can_access_project": lambda self, project_id, user_id: allowed})())

    if allowed:
        control_plane.require_project_access("user-1", "project-1")
    else:
        with pytest.raises(HTTPException) as exc:
            control_plane.require_project_access("user-1", "project-1")
        assert exc.value.status_code == 403


def test_development_mode_does_not_apply_supabase_membership_check(monkeypatch) -> None:
    monkeypatch.setattr(control_plane, "supabase_auth_enabled", lambda: False)

    def should_not_be_called(*_args, **_kwargs):
        raise AssertionError("membership lookup should not run in development mode")

    monkeypatch.setattr(control_plane.identity, "can_access_project", should_not_be_called)
    control_plane.require_project_access("local-developer", "demo")
