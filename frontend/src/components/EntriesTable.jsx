import React from "react";

function EntriesTable({
  entries = [],
  loading = false,
  onEditEntry,
  onDeleteEntry,
  showActions = true,
}) {
  const hasActions = Boolean((onEditEntry || onDeleteEntry) && showActions);

  if (loading && entries.length === 0) {
    return <p className="hint loading-placeholder">Loading entries...</p>;
  }

  if (!loading && entries.length === 0) {
    return (
      <p className="hint">
        No entries to display. Add entries above or import legacy data, then
        refresh.
      </p>
    );
  }

  return (
    <table className="entries-table">
      <thead>
        <tr>
          <th style={{ width: "110px" }}>Date</th>
          <th style={{ width: "180px" }}>Category</th>
          <th>Details</th>
          {hasActions && <th style={{ width: "140px" }}>Actions</th>}
        </tr>
      </thead>
      <tbody>
        {entries.map((entry) => (
          <tr key={entry.id}>
            <td>{entry.date}</td>
            <td>{entry.category}</td>
            <td>{entry.details}</td>
            {hasActions && (
              <td>
                <div className="entry-actions">
                  {onEditEntry && (
                    <button
                      type="button"
                      className="action-btn action-edit"
                      onClick={() => onEditEntry(entry.id)}
                      title="Edit entry"
                    >
                      Edit
                    </button>
                  )}
                  {onDeleteEntry && (
                    <button
                      type="button"
                      className="action-btn action-delete"
                      onClick={() => onDeleteEntry(entry.id)}
                      title="Delete entry"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default EntriesTable;
