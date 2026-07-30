import React from "react";
import { Link } from "react-router-dom";

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer style={{ background: "var(--color-ink)", color: "rgba(255,255,255,0.85)", marginTop: 60 }}>
      <div
        className="container"
        style={{
          padding: "40px 24px 24px",
          display: "grid",
          gridTemplateColumns: "1.4fr 1fr 1fr 1fr",
          gap: 32,
        }}
      >
        <div>
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "1.3rem",
              fontWeight: 800,
              color: "#fff",
            }}
          >
            Borrowly
          </span>
          <p style={{ color: "rgba(255,255,255,0.65)", fontSize: "0.88rem", maxWidth: 260, marginTop: 10 }}>
            Rent everyday items from people near you — tools, cameras, camping gear, and more. One account, buy or sell anytime.
          </p>
        </div>

        <div>
          <h4 style={{ color: "#fff", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 12 }}>
            Marketplace
          </h4>
          <FooterLink to="/">Browse listings</FooterLink>
          <FooterLink to="/listings/new">List an item</FooterLink>
          <FooterLink to="/dashboard">Dashboard</FooterLink>
        </div>

        <div>
          <h4 style={{ color: "#fff", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 12 }}>
            Account
          </h4>
          <FooterLink to="/login">Log in</FooterLink>
          <FooterLink to="/register">Sign up</FooterLink>
        </div>

        <div>
          <h4 style={{ color: "#fff", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 12 }}>
            Popular categories
          </h4>
          <FooterLink to="/?category=tools-equipment">Tools & Equipment</FooterLink>
          <FooterLink to="/?category=cameras-photography">Cameras & Photography</FooterLink>
          <FooterLink to="/?category=camping-outdoor">Camping & Outdoor</FooterLink>
        </div>
      </div>

      <div
        style={{
          borderTop: "1px solid rgba(255,255,255,0.12)",
          padding: "16px 24px",
          textAlign: "center",
          fontSize: "0.78rem",
          color: "rgba(255,255,255,0.5)",
        }}
      >
        © {year} Borrowly. Demo project — not a real marketplace.
      </div>
    </footer>
  );
}

function FooterLink({ to, children }) {
  return (
    <Link to={to} style={{ display: "block", color: "rgba(255,255,255,0.7)", fontSize: "0.88rem", textDecoration: "none", marginBottom: 8 }}>
      {children}
    </Link>
  );
}