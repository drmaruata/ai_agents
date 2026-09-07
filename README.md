# Ruata AI Software Development Platform

Hybrid cloud + local execution platform for a role-based AI software engineering team.

The platform is designed around six specialist agents coordinated by Ruata, a **Supabase-backed cloud platform**, a Python/FastAPI control plane, and a secure local development bridge for working with projects on a developer workstation.

> **Canonical documentation:** `AI_Software_Development_Agent_Team_Architecture.md` defines the target architecture; `AI Software Development Agent Team — Development Roadmap.md` defines implementation order and acceptance gates; `docs/MOSES_MOBILE_AGENT_ARCHITECTURE_ADDENDUM.md` and `docs/MOSES_MOBILE_AGENT_ROADMAP_ADDENDUM.md` define the Moses-specific extension to the six-agent fleet. This README is the operational entry point and must remain consistent with those documents.

## Agent team

- **Ruata** — Principal Engineering Orchestrator
- **Kimi** — Research & Architecture Engineer
- **Manasseh** — Frontend / Web Engineer
- **John** — Backend & Data Engineer
- **Moses** — Mobile Application Engineer
- **Ian** — Quality, Security & Reliability Engineer

Moses owns mobile application development for iOS and Android across React Native/Expo, Flutter, and native platform implementations. John owns backend/API/data contracts; Manasseh owns the web client; Ian validates the complete cross-platform result.

## Backend architecture: Supabase-first

Supabase is the **canonical managed cloud backend foundation** for this project.

```text
Supabase
├── Auth              Production user identity and sessions
├── PostgreSQL        Durable application/runtime state
├── RLS               Database-enforced authorization
├── Realtime          Live dashboard/application state
├── Storage           Larger artifacts and blobs
└── Edge Functions    Bounded webhooks/lightweight server operations

Python/FastAPI Control Plane
├── Ruata orchestration
├── Agent runtime
├── Task scheduling
├── Policy engine
├── Tool gateway
├── Approval workflow
├── Long-running/background workers
└── Secure local-bridge gateway

Local Agent Bridge
├── Filesystem
├── Terminal
├── Git / worktrees
├── Browser / Playwright
├── Docker / local tooling
└── VS Code integration
```

Supabase is not intended to replace the Python control plane. The control plane owns orchestration, model execution, policy, approvals, long-running jobs, and the secure bridge protocol. Supabase provides managed identity, relational persistence, authorization, realtime delivery, and appropriate storage/serverless primitives.

Self-managed PostgreSQL remains an optional local/integration-test configuration. It is not the production source of truth.

## Current implementation status

The project is under active phased development. Early domain, persistence, identity, bridge, policy, orchestration, agent-runtime, dashboard, VS Code, evaluation, CI, sandbox, and observability foundations exist, with Moses now registered as the sixth specialist agent. The system is **not yet a production-ready autonomous coding platform**.

The current mobile-agent flow is:

```text
Mobile requirement
        ↓
Ruata classification
        ↓
Moses mobile implementation
        ↓
John shared backend/API as required
        +
Manasseh web implementation as required
        ↓
Ian cross-platform validation
```

See `AI Software Development Agent Team — Development Roadmap.md` and the Moses addenda for the current phase table and acceptance gates.

## Architecture

See the canonical architecture specification:

`AI_Software_Development_Agent_Team_Architecture.md`

The development roadmap is:

`AI Software Development Agent Team — Development Roadmap.md`

Target operating model:

```text
Human
  |
  v
Next.js Dashboard / VS Code / Mobile Clients
  |
  +---- Supabase Auth
  +---- Supabase Realtime
  |
  v
Python/FastAPI Control Plane
  |
  +-- Ruata Orchestrator
  +-- Kimi
  +-- Manasseh
  +-- John
  +-- Moses
  +-- Ian
  +-- Policy / Approval / Tool Gateway
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
  |
  v
GitHub / CI
```

The local bridge is the workstation security boundary. It should not expose an unrestricted inbound server.

## Supabase security model

The public repository must contain no secrets.

Safe client-side configuration may include the project's Supabase URL and publishable/client key intended for browser or mobile use. Never commit or expose:

```text
Supabase service-role keys
Supabase secret keys
Database passwords
JWT signing secrets
LLM API keys
OAuth client secrets
Local bridge tokens
Production credentials
Mobile signing credentials
Android keystores
iOS provisioning/signing secrets
```

Privileged Supabase credentials are server-side only and must never be shipped in the Next.js browser bundle, mobile app bundle, VS Code extension, or Local Agent Bridge.

RLS is a required authorization layer for user-facing Supabase tables. Application-level authorization in the control plane does not replace database-level policy testing.

## Repository policy

This repository uses **main-only development**. All changes are committed directly to `main`. Do not create feature branches or pull requests for routine development unless this policy is explicitly changed.

Read `AGENTS.md` before making implementation changes.

## Monorepo layout

```text
apps/
  dashboard/          Next.js dashboard
  mobile/             Reserved mobile application workspace
agents/               Six agent role specifications
services/
  control_plane/      FastAPI API/control plane
  agents/             Model runtime and agent composition
  orchestrator/       Ruata planning
  persistence/        Repository/domain persistence abstraction
  identity/           User/device/workspace identity service
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
  db/                 Supabase/PostgreSQL migrations
evaluations/           Agent evaluation fixtures and runners
tests/                 Cross-service/unit/security tests
docs/                  Architecture, roadmap, API, security and operations
```

The `apps/mobile/` directory is a reserved application workspace; Moses remains framework-neutral until Kimi/architecture review selects React Native/Expo, Flutter, or native iOS/Android for a specific project.

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

For mobile development when a mobile project is present:

- Node.js/npm or the project-selected package manager
- Android SDK/ADB for Android work
- Xcode and an Apple development environment for iOS work
- Project-selected mobile toolchain such as Expo, Flutter, or native SDKs

For local development and testing:

- Docker Desktop or Docker Engine when using local infrastructure/sandbox adapters
- A Supabase project for backend integration testing when the Supabase environment is required
- Supabase CLI for migration workflows where applicable

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

## Configure environment

Copy the environment template:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

For Supabase-backed development, configure the values expected by the current application implementation. The canonical production direction is:

```dotenv
ENVIRONMENT=development
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_PUBLISHABLE_KEY=YOUR_PUBLISHABLE_KEY
SUPABASE_SECRET_KEY=YOUR_SERVER_ONLY_SECRET
MODEL_PROVIDER=openai
MODEL_NAME=your-supported-model
OPENAI_API_KEY=your-key
```

Do not commit `.env` or real credentials.

### Credential boundary

`SUPABASE_PUBLISHABLE_KEY` may be used by browser/mobile-facing code when appropriate. A Supabase secret/service credential must only be used by trusted server-side control-plane code and must never be exposed to clients.

The exact environment-variable names may evolve during the migration, but the security boundary does not.

Mobile signing credentials must use secure OS/CI secret storage and never Git.

## Supabase database workflow

The canonical production database is the project's Supabase PostgreSQL instance.

Versioned SQL migrations live under:

```text
infra/db/
supabase/migrations/
```

The migration workflow should be:

```text
1. Create/update migration
2. Apply to a clean development/staging Supabase project
3. Run schema and RLS tests
4. Review the generated database changes
5. Promote through the controlled deployment process
```

Local Docker PostgreSQL may be used for fast integration testing where it matches the required behavior, but it must not become the production source of truth.

Before modifying database/Auth/RLS behavior, read the canonical architecture and roadmap and verify which acceptance gate is affected.

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

The development-only auth path may remain available temporarily during migration for isolated tests. It must not be treated as the production authentication architecture.

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

The target dashboard authentication flow is Supabase Auth, while privileged task/agent operations continue through the control plane.

## Realtime dashboard behavior

Use Supabase Realtime selectively for live state such as:

```text
task status
agent status
approval state
device presence
execution state
```

Realtime is a delivery mechanism, not the source of truth. Durable state remains in Supabase PostgreSQL.

## Storage and artifacts

Use Supabase Storage for appropriate larger artifacts such as:

```text
reports
logs
test artifacts
screenshots
mobile build artifacts when explicitly required
other non-secret blobs
```

Store structured metadata in PostgreSQL and enforce authorization for Storage access. Do not upload `.env` files, credentials, private keys, signing material, or other secrets as general artifacts.

## Edge Functions

Supabase Edge Functions are intended for bounded operations such as:

```text
webhooks
lightweight authenticated endpoints
notification fan-out
database-adjacent automation
```

They are not the primary runtime for long-running agent execution, arbitrary terminal access, browser automation, or local workstation control. Those remain control-plane/worker or Local Agent Bridge responsibilities.

## Mobile application development

Moses is the dedicated mobile specialist.

For a mobile task, Ruata should route work according to actual requirements:

```text
Mobile-only
  → Moses
  → Ian

Mobile + Backend
  → John + Moses
  → Ian

Mobile + Web + Backend
  → John + Manasseh + Moses
  → Ian

Architecture uncertainty
  → Kimi
  → John / Manasseh / Moses as applicable
  → Ian
```

Moses may work on React Native/Expo, Flutter, native Android/Kotlin, native iOS/Swift/SwiftUI, or another approved mobile stack.

Mobile clients consume approved backend contracts and Supabase Auth/RLS-safe data access. They never contain service-role keys, database passwords, or signing secrets.

## Start local infrastructure

The repository contains optional Docker infrastructure for local development, integration tests, and sandbox support:

```bash
docker compose -f infra/docker-compose.yml up -d
```

Check containers:

```bash
docker compose -f infra/docker-compose.yml ps
```

Do not interpret local Docker PostgreSQL as the production backend.

## Run the tests

From repository root:

```bash
python -m pytest -v
```

Supabase-dependent tests should run against a dedicated test/development Supabase environment or an explicitly supported local PostgreSQL equivalent, with RLS/Auth tests included for the relevant acceptance gate.

Mobile-specific tests should include the applicable platform build, emulator/simulator, integration, accessibility, and offline/online checks.

The current suite covers the domain state machine, planning, identity foundations, approval behavior, local bridge policy controls, and Moses routing tests. The suite will expand as the Supabase migration and remaining roadmap phases are implemented.

## Run the Ruata evaluation fixture

```bash
python evaluations/runner.py
```

This currently validates deterministic routing scenarios. Model-quality evaluations will be added under:

```text
evaluations/ruata
evaluations/kimi
evaluations/john
evaluations/manasseh
evaluations/moses
evaluations/ian
evaluations/system
```

## Local Agent Bridge

The Local Agent Bridge lives under:

```text
local/bridge/
```

It runs on the developer workstation and maintains an authenticated outbound connection to the control plane.

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

Supabase Auth is the production user identity layer, but the bridge remains a separate device/workspace execution boundary.

## Device and workspace enrollment

The intended target flow is:

```text
1. User signs in with Supabase Auth.
2. User creates/selects a workspace/project.
3. Device is enrolled and associated with the authorized user/workspace.
4. Workspace path is explicitly registered.
5. VS Code extension receives non-privileged configuration.
6. Local Agent Bridge establishes outbound authenticated connection.
7. Control plane authorizes task-specific operations.
8. High-risk operations require approval.
```

Device revocation must prevent subsequent local execution until the device is re-enrolled.

## VS Code extension

From the extension directory:

```bash
cd vscode-extension
npm install
npm run compile
```

Open the extension folder in VS Code and use **Run Extension** from the Extension Development Host workflow.

Configure non-secret settings such as:

```text
ruata.controlPlaneUrl
ruata.deviceId
ruata.pythonPath
```

The extension must not contain Supabase service-role/secret credentials or other privileged backend credentials.

Then run:

```text
Ruata: Connect
```

The extension starts the local bridge for the currently opened workspace. `Ruata: Status` reports the current workspace/device/bridge state, and `Ruata: Stop Local Bridge` terminates it.

Production credential storage will use VS Code/OS secure storage where credentials are legitimately required by the extension.

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
 +-- task-123-moses
 +-- task-123-ian
```

This repository itself remains **main-only**. Agent worktree isolation applies to the development projects being operated on by the platform, not to this repository's contribution policy.

## CI

GitHub Actions is configured in:

```text
.github/workflows/ci.yml
```

CI should run Python tests, dashboard/VS Code checks, and progressively add Supabase migration/RLS/Auth and mobile integration checks as those capabilities become testable in automation.

A passing CI run must not be claimed unless the actual workflow result is verified.

## Security model

The platform follows least privilege by default:

- The cloud should not receive unrestricted filesystem access.
- Local communication is outbound and authenticated.
- Workspaces are explicitly selected and scoped.
- `.env`, credentials, secrets, private-key paths, and mobile signing secrets are blocked by default.
- Commands use `shell=False` in the local bridge.
- Agent/tool/path/risk policy is evaluated before execution.
- High/critical local actions require an approval workflow.
- Supabase RLS protects user-facing database rows.
- Supabase secret/service credentials remain server-side only.
- Mobile clients use only public/publishable configuration plus user-scoped sessions.
- Database/Auth/Storage changes are tested as security-sensitive changes.
- Agents must not weaken tests, linting, type checks, RLS, or security controls to hide failures.

See `AI_Software_Development_Agent_Team_Architecture.md` and the Moses architecture addendum for the complete operating model.

## Development sequence

The implementation follows:

`AI Software Development Agent Team — Development Roadmap.md`

Current target sequence:

```text
Supabase schema / migrations
  -> Supabase Auth
  -> profiles + workspace memberships
  -> RLS + authorization tests
  -> repository/control-plane integration
  -> durable task/run/audit/idempotency state
  -> Local Bridge authorization
  -> Realtime / Storage / Edge Functions
  -> Tools / MCP
  -> Ruata
  -> Kimi
  -> John
  -> Manasseh
  -> Moses
  -> Ian
  -> VS Code / Dashboard / Mobile
  -> Git / CI
  -> Sandboxes / Evaluations / Observability
  -> Security Hardening
  -> Production Deployment
  -> End-to-End Benchmark
```

Do not skip acceptance gates merely to expose more autonomy earlier.

## Source-of-truth rule

When implementation decisions are made, use this order:

```text
1. AI_Software_Development_Agent_Team_Architecture.md
2. AI Software Development Agent Team — Development Roadmap.md
3. Moses architecture/roadmap addenda where mobile behavior is concerned
4. AGENTS.md and repository-local instructions
5. Existing code/tests
6. Current authoritative external documentation for technologies used
```

When implementation diverges from the architecture, update the source-of-truth documents first or record an explicit architecture decision before continuing.
