# AI Software Development Agent Team — Architecture & Agent Specifications

**Version:** 2.0  
**Date:** September 6, 2026  
**Purpose:** Define a production-oriented hybrid cloud + local execution platform for a multi-agent AI software-engineering team, including agent roles, orchestration, local VS Code integration, security, isolation, observability, deployment, and controlled delivery.

---

## 1. Executive Summary

The recommended system uses five specialized agent roles under a task-driven orchestration model:

1. **Ruata** — Principal Engineering Orchestrator / Engineering Manager
2. **Kimi** — Research & Architecture Engineer
3. **Manasseh** — Frontend Engineer
4. **John** — Backend & Data Engineer
5. **Ian** — Quality, Security & Reliability Engineer

The five roles should **not** operate as five autonomous chatbots continuously conversing with one another. Instead, Ruata should manage a structured task graph, delegate bounded work to specialist agents, maintain task state, enforce quality gates, and require human approval for consequential actions.

The central operating principle is:

> **Ruata coordinates. Kimi decides. Manasseh and John build. Ian proves it works. The human approves consequential changes.**

The architecture is designed around current agentic software-engineering practices: specialized subagents, parallel execution where useful, repository-local instructions, isolated workspaces, structured artifacts, automated validation, evaluations, security controls, observability, and human oversight.

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
                         │       RUATA          │
                         │ Orchestrator / EM    │
                         └──────────┬───────────┘
                                    │
                       Task Graph / Delegation
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
        ┌───────────┐         ┌─────────────┐       ┌─────────────┐
        │   KIMI    │         │  MANASSEH   │       │    JOHN     │
        │ Research  │         │  Frontend   │       │  Backend    │
        │ Architect │         │  Engineer   │       │  Engineer   │
        └─────┬─────┘         └──────┬──────┘       └──────┬──────┘
              │                      │                     │
              │                      └──────────┬──────────┘
              │                                 │
              └─────────────────────────────────┘
                                                ▼
                                       ┌─────────────────┐
                                       │      IAN        │
                                       │ QA / Security   │
                                       │ Reliability     │
                                       └────────┬────────┘
                                                │
                                       PASS / FAIL / FIX
                                                │
                                   ┌────────────┴────────────┐
                                   │                         │
                                   ▼                         ▼
                              Ruata Review             Human Review
                                   │                         │
                                   └────────────► Merge ◄────┘
```

## 2.1 Core Design Principle

Agents communicate primarily through **structured artifacts and task state**, not long free-form conversations.

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

This improves reproducibility, traceability, auditability, and handoff quality.

---


# 2A. Hybrid Cloud + Local Execution Architecture

The recommended deployment model is a **hybrid cloud + local execution system**.

The cloud hosts the platform control plane: dashboard, orchestration, task state, agent registry, project memory metadata, audit logs, policy evaluation, model access, and optional cloud sandboxes.

The user's computer hosts a **Local Development Node** consisting of a VS Code extension and local agent bridge. This node provides controlled access to the currently selected VS Code workspace, terminal, Git, browser automation, local services, and development tools.

The local node should maintain an outbound secure connection to the cloud control plane. The development computer should not be exposed directly to the public Internet merely so cloud agents can reach it.

## 2A.1 Reference Topology

```text
                                INTERNET
                                   │
                                   ▼
                     ┌────────────────────────────┐
                     │      AGENTS DASHBOARD      │
                     │        Web Application     │
                     │                            │
                     │ Projects · Agents · Tasks │
                     │ Runs · Memory · Approvals  │
                     └─────────────┬──────────────┘
                                   │
                              HTTPS / SSE
                                   │
                                   ▼
                     ┌────────────────────────────┐
                     │     CLOUD CONTROL PLANE    │
                     │                            │
                     │ Ruata Orchestrator         │
                     │ Task Engine / Queue        │
                     │ Agent Registry             │
                     │ Policy Engine              │
                     │ Memory / Artifacts         │
                     │ Audit / Observability      │
                     │ Model Gateway              │
                     └─────────────┬──────────────┘
                                   │
                           secure outbound WSS
                                   │
                    ╔══════════════▼═══════════════╗
                    ║       LOCAL DEV NODE         ║
                    ║          Your PC              ║
                    ║                                ║
                    ║  ┌────────────────────────┐    ║
                    ║  │   VS Code Extension    │    ║
                    ║  └───────────┬────────────┘    ║
                    ║              │                 ║
                    ║  ┌───────────▼────────────┐    ║
                    ║  │   Local Agent Bridge   │    ║
                    ║  └───────┬───┬───┬────────┘    ║
                    ║          │   │   │             ║
                    ║          ▼   ▼   ▼             ║
                    ║       Files Git Terminal       ║
                    ║          │   │   │             ║
                    ║          ├── Browser           ║
                    ║          ├── Playwright        ║
                    ║          ├── Docker            ║
                    ║          ├── Node / Python     ║
                    ║          └── Project Services  ║
                    ║                                ║
                    ║       Registered Workspaces   ║
                    ╚════════════════════════════════╝
                                   │
                                   ▼
                              Git / GitHub
```

## 2A.2 Separation of Responsibilities

### Cloud control plane

The cloud side should own:

- authentication and user identity
- project registration
- device registration
- agent definitions and versions
- task creation and routing
- task dependency graphs
- agent lifecycle state
- model routing
- shared project metadata
- artifact metadata and storage
- policy decisions
- approvals
- audit logging
- evaluation data
- observability
- optional cloud execution

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

The cloud control plane should issue **requests**, not unrestricted shell instructions. The local bridge decides whether an operation is permitted before execution.

## 2A.3 Why the Hybrid Model

This architecture provides four important properties:

1. **Local context:** agents can work against the exact project and VS Code workspace currently being developed.
2. **Cloud accessibility:** the dashboard and orchestration layer remain accessible from any device.
3. **Security boundary:** the workstation is not a publicly exposed execution server.
4. **Optional scalability:** long-running tasks can be moved to isolated cloud sandboxes without redesigning the overall system.

## 2A.4 Local Development Node

The local node should be treated as a first-class platform component rather than a temporary helper script.

Recommended components:

```text
Local Development Node
├── Ruata VS Code Extension
├── Local Agent Bridge
├── Workspace Registry
├── Permission / Policy Enforcer
├── Process Manager
├── Git / Worktree Manager
├── Browser Controller
├── Test Runner Adapter
├── Diagnostics Adapter
└── Secure Credential Broker
```

### VS Code extension

The extension should provide the user interface inside VS Code and expose editor-aware operations such as:

```text
get_workspace()
get_current_file()
get_open_files()
get_selection()
get_diagnostics()
get_git_status()
get_active_editor()
open_file()
apply_edit()
create_file()
run_task()
read_terminal_output()
```

The extension should not itself contain the full orchestration engine. It should act as the editor-facing component of the local node.

### Local Agent Bridge

The bridge should be a separate local service responsible for:

- maintaining the secure connection to the cloud
- authenticating the device
- validating requested actions
- mapping project IDs to local workspaces
- enforcing path restrictions
- enforcing command restrictions
- invoking local tools
- returning structured results
- collecting local execution telemetry
- handling temporary disconnection and reconnection

## 2A.5 Outbound-Only Connection Pattern

Preferred network model:

```text
Local Dev Node
      │
      │ outbound TLS/WebSocket
      ▼
Cloud Gateway
      │
      ▼
Control Plane
```

Avoid requiring inbound Internet connectivity to the developer machine.

The connection should use:

- TLS
- short-lived access tokens where practical
- device identity
- connection renewal
- message authentication
- replay protection
- request IDs / correlation IDs
- explicit session state

## 2A.6 Device Registration

Each development computer should be registered as a device.

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

## 2A.7 Workspace Registration

Do not grant all-agent access to an entire user profile.

Projects should be explicitly registered:

```text
Project Registry

MizoramStay
C:\Projects\MizoramStay

HospitalQualityPortal
C:\Projects\HospitalQualityPortal

HIMS
C:\Projects\HIMS
```

Each workspace should have:

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

## 2A.8 Local Policy Example

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

The precise allowlist/denylist strategy should be adapted to the operating system and project tooling. Path and capability restrictions should be enforced by the local bridge, not only described in prompts.

## 2A.9 Cloud Execution Mode

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

## 2A.10 Dashboard Architecture

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

A project view should show:

```text
Project: MizoramStay

Agents
✓ Ruata       Coordinating
✓ Kimi        Complete
● John        Working
● Manasseh    Working
○ Ian         Waiting

Current task
TASK-8432  Booking Cancellation

Branch
feature/8432-booking-cancellation

Validation
✓ Typecheck
✓ Lint
● Integration tests
○ E2E

Controls
[Pause] [Stop] [Approve] [Open VS Code]
```

## 2A.11 Event Model

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

Every event should include a correlation ID so the full history of a task can be reconstructed.

## 2A.12 Request/Response Contract Between Cloud and Local Node

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

## 2A.13 Execution Permissions by Agent

| Capability | Ruata | Kimi | Manasseh | John | Ian |
|---|---:|---:|---:|---:|---:|
| Read repository | Yes | Yes | Yes | Yes | Yes |
| Edit frontend | Limited | No | Yes | No | Tests only |
| Edit backend | Limited | No | No | Yes | Tests only |
| Edit database | No | No | No | Yes | Verify |
| Run terminal | Controlled | Safe/read-heavy | Yes | Yes | Yes |
| Browser | As needed | Research | Yes | As needed | Yes |
| Git branch | Yes | Read/create research branches | Yes | Yes | Yes |
| Merge | Controlled | No | No | No | Recommend |
| Production deploy | Approval only | No | No | No | Verify |
| Secrets access | Brokered/minimal | No | No | Minimal | No |
| Security scans | Trigger | Analyze | Limited | Limited | Yes |
```

Permissions should be dynamically reduced further for high-risk projects or sensitive workspaces.

## 2A.14 Tool Gateway

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

## 2A.15 MCP and Tool Integration

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

## 2A.16 Repository State Strategy

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

Recommended behavior when uncommitted changes exist:

```text
Detect changes
     ↓
Classify ownership
     ├── user changes → preserve
     ├── same-task changes → continue carefully
     └── unknown changes → pause / request decision
```

## 2A.17 Agent Session Lifecycle

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

## 2A.18 Failure Handling

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

## 2A.19 Local Node Offline Behavior

If the local node disconnects:

```text
Cloud detects disconnect
        ↓
Pause local execution tasks
        ↓
Preserve task state
        ↓
Wait for reconnect
        ↓
Reconcile node state
        ↓
Resume only after state validation
```

Tasks that do not depend on the local node may continue in the cloud.

## 2A.20 Security Boundary

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

## 2A.21 Emergency Controls

The local node should expose:

```text
[ STOP ALL AGENTS ]
[ DISCONNECT FROM CLOUD ]
[ REVOKE DEVICE ]
```

The Stop action should terminate active agent-controlled processes according to a safe escalation procedure and prevent new execution until explicitly re-enabled.

## 2A.22 Observability for Local Execution

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

## 2A.23 Recommended Technology Topology

A practical first implementation can use:

```text
Dashboard
→ Next.js / TypeScript

Cloud API / Orchestrator
→ Python / FastAPI

Agent Runtime
→ OpenAI Agents SDK or equivalent agent runtime

Database
→ PostgreSQL / Supabase

Realtime
→ WebSocket / Server-Sent Events

Task Queue
→ Redis or managed queue

Artifacts
→ Object storage

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

These are implementation choices, not hard dependencies. The platform should keep model, agent, and tool interfaces replaceable.

## 2A.24 Recommended Hosting Model

A practical initial deployment could be:

```text
Vercel
├── Dashboard / Next.js

Managed Cloud Backend
├── API
├── Orchestrator
├── WebSocket / Realtime
└── Worker processes

Supabase / PostgreSQL
├── users
├── projects
├── devices
├── agents
├── tasks
├── runs
├── approvals
├── events
└── evaluation metadata

Object Storage
└── logs / reports / artifacts

Developer PC
└── Local Development Node
```

The exact cloud providers can change without changing the logical architecture.

## 2A.25 Multi-Device Future State

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

Ruata can then route a task based on:

- project location
- required tools
- available hardware
- connectivity
- sensitivity
- workload duration
- resource availability

## 2A.26 Human Control Model

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

High-risk operations should surface a concise approval request:

```text
Approval required

Task: TASK-8432
Operation: Apply production database migration
Risk: HIGH
Reason: Changes live schema

Affected resources:
- production database
- booking table

[Approve] [Reject]
```

## 2A.27 Platform-Level Data Model

A minimal relational model should include:

```text
users
organizations (optional)
projects
devices
workspaces
agents
agent_versions
agent_runs
tasks
task_dependencies
artifacts
approvals
events
tool_requests
policy_rules
evaluations
model_usage
```

Important relationships:

```text
User → Projects
Project → Workspaces
Workspace → Device
Project → Tasks
Task → Task Dependencies
Task → Agent Runs
Agent Run → Tool Requests
Task → Artifacts
Task → Approvals
Everything → Events
```

## 2A.28 Build Strategy

Do not start with five fully autonomous agents plus a dashboard plus cloud execution plus production deployment at once.

Recommended sequence:

```text
1. Local Development Node
2. VS Code extension
3. Workspace / device registration
4. Ruata control plane
5. Task state machine
6. Kimi
7. John + Manasseh
8. Ian validation pipeline
9. Dashboard
10. Cloud sandbox execution
11. Advanced evaluations
12. Increased autonomy
```

This produces usable milestones and keeps the security boundary understandable.

# 3. Agent Fleet

| Agent | Role | Primary Mission |
|---|---|---|
| **Ruata** | Principal Engineering Orchestrator | Understand requirements, plan, delegate, coordinate, enforce gates, integrate results, control risk |
| **Kimi** | Research & Architecture Engineer | Research technology and architecture questions, inspect existing systems, make technical recommendations and decisions |
| **Manasseh** | Frontend Engineer | Build and maintain frontend UI, state, interactions, accessibility, and frontend tests |
| **John** | Backend & Data Engineer | Build APIs, database, business logic, auth, integrations, backend tests, and data-layer security |
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
- Enforce repository and project policies.
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

## 4.4 Task Graph Example

```text
FEATURE-142
│
├── TASK-142.1 Requirements analysis
│       └── Kimi
│
├── TASK-142.2 Database changes
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
├── TASK-142.6 Backend tests
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
- What is the recommended database design?
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
- API consumption.
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
Backend implementation
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
[ ] Types are correct
[ ] Lint passes
[ ] Tests pass
[ ] No unrelated files changed
```

---

# 7. John — Backend & Data Engineer

## 7.1 Mission

John owns backend services, APIs, databases, authentication/authorization, business logic, integrations, and backend testing.

## 7.2 Primary Responsibilities

- API implementation.
- Database schema design.
- PostgreSQL/Supabase changes.
- Database migrations.
- Row Level Security (RLS).
- Authentication.
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
- secrets handling
- rate limiting
- tenant isolation where applicable
- transaction correctness
- sensitive logging

## 7.5 Database Change Requirements

Database changes should normally include:

```text
[ ] Migration created
[ ] Migration reversible where appropriate
[ ] Existing data considered
[ ] Constraints verified
[ ] Indexing considered
[ ] RLS verified
[ ] Authorization verified
[ ] Performance implications considered
[ ] Tests updated
[ ] Rollout / rollback implications documented
```

## 7.6 John Should NOT

- Silently change frontend requirements.
- Bypass authorization to make tests pass.
- Disable RLS simply to solve implementation problems.
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
API → Database
Authentication → API
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

## Before coding
1. Inspect repository instructions.
2. Inspect the existing implementation.
3. Determine the smallest appropriate change.
4. Create an implementation plan for non-trivial work.

## After coding
1. Run formatter.
2. Run lint.
3. Run type checking.
4. Run unit tests.
5. Run integration tests where applicable.
6. Run end-to-end tests where applicable.
7. Review the git diff.
8. Report failures explicitly.
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

    research/
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

For stronger isolation, use worktrees or equivalent sandboxed workspaces:

```text
/worktrees/
    manasseh-feature-142/
    john-feature-142/
    ian-feature-142/
```

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
Database
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
```

## 13.2 Kimi Tools

```text
Web / documentation
GitHub
Repository inspection
Package metadata
Research sources
Architecture artifacts
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
```

## 13.4 John Tools

```text
Filesystem
GitHub
Terminal
Supabase / PostgreSQL
API tooling
Backend test tools
Logs
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
```

## Level 2 — Write / Implement

Agent can:

```text
modify code
write tests
create branches
create migrations
update artifacts
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

## Medium Risk

Require stronger review:

- database schema changes
- authentication changes
- API modifications
- dependency upgrades
- business logic changes

## High Risk

Human approval should be mandatory:

- production database changes
- destructive migrations
- production deployment
- payment logic
- credentials
- security configuration
- infrastructure modifications
- data deletion

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
```

This is essential for debugging agent behavior and improving prompts, routing, policies, and models.

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

---

# 22. Recommended Repository Architecture

```text
my-project/
├── AGENTS.md
├── README.md
├── .ai/
│   ├── architecture/
│   ├── decisions/
│   ├── research/
│   ├── tasks/
│   └── task-state/
├── frontend/
├── backend/
├── database/
├── tests/
└── ...
```

The AI layer should remain closely connected to the actual source repository but should not replace standard software-engineering structure.

---

# 23. Recommended Agent Runtime Architecture

```text
                    ┌────────────────────┐
                    │      Ruata UI      │
                    └─────────┬──────────┘
                              │
                        Orchestrator
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
                         GitHub PR
                              │
                            Human
```

A practical implementation can use an agent SDK, structured tool calls, MCP-compatible tools, isolated sandboxes/worktrees, CI, and a persistent task store.

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

2. RUATA
   Analyzes request and repository

3. KIMI (when required)
   Researches and creates technical decisions

4. RUATA
   Creates task graph and acceptance criteria

5. JOHN / MANASSEH
   Implement backend and frontend work

6. IAN
   Runs continuous validation

7. FAIL?
   Ruata creates repair loop

8. PASS
   Full integration, regression and security validation

9. RUATA
   Reviews overall task status

10. HUMAN
    Approves consequential changes

11. GIT / CI
    Merge and deploy according to policy

12. PROJECT MEMORY
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

---

# 29. Final Recommended Team Definition

### Ruata — Principal Engineering Orchestrator

**Does:** planning, delegation, task state, integration, policy enforcement, risk management, human escalation.

**Does not:** act as the main production coder.

### Kimi — Research & Architecture Engineer

**Does:** research, architectural analysis, technical decisions, ADRs, dependency evaluation, implementation specifications.

**Does not:** make undocumented design decisions or duplicate established research unnecessarily.

### Manasseh — Frontend Engineer

**Does:** UI/UX, React/Next.js, components, state, API integration, accessibility, frontend performance, frontend tests.

**Does not:** invent backend contracts independently.

### John — Backend & Data Engineer

**Does:** APIs, business logic, PostgreSQL/Supabase, migrations, auth, authorization, integrations, observability, backend tests.

**Does not:** bypass security controls to make implementation easier.

### Ian — Quality, Security & Reliability Engineer

**Does:** testing, E2E, regression, security, performance, static analysis, CI validation, code review, release verification.

**Does not:** approve unresolved critical quality or security failures.

---

# 30. Recommended Next Implementation Phase

The best next step is to build this architecture in stages rather than attempting a fully autonomous five-agent platform immediately.

## Phase 1 — Foundation

Build:

- repository instruction framework
- project memory structure
- Git/worktree isolation
- common tool layer
- structured task schema
- task state machine
- logging/observability

## Phase 2 — Ruata

Implement:

- task intake
- planning
- task graph creation
- routing
- agent lifecycle management
- approval routing

## Phase 3 — Kimi

Implement:

- research workflow
- architecture analysis
- ADR generation
- technical specification generation

## Phase 4 — Manasseh + John

Implement:

- bounded coding environments
- standard implementation workflow
- contract-driven frontend/backend handoff
- automated test execution

## Phase 5 — Ian

Implement:

- testing pipeline
- security checks
- regression suite
- release gate
- automated repair-loop feedback

## Phase 6 — Evaluations

Build an evaluation suite for:

- feature implementation
- bug fixing
- refactoring
- database changes
- API changes
- frontend changes
- authentication changes
- security-sensitive changes
- regression handling

## Phase 7 — Controlled Autonomy

Gradually allow more autonomous execution according to measured reliability and risk.

---

# 31. Reference Operating Model

```text
                         HUMAN
                           │
                  ┌────────▼────────┐
                  │ AGENTS DASHBOARD│
                  └────────┬────────┘
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
                           ▼
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
- **Git, CI, structured artifacts, repository instructions, and project memory provide the shared engineering infrastructure.**
- **Humans remain the final authority for consequential changes.**

This structure should scale substantially better than a simple linear “agent-to-agent conversation” architecture and provides a clear path from assisted coding to controlled, semi-autonomous software engineering.
