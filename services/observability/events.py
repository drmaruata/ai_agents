from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

logger = logging.getLogger("ruata.agent")


def emit(event: str, *, actor: str, task_id: str | None = None, **fields: Any) -> dict[str, Any]:
    record = {
        "event": event,
        "actor": actor,
        "task_id": task_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    logger.info(record)
    return record
