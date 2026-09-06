"use client";

import { useEffect, useState } from "react";

type Agent = { id: string; name: string; role: string; status: string };
type Task = { task_id: string; title: string; status: string; risk_level: string };

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const tokenResponse = await fetch(`${API}/api/auth/dev-token`, { method: "POST" });
        const tokenBody = await tokenResponse.json();
        if (!tokenResponse.ok) throw new Error(tokenBody.detail ?? "Unable to authenticate");
        const headers = { Authorization: `Bearer ${tokenBody.access_token}` };
        const [agentResponse, taskResponse] = await Promise.all([
          fetch(`${API}/api/agents`, { headers }),
          fetch(`${API}/api/tasks`, { headers }),
        ]);
        if (!agentResponse.ok || !taskResponse.ok) throw new Error("Control plane request failed");
        setAgents(await agentResponse.json());
        setTasks(await taskResponse.json());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to reach control plane");
      }
    };
    void load();
  }, []);

  return (
    <main className="dashboard">
      <aside className="sidebar">
        <div className="brand">RUATA</div>
        <nav className="nav" aria-label="Primary">
          {['Dashboard','Projects','Devices','Agents','Tasks','Runs','Approvals','Evaluations','Audit Log','Settings'].map((item, index) => (
            <span className={index === 0 ? "active" : ""} key={item}>{item}</span>
          ))}
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
        {error && <div className="card" style={{ marginBottom: 16 }}>Control plane: {error}</div>}
        <section className="grid" aria-label="Agents">
          {(agents.length ? agents : [
            { id: 'ruata', name: 'Ruata', role: 'Principal Engineering Orchestrator', status: 'idle' },
            { id: 'kimi', name: 'Kimi', role: 'Research & Architecture', status: 'idle' },
            { id: 'manasseh', name: 'Manasseh', role: 'Frontend Engineer', status: 'idle' },
            { id: 'john', name: 'John', role: 'Backend & Data Engineer', status: 'idle' },
            { id: 'ian', name: 'Ian', role: 'Quality / Security / Reliability', status: 'idle' },
          ]).map((agent) => (
            <article className="card" key={agent.id}>
              <div className="agent-name">{agent.name}</div>
              <div className="muted">{agent.role}</div>
              <div className="status">● {agent.status}</div>
            </article>
          ))}
        </section>
        <section className="section card">
          <div className="header" style={{ marginBottom: 12 }}>
            <div><h2 style={{ margin: 0 }}>Tasks</h2><div className="muted">Live control-plane task state</div></div>
            <span className="badge">{tasks.length} total</span>
          </div>
          {tasks.length === 0 ? <div className="muted">No tasks yet. Use the API to create the first task.</div> : (
            <div style={{ display: "grid", gap: 10 }}>
              {tasks.map((task) => (
                <div className="task" key={task.task_id}>
                  <span className="badge">{task.status}</span>
                  <div><strong>{task.title}</strong><div className="muted">{task.task_id}</div></div>
                  <span className="badge">{task.risk_level}</span>
                </div>
              ))}
            </div>
          )}
        </section>
        <section className="section grid" style={{ gridTemplateColumns: "repeat(3,minmax(0,1fr))" }}>
          <article className="card"><strong>Agents</strong><div className="muted" style={{ marginTop: 6 }}>{agents.length || 5} registered</div></article>
          <article className="card"><strong>Active runs</strong><div className="muted" style={{ marginTop: 6 }}>0 running</div></article>
          <article className="card"><strong>Approvals</strong><div className="muted" style={{ marginTop: 6 }}>0 pending</div></article>
        </section>
      </section>
    </main>
  );
}
