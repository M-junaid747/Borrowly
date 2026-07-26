import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";
import RoleSwitch from "./RoleSwitch.jsx";

const UNREAD_POLL_MS = 10000;

export default function NavBar() {
  const { user, logout, switchRole } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!user) return undefined;
    const poll = () => api.unreadCount().then((data) => setUnreadCount(data.count)).catch(() => {});
    poll();
    const interval = setInterval(poll, UNREAD_POLL_MS);
    return () => clearInterval(interval);
  }, [user]);

  const handleSwitch = async (role) => {
    await switchRole(role);
    navigate("/dashboard");
  };

  return (
    <header style={{ borderBottom: "1px solid var(--color-border)", background: "var(--color-surface)", position: "sticky", top: 0, zIndex: 10 }}>
      <div className="container" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 24px", gap: 20 }}>
        <Link to="/" style={{ textDecoration: "none" }}>
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "1.5rem",
              fontWeight: 800,
              backgroundImage: "var(--gradient-brand)",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              color: "transparent",
            }}
          >
            Borrowly
          </span>
        </Link>

        <nav style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <Link to="/" style={{ textDecoration: "none", color: "var(--color-ink-soft)", fontWeight: 500, fontSize: "0.92rem" }}>
            Browse
          </Link>

          {user ? (
            <>
              <RoleSwitch activeRole={user.active_role} onSwitch={handleSwitch} />
              <Link to="/dashboard" style={{ textDecoration: "none", color: "var(--color-ink-soft)", fontWeight: 500, fontSize: "0.92rem", position: "relative" }}>
                Dashboard
                {unreadCount > 0 && (
                  <span
                    style={{
                      position: "absolute", top: -8, right: -14, background: "var(--color-accent)", color: "#fff",
                      borderRadius: 999, fontSize: "0.68rem", fontWeight: 700, padding: "1px 6px", lineHeight: 1.4,
                    }}
                  >
                    {unreadCount}
                  </span>
                )}
              </Link>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => {
                  logout();
                  navigate("/");
                }}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" style={{ textDecoration: "none", color: "var(--color-ink-soft)", fontWeight: 500, fontSize: "0.92rem" }}>
                Log in
              </Link>
              <Link to="/register" className="btn btn-primary btn-sm" style={{ textDecoration: "none" }}>
                Sign up
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
