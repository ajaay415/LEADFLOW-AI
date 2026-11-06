import { useState } from "react";
import "./App.css";
import CRM from "./CRM.jsx";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  if (window.location.pathname === "/dashboard") return <CRM />;
  const [showDemo, setShowDemo] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);

  const [form, setForm] = useState({
    name: "",
    company: "",
    email: "",
    budget: "",
    requirement: "",
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyzeLead = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/leads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          budget: form.budget.trim() ? Number(form.budget) : null,
        }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(
          typeof payload.detail === "string"
            ? payload.detail
            : "Unable to analyze this lead. Please try again."
        );
      }

      const lead = payload.lead || {};
      const analysis = payload.analysis || {};
      setResult({
        score: lead.lead_score ?? analysis.lead_score ?? 0,
        priority: `${lead.priority || analysis.priority || "MEDIUM"} PRIORITY`,
        action:
          lead.recommended_action ||
          analysis.recommended_action ||
          "Follow up with this customer.",
        category: lead.category || analysis.category || "General Enquiry",
      });
    } catch (requestError) {
      setError(
        requestError.message ||
          "Could not connect to LEADFLOW AI. Check that the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const closeDemo = () => {
    setShowDemo(false);
    setResult(null);
    setError("");
  };

  return (
    <div className="app">

      {/* NAVBAR */}

      <header className="navbar">
        <div className="container nav-content">

          <a href="#" className="logo">
            <span className="logo-icon">◉</span>
            LEADFLOW <span className="logo-ai">AI</span>
          </a>

          <nav className={mobileMenu ? "nav-links mobile-open" : "nav-links"}>
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
            <a href="#business">Businesses</a>
          </nav>

          <div className="nav-actions">
            <button
              className="login-btn"
              onClick={() =>
                alert("Login will be available in the SaaS version.")
              }
            >
              Login
            </button>

            <button
              className="primary-btn small"
              onClick={() => setShowDemo(true)}
            >
              Get Started
            </button>
          </div>

          <button
            className="mobile-menu"
            onClick={() => setMobileMenu(!mobileMenu)}
          >
            ☰
          </button>

        </div>
      </header>


      {/* HERO */}

      <section className="hero">

        <div className="hero-glow glow-one"></div>
        <div className="hero-glow glow-two"></div>

        <div className="container hero-grid">

          <div className="hero-content">

            <div className="eyebrow">
              <span className="pulse"></span>
              AI-POWERED SALES INTELLIGENCE
            </div>

            <h1>
              Turn More Leads
              <span>Into Customers.</span>
            </h1>

            <p className="hero-description">
              AI-powered lead qualification for growing teams.
              Capture every opportunity, understand customer intent,
              and focus your sales team on the leads that matter.
            </p>

            <div className="hero-flow">
              <span>Capture</span>
              <b>→</b>
              <span>Analyze</span>
              <b>→</b>
              <span>Prioritize</span>
              <b>→</b>
              <span>Convert</span>
            </div>

            <div className="hero-buttons">

              <button
                className="primary-btn"
                onClick={() => setShowDemo(true)}
              >
                Try LEADFLOW AI →
              </button>

              <button
                className="secondary-btn"
                onClick={() => setShowDemo(true)}
              >
                ▶ Watch Demo
              </button>

            </div>

            <div className="hero-note">
              <span>✓</span> Start with your first leads
              <span>✓</span> No complex setup
            </div>

          </div>


          {/* AI CARD */}

          <div className="hero-visual">

            <div className="ai-card">

              <div className="ai-top">

                <div>
                  <div className="mini-label">
                    AI LEAD SCORE
                  </div>

                  <div className="analyzed">
                    <span className="status-dot"></span>
                    AI ANALYZED
                  </div>
                </div>

                <div className="score">
                  <strong>
                    {result?.score || 92}
                  </strong>
                  <small>/100</small>
                </div>

              </div>

              <div className="lead-person">

                <div className="avatar">
                  RK
                </div>

                <div>
                  <h3>
                    {form.name || "Rahul Kumar"}
                  </h3>

                  <p>
                    {form.company || "RK Digital Solutions"}
                  </p>
                </div>

              </div>

              <div className="priority">
                {result?.priority || "🔥 HIGH PRIORITY"}
              </div>

              <div className="lead-details">

                <div>
                  <small>REQUIREMENT</small>
                  <strong>
                    {form.requirement || "Business Website"}
                  </strong>
                </div>

                <div>
                  <small>BUDGET</small>
                  <strong>
                    ₹{form.budget || "75,000"}
                  </strong>
                </div>

              </div>

              <div className="recommendation">

                <div className="recommendation-icon">
                  ✦
                </div>

                <div>
                  <small>RECOMMENDED ACTION</small>

                  <p>
                    {result?.action ||
                      "Contact this lead immediately"}
                  </p>
                </div>

              </div>

            </div>

          </div>

        </div>

      </section>


      {/* FEATURES */}

      <section className="section" id="features">

        <div className="container">

          <div className="section-heading">

            <span className="section-label">
              WHY LEADFLOW AI?
            </span>

            <h2>
              Your leads deserve
              <span>better follow-up.</span>
            </h2>

            <p>
              Stop manually checking every enquiry.
              Let LEADFLOW AI identify your best opportunities.
            </p>

          </div>

          <div className="feature-grid">

            <div className="feature-card">

              <div className="feature-icon purple">
                🤖
              </div>

              <h3>AI Scoring</h3>

              <p>
                Automatically evaluate every lead and
                assign a score from 0 to 100.
              </p>

              <div className="feature-number">
                01
              </div>

            </div>

            <div className="feature-card">

              <div className="feature-icon orange">
                ⚡
              </div>

              <h3>Instant Priority</h3>

              <p>
                Quickly identify HIGH, MEDIUM and LOW
                priority opportunities.
              </p>

              <div className="feature-number">
                02
              </div>

            </div>

            <div className="feature-card">

              <div className="feature-icon blue">
                📊
              </div>

              <h3>Sales Analytics</h3>

              <p>
                Understand your pipeline, lead quality,
                conversion and sales opportunities.
              </p>

              <div className="feature-number">
                03
              </div>

            </div>

          </div>

        </div>

      </section>


      {/* HOW IT WORKS */}

      <section className="section" id="how">

        <div className="container">

          <div className="section-heading">

            <span className="section-label">
              HOW IT WORKS
            </span>

            <h2>
              From enquiry to
              <span>opportunity.</span>
            </h2>

          </div>

          <div className="process">

            <div className="process-step">
              <div className="process-number">01</div>
              <div className="process-icon">👤</div>
              <h3>Capture</h3>
              <p>Receive customer enquiries.</p>
            </div>

            <div className="process-arrow">→</div>

            <div className="process-step">
              <div className="process-number">02</div>
              <div className="process-icon">🤖</div>
              <h3>Analyze</h3>
              <p>Understand customer intent.</p>
            </div>

            <div className="process-arrow">→</div>

            <div className="process-step">
              <div className="process-number">03</div>
              <div className="process-icon">🔥</div>
              <h3>Prioritize</h3>
              <p>Find your best opportunities.</p>
            </div>

            <div className="process-arrow">→</div>

            <div className="process-step">
              <div className="process-number">04</div>
              <div className="process-icon">🎯</div>
              <h3>Convert</h3>
              <p>Follow up and close deals.</p>
            </div>

          </div>

        </div>

      </section>


      {/* BUSINESSES */}

      <section className="section business-section" id="business">

        <div className="container business-content">

          <div>

            <span className="section-label">
              BUILT FOR BUSINESSES THAT GET LEADS
            </span>

            <h2>
              Wherever leads matter,
              <span>LEADFLOW helps.</span>
            </h2>

            <p>
              Designed for teams that depend on customer
              enquiries to grow their business.
            </p>

          </div>

          <div className="business-grid">

            <div className="business-item">
              <span>💻</span>
              <strong>Agencies</strong>
            </div>

            <div className="business-item">
              <span>🚀</span>
              <strong>Startups</strong>
            </div>

            <div className="business-item">
              <span>🏢</span>
              <strong>Software Companies</strong>
            </div>

            <div className="business-item">
              <span>🏠</span>
              <strong>Real Estate</strong>
            </div>

            <div className="business-item">
              <span>🎓</span>
              <strong>Education</strong>
            </div>

            <div className="business-item">
              <span>🛠️</span>
              <strong>Service Businesses</strong>
            </div>

          </div>

        </div>

      </section>


      {/* CTA */}

      <section className="cta-section">

        <div className="container">

          <div className="cta-card">

            <span className="section-label">
              READY TO GROW?
            </span>

            <h2>
              Stop losing leads.
              <span>Start closing them.</span>
            </h2>

            <p>
              Try LEADFLOW AI with your real customer enquiries
              and discover which opportunities deserve attention.
            </p>

            <button
              className="primary-btn large"
              onClick={() => setShowDemo(true)}
            >
              Start Free Demo →
            </button>

          </div>

        </div>

      </section>


      {/* FOOTER */}

      <footer>

        <div className="container footer-content">

          <div>

            <a href="#" className="logo">
              <span className="logo-icon">◉</span>
              LEADFLOW <span className="logo-ai">AI</span>
            </a>

            <p>
              AI-powered sales intelligence
              for growing businesses.
            </p>

          </div>

          <div className="footer-links">
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
            <a href="#business">Businesses</a>
          </div>

          <div>
            © 2026 LEADFLOW AI
          </div>

        </div>

      </footer>


      {/* DEMO MODAL */}

      {showDemo && (

        <div className="modal">

          <div
            className="modal-overlay"
            onClick={closeDemo}
          ></div>

          <div className="modal-box">

            <button
              className="modal-close"
              onClick={closeDemo}
            >
              ×
            </button>

            <span className="section-label">
              LEADFLOW AI DEMO
            </span>

            <h2>
              See your lead
              <span>in action.</span>
            </h2>

            <p>
              Enter a sample lead and see how LEADFLOW
              evaluates the opportunity.
            </p>

            <form onSubmit={analyzeLead}>

              <input
                type="text"
                placeholder="Customer name"
                value={form.name}
                onChange={(e) =>
                  setForm({
                    ...form,
                    name: e.target.value,
                  })
                }
                required
              />

              <input
                type="email"
                placeholder="Email address"
                value={form.email}
                onChange={(e) =>
                  setForm({
                    ...form,
                    email: e.target.value,
                  })
                }
                required
              />

              <input
                type="text"
                placeholder="Company"
                value={form.company}
                onChange={(e) =>
                  setForm({
                    ...form,
                    company: e.target.value,
                  })
                }
                required
              />

              <input
                type="number"
                placeholder="Budget"
                value={form.budget}
                onChange={(e) =>
                  setForm({
                    ...form,
                    budget: e.target.value,
                  })
                }
              />

              <textarea
                placeholder="Customer requirement"
                value={form.requirement}
                onChange={(e) =>
                  setForm({
                    ...form,
                    requirement: e.target.value,
                  })
                }
                required
              ></textarea>

              <button
                className="primary-btn full-btn"
                type="submit"
                disabled={loading}
              >
                {loading ? "Analyzing with AI..." : "Analyze Lead →"}
              </button>

            </form>

            {error && <p className="form-error" role="alert">{error}</p>}

            {result && (

              <div className="demo-result show">

                <div className="result-score">
                  <strong>{result.score}</strong>
                  <span>/100</span>
                </div>

                <div className="result-priority">
                  {result.priority}
                </div>

                <p>
                  {result.action}
                </p>

              </div>

            )}

          </div>

        </div>

      )}

    </div>
  );
}

export default App;