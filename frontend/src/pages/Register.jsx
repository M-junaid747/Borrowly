import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Register() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await api.register(form);
      await login(form.username, form.password);
      navigate("/");
    } catch (err) {
      setError("Could not create account. Username or email may already be taken.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: 420, padding: "70px 24px" }}>
      <h2>Create an account</h2>
      <p style={{ color: "var(--color-ink-soft)", marginTop: -8 }}>
        One account for everything — rent items from others, or list your own to earn from. Switch anytime from the nav bar.
      </p>
      <form onSubmit={handleSubmit} className="card" style={{ padding: 26, marginTop: 16 }}>
        <div className="field">
          <label htmlFor="username">Username</label>
          <input id="username" className="input" value={form.username} onChange={update("username")} required />
        </div>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" className="input" value={form.email} onChange={update("email")} required />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" className="input" minLength={8} value={form.password} onChange={update("password")} required />
        </div>
        {error && <p className="error-text">{error}</p>}
        <button className="btn btn-primary" style={{ width: "100%" }} disabled={submitting}>
          {submitting ? "Creating…" : "Sign up"}
        </button>
      </form>
    </div>
  );
}
