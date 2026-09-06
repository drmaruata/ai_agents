# AGENTS.md — ai_agents

## Repository policy

- The repository `drmaruata/ai_agents` uses **main-only development**.
- All repository changes must be committed directly to `main`.
- Do not create feature branches or pull requests for normal changes to this repository.
- Never force-push `main` unless the repository owner explicitly authorizes it.
- Verify the target branch is `main` before every write operation.

## Project mission

Build a hybrid cloud + local AI software-engineering platform with five role-based agents:

- Ruata — Orchestrator / Engineering Manager
- Kimi — Research & Architecture
- Manasseh — Frontend Engineer
- John — Backend & Data Engineer
- Ian — QA / Security / Reliability Engineer

## Engineering rules

1. Read the architecture specification before making material design changes.
2. Preserve least-privilege boundaries between agents.
3. Do not expose developer machines through unrestricted inbound network access.
4. Route local filesystem, terminal, Git, browser and VS Code operations through the Local Agent Bridge.
5. Prefer structured artifacts over long agent-to-agent conversational state.
6. Add tests for behavioral changes.
7. Run formatting, linting, type checking and relevant tests before committing.
8. Never commit secrets, credentials, tokens, private keys, or generated sensitive state.
9. Do not weaken security controls simply to make a check pass.
10. High-risk or destructive operations require explicit human approval.
11. Keep changes scoped to the task.
12. Review `git diff` before every commit.

## Documentation

The canonical architecture document is:

`AI Software Development Agent Team — Architecture & Agent Specifications.md`

Update that document when implementation changes materially affect the platform architecture, agent responsibilities, security model, execution model, or operating policies.

## Commit style

Use concise conventional commit messages where practical, for example:

- `feat: add local agent bridge`
- `fix: enforce workspace permission policy`
- `docs: update architecture specification`
- `test: add orchestrator state coverage`

## Done criteria

A change is ready for commit only when:

- implementation is complete,
- required tests pass,
- security implications are reviewed,
- no unrelated files are changed,
- documentation is updated when needed, and
- the final diff is reviewed.
