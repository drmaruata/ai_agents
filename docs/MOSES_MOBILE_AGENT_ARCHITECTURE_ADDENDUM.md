# Moses Mobile Agent — Architecture Addendum

**Status:** Canonical amendment to the six-agent fleet

This addendum extends `AI_Software_Development_Agent_Team_Architecture.md` with the sixth specialist agent, **Moses — Mobile Application Engineer**. Where this addendum conflicts with older five-agent wording in the architecture document, the six-agent definition in this addendum is authoritative until the architecture document is regenerated in full.

## Agent fleet

```text
Ruata    → Principal Engineering Orchestrator
Kimi     → Research & Architecture Engineer
John     → Backend & Data Engineer
Manasseh → Frontend / Web Engineer
Moses    → Mobile Application Engineer
Ian      → Quality / Security / Reliability Engineer
```

## Moses mission

Moses owns production mobile application development for iOS and Android. The role is framework-neutral and may implement React Native/Expo, Flutter, native Android/Kotlin, native iOS/Swift/SwiftUI, or another approved mobile stack selected through architecture review.

## Ownership boundary

```text
John     → API, backend, Supabase/PostgreSQL, business logic, data contracts
Manasseh → Web UI, Next.js/React, browser-facing UX
Moses    → iOS/Android application code and mobile-specific UX/platform behavior
Ian      → Cross-platform validation, security, regression and release readiness
```

Moses consumes backend contracts established by John and should not silently redefine them.

## Mobile capabilities

Moses may work with:

- mobile navigation and state
- offline-aware and cached data flows
- secure local storage
- Supabase Auth client sessions
- RLS-aware data access
- push notifications
- deep links
- camera, location and device APIs
- accessibility
- performance, battery and network optimization
- Android/iOS build configuration
- emulator/simulator validation
- mobile unit/component/integration/E2E tests

## Security boundary

Mobile builds may contain only public/publishable client configuration. Service-role keys, Supabase secret keys, database passwords, signing credentials, provisioning profiles, keystores, private keys, and other privileged secrets are never committed to the repository or embedded in the application bundle.

Production App Store / Google Play publication and consequential mobile infrastructure changes remain subject to the platform's human approval policy.

## Ruata routing

Mobile-only work:

```text
Ruata → Moses → Ian
```

Full-stack web + mobile work:

```text
            Ruata
              │
       ┌──────┼──────┐
       ▼      ▼      ▼
     John  Manasseh Moses
       │      │      │
       └──────┼──────┘
              ▼
             Ian
```

Research-required mobile work places Kimi before the implementation specialists.
