# Moses Mobile Agent — Roadmap Addendum

**Status:** Active implementation amendment

Moses is now a first-class specialist in the Ruata platform.

## Roadmap impact

### Phase 1 — Shared Domain Model

`AgentRole.MOSES` is required in the shared domain contract.

### Phase 5 — Policy Engine

Moses receives a bounded mobile-development policy covering mobile source trees and approved mobile toolchains. Production publication remains high-risk and requires human approval.

### Phase 6 — Tool Registry / MCP

Mobile tooling should be exposed through explicit tool definitions rather than unrestricted shell access. Candidate tools include mobile build, test, emulator/simulator inspection, device logs, and platform diagnostics.

### Phase 7 — Ruata Orchestration

Ruata detects mobile requirements and routes them to Moses. For cross-platform features, Moses can execute in parallel with Manasseh after shared research/backend dependencies are satisfied. Ian remains the final validation gate.

### Phase 9 — John Backend

John owns the shared API, Supabase/PostgreSQL schema, authentication contracts, and data services consumed by Moses.

### Phase 10 — Manasseh Web Frontend

Manasseh remains responsible for web UX. He does not take ownership of mobile-specific screens or platform behavior.

### Phase 10A — Moses Mobile Engineering

New mobile specialist phase within the agent fleet:

```text
Architecture decision
        ↓
Mobile implementation
        ↓
Platform-specific integration
        ↓
Unit/component/integration tests
        ↓
Android/iOS build validation
        ↓
Accessibility + performance checks
        ↓
Ian cross-platform validation
```

Acceptance requires applicable Android/iOS builds, mobile test coverage, authentication/session correctness, RLS-safe data access, accessibility validation, and no embedded privileged secrets.

### Phase 11 — Ian Quality/Security

Ian adds mobile-specific validation for permissions, deep links, secure storage, offline/online transitions, platform builds, and release security.

### Phase 13 — Dashboard

The dashboard must show six agents and provide mobile-task status, build/test evidence, and mobile-specific validation results.

### Phase 15 — CI/CD

CI should progressively add mobile lint/type/test/build checks. Store signing/release secrets only in secure CI/CD secret storage; never in Git.

### Phase 17 — Evaluation

Add Moses evaluation scenarios covering:

- mobile feature implementation
- API integration
- authentication
- offline behavior
- deep linking
- notification flows
- Android build failures
- iOS build failures
- accessibility regressions
- platform-specific bugs

## Mobile v1 acceptance benchmark

A representative v1 benchmark should require Moses to implement a mobile feature against the existing Supabase-backed backend while preserving RLS/Auth boundaries and passing Ian's cross-platform validation.
