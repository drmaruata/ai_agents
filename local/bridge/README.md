# Local Agent Bridge

The Local Agent Bridge is the security boundary between the cloud control plane and a developer workstation.

## Responsibilities

- Maintain an authenticated outbound connection to the cloud.
- Register device and workspaces.
- Validate task, project, workspace, agent, and tool permissions.
- Execute approved filesystem, terminal, Git, browser, and VS Code actions.
- Return structured results and audit events.
- Fail closed when policy is ambiguous.

## Security

The bridge must never expose an unrestricted inbound server on the developer machine. Store tokens using the operating system's secure credential facilities in the production implementation. Keep development credentials out of the repository.
