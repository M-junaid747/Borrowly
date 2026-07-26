import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError("Incorrect username or password.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: 400, padding: "70px 24px" }}>
      <h2>Welcome back</h2>
      <p style={{ color: "var(--color-ink-soft)", marginTop: -8 }}>Log in to message owners and manage bookings.</p>
      <form onSubmit={handleSubmit} className="card" style={{ padding: 26, marginTop: 20 }}>
        <div className="field">
          <label htmlFor="username">Username</label>
          <input id="username" className="input" value={username} onChange={(e) => setUsername(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <p className="error-text">{error}</p>}
        <button className="btn btn-primary" style={{ width: "100%" }} disabled={submitting}>
          {submitting ? "Logging in…" : "Log in"}
        </button>
      </form>
      <p style={{ marginTop: 16, color: "var(--color-ink-soft)" }}>
        No account? <Link to="/register" style={{ color: "var(--brand-start)", fontWeight: 600 }}>Sign up</Link>
      </p>
    </div>
  );
}
