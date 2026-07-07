import { useState } from "react";
import { api } from "../api";

export default function ServiceFinder({ t, language }) {
  const [need, setNeed] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!need.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.recommendServices(need, language);
      setResults(res.results);
    } catch (err) {
      setError(err.message || t.errorGeneric);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section aria-labelledby="services-heading" className="panel">
      <h2 id="services-heading">{t.navServices}</h2>
      <form onSubmit={handleSubmit} className="inline-form">
        <label htmlFor="service-need" className="sr-only">
          {t.serviceNeedPlaceholder}
        </label>
        <input
          id="service-need"
          type="text"
          value={need}
          onChange={(e) => setNeed(e.target.value)}
          placeholder={t.serviceNeedPlaceholder}
        />
        <button type="submit" disabled={loading || !need.trim()}>
          {t.findServices}
        </button>
      </form>

      {error && <p className="error-text" role="alert">{error}</p>}

      <ul className="card-list">
        {results?.map((s) => (
          <li key={s.name} className="card">
            <h3>{s.name}</h3>
            <p>{s.description}</p>
            <a href={s.portal} target="_blank" rel="noopener noreferrer">
              {t.portal}
            </a>
          </li>
        ))}
        {results && results.length === 0 && <p>{t.errorGeneric}</p>}
      </ul>
    </section>
  );
}
