import { useState, useRef, useEffect } from "react";
import { api } from "../api";

export default function ChatCompanion({ t, language }) {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Namaste! How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const logRef = useRef(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [messages]);

  async function handleSubmit(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setLoading(true);
    setError("");
    try {
      const res = await api.chat(text, language);
      setMessages((m) => [...m, { role: "assistant", text: res.reply }]);
    } catch (err) {
      setError(err.message || t.errorGeneric);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section aria-labelledby="chat-heading" className="panel">
      <h2 id="chat-heading">{t.navChat}</h2>
      <div
        className="chat-log"
        role="log"
        aria-live="polite"
        aria-label={t.navChat}
        ref={logRef}
      >
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble ${m.role}`}>
            {m.text}
          </div>
        ))}
        {loading && <div className="chat-bubble assistant chat-loading">{t.thinking}</div>}
      </div>

      {error && <p className="error-text" role="alert">{error}</p>}

      <form onSubmit={handleSubmit} className="chat-form">
        <label htmlFor="chat-input" className="sr-only">
          {t.chatPlaceholder}
        </label>
        <input
          id="chat-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t.chatPlaceholder}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {t.send}
        </button>
      </form>
    </section>
  );
}
