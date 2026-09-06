# Ruata AI Software Development Platform

Hybrid cloud + local execution platform for a role-based AI software engineering team.

## Agent team

- **Ruata** — Principal Engineering Orchestrator
- **Kimi** — Research & Architecture Engineer
- **Manasseh** — Frontend Engineer
- **John** — Backend & Data Engineer
- **Ian** — Quality, Security & Reliability Engineer

## Architecture

See:

`AI Software Development Agent Team — Architecture & Agent Specifications.md`

## Repository policy

This repository uses **main-only development**. All changes are committed directly to `main`.

## Monorepo layout

```text
apps/
  dashboard/          Next.js dashboard placeholder
  api/                FastAPI control-plane scaffold
agents/               Agent role specifications
services/             Orchestrator/task/policy/runtime service packages
packages/              Shared schemas/types/tool contracts
local/                Local Agent Bridge
vscode-extension/     VS Code integration scaffold
infra/                 Deployment/configuration scaffolding
evaluations/           Agent evaluation fixtures
tests/                 Cross-service tests
docs/                  Architecture and API docs
```

## First implementation milestone

1. Start the FastAPI API service.
2. Start the dashboard.
3. Register a local device/workspace.
4. Connect the local bridge over an authenticated outbound WebSocket.
5. Create a task in Ruata and execute a safe local tool action.
6. Persist run/task state and test results.

## Development

The scaffold intentionally keeps provider/model integrations abstract. Add concrete model adapters under the agent runtime once the control-plane contracts are stable.
