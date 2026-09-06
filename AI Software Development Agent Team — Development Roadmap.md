# AI Software Development Agent Team — Development Roadmap

**Repository:** `drmaruata/ai_agents`  
**Development branch:** `main` only  
**Target:** Production-grade hybrid cloud + local AI software engineering platform  
**Roadmap version:** 1.0  
**Status:** Implementation roadmap

---

## 1. Purpose

This document defines the phased development plan for the **Ruata AI Software Development Platform**: a controlled, role-based AI software engineering team consisting of Ruata, Kimi, Manasseh, John, and Ian.

The platform is designed to let a developer submit software-development work through an Agents Dashboard while specialist agents plan, research, implement, test, review, and validate changes. A secure Local Agent Bridge provides controlled access to the developer's workstation, VS Code workspace, terminal, Git repository, browser, and other approved development tools. Cloud sandboxes can be added for isolated or long-running work.

The roadmap deliberately separates **control**, **intelligence**, and **execution** so model providers, local tooling, and cloud infrastructure can evolve independently.

---

## 2. Target Architecture

```text
                         YOU
                          |
                          v
                +----------------------+
                |    Agents Dashboard  |
                |       Web App        |
                +----------+-----------+
                           |
                           v
                +----------------------+
                |   Cloud Control Plane |
                |                       |
                | Ruata Orchestrator    |
                | Task / Run Engine     |
                | Policy Engine         |
                | Agent Registry        |
                | Memory / Artifacts    |
                | Approval / Audit      |
                +----------+------------+
                           |
              +------------+-------------+
              |                          |
              v                          v
      +----------------+        +------------------+
      | Local Execution |        | Cloud Sandbox    |
      |                |        |                  |
      | Local Bridge   |        | Isolated Agent   |
      | VS Code        |        | Workspace        |
      | Terminal       |        | GitHub           |
      | Git            |        | CI / Heavy Tests |
      | Browser        |        +------------------+
      +-------+--------+
              |
              v
        Developer Projects
```

### Agent topology

```text
                        RUATA
             Principal Engineering Orchestrator
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
           KIMI        MANASSEH        JOHN
     Research &        Frontend       Backend &
      Architecture     Engineer       Data Engineer
             |             |             |
             +-------------+-------------+
                           |
                           v
                         IAN
              QA / Security / Reliability
```

---

# 3. Guiding Engineering Principles

1. **Build the platform before maximizing agent autonomy.** Reliable state, tools, permissions, and execution boundaries come before advanced orchestration.
2. **Use role-based agents, not five unrestricted chatbots.** Each agent receives a bounded mission, tool set, and permission scope.
3. **Communicate through structured artifacts.** Prefer task specifications, ADRs, API contracts, test reports, and machine-readable events over long agent-to-agent conversations.
4. **Parallelize only independent work.** Ruata should create a dependency-aware task graph and use concurrency where it is safe.
5. **Make completion evidence-based.** A task is not complete because an agent says it is complete; required validation gates must pass.
6. **Least privilege by default.** Local execution, secrets, production systems, destructive operations, and high-risk tool calls are policy-controlled.
7. **Human approval for consequential changes.** High-risk and production actions should not be silently autonomous.
8. **Git is a safety boundary.** Use isolated worktrees or equivalent workspace isolation where simultaneous agent changes could conflict.
9. **Evaluation is continuous.** Each agent and the end-to-end system require repeatable evaluation suites.
10. **Main-only repository policy.** This repository uses direct commits to `main`; do not create feature branches or routine pull requests unless the policy is explicitly changed.

---

# 4. Phase 0 — Architecture and Repository Baseline

## Objective

Make the repository internally consistent and usable as the source of truth for the platform.

## Tasks

- Normalize repository layout and naming.
- Keep the canonical architecture specification current.
- Maintain root `AGENTS.md` as the repository engineering contract.
- Document development commands and environment variables.
- Establish coding, testing, security, and Git conventions.
- Verify that the scaffold can be cloned and understood without hidden context.

## Expected structure

```text
AGENTS.md
README.md
pyproject.toml
.env.example

agents/
services/
packages/
local/
vscode-extension/
apps/
infra/
evaluations/
tests/
docs/
```

## Deliverables

- Repository baseline.
- Canonical architecture specification.
- Engineering rules.
- Initial developer documentation.

## Acceptance gate

A clean clone on `main` can be installed, inspected, and understood by a developer using only repository documentation.

---

# 5. Phase 1 — Core Domain Model

## Objective

Define the platform's core entities independently of any model provider.

## Core entities

```text
User
Device
Workspace
Project
Agent
Task
TaskDependency
TaskRun
Execution
Tool
ToolPermission
Approval
Artifact
AgentMessage
TestRun
Evaluation
AuditEvent
```

## Task state machine

```text
BACKLOG
  |
  v
ANALYZING
  |
  v
PLANNED
  |
  v
IMPLEMENTING
  |
  v
VALIDATING
  +------> REPAIR ------+
  |                     |
  +---------------------+
  |
  v
REVIEW
  |
  v
HUMAN_APPROVAL
  |
  +-----> COMPLETED

Failure/blocking states:
FAILED
BLOCKED
```

## Tasks

- Move domain types into shared packages.
- Define state transition rules.
- Define task dependency semantics.
- Define idempotency rules.
- Define event schemas.
- Define artifact metadata and lifecycle.

## Acceptance gate

Tasks can be created, queried, and transitioned through valid states without an LLM or external model dependency.

---

# 6. Phase 2 — Persistent Control Plane

## Objective

Replace prototype in-memory state with durable storage.

The current API scaffold keeps tasks in memory; this phase replaces that prototype with PostgreSQL/Supabase-backed persistence.

## Components

```text
PostgreSQL / Supabase
  |
  +-- users
  +-- devices
  +-- workspaces
  +-- projects
  +-- agents
  +-- tasks
  +-- task_dependencies
  +-- task_runs
  +-- executions
  +-- artifacts
  +-- approvals
  +-- audit_events
  +-- evaluations
```

## Tasks

- Implement migrations.
- Add foreign keys and constraints.
- Add indexes for task and event queries.
- Store timestamps and state history.
- Add optimistic concurrency/versioning where required.
- Make state-changing APIs idempotent.
- Persist task and run history.

## Acceptance gate

Restarting the control-plane service does not lose task, execution, approval, or audit state.

---

# 7. Phase 3 — Authentication, Identity, and Device Registration

## Objective

Establish secure identity for users, devices, projects, and workspaces.

## Build

```text
User authentication
      |
      v
Session / access token
      |
      v
Device registration
      |
      v
Workspace registration
      |
      v
Authorized execution
```

## Device model

```text
device_id
device_name
platform
hostname
vs_code_version
bridge_version
status
last_seen
created_at
```

## Enrollment flow

```text
Dashboard
   |
   v
Generate pairing code
   |
   v
Local Bridge
   |
   v
Complete enrollment
   |
   v
Issue scoped device credential
   |
   v
Device registered
```

## Acceptance gate

Only authenticated, registered devices with an authorized workspace can execute local tasks.

---

# 8. Phase 4 — Local Agent Bridge

## Objective

Create the secure workstation-side runtime that lets cloud orchestration reach selected local development resources without exposing the workstation as an unrestricted public server.

## Responsibilities

- Maintain authenticated outbound connectivity.
- Register device and workspaces.
- Enforce task/project/workspace/agent/tool permissions.
- Execute approved local actions.
- Return structured results.
- Emit audit events.
- Fail closed on ambiguous authorization.

## Initial tool surface

```text
workspace.list
workspace.info
file.read
file.write
file.patch
git.status
git.diff
git.branch
git.worktree
terminal.run
test.run
```

## Later tool surface

```text
browser.open
browser.click
browser.type
playwright.run
docker.run
database.query
vscode.get_active_file
vscode.get_diagnostics
vscode.open_file
vscode.apply_edit
```

## Transport

```text
Local Bridge
    |
    | outbound TLS/WebSocket or equivalent authenticated channel
    v
Cloud Control Plane
```

Do not expose an arbitrary inbound public port on the developer workstation.

## Acceptance gate

Ruata can request a safe action such as reading a selected project file or running a permitted test command, receive a structured result, and record the action in the audit trail.

---

# 9. Phase 5 — Permission and Policy Engine

## Objective

Make every agent action subject to explicit authorization.

## Permission dimensions

```text
Agent
Project
Workspace
Tool
Path
Command
Network target
Environment
Risk level
```

## Risk levels

```text
LOW
MEDIUM
HIGH
CRITICAL
```

## Example policy

```yaml
agent: manasseh

filesystem:
  read:
    - frontend/**
    - shared/**
  write:
    - frontend/**
    - tests/frontend/**

commands:
  allow:
    - npm
    - pnpm
    - npx

production:
  allowed: false
```

## Approval model

```text
LOW       -> automatic
MEDIUM    -> policy + validation
HIGH      -> human approval
CRITICAL  -> explicit human approval
```

## Acceptance gate

Every tool execution is authorized before it runs, and unauthorized operations are rejected with an auditable reason.

---

# 10. Phase 6 — Tool and MCP Layer

## Objective

Provide a reusable, standardized tool surface to all agents.

## Tool gateway

```text
packages/tools/
services/tool_gateway/
```

## Tool families

```text
Filesystem
Git
GitHub
Terminal
Browser
Playwright
PostgreSQL
Supabase
Documentation
Search
CI/CD
Observability
```

## Local tools

```text
Filesystem
Terminal
Git
VS Code
Browser
Docker
```

## Remote tools

```text
GitHub
Supabase
Cloud services
Issue trackers
Documentation/search
CI systems
```

## MCP strategy

Use MCP where it reduces integration duplication and provides a standard tool boundary. Agent-specific code should depend on shared tool contracts rather than embedding service-specific integration logic.

## Acceptance gate

A tool can be registered, discovered, permission-checked, executed, timed out/cancelled where appropriate, and audited without custom code inside every agent.

---

# 11. Phase 7 — Ruata Orchestrator

## Objective

Turn Ruata into the intelligent control layer that translates user intent into safe, dependency-aware execution.

## Ruata loop

```text
USER REQUEST
    |
    v
UNDERSTAND
    |
    v
INSPECT PROJECT
    |
    v
CLASSIFY TASK
    |
    +---- research required? ---- yes --> KIMI
    |
    v
PLAN
    |
    v
DECOMPOSE
    |
    v
TASK GRAPH
    |
    v
ASSIGN
    |
    v
EXECUTE
    |
    v
VALIDATE
    |
    +---- fail ----> REPAIR
    |
    v
REVIEW
    |
    v
APPROVAL
    |
    v
COMPLETE
```

## Ruata responsibilities

- Understand requirements.
- Inspect repository instructions and Git state.
- Determine scope and risks.
- Invoke research when needed.
- Create dependency-aware task graphs.
- Assign work to specialist agents.
- Parallelize independent tasks.
- Track progress and artifacts.
- Route validation failures back to the appropriate agent.
- Enforce policies and approval gates.
- Produce final execution summaries.

## Non-goals

Ruata should not become the default implementation agent. It coordinates work and only performs limited control-plane operations.

## Acceptance gate

Given a representative feature request, Ruata creates a correct task graph, assigns the appropriate specialist agents, tracks dependencies, and stops/retries according to policy without requiring hand-written orchestration for every feature.

---

# 12. Phase 8 — Kimi: Research and Architecture Agent

## Objective

Turn uncertain technical questions into trustworthy implementation guidance.

## Kimi workflow

```text
Question
   |
   v
Repository inspection
   |
   v
Documentation research
   |
   v
Technology research
   |
   v
Alternative evaluation
   |
   v
Architecture proposal
   |
   v
ADR / decision record
   |
   v
Implementation specification
```

## Kimi outputs

```text
research.md
architecture.md
ADR-xxx.md
implementation-plan.md
api-contract.yaml
risk-assessment.md
```

## Constraints

- Prefer primary documentation and authoritative sources.
- Record uncertainty explicitly.
- Do not silently invent unsupported APIs or behavior.
- Do not modify application source code by default.

## Acceptance gate

Representative research and architecture tasks are evaluated for technical accuracy, evidence quality, completeness, and usefulness to implementation agents.

---

# 13. Phase 9 — John: Backend and Data Engineer

## Objective

Implement backend functionality from approved specifications and contracts.

## Scope

```text
API
Database
Authentication
Authorization
Business logic
RLS
Migrations
Transactions
Caching
External integrations
Background jobs
Observability
Backend tests
```

## Workflow

```text
Specification
    |
    v
Inspect backend/database
    |
    v
Implementation plan
    |
    v
Migration
    |
    v
Backend implementation
    |
    v
API contract
    |
    v
Unit/integration tests
    |
    v
Static validation
```

## Acceptance gate

John cannot declare success from a passing build alone. Required checks include relevant type checking, linting, unit tests, integration tests, migration validation, contract validation, and security checks.

---

# 14. Phase 10 — Manasseh: Frontend Engineer

## Objective

Implement production-quality frontend experiences against approved API and architecture contracts.

## Scope

```text
React / Next.js
Components
Layouts
Forms
State
Hooks
API integration
Accessibility
Responsive design
Loading/error/empty states
Frontend tests
Browser/E2E preparation
```

## Workflow

```text
Specification
    |
    v
Design/system inspection
    |
    v
Component reuse analysis
    |
    v
Implementation
    |
    v
Browser validation
    |
    v
Accessibility validation
    |
    v
Frontend tests
```

## Constraints

- Consume agreed backend contracts.
- Avoid inventing backend behavior.
- Preserve established design-system conventions where possible.
- Keep frontend changes scoped to the assigned task.

## Acceptance gate

A representative feature behaves correctly in browser validation across required viewport sizes and states, and required frontend tests pass.

---

# 15. Phase 11 — Ian: Quality, Security, and Reliability Engineer

## Objective

Make quality an executable gate rather than a final subjective review.

## Validation layers

```text
Static analysis
    |
Unit tests
    |
Integration tests
    |
E2E tests
    |
Security checks
    |
Dependency audit
    |
Build validation
    |
Regression tests
```

## Ian responsibilities

- Detect regressions.
- Review test adequacy.
- Validate application behavior.
- Perform security-oriented checks.
- Report reproducible failures.
- Verify that agents did not weaken quality controls.
- Recommend repair, approval, or completion.

## Structured result

```json
{
  "status": "failed",
  "checks": [
    {"name": "unit-tests", "status": "passed"},
    {"name": "e2e", "status": "failed", "severity": "high"}
  ],
  "recommendation": "repair"
}
```

## Repair loop

```text
Implementation Agent
        |
        v
       Ian
        |
      FAIL
        |
        v
      Ruata
        |
        v
Targeted repair
        |
        v
       Ian
```

## Acceptance gate

Ian reliably detects seeded defects and meaningful regressions without producing excessive false positives.

---

# 16. Phase 12 — VS Code Extension

## Objective

Provide a native developer experience for the local execution system.

## Responsibilities

- Display Ruata/agent status.
- Display current task and workspace.
- Show approvals and tool requests.
- Open affected files.
- Show diffs.
- Surface diagnostics and test failures.
- Provide pause/stop controls.
- Expose editor context through approved tools.

## Suggested tool surface

```text
get_current_file
get_open_files
get_workspace
get_selection
get_diagnostics
get_terminal_output
get_git_status
open_file
apply_edit
create_file
run_task
```

## Architecture

```text
Cloud Agent Runtime
       |
       v
Control Plane
       |
       v
Local Agent Bridge
       |
       v
VS Code Extension
       |
       +-- editor context
       +-- diagnostics
       +-- terminal
       +-- Git
       +-- tests
       +-- browser tooling
```

## Acceptance gate

A user can open VS Code, select a registered workspace, observe agent activity, inspect a proposed change, and approve/stop relevant actions without leaving the editor.

---

# 17. Phase 13 — Agents Dashboard

## Objective

Provide a centralized user interface for projects, agents, tasks, runs, approvals, and observability.

## Primary screens

```text
Dashboard
Projects
Devices
Agents
Tasks
Runs
Artifacts
Research
Architecture Decisions
Approvals
Evaluations
Audit Log
Settings
```

## Project view

The dashboard should expose:

- Current project and workspace.
- Agent statuses.
- Active tasks.
- Progress by task.
- Validation state.
- Pending approvals.
- Recent diffs and artifacts.
- Execution history.

## Acceptance gate

A user can create a task, monitor execution, inspect evidence, respond to approval requests, and understand why a task is blocked or completed.

---

# 18. Phase 14 — Git and Worktree Orchestration

## Objective

Prevent concurrent agents from corrupting or overwriting one another's work.

## Recommended model

```text
main
 |
 +-- task-100-john worktree
 |
 +-- task-100-manasseh worktree
 |
 +-- task-100-ian validation workspace
```

## Ruata controls

- Workspace assignment.
- File-scope constraints.
- Branch/worktree lifecycle.
- Integration order.
- Conflict detection.
- Cleanup after completion.

## Acceptance gate

Two independent implementation tasks can run concurrently without uncontrolled shared-working-tree collisions.

---

# 19. Phase 15 — CI/CD Integration

## Objective

Combine local validation with authoritative CI validation.

## Pipeline

```text
Agent change
    |
    v
Local validation
    |
    v
Git diff review
    |
    v
CI
    |
    +-- unit
    +-- integration
    +-- E2E
    +-- security
    +-- build
    |
    v
Ian / Ruata
    |
    v
Approval / release decision
```

## Rules

- Local success is not equivalent to CI success.
- CI results become part of task evidence.
- Failed CI checks create repair work rather than silent completion.

## Acceptance gate

A real repository change can be validated locally and through CI, and the resulting evidence is visible to Ruata and Ian.

---

# 20. Phase 16 — Cloud Sandbox Execution

## Objective

Add isolated remote execution for long-running, heavy, parallel, or potentially untrusted workloads.

## Execution modes

```text
                   RUATA
                     |
             +-------+-------+
             |               |
             v               v
        Local Bridge      Cloud Sandbox
             |               |
          VS Code          GitHub
             |               |
             +-------+-------+
                     |
                     v
                    Ian
```

## Use local execution for

- Active developer workspace.
- Uncommitted code.
- Local services.
- Interactive debugging.
- VS Code context.

## Use cloud execution for

- Long-running work.
- Isolated builds.
- Large test suites.
- Parallel experimentation.
- CI reproduction.
- Untrusted repositories.

## Acceptance gate

Ruata can select local or cloud execution according to policy, task requirements, and workspace availability while preserving equivalent task/audit semantics.

---

# 21. Phase 17 — Evaluation Framework

## Objective

Make agent quality measurable and regression-testable.

## Structure

```text
evaluations/
├── ruata/
├── kimi/
├── manasseh/
├── john/
├── ian/
└── system/
```

## Evaluate Ruata

```text
task decomposition
routing
dependency detection
parallelization
policy compliance
recovery
```

## Evaluate Kimi

```text
research quality
technical accuracy
source quality
architecture quality
decision usefulness
```

## Evaluate John

```text
correctness
security
API compliance
database correctness
test quality
```

## Evaluate Manasseh

```text
visual correctness
responsive behavior
accessibility
component reuse
frontend test coverage
```

## Evaluate Ian

```text
bug detection
security detection
regression detection
false-positive rate
coverage
```

## System-level evaluation

Measure:

```text
task success rate
human intervention rate
repair success rate
policy violations
mean time to completion
cost per successful task
regression rate
```

## Acceptance gate

A representative benchmark suite runs automatically and fails the build when agent performance regresses beyond defined thresholds.

---

# 22. Phase 18 — Observability

## Objective

Provide full traceability for agent behavior, tool usage, cost, and failures.

## Capture

```text
agent
task
run
model
provider
tool
input/output metadata
latency
tokens/cost
retries
errors
approvals
policy decisions
test results
```

## Trace example

```text
TASK-8432
   |
   +-- Ruata run
   |     +-- Kimi
   |     +-- John
   |     +-- Manasseh
   |
   +-- Ian
   |
   +-- CI
```

## Acceptance gate

For any completed or failed task, the operator can reconstruct what happened, which tools were invoked, which agents participated, and why the final status was reached.

---

# 23. Phase 19 — Security Hardening

## Threat model

Explicitly test for:

```text
prompt injection
malicious repository content
secret exfiltration
command injection
workspace escape
credential theft
agent privilege escalation
unsafe tool/MCP behavior
supply-chain attacks
data leakage
```

## Controls

```text
sandboxing
least privilege
credential isolation
secret redaction
path allowlists
command allowlists
network restrictions
tool scopes
approval gates
audit logging
timeouts
resource limits
rate limits
kill switch
```

## Acceptance gate

Security tests demonstrate that an agent cannot escape its assigned workspace/tool scope or silently perform a high-risk action without authorization.

---

# 24. Phase 20 — Production Deployment

## Recommended deployment topology

```text
                     Cloudflare / Edge
                            |
                            v
                         Vercel
                            |
                       Dashboard
                            |
                            v
                         API Layer
                            |
                +-----------+-----------+
                |           |           |
                v           v           v
             Postgres     Redis      Object Store
                |
                v
          Agent Runtime
                |
         +------+------+
         |             |
         v             v
   Local Bridges   Cloud Sandboxes
```

## Production components

```text
Dashboard
API / control plane
Agent runtime
Task queue
Database
Realtime transport
Tool gateway
Object storage
Observability
Secrets management
CI/CD
Cloud sandbox runtime
Local bridge distribution
VS Code extension
```

## Acceptance gate

The production platform has reproducible deployment, secure secrets, monitoring, backup/recovery, controlled rollouts, and documented operator procedures.

---

# 25. Phase 21 — First Real End-to-End Project

## Objective

Prove that the platform can deliver a substantial real feature rather than merely demonstrate isolated agent capabilities.

## Recommended benchmark

A complete CRUD-style feature that includes:

```text
database
API
authentication/authorization
frontend
validation
unit tests
integration tests
E2E tests
documentation
```

## Expected workflow

```text
"Build feature X"
      |
      v
Requirement understanding
      |
      v
Architecture/research
      |
      v
Task graph
      |
      +--------+--------+
      |                 |
      v                 v
     John           Manasseh
      |                 |
      +--------+--------+
               |
               v
              Ian
               |
               v
          Security/CI
               |
               v
          Human approval
               |
               v
             Commit
               |
               v
        Development report
```

## Acceptance gate

A real feature can move from a natural-language request to validated code and an auditable final result with limited human intervention.

---

# 26. Milestone Plan

## Milestone A — Foundation

```text
Phase 0
Phase 1
Phase 2
Phase 3
```

### Outcome

Reliable persistent cloud control plane with identity and device registration.

---

## Milestone B — Local Execution

```text
Phase 4
Phase 5
```

### Outcome

Secure cloud-to-workstation execution with explicit permissions.

---

## Milestone C — Tools and Integrations

```text
Phase 6
```

### Outcome

Reusable MCP/tool infrastructure.

---

## Milestone D — Intelligent Orchestration

```text
Phase 7
Phase 8
```

### Outcome

Ruata + Kimi can understand requirements, research, plan, and produce execution-ready task graphs.

---

## Milestone E — AI Coding Team

```text
Phase 9
Phase 10
Phase 11
```

### Outcome

John + Manasseh + Ian complete backend, frontend, and validation workflows.

---

## Milestone F — Developer Experience

```text
Phase 12
Phase 13
Phase 14
Phase 15
```

### Outcome

Usable Dashboard + VS Code + Git/worktree + CI/CD experience.

---

## Milestone G — Production Platform

```text
Phase 16
Phase 17
Phase 18
Phase 19
Phase 20
Phase 21
```

### Outcome

Production-grade AI software engineering platform with local and cloud execution.

---

# 27. Recommended Implementation Order

Do not implement all five agents simultaneously.

The recommended order is:

```text
1. Repository / architecture baseline
2. Domain schemas
3. Persistent task/control-plane storage
4. Authentication
5. Device registration
6. Local Agent Bridge
7. Secure transport
8. Workspace registration
9. Permission engine
10. Filesystem / terminal / Git tools
11. Basic task execution
12. Ruata orchestrator
13. Kimi research/architecture agent
14. John backend agent
15. Manasseh frontend agent
16. Ian QA/security agent
17. VS Code extension
18. Agents Dashboard
19. Git/worktree orchestration
20. CI/CD integration
21. Cloud sandboxes
22. Evaluation framework expansion
23. Observability hardening
24. Security hardening
25. Production deployment
26. First complete end-to-end benchmark
```

This ordering minimizes the risk of creating sophisticated agents that lack reliable execution infrastructure.

---

# 28. Version Roadmap

## v0.1 — Foundation

```text
Control plane
Database
Authentication
Tasks
Devices
Local Bridge scaffold
Basic tool contracts
```

## v0.2 — Ruata

```text
Task planning
Delegation
Task graph
State machine
Policy integration
```

## v0.3 — Kimi

```text
Research
Architecture
ADR
Specifications
```

## v0.4 — John

```text
Backend implementation
Database
API
Backend tests
```

## v0.5 — Manasseh

```text
Frontend implementation
UI
Browser validation
Frontend tests
```

## v0.6 — Ian

```text
QA
E2E
Security checks
Regression
```

## v0.7 — Developer Experience

```text
Dashboard
VS Code extension
Git/worktrees
Approvals
```

## v0.8 — Production Infrastructure

```text
Cloud sandbox
Observability
Evaluations
Security hardening
CI/CD
```

## v1.0 — AI Software Engineering Platform

The system can accept real software-development work, coordinate the five-agent team, execute locally or in cloud sandboxes, validate changes, enforce policy, and provide a complete audit trail with human approval for consequential actions.

---

# 29. Definition of Done for v1.0

A v1.0 task is considered successful only when the platform can, where appropriate:

```text
[ ] Detect the correct project/workspace
[ ] Inspect repository instructions
[ ] Understand requirements
[ ] Research when required
[ ] Create an architecture/specification
[ ] Generate a dependency-aware task graph
[ ] Delegate work to the correct agents
[ ] Execute approved work locally or remotely
[ ] Preserve workspace isolation
[ ] Run type/lint/static checks
[ ] Run unit tests
[ ] Run integration tests
[ ] Run E2E tests when applicable
[ ] Perform security checks
[ ] Detect failures
[ ] Perform targeted repairs
[ ] Re-run validation
[ ] Produce a reviewable Git diff
[ ] Request human approval for high-risk actions
[ ] Commit approved changes
[ ] Record task/run/tool/audit history
[ ] Produce a final development report
```

---

# 30. First Development Sprint

The first sprint should focus on platform foundations rather than advanced agent prompts.

## Sprint scope

```text
1. Finalize repository conventions
2. Finalize shared schemas
3. Implement persistent task storage
4. Implement device registration
5. Implement authenticated bridge transport
6. Implement workspace registration
7. Implement authorization/policy checks
8. Implement filesystem read/write tools
9. Implement terminal tool with allowlists
10. Implement Git status/diff tools
11. Implement structured execution events
12. Implement the first end-to-end safe local task
```

## Sprint success condition

The following workflow must work:

```text
Open Dashboard
     |
     v
Register computer
     |
     v
Register project/workspace
     |
     v
Create task
     |
     v
Ruata receives task
     |
     v
Ruata inspects project
     |
     v
Safe local tool action
     |
     v
Structured result
     |
     v
Audit event
```

Only after this flow is stable should the first LLM-backed specialist agent be introduced.

---

# 31. Long-Term Platform Principles

## Control plane, intelligence, and execution must remain separate

```text
LAYER 1 — CONTROL
Ruata
Task state
Policies
Approvals
Memory
Audit
Orchestration

LAYER 2 — INTELLIGENCE
Kimi
John
Manasseh
Ian
Model providers

LAYER 3 — EXECUTION
Local Bridge
VS Code
Filesystem
Terminal
Git
Browser
MCP
Cloud Sandbox
```

This separation should allow model providers, local runtimes, and cloud infrastructure to change independently.

## Dynamic agent composition

The named five agents are logical roles, not necessarily five permanently running processes. Ruata may spawn multiple task-scoped workers where independent work exists:

```text
Kimi-1
Kimi-2
John-1
Manasseh-1
Manasseh-2
Ian-1
```

The system should scale worker instances without changing role semantics or security policy.

## Avoid unnecessary multi-agent execution

A trivial task may use only one specialist:

```text
Ruata -> Manasseh -> validation
```

A complex feature may use the full workflow:

```text
Ruata -> Kimi -> John + Manasseh -> Ian
```

Agent count must be driven by dependency, risk, and expected value rather than by a requirement to involve all five agents on every task.

---

# 32. Exit Criteria for the Development Program

The platform is ready for serious daily use when:

1. The dashboard is stable and authenticated.
2. Devices and workspaces are securely registered.
3. The local bridge works reliably on the target developer workstation.
4. Tools are permission-controlled and auditable.
5. Ruata can orchestrate real tasks without hard-coded feature-specific workflows.
6. Kimi produces useful, evidence-backed architecture decisions.
7. John and Manasseh can implement production-quality changes.
8. Ian reliably validates and rejects defective changes.
9. Git/worktree isolation prevents cross-agent collisions.
10. CI and local validation are integrated.
11. Evaluation suites prevent silent agent regressions.
12. Security tests demonstrate meaningful isolation and least privilege.
13. The system can complete the benchmark end-to-end project.
14. The platform provides enough observability to debug both agent and infrastructure failures.

---

# 33. Recommended Next Build Target

The immediate implementation target is **Milestone A + Milestone B**:

```text
Persistent Control Plane
        +
Authentication / Device Registration
        +
Local Agent Bridge
        +
Secure Transport
        +
Workspace Management
        +
Permission Engine
        +
Basic Filesystem / Terminal / Git Tools
```

Once those capabilities are stable, implement **Ruata**, then **Kimi**, followed by **John**, **Manasseh**, and **Ian**.

This creates the foundation for an agent fleet that can operate on real software projects while keeping execution bounded, observable, and under developer control.
