import { useState, useEffect, useCallback } from "react";
import { api } from "../api";

const CATEGORIES = ["road", "water", "electricity", "sanitation", "public_safety", "other"];

export default function ComplaintTracker({ t, language }) {
  const [form, setForm] = useState({ title: "", description: "", category: "road", location: "" });
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadComplaints = useCallback(async () => {
    try {
      const data = await api.listComplaints();
      setComplaints(data);
    } catch (err) {
      setError(err.message || t.errorGeneric);
    }
  }, [t.errorGeneric]);

  useEffect(() => {
    loadComplaints();
  }, [loadComplaints]);

  function updateField(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.title.trim() || !form.description.trim()) return;
    setLoading(true);
    setError("");
    try {
      await api.createComplaint({ ...form, language });
      setForm({ title: "", description: "", category: "road", location: "" });
      await loadComplaints();
    } catch (err) {
      setError(err.message || t.errorGeneric);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section aria-labelledby="complaints-heading" className="panel">
      <h2 id="complaints-heading">{t.navComplaints}</h2>

      <form onSubmit={handleSubmit} className="complaint-form">
        <label htmlFor="c-title">{t.complaintTitle}</label>
        <input
          id="c-title"
          type="text"
          value={form.title}
          onChange={(e) => updateField("title", e.target.value)}
          required
        />

        <label htmlFor="c-desc">{t.complaintDescription}</label>
        <textarea
          id="c-desc"
          value={form.description}
          onChange={(e) => updateField("description", e.target.value)}
          rows={3}
          required
        />

        <label htmlFor="c-category">{t.complaintCategory}</label>
        <select
          id="c-category"
          value={form.category}
          onChange={(e) => updateField("category", e.target.value)}
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c.replace("_", " ")}
            </option>
          ))}
        </select>

        <label htmlFor="c-location">{t.complaintLocation}</label>
        <input
          id="c-location"
          type="text"
          value={form.location}
          onChange={(e) => updateField("location", e.target.value)}
        />

        {error && <p className="error-text" role="alert">{error}</p>}

        <button type="submit" disabled={loading}>
          {t.submitComplaint}
        </button>
      </form>

      <h3>{t.yourComplaints}</h3>
      {complaints.length === 0 ? (
        <p>{t.noComplaints}</p>
      ) : (
        <ul className="card-list">
          {complaints.map((c) => (
            <li key={c.id} className="card">
              <h4>
                #{c.id} — {c.title}
              </h4>
              <p>{c.description}</p>
              <p>
                <strong>{t.status}:</strong>{" "}
                <span className={`status-badge status-${c.status}`}>{c.status}</span>
              </p>
              {c.location && <p>{c.location}</p>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
