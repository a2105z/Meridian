// frontend/src/App.jsx

import React, { useState, useEffect, useCallback } from "react";
import { BrowserRouter, Navigate, Route, Routes, useNavigate, useLocation } from "react-router-dom";

import Navbar from "./components/Navbar";
import LoginPage from "./pages/LoginPage";
import EntriesFilters from "./components/EntriesFilters";
import EntriesTable from "./components/EntriesTable";
import EntriesPagination from "./components/EntriesPagination";
import EntryForm from "./components/EntryForm";

import {
  registerUser,
  loginUser,
  fetchMe,
  getStoredToken,
  getStoredUser,
  clearSession,
  getActivitySummaryReport,
  listEntries,
  getCategories,
  createEntry,
  updateEntry,
  deleteEntry,
  exportUserData,
} from "./api";

const DEFAULT_CATEGORIES = [
  "Awards & Honors",
  "Professional Experiences",
  "Summer Programs",
  "SAT/ACT/SATII/ACTII Scores",
  "AP Scores",
  "GPA",
  "Future Plans & Competitions",
  "Personal Goals",
  "Reflection Journal",
];

function MeridianApp() {
  const navigate = useNavigate();
  const location = useLocation();

  const [user, setUser] = useState(null);
  const [bootstrapping, setBootstrapping] = useState(true);
  const [error, setError] = useState("");
  const [authMessage, setAuthMessage] = useState("");
  const [loadingAuth, setLoadingAuth] = useState(false);

  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(false);

  const [entries, setEntries] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [entriesLoading, setEntriesLoading] = useState(false);
  const [entryFilters, setEntryFilters] = useState({
    category: undefined,
    search: undefined,
    from: undefined,
    to: undefined,
    sort: "date",
    order: "desc",
    limit: 50,
    offset: 0,
  });
  const [editingEntryId, setEditingEntryId] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);
  const [categories, setCategories] = useState(DEFAULT_CATEGORIES);

  const currentView = location.pathname.startsWith("/entries")
    ? "entries"
    : location.pathname.startsWith("/dashboard")
      ? "dashboard"
      : "";

  useEffect(() => {
    async function restore() {
      const token = getStoredToken();
      const cached = getStoredUser();
      if (!token) {
        setBootstrapping(false);
        return;
      }
      if (cached) setUser(cached);
      try {
        const me = await fetchMe();
        setUser(me);
      } catch {
        clearSession();
        setUser(null);
      } finally {
        setBootstrapping(false);
      }
    }
    restore();
  }, []);

  useEffect(() => {
    if (!user) return;
    getCategories()
      .then((cats) => setCategories(cats.length ? cats : DEFAULT_CATEGORIES))
      .catch(() => setCategories(DEFAULT_CATEGORIES));
  }, [user]);

  const loadSummary = useCallback(async () => {
    setLoadingSummary(true);
    setError("");
    try {
      setSummary(await getActivitySummaryReport());
    } catch (err) {
      setError(err.message || "Failed to load summary.");
    } finally {
      setLoadingSummary(false);
    }
  }, []);

  const loadEntries = useCallback(
    async (filters = entryFilters) => {
      setEntriesLoading(true);
      setError("");
      try {
        const data = await listEntries({
          category: filters.category,
          search: filters.search,
          from: filters.from,
          to: filters.to,
          sort: filters.sort,
          order: filters.order,
          limit: filters.limit,
          offset: filters.offset,
        });
        setEntries(data.entries || []);
        setTotalCount(data.total_count ?? 0);
      } catch (err) {
        setError(err.message || "Failed to load entries.");
      } finally {
        setEntriesLoading(false);
      }
    },
    [entryFilters]
  );

  useEffect(() => {
    if (!user) return;
    if (currentView === "dashboard") loadSummary();
    if (currentView === "entries") loadEntries(entryFilters);
  }, [user, currentView]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleLoginExisting({ username, password }) {
    setError("");
    setAuthMessage("");
    if (!username || !password) {
      setError("Please enter username and password.");
      return;
    }
    setLoadingAuth(true);
    try {
      const data = await loginUser(username, password);
      setUser(data.user);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Login failed.");
    } finally {
      setLoadingAuth(false);
    }
  }

  async function handleCreateAccount({ firstName, lastName, birthday, username, password }) {
    setError("");
    setAuthMessage("");
    if (!firstName || !lastName || !birthday || !username || !password) {
      setError("Please fill in all fields for account creation.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoadingAuth(true);
    try {
      const data = await registerUser({
        first_name: firstName,
        last_name: lastName,
        birthday,
        username,
        password,
      });
      setUser(data.user);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Failed to create account.");
    } finally {
      setLoadingAuth(false);
    }
  }

  function handleLogout() {
    clearSession();
    setUser(null);
    setSummary(null);
    setEntries([]);
    setError("");
    setAuthMessage("");
    setEditingEntryId(null);
    setCategories(DEFAULT_CATEGORIES);
    navigate("/login");
  }

  async function handleCreateEntry(entryData) {
    await createEntry(entryData);
    await loadEntries(entryFilters);
    await loadSummary();
  }

  async function handleUpdateEntry(entryId, patch) {
    await updateEntry(entryId, patch);
    setEditingEntryId(null);
    await loadEntries(entryFilters);
    await loadSummary();
  }

  async function handleDeleteEntry(entryId) {
    if (!window.confirm("Delete this entry?")) return;
    try {
      await deleteEntry(entryId);
      setEditingEntryId(null);
      await loadEntries(entryFilters);
      await loadSummary();
    } catch (err) {
      setError(err.message || "Failed to delete entry.");
    }
  }

  async function handleExport(format) {
    setExporting(true);
    setError("");
    setExportSuccess(false);
    try {
      if (format === "json") {
        const data = await exportUserData("json");
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `meridian_export_${user.username}.json`;
        a.click();
        URL.revokeObjectURL(a.href);
      } else {
        await exportUserData("csv");
      }
      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 2500);
    } catch (err) {
      setError(err.message || "Export failed.");
    } finally {
      setExporting(false);
    }
  }

  function handleFiltersChange(newFilters) {
    const merged = { ...entryFilters, ...newFilters };
    setEntryFilters(merged);
    loadEntries(merged);
  }

  if (bootstrapping) {
    return (
      <div className="app-root">
        <main className="app-main">
          <p className="hint loading-placeholder">Loading Meridian…</p>
        </main>
      </div>
    );
  }

  return (
    <div className="app-root">
      {user && (
        <Navbar
          appTitle="Meridian"
          username={user?.username || null}
          currentView={currentView}
          onDashboardClick={() => navigate("/dashboard")}
          onEntriesClick={() => navigate("/entries")}
          onExport={user ? (format) => handleExport(format) : null}
          onLogout={handleLogout}
        />
      )}

      <main className={"app-main" + (!user ? " auth-mode" : "")}>
        {user && error && <div className="error-banner">{error}</div>}

        <Routes>
          <Route
            path="/login"
            element={
              user ? (
                <Navigate to="/dashboard" replace />
              ) : (
                <LoginPage
                  onLogin={handleLoginExisting}
                  onCreateAccount={handleCreateAccount}
                  loading={loadingAuth}
                  error={error}
                  infoMessage={authMessage}
                />
              )
            }
          />
          <Route
            path="/dashboard"
            element={
              !user ? (
                <Navigate to="/login" replace />
              ) : (
                <div className="card">
                  <h1>Dashboard</h1>
                  <p className="card-subtitle">
                    A clear view of your academic momentum — secured and scoped only to your account.
                  </p>
                  <div className="dashboard-actions">
                    <button className="secondary-button" type="button" onClick={loadSummary} disabled={loadingSummary}>
                      {loadingSummary ? "Refreshing..." : "Refresh"}
                    </button>
                    <div className="export-buttons">
                      <span className="export-label">Export:</span>
                      {exportSuccess && <span className="export-success">Downloaded ✓</span>}
                      <button type="button" className="secondary-button export-btn" onClick={() => handleExport("json")} disabled={exporting}>
                        JSON
                      </button>
                      <button type="button" className="secondary-button export-btn" onClick={() => handleExport("csv")} disabled={exporting}>
                        CSV
                      </button>
                    </div>
                  </div>
                  {loadingSummary && !summary && <p className="hint loading-placeholder">Loading summary...</p>}
                  {summary && (
                    <>
                      <div className="summary-grid">
                        <SummaryStat label="Total entries" value={summary.total_entries} />
                        <SummaryStat label="First entry" value={summary.first_entry_date || "—"} />
                        <SummaryStat label="Most recent" value={summary.last_entry_date || "—"} />
                      </div>
                      <h2 className="section-title">Entries per category</h2>
                      <div className="category-list">
                        {Object.entries(summary.entries_per_category || {}).map(([category, count]) => (
                          <div key={category} className="category-item">
                            <span className="category-name">{category}</span>
                            <span className="category-count">{count}</span>
                          </div>
                        ))}
                      </div>
                      {summary.timeline_by_month?.length > 0 && (
                        <>
                          <h2 className="section-title">Activity by month</h2>
                          <div className="timeline-table-wrap">
                            <table className="timeline-table">
                              <thead>
                                <tr>
                                  <th>Month</th>
                                  <th>Entries</th>
                                </tr>
                              </thead>
                              <tbody>
                                {summary.timeline_by_month.map(({ period, count }) => (
                                  <tr key={period}>
                                    <td>{period}</td>
                                    <td>{count}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </>
                      )}
                    </>
                  )}
                </div>
              )
            }
          />
          <Route
            path="/entries"
            element={
              !user ? (
                <Navigate to="/login" replace />
              ) : (
                <EntriesView
                  categories={categories}
                  entries={entries}
                  totalCount={totalCount}
                  entriesLoading={entriesLoading}
                  entryFilters={entryFilters}
                  editingEntryId={editingEntryId}
                  setEditingEntryId={setEditingEntryId}
                  onFiltersChange={handleFiltersChange}
                  onRefresh={() => loadEntries(entryFilters)}
                  onCreate={handleCreateEntry}
                  onUpdate={handleUpdateEntry}
                  onDelete={handleDeleteEntry}
                />
              )
            }
          />
          <Route path="*" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
        </Routes>
      </main>
    </div>
  );
}

function EntriesView({
  categories,
  entries,
  totalCount,
  entriesLoading,
  entryFilters,
  editingEntryId,
  setEditingEntryId,
  onFiltersChange,
  onRefresh,
  onCreate,
  onUpdate,
  onDelete,
}) {
  const editingEntry = editingEntryId ? entries.find((e) => e.id === editingEntryId) : null;

  return (
    <div className="card">
      <h1>Entries</h1>
      <p className="card-subtitle">Add, filter, and refine what matters in your journey.</p>

      <EntriesFilters
        filters={entryFilters}
        categories={categories}
        onFiltersChange={onFiltersChange}
        onRefresh={onRefresh}
        loading={entriesLoading}
      />

      <h2 className="section-title">Add new entry</h2>
      <EntryForm categories={categories} onSubmit={onCreate} loading={entriesLoading} />

      {editingEntry && (
        <>
          <h2 className="section-title">Edit entry</h2>
          <EntryForm
            key={editingEntryId}
            categories={categories}
            onSubmit={async (data) => onUpdate(editingEntryId, data)}
            onCancel={() => setEditingEntryId(null)}
            loading={entriesLoading}
            submitLabel="Save changes"
            initialCategory={editingEntry.category}
            initialDate={editingEntry.date}
            initialDetails={editingEntry.category === "AP Scores" ? "" : editingEntry.details}
            initialApExam={
              editingEntry.category === "AP Scores" && editingEntry.details?.includes(" - ")
                ? editingEntry.details.split(" - ")[0]?.trim() ?? ""
                : ""
            }
            initialApScore={
              editingEntry.category === "AP Scores" && editingEntry.details?.includes(" - ")
                ? editingEntry.details.split(" - ")[1]?.trim() ?? ""
                : ""
            }
          />
        </>
      )}

      <h2 className="section-title" style={{ marginTop: "1.5rem" }}>
        Existing entries
        {totalCount > 0 && <span className="entries-count"> ({totalCount})</span>}
      </h2>
      <EntriesTable
        entries={entries}
        loading={entriesLoading}
        onEditEntry={(id) => setEditingEntryId(id)}
        onDeleteEntry={onDelete}
        showActions={true}
      />
      <EntriesPagination
        filters={entryFilters}
        totalCount={totalCount}
        onFiltersChange={onFiltersChange}
        loading={entriesLoading}
      />
    </div>
  );
}

function SummaryStat({ label, value }) {
  return (
    <div className="summary-stat">
      <div className="summary-label">{label}</div>
      <div className="summary-value">{value}</div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <MeridianApp />
    </BrowserRouter>
  );
}
