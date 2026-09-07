from packages.schemas.domain import AgentRole, RiskLevel
from .engine import ToolPolicy


DEFAULT_POLICIES = [
    ToolPolicy(
        agent=AgentRole.RUATA,
        tool_names=frozenset({"workspace.info", "git.status", "git.diff", "task.inspect"}),
        read_paths=("**",),
        commands=frozenset({"git"}),
        max_risk=RiskLevel.MEDIUM,
    ),
    ToolPolicy(
        agent=AgentRole.KIMI,
        tool_names=frozenset({"workspace.info", "file.read", "documentation.search", "web.search"}),
        read_paths=("**",),
        max_risk=RiskLevel.MEDIUM,
    ),
    ToolPolicy(
        agent=AgentRole.MANASSEH,
        tool_names=frozenset({"workspace.info", "file.read", "file.write", "file.patch", "git.status", "git.diff", "terminal.run", "test.run", "browser.run"}),
        read_paths=("**",),
        write_paths=("frontend/**", "src/**", "app/**", "components/**", "public/**", "tests/frontend/**", "tests/e2e/**"),
        commands=frozenset({"npm", "pnpm", "npx", "node", "git"}),
        network_targets=frozenset({"localhost"}),
        max_risk=RiskLevel.MEDIUM,
    ),
    ToolPolicy(
        agent=AgentRole.JOHN,
        tool_names=frozenset({"workspace.info", "file.read", "file.write", "file.patch", "git.status", "git.diff", "terminal.run", "test.run", "database.query"}),
        read_paths=("**",),
        write_paths=("backend/**", "api/**", "server/**", "services/**", "supabase/**", "migrations/**", "tests/backend/**", "tests/integration/**", "openapi.yaml", "openapi.yml"),
        commands=frozenset({"python", "uv", "pytest", "poetry", "pip", "git", "supabase"}),
        network_targets=frozenset({"localhost"}),
        max_risk=RiskLevel.HIGH,
    ),
    ToolPolicy(
        agent=AgentRole.MOSES,
        tool_names=frozenset({"workspace.info", "file.read", "file.write", "file.patch", "git.status", "git.diff", "terminal.run", "test.run", "browser.run"}),
        read_paths=("**",),
        write_paths=("mobile/**", "apps/mobile/**", "src/mobile/**", "ios/**", "android/**", "tests/mobile/**", "e2e/mobile/**"),
        commands=frozenset({"npm", "pnpm", "npx", "node", "yarn", "expo", "flutter", "dart", "gradle", "adb", "fastlane", "pod", "git"}),
        network_targets=frozenset({"localhost"}),
        max_risk=RiskLevel.MEDIUM,
    ),
    ToolPolicy(
        agent=AgentRole.IAN,
        tool_names=frozenset({"workspace.info", "file.read", "git.status", "git.diff", "terminal.run", "test.run", "security.scan", "browser.run"}),
        read_paths=("**",),
        commands=frozenset({"python", "uv", "pytest", "npm", "pnpm", "npx", "git"}),
        network_targets=frozenset({"localhost"}),
        max_risk=RiskLevel.MEDIUM,
    ),
]
