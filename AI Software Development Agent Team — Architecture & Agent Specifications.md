# AI Software Development Agent Team — Architecture & Agent Specifications

**Version:** 2.0  
**Date:** September 6, 2026  
**Purpose:** Define a production-oriented hybrid cloud + local execution platform for a multi-agent AI software-engineering team, including agent roles, orchestration, local VS Code integration, security, isolation, observability, deployment, and controlled delivery.

---

> This repository is the implementation home for the architecture defined in this specification. The repository policy is **main-only development**: all changes are committed directly to `main`; feature branches and pull requests are intentionally not part of the operating model for this project.

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
                     ┌──────────────┼──────────────┐
                     │              │              │
                     ▼              ▼              ▼
               ┌──────────┐   ┌───────────┐  ┌───────────┐
               │  KIMI    │   │ MANASSEH  │  │   JOHN    │
               │ Research │   │ Frontend  │  │ Backend   │
               │ Architect│   │ Engineer  │  │ Engineer  │
               └────┬─────┘   └─────┬─────┘  └─────┬─────┘
                    │               │              │
                    └───────────────┼──────────────┘
                                    ▼
                            ┌─────────────────┐
                            │      IAN        │
                            │ QA / Security   │
                            │ Review / Evals  │
                            └────────┬────────┘
                                     │
                             PASS / FAIL / FIX
                                     │
                     ┌───────────────┴──────────────┐
                     │                              │
                     ▼                              ▼
              Integration                     Human Review
                  Tests                            ↓
                     │                          Merge
                     ▼                            /
                   Ruata ◄───────────────────────
```

The core platform is a hybrid system:

```text
                         INTERNET
                            │
                            ▼
              ┌─────────────────────────────┐
              │       AGENTS DASHBOARD      │
              │          Web App            │
              └──────────────┬──────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │       CLOUD CONTROL PLANE   │
              │                             │
              │  Ruata Orchestrator         │
              │  Agent Runtime              │
              │  Task Queue                 │
              │  Memory / State             │
              │  Policies                   │
              │  Audit Logs                 │
              └──────────────┬──────────────┘
                             │
                         Secure WSS
                             │
                             ▼
              ┌─────────────────────────────┐
              │    LOCAL DEVELOPMENT NODE   │
              │                             │
              │  VS Code Extension          │
              │  Local Agent Bridge         │
              │  Workspace Manager          │
              └──────────────┬──────────────┘
                             │
                 ┌───────────┼───────────┐
                 ▼           ▼           ▼
               Files      Terminal      Git
                 │           │           │
                 └───────────┼───────────┘
                             ▼
                         Any Project
```

---

# 3. Design Principles

1. **Task-driven, not conversation-driven.** Agents receive explicit objectives, constraints, inputs, outputs, and completion criteria.
2. **Least privilege.** Every agent receives only the tools, paths, credentials, and execution capabilities it requires.
3. **Local code stays local by default.** The cloud control plane coordinates work but does not require public inbound access to the developer's machine.
4. **Structured artifacts over conversational memory.** Research, decisions, plans, contracts, test reports, and task state are persistent files/data objects.
5. **Parallelize independent work.** Ruata should construct a dependency graph and run independent agent tasks concurrently.
6. **Validation is a first-class workflow stage.** Ian is not only an end-of-project tester; quality gates run throughout execution.
7. **Git provides provenance and rollback.** All code changes are attributable to a task and agent execution.
8. **Human approval for consequential operations.** Production, destructive, security-sensitive, and credential-related operations require approval.
9. **Fail closed.** If a permission, workspace, tool, or policy check is ambiguous, the operation is denied.
10. **Provider/model agnostic where practical.** The platform should permit model selection per agent/task without coupling the orchestration layer to one provider.
11. **Observability is mandatory.** Every agent action, tool call, task transition, and approval decision should be traceable.
12. **Main-only repository policy.** This platform repository itself is updated only on `main`, per the project owner's explicit operating requirement.

---

# 4. Agent Team

## 4.1 Ruata — Principal Engineering Orchestrator

### Mission

Turn human requests into executable software-engineering workflows, coordinate specialist agents, enforce policies and quality gates, integrate outcomes, and provide a reliable final status.

### Primary responsibilities

- Requirement interpretation
- Repository reconnaissance
- Task decomposition
- Dependency graph construction
- Agent selection and delegation
- Task state management
- Parallel execution management
- Conflict resolution
- Quality-gate enforcement
- Human approval routing
- Final change summary
- Release readiness assessment

### Ruata should not primarily write application code

Ruata may make small coordination changes where necessary, but application implementation belongs to the specialist agents unless a task explicitly routes coding to Ruata.

### Inputs

- Human request
- Project configuration
- Repository instructions
- Current Git status
- Existing task state
- Architecture/decision records
- Tool and permission policy
- Previous test results

### Outputs

- Requirement summary
- Task graph
- Agent assignments
- Execution plan
- Status events
- Escalations
- Final implementation summary
- Release recommendation

### Tools

- Task queue
- Agent registry
- Git/GitHub
- Repository inspection
- CI status
- Test reports
- Local device/workspace registry
- Policy engine
- Artifact store

### Restricted operations

By default Ruata cannot:

- Exfiltrate secrets
- Modify production directly
- Bypass approval gates
- Override security policy silently
- Mark a failed validation as passed

---

## 4.2 Kimi — Research & Architecture Engineer

### Mission

Reduce technical uncertainty and convert research into concrete engineering decisions and implementation contracts.

### Primary responsibilities

- Technology research
- Documentation review
- Existing architecture inspection
- Dependency evaluation
- API/provider comparison
- Performance/security research
- Architecture design
- ADR creation
- Interface/API contract creation
- Implementation constraints

### Core principle

Kimi should produce decisions and specifications, not just links or prose research.

### Expected artifacts

```text
.ai/research/<task-id>/
├── research.md
├── architecture.md
├── decisions.md
├── api-contract.yaml
└── references.md
```

### ADR format

```text
Decision:
Why:
Alternatives considered:
Trade-offs:
Security implications:
Performance implications:
Migration considerations:
Implementation constraints:
```

### Restrictions

- No production database changes
- No production deployment
- No credential retrieval beyond approved metadata
- No arbitrary application-code modifications unless explicitly delegated

---

## 4.3 Manasseh — Frontend Engineer

### Mission

Design and implement robust, accessible, responsive client experiences that conform to approved architecture and API contracts.

### Responsibilities

- UI implementation
- UX flows
- React/Next.js development where applicable
- Component architecture
- Design system integration
- Client-side state
- Forms and validation
- Loading/error/empty states
- Accessibility
- Responsive behavior
- Browser integration
- Frontend unit/integration tests
- E2E test contribution

### Boundary

Manasseh consumes backend/API contracts rather than inventing incompatible backend interfaces.

### Typical editable scope

```text
app/
src/app/
src/components/
src/features/
src/hooks/
src/stores/
src/lib/client/
styles/
tests/frontend/
```

### Restrictions

- No unauthorized backend schema changes
- No silent modification of authentication/authorization policy
- No production deployment
- No secret exposure

---

## 4.4 John — Backend & Data Engineer

### Mission

Implement secure, durable server-side behavior, data models, APIs, integrations, and backend validation.

### Responsibilities

- API implementation
- Business logic
- PostgreSQL/Supabase
- Database schema/migrations
- Row Level Security
- Authentication
- Authorization
- Server-side validation
- Transactions
- Background jobs
- External integrations
- Caching where appropriate
- Logging and observability
- Backend unit/integration tests
- API contract maintenance

### API contract

For typed HTTP APIs, maintain an explicit contract such as:

```text
openapi/openapi.yaml
```

or a project-appropriate equivalent.

### Restrictions

- No destructive production migration without approval
- No secret rotation without approval
- No disabling security controls to resolve failing tests
- No unrelated frontend changes

---

## 4.5 Ian — Quality, Security & Reliability Engineer

### Mission

Provide objective evidence that the change is correct, secure, maintainable, and compatible with existing functionality.

### Responsibilities

#### Static validation

- Formatting
- Linting
- Type checking
- Dependency checks
- Secret scanning

#### Automated testing

- Unit
- Integration
- E2E
- Regression
- Contract tests

#### Security

- Authentication checks
- Authorization checks
- RLS verification
- Injection risks
- XSS/CSRF review where applicable
- IDOR/access-control review
- Secret leakage
- Dependency/security advisories
- Unsafe configuration

#### Reliability/performance

- Failure-path testing
- Boundary conditions
- Timeouts/retries
- Resource handling
- Performance smoke checks where appropriate

### Core rule

Ian must not alter production behavior merely to make a test pass without routing that change through the normal implementation and review process.

---

# 5. Task Graph Model

Tasks are modeled as nodes with explicit dependencies.

```text
FEATURE-142
│
├── TASK-142.1 Requirements / architecture
│        └── Kimi
│
├── TASK-142.2 Database changes
│        └── John
│
├── TASK-142.3 API implementation
│        └── John
│
├── TASK-142.4 UI implementation
│        └── Manasseh
│
├── TASK-142.5 Frontend tests
│        └── Manasseh
│
├── TASK-142.6 Backend tests
│        └── John
│
└── TASK-142.7 Integration / security / regression
         └── Ian
```

A minimal task object should contain:

```json
{
  "task_id": "TASK-142.3",
  "project_id": "project-001",
  "parent_task_id": "FEATURE-142",
  "agent_role": "john",
  "status": "ready",
  "workspace_id": "ws-001",
  "dependencies": ["TASK-142.2"],
  "allowed_paths": ["backend/", "supabase/"],
  "acceptance_criteria": [],
  "required_checks": [],
  "risk_level": "medium"
}
```

---

# 6. State Machine

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
HUMAN_APPROVAL (when required)
 │
 ▼
COMPLETED
```

Additional terminal/error states:

```text
BLOCKED
CANCELLED
FAILED
POLICY_DENIED
TIMED_OUT
``` 

---

# 7. Definition of Done

Every task should have explicit completion criteria.

```text
[ ] Requirements understood
[ ] Architecture/technical decision complete where required
[ ] Database change complete where applicable
[ ] API contract updated where applicable
[ ] Backend implementation complete
[ ] Frontend implementation complete
[ ] Unit tests added/updated
[ ] Integration tests added/updated
[ ] E2E/regression tests added where appropriate
[ ] Security checks complete
[ ] Type check passed
[ ] Lint passed
[ ] Build passed
[ ] Required CI checks passed
[ ] Git diff reviewed
[ ] No unrelated changes
[ ] Human approval obtained for high-risk operations
```

---

# 8. Structured Artifacts

Agents should communicate through persistent structured artifacts rather than large free-form message chains.

Recommended artifact set:

```text
.ai/
├── project.md
├── architecture.md
├── conventions.md
├── decisions/
├── research/
├── tasks/
├── plans/
├── contracts/
├── test-reports/
├── reviews/
└── runs/
```

Typical files:

```text
.ai/tasks/TASK-142.json
.ai/plans/TASK-142.md
.ai/research/TASK-142/research.md
.ai/decisions/ADR-021.md
.ai/contracts/TASK-142/openapi.yaml
.ai/test-reports/TASK-142.json
.ai/reviews/TASK-142.md
```

---

# 9. Repository Instructions

Each target software project should contain a root-level `AGENTS.md`.

Optional localized instruction files:

```text
AGENTS.md
frontend/AGENTS.md
backend/AGENTS.md
database/AGENTS.md
tests/AGENTS.md
```

Recommended contents:

- Project architecture
- Supported commands
- Formatting/lint rules
- Testing commands
- File ownership rules
- Migration rules
- Security rules
- Deployment policy
- Forbidden operations
- Definition of Done

The platform itself should also have a top-level `AGENTS.md` describing its architecture and main-only repository policy.

---

# 10. Hybrid Cloud + Local Execution

## 10.1 Cloud Control Plane

The cloud is responsible for:

- Agents Dashboard
- Authentication
- Project registry
- Device registry
- Agent registry
- Ruata orchestration
- Task queue
- Task state
- Agent run metadata
- Memory metadata
- Policy evaluation
- Audit logging
- Evaluation data
- Artifact metadata
- Cloud execution scheduling

The cloud does **not** require unrestricted inbound access to the developer's machine.

## 10.2 Local Development Node

The local node consists of:

```text
Ruata Local Development Node
├── VS Code Extension
├── Local Agent Bridge
├── Workspace Manager
├── Permission Manager
├── Git Manager
├── Terminal Manager
├── Test Runner
└── Browser Controller
```

The local bridge maintains an authenticated outbound connection to the cloud control plane.

```text
PC
 │
 │ outbound TLS / WebSocket
 ▼
Cloud Control Plane
```

## 10.3 Why outbound connectivity

Avoid exposing development ports such as SSH, local HTTP servers, or arbitrary bridge ports directly to the public internet. The local bridge should establish the connection and receive only authorized task instructions.

---

# 11. VS Code Integration

The preferred implementation is a first-party VS Code extension plus a local bridge.

The extension should expose controlled editor/workspace capabilities such as:

```text
get_current_file()
get_open_files()
get_workspace()
get_selection()
get_diagnostics()
get_terminal_output()
get_git_status()
get_active_editor()
open_file()
apply_edit()
create_file()
run_task()
```

The extension should display:

- Connection status
- Selected project/workspace
- Active task
- Agent statuses
- Pending approval requests
- Recent tool actions
- Test state
- Stop/pause controls

The system should not depend on GUI mouse automation of VS Code for routine development tasks.

---

# 12. Workspace and Device Registration

A developer computer should be registered as a trusted execution device.

Example:

```text
Device: Maruata-PC
OS: Windows
VS Code: connected
Status: Online
Registered projects: 3
```

Projects should be explicitly registered:

```text
MizoramStay
C:\Projects\MizoramStay

HospitalQualityPortal
C:\Projects\HospitalQualityPortal
```

Task routing becomes:

```text
Project
   ↓
Device
   ↓
Workspace
   ↓
Agent
```

The system should support multiple future devices, including another workstation, laptop, or cloud sandbox.

---

# 13. Permission Model

Agents should not have equal permissions.

## Ruata

```text
READ:
  Project files, Git state, task state, test results

WRITE:
  Plans, task state, coordination artifacts

EXECUTE:
  Delegation and approved validation

RESTRICTED:
  Secrets, destructive operations, production changes
```

## Kimi

```text
READ:
  Repository, docs, research sources, package metadata

WRITE:
  Research, ADRs, specifications

EXECUTE:
  Safe analysis commands

RESTRICTED:
  Production systems, arbitrary code changes
```

## Manasseh

```text
READ:
  Frontend, contracts, design system, browser state

WRITE:
  Frontend code and tests

EXECUTE:
  Frontend tools and browser tests

RESTRICTED:
  Backend schema and production operations
```

## John

```text
READ:
  Backend, database, contracts, configuration metadata

WRITE:
  Backend code, migrations, contracts, tests

EXECUTE:
  Database/dev tools and tests

RESTRICTED:
  Production destructive operations
```

## Ian

```text
READ:
  Whole project and CI artifacts

WRITE:
  Tests, reports, review annotations

EXECUTE:
  Test suites, security checks, builds

RESTRICTED:
  Unreviewed production behavior changes
```

---

# 14. Workspace Isolation

Each agent execution should receive an isolated or controlled workspace whenever concurrent modification is possible.

Preferred options:

```text
/worktrees/
├── manasseh-TASK-142/
├── john-TASK-142/
└── ian-TASK-142/
```

For cloud execution:

```text
Cloud Sandbox
   ↓
Ephemeral workspace
   ↓
Task branch/worktree internally
   ↓
Validation
   ↓
Artifact/commit result
```

The platform repository itself remains main-only for this project. Main-only is a repository policy; it does not require concurrent agent executions to share the same mutable working directory.

---

# 15. Git and Main-Only Repository Policy

## Explicit project requirement

For `drmaruata/ai_agents`:

> **All changes must be pushed and committed to `main` only.**

Do not create or use feature branches for this repository as part of the normal agent workflow.

### Required behavior

- Verify current branch is `main` before repository writes.
- Refuse repository writes if the target branch is not `main`.
- Keep commit messages descriptive and task-oriented.
- Review the diff before committing.
- Run required checks before pushing.
- Record task/run identifiers in commit metadata where practical.
- Never force-push `main` unless explicitly authorized.

Example commit messages:

```text
feat: scaffold hybrid agent platform

docs: update agent architecture specification

fix: enforce local bridge permission checks

test: add orchestrator task-state coverage
```

### Important distinction

The **main-only policy applies to this platform repository**. Target application repositories may use their own branch/PR policies unless explicitly configured otherwise.

---

# 16. Tool Layer and MCP

The system should expose a standardized tool layer.

```text
Agent Runtime
      │
      ▼
     Tools / MCP
 ┌────┼───────────┐
 │    │           │
 ▼    ▼           ▼
GitHub Supabase Browser
 │    │           │
 ▼    ▼           ▼
Repo  DB/API   Playwright
```

Potential tools:

```text
GitHub
Supabase/PostgreSQL
Filesystem
Terminal
Browser/Playwright
Package/documentation search
Issue tracker
CI/CD
Observability
```

Use local `stdio` tools for local-only capabilities where practical and authenticated remote transports for cloud-hosted services.

---

# 17. Browser and UI Testing

Playwright should be a first-class capability for Manasseh and Ian.

Typical workflow:

```text
Manasseh
  ↓
Implement UI
  ↓
Run local app
  ↓
Playwright smoke test
  ↓
Ian
  ↓
Full E2E / regression suite
```

The local bridge should ensure that browser commands are scoped to approved workspaces and development environments.

---

# 18. Cloud Execution

Cloud execution is useful for long-running, isolated, or reproducible tasks.

```text
Ruata
  ↓
Cloud execution request
  ↓
Ephemeral sandbox
  ↓
Repository checkout
  ↓
Agent task
  ↓
Tests
  ↓
Artifacts + result
  ↓
Ruata
```

Cloud execution should be preferred when:

- The task does not require the local VS Code state.
- The task is resource-intensive.
- The task benefits from isolation.
- The task should run unattended.
- A reproducible clean environment is desirable.

Local execution should be preferred when:

- Working on uncommitted local changes.
- Debugging a developer-specific setup.
- Inspecting the active editor/context.
- Accessing a local-only dependency/service.

---

# 19. Approval Model

Use three practical autonomy levels.

## Level 1 — Read

```text
Inspect
Search
Analyze
Research
Run safe read-only commands
```

## Level 2 — Write

```text
Modify code
Write tests
Create migrations in development
Create documentation
```

## Level 3 — Execute/Deploy

```text
Deploy
Change production state
Modify credentials
Perform destructive operations
```

Level 3 should generally require explicit human approval.

### Risk classes

| Risk | Examples | Approval |
|---|---|---|
| Low | Formatting, docs, tests | Agent policy |
| Medium | API changes, schema changes, dependency upgrades | Ruata + Ian; human as configured |
| High | Production DB, secrets, payments, destructive migration | Human mandatory |

---

# 20. Project Memory

Do not rely on model context alone.

Recommended project memory:

```text
.ai/
├── project.md
├── architecture.md
├── conventions.md
├── decisions/
├── research/
├── known-issues/
└── task-state/
```

Memory should be:

- Versioned where appropriate
- Searchable
- Attributable
- Scoped by project
- Scoped by environment
- Protected against unauthorized mutation

---

# 21. Observability

Every run should have a traceable identifier.

```text
run_id
task_id
project_id
agent_role
model
workspace_id
device_id
started_at
finished_at
status
cost/tokens where available
tool_calls
files_changed
tests_run
approvals
errors
```

Dashboard should expose:

- Current agent state
- Task timeline
- Tool-call history
- Files changed
- Test status
- Approvals
- Failures/retries
- Resource usage

Sensitive data must be redacted before logging.

---

# 22. Failure Recovery

Agents and tool invocations can fail. Ruata should handle:

- Tool timeouts
- Connection loss
- Local device offline
- Agent context overflow
- Test failure
- Merge conflict
- Permission denial
- Sandbox destruction
- API rate limits
- Model failure

Retry policy:

```text
Transient tool error
   ↓
Retry with bounded backoff
   ↓
Still failing?
   ↓
Replan / alternate tool
   ↓
Still failing?
   ↓
Escalate to Ruata
   ↓
Human if required
```

Never create infinite autonomous retry loops.

---

# 23. Evaluation System

The platform should continuously evaluate agent quality.

Evaluation categories:

- Task completion
- Correctness
- Regression rate
- Tool-use accuracy
- Security adherence
- Instruction following
- Scope discipline
- Test quality
- Cost/latency

Example evaluation record:

```json
{
  "task_id": "TASK-142",
  "agent": "john",
  "success": true,
  "tests_passed": 42,
  "tests_failed": 0,
  "files_changed": 8,
  "scope_violation": false,
  "security_findings": 0
}
```

---

# 24. Dashboard

The dashboard should provide:

```text
Dashboard
├── Overview
├── Projects
├── Agents
├── Tasks
├── Runs
├── Devices
├── Workspaces
├── Research
├── Decisions
├── Test Reports
├── Approvals
├── Logs
└── Settings
```

Example agent view:

```text
┌─────────────────────────────────────────────┐
│ RUATA AI SOFTWARE ENGINEERING               │
├─────────────────────────────────────────────┤
│ Project: MizoramStay                        │
│                                             │
│ Ruata       ● Working                       │
│ Kimi        ● Researching                   │
│ Manasseh    ● Working                       │
│ John        ● Working                       │
│ Ian         ○ Waiting                       │
│                                             │
│ Current Task: TASK-142                      │
│                                             │
│ [Pause] [Stop] [Approve] [Open VS Code]     │
└─────────────────────────────────────────────┘
```

---

# 25. Data Model

Core entities:

```text
User
Project
Device
Workspace
Agent
Task
TaskDependency
AgentRun
ToolCall
Artifact
Decision
TestRun
ApprovalRequest
Policy
AuditEvent
CredentialReference
```

Relationship example:

```text
User
 ├── Projects
 └── Devices

Project
 ├── Workspaces
 ├── Tasks
 ├── Agents/Runs
 ├── Artifacts
 └── Policies

Task
 ├── Dependencies
 ├── AgentRun
 ├── Artifacts
 ├── TestRuns
 └── ApprovalRequests
```

---

# 26. Suggested Technology Stack

```text
Dashboard
  Next.js + TypeScript

UI
  Tailwind CSS + component library

Cloud API / Control Plane
  FastAPI + Python

Agent Runtime
  OpenAI Agents SDK or compatible orchestration layer

Tool Protocol
  MCP

Database
  PostgreSQL / Supabase

Queue / Eventing
  Redis-compatible queue or managed event service

Realtime
  WebSocket / SSE

Local Bridge
  Python or Node.js

VS Code Extension
  TypeScript + VS Code Extension API

Browser Automation
  Playwright

Source Control
  Git + GitHub

CI/CD
  GitHub Actions

Cloud Web Hosting
  Vercel or equivalent

Cloud compute
  Container/serverless platform appropriate to workload

Secrets
  Managed secret store
```

The exact provider can evolve without changing the agent-role model.

---

# 27. Recommended Repository Structure

```text
ai_agents/
├── AGENTS.md
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
│
├── docs/
│   ├── AI Software Development Agent Team — Architecture & Agent Specifications.md
│   ├── architecture/
│   ├── adr/
│   └── api/
│
├── apps/
│   ├── dashboard/
│   └── api/
│
├── agents/
│   ├── ruata/
│   │   ├── system.md
│   │   ├── workflows/
│   │   └── policies/
│   │
│   ├── kimi/
│   │   ├── system.md
│   │   └── tools/
│   │
│   ├── manasseh/
│   │   ├── system.md
│   │   └── tools/
│   │
│   ├── john/
│   │   ├── system.md
│   │   └── tools/
│   │
│   └── ian/
│       ├── system.md
│       └── tools/
│
├── services/
│   ├── orchestrator/
│   ├── task-engine/
│   ├── policy-engine/
│   ├── agent-runtime/
│   ├── memory-service/
│   ├── audit-service/
│   └── evaluation-service/
│
├── packages/
│   ├── schemas/
│   ├── shared-types/
│   ├── prompt-templates/
│   └── tool-sdk/
│
├── local/
│   ├── bridge/
│   ├── workspace-manager/
│   └── permissions/
│
├── vscode-extension/
│   ├── src/
│   ├── package.json
│   └── README.md
│
├── infra/
│   ├── docker/
│   ├── deployment/
│   └── migrations/
│
├── evaluations/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── security/
│
└── scripts/
```

---

# 28. Example Agent Interaction

User request:

> Add booking cancellation to MizoramStay.

Ruata:

```text
1. Inspect project
2. Inspect Git state
3. Inspect architecture and policies
4. Determine research need
```

Kimi:

```text
Research cancellation rules
Design state transitions
Produce ADR
Produce API contract
```

John:

```text
Implement schema changes
Implement server-side rules
Implement cancellation API
Add backend tests
```

Manasseh:

```text
Implement cancellation UI
Consume approved API contract
Add frontend tests
```

Ian:

```text
Run static checks
Run unit/integration tests
Run security checks
Run E2E/regression tests
```

Ruata:

```text
Review all artifacts
Confirm Definition of Done
Request human approval where required
Finalize run
```

---

# 29. Example Local Execution Sequence

```text
Dashboard
   │
   ▼
Ruata creates TASK-142
   │
   ▼
Cloud task queue
   │
   ▼
Local device online
   │
   ▼
Local Bridge receives signed task
   │
   ▼
Policy validation
   │
   ▼
Workspace selected
   │
   ▼
Agent tool execution
   │
   ├── filesystem
   ├── terminal
   ├── git
   ├── VS Code API
   └── browser
   │
   ▼
Results + artifacts
   │
   ▼
Cloud control plane
   │
   ▼
Ruata
```

---

# 30. Security Architecture

Security layers:

```text
Identity
  ↓
Device trust
  ↓
Project/workspace authorization
  ↓
Agent capability policy
  ↓
Tool authorization
  ↓
Filesystem restrictions
  ↓
Command restrictions
  ↓
Approval gates
  ↓
Audit trail
```

Additional controls:

- Short-lived access tokens
- Credential references rather than raw secrets
- Secret redaction
- TLS everywhere in transit
- Encryption at rest for sensitive state
- Signed task instructions where practical
- Local bridge authentication
- Device revocation
- Session expiration
- Rate limits
- Tool allowlists
- Command deny/allow policies
- Human kill switch

---

# 31. Emergency Controls

The dashboard and local bridge should support:

```text
STOP ALL AGENTS
DISABLE DEVICE
DISABLE PROJECT
REVOKE SESSION
BLOCK TOOL
PAUSE QUEUE
```

A local emergency stop should immediately prevent further agent tool execution until re-enabled.

---

# 32. Main-Only Change Workflow for This Repository

For `drmaruata/ai_agents`, every implementation cycle should follow:

```text
Inspect main
   ↓
Plan
   ↓
Implement locally / through controlled execution
   ↓
Run checks
   ↓
Review diff
   ↓
Commit to main
   ↓
Push main
   ↓
Verify remote state
```

The automation layer should enforce:

```text
if repository == "drmaruata/ai_agents" and target_branch != "main":
    deny_write
```

No normal PR workflow is required for this repository under the requested policy.

---

# 33. Implementation Roadmap

## Phase 1 — Repository and contracts

- Repository scaffold
- `AGENTS.md`
- Architecture specification
- Shared schemas
- Configuration model
- Task model
- Event model

## Phase 2 — Cloud control plane

- Authentication
- Project registry
- Device registry
- Task service
- Agent registry
- Orchestrator service
- Dashboard MVP

## Phase 3 — Local execution

- Local bridge
- Secure outbound connection
- Device registration
- Workspace registration
- Filesystem tool
- Terminal tool
- Git tool

## Phase 4 — VS Code extension

- Extension shell
- Status panel
- Workspace binding
- Agent activity
- Approval prompts
- Editor context tools

## Phase 5 — Specialist agents

- Ruata
- Kimi
- Manasseh
- John
- Ian

## Phase 6 — Validation and security

- CI integration
- Test orchestration
- Security scanning
- Evaluation framework
- Audit logging
- Emergency controls

## Phase 7 — Cloud sandboxes and scale

- Ephemeral workspaces
- Multi-device support
- Parallel agent execution
- Resource scheduling
- Cost/latency controls

---

# 34. Initial MVP Acceptance Criteria

The first MVP should be considered successful when:

1. A user can sign into the dashboard.
2. A local computer can be registered securely.
3. A VS Code workspace can be registered.
4. Ruata can create a task.
5. Ruata can assign a task to one specialist agent.
6. The local bridge can execute an approved file/terminal operation.
7. Agent actions appear in the dashboard.
8. Ian can run the project's automated checks.
9. Failed checks return the task to a repair state.
10. High-risk operations trigger human approval.
11. The repository policy prevents writes to branches other than `main` for `drmaruata/ai_agents`.
12. All platform changes can be committed and pushed to `main` with an auditable commit history.

---

# 35. Long-Term Vision

The platform should evolve from five fixed agents into a role-based engineering workforce.

Conceptually:

```text
                      RUATA
                        │
             ┌──────────┼──────────┐
             │          │          │
             ▼          ▼          ▼
           KIMI      MANASSEH     JOHN
             │          │          │
             └──────────┼──────────┘
                        ▼
                       IAN
```

Operationally, Ruata may create multiple concurrent workers:

```text
Kimi-1     Kimi-2
Manasseh-1 Manasseh-2
John-1
Ian-1      Ian-2
```

The roles are stable; worker instances are elastic.

The resulting system is a **software engineering agent platform**, not simply five chatbots. It can progressively support multiple projects, devices, cloud sandboxes, models, tool servers, and engineering workflows while retaining explicit boundaries and human control.

---

# 36. Operational Rules Summary

```text
1. Ruata owns orchestration.
2. Kimi owns research and architecture decisions.
3. Manasseh owns frontend implementation.
4. John owns backend/data implementation.
5. Ian owns verification, security and reliability.
6. Agents communicate through structured artifacts.
7. Local execution is mediated by the Local Agent Bridge.
8. VS Code is integrated through an extension/API, not GUI automation.
9. Cloud services never require unrestricted inbound access to the developer PC.
10. Agent permissions follow least privilege.
11. High-risk operations require human approval.
12. Tests and security checks are mandatory quality gates.
13. Project knowledge is persisted under .ai/.
14. Every run is observable and auditable.
15. This repository uses main-only development.
```

---

# 37. References and Current-Practice Basis

This architecture is informed by current agentic software-development patterns including specialized agents/subagents, sandboxed execution, repository-local instructions, tool integration, MCP, evaluation-driven workflows, and human approval/oversight.

Primary implementation references to keep current as the platform evolves include:

- OpenAI Agents SDK and coding-agent architecture documentation
- OpenAI Codex / sandboxing and secure execution guidance
- Anthropic agentic coding and evaluation guidance
- Model Context Protocol specifications
- Visual Studio Code agent, MCP, and Language Model Tools documentation
- GitHub repository, Actions, and Git data APIs

Because agent platforms and tool specifications change quickly, implementation-specific API choices should be revalidated against current official documentation before each major platform release.

---

# 38. Repository Policy Notice

**This project intentionally uses `main` as its sole development branch.**

Future updates to this repository should:

- target `main` directly,
- preserve the architecture and security invariants unless intentionally revised,
- update this specification when implementation decisions materially change the architecture, and
- maintain an auditable commit history.
