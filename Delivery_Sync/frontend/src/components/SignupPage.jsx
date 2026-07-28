import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import "../styles/auth.css";

export default function SignupPage({ onSwitchToLogin }) {
  const { signup } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [role, setRole] = useState("agent");
  const [orgMode, setOrgMode] = useState("join"); // "join" or "create"
  const [orgName, setOrgName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createdInviteCode, setCreatedInviteCode] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      const result = await signup({
        username,
        email,
        password,
        role,
        display_name: displayName,
        org_name: orgMode === "create" ? orgName : undefined,
        invite_code: orgMode === "join" ? inviteCode : undefined,
      });
      if (result.org_invite_code) {
        // A brand new organization was just created — show its invite
        // code prominently, since the user needs to share it with any
        // teammates who'll join afterward, and it's only ever shown once.
        setCreatedInviteCode(result.org_invite_code);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  // After creating a new org, show the invite code before letting them
  // continue into the app — this is genuinely important info they'd
  // otherwise have no way to retrieve again from this screen.
  if (createdInviteCode) {
    return (
      <div className="auth-page-wrapper">
        <div className="auth-card">
          <h2>Organization Created!</h2>
          <p style={{ fontSize: "13.5px", color: "var(--text-secondary)", marginBottom: "12px" }}>
            Share this invite code with your team so they can join your
            organization when they sign up. Save it now — it won't be shown
            again here (though any admin can look it up later).
          </p>
          <div
            className="mono"
            style={{
              backgroundColor: "var(--bg-input)",
              border: "1px solid var(--border-color-light)",
              borderRadius: "var(--radius-sm)",
              padding: "14px",
              textAlign: "center",
              fontSize: "20px",
              fontWeight: 600,
              letterSpacing: "0.1em",
              marginBottom: "16px",
            }}
          >
            {createdInviteCode}
          </div>
          <button
            className="auth-submit-btn"
            onClick={() => window.location.reload()}
          >
            Continue to App
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page-wrapper">
      <button className="auth-theme-toggle" onClick={toggleTheme}>
        {theme === "dark" ? "☀ Light" : "☾ Dark"}
      </button>
      <div className="auth-card">
        <h2>Create your account</h2>
        <form onSubmit={handleSubmit}>
          <div className="auth-field">
            <label>Organization</label>
            <div style={{ display: "flex", gap: "16px", marginBottom: "8px", fontSize: "13px" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
                <input type="radio" checked={orgMode === "join"} onChange={() => setOrgMode("join")} />
                Join existing
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
                <input type="radio" checked={orgMode === "create"} onChange={() => setOrgMode("create")} />
                Create new
              </label>
            </div>

            {orgMode === "join" ? (
              <input
                type="text"
                value={inviteCode}
                onChange={(e) => setInviteCode(e.target.value)}
                placeholder="Invite code from your admin"
                required
              />
            ) : (
              <input
                type="text"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                placeholder="Your company/organization name"
                required
              />
            )}
          </div>

          {orgMode === "create" && (
            <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "-8px", marginBottom: "16px" }}>
              You'll become this organization's admin automatically.
            </p>
          )}

          <div className="auth-field">
            <label>Display name</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
            />
          </div>

          <div className="auth-field">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="auth-field">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="auth-field">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {orgMode === "join" && (
            <div className="auth-field">
              <label>I am a...</label>
              <select value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="agent">Delivery Agent</option>
                <option value="dispatcher">Dispatcher</option>
              </select>
            </div>
          )}

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" className="auth-submit-btn" disabled={isSubmitting}>
            {isSubmitting ? "Creating account..." : "Sign up"}
          </button>
        </form>

        <p className="auth-switch-text">
          Already have an account?{" "}
          <button className="auth-switch-link" onClick={onSwitchToLogin}>
            Log in
          </button>
        </p>
      </div>
    </div>
  );
}
