// frontend/src/api.js

const API_BASE_URL = import.meta.env.DEV
  ? "/api"
  : import.meta.env.VITE_API_URL || "http://localhost:8000";

const TOKEN_KEY = "meridian_token";
const USER_KEY = "meridian_user";

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setSession({ access_token, user }) {
  localStorage.setItem(TOKEN_KEY, access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function fetchJson(url, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const token = getStoredToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const resp = await fetch(url, { ...options, headers });
  const text = await resp.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    // ignore
  }

  if (resp.status === 401) {
    clearSession();
  }

  if (!resp.ok) {
    const message =
      (data && (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail))) ||
      `Request failed with status ${resp.status}`;
    const err = new Error(message);
    err.status = resp.status;
    err.data = data;
    throw err;
  }

  if (resp.status === 204) return null;
  return data;
}

export async function registerUser(payload) {
  const data = await fetchJson(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  setSession(data);
  return data;
}

export async function loginUser(username, password) {
  const data = await fetchJson(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setSession(data);
  return data;
}

export async function fetchMe() {
  return fetchJson(`${API_BASE_URL}/auth/me`);
}

export async function getCategories() {
  return fetchJson(`${API_BASE_URL}/me/categories`);
}

export async function listEntries(params = {}) {
  const qs = new URLSearchParams();
  if (params.category) qs.set("category", params.category);
  if (params.search) qs.set("search", params.search);
  if (params.from) qs.set("from", params.from);
  if (params.to) qs.set("to", params.to);
  if (params.sort) qs.set("sort", params.sort);
  if (params.order) qs.set("order", params.order);
  if (params.limit != null) qs.set("limit", params.limit);
  if (params.offset != null) qs.set("offset", params.offset);
  const queryString = qs.toString() ? `?${qs.toString()}` : "";
  return fetchJson(`${API_BASE_URL}/me/entries${queryString}`);
}

export async function createEntry(data) {
  return fetchJson(`${API_BASE_URL}/me/entries`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateEntry(entryId, data) {
  return fetchJson(`${API_BASE_URL}/me/entries/${entryId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteEntry(entryId) {
  await fetchJson(`${API_BASE_URL}/me/entries/${entryId}`, { method: "DELETE" });
  return true;
}

export async function getActivitySummaryReport() {
  return fetchJson(`${API_BASE_URL}/me/reports/activity-summary`);
}

export async function getAnalyticsSummary() {
  return fetchJson(`${API_BASE_URL}/me/analytics/summary`);
}

export async function getTimelineReport(groupBy = "month") {
  return fetchJson(
    `${API_BASE_URL}/me/reports/timeline?group_by=${encodeURIComponent(groupBy)}`
  );
}

export async function getByCategoryReport() {
  return fetchJson(`${API_BASE_URL}/me/reports/by-category`);
}

export async function exportUserData(format = "csv") {
  const url = `${API_BASE_URL}/me/export?format=${format}`;
  const token = getStoredToken();
  const resp = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!resp.ok) {
    const text = await resp.text();
    let err;
    try {
      err = JSON.parse(text);
    } catch {
      err = { detail: text };
    }
    throw new Error(err.detail || `Export failed: ${resp.status}`);
  }
  if (format === "json") {
    return resp.json();
  }
  const blob = await resp.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "meridian_export.csv";
  a.click();
  URL.revokeObjectURL(a.href);
  return true;
}

export { API_BASE_URL };
