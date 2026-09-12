/**
 * Centralized API client. Every backend call goes through here — no
 * component calls fetch() directly. This keeps the API contract in
 * one place, matching the pattern used on the backend (one settings
 * module, one place that knows the DB URL, etc.)
 */
const BASE = "/api"; // proxied to FastAPI by vite.config.js in dev

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export function fetchMetrics({ company, fiscalYear } = {}) {
  const params = new URLSearchParams();
  if (company) params.set("company", company);
  if (fiscalYear) params.set("fiscal_year", fiscalYear);
  const query = params.toString() ? `?${params.toString()}` : "";
  return request(`/metrics${query}`);
}

export function sendChatMessage({ question, company, fiscalYear }) {
  return request("/chat", {
    method: "POST",
    body: JSON.stringify({ question, company, fiscal_year: fiscalYear }),
  });
}

export function ingestReport({ file, company, fiscalYear }) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("company", company);
  formData.append("fiscal_year", fiscalYear);
  return request("/ingest", { method: "POST", body: formData });
}