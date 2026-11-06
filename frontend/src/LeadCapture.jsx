import { useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function LeadCapture() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    company: "",
    requirement: "",
    budget: "",
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const submitLead = async (e) => {
    e.preventDefault();

    setLoading(true);
    setSuccess(null);
    setError("");

    try {
      const response = await fetch(`${API}/leads`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: form.name,
          email: form.email,
          company: form.company,
          requirement: form.requirement,
          budget: form.budget
            ? Number(form.budget)
            : null,
        }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(
          typeof payload.detail === "string"
            ? payload.detail
            : "Unable to submit lead"
        );
      }

      setSuccess(payload);

      setForm({
        name: "",
        email: "",
        company: "",
        requirement: "",
        budget: "",
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="lead-capture-page">

      <div className="lead-capture-card">

        <div className="lead-capture-header">
          <div className="brand">
            <span>◉</span>
            LEADFLOW AI
          </div>

          <h1>Let's talk about your project.</h1>

          <p>
            Tell us what you need and our team will
            get back to you shortly.
          </p>
        </div>

        <form onSubmit={submitLead}>

          <div className="capture-grid">

            <div className="capture-group">
              <label>Full Name</label>

              <input
                name="name"
                value={form.name}
                onChange={handleChange}
                placeholder="Rahul Kumar"
                required
              />
            </div>

            <div className="capture-group">
              <label>Email</label>

              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder="rahul@example.com"
                required
              />
            </div>

            <div className="capture-group">
              <label>Company</label>

              <input
                name="company"
                value={form.company}
                onChange={handleChange}
                placeholder="RK Digital Solutions"
              />
            </div>

            <div className="capture-group">
              <label>Estimated Budget</label>

              <input
                type="number"
                name="budget"
                value={form.budget}
                onChange={handleChange}
                placeholder="75000"
              />
            </div>

            <div className="capture-group full">
              <label>What do you need?</label>

              <textarea
                name="requirement"
                value={form.requirement}
                onChange={handleChange}
                placeholder="Tell us about your project..."
                rows="5"
                required
              />
            </div>

          </div>

          {error && (
            <div className="capture-error">
              {error}
            </div>
          )}

          {success && (
            <div className="capture-success">
              <strong>Lead received successfully! 🎉</strong>

              <span>
                Lead ID: #{success.lead?.id || "received"}
              </span>

              <span>
                Your requirement has been analyzed and saved.
              </span>
            </div>
          )}

          <button
            type="submit"
            className="capture-submit"
            disabled={loading}
          >
            {loading
              ? "Submitting..."
              : "Submit Requirement →"}
          </button>

        </form>

      </div>

    </div>
  );
}