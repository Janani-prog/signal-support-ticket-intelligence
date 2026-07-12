// Signal API client — talks to the FastAPI backend (src/api/main.py).
// API_BASE is same-origin by default (frontend served by the same host, or a reverse proxy in
// front of both); override via `window.SIGNAL_API_BASE` before this script loads if needed.
const API_BASE = window.SIGNAL_API_BASE || "http://127.0.0.1:8000";

async function apiRequest(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch (_) {
      /* ignore */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

const SignalAPI = {
  health: () => apiRequest("/health"),
  stats: () => apiRequest("/stats"),
  classify: (text) =>
    apiRequest("/classify", { method: "POST", body: JSON.stringify({ text }) }),
  listClusters: () => apiRequest("/clusters"),
  getCluster: (id) => apiRequest(`/clusters/${id}`),
  ask: (question, topK = 5) =>
    apiRequest("/ask", { method: "POST", body: JSON.stringify({ question, top_k: topK }) }),
};
