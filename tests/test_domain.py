import pytest

from packages.schemas.domain import (
    RiskLevel,
    TaskStatus,
    validate_task_transition,
)


def test_valid_task_transitions():
    validate_task_transition(TaskStatus.BACKLOG, TaskStatus.ANALYZING)
    validate_task_transition(TaskStatus.ANALYZING, TaskStatus.RESEARCH)
    validate_task_transition(TaskStatus.RESEARCH, TaskStatus.PLANNED)
    validate_task_transition(TaskStatus.PLANNED, TaskStatus.IMPLEMENTING)
    validate_task_transition(TaskStatus.IMPLEMENTING, TaskStatus.VALIDATING)
    validate_task_transition(TaskStatus.VALIDATING, TaskStatus.REVIEW)
    validate_task_transition(TaskStatus.REVIEW, TaskStatus.HUMAN_APPROVAL)
    validate_task_transition(TaskStatus.HUMAN_APPROVAL, TaskStatus.COMPLETED)


def test_invalid_task_transition_is_rejected():
    with pytest.raises(ValueError):
        validate_task_transition(TaskStatus.BACKLOG, TaskStatus.COMPLETED)


def test_critical_risk_is_supported():
    assert RiskLevel.CRITICAL.value == "critical"
