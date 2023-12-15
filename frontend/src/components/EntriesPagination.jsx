import React from "react";

function EntriesPagination({
  filters = {},
  totalCount = 0,
  onFiltersChange,
  loading = false,
}) {
  const limit = filters.limit ?? 50;
  const offset = filters.offset ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalCount / limit));
  const currentPage = Math.floor(offset / limit) + 1;
  const hasPrev = offset > 0;
  const hasNext = offset + limit < totalCount;

  const goToPage = (newOffset) => {
    onFiltersChange({ offset: newOffset });
  };

  if (totalCount <= limit) return null;

  return (
    <div className="pagination">
      <span className="pagination-info">
        Showing {offset + 1}–{Math.min(offset + limit, totalCount)} of{" "}
        {totalCount}
      </span>
      <div className="pagination-buttons">
        <button
          type="button"
          className="secondary-button pagination-btn"
          onClick={() => goToPage(0)}
          disabled={!hasPrev || loading}
        >
          First
        </button>
        <button
          type="button"
          className="secondary-button pagination-btn"
          onClick={() => goToPage(Math.max(0, offset - limit))}
          disabled={!hasPrev || loading}
        >
          Previous
        </button>
        <span className="pagination-page">
          Page {currentPage} of {totalPages}
        </span>
        <button
          type="button"
          className="secondary-button pagination-btn"
          onClick={() => goToPage(offset + limit)}
          disabled={!hasNext || loading}
        >
          Next
        </button>
        <button
          type="button"
          className="secondary-button pagination-btn"
          onClick={() => goToPage((totalPages - 1) * limit)}
          disabled={!hasNext || loading}
        >
          Last
        </button>
      </div>
    </div>
  );
}

export default EntriesPagination;
