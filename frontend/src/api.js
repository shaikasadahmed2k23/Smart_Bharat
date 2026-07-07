const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  chat: (message, language) =>
    request("/api/chat", { method: "POST", body: JSON.stringify({ message, language }) }),

  recommendServices: (need, language) =>
    request("/api/services/recommend", { method: "POST", body: JSON.stringify({ need, language }) }),

  documentRequirements: (service_name, language) =>
    request("/api/documents/requirements", {
      method: "POST",
      body: JSON.stringify({ service_name, language }),
    }),

  listComplaints: () => request("/api/complaints"),

  createComplaint: (data) =>
    request("/api/complaints", { method: "POST", body: JSON.stringify(data) }),

  updateComplaintStatus: (id, status) =>
    request(`/api/complaints/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }),
};
