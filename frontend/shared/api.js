// Signal API client — talks to the FastAPI backend (src/api/main.py).
// In production (Docker/HF Spaces) the frontend is served BY the same FastAPI app, so same-origin
// relative requests ("") are correct. For local dev where the frontend is served separately
// (`python -m http.server 5500` while the API runs on 8000), default to localhost:8000 instead.
// Override via `window.SIGNAL_API_BASE` before this script loads if neither guess fits.
const API_BASE =
  window.SIGNAL_API_BASE !== undefined
    ? window.SIGNAL_API_BASE
    : location.port === "5500"
    ? "http://127.0.0.1:8000"
    : "";

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
