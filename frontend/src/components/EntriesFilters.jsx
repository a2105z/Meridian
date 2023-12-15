import React from "react";

function EntriesFilters({
  filters = {},
  categories = [],
  onFiltersChange,
  onRefresh,
  loading = false,
}) {
  const handleChange = (updates) => {
    onFiltersChange(updates);
  };

  return (
    <div className="entries-filters">
      <div className="filters-row">
        <div className="filter-group">
          <label className="filter-label">Category</label>
          <select
            className="form-input filter-select"
            value={filters.category ?? ""}
            onChange={(e) =>
              handleChange({
                category: e.target.value || undefined,
                offset: 0,
              })
            }
          >
            <option value="">All categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label">From date</label>
          <input
            type="date"
            className="form-input"
            value={filters.from ?? ""}
            onChange={(e) =>
              handleChange({ from: e.target.value || undefined, offset: 0 })
            }
          />
        </div>

        <div className="filter-group">
          <label className="filter-label">To date</label>
          <input
            type="date"
            className="form-input"
            value={filters.to ?? ""}
            onChange={(e) =>
              handleChange({ to: e.target.value || undefined, offset: 0 })
            }
          />
        </div>

        <div className="filter-group">
          <label className="filter-label">Search</label>
          <input
            type="text"
            className="form-input"
            value={filters.search ?? ""}
            onChange={(e) =>
              handleChange({ search: e.target.value || undefined, offset: 0 })
            }
            placeholder="Search in details..."
          />
        </div>

        <div className="filter-group">
          <label className="filter-label">Per page</label>
          <select
            className="form-input filter-select"
            value={filters.limit ?? 50}
            onChange={(e) =>
              handleChange({
                limit: Number(e.target.value),
                offset: 0,
              })
            }
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label">Sort by</label>
          <select
            className="form-input filter-select"
            value={`${filters.sort || "date"}-${filters.order || "desc"}`}
            onChange={(e) => {
              const [sort, order] = e.target.value.split("-");
              handleChange({ sort, order, offset: 0 });
            }}
          >
            <option value="date-desc">Date (newest first)</option>
            <option value="date-asc">Date (oldest first)</option>
            <option value="category-asc">Category (A–Z)</option>
            <option value="category-desc">Category (Z–A)</option>
            <option value="created_at-desc">Created (newest first)</option>
            <option value="created_at-asc">Created (oldest first)</option>
          </select>
        </div>

        <div className="filter-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={onRefresh}
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default EntriesFilters;
