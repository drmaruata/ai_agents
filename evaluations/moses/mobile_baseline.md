# Moses Mobile Baseline Evaluation

## Scenario
Build a mobile booking feature against an existing Supabase-backed application.

## Required behavior

- Use the approved backend/API contract.
- Authenticate through Supabase Auth.
- Read/write only data permitted by RLS.
- Implement iOS and Android-compatible mobile UI.
- Handle loading, error, empty, offline, and reconnect states.
- Validate accessibility and platform-specific behavior.
- Add unit/component/integration tests appropriate to the selected stack.
- Produce an Android and/or iOS build validation result appropriate to the available environment.

## Security checks

- No service-role or secret Supabase credential in client code.
- No database password or signing secret in source or app bundle.
- Deep links and external inputs are validated.
- Sensitive values are not logged.

## Acceptance

Moses passes when the implementation uses the approved architecture, preserves backend contracts, respects Supabase Auth/RLS boundaries, passes applicable tests and build checks, and documents any platform-specific limitation.
