import React, { useState } from "react";

function EntryForm({
  categories = [],
  onSubmit,
  onCancel,
  loading = false,
  error = "",
  initialCategory = "",
  initialDate = "",
  initialDetails = "",
  initialApExam = "",
  initialApScore = "",
  submitLabel = "Add entry",
}) {
  const [category, setCategory] = useState(initialCategory || "");
  const [date, setDate] = useState(initialDate || "");
  const [details, setDetails] = useState(initialDetails || "");
  const [apExam, setApExam] = useState(initialApExam || "");
  const [apScore, setApScore] = useState(initialApScore || "");
  const [localError, setLocalError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError("");

    if (!category) {
      setLocalError("Please select a category.");
      return;
    }
    if (!date) {
      setLocalError("Please choose a date.");
      return;
    }

    const trimmedDetails = details.trim();

    const entryData = {
      category,
      date, // "YYYY-MM-DD" → FastAPI/Pydantic will parse to date
      details: "",
    };

    // Special behavior for AP Scores, like in your Tkinter app
    if (category === "AP Scores") {
      if (!apExam.trim() || !apScore.trim()) {
        setLocalError("Please enter AP exam and score.");
        return;
      }
      entryData.details = `${apExam.trim()} - ${apScore.trim()}`;
    } else {
      if (!trimmedDetails) {
        setLocalError("Please enter some details.");
        return;
      }
      entryData.details = trimmedDetails;
    }

    try {
      await onSubmit?.(entryData);

      // Reset details fields after successful submit
      if (category === "AP Scores") {
        setApExam("");
        setApScore("");
      } else {
        setDetails("");
      }
      // We keep category & date so user can quickly add similar entries
    } catch (err) {
      console.error(err);
      setLocalError(err.message || "Failed to submit entry.");
    }
  };

  const displayError = error || localError;

  return (
    <form onSubmit={handleSubmit} className="form" style={{ marginTop: "1rem" }}>
      {displayError && <div className="error-banner">{displayError}</div>}

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.75rem",
        }}
      >
        {/* Category select */}
        <label className="form-label" style={{ flex: "1 1 180px" }}>
          Category
          <select
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              // When switching away from AP Scores, clear AP fields
              if (e.target.value !== "AP Scores") {
                setApExam("");
                setApScore("");
              }
            }}
            className="form-input"
          >
            <option value="">Select category...</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </label>

        {/* Date input */}
        <label className="form-label" style={{ flex: "0 0 160px" }}>
          Date
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="form-input"
          />
        </label>
      </div>

      {/* Details vs AP-specific inputs */}
      {category === "AP Scores" ? (
        <>
          <label className="form-label" style={{ marginTop: "0.75rem" }}>
            AP Exam
            <input
              type="text"
              value={apExam}
              onChange={(e) => setApExam(e.target.value)}
              className="form-input"
              placeholder="e.g. AP Biology"
            />
          </label>

          <label className="form-label" style={{ marginTop: "0.75rem" }}>
            Score
            <input
              type="text"
              value={apScore}
              onChange={(e) => setApScore(e.target.value)}
              className="form-input"
              placeholder="e.g. 5"
            />
          </label>
        </>
      ) : (
        <label className="form-label" style={{ marginTop: "0.75rem" }}>
          Details
          <textarea
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            className="form-input"
            rows={3}
            placeholder="Describe the achievement, score, experience, or reflection..."
            style={{ resize: "vertical" }}
          />
        </label>
      )}

      <div className="form-actions" style={{ marginTop: "0.5rem", gap: "0.5rem" }}>
        <button
          type="submit"
          className="primary-button"
          disabled={loading}
        >
          {loading ? "Saving..." : submitLabel}
        </button>
        {onCancel && (
          <button
            type="button"
            className="secondary-button"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}

export default EntryForm;
