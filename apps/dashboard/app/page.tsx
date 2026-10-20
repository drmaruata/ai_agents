"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { getSupabaseBrowserClient } from "../lib/supabase";

type Agent = { id: string; name: string; role: string; status: string };
type Task = { task_id: string; title: string; status: string; risk_level: string };
type Project = { project_id: string; name: string; repository_url?: string | null; default_branch: string };

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const fallbackAgents: Agent[] = [
  { id: "ruata", name: "Ruata", role: "Principal Engineering Orchestrator", status: "idle" },
  { id: "kimi", name: "Kimi", role: "Research & Architecture", status: "idle" },
  { id: "manasseh", name: "Manasseh", role: "Frontend Engineer", status: "idle" },
  { id: "john", name: "John", role: "Backend & Data Engineer", status: "idle" },
  { id: "moses", name: "Moses", role: "Mobile Application Engineer", status: "idle" },
  { id: "ian", name: "Ian", role: "Quality / Security / Reliability", status: "idle" },
];

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [configured, setConfigured] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [projectName, setProjectName] = useState("");
  const [repositoryUrl, setRepositoryUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    try {
      const supabase = getSupabaseBrowserClient();
      void supabase.auth.getSession().then(({ data, error: sessionError }) => {
        if (sessionError) setError(sessionError.message);
        setSession(data.session);
      });
      const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => {
        setSession(nextSession);
      });
      return () => data.subscription.unsubscribe();
    } catch (err) {
      setConfigured(false);
      setError(err instanceof Error ? err.message : "Supabase configuration is missing.");
    }
  }, []);

  const apiFetch = useCallback(async (path: string, init: RequestInit = {}) => {
    if (!session?.access_token) throw new Error("Sign in to continue.");
    const headers = new Headers(init.headers);
    headers.set("Authorization", `Bearer ${session.access_token}`);
    if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    const response = await fetch(`${API}${path}`, {
      ...init,
      headers,
      cache: "no-store",
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = typeof body.detail === "string" ? body.detail : "Control-plane request failed.";
      throw new Error(detail);
    }
    return body;
  }, [session]);

  const loadWorkspace = useCallback(async () => {
    if (!session) return;
    setError(null);
    try {
      const [agentData, projectData] = await Promise.all([
        apiFetch("/api/agents"),
        apiFetch("/api/projects"),
      ]);
      setAgents(agentData);
      setProjects(projectData);
      const selected = projectData.find((item: Project) => item.project_id === projectId) ?? projectData[0];
      setProjectId(selected?.project_id ?? "");
      if (selected) {
        const taskData = await apiFetch(`/api/tasks?project_id=${encodeURIComponent(selected.project_id)}`);
        setTasks(taskData);
      } else {
        setTasks([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reach the control plane.");
    }
  }, [session, apiFetch, projectId]);

  useEffect(() => {
    if (session) void loadWorkspace();
  }, [session, loadWorkspace]);

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const supabase = getSupabaseBrowserClient();
      const { error: authError } = await supabase.auth.signInWithPassword({ email, password });
      if (authError) throw authError;
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    setBusy(true);
    try {
      const { error: authError } = await getSupabaseBrowserClient().auth.signOut();
      if (authError) throw authError;
      setTasks([]);
      setProjects([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-out failed.");
    } finally {
      setBusy(false);
    }
  }

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const created = await apiFetch("/api/projects", {
        method: "POST",
        body: JSON.stringify({ name: projectName, repository_url: repositoryUrl || null, default_branch: "main" }),
      });
      setProjectName("");
      setRepositoryUrl("");
      setNotice(`Project “${created.name}” created.`);
      await loadWorkspace();
      setProjectId(created.project_id);
      setTasks([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create project.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!session || !projectId) return;
    let cancelled = false;
    void apiFetch(`/api/tasks?project_id=${encodeURIComponent(projectId)}`)
      .then((data) => { if (!cancelled) setTasks(data); })
      .catch((err) => { if (!cancelled) setError(err instanceof Error ? err.message : "Unable to load tasks."); });
    return () => { cancelled = true; };
  }, [session, projectId, apiFetch]);

  if (!configured || !session) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <div className="brand">RUATA</div>
          <h1 className="title">Sign in to your workspace</h1>
          <p className="muted">Use your Supabase Auth account to access projects, tasks, and approvals.</p>
          {!configured ? (
            <p className="error">Configure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY in the dashboard deployment environment. Do not use a service-role key in browser variables.</p>
          ) : (
            <form className="auth-form" onSubmit={signIn}>
              <label>Email<input autoComplete="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
              <label>Password<input autoComplete="current-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
              <button type="submit" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
            </form>
          )}
          {error && <p className="error" role="alert">{error}</p>}
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard">
      <aside className="sidebar">
        <div className="brand">RUATA</div>
        <nav className="nav" aria-label="Primary">
          {["Dashboard", "Projects", "Devices", "Agents", "Tasks", "Runs", "Approvals", "Evaluations", "Audit Log", "Settings"].map((item, index) => (
            <span className={index === 0 ? "active" : ""} key={item}>{item}</span>
          ))}
        </nav>
        <button className="secondary-button signout" onClick={signOut} disabled={busy}>Sign out</button>
      </aside>
      <section className="main">
        <header className="header">
          <div>
            <h1 className="title">AI Software Engineering Team</h1>
            <div className="muted">{session.user.email ?? session.user.id} · authenticated with Supabase</div>
          </div>
          <span className="badge">Development</span>
        </header>
        {error && <div className="card error" role="alert">{error}</div>}
        {notice && <div className="card notice" role="status">{notice}</div>}
        <section className="grid" aria-label="Agents">
          {(agents.length ? agents : fallbackAgents).map((agent) => (
            <article className="card" key={agent.id}>
              <div className="agent-name">{agent.name}</div>
              <div className="muted">{agent.role}</div>
              <div className="status">● {agent.status}</div>
            </article>
          ))}
        </section>
        <section className="section card">
          <div className="header" style={{ marginBottom: 12 }}>
            <div><h2 style={{ margin: 0 }}>Projects</h2><div className="muted">Projects visible to your account</div></div>
            <span className="badge">{projects.length} total</span>
          </div>
          <div className="project-toolbar">
            <label className="project-select">Selected project
              <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
                <option value="">Select a project</option>
                {projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.name}</option>)}
              </select>
            </label>
          </div>
          <form className="project-form" onSubmit={createProject}>
            <label>New project name<input value={projectName} onChange={(event) => setProjectName(event.target.value)} minLength={1} maxLength={120} required /></label>
            <label>Repository URL (optional)<input type="url" value={repositoryUrl} onChange={(event) => setRepositoryUrl(event.target.value)} placeholder="https://github.com/org/repository" /></label>
            <button type="submit" disabled={busy}>{busy ? "Working…" : "Create project"}</button>
          </form>
        </section>
        <section className="section card">
          <div className="header" style={{ marginBottom: 12 }}>
            <div><h2 style={{ margin: 0 }}>Tasks</h2><div className="muted">Live control-plane task state for the selected project</div></div>
            <span className="badge">{tasks.length} total</span>
          </div>
          {!projectId ? <div className="muted">Create or select a project to view tasks.</div> : tasks.length === 0 ? <div className="muted">No tasks yet in this project.</div> : (
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
        <section className="section grid metrics" aria-label="Summary">
          <article className="card"><strong>Agents</strong><div className="muted metric-value">{agents.length} registered</div></article>
          <article className="card"><strong>Tasks</strong><div className="muted metric-value">{tasks.length} in selected project</div></article>
          <article className="card"><strong>Projects</strong><div className="muted metric-value">{projects.length} accessible</div></article>
        </section>
      </section>
    </main>
  );
}
