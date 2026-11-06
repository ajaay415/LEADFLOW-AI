import { useCallback, useEffect, useMemo, useState } from "react";
import "./CRM.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const STATUSES = ["NEW", "CONTACTED", "QUALIFIED", "PROPOSAL", "WON", "LOST"];

function money(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

export default function CRM() {
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [leadResponse, statsResponse] = await Promise.all([
        fetch(`${API}/leads`),
        fetch(`${API}/dashboard/stats`),
      ]);
      if (!leadResponse.ok || !statsResponse.ok) {
        throw new Error("The CRM API could not load dashboard data.");
      }
      const [leadData, statsData] = await Promise.all([
        leadResponse.json(),
        statsResponse.json(),
      ]);
      setLeads(leadData);
      setStats(statsData);
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const visibleLeads = useMemo(() => {
    const query = search.trim().toLowerCase();
    return leads.filter((lead) => {
      const matchesStatus = status === "ALL" || lead.status === status;
      const matchesSearch =
        !query ||
        [lead.name, lead.email, lead.company, lead.requirement]
          .some((value) => String(value || "").toLowerCase().includes(query));
      return matchesStatus && matchesSearch;
    });
  }, [leads, search, status]);

  async function updateStatus(leadId, nextStatus) {
    setBusyId(leadId);
    setError("");
    try {
      const response = await fetch(`${API}/leads/${leadId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (!response.ok) throw new Error("Could not update lead status.");
      await loadDashboard();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  async function removeLead(leadId) {
    if (!window.confirm("Delete this lead permanently?")) return;
    setBusyId(leadId);
    setError("");
    try {
      const response = await fetch(`${API}/leads/${leadId}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Could not delete this lead.");
      await loadDashboard();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  const highPriority = stats?.by_priority?.HIGH || 0;
  const qualified = (stats?.by_status?.QUALIFIED || 0) + (stats?.by_status?.PROPOSAL || 0);
  const won = stats?.by_status?.WON || 0;

  return (
    <main className="crm-shell">
      <aside className="crm-sidebar">
        <a className="crm-brand" href="/">◉ LEADFLOW <span>AI</span></a>
        <div className="crm-workspace-label">WORKSPACE</div>
        <a className="crm-nav active" href="/dashboard">▦ <span>Overview</span></a>
        <a className="crm-nav" href="#leads">◉ <span>Leads</span></a>
        <a className="crm-nav" href="#analytics">▥ <span>Analytics</span></a>
        <div className="crm-sidebar-bottom">
          <div className="crm-avatar">LF</div>
          <div><strong>LEADFLOW Admin</strong><small>Workspace</small></div>
        </div>
      </aside>

      <section className="crm-main">
        <header className="crm-topbar">
          <div><span className="crm-eyebrow">WORKSPACE / OVERVIEW</span><h1>Dashboard</h1></div>
          <div className="crm-top-actions">
            <span className="crm-live-dot">API workspace</span>
            <button className="crm-refresh" onClick={loadDashboard} disabled={loading}>↻ Refresh</button>
          </div>
        </header>

        {error && <div className="crm-alert" role="alert">{error}</div>}

        <section className="crm-metrics">
          <article className="crm-metric"><span>Total leads</span><strong>{stats?.total_leads ?? "—"}</strong><small>All captured enquiries</small><i>◉</i></article>
          <article className="crm-metric"><span>High priority</span><strong>{highPriority}</strong><small>Require quick attention</small><i>↗</i></article>
          <article className="crm-metric"><span>Qualified pipeline</span><strong>{qualified}</strong><small>Qualified + proposal</small><i>▥</i></article>
          <article className="crm-metric"><span>Pipeline value</span><strong>{stats ? money(stats.pipeline_value) : "—"}</strong><small>Based on submitted budgets</small><i>₹</i></article>
        </section>

        <section className="crm-insights" id="analytics">
          <article className="crm-panel crm-chart-panel">
            <div className="crm-panel-heading"><div><span className="crm-eyebrow">PIPELINE</span><h2>Lead status</h2></div><span className="crm-muted">{stats?.total_leads || 0} total</span></div>
            <div className="crm-bars">
              {STATUSES.map((item) => {
                const count = stats?.by_status?.[item] || 0;
                const percent = stats?.total_leads ? Math.max(4, count / stats.total_leads * 100) : 0;
                return <div className="crm-bar-row" key={item}><span>{item}</span><div className="crm-bar-track"><div className="crm-bar-fill" style={{ width: `${percent}%` }} /></div><b>{count}</b></div>;
              })}
            </div>
          </article>
          <article className="crm-panel crm-score-panel">
            <span className="crm-eyebrow">AI INTELLIGENCE</span><h2>Average lead score</h2>
            <div className="crm-score-ring"><div><strong>{Math.round(stats?.average_score || 0)}</strong><small>/ 100</small></div></div>
            <p>Average qualification score across your saved leads.</p>
            <div className="crm-score-foot"><span>Won deals</span><strong>{won}</strong></div>
          </article>
        </section>

        <section className="crm-panel crm-leads-panel" id="leads">
          <div className="crm-panel-heading crm-leads-heading">
            <div><span className="crm-eyebrow">CUSTOMER RELATIONSHIP</span><h2>Lead management</h2></div>
            <span className="crm-muted">{visibleLeads.length} records</span>
          </div>
          <div className="crm-toolbar">
            <input aria-label="Search leads" placeholder="Search name, email, company..." value={search} onChange={(event) => setSearch(event.target.value)} />
            <select aria-label="Filter by status" value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="ALL">All statuses</option>
              {STATUSES.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>
          {loading ? <div className="crm-empty">Loading your leads...</div> : visibleLeads.length === 0 ? <div className="crm-empty">No leads found. Submit a lead through the website demo form to get started.</div> : (
            <div className="crm-table-wrap"><table className="crm-table">
              <thead><tr><th>Contact</th><th>Requirement</th><th>AI score</th><th>Priority</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>{visibleLeads.map((lead) => (
                <tr key={lead.id}>
                  <td><strong>{lead.name}</strong><small>{lead.email}</small>{lead.company && <small>{lead.company}</small>}</td>
                  <td className="crm-requirement">{lead.requirement}</td>
                  <td><span className="crm-score-pill">{lead.lead_score ?? "—"}</span></td>
                  <td><span className={`crm-priority ${String(lead.priority || "low").toLowerCase()}`}>{lead.priority || "UNSCORED"}</span></td>
                  <td><select aria-label={`Status for ${lead.name}`} value={lead.status || "NEW"} disabled={busyId === lead.id} onChange={(event) => updateStatus(lead.id, event.target.value)}>{STATUSES.map((item) => <option key={item} value={item}>{item}</option>)}</select></td>
                  <td><button className="crm-delete" disabled={busyId === lead.id} onClick={() => removeLead(lead.id)}>Delete</button></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </section>
        <footer className="crm-footer">LEADFLOW AI · Intelligent lead operations</footer>
      </section>
    </main>
  );
}
