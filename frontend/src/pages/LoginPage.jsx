import React, { useEffect, useState } from "react";

const CHAOS_ITEMS = [
  { label: "AP Bio — ?", x: 8, y: 18, rot: -8 },
  { label: "Internship offer.pdf", x: 62, y: 12, rot: 6 },
  { label: "SAT 1480?", x: 28, y: 48, rot: 10 },
  { label: "Summer program", x: 70, y: 42, rot: -12 },
  { label: "Award — lost in Drive", x: 14, y: 72, rot: 4 },
  { label: "Recommendation draft", x: 58, y: 70, rot: -5 },
];

const ORDERED_ITEMS = [
  { label: "Awards", year: "2023" },
  { label: "Scores", year: "2024" },
  { label: "Programs", year: "2025" },
  { label: "Goals", year: "Now" },
];

function LoginPage({
  onLogin,
  onCreateAccount,
  loading = false,
  error = "",
  infoMessage = "",
}) {
  const [mode, setMode] = useState("login"); // login | signup
  const [story, setStory] = useState("problem"); // problem | solution
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [birthday, setBirthday] = useState("");
  const [signupUsername, setSignupUsername] = useState("");
  const [signupPassword, setSignupPassword] = useState("");

  useEffect(() => {
    const id = setInterval(() => {
      setStory((s) => (s === "problem" ? "solution" : "problem"));
    }, 4200);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="auth-shell">
      <section className={`auth-story ${story === "solution" ? "is-solution" : "is-problem"}`} aria-hidden="true">
        <div className="auth-story-glow" />
        <p className="auth-brand">Meridian</p>
        <div className="auth-story-copy">
          <p className="auth-kicker">{story === "problem" ? "The problem" : "The solution"}</p>
          <h2 className="auth-headline">
            {story === "problem" ? (
              <>
                Achievements scatter.
                <span> Applications suffer.</span>
              </>
            ) : (
              <>
                One path.
                <span> Every milestone in place.</span>
              </>
            )}
          </h2>
          <p className="auth-sub">
            {story === "problem"
              ? "Scores in one tab. Awards in another. Programs buried in email. When opportunity arrives, the story is incomplete."
              : "Meridian turns chaos into a living academic narrative — searchable, analyzable, and ready to export."}
          </p>
        </div>

        <div className="auth-stage">
          {story === "problem" ? (
            <div className="chaos-field">
              {CHAOS_ITEMS.map((item) => (
                <div
                  key={item.label}
                  className="chaos-card"
                  style={{
                    left: `${item.x}%`,
                    top: `${item.y}%`,
                    transform: `rotate(${item.rot}deg)`,
                  }}
                >
                  {item.label}
                </div>
              ))}
              <div className="chaos-noise" />
            </div>
          ) : (
            <div className="solution-field">
              <div className="meridian-line" />
              {ORDERED_ITEMS.map((item, i) => (
                <div key={item.label} className="solution-node" style={{ animationDelay: `${i * 0.12}s` }}>
                  <span className="solution-year">{item.year}</span>
                  <span className="solution-dot" />
                  <span className="solution-label">{item.label}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="auth-story-progress">
          <button
            type="button"
            className={story === "problem" ? "active" : ""}
            onClick={() => setStory("problem")}
            aria-label="Show problem"
          />
          <button
            type="button"
            className={story === "solution" ? "active" : ""}
            onClick={() => setStory("solution")}
            aria-label="Show solution"
          />
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-panel-inner">
          <p className="auth-panel-brand">Meridian</p>
          <h1 className="auth-panel-title">{mode === "login" ? "Welcome back" : "Begin your path"}</h1>
          <p className="auth-panel-sub">
            {mode === "login"
              ? "Sign in to continue your academic journey."
              : "Create an account to organize awards, scores, programs, and goals."}
          </p>

          <div className="auth-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              className={mode === "login" ? "active" : ""}
              onClick={() => setMode("login")}
            >
              Sign in
            </button>
            <button
              type="button"
              role="tab"
              className={mode === "signup" ? "active" : ""}
              onClick={() => setMode("signup")}
            >
              Create account
            </button>
          </div>

          {error && <div className="error-banner">{error}</div>}
          {infoMessage && <p className="hint">{infoMessage}</p>}

          {mode === "login" ? (
            <form
              className="form"
              onSubmit={(e) => {
                e.preventDefault();
                onLogin?.({
                  username: loginUsername.trim(),
                  password: loginPassword,
                });
              }}
            >
              <label className="form-label">
                Username
                <input
                  className="form-input"
                  value={loginUsername}
                  onChange={(e) => setLoginUsername(e.target.value)}
                  placeholder="your_username"
                  autoComplete="username"
                  required
                />
              </label>
              <label className="form-label">
                Password
                <input
                  type="password"
                  className="form-input"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="Your password"
                  autoComplete="current-password"
                  required
                />
              </label>
              <button type="submit" className="primary-button auth-submit" disabled={loading}>
                {loading ? "Signing in…" : "Enter Meridian"}
              </button>
            </form>
          ) : (
            <form
              className="form"
              onSubmit={(e) => {
                e.preventDefault();
                onCreateAccount?.({
                  firstName: firstName.trim(),
                  lastName: lastName.trim(),
                  birthday,
                  username: signupUsername.trim(),
                  password: signupPassword,
                });
              }}
            >
              <div className="auth-name-row">
                <label className="form-label">
                  First name
                  <input className="form-input" value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
                </label>
                <label className="form-label">
                  Last name
                  <input className="form-input" value={lastName} onChange={(e) => setLastName(e.target.value)} required />
                </label>
              </div>
              <label className="form-label">
                Birthday
                <input type="date" className="form-input" value={birthday} onChange={(e) => setBirthday(e.target.value)} required />
              </label>
              <label className="form-label">
                Username
                <input
                  className="form-input"
                  value={signupUsername}
                  onChange={(e) => setSignupUsername(e.target.value)}
                  placeholder="letters, numbers, _"
                  autoComplete="username"
                  required
                />
              </label>
              <label className="form-label">
                Password
                <input
                  type="password"
                  className="form-input"
                  value={signupPassword}
                  onChange={(e) => setSignupPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
              </label>
              <button type="submit" className="primary-button auth-submit" disabled={loading}>
                {loading ? "Creating…" : "Create account"}
              </button>
            </form>
          )}
        </div>
      </section>
    </div>
  );
}

export default LoginPage;
