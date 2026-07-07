import { useState } from "react";
import { api } from "../api";

export default function DocumentChecklist({ t, language }) {
  const [serviceName, setServiceName] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!serviceName.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await api.documentRequirements(serviceName, language);
      setResult(res);
    } catch (err) {
      setError(err.message || t.errorGeneric);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section aria-labelledby="documents-heading" className="panel">
      <h2 id="documents-heading">{t.navDocuments}</h2>
      <form onSubmit={handleSubmit} className="inline-form">
        <label htmlFor="doc-service" className="sr-only">
          {t.documentServicePlaceholder}
        </label>
        <input
          id="doc-service"
          type="text"
          value={serviceName}
          onChange={(e) => setServiceName(e.target.value)}
          placeholder={t.documentServicePlaceholder}
        />
        <button type="submit" disabled={loading || !serviceName.trim()}>
          {t.getDocuments}
        </button>
      </form>

      {error && <p className="error-text" role="alert">{error}</p>}

      {result && (
        <div className="card">
          <h3>{result.service}</h3>
          <p>{t.documentsNeeded}:</p>
          <ul>
            {result.documents.map((d) => (
              <li key={d}>{d}</li>
            ))}
          </ul>
          <a href={result.portal} target="_blank" rel="noopener noreferrer">
            {t.portal}
          </a>
        </div>
      )}
    </section>
  );
}
