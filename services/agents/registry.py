from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class AgentConfig:
    agent_id: str
    name: str
    role: str
    instructions_file: str


AGENT_CONFIGS = {
    "ruata": AgentConfig("ruata", "Ruata", "orchestrator", str(ROOT / "agents/ruata/system.md")),
    "kimi": AgentConfig("kimi", "Kimi", "research_architecture", str(ROOT / "agents/kimi/system.md")),
    "manasseh": AgentConfig("manasseh", "Manasseh", "frontend", str(ROOT / "agents/manasseh/system.md")),
    "john": AgentConfig("john", "John", "backend_data", str(ROOT / "agents/john/system.md")),
    "moses": AgentConfig("moses", "Moses", "mobile", str(ROOT / "agents/moses/system.md")),
    "ian": AgentConfig("ian", "Ian", "qa_security_reliability", str(ROOT / "agents/ian/system.md")),
}
