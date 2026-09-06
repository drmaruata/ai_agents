# First End-to-End Software Engineering Benchmark

## Objective

Validate the complete platform on one realistic full-stack feature from natural-language request through tested, auditable implementation.

## Benchmark input

> Add a booking cancellation feature to a representative web application. A user must be able to cancel an eligible booking, the backend must enforce authorization and business rules, the database state must be updated safely, the UI must communicate loading/success/error states, and the behavior must be covered by automated tests.

## Required workflow

1. Ruata analyzes the request and project context.
2. Kimi researches any uncertain architecture/library questions and produces implementation guidance.
3. Ruata produces a dependency-aware task graph.
4. John implements database/backend changes and tests.
5. Manasseh implements frontend changes and browser tests.
6. Ian performs static, unit, integration, E2E, regression, and security validation.
7. Failed checks create targeted repair work.
8. High-risk changes request human approval.
9. Ruata produces a final evidence package.

## Evidence package

```text
requirements.md
research.md (when needed)
architecture.md
api-contract.yaml (when applicable)
implementation summary
git diff
test report
security report
audit events
approval record (when applicable)
final release recommendation
```

## Success criteria

- Functional acceptance criteria pass.
- No critical or high-severity security finding remains.
- Required automated tests pass.
- No unrelated files are modified.
- All tool calls are authorized and auditable.
- The final task state is reproducible from persisted state and artifacts.
- Human intervention is limited to defined approval gates.
