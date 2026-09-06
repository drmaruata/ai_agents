# AI Software Development Agent Team — Development Roadmap

**Repository:** `drmaruata/ai_agents`  
**Development branch:** `main` only  
**Target:** Production-grade hybrid cloud + local AI software engineering platform  
**Roadmap version:** 1.0  
**Status:** Active implementation roadmap

---

## Implementation Status — 2026-09-06

The roadmap is being executed directly on `main`. The current implementation has moved beyond the initial scaffold and now includes the first working foundations for Phases 0–8 plus supporting foundations for later phases.

| Phase | Status | Current implementation |
|---|---|---|
| 0 | **Complete** | Repository baseline, `AGENTS.md`, architecture, README, environment configuration |
| 1 | **Complete** | Shared domain entities, task state machine, transition validation, tests |
| 2 | **In progress** | PostgreSQL schema, repository abstraction, durable task/run/audit persistence |
| 3 | **In progress** | JWT development authentication, device enrollment, workspace registration; production identity persistence still required |
| 4 | **In progress** | Local bridge, outbound WebSocket protocol, scoped filesystem/command execution |
| 5 | **In progress** | Agent/tool/path/command/risk policy engine and high-risk approval gate |
| 6 | **In progress** | Shared tool registry and MCP-ready contracts; production MCP servers remain to be integrated |
| 7 | **In progress** | Deterministic Ruata planner, task decomposition, specialist routing, orchestration service |
| 8 | **In progress** | Kimi role contract and provider-neutral model runtime; research web/tool execution remains to be completed |
| 9 | **Foundation ready** | John agent contract and model runtime; full backend coding toolchain remains |
| 10 | **Foundation ready** | Manasseh agent contract and VS Code/browser foundation; full frontend coding workflow remains |
| 11 | **Foundation ready** | Ian QA contract, validation result model and test fixtures; full automated QA pipeline remains |
| 12 | **In progress** | VS Code extension connects to local bridge and exposes status/start/stop controls |
| 13 | **In progress** | Next.js dashboard connected to live control-plane agent/task state |
| 14 | **Foundation ready** | Git worktree manager added; agent worktree lifecycle integration remains |
| 15 | **Foundation ready** | GitHub Actions CI for Python, dashboard, and VS Code extension |
| 16 | **Foundation ready** | Sandbox interface and local Docker adapter; cloud sandbox provider integration remains |
| 17 | **Foundation ready** | Ruata planning fixtures and deterministic evaluation runner |
| 18 | **Foundation ready** | Structured observability events; centralized tracing/cost/metrics remains |
| 19 | **Planned** | Threat model and controls defined; dedicated security test suite remains |
| 20 | **Planned** | Production deployment topology defined; production infrastructure and operations remain |
| 21 | **Planned** | First real end-to-end benchmark remains the primary v1.0 acceptance test |

**Important:** “Foundation ready” does not mean the phase is production-complete. A phase is complete only when its acceptance gate is demonstrably satisfied in the running system.

---

## 1. Purpose

This document defines the phased development plan for the **Ruata AI Software Development Platform**: a controlled, role-based AI software engineering team consisting of Ruata, Kimi, Manasseh, John, and Ian.

The platform is designed to let a developer submit software-development work through an Agents Dashboard while specialist agents plan, research, implement, test, review, and validate changes. A secure Local Agent Bridge provides controlled access to the developer's workstation, VS Code workspace, terminal, Git repository, browser, and other approved development tools. Cloud sandboxes can be added for isolated or long-running work.

The roadmap deliberately separates **control**, **intelligence**, and **execution** so model providers, local tooling, and cloud infrastructure can evolve independently.

---
