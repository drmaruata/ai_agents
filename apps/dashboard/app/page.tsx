const agents = [
  { name: "Ruata", role: "Principal Engineering Orchestrator", status: "idle" },
  { name: "Kimi", role: "Research & Architecture", status: "idle" },
  { name: "Manasseh", role: "Frontend Engineer", status: "idle" },
  { name: "John", role: "Backend & Data Engineer", status: "idle" },
  { name: "Ian", role: "Quality / Security / Reliability", status: "idle" },
];

export default function Home() {
  return (
    <main className="dashboard">
      <aside className="sidebar">
        <div className="brand">RUATA</div>
        <nav className="nav" aria-label="Primary">
          <span className="active">Dashboard</span>
          <span>Projects</span>
          <span>Devices</span>
          <span>Agents</span>
          <span>Tasks</span>
          <span>Runs</span>
          <span>Approvals</span>
          <span>Evaluations</span>
          <span>Audit Log</span>
          <span>Settings</span>
        </nav>
      </aside>

      <section className="main">
        <header className="header">
          <div>
            <h1 className="title">AI Software Engineering Team</h1>
            <div className="muted">Hybrid cloud + local execution control plane</div>
          </div>
          <span className="badge">Development</span>
        </header>

        <section className="grid" aria-label="Agents">
          {agents.map((agent) => (
            <article className="card" key={agent.name}>
              <div className="agent-name">{agent.name}</div>
              <div className="muted">{agent.role}</div>
              <div className="status">● {agent.status}</div>
            </article>
          ))}
        </section>

        <section className="section card">
          <div className="header" style={{ marginBottom: 12 }}>
            <div>
              <h2 style={{ margin: 0 }}>Current task</h2>
              <div className="muted">Connect the dashboard to the control-plane task API.</div>
            </div>
            <span className="badge">0%</span>
          </div>
          <div className="progress" aria-label="Task progress">
            <span style={{ width: "0%" }} />
          </div>
        </section>

        <section className="section grid" style={{ gridTemplateColumns: "repeat(3,minmax(0,1fr))" }}>
          <article className="card"><strong>Local devices</strong><div className="muted" style={{ marginTop: 6 }}>0 connected</div></article>
          <article className="card"><strong>Active runs</strong><div className="muted" style={{ marginTop: 6 }}>0 running</div></article>
          <article className="card"><strong>Approvals</strong><div className="muted" style={{ marginTop: 6 }}>0 pending</div></article>
        </section>
      </section>
    </main>
  );
}
