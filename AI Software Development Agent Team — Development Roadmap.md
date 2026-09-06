# AI Software Development Agent Team — Development Roadmap

**Repository:** `drmaruata/ai_agents`  
**Development branch:** `main` only  
**Target:** Production-grade hybrid cloud + local AI software engineering platform  
**Roadmap version:** 2.0  
**Status:** Active implementation roadmap  
**Backend direction:** **Supabase-first**

> **Canonical documentation set:** `AI_Software_Development_Agent_Team_Architecture.md` defines the target architecture, this document defines implementation order and acceptance gates, and the root `README.md` defines the practical developer entry point. These documents must remain synchronized.

---

## 0. Architectural Decision — Supabase as Managed Backend Foundation

The platform will use **Supabase as the canonical managed cloud backend foundation**.

Supabase is responsible for:

- PostgreSQL durable application/runtime state
- Supabase Auth for production user identity and session management
- PostgreSQL Row Level Security (RLS) for database-enforced resource authorization
- Realtime for selected live state propagation to dashboard clients
- Storage for appropriate large artifacts/blobs
- bounded Edge Functions for webhooks and lightweight server-side operations

The Python/FastAPI control plane remains responsible for:

- Ruata orchestration
- agent runtime execution
- task scheduling
- policy evaluation
- tool gateway
- approval workflows
- long-running workers
- secure local-bridge connections
- model/provider routing

### Non-negotiable boundaries

```text
Supabase
  = managed identity + database + RLS + realtime + storage + bounded serverless functions

Python Control Plane
  = orchestration + agents + policy + approvals + long-running work

Local Agent Bridge
  = privileged workstation execution

Next.js / VS Code
  = user interfaces and client integration
```

Self-managed PostgreSQL remains optional for local/integration testing. It is **not** the production source of truth.

---

## Implementation Status — 2026-09-06

The roadmap is being executed directly on `main`. The repository currently contains substantial foundations across the early and supporting phases. The Supabase architecture decision now changes the remaining implementation order for persistence and identity: the existing PostgreSQL repository and development JWT foundations should be migrated to the Supabase-first model before declaring those phases complete.

| Phase | Status | Current implementation / next acceptance gate |
|---|---|---|
| 0 | **Complete** | Repository baseline, `AGENTS.md`, architecture, README, environment configuration |
| 1 | **Complete** | Shared domain entities, task state machine, transition validation, tests |
| 2 | **In progress — Supabase migration** | Existing PostgreSQL schema/repository/idempotency/state history foundation exists; migrate canonical production persistence to Supabase, validate restart durability and migration workflow |
| 3 | **In progress — Supabase Auth/RLS** | Device/workspace persistence foundation exists; replace development-only JWT identity path with Supabase Auth, membership model, RLS, authenticated API flow, and authorization tests |
| 4 | **In progress** | Local bridge, outbound WebSocket protocol, scoped filesystem/command execution; integrate authenticated Supabase-backed device/workspace authorization |
| 5 | **In progress** | Agent/tool/path/command/risk policy engine and high-risk approval gate |
| 6 | **In progress** | Shared tool registry and MCP-ready contracts; production MCP/tool integrations remain |
| 7 | **In progress** | Deterministic Ruata planner, task decomposition, specialist routing, orchestration service |
| 8 | **In progress** | Kimi role contract and provider-neutral model runtime; research web/tool execution remains |
| 9 | **Foundation ready** | John agent contract and model runtime; complete Supabase backend coding/toolchain integration |
| 10 | **Foundation ready** | Manasseh agent contract and VS Code/browser foundation; complete Supabase Auth/Realtime-aware frontend workflow |
| 11 | **Foundation ready** | Ian QA contract, validation result model and test fixtures; complete RLS/Auth/security QA pipeline |
| 12 | **In progress** | VS Code extension connects to local bridge and exposes status/start/stop controls |
| 13 | **In progress** | Next.js dashboard connected to control-plane agent/task state; add Supabase Auth/session and Realtime integration |
| 14 | **Foundation ready** | Git worktree manager added; agent worktree lifecycle integration remains |
| 15 | **Foundation ready** | GitHub Actions CI for Python, dashboard, and VS Code extension; add Supabase migration/RLS integration checks where feasible |
| 16 | **Foundation ready** | Sandbox interface and local Docker adapter; cloud sandbox provider integration remains |
| 17 | **Foundation ready** | Ruata planning fixtures and deterministic evaluation runner |
| 18 | **Foundation ready** | Structured observability events; centralized tracing/cost/metrics remains |
| 19 | **Planned** | Threat model and controls defined; dedicated security test suite, including Supabase/RLS/Auth tests, remains |
| 20 | **Planned** | Production deployment topology defined; Supabase project environments, compute deployment, secrets, migrations, backups/operations remain |
| 21 | **Planned** | First real end-to-end benchmark remains the primary v1.0 acceptance test |

**Important:** “Foundation ready” does not mean the phase is production-complete. A phase is complete only when its acceptance gate is demonstrably satisfied in the running system.

---

# 1. Development Principles

The implementation follows these principles:

1. **Supabase-first backend:** use Supabase for production identity, relational persistence, RLS, Realtime, and appropriate Storage/Edge Functions.
2. **Control-plane separation:** keep orchestration, model execution, long-running jobs, policy, approvals, and bridge sessions in trusted compute outside database/serverless primitives that are not suitable for those workloads.
3. **RLS is a security boundary:** user-facing Supabase tables require explicit policies and tests.
4. **Repository abstraction remains:** business logic must not be coupled directly to one client SDK implementation.
5. **Local execution remains isolated:** cloud services send structured requests; the Local Agent Bridge decides whether privileged workstation actions are permitted.
6. **Human approval remains mandatory for consequential operations.**
7. **No secrets in the public repository.**
8. **Acceptance gates must be demonstrated, not inferred from scaffolding.**

---

# 2. Phase 0 — Repository and Documentation Foundation

**Status: Complete**

Deliverables:

- repository structure
- `AGENTS.md`
- canonical architecture specification
- development roadmap
- root README
- environment template
- initial testing conventions

Acceptance:

- repository instructions are explicit
- architecture is documented
- development order is documented
- no secrets are committed

---

# 3. Phase 1 — Shared Domain Model

**Status: Complete**

Deliverables:

- shared domain entities
- task state machine
- validated task transitions
- shared risk model
- device/workspace models
- approval/run/audit models
- deterministic domain tests

Acceptance:

- domain model imports cleanly
- invalid transitions are rejected
- required tests pass

---

# 4. Phase 2 — Supabase Persistence Foundation

**Status: In progress — migration required**

Phase 2 is now explicitly a **Supabase persistence phase**.

## 4.1 Goals

Build durable cloud state using Supabase PostgreSQL and versioned migrations.

## 4.2 Required database domains

At minimum:

```text
profiles
workspace_members
projects
devices
workspaces
agents
agent_versions
tasks
task_dependencies
task_runs
executions
tool_requests
artifacts
approvals
audit_events
task_state_history
idempotency_keys
model_usage
evaluations
```

The exact schema may evolve, but ownership and RLS boundaries must remain explicit.

## 4.3 Deliverables

- canonical SQL migrations under `infra/db/`
- Supabase-compatible schema
- repository/service integration
- optimistic/concurrency-safe task transitions
- durable task/run/audit persistence
- state-history persistence
- idempotency persistence
- migration application procedure
- rollback/recovery documentation
- integration tests against a PostgreSQL-compatible environment

## 4.4 Supabase-specific requirements

- database migrations must be reproducible against the target Supabase project
- production state must not depend on local Docker volumes
- service-role/secret credentials are server-side only
- database functions/triggers must be reviewed for authorization impact
- RLS policies must exist for all browser-accessible application tables
- privileged application operations may execute through trusted control-plane/server-side paths rather than direct browser writes

## 4.5 Phase 2 Acceptance Gate

The phase is complete only when:

```text
1. Apply all migrations to a clean Supabase project.
2. Start the control-plane service against Supabase.
3. Create a project/task/run/approval/audit record.
4. Restart the control-plane service.
5. Reload the records successfully.
6. Verify task version/state history remains intact.
7. Verify idempotent task creation does not duplicate records.
8. Verify unauthorized clients cannot directly read/write protected records.
9. Verify migration/recovery procedure is documented and repeatable.
```

---

# 5. Phase 3 — Supabase Auth, Identity, Device and Workspace Security

**Status: In progress — migration required**

## 5.1 Goals

Replace the development-only identity path with production-grade Supabase Auth and database-enforced resource authorization.

## 5.2 Deliverables

- Supabase Auth configuration
- application `profiles` model linked to Auth users
- workspace membership and roles
- project/workspace authorization model
- persistent device registration
- workspace registration
- authenticated control-plane request verification
- RLS policies
- authorization tests
- device enrollment/revocation
- session expiry/refresh handling

## 5.3 Development compatibility

A development JWT endpoint may remain temporarily for isolated tests, but it must be clearly marked development-only and must not be used by production deployments.

## 5.4 Phase 3 Acceptance Gate

A local device may execute a task only when:

```text
Authenticated user
      ↓
Authorized workspace membership
      ↓
Registered device
      ↓
Authorized task/project
      ↓
Approved operation/policy
      ↓
Local Agent Bridge
```

The acceptance test must prove that an authenticated but unauthorized user, unregistered device, and unauthorized workspace cannot execute local operations.

---

# 6. Phase 4 — Local Agent Bridge

**Status: In progress**

Deliverables:

- outbound WebSocket connection
- device authentication
- workspace scoping
- path restrictions
- command restrictions
- structured request/response protocol
- cancellation
- reconnect behavior
- audit integration

Tools:

```text
file.read
file.write
terminal.run
git.diff
```

Acceptance:

- safe read request succeeds
- approved write request succeeds
- blocked path fails
- blocked command fails
- high-risk action requires approval
- execution event is persisted and attributable to user/device/task

---

# 7. Phase 5 — Policy Engine and Approval Gate

**Status: In progress**

Policy checks must consider:

```text
user
workspace
project
device
agent
task
tool
path
command
risk
approval
```

High/critical actions require human approval.

Supabase-specific high-risk categories include:

- production migration
- destructive SQL
- broad RLS policy change
- production Auth configuration change
- service-role credential operation
- production data deletion
- broad Storage access-policy change

Acceptance:

- every tool execution receives a policy decision
- high-risk operations cannot bypass approval
- decision is auditable

---

# 8. Phase 6 — Tool Registry and MCP Integration

**Status: In progress**

Register tools with explicit metadata:

```text
name
version
agent permissions
input schema
output schema
risk level
approval requirement
scope requirements
execution environment
```

Potential tools:

```text
GitHub
Supabase
PostgreSQL
Browser
Documentation
CI
Observability
Issue tracker
Filesystem
Terminal
```

Local privileged tools remain behind the Local Agent Bridge.

Acceptance:

- tool registered
- tool discovered
- policy evaluated
- authorized execution performed
- execution audited

---

# 9. Phase 7 — Ruata Orchestration

**Status: In progress**

Ruata must:

- parse requirements
- classify work
- decide whether research is needed
- decompose tasks
- assign agents
- order dependencies
- launch independent work in parallel where safe
- monitor execution
- create repair loops
- enforce acceptance gates
- request human approval

Persistent task orchestration state is stored in Supabase.

Acceptance:

- deterministic planning fixtures pass
- correct specialist selected
- dependency ordering is correct
- failed work enters repair/revalidation flow

---

# 10. Phase 8 — Kimi Research and Architecture

**Status: In progress**

Kimi should verify current information from authoritative sources and produce structured research artifacts.

For Supabase-related work Kimi should explicitly verify:

- current Auth behavior
- current RLS capabilities/semantics
- Realtime behavior
- Storage behavior
- Edge Function constraints
- PostgreSQL compatibility
- current SDK/CLI interfaces
- migration implications

Acceptance:

- research package is accurate
- sources are recorded
- decisions include alternatives and trade-offs

---

# 11. Phase 9 — John Backend and Data Engineering

**Status: Foundation ready**

John owns:

- FastAPI/control-plane APIs
- Supabase/PostgreSQL schema
- SQL migrations
- RLS
- Auth integration
- business logic
- integrations
- background jobs
- data-layer tests

Acceptance additions:

```text
[ ] Supabase migrations verified
[ ] RLS policies verified
[ ] Auth boundaries verified
[ ] Service-role usage minimized
[ ] Integration tests pass
```

---

# 12. Phase 10 — Manasseh Frontend Engineering

**Status: Foundation ready**

Manasseh owns:

- Next.js UI
- state management
- forms
- accessibility
- API integration
- Supabase Auth client behavior where appropriate
- Supabase Realtime subscriptions where appropriate
- browser tests

Acceptance additions:

```text
[ ] Auth/session lifecycle verified
[ ] Unauthorized views/actions blocked
[ ] Realtime updates behave correctly
[ ] Loading/error states verified
```

---

# 13. Phase 11 — Ian Quality, Security and Reliability

**Status: Foundation ready**

Ian must verify:

- unit tests
- integration tests
- E2E tests
- RLS/Auth behavior
- secret exposure
- API authorization
- policy bypass attempts
- dependency security
- reliability
- regression safety

Acceptance additions:

```text
[ ] RLS test suite passes
[ ] Auth boundary tests pass
[ ] Privileged credential exposure test passes
[ ] Security regression suite passes
```

---

# 14. Phase 12 — VS Code Integration

**Status: In progress**

Deliverables:

- local node connection
- workspace-aware controls
- device status
- bridge start/stop
- task status
- approval prompts
- emergency disconnect

Authentication must never store privileged Supabase credentials in the extension.

---

# 15. Phase 13 — Agents Dashboard

**Status: In progress**

Dashboard views:

```text
Dashboard
Projects
Agents
Tasks
Runs
Approvals
Devices
Workspaces
Research
Architecture
Artifacts
Logs
Evaluations
Settings
```

Data access model:

```text
Supabase Auth
      ↓
Client session
      ↓
RLS-safe reads / control-plane API
      ↓
Dashboard
```

Realtime should update selected live state without becoming the system of record.

---

# 16. Phase 14 — Agent Workspace Isolation

**Status: Foundation ready**

Use worktrees or sandboxes for agent execution.

Supabase stores task/run/workspace metadata but does not replace filesystem isolation.

---

# 17. Phase 15 — CI/CD

**Status: Foundation ready**

CI should include:

```text
Python tests
Type checks
Lint
Dashboard build
VS Code compile
Security checks
Migration validation
RLS/Auth integration tests where environment permits
```

Production deployment must require all mandatory checks.

---

# 18. Phase 16 — Cloud Sandbox

**Status: Foundation ready**

Cloud sandbox execution must remain isolated from the primary control plane.

Supabase stores sandbox metadata; sandbox compute performs the actual workload.

---

# 19. Phase 17 — Agent Evaluation

**Status: Foundation ready**

Evaluate:

- planning quality
- implementation quality
- tool selection
- policy adherence
- security behavior
- RLS/Auth correctness
- regression behavior
- cost
- time
- human intervention rate

---

# 20. Phase 18 — Observability

**Status: Foundation ready**

Record:

```text
user
workspace
project
task
agent
model
tool
request
approval
Supabase operation metadata where safe
files changed
tests
failures
retries
cost
latency
outcome
```

Never log secrets or raw credential values.

---

# 21. Phase 19 — Security Hardening

**Status: Planned**

Dedicated security testing should cover:

```text
Supabase Auth bypass
RLS bypass
IDOR
privilege escalation
service-role leakage
Storage authorization bypass
unsafe Edge Function exposure
SQL injection
command injection
local bridge abuse
WebSocket session abuse
replay attacks
secret leakage
```

---

# 22. Phase 20 — Production Deployment

**Status: Planned**

Target topology:

```text
Vercel
└── Next.js Dashboard

Supabase
├── Auth
├── PostgreSQL
├── RLS
├── Realtime
├── Storage
└── Edge Functions

Managed Compute
├── Python/FastAPI control plane
├── agent workers
├── background jobs
└── bridge gateway

Developer devices
└── Local Agent Bridge

GitHub
├── Source
└── CI/CD
```

Production requirements:

- separate development/staging/production environments
- secret management
- Supabase migration deployment
- backups/recovery procedure
- monitoring/alerts
- audit retention
- rate limiting
- incident response
- key rotation
- device revocation
- Auth configuration review
- RLS regression testing

---

# 23. Phase 21 — First Real End-to-End Benchmark

**Status: Planned**

Primary benchmark:

```text
User request
 ↓
Supabase Auth
 ↓
Ruata
 ↓
Kimi research (if needed)
 ↓
John / Manasseh implementation
 ↓
Supabase persistence / RLS
 ↓
Ian validation
 ↓
Approval when required
 ↓
Git / CI
 ↓
Local or cloud execution
 ↓
Final artifact + audit trail
```

The benchmark must produce a complete evidence package covering:

- requirements
- task graph
- implementation
- test results
- security results
- Supabase/Auth/RLS evidence
- approvals
- audit events
- Git state
- final outcome

---

# 24. Cross-Phase Acceptance Rules

A phase may not be marked complete solely because code or scaffolding exists.

Completion requires:

```text
Implementation
+ tests
+ security verification
+ operational verification
+ acceptance gate evidence
```

When a phase depends on Supabase, the gate must test the real authorization/persistence behavior rather than only mocked clients.

---

# 25. Canonical Environment Model

The project should use at least:

```text
development
staging
production
```

Each environment should have independently managed:

```text
Supabase project/configuration
Auth configuration
database state
Storage buckets/policies
Realtime configuration
Edge Functions
control-plane compute
secrets
observability
```

Production credentials must never be committed to GitHub.

---

# 26. Recommended Implementation Order From Current State

The next implementation sequence is now:

```text
1. Finalize Supabase database schema/migrations
2. Fix/normalize identity tables and workspace membership
3. Implement Supabase Auth integration
4. Implement and test RLS policies
5. Connect repository layer to Supabase
6. Verify durable task/run/audit/idempotency state
7. Integrate control-plane authentication/authorization
8. Integrate Local Agent Bridge with authenticated device/workspace state
9. Add Supabase Realtime to dashboard
10. Add Supabase Storage for artifacts where appropriate
11. Add bounded Edge Functions where justified
12. Complete tool/MCP integrations
13. Complete Ruata/Kimi/John/Manasseh/Ian workflows
14. Complete security suite and production deployment
15. Run the full end-to-end benchmark
```

Do not increase autonomous execution privileges until persistence, identity, authorization, policy, and audit acceptance gates are demonstrably satisfied.

---

# 27. Definition of v1.0 Done

Version 1.0 is complete only when:

```text
[ ] Supabase production persistence verified
[ ] Supabase Auth verified
[ ] RLS verified
[ ] Device/workspace authorization verified
[ ] Local bridge security boundary verified
[ ] Tool authorization verified
[ ] Ruata orchestration verified
[ ] Kimi research verified
[ ] John backend workflow verified
[ ] Manasseh frontend workflow verified
[ ] Ian QA/security gate verified
[ ] Dashboard operational
[ ] VS Code integration operational
[ ] Cloud sandbox operational
[ ] Evaluations operational
[ ] Observability operational
[ ] Security suite passes
[ ] Production deployment verified
[ ] First full end-to-end benchmark passes
```

The platform should optimize for **controlled reliability before autonomy**.
