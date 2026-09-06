# Ruata AI Software Development Platform

Hybrid cloud + local execution platform for a role-based AI software engineering team.

The platform is designed around five specialist agents coordinated by Ruata, with a cloud control plane and a secure local development bridge for working with projects on a developer workstation.

## Agent team

- **Ruata** — Principal Engineering Orchestrator
- **Kimi** — Research & Architecture Engineer
- **Manasseh** — Frontend Engineer
- **John** — Backend & Data Engineer
- **Ian** — Quality, Security & Reliability Engineer

## Current implementation status

The project is under active phased development. Phases 0–8 have working foundations, with supporting implementation for the later platform phases. See the live status table in `AI Software Development Agent Team — Development Roadmap.md`.

Currently implemented foundations include:

- Shared domain models and task state machine.
- PostgreSQL schema and repository abstraction.
- Development JWT authentication primitives.
- Device and workspace enrollment services.
- Local Agent Bridge with workspace/path/command policy enforcement.
- Secure outbound WebSocket bridge protocol.
- Agent/tool policy engine and explicit high-risk approval gate.
- Shared tool registry.
- Ruata task planning and specialist routing.
- Provider-neutral OpenAI Agents SDK adapter.
- Five role-specific agent specifications.
- Initial Next.js dashboard.
- VS Code extension that can start/stop the local bridge.
- Git worktree manager.
- Docker-based local sandbox adapter.
- GitHub Actions CI.
- Initial Ruata evaluation fixtures/runner.
- Structured observability events.

The project is **not yet a production-ready autonomous coding platform**. Authentication persistence, cloud MCP servers, full tool implementations, production sandbox providers, comprehensive dashboard workflows, centralized observability, security testing, and the first full end-to-end benchmark are still being implemented.

## Architecture

See the canonical architecture specification:

`AI_Software_Development_Agent_Team_Architecture.md`

The development roadmap is:

`AI Software Development Agent Team — Development Roadmap.md`

Target operating model:

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
     +-- Git / Worktrees
     +-- Browser / Playwright
     +-- Docker / local tooling
```

The local bridge is the workstation security boundary. It should not expose an unrestricted inbound server.

## Repository policy

This repository uses **main-only development**. All changes are committed directly to `main`. Do not create feature branches or pull requests for routine development unless this policy is explicitly changed.

Read `AGENTS.md` before making implementation changes.

## Monorepo layout

```text
apps/
  dashboard/          Next.js dashboard
agents/               Agent role specifications
services/
  control_plane/      FastAPI API/control plane
  agents/             Model runtime and agent composition
  orchestrator/       Ruata planning
  persistence/        In-memory/PostgreSQL repositories
  identity/           Device/workspace identity service
  approval/           Human approval gate
  policy/             Least-privilege policy engine
  tool_gateway/       Shared tool registry
  bridge/             Cloud-side bridge connection manager
  git/                Git worktree management
  sandbox/            Sandbox abstraction and local Docker adapter
  observability/      Structured operational events
packages/
  schemas/            Shared domain contracts
local/
  bridge/             Developer workstation bridge
vscode-extension/     VS Code integration
config/               Declarative agent policies
infra/
  db/                 PostgreSQL schema migrations
  docker-compose.yml  Local Postgres/Redis
  ...                 Deployment scaffolding
evaluations/           Agent evaluation fixtures and runners
tests/                 Cross-service/unit/security tests
docs/                  Architecture, API, security and operations
```

## Prerequisites

For the Python control plane and local bridge:

- **Python 3.11 or newer**
- **Git**
- A terminal / shell

For the dashboard:

- **Node.js 22 or newer**
- npm

For the VS Code integration:

- VS Code
- Node.js/npm
- A Python executable visible to the extension

For local persistence/sandbox development:

- Docker Desktop or Docker Engine

## Clone the repository

```bash
git clone https://github.com/drmaruata/ai_agents.git
cd ai_agents
git checkout main
git branch --show-current
```

The branch should be `main`.

## Local Python environment

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

### Windows Command Prompt

```cmd
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e .
```

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Configure local environment

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Set at minimum for model-backed development:

```dotenv
ENVIRONMENT=development
JWT_SECRET=replace-with-a-long-local-development-secret
OPENAI_API_KEY=your-key
MODEL_PROVIDER=openai
MODEL_NAME=your-supported-model
```

If using the local Postgres stack:

```dotenv
DATABASE_URL=postgresql://ruata:ruata@localhost:5432/ruata
```

Do not commit `.env` or real credentials.

## Start local infrastructure

```bash
docker compose -f infra/docker-compose.yml up -d
```

Check containers:

```bash
docker compose -f infra/docker-compose.yml ps
```

The current compose stack provides PostgreSQL and Redis for local development. Apply `infra/db/001_initial_schema.sql` and `infra/db/002_identity.sql` to PostgreSQL before running the API with `DATABASE_URL` configured.

One way to apply the SQL using `psql` is:

```bash
psql postgresql://ruata:ruata@localhost:5432/ruata -f infra/db/001_initial_schema.sql
psql postgresql://ruata:ruata@localhost:5432/ruata -f infra/db/002_identity.sql
```

## Start the control plane

With `.venv` activated:

```bash
python -m uvicorn services.control_plane.main:app --reload --host 127.0.0.1 --port 8000
```

Endpoints:

```text
Health: http://127.0.0.1:8000/health
Docs:   http://127.0.0.1:8000/docs
```

In development, a temporary JWT can be requested with:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/dev-token
```

Use the returned bearer token for authenticated API calls.

## Start the dashboard

In a second terminal:

```bash
cd apps/dashboard
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

The dashboard currently reads agent/task state from the control plane and serves as the starting point for the full Agents Dashboard described in the roadmap.

## Run the tests

From repository root:

```bash
python -m pytest -v
```

The current suite covers the domain state machine, Ruata planner, identity enrollment, approval behavior, and local bridge policy controls. The suite will expand as the remaining roadmap phases are implemented.

## Run the Ruata evaluation fixture

```bash
python evaluations/runner.py
```

This currently validates deterministic routing scenarios. Model-quality evaluations will be added under `evaluations/ruata`, `evaluations/kimi`, `evaluations/john`, `evaluations/manasseh`, `evaluations/ian`, and `evaluations/system`.

## Local Agent Bridge

The Local Agent Bridge lives under:

```text
local/bridge/
```

It is intended to run on the developer workstation and maintain an authenticated outbound connection to the control plane.

The current bridge CLI requires:

```bash
python -m local.bridge.main \
  --workspace /path/to/project \
  --url ws://127.0.0.1:8000/ws/bridge \
  --token YOUR_BRIDGE_TOKEN \
  --device-id YOUR_DEVICE_ID \
  --project-id YOUR_PROJECT_ID \
  --workspace-id YOUR_WORKSPACE_ID
```

The bridge currently supports the first safe tool set:

```text
file.read
file.write
terminal.run
git.diff
```

Before executing a request it validates workspace scope, sensitive-path blocks, agent/tool policy, command allowlists, and risk level.

## Device enrollment

The intended development flow is:

```text
1. Start control plane.
2. Obtain a development auth token.
3. Request a device enrollment code.
4. Enroll the workstation/device.
5. Register a workspace.
6. Configure the device ID in the VS Code extension.
7. Start the Local Agent Bridge.
```

The identity service is currently an application-level development implementation. Durable user/device/workspace persistence and production identity integration remain roadmap work.

## VS Code extension

From the extension directory:

```bash
cd vscode-extension
npm install
npm run compile
```

Open the extension folder in VS Code and use **Run Extension** from the Extension Development Host workflow.

Configure:

```text
ruata.controlPlaneUrl
ruata.bridgeToken
ruata.deviceId
ruata.pythonPath
```

Then run:

```text
Ruata: Connect
```

The extension starts the local bridge for the currently opened workspace. `Ruata: Status` reports the current workspace/device/bridge state, and `Ruata: Stop Local Bridge` terminates it.

Production credential storage will move to VS Code/OS secure storage as the extension matures.

## Git worktrees

The project contains a worktree manager under:

```text
services/git/worktree.py
```

The intended agent isolation model is:

```text
main
 |
 +-- task-123-john
 +-- task-123-manasseh
 +-- task-123-ian
```

This repository itself remains **main-only**. Agent worktree isolation applies to the development projects being operated on by the platform, not to this repository's contribution policy.

## CI

GitHub Actions is configured in:

```text
.github/workflows/ci.yml
```

Pushes to `main` run Python tests across supported Python versions plus dashboard and VS Code compilation checks.

## Security model

The platform follows least privilege by default:

- The cloud should not receive unrestricted filesystem access.
- Local communication is outbound and authenticated.
- Workspaces are explicitly selected and scoped.
- `.env`, credentials, secrets, and private-key paths are blocked by default.
- Commands use `shell=False` in the local bridge.
- Agent/tool/path/risk policy is evaluated before execution.
- High/critical local actions require an approval workflow.
- Agents must not weaken tests, linting, type checks, or security controls to hide failures.

See `AI_Software_Development_Agent_Team_Architecture.md` for the complete security and operating model.

## Development sequence

The implementation follows:

`AI Software Development Agent Team — Development Roadmap.md`

The intended order is:

```text
Foundation
  -> Persistence / Identity
  -> Local Bridge / Policy
  -> Tools / MCP
  -> Ruata
  -> Kimi
  -> John
  -> Manasseh
  -> Ian
  -> VS Code / Dashboard
  -> Git / CI
  -> Sandboxes / Evaluations / Observability
  -> Security Hardening
  -> Production Deployment
  -> End-to-End Benchmark
```

Do not skip acceptance gates merely to expose more autonomy earlier.
