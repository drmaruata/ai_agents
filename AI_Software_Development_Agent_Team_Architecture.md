# AI Software Development Agent Team — Architecture & Agent Specifications

**Version:** 3.0  
**Date:** September 6, 2026  
**Status:** Canonical architecture specification  
**Purpose:** Define a production-oriented hybrid cloud + local execution platform for a multi-agent AI software-engineering team, including agent roles, orchestration, Supabase-backed cloud services, local VS Code integration, security, isolation, observability, deployment, and controlled delivery.

> **Source of truth:** This document defines the target architecture. The Development Roadmap defines implementation order and acceptance gates. The root `README.md` provides the operational entry point. When implementation documents conflict, these three canonical documents must be reconciled before code changes continue.

---

## 1. Executive Summary

The recommended system uses five specialized agent roles under a task-driven orchestration model:

1. **Ruata** — Principal Engineering Orchestrator / Engineering Manager
2. **Kimi** — Research & Architecture Engineer
3. **Manasseh** — Frontend Engineer
4. **John** — Backend & Data Engineer
5. **Ian** — Quality, Security & Reliability Engineer

The five roles should **not** operate as five autonomous chatbots continuously conversing with one another. Instead, Ruata should manage a structured task graph, delegate bounded work to specialist agents, maintain durable task state, enforce quality gates, and require human approval for consequential actions.

The central operating principle is:

> **Ruata coordinates. Kimi decides. Manasseh and John build. Ian proves it works. The human approves consequential changes.**

The platform uses **Supabase as the managed cloud backend foundation**: PostgreSQL for durable relational state, Supabase Auth for user identity, Row Level Security (RLS) for tenant/resource authorization, Realtime for live state propagation, Storage for durable artifacts where appropriate, and Edge Functions for bounded server-side API/webhook jobs. A dedicated Python/FastAPI control plane remains responsible for orchestration, policy, agent runtime coordination, long-running work, and the secure local-bridge protocol.

The architecture deliberately separates:

```text
Identity + durable cloud state  → Supabase
Control + orchestration         → Python/FastAPI
Agent reasoning                 → provider-neutral agent runtime
Local privileged execution      → Local Agent Bridge
User-facing application         → Next.js dashboard / VS Code
Source control + CI              → GitHub / GitHub Actions
```

---

# 2. High-Level Architecture

```text
                         ┌──────────────────────┐
                         │       HUMAN          │
                         │   Product Owner      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   NEXT.JS DASHBOARD  │
                         │       / VS CODE      │
                         └──────────┬───────────┘
                                    │
                         Supabase Auth / Realtime
                                    │
                                    ▼
                   ┌────────────────────────────────┐
                   │       SUPABASE PLATFORM        │
                   │                                │
                   │ PostgreSQL                     │
                   │ Auth                           │
                   │ RLS                            │
                   │ Realtime                       │
                   │ Storage                        │
                   │ Edge Functions                 │
                   └───────────────┬────────────────┘
                                   │
                          authenticated API
                                   │
                                   ▼
                   ┌────────────────────────────────┐
                   │       PYTHON CONTROL PLANE     │
                   │                                │
                   │ Ruata Orchestrator             │
                   │ Task Engine / Queue            │
                   │ Agent Runtime                   │
                   │ Tool Gateway / Policy          │
                   │ Approval Workflow               │
                   │ Model Gateway                   │
                   │ WebSocket / Bridge Gateway      │
                   └───────────────┬────────────────┘
                                   │
                           secure outbound WSS
                                   │
                    ╔══════════════▼═══════════════╗
                    ║       LOCAL DEV NODE         ║
                    ║                              ║
                    ║ VS Code Extension            ║
                    ║ Local Agent Bridge            ║
                    ║ Workspace / Files            ║
                    ║ Terminal / Git               ║
                    ║ Browser / Playwright         ║
                    ║ Docker / local tooling      ║
                    ╚══════════════┬═══════════════╝
                                   │
                                   ▼
                               GitHub / CI
```

## 2.1 Core Design Principle

Agents communicate primarily through **structured artifacts, durable task state, events, and typed contracts**, not long free-form conversations.

Typical artifacts:

```text
task.json
research.md
architecture.md
ADR-xxx.md
implementation-plan.md
api-contract.yaml
test-plan.md
test-report.json
security-report.md
review.md
```

The source repository remains the durable engineering memory. Supabase stores runtime/application state and cloud metadata required to operate the platform.

---

# 2A. Hybrid Cloud + Local Execution Architecture

The platform is a **hybrid cloud + local execution system**.

Supabase is the managed backend foundation for identity, relational state, authorization, realtime updates, and managed object storage. The Python control plane provides orchestration and policy enforcement above that foundation. The user's computer hosts a **Local Development Node** consisting of a VS Code extension and local agent bridge.

The local node provides controlled access to the currently selected VS Code workspace, terminal, Git, browser automation, local services, and development tools. It maintains an outbound secure connection to the cloud control plane. The development computer must not be exposed directly to the public Internet merely so cloud agents can reach it.

## 2A.1 Cloud Service Responsibilities

### Supabase

Supabase should be the canonical managed backend platform for:

- user authentication and session identity
- user/profile linkage to application records
- workspace and project metadata
- task/run/execution persistence
- device registration metadata
- approvals and audit records
- row-level authorization using PostgreSQL RLS
- realtime delivery of approved application state changes
- artifact/object storage where database rows are insufficient
- bounded Edge Functions for webhooks, lightweight server-side endpoints, and database-adjacent automation

### Python/FastAPI control plane

The control plane should own:

- Ruata orchestration
- task decomposition and dependency execution
- specialist-agent lifecycle
- model/provider routing
- policy evaluation
- tool authorization
- approval enforcement
- bridge session management
- long-running/background work
- agent runtime execution
- structured event emission
- integrations that require stateful workers or long-lived connections

Supabase is therefore **not** a replacement for the control-plane architecture. It is the managed persistence/auth/realtime backend on which the control plane is built.

## 2A.2 Separation of Responsibilities

### Supabase / managed cloud backend

The Supabase layer should own:

- authentication identity
- session/token issuance and refresh
- application relational data
- durable task and run state
- workspace/project membership data
- RLS enforcement for user-facing data access
- realtime application-state changes
- durable artifact storage metadata and selected blobs
- database functions/triggers where appropriate
- bounded Edge Functions

### Cloud control plane

The Python control plane should own:

- agent orchestration
- task scheduling and execution loops
- model invocation
- policy decisions that require contextual task/agent state
- tool gateway
- bridge gateway
- approval orchestration
- correlation IDs and execution context
- long-running workers
- reconciliation between local nodes and cloud state

### Local development node

The local node should own:

- filesystem access
- VS Code workspace access
- local terminal execution
- Git worktrees
- local development servers
- local databases where applicable
- Docker/local containers
- browser automation
- editor diagnostics
- selected project credentials that must remain local
- enforcement of local execution policy

The cloud control plane should issue **structured requests**, not unrestricted shell instructions. The local bridge decides whether an operation is permitted before execution.

## 2A.3 Why Supabase Is the Canonical Backend Foundation

The platform needs durable relational state, authentication, resource authorization, live updates, and managed storage. Supabase provides these capabilities while retaining standard PostgreSQL semantics.

The design goals are:

1. **Managed persistence:** avoid making self-managed PostgreSQL infrastructure a prerequisite for the production control plane.
2. **Integrated identity:** use Supabase Auth rather than maintaining a parallel production identity issuer.
3. **Database-enforced authorization:** use RLS so authorization does not depend solely on API code paths.
4. **Realtime UI state:** use Supabase Realtime for dashboard-facing state updates where appropriate.
5. **Managed object storage:** use Supabase Storage for larger artifacts that should not live in relational rows.
6. **Operational simplicity:** keep deployment responsibilities focused on the Python control plane, frontend, local bridge, and agent workers.

Self-hosted PostgreSQL remains an optional local/testing configuration, not the canonical production backend.

## 2A.4 Supabase Service Map

```text
Supabase
├── Auth
│   ├── sign-in / sign-out
│   ├── session management
│   └── identity claims
│
├── PostgreSQL
│   ├── profiles
│   ├── workspace_members
│   ├── projects
│   ├── devices
│   ├── workspaces
│   ├── agents
│   ├── tasks
│   ├── task_dependencies
│   ├── task_runs
│   ├── executions
│   ├── approvals
│   ├── artifacts
│   ├── audit_events
│   ├── task_state_history
│   ├── idempotency_keys
│   └── other runtime metadata
│
├── RLS
│   ├── tenant/workspace isolation
│   ├── user ownership checks
│   ├── role-based access
│   └── privileged server-only paths
│
├── Realtime
│   ├── task updates
│   ├── agent status
│   ├── approvals
│   ├── device presence
│   └── execution events where useful
│
├── Storage
│   ├── reports
│   ├── logs
│   ├── generated artifacts
│   └── larger binary objects
│
└── Edge Functions
    ├── webhooks
    ├── lightweight APIs
    ├── bounded automation
    └── database-adjacent functions
```

Not every table must be exposed directly to browser clients. Sensitive state should remain behind the Python control plane or server-side functions even when stored in Supabase.

## 2A.5 Authentication and Identity Model

Supabase Auth is the canonical production identity provider.

```text
User
  ↓
Supabase Auth
  ↓
JWT / session
  ↓
Next.js / API client
  ↓
Authenticated control-plane request
  ↓
RLS + application authorization
```

Application tables should use stable references to the Supabase Auth user identity. A `profiles` table may hold application-specific attributes while the actual authentication identity remains owned by Supabase Auth.

The development JWT endpoint may exist only as a local testing compatibility mechanism during migration. It is not the production identity model.

Never expose Supabase secret/service-role credentials to browser code, VS Code client code, or the Local Agent Bridge. Privileged Supabase credentials may be used only in trusted server-side processes that require them and must remain in deployment secrets.

## 2A.6 Authorization and RLS Model

RLS is a first-class security layer.

The intended hierarchy is:

```text
auth.users
   │
   ▼
profiles
   │
   ▼
workspace_members
   │
   ▼
workspaces
   │
   ├── projects
   ├── devices
   ├── tasks
   ├── approvals
   ├── artifacts
   └── audit events
```

Policies should enforce at least:

- a user may access only workspaces to which they belong
- project/task visibility must respect workspace membership
- roles must restrict read/write/approval capabilities
- sensitive system records must not be writable directly by untrusted clients
- service-side privileged operations must be separated from browser-facing access

RLS must be tested directly, not merely assumed from application code.

## 2A.7 Database Authority and Repository Boundary

The application should retain a repository/service abstraction so business logic does not become coupled to Supabase client details.

Preferred logical structure:

```text
Application services
        ↓
Repository / domain services
        ↓
Supabase PostgreSQL
```

A lightweight in-memory repository remains useful for deterministic unit tests. Direct PostgreSQL access can remain available for integration tests and local development, but the canonical production database is Supabase PostgreSQL.

Migrations should be maintained as versioned SQL under `infra/db/` and applied to the Supabase database through the project's database deployment workflow.

## 2A.8 Realtime Model

Use Realtime selectively for state that benefits from live dashboard updates.

Typical channels/events:

```text
task status changed
agent status changed
approval requested/granted/rejected
device connected/disconnected
execution started/completed/failed
```

Realtime should not replace durable writes or the event/audit model. The database remains authoritative; realtime is a delivery mechanism for clients.

## 2A.9 Storage Model

Use relational rows for structured metadata and Supabase Storage for larger blobs.

```text
Database
  artifact_id
  task_id
  type
  checksum
  metadata
  storage_path

Supabase Storage
  reports/...
  logs/...
  test-artifacts/...
```

Storage access must follow workspace/project authorization and should use short-lived signed access where appropriate. Secret-bearing files should remain on the local node or approved secret-management infrastructure rather than being copied into general artifact storage.

## 2A.10 Edge Function Boundaries

Edge Functions are appropriate for bounded operations such as:

- authenticated webhooks
- lightweight API transformations
- webhook ingestion
- simple notification fan-out
- narrow database-adjacent operations

Do **not** use Edge Functions as the primary runtime for:

- long-running agent loops
- arbitrary terminal execution
- local filesystem access
- browser automation
- large model workflows
- long-lived orchestration workers
- privileged workstation control

Those remain responsibilities of trusted control-plane/worker infrastructure.

## 2A.11 Reference Topology

```text
                                INTERNET
                                   │
               ┌───────────────────┴──────────────────┐
               │                                      │
               ▼                                      ▼
     ┌──────────────────────┐              ┌──────────────────────┐
     │   Next.js Dashboard  │              │    VS Code Client    │
     └──────────┬───────────┘              └──────────┬───────────┘
                │                                     │
                └───────────────┬─────────────────────┘
                                │
                         Supabase Auth
                         / Realtime APIs
                                │
                                ▼
                  ┌──────────────────────────────┐
                  │       SUPABASE CLOUD         │
                  │ PostgreSQL · Auth · RLS      │
                  │ Realtime · Storage · Edge    │
                  └──────────────┬───────────────┘
                                 │
                       authenticated server access
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │     PYTHON CONTROL PLANE     │
                  │ Ruata · Agents · Policy      │
                  │ Tools · Approvals · Workers  │
                  └──────────────┬───────────────┘
                                 │
                           outbound WSS
                                 │
                  ╔══════════════▼═══════════════╗
                  ║       LOCAL DEV NODE         ║
                  ║ VS Code · Files · Git        ║
                  ║ Terminal · Browser · Docker  ║
                  ╚══════════════┬═══════════════╝
                                 │
                                 ▼
                              GitHub / CI
```

## 2A.12 Outbound-Only Connection Pattern

Preferred network model:

```text
Local Dev Node
      │
      │ outbound TLS/WebSocket
      ▼
Cloud Bridge Gateway
      │
      ▼
Python Control Plane
      │
      ▼
Supabase / cloud services
```

Avoid requiring inbound Internet connectivity to the developer machine.

The connection should use:

- TLS
- device identity
- short-lived credentials where practical
- connection renewal
- message authentication
- replay protection
- request IDs / correlation IDs
- explicit session state

## 2A.13 Device Registration

Each development computer should be registered as a device in the platform database.

Example:

```text
Device: Maruata-PC
Device ID: RUA-PC-01
OS: Windows
VS Code: Connected
Status: Online
Projects: 3
```

The dashboard should support:

```text
Devices
├── Maruata-PC        Online
├── Laptop            Offline
└── Cloud Sandbox     Available
```

A project should be mapped explicitly to a device and workspace:

```text
Project: MizoramStay
        ↓
Device: Maruata-PC
        ↓
Workspace: C:\Projects\MizoramStay
```

## 2A.14 Workspace Registration

Do not grant all-agent access to an entire user profile.

Projects should be explicitly registered with:

- project ID
- local path
- Git remote
- default branch
- environment profile
- allowed agents
- allowed tools
- allowed commands
- protected files/directories
- approval policy

## 2A.15 Local Policy Example

```yaml
project: MizoramStay

allowed_paths:
  - ./app
  - ./src
  - ./components
  - ./lib
  - ./supabase
  - ./tests

blocked_paths:
  - .env
  - .env.local
  - credentials/
  - secrets/

allowed_commands:
  - git
  - npm
  - pnpm
  - npx
  - supabase
  - playwright

restricted_commands:
  - rm
  - rmdir
  - format
  - shutdown

require_approval:
  - production-deploy
  - production-migration
  - secret-change
  - destructive-database-operation
```

The precise allowlist/denylist strategy should be adapted to the operating system and project tooling. Path and capability restrictions must be enforced by the local bridge, not only described in prompts.

## 2A.16 Cloud Execution Mode

The platform should support a second execution path for tasks that do not need the user's workstation.

```text
                   Ruata
                     │
            ┌────────┴────────┐
            │                 │
            ▼                 ▼
       LOCAL NODE         CLOUD SANDBOX
            │                 │
         VS Code           Isolated VM
            │                 │
            └────────┬────────┘
                     ▼
                   GitHub
```

Typical local tasks:

- modify an uncommitted local project
- debug a local service
- inspect the currently open VS Code workspace
- use a local database
- reproduce a workstation-specific problem

Typical cloud tasks:

- long-running isolated builds
- large automated test suites
- PR-oriented implementation from a clean branch
- parallel experiments
- evaluation benchmarks
- tasks that should not touch the user's workstation

Cloud sandbox state may use the same Supabase database for metadata, but sandbox execution remains isolated from the primary control-plane process.

## 2A.17 Dashboard Architecture

The dashboard should contain at least these views:

```text
Dashboard
Projects
Agents
Tasks
Runs
Workspaces / Devices
Memory
Research
Architecture Decisions
Approvals
Logs
Evaluations
Settings
```

Dashboard data should use Supabase Auth for identity, the control plane for privileged operations, and Realtime for selected live state updates.

## 2A.18 Event Model

Use an event-driven model for state changes.

Typical events:

```text
project.created
project.updated
agent.started
agent.paused
agent.completed
agent.failed
task.created
task.assigned
task.blocked
task.completed
tool.requested
tool.approved
tool.denied
workspace.connected
workspace.disconnected
test.started
test.failed
test.passed
approval.requested
approval.granted
approval.rejected
git.branch.created
git.pr.created
deployment.requested
deployment.completed
```

Every event should include a correlation ID so the full history of a task can be reconstructed. Durable audit events belong in Supabase PostgreSQL; Realtime is used for delivery to interested clients.

## 2A.19 Request/Response Contract Between Cloud and Local Node

Use structured messages rather than raw shell strings where possible.

Example request:

```json
{
  "request_id": "req_8432_001",
  "task_id": "TASK-8432",
  "device_id": "RUA-PC-01",
  "workspace_id": "ws_mizoramstay",
  "agent": "john",
  "operation": "run_command",
  "arguments": {
    "command": "npm",
    "args": ["test", "--", "--runInBand"]
  },
  "risk": "low"
}
```

Example response:

```json
{
  "request_id": "req_8432_001",
  "status": "completed",
  "exit_code": 0,
  "stdout_ref": "artifact://logs/8432-test.stdout",
  "stderr_ref": "artifact://logs/8432-test.stderr",
  "duration_ms": 48211
}
```

For file edits, prefer structured patches or edit operations over arbitrary text replacement where feasible.

## 2A.20 Execution Permissions by Agent

| Capability | Ruata | Kimi | Manasseh | John | Ian |
|---|---:|---:|---:|---:|---:|
| Read repository | Yes | Yes | Yes | Yes | Yes |
| Edit frontend | Limited | No | Yes | No | Tests only |
| Edit backend | Limited | No | No | Yes | Tests only |
| Edit database / Supabase | No | No | No | Yes | Verify |
| Run terminal | Controlled | Safe/read-heavy | Yes | Yes | Yes |
| Browser | As needed | Research | Yes | As needed | Yes |
| Git branch | Yes | Read/create research branches | Yes | Yes | Yes |
| Merge | Controlled | No | No | No | Recommend |
| Production deploy | Approval only | No | No | No | Verify |
| Secrets access | Brokered/minimal | No | No | Minimal | No |
| Security scans | Trigger | Analyze | Limited | Limited | Yes |

Permissions should be dynamically reduced further for high-risk projects or sensitive workspaces.

## 2A.21 Tool Gateway

The platform should place a policy-aware gateway between agents and tools.

```text
Agent
  ↓
Tool Request
  ↓
Policy Engine
  ├── identity
  ├── task scope
  ├── workspace scope
  ├── risk level
  ├── command/path policy
  └── approval requirement
  ↓
Tool Adapter / MCP
  ↓
Execution
```

This prevents the agent prompt from being the only security boundary.

## 2A.22 MCP and Tool Integration

Use MCP where it provides a clean standardized interface to external systems such as:

```text
GitHub
Supabase / PostgreSQL
Browser
Documentation
Issue Tracker
CI/CD
Observability
Cloud Infrastructure
```

Keep local, high-trust operations behind the local bridge and policy engine even when an MCP-compatible interface is used.

## 2A.23 Repository State Strategy

The platform should understand at least four Git states:

```text
CLEAN
UNCOMMITTED
IN_PROGRESS_BRANCH
PULL_REQUEST
```

Before an agent starts writing, Ruata should inspect:

- current branch
- uncommitted changes
- staged changes
- upstream divergence
- active worktree
- active agents using the same workspace

An agent should not silently overwrite unrelated user work.

## 2A.24 Agent Session Lifecycle

Each agent run should have a lifecycle:

```text
CREATED
  ↓
ASSIGNED
  ↓
CONTEXT_LOADING
  ↓
READY
  ↓
EXECUTING
  ├── WAITING_TOOL
  ├── WAITING_APPROVAL
  └── PAUSED
  ↓
VALIDATING
  ↓
SUCCEEDED / FAILED / CANCELLED
  ↓
ARTIFACTS_SAVED
```

Session state and durable run metadata should be persisted in Supabase.

## 2A.25 Failure Handling

The platform should distinguish:

```text
TRANSIENT
- network interruption
- temporary provider error
- rate limit

TOOL
- invalid command
- missing dependency
- permission denied

TASK
- implementation error
- failed test
- architectural mismatch

POLICY
- operation denied
- approval unavailable

SYSTEM
- node disconnected
- corrupted state
```

Only retry failures that are safe and likely to succeed on retry. Do not blindly repeat destructive operations.

## 2A.26 Local Node Offline Behavior

If the local node disconnects:

```text
Cloud detects disconnect
        ↓
Pause local execution tasks
        ↓
Persist task/run state
        ↓
Wait for reconnect
        ↓
Reconcile node state
        ↓
Resume only after state validation
```

Tasks that do not depend on the local node may continue in the cloud.

## 2A.27 Security Boundary

The local node is a privileged boundary because it can execute commands on the user's computer.

Minimum requirements:

- explicit device registration
- authenticated cloud connection
- least-privilege execution
- workspace allowlists
- protected file handling
- environment-variable filtering
- secret isolation
- command/path controls
- approval gates
- audit logging
- task-scoped permissions
- cancellation/kill controls
- local emergency disconnect

The user should have a local **Stop All Agents** control independent of the cloud dashboard.

Supabase credentials must also follow least privilege. Browser clients use only publishable/client credentials appropriate to their role. Secret/service credentials remain server-side.

## 2A.28 Emergency Controls

The local node should expose:

```text
[ STOP ALL AGENTS ]
[ DISCONNECT FROM CLOUD ]
[ REVOKE DEVICE ]
```

The Stop action should terminate active agent-controlled processes according to a safe escalation procedure and prevent new execution until explicitly re-enabled.

## 2A.29 Observability for Local Execution

For every local operation record:

```text
request ID
agent
user
project
workspace
device
task
operation
command / tool
approval state
start time
end time
exit status
files changed
artifact references
error information
```

Never capture secret values in logs.

## 2A.30 Recommended Technology Topology

```text
Dashboard
→ Next.js / TypeScript
→ Supabase Auth client
→ Supabase Realtime where appropriate

Cloud Control Plane
→ Python / FastAPI
→ Supabase server-side database access
→ Long-running worker processes

Agent Runtime
→ OpenAI Agents SDK or equivalent provider-neutral runtime

Database
→ Supabase PostgreSQL
→ SQL migrations under infra/db/

Authentication
→ Supabase Auth

Authorization
→ PostgreSQL RLS + application-level policy checks

Realtime
→ Supabase Realtime + control-plane events

Artifacts
→ Supabase Storage where appropriate

Serverless APIs
→ Supabase Edge Functions for bounded operations

Task Queue
→ Managed queue / Redis only where required by workload

Local Node
→ Python or Node.js service

VS Code Extension
→ TypeScript

Browser Automation
→ Playwright

Source Control
→ Git + GitHub

CI/CD
→ GitHub Actions
```

Supabase is the canonical backend foundation. Other infrastructure components are introduced only where the workload requires capabilities not provided directly by Supabase.

## 2A.31 Recommended Hosting Model

A practical initial deployment could be:

```text
Vercel
├── Dashboard / Next.js

Supabase
├── Auth
├── PostgreSQL
├── RLS
├── Realtime
├── Storage
└── Edge Functions

Managed Compute
├── Python/FastAPI control plane
├── Agent workers
├── Background jobs
└── WebSocket / bridge gateway

Developer PC
└── Local Development Node

GitHub
├── Source control
└── GitHub Actions CI/CD
```

The exact compute provider can change without changing the logical architecture. Supabase remains the canonical managed backend unless a later architecture decision explicitly replaces it.

## 2A.32 Multi-Device Future State

The architecture should support multiple execution nodes from the beginning:

```text
                        RUATA CLOUD
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
          Desktop         Laptop       Cloud Sandbox
              │              │              │
            VS Code        VS Code        Isolated VM
              │              │              │
          Projects       Projects       Git branches
```

Supabase stores device/workspace metadata and presence-related application state; the control plane routes execution according to:

- project location
- required tools
- available hardware
- connectivity
- sensitivity
- workload duration
- resource availability

## 2A.33 Human Control Model

The dashboard should make the human role explicit rather than hiding it.

Recommended controls:

```text
START
PAUSE
STOP
APPROVE
REJECT
RETRY
OPEN VS CODE
OPEN PR
VIEW DIFF
VIEW TESTS
VIEW LOGS
```

High-risk operations should surface a concise approval request.

## 2A.34 Platform-Level Data Model

A minimal production relational model should include:

```text
auth.users                   ← Supabase Auth authority
profiles
workspace_members
projects
devices
workspaces
agents
agent_versions
agent_runs
tasks
task_dependencies
executions
tool_requests
artifacts
approvals
events / audit_events
policy_rules
evaluations
model_usage
idempotency_keys
task_state_history
```

Important relationships:

```text
Auth User → Profile
Profile → Workspace Memberships
Workspace → Projects
Workspace → Devices
Workspace → Tasks
Project → Workspaces
Project → Tasks
Task → Task Dependencies
Task → Agent Runs
Agent Run → Tool Requests
Task → Artifacts
Task → Approvals
Everything important → Audit Events
```

RLS policies must follow the ownership/membership graph and prevent direct browser access to privileged records.

## 2A.35 Build Strategy

Do not start with five fully autonomous agents plus a dashboard plus cloud execution plus production deployment at once.

The backend foundation should now be established in this order:

```text
1. Supabase project and environments
2. Auth and application identity model
3. Core PostgreSQL schema / migrations
4. RLS policies and authorization tests
5. Repository/service integration
6. Realtime state propagation
7. Storage integration
8. Bounded Edge Functions
9. Python control-plane integration
10. Local Development Node
11. Agent orchestration and tools
12. Cloud sandbox execution
```

This makes the backend contract stable before increased agent autonomy is introduced.

# 3. Agent Fleet

| Agent | Role | Primary Mission |
|---|---|---|
| **Ruata** | Principal Engineering Orchestrator | Understand requirements, plan, delegate, coordinate, enforce gates, integrate results, control risk |
| **Kimi** | Research & Architecture Engineer | Research technology and architecture questions, inspect existing systems, make technical recommendations and decisions |
| **Manasseh** | Frontend Engineer | Build and maintain frontend UI, state, interactions, accessibility, and frontend tests |
| **John** | Backend & Data Engineer | Build APIs, Supabase/PostgreSQL data layer, business logic, authentication/authorization integration, backend tests, and data security |
| **Ian** | Quality, Security & Reliability Engineer | Verify correctness, security, regression safety, performance, integration behavior, and release readiness |

---

# 4. Ruata — Principal Engineering Orchestrator

## 4.1 Mission

Ruata is the system's control-plane agent. Ruata should coordinate the team rather than acting as the main code writer.

## 4.2 Primary Responsibilities

- Understand user requirements.
- Convert requests into clear engineering objectives.
- Inspect the repository and existing architecture.
- Identify affected modules and dependencies.
- Decide whether research is required.
- Delegate research to Kimi when necessary.
- Construct a task graph and dependency graph.
- Assign frontend tasks to Manasseh.
- Assign backend/data tasks to John.
- Assign validation and security work to Ian.
- Allow independent work to run in parallel.
- Track task status.
- Resolve conflicts among agent outputs.
- Enforce repository, Supabase, security, and project policies.
- Prevent agents from modifying unrelated areas.
- Trigger retries or repair loops after failures.
- Decide when human approval is required.
- Produce an implementation summary and completion report.

## 4.3 What Ruata Should Usually NOT Do

- Write large amounts of production code.
- Re-run research that Kimi has already completed without a reason.
- Perform detailed frontend implementation.
- Perform detailed backend implementation.
- Mark work complete merely because an agent claims it is complete.
- Merge high-risk changes without required approval.
- Bypass RLS or authentication controls.

## 4.4 Task Graph Example

```text
FEATURE-142
│
├── TASK-142.1 Requirements analysis
│       └── Kimi
│
├── TASK-142.2 Supabase database changes
│       └── John
│
├── TASK-142.3 API implementation
│       └── John
│
├── TASK-142.4 UI implementation
│       └── Manasseh
│
├── TASK-142.5 Frontend tests
│       └── Manasseh
│
├── TASK-142.6 Backend / RLS tests
│       └── John
│
└── TASK-142.7 Integration/security review
        └── Ian
```

## 4.5 Ruata State Machine

```text
BACKLOG
   ↓
ANALYZING
   ↓
RESEARCH_REQUIRED?
   ├── YES → RESEARCH
   └── NO
          ↓
PLANNED
   ↓
IMPLEMENTING
   ↓
VALIDATING
   ↓
FAILED?
 ┌─YES────────────┐
 │                │
 ▼                │
REPAIR ───────────┘
 │
 ▼
VALIDATING
 │
 ▼
REVIEW
 │
 ▼
HUMAN_APPROVAL
 │
 ▼
MERGED
 │
 ▼
DONE
```

## 4.6 Delegation Rules

Ruata should route work according to the task's actual needs, not force all five agents into every workflow.

### Simple frontend change

```text
Ruata → Manasseh → validation
```

### Supabase authentication feature

```text
Ruata
  ↓
Kimi
  ↓
John ─────────┐
              ├──→ Ian
Manasseh ─────┘
```

### Intermittent checkout failure

```text
Ruata → Kimi → John → Ian
```

## 4.7 Ruata Outputs

Every significant task should produce:

- task specification
- delegation plan
- dependency graph
- current task state
- risk assessment
- completion criteria
- final implementation summary
- validation summary
- unresolved issues

---

# 5. Kimi — Research & Architecture Engineer

## 5.1 Mission

Kimi is responsible for technical research, architecture analysis, technology evaluation, technical decision-making, and implementation specifications.

Kimi should not be treated as a generic research chatbot.

## 5.2 Primary Responsibilities

- Research technologies and libraries.
- Verify current APIs and documentation.
- Inspect existing application architecture.
- Identify compatibility constraints.
- Evaluate competing technical approaches.
- Analyze security implications.
- Analyze scalability and performance implications.
- Analyze migration risks.
- Define implementation boundaries.
- Produce technical specifications.
- Produce Architecture Decision Records (ADRs).
- Define API contracts where architecture requires it.
- Identify assumptions and unresolved questions.
- Verify current Supabase APIs, Auth behavior, RLS semantics, Realtime behavior, Storage behavior, and deployment considerations when relevant.

## 5.3 Research Outputs

A typical research package:

```text
.ai/research/feature-142/
    research.md
    architecture.md
    decisions.md
    api-contract.md
    references.md
```

## 5.4 Engineering Decision Record

```text
Decision:
Use X instead of Y.

Context:
...

Why:
...

Alternatives considered:
...

Trade-offs:
...

Security implications:
...

Performance implications:
...

Implementation constraints:
...

Migration considerations:
...
```

## 5.5 Kimi Should Answer Questions Such As

- Which library or service is appropriate?
- Is the existing architecture suitable for the requested feature?
- Does an existing component/service already solve the problem?
- What is the recommended Supabase/PostgreSQL database design?
- What should the frontend/backend contract look like?
- Which APIs are current or deprecated?
- What are the security implications?
- What will be the likely performance bottlenecks?
- What changes can be made without breaking compatibility?

## 5.6 Kimi Should NOT

- Implement unrelated production code.
- Make undocumented architectural decisions.
- Force a preferred technology without evaluating alternatives.
- Duplicate research already captured in project memory.
- Replace automated verification with research claims.

---

# 6. Manasseh — Frontend Engineer

## 6.1 Mission

Manasseh owns the frontend implementation and user-facing application behavior.

## 6.2 Primary Responsibilities

- UI implementation.
- Responsive design.
- Design-system integration.
- React/Next.js or equivalent frontend development.
- Component development.
- Client-side state management.
- Forms and validation.
- Supabase Auth client integration where appropriate.
- Supabase Realtime subscriptions where appropriate.
- API/control-plane consumption.
- Loading states.
- Empty states.
- Error states.
- Optimistic updates where justified.
- Accessibility.
- Cross-browser behavior.
- Frontend performance.
- Frontend unit/integration tests.
- End-to-end flows where appropriate.

## 6.3 Frontend Ownership Boundary

Manasseh should own frontend concerns but should not invent backend behavior independently.

Preferred flow:

```text
Kimi
  ↓
API / Architecture Contract
  ↓
John
  ↓
Backend + Supabase implementation
  ↓
Manasseh
  ↓
Frontend integration
```

## 6.4 Manasseh Deliverables

For a feature, expect:

- components
- pages/routes
- hooks
- state changes
- frontend validation
- API integration
- accessibility behavior
- responsive behavior
- frontend tests
- screenshots or visual validation when appropriate
- implementation notes for non-obvious choices

## 6.5 Frontend Quality Checklist

```text
[ ] Reuses existing components where appropriate
[ ] Responsive behavior verified
[ ] Loading state implemented
[ ] Empty state implemented
[ ] Error state implemented
[ ] Accessibility considered
[ ] Keyboard behavior verified
[ ] Form validation implemented
[ ] API error handling implemented
[ ] Supabase session behavior verified where applicable
[ ] Types are correct
[ ] Lint passes
[ ] Tests pass
[ ] No unrelated files changed
```

---

# 7. John — Backend & Data Engineer

## 7.1 Mission

John owns backend services, APIs, Supabase/PostgreSQL data design, authentication/authorization integration, business logic, integrations, and backend testing.

## 7.2 Primary Responsibilities

- API implementation.
- Database schema design.
- PostgreSQL/Supabase changes.
- SQL migrations.
- Row Level Security (RLS).
- Supabase Auth integration.
- Authorization.
- Business logic.
- Server-side validation.
- External integrations.
- Background jobs.
- Caching.
- Rate limiting.
- Error handling.
- Logging and observability.
- Transaction design.
- Backend tests.

## 7.3 API Contract

The backend should maintain a machine-readable contract where practical:

```text
/openapi
    openapi.yaml
```

or an equivalent typed contract.

The goal is to prevent frontend/backend divergence.

## 7.4 Backend Security Responsibilities

John must explicitly check:

- authentication boundaries
- authorization rules
- RLS policies
- data exposure
- input validation
- SQL injection risks
- privilege escalation
- service-role credential handling
- rate limiting
- tenant/workspace isolation
- transaction correctness
- sensitive logging

## 7.5 Supabase Change Requirements

Database/backend changes should normally include:

```text
[ ] Migration created under infra/db/
[ ] Migration ordering verified
[ ] Existing data considered
[ ] Constraints verified
[ ] Indexing considered
[ ] RLS policies created/updated
[ ] Authorization verified
[ ] Service-role access minimized
[ ] Performance implications considered
[ ] Integration tests updated
[ ] Rollout / rollback implications documented
```

## 7.6 John Should NOT

- Silently change frontend requirements.
- Bypass authorization to make tests pass.
- Disable RLS simply to solve implementation problems.
- Commit service-role keys or other Supabase secrets.
- Modify production data without required approvals.
- Add dependencies without evaluating them.

---

# 8. Ian — Quality, Security & Reliability Engineer

## 8.1 Mission

Ian is the system's verification and quality gate. Ian should not only run tests after implementation; Ian should continuously verify correctness, security, regression safety, and release readiness.

## 8.2 Primary Responsibilities

- Test planning.
- Unit testing.
- Integration testing.
- End-to-end testing.
- Regression testing.
- Static analysis.
- Type checking.
- Linting.
- Build verification.
- Security testing.
- Dependency checks.
- Secret scanning.
- RLS/security-policy testing.
- Performance checks.
- Reliability checks.
- Code review.
- Release validation.

## 8.3 Validation Layers

### Level 1 — Static Validation

```text
TypeScript / type checking
ESLint
Formatter checks
Build
Dependency auditing
Secret scanning
```

### Level 2 — Unit Tests

```text
Frontend
Backend
Utilities
Business logic
Database functions
```

### Level 3 — Integration Tests

```text
Frontend → API
API → Supabase PostgreSQL
Authentication → API
RLS → authenticated user roles
External service → Application
```

### Level 4 — End-to-End Tests

Example:

```text
Login
  ↓
Create booking
  ↓
Payment
  ↓
Confirmation
```

### Level 5 — Security Testing

Check for relevant classes of vulnerabilities such as:

```text
Broken access control
Authentication bypass
Authorization errors
IDOR
XSS
CSRF
SQL injection
Secrets leakage
Unsafe dependencies
API abuse
Data exposure
Incorrect RLS policies
Service-role credential exposure
```

### Level 6 — Regression Testing

```text
New change
   ↓
New tests
   ↓
Existing tests
   ↓
Regression suite
```

## 8.4 Ian Decision Model

Ian should provide explicit status:

```text
PASS
PASS_WITH_WARNINGS
FAIL
BLOCKED
```

A task should not be marked complete solely because code exists.

## 8.5 Ian Outputs

```text
.ai/tasks/TASK-142/
    test-plan.md
    test-report.json
    security-report.md
    regression-report.md
    review.md
```

## 8.6 Ian Should NOT

- Remove failing tests to obtain a green build.
- Disable lint/type checking to conceal errors.
- Accept “works on my machine” as proof.
- Treat a passing unit test as proof that production behavior is correct.
- Approve unresolved critical security findings.

---

# 9. Shared Engineering Rules

Create a project-level `AGENTS.md` and, where appropriate, localized instruction files.

Recommended structure:

```text
AGENTS.md
frontend/AGENTS.md
backend/AGENTS.md
database/AGENTS.md
tests/AGENTS.md
```

## 9.1 Example `AGENTS.md`

```text
# Project Engineering Rules

## General
- Never modify unrelated files.
- Never remove tests merely to make them pass.
- Never disable linting or type checking.
- Never commit secrets.
- Preserve existing API compatibility unless explicitly approved.
- Treat Supabase Auth, RLS, and production data changes as security-sensitive.

## Before coding
1. Inspect repository instructions.
2. Inspect the existing implementation.
3. Determine the smallest appropriate change.
4. Create an implementation plan for non-trivial work.
5. Verify whether Supabase schema, RLS, Auth, Realtime, Storage, or Edge Functions are affected.

## After coding
1. Run formatter.
2. Run lint.
3. Run type checking.
4. Run unit tests.
5. Run integration tests where applicable.
6. Run RLS/auth tests where applicable.
7. Run end-to-end tests where applicable.
8. Review the git diff.
9. Report failures explicitly.
```

---

# 10. Shared Project Memory

Do not rely entirely on model memory. Store persistent engineering knowledge in the repository.

Recommended structure:

```text
.ai/
├── project.md
├── architecture.md
├── conventions.md
├── decisions/
├── standards/
├── workflows/
├── known-issues/
├── research/
└── task-state/
```

Example:

```text
.ai/
    project.md
    architecture.md
    conventions.md

    decisions/
        ADR-001-database.md
        ADR-002-authentication.md
        ADR-003-supabase-platform.md

    research/
        supabase-auth.md
        supabase-rls.md
        supabase-storage.md
        payments.md

    task-state/
        TASK-142.json
```

This memory layer should contain durable facts and decisions rather than long conversational transcripts.

---

# 11. Agent Communication Model

Prefer structured handoffs:

```text
Ruata
  ↓
Task Specification
  ↓
Kimi
  ↓
Architecture / Decision
  ↓
John + Manasseh
  ↓
Implementation
  ↓
Ian
  ↓
Validation Report
  ↓
Ruata
```

## 11.1 Recommended Artifact Types

```text
task.json
research.md
architecture.md
ADR-xxx.md
implementation-plan.md
api-contract.yaml
test-plan.md
test-report.json
security-report.md
review.md
```

Each artifact should have an owner, timestamp/version, task ID, and status where practical.

---

# 12. Git and Workspace Isolation

Agents should not freely modify the same working tree without controls.

Preferred approach:

```text
main
 │
 ├── feature/142-booking-api
 ├── feature/142-booking-ui
 └── feature/142-tests
```

For stronger isolation, use worktrees or equivalent sandboxed workspaces.

Each agent should receive:

- a bounded workspace
- a defined objective
- allowed files or directories when practical
- a test command
- a completion criterion
- explicit restrictions

---

# 13. Tool Layer

Agents should receive tools based on their role rather than identical unrestricted access.

Recommended shared capabilities:

```text
GitHub
Filesystem
Terminal / shell
Supabase / PostgreSQL
Browser
Documentation/search
Testing
CI/CD
Observability
Task tracker
```

A modern MCP-oriented tool layer can expose these capabilities consistently.

## 13.1 Ruata Tools

```text
GitHub
Task queue
Agent status
Filesystem metadata
Test reports
Project memory
CI status
Supabase task/project metadata
```

## 13.2 Kimi Tools

```text
Web / documentation
GitHub
Repository inspection
Package metadata
Research sources
Architecture artifacts
Supabase documentation
```

## 13.3 Manasseh Tools

```text
Filesystem
GitHub
Terminal
Browser
Playwright / browser automation
Visual inspection
Frontend test tools
Supabase client integration as permitted by frontend contracts
```

## 13.4 John Tools

```text
Filesystem
GitHub
Terminal
Supabase / PostgreSQL
Supabase CLI
API tooling
Backend test tools
Logs
RLS/auth test tooling
```

## 13.5 Ian Tools

```text
GitHub
Terminal
Test runners
Playwright
Security scanners
Dependency audit
CI
Logs
Performance tooling
Supabase/RLS/auth verification tooling
```

---

# 14. Autonomy Levels

Use three practical autonomy levels.

## Level 1 — Read / Analyze

Agent can:

```text
inspect files
search repository
research
analyze
run safe read-only commands
inspect approved Supabase metadata
```

## Level 2 — Write / Implement

Agent can:

```text
modify code
write tests
create branches
create migrations
update artifacts
implement approved Supabase schema/RLS changes
```

## Level 3 — Execute / Deploy

Agent can:

```text
merge
run production operations
deploy
modify production data
change infrastructure
use highly privileged credentials
```

Level 3 should normally require explicit human approval for consequential operations.

---

# 15. Risk-Based Approval Policy

## Low Risk

Automate where practical:

- formatting
- documentation
- small UI changes
- tests
- non-functional refactors
- local development database changes in isolated environments

## Medium Risk

Require stronger review:

- database schema changes
- RLS changes
- authentication changes
- API modifications
- dependency upgrades
- business logic changes
- Realtime/Storage authorization changes

## High Risk

Human approval should be mandatory:

- production database changes
- destructive migrations
- production deployment
- payment logic
- credentials/service-role access
- security configuration
- infrastructure modifications
- data deletion
- changes to production RLS policies with broad impact

---

# 16. Definition of Done

Every significant task should have explicit acceptance criteria.

Example:

```text
TASK: Add booking cancellation

Definition of Done:

[ ] Requirements understood
[ ] Architecture approved
[ ] Database migration created
[ ] RLS verified
[ ] API implemented
[ ] API contract updated
[ ] Frontend implemented
[ ] Loading/error states implemented
[ ] Unit tests added
[ ] Integration tests added
[ ] E2E test added
[ ] Security review passed
[ ] Type check passed
[ ] Lint passed
[ ] Build passed
[ ] Git diff reviewed
[ ] No unrelated changes
```

Ruata should not mark a task `DONE` until required gates are satisfied or an explicit exception is approved.

---

# 17. Dynamic Agent Usage

The system should not invoke all five agents for every task.

## Example A — Simple UI change

```text
Ruata
  ↓
Manasseh
  ↓
Validation
```

## Example B — New authentication feature

```text
Ruata
  ↓
Kimi
  ↓
John ──────────────┐
                   ├──→ Ian
Manasseh ──────────┘
```

## Example C — Production bug diagnosis

```text
Ruata
  ↓
Kimi
  ↓
John
  ↓
Ian
  ↓
Ruata
```

The objective is to minimize unnecessary context switching, token cost, duplicated research, and agent overhead.

---

# 18. Parallelism Strategy

When tasks are independent, Ruata should execute them concurrently where safe.

Example:

```text
FEATURE-200

Kimi-1 → Payment provider research
Kimi-2 → Database architecture research

John-1 → Payment backend

Manasseh-1 → Checkout UI
Manasseh-2 → Payment status component

Ian-1 → Backend tests
Ian-2 → E2E tests
```

Concurrency should be bounded by:

- dependency relationships
- resource contention
- shared files
- database state
- rate limits
- cost limits
- risk level

---

# 19. Testing and Evaluation Strategy

The platform should test both the software being built and the agents building it.

## 19.1 Software Evaluation

Measure:

- test pass rate
- regression rate
- defect escape rate
- security findings
- performance regressions
- build stability
- deployment failures
- RLS/auth regression rate

## 19.2 Agent Evaluation

Measure:

- task completion rate
- unnecessary file modifications
- incorrect assumptions
- test quality
- rollback frequency
- repeated failures
- tool errors
- time/cost per task
- human intervention rate
- successful first-pass rate

Maintain representative evaluation tasks for common workflows.

---

# 20. Observability

Agentic development should be observable.

Track:

```text
Task ID
Agent
Model
Prompt/version
Tools used
Commands executed
Files modified
Tests run
Test results
Retries
Failures
Approval events
Duration
Token/cost metrics
Final outcome
Supabase request/operation metadata where safe
```

Never capture secret values in logs.

---

# 21. Security Architecture

Security should be built into the platform rather than added later.

## 21.1 Minimum Controls

- sandboxed execution
- least-privilege tool access
- separate credentials by environment
- secret isolation
- network restrictions where appropriate
- command allowlists/denylists where useful
- protected branches
- mandatory CI
- human approval for high-risk actions
- audit logs
- reversible changes where practical
- Supabase RLS on user-facing tables
- Auth/session validation
- strict separation of publishable and privileged Supabase credentials

## 21.2 Credential Model

Do not give every agent one universal credential.

Prefer role-specific permissions:

```text
Kimi        → read-oriented research access
Manasseh    → frontend repo + test environment
John        → backend/database development access
Ian         → CI/test/security read access + isolated test execution
Ruata       → orchestration + metadata + controlled GitHub operations
```

Production privileges should be separated.

Supabase service-role/secret credentials are trusted server-side credentials and must never be bundled into public frontend assets, browser code, the VS Code extension, or the local bridge.

---

# 22. Recommended Repository Architecture

```text
ai_agents/
├── AGENTS.md
├── README.md
├── AI_Software_Development_Agent_Team_Architecture.md
├── AI Software Development Agent Team — Development Roadmap.md
├── .ai/
│   ├── architecture/
│   ├── decisions/
│   ├── research/
│   ├── tasks/
│   └── task-state/
├── apps/
│   └── dashboard/
├── agents/
├── services/
│   ├── control_plane/
│   ├── agents/
│   ├── orchestrator/
│   ├── persistence/
│   ├── identity/
│   ├── approval/
│   ├── policy/
│   ├── tool_gateway/
│   ├── bridge/
│   ├── git/
│   ├── sandbox/
│   └── observability/
├── packages/
│   └── schemas/
├── local/
│   └── bridge/
├── vscode-extension/
├── config/
├── infra/
│   ├── db/                 Supabase/PostgreSQL migrations
│   └── docker-compose.yml  Optional local infrastructure
├── evaluations/
├── tests/
├── docs/
└── .github/workflows/
```

Local Docker PostgreSQL/Redis may be used for development experiments where necessary, but it is not the production source of truth.

---

# 23. Recommended Agent Runtime Architecture

```text
                    ┌────────────────────┐
                    │    Dashboard/UI     │
                    └─────────┬──────────┘
                              │
                     Supabase Auth/session
                              │
                    ┌─────────▼──────────┐
                    │  Python Control    │
                    │  Plane / Ruata     │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Agent Runtime    │
                    │   / Task Engine    │
                    └─────────┬──────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
              Kimi        Manasseh        John
                │             │             │
                └─────────────┼─────────────┘
                              ▼
                             Ian
                              │
                         CI / Tests
                              │
                         GitHub / Release
                              │
                            Human
                              │
                    Supabase durable state
```

A practical implementation can use an agent SDK, structured tool calls, MCP-compatible tools, isolated sandboxes/worktrees, CI, and Supabase-backed persistence/auth.

---

# 24. Human-in-the-Loop Model

The human should act primarily as:

- product owner
- strategic decision-maker
- high-risk approver
- exception resolver
- final release authority

Avoid requiring human approval for every low-risk file edit. Instead, use risk-based escalation.

Recommended pattern:

```text
LOW RISK
Agent → automated verification → merge automation where appropriate

MEDIUM RISK
Agent → Ian → Ruata → human review

HIGH RISK
Agent → Ian → Ruata → mandatory human approval → execution
```

---

# 25. Recommended End-to-End Workflow

```text
1. HUMAN
   Provides requirement

2. SUPABASE AUTH
   Establishes authenticated user context

3. RUATA
   Analyzes request and repository

4. KIMI (when required)
   Researches and creates technical decisions

5. RUATA
   Creates task graph and acceptance criteria

6. JOHN / MANASSEH
   Implement backend/frontend work

7. SUPABASE
   Persists task/run state and enforces application RLS boundaries

8. IAN
   Runs continuous validation

9. FAIL?
   Ruata creates repair loop

10. PASS
   Full integration, regression and security validation

11. RUATA
   Reviews overall task status

12. HUMAN
   Approves consequential changes

13. GIT / CI
   Merge and deploy according to policy

14. PROJECT MEMORY
   Store durable decisions and lessons learned
```

---

# 26. Recommended Agent Prompt Philosophy

Each agent prompt should specify:

1. Identity and role.
2. Mission.
3. Responsibilities.
4. Non-responsibilities.
5. Available tools.
6. Input artifact formats.
7. Output artifact formats.
8. Completion criteria.
9. Security restrictions.
10. Escalation rules.
11. Error-handling rules.
12. Repository instructions.
13. Supabase access boundaries when applicable.

Avoid giant prompts containing every project-specific fact. Put stable project knowledge into repository artifacts such as `AGENTS.md`, architecture documents, ADRs, and project memory.

---

# 27. Practical Naming Scheme

Recommended internal role names:

```text
ruata-orchestrator
kimi-research-architect
manasseh-frontend
john-backend-data
ian-quality-security
```

Instances can be dynamically spawned:

```text
kimi-1
kimi-2
manasseh-1
john-1
ian-1
ian-2
```

The names identify roles; they do not require every role to correspond to one permanently running model process.

---

# 28. Key Architectural Principles

## Principle 1 — Specialization

Give each agent a clear domain boundary.

## Principle 2 — Bounded Autonomy

Agents should have only the permissions required for the current task.

## Principle 3 — Structured Handoffs

Prefer artifacts and state over conversational chains.

## Principle 4 — Parallelism

Run independent work concurrently when safe.

## Principle 5 — Verification

A code-generation claim is not evidence of correctness.

## Principle 6 — Persistent Engineering Memory

Store durable architectural knowledge outside the model context.

## Principle 7 — Risk-Based Human Oversight

Automate low-risk work and escalate high-risk operations.

## Principle 8 — Git Isolation

Use branches/worktrees/sandboxes to prevent uncontrolled cross-agent interference.

## Principle 9 — Observability

Record agent behavior, tool usage, tests, failures, and outcomes.

## Principle 10 — Continuous Evaluation

Evaluate both the software and the agent system itself.

## Principle 11 — Supabase as Managed Backend Foundation

Use Supabase PostgreSQL, Auth, RLS, Realtime, Storage, and bounded Edge Functions as the canonical managed backend layer unless a future architecture decision explicitly changes this standard.

## Principle 12 — Control Plane Separately Scaled

Do not force long-running agent orchestration, model execution, bridge sessions, or privileged local operations into database/serverless primitives that are not designed for them.

---

# 29. Final Recommended Team Definition

### Ruata — Principal Engineering Orchestrator

**Does:** planning, delegation, task state, integration, policy enforcement, risk management, human escalation.

**Does not:** act as the main production coder.

### Kimi — Research & Architecture Engineer

**Does:** research, architectural analysis, technical decisions, ADRs, dependency evaluation, implementation specifications.

**Does not:** make undocumented design decisions or duplicate established research unnecessarily.

### Manasseh — Frontend Engineer

**Does:** UI/UX, React/Next.js, components, state, API integration, accessibility, frontend performance, frontend tests, and approved Supabase client integration.

**Does not:** invent backend contracts independently or access privileged Supabase credentials.

### John — Backend & Data Engineer

**Does:** APIs, business logic, PostgreSQL/Supabase, migrations, RLS, Auth integration, authorization, integrations, observability, backend tests.

**Does not:** bypass security controls to make implementation easier.

### Ian — Quality, Security & Reliability Engineer

**Does:** testing, E2E, regression, security, RLS/Auth validation, performance, static analysis, CI validation, code review, release verification.

**Does not:** approve unresolved critical quality or security failures.

---

# 30. Recommended Implementation Phase Model

The backend platform is now defined as Supabase-first.

## Phase A — Supabase Foundation

Build and verify:

- Supabase project(s) and environment separation
- Auth configuration
- profiles/workspace membership model
- canonical PostgreSQL migrations
- RLS policies
- authorization test fixtures
- server-side Supabase client/repository integration

## Phase B — Control Plane Integration

Build and verify:

- authenticated control-plane requests
- task/run persistence
- idempotency
- approvals
- audit events
- WebSocket/local-node gateway
- application-level authorization checks

## Phase C — Realtime / Storage / Edge

Build and verify:

- Realtime dashboard state
- artifact storage
- bounded Edge Functions
- webhook/event integrations

## Phase D — Agent Runtime

Build and verify:

- Ruata
- Kimi
- John
- Manasseh
- Ian
- tool gateway
- policy engine
- model provider abstraction

## Phase E — Local + Cloud Execution

Build and verify:

- Local Agent Bridge
- VS Code extension
- worktrees
- cloud sandbox workers
- reconciliation/recovery

## Phase F — Quality / Security / Operations

Build and verify:

- automated evaluation
- centralized observability
- security test suite
- deployment automation
- end-to-end benchmark

---

# 31. Reference Operating Model

```text
                         HUMAN
                           │
                  ┌────────▼────────┐
                  │ AGENTS DASHBOARD│
                  └────────┬────────┘
                           │
                     Supabase Auth
                           │
                           ▼
                    SUPABASE PLATFORM
               Auth · PostgreSQL · RLS
               Realtime · Storage · Edge
                           │
                           ▼
                    CLOUD CONTROL PLANE
                           │
                        RUATA
                           │
                  ┌────────┼────────┐
                  │        │        │
                  ▼        ▼        ▼
                KIMI   MANASSEH    JOHN
                  │        │        │
                  └────────┼────────┘
                           ▼
                          IAN
                           │
                    PASS / FAIL / FIX
                           │
                     HUMAN APPROVAL
                           │
                     ┌─────┴─────┐
                     │           │
                     ▼           ▼
               LOCAL NODE    CLOUD SANDBOX
                     │           │
               VS Code/Git      │
               Terminal/etc.    │
                     │           │
                     └─────┬─────┘
                           ▼
                         GitHub
                           │
                      CI / Release
                           │
                           ▼
                    PROJECT MEMORY
```

---

# 32. Key Takeaway

The strongest implementation of this five-agent concept is not five equal autonomous agents. It is a **role-based engineering system** in which:

- **Ruata is the control plane.**
- **Kimi converts uncertainty into technical decisions.**
- **Manasseh owns the frontend.**
- **John owns the backend and data layer.**
- **Ian acts as the independent verification and security gate.**
- **Supabase provides the managed production backend foundation: Auth, PostgreSQL, RLS, Realtime, Storage, and bounded Edge Functions.**
- **The Python control plane provides orchestration, agent runtime coordination, policy, approvals, long-running workers, and the local-bridge gateway.**
- **The Local Agent Bridge remains the workstation security boundary.**
- **Git, CI, structured artifacts, repository instructions, and project memory provide the shared engineering infrastructure.**
- **Humans remain the final authority for consequential changes.**

This architecture provides a clear path from assisted coding to controlled, semi-autonomous software engineering without making the database, serverless layer, or model provider responsible for functions they should not own.
