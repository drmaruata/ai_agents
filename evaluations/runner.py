from __future__ import annotations

import json
from pathlib import Path

from services.orchestrator.ruata import RuataOrchestrator, TaskSpec


def run_ruata_fixture(path: str | Path) -> list[dict[str, object]]:
    fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    planner = RuataOrchestrator()
    results: list[dict[str, object]] = []
    for scenario in fixture["scenarios"]:
        task = TaskSpec(
            task_id=f"EVAL-{scenario['id']}",
            project_id="eval",
            title=str(scenario["input"]),
            description=str(scenario["input"]),
        )
        plan = planner.plan(task)
        agents = [item.agent.value for item in plan]
        expected = list(scenario.get("expected_agents", []))
        first_expected = scenario.get("expected_first_agent")
        passed = (not expected or all(agent in agents for agent in expected)) and (first_expected is None or agents[:1] == [first_expected])
        results.append({"id": scenario["id"], "passed": passed, "agents": agents, "expected_agents": expected, "expected_first_agent": first_expected})
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", default="evaluations/fixtures/ruata_planning.json")
    args = parser.parse_args()
    print(json.dumps(run_ruata_fixture(args.fixture), indent=2))
