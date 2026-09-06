# Ruata AI Software Development Platform

Hybrid cloud + local execution platform for a role-based AI software engineering team.

The platform is designed around five specialist agents coordinated by Ruata, with a cloud control plane and a secure local development bridge for working with projects on a developer workstation.

## Agent team

- **Ruata** — Principal Engineering Orchestrator
- **Kimi** — Research & Architecture Engineer
- **Manasseh** — Frontend Engineer
- **John** — Backend & Data Engineer
- **Ian** — Quality, Security & Reliability Engineer

## Architecture

See the canonical architecture specification:

`AI Software Development Agent Team — Architecture & Agent Specifications.md`

The target operating model is:

```text
Web Dashboard
     |
     v
Cloud Control Plane
     |
     +-- Ruata Orchestrator
     +-- Kimi
     +-- Manasseh
     +-- John
     +-- Ian
     |
     | authenticated outbound connection
     v
Local Agent Bridge
     |
     +-- VS Code
     +-- Workspace / Files
     +-- Terminal
     +-- Git
     +-- Browser / Playwright
     +-- Docker / local tooling
```

The local bridge is intended to be the security boundary between cloud agents and the developer workstation. It should not expose an unrestricted inbound server.

## Repository policy

This repository uses **main-only development**. All changes are committed directly to `main`. Do not create feature branches or pull requests for routine development in this repository unless this policy is explicitly changed.

## Monorepo layout

```text
apps/
  dashboard/          Web dashboard scaffold
  api/                API/application scaffold
agents/               Agent role specifications
services/             Control-plane/orchestration service packages
packages/              Shared schemas/types/tool contracts
local/
  bridge/             Local Agent Bridge scaffold
vscode-extension/     VS Code integration scaffold
infra/                 Deployment/configuration scaffolding
evaluations/           Agent evaluation fixtures
tests/                 Cross-service tests
docs/                  Architecture and API documentation
```

## Prerequisites

For the current Python control-plane scaffold:

- **Python 3.11 or newer**
- **Git**
- A terminal / shell

For later dashboard and VS Code work, you will additionally need the normal Node.js/npm and VS Code development toolchain. Those parts of the repository are currently scaffolds and are not yet a complete production dashboard/extension release.

## Clone the repository

```bash
git clone https://github.com/drmaruata/ai_agents.git
cd ai_agents
git checkout main
```

Verify that you are on `main`:

```bash
git branch --show-current
```

It should print:

```text
main
```

## Local Python environment

Create a virtual environment:

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```cmd
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
```

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Upgrade pip and install the project in editable mode:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

The current project metadata requires Python 3.11+ and includes FastAPI, Uvicorn, Pydantic, WebSockets, HTTPX, and pytest dependencies.

## Configure local environment variables

Copy the example environment file:

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### macOS / Linux

```bash
cp .env.example .env
```

The current scaffold uses these main settings:

```dotenv
ENVIRONMENT=development
API_HOST=127.0.0.1
API_PORT=8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
RUATA_CONTROL_PLANE_URL=ws://localhost:8000/ws/bridge
RUATA_DEVICE_ID=
RUATA_DEVICE_TOKEN=
MODEL_PROVIDER=
MODEL_NAME=
MODEL_API_KEY=
DATABASE_URL=
```

For local development, do not commit `.env` or real credentials. Use `.env.example` as the template.

## Start the current control-plane API

From the repository root, with the virtual environment activated:

```bash
python -m uvicorn services.control_plane.main:app --reload --host 127.0.0.1 --port 8000
```

The development API should then be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

The current scaffold exposes the initial control-plane endpoints for agents and tasks and an event WebSocket. These are development contracts and are expected to evolve as persistence, authentication, the policy engine, and the full bridge protocol are implemented.

## Run the tests

With the virtual environment activated:

```bash
python -m pytest
```

For a more verbose run:

```bash
python -m pytest -v
```

## Local Agent Bridge

The Local Agent Bridge is the workstation-side component that will eventually allow Ruata and the specialist agents to work on selected local projects through VS Code and approved development tools.

Current source location:

```text
local/bridge/
```

The bridge is intentionally scaffolded separately from the cloud control plane. Its production design should:

- Maintain an authenticated **outbound** connection to the cloud control plane.
- Register the developer device and permitted workspaces.
- Enforce project, workspace, agent, and tool permissions.
- Execute approved filesystem, terminal, Git, browser, and VS Code actions.
- Return structured results and audit events.
- Fail closed when policy is ambiguous.
- Store credentials using OS-secure credential storage in the production implementation.

The current bridge code is a scaffold, not yet the complete secure workstation agent.

## VS Code integration

The VS Code integration is located in:

```text
vscode-extension/
```

The planned architecture is a VS Code extension plus the Local Agent Bridge. The extension will expose editor/workspace context and safe developer actions while the bridge enforces workstation-level permissions.

The production workflow is intended to be:

```text
Ruata / specialist agent
        |
        v
Cloud Control Plane
        |
   authenticated outbound connection
        |
        v
Local Agent Bridge
        |
        v
VS Code Extension
        |
        +-- workspace files
        +-- diagnostics
        +-- terminal
        +-- Git
        +-- tests
        +-- browser tooling
```

## Running the development stack

For the current scaffold, start the pieces independently in separate terminals.

### Terminal 1 — Control plane

```bash
source .venv/bin/activate  # macOS/Linux
python -m uvicorn services.control_plane.main:app --reload --host 127.0.0.1 --port 8000
```

On Windows PowerShell, activate `.venv` first using:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then run the same Uvicorn command.

### Terminal 2 — Tests / development commands

Use this terminal for the test suite, API checks, or later local agent processes:

```bash
python -m pytest -v
```

The dashboard, full local bridge protocol, model adapters, persistent task store, and production VS Code extension are not yet wired into a single `docker compose up` or one-command development environment. That integration is part of the next implementation phases.

## First end-to-end milestone

The next functional target is:

```text
1. Start the FastAPI control plane.
2. Start the dashboard locally.
3. Register a local development device/workspace.
4. Establish an authenticated outbound bridge connection.
5. Create a task in Ruata.
6. Delegate a safe local tool action.
7. Execute it in a selected workspace.
8. Return structured execution results.
9. Persist task/run state and test results.
10. Validate the change through Ian's quality gates.
```

## Model providers

Model integrations are intentionally abstracted in the scaffold. Configure provider/model information through environment variables once concrete adapters are implemented.

Do not hard-code API keys in source files, agent prompts, GitHub Actions files, or repository configuration.

## Git workflow for this repository

Because this repository is **main-only**, normal updates should be made as follows:

```bash
git checkout main
git pull origin main
# make changes
python -m pytest
git add .
git commit -m "describe the change"
git push origin main
```

Keep commits focused and preserve a passing development state whenever practical.

## Security principles

The platform is designed around a least-privilege model.

- The cloud must not receive unrestricted access to the developer filesystem.
- The local bridge should use an outbound authenticated connection rather than an open inbound port.
- Workspaces should be explicitly registered and permission-scoped.
- Secrets must be excluded from agent context unless explicitly required and authorized.
- Destructive operations, production changes, credential changes, and other high-risk actions should require approval.
- Agents must not disable tests, linting, type checking, or security controls merely to make a task pass.
- Audit events should be retained for agent actions and policy decisions.

## Canonical architecture document

The full system design, agent specifications, permissions, task lifecycle, execution model, security architecture, observability requirements, and staged implementation plan are maintained in:

`AI Software Development Agent Team — Architecture & Agent Specifications.md`

Read that document before making architectural changes to the platform.
