import { useState, useEffect } from "react";
import { LANGUAGES, STRINGS } from "./i18n";
import ChatCompanion from "./components/ChatCompanion";
import ServiceFinder from "./components/ServiceFinder";
import DocumentChecklist from "./components/DocumentChecklist";
import ComplaintTracker from "./components/ComplaintTracker";

const TABS = [
  { id: "chat", labelKey: "navChat" },
  { id: "services", labelKey: "navServices" },
  { id: "documents", labelKey: "navDocuments" },
  { id: "complaints", labelKey: "navComplaints" },
];

export default function App() {
  const [language, setLanguage] = useState("en");
  const [activeTab, setActiveTab] = useState("chat");
  const t = STRINGS[language];

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  return (
    <div className="app">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <header className="app-header">
        <div>
          <h1>{t.appName}</h1>
          <p className="tagline">{t.tagline}</p>
        </div>

        <div className="lang-switcher">
          <label htmlFor="lang-select" className="sr-only">
            Language
          </label>
          <select
            id="lang-select"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </div>
      </header>

      <nav aria-label="Main navigation" className="tab-nav">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`tab-button ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {t[tab.labelKey]}
          </button>
        ))}
      </nav>

      <main id="main-content" className="app-main">
        {activeTab === "chat" && <ChatCompanion t={t} language={language} />}
        {activeTab === "services" && <ServiceFinder t={t} language={language} />}
        {activeTab === "documents" && <DocumentChecklist t={t} language={language} />}
        {activeTab === "complaints" && <ComplaintTracker t={t} language={language} />}
      </main>

      <footer className="app-footer">
        <details className="transparency-note">
          <summary>How Smart Bharat uses your data</summary>
          <p>
            Complaints are stored to track status only. Chat messages are sent to Gemini
            to generate a reply and are not stored. We never ask for Aadhaar numbers,
            bank details, or passwords. All service and document information links to
            official government portals.
          </p>
        </details>
        <p>Smart Bharat — Build. Learn. Lead. Impact.</p>
      </footer>
    </div>
  );
}
